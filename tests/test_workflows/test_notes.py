# ABOUTME: Tests for note workflow - validates note creation and task-note linking
# ABOUTME: Mocks TaskWarrior operations and uses temporary files for testing
"""Tests for note workflow."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from brainplorp.workflows.notes import (
    create_note_with_task_link,
    link_note_to_task,
    unlink_note_from_task,
    get_linked_notes,
    get_linked_tasks,
)


@pytest.fixture
def test_vault(tmp_path):
    """Create test vault structure."""
    vault = tmp_path / "vault"
    (vault / "notes").mkdir(parents=True)
    return vault


@patch("brainplorp.workflows.notes.get_task_info")
@patch("brainplorp.integrations.taskwarrior.get_task_info")
@patch("brainplorp.workflows.notes.add_annotation")
@patch("brainplorp.workflows.notes.get_task_annotations")
@patch("brainplorp.workflows.notes.create_note")
@patch("brainplorp.workflows.notes.get_vault_path")
def test_create_note_with_task_link(
    mock_vault_path,
    mock_create_note,
    mock_annotations,
    mock_add_annotation,
    mock_tw_task_info,
    mock_task_info,
    test_vault,
):
    """Test creating note with task link."""
    mock_vault_path.return_value = test_vault
    mock_task_info.return_value = {"uuid": "abc-123", "description": "Test task"}
    mock_tw_task_info.return_value = {"uuid": "abc-123", "description": "Test task"}
    mock_annotations.return_value = []

    note_path = test_vault / "notes" / "meeting-notes.md"
    note_path.write_text("---\ntitle: Meeting Notes\n---\n\n# Meeting Notes")
    mock_create_note.return_value = note_path

    config = {"vault_path": str(test_vault)}

    result = create_note_with_task_link(config, "Meeting Notes", task_uuid="abc-123")

    assert result == note_path
    assert result.exists()

    # Verify front matter has task UUID
    content = result.read_text()
    assert "tasks:" in content
    assert "abc-123" in content

    # Verify annotation added
    mock_add_annotation.assert_called_once()


@patch("brainplorp.workflows.notes.get_task_info")
def test_create_note_with_invalid_task(mock_task_info, test_vault):
    """Test creating note with non-existent task."""
    mock_task_info.return_value = None  # Task not found

    config = {"vault_path": str(test_vault)}

    with pytest.raises(ValueError, match="Task not found"):
        create_note_with_task_link(config, "Note", task_uuid="invalid-uuid")


@patch("brainplorp.workflows.notes.create_note")
@patch("brainplorp.workflows.notes.get_vault_path")
def test_create_note_without_task(mock_vault_path, mock_create_note, test_vault):
    """Test creating note without task link."""
    mock_vault_path.return_value = test_vault

    note_path = test_vault / "notes" / "simple-note.md"
    note_path.write_text("# Simple Note")
    mock_create_note.return_value = note_path

    config = {"vault_path": str(test_vault)}

    result = create_note_with_task_link(config, "Simple Note")

    assert result.exists()

    content = result.read_text()
    # Should not have tasks field
    assert "tasks:" not in content or "tasks: []" in content


@patch("brainplorp.workflows.notes.get_task_info")
@patch("brainplorp.integrations.taskwarrior.get_task_info")
@patch("brainplorp.workflows.notes.add_annotation")
@patch("brainplorp.workflows.notes.get_task_annotations")
def test_link_note_to_task(
    mock_annotations, mock_add_ann, mock_tw_task_info, mock_task_info, test_vault
):
    """Test linking existing note to task."""
    mock_task_info.return_value = {"uuid": "abc-123", "description": "Test"}
    mock_tw_task_info.return_value = {"uuid": "abc-123", "description": "Test"}
    mock_annotations.return_value = []  # No existing annotations

    # Create a note
    note_path = test_vault / "notes" / "test-note.md"
    note_path.write_text(
        """---
title: Test Note
---

