# ABOUTME: Tests for daily workflow - validates daily note generation and task formatting
# ABOUTME: Mocks TaskWarrior integration and uses fixtures to test markdown generation
"""Tests for daily workflow."""
import pytest
from pathlib import Path
from datetime import date
from unittest.mock import patch, MagicMock

from plorp.workflows.daily import (
    start,
    generate_daily_note_content,
    format_task_checkbox,
    review,
)


@pytest.fixture
def mock_config(tmp_path):
    """Fixture for test configuration."""
    vault = tmp_path / "vault"
    vault.mkdir()
    return {
        "vault_path": str(vault),
        "taskwarrior_data": "~/.task",
    }


@pytest.fixture
def sample_tasks(sample_taskwarrior_export):
    """Sample tasks from fixture."""
    return sample_taskwarrior_export


def test_format_task_checkbox_minimal():
    """Test formatting task with minimal metadata."""
    task = {"description": "Simple task", "uuid": "abc-123"}

    result = format_task_checkbox(task)

    assert "- [ ] Simple task" in result
    assert "uuid: abc-123" in result


def test_format_task_checkbox_full():
    """Test formatting task with all metadata."""
    task = {
        "description": "Complete task",
        "uuid": "abc-123",
        "project": "plorp",
        "due": "20251006T120000Z",
        "priority": "H",
        "recur": "daily",
    }

    result = format_task_checkbox(task)

    assert "- [ ] Complete task" in result
    assert "uuid: abc-123" in result
    assert "project: plorp" in result
    assert "due: 2025-10-06" in result
    assert "priority: H" in result
    assert "recurring: daily" in result


def test_generate_daily_note_content_empty():
    """Test generating note with no tasks."""
    today = date(2025, 10, 6)

    content = generate_daily_note_content(today, [], [], [])

    assert "---" in content  # Has front matter
    assert "date: 2025-10-06" in content
    assert "type: daily" in content
    assert "# Daily Note - October 06, 2025" in content
    assert "## Notes" in content
    assert "## Review Section" in content


def test_generate_daily_note_content_with_tasks(sample_tasks):
    """Test generating note with tasks."""
    today = date(2025, 10, 6)
    overdue = [sample_tasks[1]]  # Call dentist
    due_today = [sample_tasks[0]]  # Buy groceries
    recurring = [sample_tasks[2]]  # Morning meditation

    content = generate_daily_note_content(today, overdue, due_today, recurring)

    assert "## Overdue (1)" in content
    assert "Call dentist" in content

    assert "## Due Today (1)" in content
    assert "Buy groceries" in content

    assert "## Recurring" in content
    assert "Morning meditation" in content


@patch("plorp.workflows.daily.get_overdue_tasks")
@patch("plorp.workflows.daily.get_due_today")
@patch("plorp.workflows.daily.get_recurring_today")
def test_start_creates_note(
    mock_recurring, mock_due, mock_overdue, mock_config, sample_tasks, capsys
):
    """Test start() creates daily note file."""
    # Mock TaskWarrior responses
    mock_overdue.return_value = [sample_tasks[1]]
    mock_due.return_value = [sample_tasks[0]]
    mock_recurring.return_value = [sample_tasks[2]]

    note_path = start(mock_config)

    # Verify file created
    assert note_path.exists()
    assert note_path.name == f"{date.today().strftime('%Y-%m-%d')}.md"

    # Verify content
    content = note_path.read_text()
    assert "Call dentist" in content
    assert "Buy groceries" in content
    assert "Morning meditation" in content

    # Verify output
    captured = capsys.readouterr()
    assert "✅ Daily note generated" in captured.out
    assert "1 overdue tasks" in captured.out
    assert "1 due today" in captured.out
    assert "1 recurring tasks" in captured.out


@patch("plorp.workflows.daily.get_overdue_tasks")
@patch("plorp.workflows.daily.get_due_today")
@patch("plorp.workflows.daily.get_recurring_today")
def test_start_creates_directory(mock_recurring, mock_due, mock_overdue, mock_config):
    """Test start() creates daily directory if not exists."""
    mock_overdue.return_value = []
    mock_due.return_value = []
    mock_recurring.return_value = []

    daily_dir = Path(mock_config["vault_path"]) / "daily"
    assert not daily_dir.exists()

    start(mock_config)

    assert daily_dir.exists()


@patch("plorp.workflows.daily.get_overdue_tasks")
@patch("plorp.workflows.daily.get_due_today")
@patch("plorp.workflows.daily.get_recurring_today")
def test_start_refuses_to_overwrite(mock_recurring, mock_due, mock_overdue, mock_config, capsys):
    """Test start() refuses to overwrite existing daily note."""
    mock_overdue.return_value = []
    mock_due.return_value = []
    mock_recurring.return_value = []

    # Create existing daily note
    daily_dir = Path(mock_config["vault_path"]) / "daily"
    daily_dir.mkdir()
    existing_note = daily_dir / f"{date.today().strftime('%Y-%m-%d')}.md"
    existing_note.write_text("Existing content")

    # start() should raise FileExistsError
    with pytest.raises(FileExistsError) as exc_info:
        start(mock_config)

    assert "already exists" in str(exc_info.value).lower()


@patch("plorp.workflows.daily.get_overdue_tasks")
@patch("plorp.workflows.daily.get_due_today")
@patch("plorp.workflows.daily.get_recurring_today")
def test_start_warns_on_no_tasks(mock_recurring, mock_due, mock_overdue, mock_config, capsys):
    """Test start() warns when TaskWarrior returns no tasks."""
    # All empty - could indicate TW error
    mock_overdue.return_value = []
    mock_due.return_value = []
    mock_recurring.return_value = []

    note_path = start(mock_config)

    # Should still create file
    assert note_path.exists()

    # Should warn
    captured = capsys.readouterr()
    assert "⚠️" in captured.err or "Warning" in captured.err

    # Content should mention no tasks
    content = note_path.read_text()
    assert "No tasks found" in content or "_No tasks" in content


def test_review_stub(mock_config, capsys):
    """Test review() shows not implemented message."""
    review(mock_config)

    captured = capsys.readouterr()
    assert "not yet implemented" in captured.out
    assert "Sprint 3" in captured.out


def test_format_task_checkbox_no_optional_fields():
    """Test task formatting with no optional fields."""
    task = {"description": "Task without optional fields", "uuid": "xyz-789"}

    result = format_task_checkbox(task)

    # Should only have description and uuid
    assert "- [ ] Task without optional fields" in result
    assert "uuid: xyz-789" in result
    # Should not have these fields
    assert "project:" not in result
    assert "due:" not in result
    assert "priority:" not in result
