"""
Tests for plorp.core.daily module.

Tests daily note generation workflow.
"""

import pytest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from plorp.core.daily import (
    start_day,
    _normalize_task,
    _is_overdue,
    _is_due_today,
    _is_recurring,
    _format_daily_note,
    _format_task_checkbox,
)
from plorp.core.exceptions import VaultNotFoundError, DailyNoteExistsError


def test_start_day_creates_note(tmp_path):
    """Test that start_day creates daily note with correct structure."""
    vault = tmp_path / "vault"
    vault.mkdir()

    with patch("plorp.core.daily.get_tasks") as mock_tasks:
        mock_tasks.return_value = [
            {
                "uuid": "abc-123",
                "description": "Test task",
                "status": "pending",
                "due": "20251006T000000Z",
                "priority": "H",
                "project": "work",
                "tags": ["important"],
            }
        ]

        result = start_day(date(2025, 10, 6), vault)

        # Assert structured return
        assert result["note_path"].endswith("2025-10-06.md")
        assert result["date"] == "2025-10-06"
        assert result["summary"]["total_count"] == 1
        assert result["summary"]["due_today_count"] == 1
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["uuid"] == "abc-123"

        # Assert file created
        note_path = Path(result["note_path"])
        assert note_path.exists()
        content = note_path.read_text()
        assert "# Daily Note - 2025-10-06" in content
        assert "Test task" in content
        assert "uuid: abc-123" in content


def test_start_day_raises_on_existing_note(tmp_path):
    """Test that start_day raises error if note already exists."""
    vault = tmp_path / "vault"
    vault.mkdir()

    daily_dir = vault / "daily"
    daily_dir.mkdir()

    # Create existing note
    existing_note = daily_dir / "2025-10-06.md"
    existing_note.write_text("# Existing")

    from plorp.core.exceptions import DailyNoteExistsError

    with pytest.raises(DailyNoteExistsError) as exc:
        start_day(date(2025, 10, 6), vault)

    assert exc.value.date == "2025-10-06"
    assert str(existing_note) in exc.value.note_path


def test_start_day_raises_on_missing_vault(tmp_path):
    """Test that start_day raises error if vault doesn't exist."""
    missing_vault = tmp_path / "nonexistent"

    with pytest.raises(VaultNotFoundError) as exc:
        start_day(date(2025, 10, 6), missing_vault)

    assert str(missing_vault) in exc.value.vault_path


def test_start_day_empty_task_list(tmp_path):
    """Test start_day with no tasks."""
    vault = tmp_path / "vault"
    vault.mkdir()

    with patch("plorp.core.daily.get_tasks") as mock_tasks:
        mock_tasks.return_value = []

        result = start_day(date(2025, 10, 6), vault)

        assert result["summary"]["total_count"] == 0
        assert len(result["tasks"]) == 0

        note_path = Path(result["note_path"])
        content = note_path.read_text()
        assert "No tasks scheduled for today" in content


def test_start_day_categorizes_overdue_tasks(tmp_path):
    """Test that overdue tasks are correctly categorized."""
    vault = tmp_path / "vault"
    vault.mkdir()

    with patch("plorp.core.daily.get_tasks") as mock_tasks:
        mock_tasks.return_value = [
            {
                "uuid": "overdue-1",
                "description": "Overdue task",
                "status": "pending",
                "due": "20251001T000000Z",  # 5 days before
            }
        ]

        result = start_day(date(2025, 10, 6), vault)

        assert result["summary"]["overdue_count"] == 1
        assert result["summary"]["due_today_count"] == 0
        assert result["summary"]["total_count"] == 1

        note_path = Path(result["note_path"])
        content = note_path.read_text()
        assert "Overdue Tasks" in content


