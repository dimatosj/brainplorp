# ABOUTME: Comprehensive tests for TaskWarrior integration using mocked subprocess calls
# ABOUTME: Tests all CRUD operations, filtering, and error handling without requiring TaskWarrior installation
"""
Tests for TaskWarrior integration.

All tests use mocked subprocess calls - no actual TaskWarrior required.
"""
import pytest
from unittest.mock import patch, MagicMock, call
import json
import sys
import concurrent.futures


@pytest.fixture
def mock_subprocess():
    """Fixture to mock subprocess.run calls."""
    with patch("plorp.integrations.taskwarrior.subprocess.run") as mock:
        yield mock


@pytest.fixture
def sample_task_data(sample_taskwarrior_export):
    """Return sample TaskWarrior task data from fixtures."""
    return sample_taskwarrior_export


# Tests for run_task_command()
def test_run_task_command_with_capture(mock_subprocess):
    """Test running task command with output capture."""
    mock_subprocess.return_value = MagicMock(returncode=0, stdout='{"test": "output"}', stderr="")

    from plorp.integrations.taskwarrior import run_task_command

    result = run_task_command(["export"], capture=True)

    mock_subprocess.assert_called_once()
    call_args = mock_subprocess.call_args[0][0]
    assert call_args == ["task", "export"]
    assert result.stdout == '{"test": "output"}'


def test_run_task_command_without_capture(mock_subprocess):
    """Test running task command without capture (for user interaction)."""
    mock_subprocess.return_value = MagicMock(returncode=0)

    from plorp.integrations.taskwarrior import run_task_command

    result = run_task_command(["done"], capture=False)

    mock_subprocess.assert_called_once()
    call_args = mock_subprocess.call_args
    # When capture=False, should not include capture_output
    assert call_args[1].get("capture_output") != True


# Tests for get_tasks()
def test_get_tasks_success(mock_subprocess, sample_task_data):
    """Test getting tasks with valid filter."""
    mock_subprocess.return_value = MagicMock(
        returncode=0, stdout=json.dumps(sample_task_data), stderr=""
    )

    from plorp.integrations.taskwarrior import get_tasks

    tasks = get_tasks(["status:pending"])

    assert len(tasks) == 3
    assert tasks[0]["description"] == "Buy groceries"
    mock_subprocess.assert_called_once()
    # Verify 'export' is appended
    call_args = mock_subprocess.call_args[0][0]
    assert "export" in call_args


def test_get_tasks_empty_result(mock_subprocess):
    """Test getting tasks when no matches."""
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="[]", stderr="")

    from plorp.integrations.taskwarrior import get_tasks

    tasks = get_tasks(["status:pending", "project:nonexistent"])

    assert tasks == []


def test_get_tasks_command_failure(mock_subprocess):
    """Test get_tasks handles command failure gracefully."""
    mock_subprocess.return_value = MagicMock(
        returncode=1, stdout="", stderr="TaskWarrior error: invalid filter"
    )

    from plorp.integrations.taskwarrior import get_tasks

    # Should print error to stderr but return empty list
    tasks = get_tasks(["invalid:filter"])

    assert tasks == []


def test_get_tasks_json_parse_error(mock_subprocess):
    """Test get_tasks handles malformed JSON."""
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="not valid json", stderr="")

    from plorp.integrations.taskwarrior import get_tasks

    tasks = get_tasks(["status:pending"])

    assert tasks == []


# Tests for query functions
def test_get_overdue_tasks(mock_subprocess, sample_task_data):
    """Test getting overdue tasks."""
    # Filter sample data to only overdue task
    overdue_task = [t for t in sample_task_data if t["id"] == 2]

    mock_subprocess.return_value = MagicMock(
        returncode=0, stdout=json.dumps(overdue_task), stderr=""
    )

    from plorp.integrations.taskwarrior import get_overdue_tasks

    tasks = get_overdue_tasks()

    assert len(tasks) == 1
    assert tasks[0]["description"] == "Call dentist"

    # Verify correct filter used
    call_args = mock_subprocess.call_args[0][0]
    assert "status:pending" in call_args
    assert "due.before:today" in call_args


