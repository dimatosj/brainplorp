"""
Tests for plorp.core.inbox module.

Tests inbox processing workflow.
"""

import pytest
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock

from plorp.core.inbox import (
    get_inbox_items,
    create_task_from_inbox,
    create_note_from_inbox,
    create_both_from_inbox,
    discard_inbox_item,
)
from plorp.core.exceptions import VaultNotFoundError, InboxNotFoundError


def test_get_inbox_items_success(tmp_path):
    """Test getting unprocessed inbox items from monthly file (Q14)."""
    vault = tmp_path / "vault"
    inbox_dir = vault / "inbox"
    inbox_dir.mkdir(parents=True)

    # Create monthly inbox file
    inbox_path = inbox_dir / "2025-10.md"
    inbox_path.write_text(
        """# Inbox - October 2025

## Unprocessed

- [ ] Buy groceries
- [ ] Call dentist
- [ ] Review project proposal

## Processed

- [x] Email sent - Completed
"""
    )

    result = get_inbox_items(vault, date(2025, 10, 6))

    assert result["inbox_path"].endswith("2025-10.md")
    assert result["item_count"] == 3
    assert len(result["unprocessed_items"]) == 3
    assert result["unprocessed_items"][0]["text"] == "Buy groceries"
    assert result["unprocessed_items"][0]["line_number"] == 1
    assert result["unprocessed_items"][1]["text"] == "Call dentist"
    assert result["unprocessed_items"][2]["text"] == "Review project proposal"


def test_get_inbox_items_empty(tmp_path):
    """Test getting inbox with no unprocessed items."""
    vault = tmp_path / "vault"
    inbox_dir = vault / "inbox"
    inbox_dir.mkdir(parents=True)

    inbox_path = inbox_dir / "2025-10.md"
    inbox_path.write_text(
        """# Inbox

## Unprocessed

## Processed

- [x] Task done
"""
    )

    result = get_inbox_items(vault, date(2025, 10, 6))

    assert result["item_count"] == 0
    assert len(result["unprocessed_items"]) == 0


def test_get_inbox_items_vault_not_found(tmp_path):
    """Test that get_inbox_items raises if vault doesn't exist."""
    missing_vault = tmp_path / "nonexistent"

    with pytest.raises(VaultNotFoundError):
        get_inbox_items(missing_vault)


def test_get_inbox_items_inbox_not_found(tmp_path):
    """Test that get_inbox_items raises if inbox file doesn't exist."""
    vault = tmp_path / "vault"
    vault.mkdir()

    with pytest.raises(InboxNotFoundError):
        get_inbox_items(vault, date(2025, 10, 6))


def test_create_task_from_inbox(tmp_path):
    """Test creating task from inbox item."""
    vault = tmp_path / "vault"
    inbox_dir = vault / "inbox"
    inbox_dir.mkdir(parents=True)

    inbox_path = inbox_dir / "2025-10.md"
    inbox_path.write_text(
        """## Unprocessed

- [ ] Buy groceries

## Processed
"""
    )

    with patch("plorp.core.inbox.create_task") as mock_create_task:
        with patch("plorp.core.inbox.mark_item_processed") as mock_mark:
            mock_create_task.return_value = "abc-123"

            result = create_task_from_inbox(
                vault,
                "Buy groceries",
                "Buy groceries and supplies",
                due="2025-10-10",
                priority="H",
                project="home",
                target_date=date(2025, 10, 6),
            )

            assert result["action"] == "task"
            assert result["task_uuid"] == "abc-123"
            assert result["note_path"] is None
            assert result["item_text"] == "Buy groceries"

            mock_create_task.assert_called_once_with(
                description="Buy groceries and supplies",
                project="home",
                due="2025-10-10",
                priority="H",
            )
            mock_mark.assert_called_once()


def test_create_note_from_inbox(tmp_path):
    """Test creating note from inbox item."""
    vault = tmp_path / "vault"
    inbox_dir = vault / "inbox"
    inbox_dir.mkdir(parents=True)

    inbox_path = inbox_dir / "2025-10.md"
    inbox_path.write_text(
        """## Unprocessed

- [ ] Research topic

## Processed
"""
    )

    with patch("plorp.core.inbox.create_note") as mock_create_note:
        with patch("plorp.core.inbox.mark_item_processed") as mock_mark:
            mock_note_path = vault / "notes" / "research-2025-10-06.md"
            mock_create_note.return_value = mock_note_path

            result = create_note_from_inbox(
                vault,
                "Research topic",
                "Research Notes",
                content="Some notes here",
                note_type="general",
                target_date=date(2025, 10, 6),
            )

            assert result["action"] == "note"
            assert result["task_uuid"] is None
            assert result["note_path"] == str(mock_note_path)
            assert result["item_text"] == "Research topic"

            mock_create_note.assert_called_once_with(
                vault, "Research Notes", "general", "Some notes here"
            )


