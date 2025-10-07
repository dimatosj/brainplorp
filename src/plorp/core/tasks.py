"""
Core task operations logic.

Implements pure functions for task manipulation (complete, defer, drop, priority).
No I/O decisions - returns structured data for callers to format.
"""

from datetime import date, datetime
from typing import Dict

from plorp.core.types import TaskCompleteResult, TaskDeferResult, TaskDropResult, TaskPriorityResult
from plorp.core.exceptions import TaskNotFoundError
from plorp.integrations.taskwarrior import (
    get_task_info,
    mark_done,
    defer_task as tw_defer_task,
    delete_task,
    set_priority as tw_set_priority,
)


def mark_completed(uuid: str) -> TaskCompleteResult:
    """
    Mark task as completed in TaskWarrior.

    Args:
        uuid: Task UUID

    Returns:
        TaskCompleteResult with confirmation

    Raises:
        TaskNotFoundError: Task doesn't exist
    """
    # Verify task exists
    task = get_task_info(uuid)
    if not task:
        raise TaskNotFoundError(uuid)

    description = task["description"]

    # Mark done
    success = mark_done(uuid)
    if not success:
        raise RuntimeError(f"Failed to mark task done: {uuid}")

    return {
        "uuid": uuid,
        "description": description,
        "completed_at": datetime.now().isoformat(),
    }


def defer_task(uuid: str, new_due: date) -> TaskDeferResult:
    """
    Defer task to new date.

    Args:
        uuid: Task UUID
        new_due: New due date

    Returns:
        TaskDeferResult with confirmation

    Raises:
        TaskNotFoundError: Task doesn't exist
    """
    # Verify task exists
    task = get_task_info(uuid)
    if not task:
        raise TaskNotFoundError(uuid)

    description = task["description"]
    old_due = task.get("due")

    # Update due date - TaskWarrior accepts YYYY-MM-DD format
    success = tw_defer_task(uuid, str(new_due))
    if not success:
        raise RuntimeError(f"Failed to defer task: {uuid}")

    return {
        "uuid": uuid,
        "description": description,
        "old_due": old_due,
        "new_due": str(new_due),
    }


def drop_task(uuid: str) -> TaskDropResult:
    """
    Drop/delete task from TaskWarrior.

    Args:
        uuid: Task UUID

    Returns:
        TaskDropResult with confirmation

    Raises:
        TaskNotFoundError: Task doesn't exist
    """
    # Verify task exists
    task = get_task_info(uuid)
    if not task:
        raise TaskNotFoundError(uuid)

    description = task["description"]

    # Delete task
    success = delete_task(uuid)
    if not success:
        raise RuntimeError(f"Failed to delete task: {uuid}")

    return {
        "uuid": uuid,
        "description": description,
        "deleted_at": datetime.now().isoformat(),
    }


def set_priority(uuid: str, priority: str) -> TaskPriorityResult:
    """
    Set task priority.

    Args:
        uuid: Task UUID
        priority: Priority (H, M, L, or empty string for none)

    Returns:
        TaskPriorityResult with confirmation

    Raises:
        TaskNotFoundError: Task doesn't exist
        ValueError: Invalid priority value
    """
    if priority not in ["H", "M", "L", ""]:
        raise ValueError(f"Invalid priority: {priority}. Must be H, M, L, or empty string.")

    # Verify task exists
    task = get_task_info(uuid)
    if not task:
        raise TaskNotFoundError(uuid)

    # Set priority
    success = tw_set_priority(uuid, priority if priority else "")
    if not success:
        raise RuntimeError(f"Failed to set priority for task: {uuid}")

    return {
        "uuid": uuid,
        "description": task["description"],
        "priority": priority if priority else None,
    }
