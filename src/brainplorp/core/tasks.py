"""
Core task operations logic.

Implements pure functions for task manipulation (complete, defer, drop, priority).
No I/O decisions - returns structured data for callers to format.
"""

from datetime import date, datetime
from pathlib import Path
from typing import Dict, Optional

from brainplorp.core.types import TaskCompleteResult, TaskDeferResult, TaskDropResult, TaskPriorityResult
from brainplorp.core.exceptions import TaskNotFoundError
from brainplorp.integrations.taskwarrior import (
    get_task_info,
    mark_done,
    defer_task as tw_defer_task,
    delete_task,
    set_priority as tw_set_priority,
)


def mark_completed(uuid: str, vault_path: Optional[Path] = None) -> TaskCompleteResult:
    """
    Mark task as completed in TaskWarrior.

    Sprint 8.5: State Synchronization pattern - when vault_path provided,
    automatically removes UUID from all project frontmatter.

    Args:
        uuid: Task UUID
        vault_path: Vault path for State Sync (optional, Sprint 8.5)

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

    # 1. Update TaskWarrior
    success = mark_done(uuid)
    if not success:
        raise RuntimeError(f"Failed to mark task done: {uuid}")

    # 2. State Sync: Update Obsidian (Sprint 8.5 Item 1)
    if vault_path:
        from brainplorp.core.projects import remove_task_from_all_projects
        remove_task_from_all_projects(vault_path, uuid)

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


def drop_task(uuid: str, vault_path: Optional[Path] = None) -> TaskDropResult:
    """
    Drop/delete task from TaskWarrior.

    Sprint 8.5: State Synchronization pattern - when vault_path provided,
    automatically removes UUID from all project frontmatter.

    Args:
        uuid: Task UUID
        vault_path: Vault path for State Sync (optional, Sprint 8.5)

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

    # 1. Delete from TaskWarrior
    success = delete_task(uuid)
    if not success:
        raise RuntimeError(f"Failed to delete task: {uuid}")

    # 2. State Sync: Update Obsidian (Sprint 8.5 Item 1)
    if vault_path:
        from brainplorp.core.projects import remove_task_from_all_projects
        remove_task_from_all_projects(vault_path, uuid)

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