def test_create_both_from_inbox(tmp_path):
    """Test creating both task and note from inbox item."""
    vault = tmp_path / "vault"
    inbox_dir = vault / "inbox"
    inbox_dir.mkdir(parents=True)

    inbox_path = inbox_dir / "2025-10.md"
    inbox_path.write_text(
        """## Unprocessed

- [ ] Plan meeting

## Processed
"""
    )

    with patch("plorp.core.inbox.create_task") as mock_create_task:
        # Patch where it's imported (in the notes module)
        with patch("plorp.core.notes.create_note_linked_to_task") as mock_create_note:
            with patch("plorp.core.inbox.mark_item_processed") as mock_mark:
                mock_create_task.return_value = "abc-123"
                mock_create_note.return_value = {
                    "note_path": "/vault/notes/meeting.md",
                    "created_at": "2025-10-06T10:00:00",
                    "title": "Meeting Notes",
                    "linked_task_uuid": "abc-123",
                }

                result = create_both_from_inbox(
                    vault,
                    "Plan meeting",
                    "Schedule team meeting",
                    "Meeting Notes",
                    note_content="Agenda items",
                    due="2025-10-15",
                    priority="M",
                    project="work",
                    target_date=date(2025, 10, 6),
                )

                assert result["action"] == "both"
                assert result["task_uuid"] == "abc-123"
                assert result["note_path"] == "/vault/notes/meeting.md"

                mock_create_task.assert_called_once()
                mock_create_note.assert_called_once()


def test_discard_inbox_item(tmp_path):
    """Test discarding inbox item."""
    vault = tmp_path / "vault"
    inbox_dir = vault / "inbox"
    inbox_dir.mkdir(parents=True)

    inbox_path = inbox_dir / "2025-10.md"
    inbox_path.write_text(
        """## Unprocessed

- [ ] Old idea

## Processed
"""
    )

    with patch("plorp.core.inbox.mark_item_processed") as mock_mark:
        result = discard_inbox_item(vault, "Old idea", target_date=date(2025, 10, 6))

        assert result["action"] == "discard"
        assert result["task_uuid"] is None
        assert result["note_path"] is None
        assert result["item_text"] == "Old idea"

        mock_mark.assert_called_once_with(
            inbox_path, "Old idea", "Discarded"
        )


def test_create_task_from_inbox_failure(tmp_path):
    """Test handling task creation failure."""
    vault = tmp_path / "vault"
    inbox_dir = vault / "inbox"
    inbox_dir.mkdir(parents=True)

    inbox_path = inbox_dir / "2025-10.md"
    inbox_path.write_text("## Unprocessed\n\n- [ ] Test\n")

    with patch("plorp.core.inbox.create_task") as mock_create_task:
        mock_create_task.return_value = None  # Failure

        with pytest.raises(RuntimeError, match="Failed to create task"):
            create_task_from_inbox(
                vault,
                "Test",
                "Test task",
                target_date=date(2025, 10, 6),
            )


def test_create_both_from_inbox_failure(tmp_path):
    """Test handling task creation failure in create_both."""
    vault = tmp_path / "vault"
    inbox_dir = vault / "inbox"
    inbox_dir.mkdir(parents=True)

    inbox_path = inbox_dir / "2025-10.md"
    inbox_path.write_text("## Unprocessed\n\n- [ ] Test\n")

    with patch("plorp.core.inbox.create_task") as mock_create_task:
        mock_create_task.return_value = None  # Failure

        with pytest.raises(RuntimeError, match="Failed to create task"):
            create_both_from_inbox(
                vault,
                "Test",
                "Test task",
                "Test note",
                target_date=date(2025, 10, 6),
            )


def test_get_inbox_items_defaults_to_today(tmp_path):
    """Test that get_inbox_items defaults to current month."""
    vault = tmp_path / "vault"
    inbox_dir = vault / "inbox"
    inbox_dir.mkdir(parents=True)

    # Create inbox for current month
    current_month = date.today().strftime("%Y-%m")
    inbox_path = inbox_dir / f"{current_month}.md"
    inbox_path.write_text("## Unprocessed\n\n- [ ] Current item\n")

    result = get_inbox_items(vault)  # No date specified

    assert result["inbox_path"].endswith(f"{current_month}.md")
    assert result["item_count"] == 1