Content
"""
    )

    link_note_to_task(note_path, "abc-123", test_vault)

    # Verify task UUID added to front matter
    content = note_path.read_text()
    assert "tasks:" in content
    assert "abc-123" in content

    # Verify annotation added
    mock_add_ann.assert_called_once()
    annotation = mock_add_ann.call_args[0][1]
    assert "plorp:note:" in annotation
    assert "test-note.md" in annotation


@patch("brainplorp.workflows.notes.get_task_info")
def test_link_note_to_invalid_task(mock_task_info, test_vault):
    """Test linking note to non-existent task."""
    mock_task_info.return_value = None

    note_path = test_vault / "notes" / "test.md"
    note_path.write_text("# Test")

    with pytest.raises(ValueError, match="Task not found"):
        link_note_to_task(note_path, "invalid-uuid", test_vault)


@patch("brainplorp.workflows.notes.get_task_info")
def test_link_note_not_found(mock_task_info, test_vault):
    """Test linking non-existent note."""
    mock_task_info.return_value = {"uuid": "abc-123"}

    note_path = test_vault / "notes" / "nonexistent.md"

    with pytest.raises(FileNotFoundError):
        link_note_to_task(note_path, "abc-123", test_vault)


@patch("brainplorp.workflows.notes.get_task_info")
@patch("brainplorp.integrations.taskwarrior.get_task_info")
@patch("brainplorp.workflows.notes.add_annotation")
@patch("brainplorp.workflows.notes.get_task_annotations")
def test_link_note_to_task_already_linked(
    mock_annotations, mock_add_ann, mock_tw_task_info, mock_task_info, test_vault
):
    """Test linking note that's already linked (should not duplicate)."""
    mock_task_info.return_value = {"uuid": "abc-123"}
    mock_tw_task_info.return_value = {"uuid": "abc-123"}
    mock_annotations.return_value = ["plorp:note:notes/test-note.md"]  # Already linked

    note_path = test_vault / "notes" / "test-note.md"
    note_path.write_text("---\ntitle: Test\n---\n\nContent")

    link_note_to_task(note_path, "abc-123", test_vault)

    # Annotation should not be added again
    mock_add_ann.assert_not_called()


def test_unlink_note_from_task(test_vault):
    """Test unlinking note from task."""
    note_path = test_vault / "notes" / "test.md"
    content = """---
title: Test
tasks:
  - abc-123
  - def-456
---

Content
"""
    note_path.write_text(content)

    unlink_note_from_task(note_path, "abc-123")

    updated = note_path.read_text()
    assert "abc-123" not in updated
    assert "def-456" in updated  # Other task preserved


@patch("brainplorp.workflows.notes.get_task_annotations")
def test_get_linked_notes(mock_annotations, test_vault):
    """Test getting notes linked to task."""
    # Create some notes
    note1 = test_vault / "notes" / "meeting-1.md"
    note2 = test_vault / "notes" / "meeting-2.md"
    note1.write_text("# Note 1")
    note2.write_text("# Note 2")

    # Mock task annotations
    mock_annotations.return_value = [
        "plorp:note:notes/meeting-1.md",
        "plorp:note:notes/meeting-2.md",
        "Some other annotation",
    ]

    notes = get_linked_notes("abc-123", test_vault)

    assert len(notes) == 2
    assert note1 in notes
    assert note2 in notes


@patch("brainplorp.workflows.notes.get_task_annotations")
def test_get_linked_notes_nonexistent(mock_annotations, test_vault):
    """Test getting linked notes when note files don't exist."""
    mock_annotations.return_value = ["plorp:note:notes/deleted-note.md"]

    notes = get_linked_notes("abc-123", test_vault)

    # Should not include non-existent notes
    assert len(notes) == 0


def test_get_linked_tasks(test_vault):
    """Test getting tasks linked to note."""
    note_path = test_vault / "notes" / "test.md"
    content = """---
title: Test Note
tasks:
  - abc-123
  - def-456
  - ghi-789
---

Content
"""
    note_path.write_text(content)

    tasks = get_linked_tasks(note_path)

    assert len(tasks) == 3
    assert "abc-123" in tasks
    assert "def-456" in tasks
    assert "ghi-789" in tasks


def test_get_linked_tasks_no_tasks(test_vault):
    """Test getting tasks from note with no linked tasks."""
    note_path = test_vault / "notes" / "test.md"
    note_path.write_text("---\ntitle: Test\n---\n\nContent")

    tasks = get_linked_tasks(note_path)

    assert tasks == []
