# ABOUTME: Tests for inbox workflow - validates inbox processing with mocked interactions
# ABOUTME: Uses monkeypatch to mock user input and verify task/note creation
"""Tests for inbox workflow."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from brainplorp.workflows.inbox import (
    process,
    get_current_inbox_path,
    process_item_as_task,
    process_item_as_note,
)


@pytest.fixture
def inbox_file(tmp_path):
    """Create sample inbox file."""
    vault = tmp_path / "vault"
    inbox_dir = vault / "inbox"
    inbox_dir.mkdir(parents=True)

    inbox = inbox_dir / "2025-10.md"
    content = """# Inbox - October 2025

## Unprocessed

- [ ] Buy groceries
- [ ] Research TaskWarrior hooks
- [ ] Meeting notes: Sprint planning

## Processed

- [x] Old item
"""
    inbox.write_text(content)

    return vault, inbox


def test_get_current_inbox_path(tmp_path, monkeypatch):
    """Test getting current inbox path."""
    vault = tmp_path / "vault"
    vault.mkdir()

    config = {"vault_path": str(vault)}

    # Mock datetime to control current month
    from datetime import datetime

    mock_dt = MagicMock()
    mock_dt.now.return_value.strftime.return_value = "2025-10"
    monkeypatch.setattr("brainplorp.workflows.inbox.datetime", mock_dt)

    inbox_path = get_current_inbox_path(config)

    assert inbox_path == vault / "inbox" / "2025-10.md"


@patch("brainplorp.workflows.inbox.create_task")
@patch("brainplorp.workflows.inbox.prompt")
@patch("brainplorp.workflows.inbox.confirm")
def test_process_item_as_task_success(mock_confirm, mock_prompt, mock_create_task, tmp_path):
    """Test processing inbox item as task successfully."""
    mock_prompt.side_effect = [
        "Buy groceries",  # description
        "home",  # project
        "tomorrow",  # due
        "M",  # priority
        "shopping",  # tags
    ]
    mock_confirm.return_value = True
    mock_create_task.return_value = "abc-123"

    config = {"vault_path": str(tmp_path)}

    uuid, should_mark = process_item_as_task("Buy groceries", config)

    assert uuid == "abc-123"
    assert should_mark is False
    mock_create_task.assert_called_once()
    call_kwargs = mock_create_task.call_args[1]
    assert call_kwargs["description"] == "Buy groceries"
    assert call_kwargs["project"] == "home"
    assert call_kwargs["due"] == "tomorrow"
    assert call_kwargs["priority"] == "M"
    assert call_kwargs["tags"] == ["shopping"]


@patch("brainplorp.workflows.inbox.create_task")
@patch("brainplorp.workflows.inbox.prompt")
@patch("brainplorp.workflows.inbox.confirm")
def test_process_item_as_task_cancelled(mock_confirm, mock_prompt, mock_create_task):
    """Test cancelling task creation."""
    mock_prompt.side_effect = ["Task", "", "", "", ""]
    mock_confirm.return_value = False  # User cancels

    uuid, should_mark = process_item_as_task("Item", {})

    assert uuid is None
    assert should_mark is False
    mock_create_task.assert_not_called()


@patch("brainplorp.workflows.inbox.create_task")
@patch("brainplorp.workflows.inbox.prompt")
@patch("brainplorp.workflows.inbox.confirm")
def test_process_item_as_task_retry_success(mock_confirm, mock_prompt, mock_create_task):
    """Test retry after initial failure."""
    mock_prompt.side_effect = ["Task", "", "", "", ""]
    mock_confirm.return_value = True
    # First call fails, second succeeds
    mock_create_task.side_effect = [None, "xyz-789"]

    uuid, should_mark = process_item_as_task("Item", {})

    assert uuid == "xyz-789"
    assert should_mark is False
    assert mock_create_task.call_count == 2


@patch("brainplorp.workflows.inbox.create_task")
@patch("brainplorp.workflows.inbox.prompt")
@patch("brainplorp.workflows.inbox.confirm")
def test_process_item_as_task_mark_failed(mock_confirm, mock_prompt, mock_create_task):
    """Test marking as processed after failure."""
    mock_prompt.side_effect = ["Task", "", "", "", ""]
    # First confirm: retry (True), second confirm: mark anyway (True)
    mock_confirm.side_effect = [True, True, True]  # create, retry, mark
    mock_create_task.return_value = None  # Both attempts fail

    uuid, should_mark = process_item_as_task("Item", {})

    assert uuid is None
    assert should_mark is True


@patch("brainplorp.workflows.inbox.create_note")
@patch("brainplorp.workflows.inbox.prompt")
@patch("brainplorp.workflows.inbox.confirm")
@patch("builtins.input")
def test_process_item_as_note(mock_input, mock_confirm, mock_prompt, mock_create_note, tmp_path):
    """Test processing inbox item as note."""
    vault = tmp_path / "vault"
    vault.mkdir()

    mock_prompt.side_effect = ["Meeting Notes", "meeting"]  # title  # note_type
    mock_input.side_effect = EOFError()  # No content
    mock_confirm.return_value = True

    expected_path = vault / "meetings" / "meeting-notes-2025-10-06.md"
    mock_create_note.return_value = expected_path

    config = {"vault_path": str(vault)}

    note_path = process_item_as_note("Meeting item", config)

    assert note_path == expected_path
    mock_create_note.assert_called_once()


@patch("brainplorp.workflows.inbox.prompt_choice")
@patch("brainplorp.workflows.inbox.process_item_as_task")
@patch("brainplorp.workflows.inbox.mark_item_processed")
def test_process_create_task(mock_mark, mock_task, mock_choice, inbox_file, capsys):
    """Test full inbox processing creating task."""
    vault, inbox = inbox_file

    # User chooses "Create task" then "Quit"
    mock_choice.side_effect = [0, 4]  # 0 = Create task, 4 = Quit

    mock_task.return_value = ("abc-123", False)

    config = {"vault_path": str(vault)}

    process(config)

    # Verify task created and marked
    mock_task.assert_called_once()
    mock_mark.assert_called_once()

    captured = capsys.readouterr()
    assert "✅ Task created" in captured.out


@patch("brainplorp.workflows.inbox.prompt_choice")
@patch("brainplorp.workflows.inbox.confirm")
@patch("brainplorp.workflows.inbox.mark_item_processed")
def test_process_discard_item(mock_mark, mock_confirm, mock_choice, inbox_file, capsys):
    """Test discarding inbox item."""
    vault, inbox = inbox_file

    # User chooses "Discard" then "Quit"
    mock_choice.side_effect = [2, 4]  # 2 = Discard, 4 = Quit
    mock_confirm.return_value = True

    config = {"vault_path": str(vault)}

    process(config)

    # Verify item marked as discarded
    mock_mark.assert_called_once()
    assert "Discarded" in mock_mark.call_args[0][2]


def test_process_empty_inbox(tmp_path, capsys):
    """Test processing when inbox is empty."""
    vault = tmp_path / "vault"
    inbox_dir = vault / "inbox"
    inbox_dir.mkdir(parents=True)

    inbox = inbox_dir / "2025-10.md"
    content = """# Inbox

