"""
Tests for plorp.core.tasks module.

Tests task operation functions.
"""

import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from plorp.core.tasks import mark_completed, defer_task, drop_task, set_priority
from plorp.core.exceptions import TaskNotFoundError


def test_mark_completed_success():
    """Test marking a task as completed."""
    with patch("plorp.core.tasks.get_task_info") as mock_get_task:
        with patch("plorp.core.tasks.mark_done") as mock_mark_done:
            mock_get_task.return_value = {
                "uuid": "abc-123",
                "description": "Test task",
                "status": "pending",
            }
            mock_mark_done.return_value = True

            result = mark_completed("abc-123")

            assert result["uuid"] == "abc-123"
            assert result["description"] == "Test task"
            assert "completed_at" in result
            mock_mark_done.assert_called_once_with("abc-123")


def test_mark_completed_task_not_found():
    """Test marking non-existent task raises error."""
    with patch("plorp.core.tasks.get_task_info") as mock_get_task:
        mock_get_task.return_value = None

        with pytest.raises(TaskNotFoundError) as exc:
            mark_completed("nonexistent-123")

        assert exc.value.uuid == "nonexistent-123"


def test_mark_completed_failure():
    """Test handling TaskWarrior failure."""
    with patch("plorp.core.tasks.get_task_info") as mock_get_task:
        with patch("plorp.core.tasks.mark_done") as mock_mark_done:
            mock_get_task.return_value = {
                "uuid": "abc-123",
                "description": "Test task",
            }
            mock_mark_done.return_value = False

            with pytest.raises(RuntimeError, match="Failed to mark task done"):
                mark_completed("abc-123")


def test_defer_task_success():
    """Test deferring a task to new date."""
    with patch("plorp.core.tasks.get_task_info") as mock_get_task:
        with patch("plorp.core.tasks.tw_defer_task") as mock_defer:
            mock_get_task.return_value = {
                "uuid": "abc-123",
                "description": "Test task",
                "due": "20251006T000000Z",
            }
            mock_defer.return_value = True

            result = defer_task("abc-123", date(2025, 10, 10))

            assert result["uuid"] == "abc-123"
            assert result["description"] == "Test task"
            assert result["old_due"] == "20251006T000000Z"
            assert result["new_due"] == "2025-10-10"
            mock_defer.assert_called_once_with("abc-123", "2025-10-10")


def test_defer_task_no_original_due():
    """Test deferring task that had no due date."""
    with patch("plorp.core.tasks.get_task_info") as mock_get_task:
        with patch("plorp.core.tasks.tw_defer_task") as mock_defer:
            mock_get_task.return_value = {
                "uuid": "abc-123",
                "description": "Test task",
                # No 'due' field
            }
            mock_defer.return_value = True

            result = defer_task("abc-123", date(2025, 10, 10))

            assert result["old_due"] is None
            assert result["new_due"] == "2025-10-10"


def test_defer_task_not_found():
    """Test deferring non-existent task raises error."""
    with patch("plorp.core.tasks.get_task_info") as mock_get_task:
        mock_get_task.return_value = None

        with pytest.raises(TaskNotFoundError):
            defer_task("nonexistent-123", date(2025, 10, 10))


def test_defer_task_failure():
    """Test handling TaskWarrior failure."""
    with patch("plorp.core.tasks.get_task_info") as mock_get_task:
        with patch("plorp.core.tasks.tw_defer_task") as mock_defer:
            mock_get_task.return_value = {
                "uuid": "abc-123",
                "description": "Test task",
            }
            mock_defer.return_value = False

            with pytest.raises(RuntimeError, match="Failed to defer task"):
                defer_task("abc-123", date(2025, 10, 10))


def test_drop_task_success():
    """Test dropping/deleting a task."""
    with patch("plorp.core.tasks.get_task_info") as mock_get_task:
        with patch("plorp.core.tasks.delete_task") as mock_delete:
            mock_get_task.return_value = {
                "uuid": "abc-123",
                "description": "Test task",
            }
            mock_delete.return_value = True

            result = drop_task("abc-123")

            assert result["uuid"] == "abc-123"
            assert result["description"] == "Test task"
            assert "deleted_at" in result
            mock_delete.assert_called_once_with("abc-123")


def test_drop_task_not_found():
    """Test dropping non-existent task raises error."""
    with patch("plorp.core.tasks.get_task_info") as mock_get_task:
        mock_get_task.return_value = None

        with pytest.raises(TaskNotFoundError):
            drop_task("nonexistent-123")


def test_drop_task_failure():
    """Test handling TaskWarrior failure."""
    with patch("plorp.core.tasks.get_task_info") as mock_get_task:
        with patch("plorp.core.tasks.delete_task") as mock_delete:
            mock_get_task.return_value = {
                "uuid": "abc-123",
                "description": "Test task",
            }
            mock_delete.return_value = False

            with pytest.raises(RuntimeError, match="Failed to delete task"):
                drop_task("abc-123")


def test_set_priority_success():
    """Test setting task priority."""
    with patch("plorp.core.tasks.get_task_info") as mock_get_task:
        with patch("plorp.core.tasks.tw_set_priority") as mock_set_priority:
            mock_get_task.return_value = {
                "uuid": "abc-123",
                "description": "Test task",
            }
            mock_set_priority.return_value = True

            result = set_priority("abc-123", "H")

            assert result["uuid"] == "abc-123"
            assert result["description"] == "Test task"
            assert result["priority"] == "H"
            mock_set_priority.assert_called_once_with("abc-123", "H")


def test_set_priority_to_none():
    """Test removing task priority (empty string)."""
    with patch("plorp.core.tasks.get_task_info") as mock_get_task:
        with patch("plorp.core.tasks.tw_set_priority") as mock_set_priority:
            mock_get_task.return_value = {
                "uuid": "abc-123",
                "description": "Test task",
            }
            mock_set_priority.return_value = True

            result = set_priority("abc-123", "")

            assert result["priority"] is None
            mock_set_priority.assert_called_once_with("abc-123", "")


def test_set_priority_invalid_value():
    """Test setting invalid priority raises ValueError."""
    with pytest.raises(ValueError, match="Invalid priority"):
        set_priority("abc-123", "X")


def test_set_priority_task_not_found():
    """Test setting priority on non-existent task raises error."""
    with patch("plorp.core.tasks.get_task_info") as mock_get_task:
        mock_get_task.return_value = None

        with pytest.raises(TaskNotFoundError):
            set_priority("nonexistent-123", "H")


def test_set_priority_failure():
    """Test handling TaskWarrior failure."""
    with patch("plorp.core.tasks.get_task_info") as mock_get_task:
        with patch("plorp.core.tasks.tw_set_priority") as mock_set_priority:
            mock_get_task.return_value = {
                "uuid": "abc-123",
                "description": "Test task",
            }
            mock_set_priority.return_value = False

            with pytest.raises(RuntimeError, match="Failed to set priority"):
                set_priority("abc-123", "H")


def test_set_priority_valid_values():
    """Test all valid priority values."""
    valid_priorities = ["H", "M", "L", ""]

    with patch("plorp.core.tasks.get_task_info") as mock_get_task:
        with patch("plorp.core.tasks.tw_set_priority") as mock_set_priority:
            mock_get_task.return_value = {
                "uuid": "abc-123",
                "description": "Test task",
            }
            mock_set_priority.return_value = True

            for priority in valid_priorities:
                result = set_priority("abc-123", priority)
                assert result["priority"] == (priority if priority else None)