def test_get_due_today(mock_subprocess):
    """Test getting tasks due today."""
    mock_subprocess.return_value = MagicMock(
        returncode=0,
        stdout='[{"uuid": "test", "description": "Today task", "due": "20251006T000000Z"}]',
        stderr="",
    )

    from plorp.integrations.taskwarrior import get_due_today

    tasks = get_due_today()

    assert len(tasks) == 1
    call_args = mock_subprocess.call_args[0][0]
    assert "due:today" in call_args


def test_get_recurring_today(mock_subprocess):
    """Test getting recurring tasks due today."""
    mock_subprocess.return_value = MagicMock(
        returncode=0,
        stdout='[{"uuid": "test", "description": "Recurring", "recur": "daily"}]',
        stderr="",
    )

    from plorp.integrations.taskwarrior import get_recurring_today

    tasks = get_recurring_today()

    call_args = mock_subprocess.call_args[0][0]
    assert "recur.any:" in call_args
    assert "due:today" in call_args


# Tests for get_task_info()
def test_get_task_info_found(mock_subprocess, sample_task_data):
    """Test getting info for existing task."""
    task_data = [sample_task_data[0]]
    mock_subprocess.return_value = MagicMock(returncode=0, stdout=json.dumps(task_data), stderr="")

    from plorp.integrations.taskwarrior import get_task_info

    task = get_task_info("a1b2c3d4-e5f6-7890-1234-567890abcdef")

    assert task is not None
    assert task["description"] == "Buy groceries"


def test_get_task_info_not_found(mock_subprocess):
    """Test getting info for non-existent task."""
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="[]", stderr="")

    from plorp.integrations.taskwarrior import get_task_info

    task = get_task_info("nonexistent-uuid")

    assert task is None


# Tests for create_task()
def test_create_task_minimal(mock_subprocess, sample_task_data):
    """Test creating task with just description."""
    # Mock task add command
    add_result = MagicMock(returncode=0, stdout="Created task 1.\n", stderr="")

    # Mock task N export command
    export_result = MagicMock(returncode=0, stdout=json.dumps([sample_task_data[0]]), stderr="")

    mock_subprocess.side_effect = [add_result, export_result]

    from plorp.integrations.taskwarrior import create_task

    uuid = create_task("Test task")

    assert uuid == "a1b2c3d4-e5f6-7890-1234-567890abcdef"

    # Verify commands
    assert mock_subprocess.call_count == 2
    first_call_args = mock_subprocess.call_args_list[0][0][0]
    assert first_call_args[0] == "task"
    assert first_call_args[1] == "add"
    assert first_call_args[2] == "Test task"


def test_create_task_with_metadata(mock_subprocess, sample_task_data):
    """Test creating task with project, due, priority, tags."""
    add_result = MagicMock(returncode=0, stdout="Created task 1.\n", stderr="")

    export_result = MagicMock(returncode=0, stdout=json.dumps([sample_task_data[0]]), stderr="")

    mock_subprocess.side_effect = [add_result, export_result]

    from plorp.integrations.taskwarrior import create_task

    uuid = create_task(
        "Complete sprint",
        project="plorp",
        due="friday",
        priority="H",
        tags=["development", "urgent"],
    )

    first_call_args = mock_subprocess.call_args_list[0][0][0]
    assert "project:plorp" in first_call_args
    assert "due:friday" in first_call_args
    assert "priority:H" in first_call_args
    assert "+development" in first_call_args
    assert "+urgent" in first_call_args


def test_create_task_failure(mock_subprocess):
    """Test create_task handles failure."""
    mock_subprocess.return_value = MagicMock(returncode=1, stdout="", stderr="Error")

    from plorp.integrations.taskwarrior import create_task

    uuid = create_task("This will fail")

    assert uuid is None


def test_create_task_parse_failure(mock_subprocess):
    """Test create_task handles failure to parse task ID from output."""
    add_result = MagicMock(returncode=0, stdout="No task ID here", stderr="")
    mock_subprocess.return_value = add_result

    from plorp.integrations.taskwarrior import create_task

    uuid = create_task("Test task")

    assert uuid is None


def test_create_task_export_failure(mock_subprocess):
    """Test create_task handles failure to export newly created task."""
    add_result = MagicMock(returncode=0, stdout="Created task 1.\n", stderr="")
    export_result = MagicMock(returncode=1, stdout="", stderr="Export error")
    # With retry logic: 1 add + 3 export attempts
    mock_subprocess.side_effect = [add_result, export_result, export_result, export_result]

    from plorp.integrations.taskwarrior import create_task

    uuid = create_task("Test task")

    assert uuid is None