## Unprocessed

## Processed

- [x] Old items
"""
    inbox.write_text(content)

    config = {"vault_path": str(vault)}

    with patch("brainplorp.workflows.inbox.get_current_inbox_path", return_value=inbox):
        process(config)

    captured = capsys.readouterr()
    assert "Inbox is empty" in captured.out


def test_process_creates_inbox_file(tmp_path, capsys, monkeypatch):
    """Test that process creates inbox file if it doesn't exist."""
    vault = tmp_path / "vault"
    vault.mkdir()

    inbox = vault / "inbox" / "2025-10.md"

    config = {"vault_path": str(vault)}

    # Mock datetime for consistent filename
    from datetime import datetime

    mock_dt = MagicMock()
    mock_dt.now.return_value.strftime.side_effect = lambda fmt: {
        "%Y-%m": "2025-10",
        "%B %Y": "October 2025",
    }[fmt]
    monkeypatch.setattr("brainplorp.workflows.inbox.datetime", mock_dt)

    with patch("brainplorp.workflows.inbox.get_current_inbox_path", return_value=inbox):
        process(config)

    # Verify inbox file created
    assert inbox.exists()
    content = inbox.read_text()
    assert "## Unprocessed" in content
    assert "## Processed" in content

    captured = capsys.readouterr()
    assert "✨ Created inbox file" in captured.out
    assert "Inbox is empty" in captured.out


@patch("brainplorp.workflows.inbox.prompt_choice")
def test_process_skip_item(mock_choice, inbox_file, capsys):
    """Test skipping an inbox item."""
    vault, inbox = inbox_file

    # User chooses "Skip" then "Quit"
    mock_choice.side_effect = [3, 4]  # 3 = Skip, 4 = Quit

    config = {"vault_path": str(vault)}

    process(config)

    captured = capsys.readouterr()
    assert "⏭️  Skipped" in captured.out
    assert "✅ Processed 0 items" in captured.out


@patch("brainplorp.workflows.inbox.prompt_choice")
@patch("brainplorp.workflows.inbox.process_item_as_task")
@patch("brainplorp.workflows.inbox.mark_item_processed")
def test_process_mark_failed_task(mock_mark, mock_task, mock_choice, inbox_file, capsys):
    """Test marking item as processed when task creation fails."""
    vault, inbox = inbox_file

    # User chooses "Create task" then "Quit"
    mock_choice.side_effect = [0, 4]

    # Return None for UUID but True for should_mark_failed
    mock_task.return_value = (None, True)

    config = {"vault_path": str(vault)}

    process(config)

    # Should mark as processed with failure message
    mock_mark.assert_called_once()
    assert "Failed to create task" in mock_mark.call_args[0][2]


@patch("brainplorp.workflows.inbox.prompt")
def test_process_item_as_task_no_description(mock_prompt):
    """Test task creation with empty description."""
    mock_prompt.return_value = ""

    uuid, should_mark = process_item_as_task("Item", {})

    assert uuid is None
    assert should_mark is False


@patch("brainplorp.workflows.inbox.create_note")
@patch("brainplorp.workflows.inbox.prompt")
@patch("brainplorp.workflows.inbox.confirm")
@patch("builtins.input")
def test_process_item_as_note_cancelled(
    mock_input, mock_confirm, mock_prompt, mock_create_note, tmp_path
):
    """Test cancelling note creation."""
    vault = tmp_path / "vault"
    vault.mkdir()

    mock_prompt.side_effect = ["Note Title", "general"]
    mock_input.side_effect = EOFError()
    mock_confirm.return_value = False  # Cancel

    config = {"vault_path": str(vault)}

    note_path = process_item_as_note("Item", config)

    assert note_path is None
    mock_create_note.assert_not_called()


@patch("brainplorp.workflows.inbox.prompt")
def test_process_item_as_note_no_title(mock_prompt):
    """Test note creation with empty title."""
    mock_prompt.return_value = ""

    note_path = process_item_as_note("Item", {})

    assert note_path is None