# Email Appending Tests (Sprint 9.2)


def test_append_emails_to_inbox_new_file(tmp_path):
    """Test appending emails when inbox file doesn't exist."""
    from plorp.core.inbox import append_emails_to_inbox

    vault = tmp_path / "vault"
    vault.mkdir()

    emails = [
        {"id": "1", "body_text": "- Task 1\n- Task 2", "body_html": ""}
    ]

    with patch("plorp.core.inbox.date") as mock_date:
        mock_date.today.return_value = date(2025, 10, 6)

        result = append_emails_to_inbox(emails, vault)

        assert result["appended_count"] == 1
        assert "2025-10" in result["inbox_path"]
        assert result["total_unprocessed"] == 2  # Two bullets

        # Verify file content
        inbox_file = Path(result["inbox_path"])
        assert inbox_file.exists()
        content = inbox_file.read_text()
        assert "- Task 1" in content
        assert "- Task 2" in content
        assert "## Unprocessed" in content
        assert "## Processed" in content


def test_append_emails_to_inbox_existing_file(tmp_path):
    """Test appending emails to existing inbox file."""
    from plorp.core.inbox import append_emails_to_inbox

    vault = tmp_path / "vault"
    inbox_dir = vault / "inbox"
    inbox_dir.mkdir(parents=True)

    # Create existing inbox with one item
    inbox_file = inbox_dir / "2025-10.md"
    inbox_file.write_text(
        "# Inbox 2025-10\n\n"
        "## Unprocessed\n\n"
        "- Existing item\n\n"
        "## Processed\n"
    )

    emails = [
        {"id": "2", "body_text": "New task from email", "body_html": ""}
    ]

    with patch("plorp.core.inbox.date") as mock_date:
        mock_date.today.return_value = date(2025, 10, 6)

        result = append_emails_to_inbox(emails, vault)

        assert result["appended_count"] == 1
        assert result["total_unprocessed"] == 2  # 1 existing + 1 new

        content = inbox_file.read_text()
        assert "- Existing item" in content
        assert "- New task from email" in content


def test_append_emails_with_html_body(tmp_path):
    """Test appending emails with HTML body."""
    from plorp.core.inbox import append_emails_to_inbox

    vault = tmp_path / "vault"
    vault.mkdir()

    emails = [
        {
            "id": "3",
            "body_text": "",
            "body_html": "<ul><li>Item 1</li><li>Item 2</li></ul>",
        }
    ]

    with patch("plorp.core.inbox.date") as mock_date:
        mock_date.today.return_value = date(2025, 10, 6)

        result = append_emails_to_inbox(emails, vault)

        inbox_file = Path(result["inbox_path"])
        content = inbox_file.read_text()

        # html2text should convert HTML list to markdown bullets
        assert "Item 1" in content
        assert "Item 2" in content


def test_append_emails_with_multiple_emails(tmp_path):
    """Test appending multiple emails at once."""
    from plorp.core.inbox import append_emails_to_inbox

    vault = tmp_path / "vault"
    vault.mkdir()

    emails = [
        {"id": "1", "body_text": "First email task", "body_html": ""},
        {"id": "2", "body_text": "Second email task", "body_html": ""},
        {"id": "3", "body_text": "Third email task", "body_html": ""},
    ]

    with patch("plorp.core.inbox.date") as mock_date:
        mock_date.today.return_value = date(2025, 10, 6)

        result = append_emails_to_inbox(emails, vault)

        assert result["appended_count"] == 3
        assert result["total_unprocessed"] == 3

        inbox_file = Path(result["inbox_path"])
        content = inbox_file.read_text()
        assert "- First email task" in content
        assert "- Second email task" in content
        assert "- Third email task" in content


def test_append_emails_empty_list(tmp_path):
    """Test appending empty email list."""
    from plorp.core.inbox import append_emails_to_inbox

    vault = tmp_path / "vault"
    vault.mkdir()

    emails = []

    with patch("plorp.core.inbox.date") as mock_date:
        mock_date.today.return_value = date(2025, 10, 6)

        result = append_emails_to_inbox(emails, vault)

        assert result["appended_count"] == 0
        assert result["total_unprocessed"] == 0
