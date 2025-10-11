"""
Tests for plorp.core.notes module.

Tests note creation and linking functions.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from brainplorp.core.notes import (
    create_note_standalone,
    create_note_linked_to_task,
    link_note_to_task,
)
from brainplorp.core.exceptions import (
    VaultNotFoundError,
    TaskNotFoundError,
    NoteNotFoundError,
    NoteOutsideVaultError,
)


def test_create_note_standalone(tmp_path):
    """Test creating standalone note."""
    vault = tmp_path / "vault"
    vault.mkdir()

    with patch("brainplorp.core.notes.create_note") as mock_create_note:
        mock_note_path = vault / "notes" / "test-note-2025-10-06.md"
        mock_create_note.return_value = mock_note_path

        result = create_note_standalone(
            vault, "Test Note", note_type="general", content="Some content"
        )

        assert result["note_path"] == str(mock_note_path)
        assert result["title"] == "Test Note"
        assert result["linked_task_uuid"] is None
        assert "created_at" in result

        mock_create_note.assert_called_once_with(
            vault, "Test Note", "general", "Some content"
        )


def test_create_note_standalone_vault_not_found(tmp_path):
    """Test creating note raises if vault doesn't exist."""
    missing_vault = tmp_path / "nonexistent"

    with pytest.raises(VaultNotFoundError):
        create_note_standalone(missing_vault, "Test")


def test_create_note_linked_to_task(tmp_path):
    """Test creating note linked to task."""
    vault = tmp_path / "vault"
    vault.mkdir()

    with patch("brainplorp.core.notes.get_task_info") as mock_get_task:
        with patch("brainplorp.core.notes.create_note") as mock_create_note:
            with patch("brainplorp.core.notes.link_note_to_task") as mock_link:
                mock_get_task.return_value = {
                    "uuid": "abc-123",
                    "description": "Test task",
                }
                mock_note_path = vault / "notes" / "test-note.md"
                mock_create_note.return_value = mock_note_path

                result = create_note_linked_to_task(
                    vault,
                    "Meeting Notes",
                    "abc-123",
                    note_type="meeting",
                    content="Agenda",
                )

                assert result["note_path"] == str(mock_note_path)
                assert result["title"] == "Meeting Notes"
                assert result["linked_task_uuid"] == "abc-123"
                assert "created_at" in result

                mock_get_task.assert_called_once_with("abc-123")
                mock_create_note.assert_called_once_with(
                    vault, "Meeting Notes", "meeting", "Agenda"
                )
                mock_link.assert_called_once()


def test_create_note_linked_to_task_not_found(tmp_path):
    """Test creating note linked to non-existent task raises error."""
    vault = tmp_path / "vault"
    vault.mkdir()

    with patch("brainplorp.core.notes.get_task_info") as mock_get_task:
        mock_get_task.return_value = None

        with pytest.raises(TaskNotFoundError):
            create_note_linked_to_task(vault, "Note", "nonexistent-123")


def test_link_note_to_task_success(tmp_path):
    """Test linking existing note to task."""
    vault = tmp_path / "vault"
    notes_dir = vault / "notes"
    notes_dir.mkdir(parents=True)

    note_path = notes_dir / "existing-note.md"
    note_path.write_text("# Existing Note")

    with patch("brainplorp.core.notes.get_task_info") as mock_get_task:
        with patch("brainplorp.core.notes.add_task_to_note_frontmatter") as mock_add_fm:
            with patch("brainplorp.core.notes.get_task_annotations") as mock_get_ann:
                with patch("brainplorp.core.notes.add_annotation") as mock_add_ann:
                    mock_get_task.return_value = {
                        "uuid": "abc-123",
                        "description": "Test task",
                    }
                    mock_get_ann.return_value = []

                    result = link_note_to_task(vault, note_path, "abc-123")

                    assert result["note_path"] == str(note_path)
                    assert result["task_uuid"] == "abc-123"
                    assert "linked_at" in result

                    mock_add_fm.assert_called_once_with(note_path, "abc-123")
                    # Should add annotation with plorp:note: prefix
                    mock_add_ann.assert_called_once_with(
                        "abc-123", "plorp:note:notes/existing-note.md"
                    )


