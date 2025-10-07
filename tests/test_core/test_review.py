"""
Tests for plorp.core.review module.

Tests review workflow functions.
"""

import pytest
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock

from plorp.core.review import get_review_tasks, add_review_notes, _normalize_task
from plorp.core.exceptions import VaultNotFoundError, DailyNoteNotFoundError


def test_get_review_tasks_returns_uncompleted(tmp_path):
    """Test getting uncompleted tasks from daily note."""
    vault = tmp_path / "vault"
    daily_dir = vault / "daily"
    daily_dir.mkdir(parents=True)

    # Create daily note with unchecked tasks
    note_path = daily_dir / "2025-10-06.md"
    note_path.write_text(
        """# Daily Note - 2025-10-06

## Tasks

- [ ] Uncompleted task 1 (uuid: abc-123)
- [x] Completed task (uuid: def-456)
- [ ] Uncompleted task 2 (uuid: ghi-789)
"""
    )

    with patch("plorp.core.review.get_task_info") as mock_get_task:
        mock_get_task.side_effect = lambda uuid: {
            "abc-123": {
                "uuid": "abc-123",
                "description": "Uncompleted task 1",
                "status": "pending",
                "due": None,
                "priority": "",
                "project": None,
                "tags": [],
            },
            "ghi-789": {
                "uuid": "ghi-789",
                "description": "Uncompleted task 2",
                "status": "pending",
                "due": None,
                "priority": "",
                "project": None,
                "tags": [],
            },
        }.get(uuid)

        result = get_review_tasks(date(2025, 10, 6), vault)

        assert result["date"] == "2025-10-06"
        assert result["uncompleted_count"] == 2
        assert result["total_tasks"] == 2
        assert len(result["uncompleted_tasks"]) == 2
        assert result["uncompleted_tasks"][0]["uuid"] == "abc-123"
        assert result["uncompleted_tasks"][1]["uuid"] == "ghi-789"


def test_get_review_tasks_handles_missing_tasks(tmp_path):
    """Test that missing tasks (Q16) are returned with status: missing."""
    vault = tmp_path / "vault"
    daily_dir = vault / "daily"
    daily_dir.mkdir(parents=True)

    # Create daily note with task that was deleted from TaskWarrior
    note_path = daily_dir / "2025-10-06.md"
    note_path.write_text(
        """# Daily Note - 2025-10-06

- [ ] Task deleted from TaskWarrior (uuid: deleted-123)
- [ ] Task still exists (uuid: exists-456)
"""
    )

    with patch("plorp.core.review.get_task_info") as mock_get_task:
        # First task returns None (deleted), second exists
        mock_get_task.side_effect = lambda uuid: (
            None
            if uuid == "deleted-123"
            else {
                "uuid": "exists-456",
                "description": "Task still exists",
                "status": "pending",
                "due": None,
                "priority": "",
                "project": None,
                "tags": [],
            }
        )

        result = get_review_tasks(date(2025, 10, 6), vault)

        assert result["uncompleted_count"] == 2
        # First task should have status "missing"
        assert result["uncompleted_tasks"][0]["status"] == "missing"
        assert result["uncompleted_tasks"][0]["uuid"] == "deleted-123"
        assert result["uncompleted_tasks"][0]["description"] == "Task deleted from TaskWarrior"
        # Second task should be normal
        assert result["uncompleted_tasks"][1]["status"] == "pending"


def test_get_review_tasks_raises_on_missing_vault(tmp_path):
    """Test that get_review_tasks raises if vault doesn't exist."""
    missing_vault = tmp_path / "nonexistent"

    with pytest.raises(VaultNotFoundError):
        get_review_tasks(date(2025, 10, 6), missing_vault)


def test_get_review_tasks_raises_on_missing_note(tmp_path):
    """Test that get_review_tasks raises if daily note doesn't exist."""
    vault = tmp_path / "vault"
    vault.mkdir()

    with pytest.raises(DailyNoteNotFoundError):
        get_review_tasks(date(2025, 10, 6), vault)