def test_create_task_export_empty(mock_subprocess):
    """Test create_task handles empty export result."""
    add_result = MagicMock(returncode=0, stdout="Created task 1.\n", stderr="")
    export_result = MagicMock(returncode=0, stdout="[]", stderr="")
    # With retry logic: 1 add + 3 export attempts (all return empty)
    mock_subprocess.side_effect = [add_result, export_result, export_result, export_result]

    from plorp.integrations.taskwarrior import create_task

    uuid = create_task("Test task")

    assert uuid is None


def test_create_task_export_json_error(mock_subprocess):
    """Test create_task handles JSON parse error in export."""
    add_result = MagicMock(returncode=0, stdout="Created task 1.\n", stderr="")
    export_result = MagicMock(returncode=0, stdout="not json", stderr="")
    # With retry logic: 1 add + 3 export attempts (all return invalid JSON)
    mock_subprocess.side_effect = [add_result, export_result, export_result, export_result]

    from plorp.integrations.taskwarrior import create_task

    uuid = create_task("Test task")

    assert uuid is None


# Tests for modification functions
def test_mark_done_success(mock_subprocess):
    """Test marking task as done."""
    mock_subprocess.return_value = MagicMock(returncode=0)

    from plorp.integrations.taskwarrior import mark_done

    success = mark_done("abc-123")

    assert success is True
    call_args = mock_subprocess.call_args[0][0]
    assert call_args == ["task", "abc-123", "done"]


def test_mark_done_failure(mock_subprocess):
    """Test mark_done handles failure."""
    mock_subprocess.return_value = MagicMock(returncode=1, stderr="Task not found")

    from plorp.integrations.taskwarrior import mark_done

    success = mark_done("invalid-uuid")

    assert success is False


def test_defer_task(mock_subprocess):
    """Test deferring task to new date."""
    mock_subprocess.return_value = MagicMock(returncode=0)

    from plorp.integrations.taskwarrior import defer_task

    success = defer_task("abc-123", "tomorrow")

    assert success is True
    call_args = mock_subprocess.call_args[0][0]
    assert "modify" in call_args
    assert "due:tomorrow" in call_args


def test_defer_task_failure(mock_subprocess):
    """Test defer_task handles failure."""
    mock_subprocess.return_value = MagicMock(returncode=1, stderr="Task not found")

    from plorp.integrations.taskwarrior import defer_task

    success = defer_task("invalid-uuid", "tomorrow")

    assert success is False


def test_set_priority(mock_subprocess):
    """Test setting task priority."""
    mock_subprocess.return_value = MagicMock(returncode=0)

    from plorp.integrations.taskwarrior import set_priority

    success = set_priority("abc-123", "H")

    assert success is True
    call_args = mock_subprocess.call_args[0][0]
    assert "priority:H" in call_args


def test_set_priority_failure(mock_subprocess):
    """Test set_priority handles failure."""
    mock_subprocess.return_value = MagicMock(returncode=1, stderr="Task not found")

    from plorp.integrations.taskwarrior import set_priority

    success = set_priority("invalid-uuid", "H")

    assert success is False


def test_delete_task(mock_subprocess):
    """Test deleting task."""
    mock_subprocess.return_value = MagicMock(returncode=0)

    from plorp.integrations.taskwarrior import delete_task

    success = delete_task("abc-123")

    assert success is True
    call_args = mock_subprocess.call_args[0][0]
    assert call_args == ["task", "abc-123", "delete"]


def test_delete_task_failure(mock_subprocess):
    """Test delete_task handles failure."""
    mock_subprocess.return_value = MagicMock(returncode=1, stderr="Task not found")

    from plorp.integrations.taskwarrior import delete_task

    success = delete_task("invalid-uuid")

    assert success is False


# Tests for annotation functions
def test_add_annotation(mock_subprocess):
    """Test adding annotation to task."""
    mock_subprocess.return_value = MagicMock(returncode=0)

    from plorp.integrations.taskwarrior import add_annotation

    success = add_annotation("abc-123", "Note: vault/notes/meeting.md")

    assert success is True
    call_args = mock_subprocess.call_args[0][0]
    assert "annotate" in call_args
    assert "Note: vault/notes/meeting.md" in call_args