def test_start_day_recurring_only_when_due(tmp_path):
    """Test that recurring tasks only shown when due (Q24 decision)."""
    vault = tmp_path / "vault"
    vault.mkdir()

    with patch("plorp.core.daily.get_tasks") as mock_tasks:
        # Recurring task not due today should not appear
        mock_tasks.return_value = [
            {
                "uuid": "recur-1",
                "description": "Recurring task",
                "status": "pending",
                "recur": "weekly",
                "due": "20251010T000000Z",  # Due in the future
            }
        ]

        result = start_day(date(2025, 10, 6), vault)

        assert result["summary"]["recurring_count"] == 0
        assert result["summary"]["total_count"] == 0


def test_normalize_task():
    """Test _normalize_task helper."""
    task_data = {
        "uuid": "test-uuid",
        "description": "Test description",
        "status": "pending",
        "due": "20251006T000000Z",
        "priority": "H",
        "project": "work",
        "tags": ["important", "urgent"],
    }

    result = _normalize_task(task_data)

    assert result["uuid"] == "test-uuid"
    assert result["description"] == "Test description"
    assert result["status"] == "pending"
    assert result["priority"] == "H"
    assert result["project"] == "work"
    assert result["tags"] == ["important", "urgent"]


def test_is_overdue():
    """Test _is_overdue helper."""
    # Task due yesterday
    task = {"due": "20251005T000000Z"}
    assert _is_overdue(task, date(2025, 10, 6)) is True

    # Task due today (not overdue)
    task = {"due": "20251006T000000Z"}
    assert _is_overdue(task, date(2025, 10, 6)) is False

    # Task with no due date
    task = {}
    assert _is_overdue(task, date(2025, 10, 6)) is False


def test_is_due_today():
    """Test _is_due_today helper."""
    # Task due today
    task = {"due": "20251006T000000Z"}
    assert _is_due_today(task, date(2025, 10, 6)) is True

    # Task due yesterday
    task = {"due": "20251005T000000Z"}
    assert _is_due_today(task, date(2025, 10, 6)) is False

    # Task with no due date
    task = {}
    assert _is_due_today(task, date(2025, 10, 6)) is False


def test_is_recurring():
    """Test _is_recurring helper."""
    # Recurring task
    task = {"recur": "weekly"}
    assert _is_recurring(task) is True

    # Non-recurring task
    task = {}
    assert _is_recurring(task) is False


def test_format_task_checkbox_with_full_metadata():
    """Test _format_task_checkbox with all metadata (Q15 decision)."""
    task = {
        "uuid": "abc-123",
        "description": "Test task",
        "status": "pending",
        "due": "20251006T000000Z",
        "priority": "H",
        "project": "work",
        "tags": ["important", "urgent"],
    }

    result = _format_task_checkbox(task)

    assert result.startswith("- [ ] Test task")
    assert "project: work" in result
    assert "due:" in result
    assert "priority: H" in result
    assert "tags: important, urgent" in result
    assert "uuid: abc-123" in result


def test_format_task_checkbox_minimal():
    """Test _format_task_checkbox with minimal metadata."""
    task = {
        "uuid": "abc-123",
        "description": "Simple task",
        "status": "pending",
        "due": None,
        "priority": "",
        "project": None,
        "tags": [],
    }

    result = _format_task_checkbox(task)

    assert result == "- [ ] Simple task (uuid: abc-123)"


def test_format_daily_note():
    """Test _format_daily_note helper."""
    overdue = [
        {
            "uuid": "o1",
            "description": "Overdue",
            "status": "pending",
            "due": None,
            "priority": "",
            "project": None,
            "tags": [],
        }
    ]
    due_today = [
        {
            "uuid": "d1",
            "description": "Due today",
            "status": "pending",
            "due": None,
            "priority": "",
            "project": None,
            "tags": [],
        }
    ]
    recurring = []

    content = _format_daily_note(date(2025, 10, 6), overdue, due_today, recurring)

    assert "# Daily Note - 2025-10-06" in content
    assert "Overdue Tasks" in content
    assert "Due Today" in content
    assert "Overdue" in content
    assert "Due today" in content