def test_get_review_tasks_empty_task_list(tmp_path):
    """Test get_review_tasks with no uncompleted tasks."""
    vault = tmp_path / "vault"
    daily_dir = vault / "daily"
    daily_dir.mkdir(parents=True)

    # Create daily note with only completed tasks
    note_path = daily_dir / "2025-10-06.md"
    note_path.write_text(
        """# Daily Note - 2025-10-06

- [x] Completed task (uuid: abc-123)
"""
    )

    result = get_review_tasks(date(2025, 10, 6), vault)

    assert result["uncompleted_count"] == 0
    assert len(result["uncompleted_tasks"]) == 0


def test_add_review_notes_appends_section(tmp_path):
    """Test adding review notes to daily note."""
    vault = tmp_path / "vault"
    daily_dir = vault / "daily"
    daily_dir.mkdir(parents=True)

    # Create existing note
    note_path = daily_dir / "2025-10-06.md"
    note_path.write_text("# Daily Note - 2025-10-06\n\nExisting content\n")

    reflections = {
        "went_well": "Completed all tasks",
        "could_improve": "Better time management",
        "tomorrow": "Start early",
    }

    result = add_review_notes(date(2025, 10, 6), vault, reflections)

    assert result["daily_note_path"] == str(note_path)
    assert "review_added_at" in result
    assert result["reflections"] == reflections

    # Verify content was appended
    content = note_path.read_text()
    assert "Existing content" in content
    assert "## Review" in content
    assert "What went well:" in content
    assert "Completed all tasks" in content
    assert "What could improve:" in content
    assert "Better time management" in content
    assert "Notes for tomorrow:" in content
    assert "Start early" in content


def test_add_review_notes_partial_reflections(tmp_path):
    """Test adding review notes with only some reflection fields."""
    vault = tmp_path / "vault"
    daily_dir = vault / "daily"
    daily_dir.mkdir(parents=True)

    note_path = daily_dir / "2025-10-06.md"
    note_path.write_text("# Daily Note\n")

    reflections = {"went_well": "Good day"}

    result = add_review_notes(date(2025, 10, 6), vault, reflections)

    content = note_path.read_text()
    assert "What went well:" in content
    assert "Good day" in content
    # Should not have the other sections
    assert "What could improve:" not in content
    assert "Notes for tomorrow:" not in content


def test_add_review_notes_raises_on_missing_note(tmp_path):
    """Test that add_review_notes raises if note doesn't exist."""
    vault = tmp_path / "vault"
    vault.mkdir()

    reflections = {"went_well": "Test"}

    with pytest.raises(DailyNoteNotFoundError):
        add_review_notes(date(2025, 10, 6), vault, reflections)


def test_add_review_notes_multiple_times(tmp_path):
    """Test that multiple review sections can be added (appending)."""
    vault = tmp_path / "vault"
    daily_dir = vault / "daily"
    daily_dir.mkdir(parents=True)

    note_path = daily_dir / "2025-10-06.md"
    note_path.write_text("# Daily Note\n")

    # Add first review
    add_review_notes(date(2025, 10, 6), vault, {"went_well": "First review"})

    # Add second review
    add_review_notes(date(2025, 10, 6), vault, {"went_well": "Second review"})

    content = note_path.read_text()
    # Both reviews should be present
    assert content.count("## Review") == 2
    assert "First review" in content
    assert "Second review" in content


def test_normalize_task():
    """Test _normalize_task helper."""
    task_data = {
        "uuid": "test-uuid",
        "description": "Test task",
        "status": "pending",
        "due": "20251006T000000Z",
        "priority": "H",
        "project": "work",
        "tags": ["important"],
    }

    result = _normalize_task(task_data)

    assert result["uuid"] == "test-uuid"
    assert result["description"] == "Test task"
    assert result["status"] == "pending"
    assert result["priority"] == "H"
    assert result["project"] == "work"
    assert result["tags"] == ["important"]
