"""
Core review workflow logic.

Implements pure functions for end-of-day task review.
No I/O decisions - returns structured data for callers to format.
"""

from datetime import date, datetime
from pathlib import Path
from typing import Dict

from plorp.core.types import ReviewData, ReviewResult, TaskInfo
from plorp.core.exceptions import VaultNotFoundError, DailyNoteNotFoundError
from plorp.parsers.markdown import parse_daily_note_tasks
from plorp.integrations.taskwarrior import get_task_info


def get_review_tasks(target_date: date, vault_path: Path) -> ReviewData:
    """
    Get uncompleted tasks for review.

    Pure read operation - returns data, no interaction.

    Args:
        target_date: Date to review
        vault_path: Path to vault

    Returns:
        ReviewData with uncompleted tasks

    Raises:
        VaultNotFoundError: Vault doesn't exist
        DailyNoteNotFoundError: No daily note for date
    """
    vault_path = vault_path.expanduser().resolve()
    if not vault_path.exists():
        raise VaultNotFoundError(str(vault_path))

    # Find daily note
    note_path = vault_path / "daily" / f"{target_date}.md"
    if not note_path.exists():
        raise DailyNoteNotFoundError(str(target_date))

    # Parse uncompleted tasks from note (returns list of (description, uuid) tuples)
    tasks_data = parse_daily_note_tasks(note_path)

    # Convert to TaskInfo with full data from TaskWarrior
    # Q16: Missing tasks (deleted from TW) returned with status: "missing"
    uncompleted_tasks = []
    for description, uuid in tasks_data:
        task_data = get_task_info(uuid)
        if task_data:
            # Task exists in TaskWarrior - normalize it
            uncompleted_tasks.append(_normalize_task(task_data))
        else:
            # Task deleted from TaskWarrior - mark as missing
            uncompleted_tasks.append(
                {
                    "uuid": uuid,
                    "description": description,
                    "status": "missing",
                    "due": None,
                    "priority": None,
                    "project": None,
                    "tags": [],
                }
            )

    return {
        "date": str(target_date),
        "daily_note_path": str(note_path),
        "uncompleted_tasks": uncompleted_tasks,
        "total_tasks": len(tasks_data),
        "uncompleted_count": len(uncompleted_tasks),
    }


def add_review_notes(
    target_date: date, vault_path: Path, reflections: Dict[str, str]
) -> ReviewResult:
    """
    Add review/reflection notes to daily note.

    Args:
        target_date: Date to add review for
        vault_path: Path to vault
        reflections: Dict with keys: went_well, could_improve, tomorrow

    Returns:
        ReviewResult with confirmation

    Raises:
        DailyNoteNotFoundError: No daily note for date
    """
    vault_path = vault_path.expanduser().resolve()
    note_path = vault_path / "daily" / f"{target_date}.md"

    if not note_path.exists():
        raise DailyNoteNotFoundError(str(target_date))

    # Read existing content
    content = note_path.read_text()

    # Append review section
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    review_section = f"\n## Review ({timestamp})\n\n"

    if "went_well" in reflections and reflections["went_well"]:
        review_section += f"**What went well:**\n{reflections['went_well']}\n\n"

    if "could_improve" in reflections and reflections["could_improve"]:
        review_section += f"**What could improve:**\n{reflections['could_improve']}\n\n"

    if "tomorrow" in reflections and reflections["tomorrow"]:
        review_section += f"**Notes for tomorrow:**\n{reflections['tomorrow']}\n\n"

    # Append to file
    content += review_section
    note_path.write_text(content)

    return {
        "daily_note_path": str(note_path),
        "review_added_at": timestamp,
        "reflections": reflections,
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
