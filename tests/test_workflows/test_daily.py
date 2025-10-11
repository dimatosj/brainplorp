# ABOUTME: Tests for daily workflow - validates daily note generation and task formatting
# ABOUTME: Mocks TaskWarrior integration and uses fixtures to test markdown generation
"""Tests for daily workflow."""
import pytest
from pathlib import Path
from datetime import date
from unittest.mock import patch, MagicMock

from brainplorp.workflows.daily import (
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


@patch("brainplorp.workflows.daily.get_overdue_tasks")
@patch("brainplorp.workflows.daily.get_due_today")
@patch("brainplorp.workflows.daily.get_recurring_today")
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


@patch("brainplorp.workflows.daily.get_overdue_tasks")
@patch("brainplorp.workflows.daily.get_due_today")
@patch("brainplorp.workflows.daily.get_recurring_today")
def test_start_creates_directory(mock_recurring, mock_due, mock_overdue, mock_config):
    """Test start() creates daily directory if not exists."""
    mock_overdue.return_value = []
    mock_due.return_value = []
    mock_recurring.return_value = []

    daily_dir = Path(mock_config["vault_path"]) / "daily"
    assert not daily_dir.exists()

    start(mock_config)

    assert daily_dir.exists()


@patch("brainplorp.workflows.daily.get_overdue_tasks")
@patch("brainplorp.workflows.daily.get_due_today")
@patch("brainplorp.workflows.daily.get_recurring_today")
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


@patch("brainplorp.workflows.daily.get_overdue_tasks")
@patch("brainplorp.workflows.daily.get_due_today")
@patch("brainplorp.workflows.daily.get_recurring_today")
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


# ===== Sprint 3: Review Workflow Tests =====


@pytest.fixture
def daily_note_with_uncompleted_tasks(tmp_path):
    """Create a daily note with uncompleted tasks."""
    vault = tmp_path / "vault"
    daily_dir = vault / "daily"
    daily_dir.mkdir(parents=True)

    note_path = daily_dir / "2025-10-06.md"
    content = """---
date: 2025-10-06
type: daily
---

# Daily Note - October 06, 2025

## Tasks

- [ ] Buy groceries (project: home, uuid: abc-123)
- [x] Call dentist (project: health, uuid: def-456)
- [ ] Write report (due: 2025-10-07, uuid: ghi-789)

---

## Notes

Made good progress today.

---

## Review Section

<!-- Auto-populated by `plorp review` -->
"""
    note_path.write_text(content)

    return vault, note_path


@patch("brainplorp.utils.prompts.prompt_choice")
@patch("brainplorp.integrations.taskwarrior.mark_done")
@patch("brainplorp.integrations.taskwarrior.get_task_info")
def test_review_mark_task_done(
    mock_get_task,
    mock_mark_done,
    mock_prompt,
    daily_note_with_uncompleted_tasks,
    monkeypatch,
    capsys,
):
    """Test review workflow marking task as done."""
    from datetime import date
    from brainplorp.workflows.daily import review

    vault, note_path = daily_note_with_uncompleted_tasks

    # Mock date.today()
    mock_date = type("MockDate", (), {"today": staticmethod(lambda: date(2025, 10, 6))})
    monkeypatch.setattr("plorp.workflows.daily.date", mock_date)

    # Mock task info
    mock_get_task.side_effect = [
        {"uuid": "abc-123", "description": "Buy groceries", "project": "home"},
        {"uuid": "ghi-789", "description": "Write report", "due": "20251007T000000Z"},
    ]

    # Mock user choosing "Mark done" for both tasks
    mock_prompt.side_effect = [0, 0]  # Choice 0 = Mark done

    # Mock mark_done success
    mock_mark_done.return_value = True

    config = {"vault_path": str(vault)}

    review(config)

    # Verify mark_done called twice
    assert mock_mark_done.call_count == 2

    # Verify review section appended (Q4: append, not replace)
    updated_content = note_path.read_text()
    assert "## Review Section" in updated_content
    assert "✅ Buy groceries" in updated_content
    assert "✅ Write report" in updated_content
    assert "Review completed:" in updated_content


@patch("brainplorp.utils.prompts.prompt_choice")
@patch("brainplorp.integrations.taskwarrior.defer_task")
@patch("brainplorp.integrations.taskwarrior.get_task_info")
def test_review_defer_task(
    mock_get_task, mock_defer, mock_prompt, daily_note_with_uncompleted_tasks, monkeypatch, capsys
):
    """Test review workflow deferring task."""
    from datetime import date
    from brainplorp.workflows.daily import review

    vault, note_path = daily_note_with_uncompleted_tasks

    mock_date = type("MockDate", (), {"today": staticmethod(lambda: date(2025, 10, 6))})
    monkeypatch.setattr("plorp.workflows.daily.date", mock_date)

    mock_get_task.return_value = {
        "uuid": "abc-123",
        "description": "Buy groceries",
        "project": "home",
    }

    # Mock user choosing "Defer to tomorrow" then "Quit"
    mock_prompt.side_effect = [1, 6]  # 1 = Defer to tomorrow, 6 = Quit

    mock_defer.return_value = True

    config = {"vault_path": str(vault)}

    review(config)

    # Verify defer_task called
    mock_defer.assert_called_once_with("abc-123", "tomorrow")

    # Verify review section appended
    updated_content = note_path.read_text()
    assert "📅 Buy groceries → tomorrow" in updated_content


@patch("brainplorp.integrations.taskwarrior.get_task_info")
def test_review_task_not_found(
    mock_get_task, daily_note_with_uncompleted_tasks, monkeypatch, capsys
):
    """Test review when task not found in TaskWarrior (Q3 answer)."""
    from datetime import date
    from brainplorp.workflows.daily import review

    vault, note_path = daily_note_with_uncompleted_tasks

    mock_date = type("MockDate", (), {"today": staticmethod(lambda: date(2025, 10, 6))})
    monkeypatch.setattr("plorp.workflows.daily.date", mock_date)

    # First task not found, second task exists
    mock_get_task.side_effect = [
        None,  # abc-123 not found
        {"uuid": "ghi-789", "description": "Write report"},
    ]

    config = {"vault_path": str(vault)}

    # Need to mock prompt_choice to quit after first task
    with patch("brainplorp.utils.prompts.prompt_choice", return_value=6):  # Quit
        review(config)

    # Per Q3 answer: warning printed, added to decisions, inline comment in note
    captured = capsys.readouterr()
    assert "⚠️" in captured.out and "not found" in captured.out

    updated_content = note_path.read_text()
    # Should have warning in review section
    assert "⚠️" in updated_content and "Buy groceries" in updated_content


def test_review_no_daily_note(tmp_path, capsys, monkeypatch):
    """Test review when no daily note exists."""
    from datetime import date
    from brainplorp.workflows.daily import review

    vault = tmp_path / "vault"
    vault.mkdir()

    mock_date = type("MockDate", (), {"today": staticmethod(lambda: date(2025, 10, 6))})
    monkeypatch.setattr("plorp.workflows.daily.date", mock_date)

    config = {"vault_path": str(vault)}

    review(config)

    captured = capsys.readouterr()
    assert "❌ No daily note found" in captured.out
    assert "plorp start" in captured.out


def test_review_all_tasks_complete(tmp_path, capsys, monkeypatch):
    """Test review when all tasks are checked."""
    from datetime import date
    from brainplorp.workflows.daily import review

    vault = tmp_path / "vault"
    daily_dir = vault / "daily"
    daily_dir.mkdir(parents=True)

    note_path = daily_dir / "2025-10-06.md"
    content = """---
date: 2025-10-06
---

# Daily Note

- [x] All tasks (uuid: abc-123)
- [x] Are complete (uuid: def-456)
"""
    note_path.write_text(content)

    mock_date = type("MockDate", (), {"today": staticmethod(lambda: date(2025, 10, 6))})
    monkeypatch.setattr("plorp.workflows.daily.date", mock_date)

    config = {"vault_path": str(vault)}

    review(config)

    captured = capsys.readouterr()
    assert "✅ All tasks completed" in captured.out


def test_append_review_section_new(tmp_path):
    """Test appending review section to note without one."""
    from brainplorp.workflows.daily import append_review_section

    note = tmp_path / "daily.md"
    content = """# Daily Note

## Tasks

Some tasks here
"""
    note.write_text(content)

    decisions = ["✅ Task 1 done", "📅 Task 2 deferred"]
    append_review_section(note, decisions)

    updated = note.read_text()
    assert "## Review Section" in updated
    assert "✅ Task 1 done" in updated
    assert "📅 Task 2 deferred" in updated


def test_append_review_section_appends_to_existing(tmp_path):
    """Test appending to existing review section (Q4 answer)."""
    from brainplorp.workflows.daily import append_review_section

    note = tmp_path / "daily.md"
    content = """# Daily Note

## Review Section

**Review completed:** 2025-10-06 10:00

- ✅ Morning task

"""
    note.write_text(content)

    decisions = ["✅ Evening task"]
    append_review_section(note, decisions)

    updated = note.read_text()
    # Per Q4: Should APPEND, not replace
    assert "✅ Morning task" in updated
    assert "✅ Evening task" in updated
    assert updated.count("Review completed:") == 2


@patch("brainplorp.utils.prompts.prompt")
@patch("brainplorp.utils.prompts.prompt_choice")
@patch("brainplorp.integrations.taskwarrior.set_priority")
@patch("brainplorp.integrations.taskwarrior.get_task_info")
def test_review_change_priority_with_validation(
    mock_get_task,
    mock_set_priority,
    mock_choice,
    mock_user_prompt,
    daily_note_with_uncompleted_tasks,
    monkeypatch,
    capsys,
):
    """Test review priority change with validation (Q5 answer)."""
    from datetime import date
    from brainplorp.workflows.daily import review

    vault, note_path = daily_note_with_uncompleted_tasks

    mock_date = type("MockDate", (), {"today": staticmethod(lambda: date(2025, 10, 6))})
    monkeypatch.setattr("plorp.workflows.daily.date", mock_date)

    mock_get_task.return_value = {"uuid": "abc-123", "description": "Buy groceries"}

    # User chooses "Change priority" then "Quit"
    mock_choice.side_effect = [3, 6]  # 3 = Change priority, 6 = Quit

    # Per Q5: should validate input - mock returns valid priority
    mock_user_prompt.return_value = "H"
    mock_set_priority.return_value = True

    config = {"vault_path": str(vault)}

    review(config)

    # Verify set_priority called with uppercase H
    mock_set_priority.assert_called_once_with("abc-123", "H")
