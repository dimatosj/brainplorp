"""
Core daily workflow logic.

Implements pure functions for daily note generation.
No I/O decisions - returns structured data for callers to format.
"""

from datetime import date, datetime
from pathlib import Path
from typing import List

from brainplorp.core.types import DailyStartResult, TaskInfo, TaskSummary
from brainplorp.core.exceptions import VaultNotFoundError, DailyNoteExistsError
from brainplorp.integrations.taskwarrior import get_tasks


def start_day(target_date: date, vault_path: Path) -> DailyStartResult:
    """
    Generate daily note for specified date.

    Pure function - no prompting, no printing, returns complete data.

    Args:
        target_date: Date for daily note
        vault_path: Absolute path to Obsidian vault

    Returns:
        DailyStartResult with note path, summary, and task list

    Raises:
        VaultNotFoundError: Vault directory doesn't exist
        DailyNoteExistsError: Daily note already exists for this date
    """
    # Validate vault exists
    vault_path = vault_path.expanduser().resolve()
    if not vault_path.exists():
        raise VaultNotFoundError(str(vault_path))

    # Check if daily note already exists
    daily_dir = vault_path / "daily"
    daily_dir.mkdir(exist_ok=True)

    note_path = daily_dir / f"{target_date}.md"
    if note_path.exists():
        raise DailyNoteExistsError(str(target_date), str(note_path))

    # Get tasks from TaskWarrior
    all_tasks = get_tasks(["status:pending"])

    # Categorize tasks
    overdue = []
    due_today = []
    recurring = []

    for task_data in all_tasks:
        # Only include recurring tasks if they're due today (Q24 decision)
        if _is_recurring(task_data) and _is_due_today(task_data, target_date):
            task_info = _normalize_task(task_data)
            recurring.append(task_info)
        elif _is_overdue(task_data, target_date):
            task_info = _normalize_task(task_data)
            overdue.append(task_info)
        elif _is_due_today(task_data, target_date):
            task_info = _normalize_task(task_data)
            due_today.append(task_info)

    all_categorized = overdue + due_today + recurring

    # Create note content
    content = _format_daily_note(target_date, overdue, due_today, recurring)

    # Write note
    note_path.write_text(content)

    # Return structured result
    return {
        "note_path": str(note_path),
        "created_at": datetime.now().isoformat(),
        "date": str(target_date),
        "summary": {
            "overdue_count": len(overdue),
            "due_today_count": len(due_today),
            "recurring_count": len(recurring),
            "total_count": len(all_categorized),
        },
        "tasks": all_categorized,
    }


def _normalize_task(task_data: dict) -> TaskInfo:
    """
    Normalize TaskWarrior task data to TaskInfo format.

    Args:
        task_data: Raw task data from TaskWarrior

    Returns:
        TaskInfo TypedDict with normalized fields
    """
    return {
        "uuid": task_data.get("uuid", ""),
        "description": task_data.get("description", ""),
        "status": task_data.get("status", "pending"),
        "due": task_data.get("due"),
        "priority": task_data.get("priority", ""),
        "project": task_data.get("project"),
        "tags": task_data.get("tags", []),
    }


def _is_overdue(task: dict, reference_date: date) -> bool:
    """
    Check if task is overdue relative to reference date.

    Args:
        task: TaskWarrior task data
        reference_date: Date to check against

    Returns:
        True if task is overdue
    """
    if "due" not in task or task["due"] is None:
        return False

    # TaskWarrior stores dates as ISO 8601 strings like "20251006T000000Z"
    due_str = task["due"]
    try:
        # Parse date from ISO 8601 format (basic format: YYYYMMDDTHHMMSSZ)
        if "T" in due_str:
            # Extract date part before 'T': "20251006T000000Z" -> "20251006"
            date_part = due_str.split("T")[0]
            due_date = datetime.strptime(date_part, "%Y%m%d").date()
        else:
            due_date = datetime.strptime(due_str[:8], "%Y%m%d").date()

        return due_date < reference_date
    except (ValueError, IndexError):
        return False