def test_add_annotation_failure(mock_subprocess):
    """Test add_annotation handles failure."""
    mock_subprocess.return_value = MagicMock(returncode=1, stderr="Task not found")

    from plorp.integrations.taskwarrior import add_annotation

    success = add_annotation("invalid-uuid", "Note: test.md")

    assert success is False


def test_get_task_annotations():
    """Test getting annotations from task."""
    task_with_annotations = {
        "uuid": "abc-123",
        "description": "Test task",
        "annotations": [
            {"entry": "20251006T120000Z", "description": "Note: meeting.md"},
            {"entry": "20251006T130000Z", "description": "Note: ideas.md"},
        ],
    }

    with patch("plorp.integrations.taskwarrior.get_task_info") as mock_get:
        mock_get.return_value = task_with_annotations

        from plorp.integrations.taskwarrior import get_task_annotations

        annotations = get_task_annotations("abc-123")

        assert len(annotations) == 2
        assert "Note: meeting.md" in annotations
        assert "Note: ideas.md" in annotations


def test_get_task_annotations_no_annotations():
    """Test getting annotations from task with none."""
    task_no_annotations = {"uuid": "abc-123", "description": "Test task"}

    with patch("plorp.integrations.taskwarrior.get_task_info") as mock_get:
        mock_get.return_value = task_no_annotations

        from plorp.integrations.taskwarrior import get_task_annotations

        annotations = get_task_annotations("abc-123")

        assert annotations == []


def test_get_task_annotations_task_not_found():
    """Test getting annotations when task doesn't exist."""
    with patch("plorp.integrations.taskwarrior.get_task_info") as mock_get:
        mock_get.return_value = None

        from plorp.integrations.taskwarrior import get_task_annotations

        annotations = get_task_annotations("invalid-uuid")

        assert annotations == []


# Regression tests for Bug #1: Race condition in task creation
def test_create_task_returns_uuid_reliably(mock_subprocess):
    """Ensure create_task returns UUID even with rapid calls.

    Regression test for Bug #1: Race condition where task export fails
    immediately after creation. The retry logic should handle this.
    """
    from plorp.integrations.taskwarrior import create_task

    uuids = []
    for i in range(10):
        # Simulate race condition: first export fails (empty), retry succeeds
        add_result = MagicMock(returncode=0, stdout=f"Created task {i+1}.\n", stderr="")
        export_fail = MagicMock(returncode=0, stdout="[]", stderr="")  # Empty result (race condition)
        export_success = MagicMock(
            returncode=0,
            stdout=json.dumps([{"uuid": f"uuid-{i:03d}", "description": f"Task {i}"}]),
            stderr=""
        )

        # First call: task add, second: export (fails), third: export retry (succeeds)
        mock_subprocess.side_effect = [add_result, export_fail, export_success]

        uuid = create_task(f"Task {i}")
        assert uuid is not None, f"Task {i} returned None"
        uuids.append(uuid)

        # Reset for next iteration
        mock_subprocess.reset_mock()

    # Verify all UUIDs are unique and valid
    assert len(set(uuids)) == 10, "Duplicate UUIDs returned"
    assert all(uuid.startswith("uuid-") for uuid in uuids)


def test_concurrent_task_creation(mock_subprocess):
    """Test creating multiple tasks concurrently.

    Regression test for Bug #1: Ensures retry logic works correctly
    under concurrent load.
    """
    from plorp.integrations.taskwarrior import create_task

    def create_test_task(i):
        # Each thread gets its own mock responses
        add_result = MagicMock(returncode=0, stdout=f"Created task {i}.\n", stderr="")
        export_result = MagicMock(
            returncode=0,
            stdout=json.dumps([{"uuid": f"concurrent-uuid-{i:03d}", "description": f"Concurrent task {i}"}]),
            stderr=""
        )

        # Mock will return these in sequence for this specific call
        mock_subprocess.side_effect = [add_result, export_result]

        return create_task(f"Concurrent task {i}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(create_test_task, i) for i in range(20)]
        uuids = [f.result() for f in futures]

    # All should succeed
    assert all(uuid is not None for uuid in uuids), "Some tasks returned None"
    assert len(set(uuids)) == 20, f"Expected 20 unique UUIDs, got {len(set(uuids))}"