def test_link_note_to_task_prevents_duplicates(tmp_path):
    """Test that linking prevents duplicate annotations."""
    vault = tmp_path / "vault"
    notes_dir = vault / "notes"
    notes_dir.mkdir(parents=True)

    note_path = notes_dir / "existing-note.md"
    note_path.write_text("# Existing Note")

    with patch("brainplorp.core.notes.get_task_info") as mock_get_task:
        with patch("brainplorp.core.notes.add_task_to_note_frontmatter") as mock_add_fm:
            with patch("brainplorp.core.notes.get_task_annotations") as mock_get_ann:
                with patch("brainplorp.core.notes.add_annotation") as mock_add_ann:
                    mock_get_task.return_value = {
                        "uuid": "abc-123",
                        "description": "Test task",
                    }
                    # Annotation already exists
                    mock_get_ann.return_value = ["plorp:note:notes/existing-note.md"]

                    result = link_note_to_task(vault, note_path, "abc-123")

                    # Frontmatter still updated
                    mock_add_fm.assert_called_once()
                    # But annotation NOT added again
                    mock_add_ann.assert_not_called()


def test_link_note_to_task_not_found(tmp_path):
    """Test linking to non-existent task raises error."""
    vault = tmp_path / "vault"
    notes_dir = vault / "notes"
    notes_dir.mkdir(parents=True)

    note_path = notes_dir / "note.md"
    note_path.write_text("# Note")

    with patch("brainplorp.core.notes.get_task_info") as mock_get_task:
        mock_get_task.return_value = None

        with pytest.raises(TaskNotFoundError):
            link_note_to_task(vault, note_path, "nonexistent-123")


def test_link_note_to_task_note_not_found(tmp_path):
    """Test linking non-existent note raises error."""
    vault = tmp_path / "vault"
    vault.mkdir()

    missing_note = vault / "notes" / "missing.md"

    with patch("brainplorp.core.notes.get_task_info") as mock_get_task:
        mock_get_task.return_value = {"uuid": "abc-123", "description": "Test"}

        with pytest.raises(NoteNotFoundError):
            link_note_to_task(vault, missing_note, "abc-123")


def test_link_note_to_task_outside_vault(tmp_path):
    """Test linking note outside vault raises error."""
    vault = tmp_path / "vault"
    vault.mkdir()

    outside_note = tmp_path / "outside" / "note.md"
    outside_note.parent.mkdir()
    outside_note.write_text("# Outside Note")

    with patch("brainplorp.core.notes.get_task_info") as mock_get_task:
        mock_get_task.return_value = {"uuid": "abc-123", "description": "Test"}

        with pytest.raises(NoteOutsideVaultError):
            link_note_to_task(vault, outside_note, "abc-123")


def test_link_note_to_task_normalizes_path(tmp_path):
    """Test that note path is normalized to POSIX format for annotations."""
    vault = tmp_path / "vault"
    notes_dir = vault / "meetings"
    notes_dir.mkdir(parents=True)

    note_path = notes_dir / "team-meeting.md"
    note_path.write_text("# Meeting")

    with patch("brainplorp.core.notes.get_task_info") as mock_get_task:
        with patch("brainplorp.core.notes.add_task_to_note_frontmatter") as mock_add_fm:
            with patch("brainplorp.core.notes.get_task_annotations") as mock_get_ann:
                with patch("brainplorp.core.notes.add_annotation") as mock_add_ann:
                    mock_get_task.return_value = {"uuid": "abc-123", "description": "Test"}
                    mock_get_ann.return_value = []

                    link_note_to_task(vault, note_path, "abc-123")

                    # Should use POSIX path format (forward slashes)
                    mock_add_ann.assert_called_once_with(
                        "abc-123", "plorp:note:meetings/team-meeting.md"
                    )