def _is_due_today(task: dict, reference_date: date) -> bool:
    """
    Check if task is due on the reference date.

    Args:
        task: TaskWarrior task data
        reference_date: Date to check against

    Returns:
        True if task is due today
    """
    if "due" not in task or task["due"] is None:
        return False

    # TaskWarrior stores dates as ISO 8601 strings like "20251006T000000Z"
    due_str = task["due"]
    try:
        # Parse date from ISO 8601 format (basic format: YYYYMMDDTHHMMSSZ)
        if "T" in due_str:
            # Extract date part before 'T': "20251006T000000Z" -> "20251006"
            date_part = due_str.split("T")[0]
            due_date = datetime.strptime(date_part, "%Y%m%d").date()
        else:
            due_date = datetime.strptime(due_str[:8], "%Y%m%d").date()

        return due_date == reference_date
    except (ValueError, IndexError):
        return False


def _is_recurring(task: dict) -> bool:
    """
    Check if task is a recurring task.

    Args:
        task: TaskWarrior task data

    Returns:
        True if task has recurrence information
    """
    # TaskWarrior marks recurring tasks with "recur" field
    return "recur" in task and task["recur"] is not None


def _format_daily_note(
    target_date: date, overdue: List[TaskInfo], due_today: List[TaskInfo], recurring: List[TaskInfo]
) -> str:
    """
    Format daily note content with task lists.

    Full metadata visible including UUID (Q15 decision).
    Format: - [ ] Description (project: X, due: Y, uuid: Z)

    Args:
        target_date: Date for the note
        overdue: List of overdue tasks
        due_today: List of tasks due today
        recurring: List of recurring tasks due today

    Returns:
        Formatted markdown content
    """
    lines = []
    lines.append(f"# Daily Note - {target_date}\n")
    lines.append(f"**Date:** {target_date.strftime('%A, %B %d, %Y')}\n")
    lines.append("")

    # Add overdue section
    if overdue:
        lines.append("## ⚠️  Overdue Tasks\n")
        for task in overdue:
            lines.append(_format_task_checkbox(task))
        lines.append("")

    # Add due today section
    if due_today:
        lines.append("## 📅 Due Today\n")
        for task in due_today:
            lines.append(_format_task_checkbox(task))
        lines.append("")

    # Add recurring section
    if recurring:
        lines.append("## 🔄 Recurring Tasks\n")
        for task in recurring:
            lines.append(_format_task_checkbox(task))
        lines.append("")

    # Add empty sections if no tasks
    if not overdue and not due_today and not recurring:
        lines.append("## 📋 Tasks\n")
        lines.append("No tasks scheduled for today.\n")
        lines.append("")

    # Add notes section
    lines.append("## 📝 Notes\n")
    lines.append("")

    return "\n".join(lines)


def _format_task_checkbox(task: TaskInfo) -> str:
    """
    Format task as markdown checkbox with full metadata.

    Format: - [ ] Description (project: X, due: Y, uuid: Z)

    Args:
        task: TaskInfo to format

    Returns:
        Formatted checkbox line
    """
    metadata_parts = []

    if task["project"]:
        metadata_parts.append(f"project: {task['project']}")

    if task["due"]:
        # Format due date for readability
        try:
            if "T" in task["due"]:
                # Extract date part before 'T': "20251006T000000Z" -> "20251006"
                date_part = task["due"].split("T")[0]
                due_date = datetime.strptime(date_part, "%Y%m%d").date()
                metadata_parts.append(f"due: {due_date}")
            else:
                metadata_parts.append(f"due: {task['due'][:10]}")
        except (ValueError, IndexError):
            metadata_parts.append(f"due: {task['due']}")

    if task["priority"] and task["priority"] != "":
        metadata_parts.append(f"priority: {task['priority']}")

    if task["tags"]:
        tags_str = ", ".join(task["tags"])
        metadata_parts.append(f"tags: {tags_str}")

    # Always include UUID for robustness
    metadata_parts.append(f"uuid: {task['uuid']}")

    if metadata_parts:
        metadata = " (" + ", ".join(metadata_parts) + ")"
    else:
        metadata = f" (uuid: {task['uuid']})"

    return f"- [ ] {task['description']}{metadata}"
