# ABOUTME: Daily workflow implementation - generates daily notes from TaskWarrior tasks
# ABOUTME: Provides start() to create daily note and review() for end-of-day processing (Sprint 3)
"""
Daily workflow: start and review.

Status:
- start() - Implemented in Sprint 2
- review() - To be implemented in Sprint 3
"""
import sys
from pathlib import Path
from datetime import date
from typing import List, Dict, Any

from plorp.integrations.taskwarrior import (
    get_overdue_tasks,
    get_due_today,
    get_recurring_today,
)
from plorp.utils.files import write_file, ensure_directory
from plorp.utils.dates import (
    format_date_iso,
    format_date_long,
    format_taskwarrior_date_short,
)


def start(config: Dict[str, Any]) -> Path:
    """
    Generate daily note for today.

    Queries TaskWarrior for overdue, due today, and recurring tasks,
    then generates a formatted markdown daily note in the Obsidian vault.

    Args:
        config: Configuration dictionary with 'vault_path'

    Returns:
        Path to created daily note file

    Raises:
        FileExistsError: If daily note already exists
        FileNotFoundError: If vault_path doesn't exist
        IOError: If file can't be written

    Example:
        >>> config = load_config()
        >>> note_path = start(config)
        >>> print(f"Daily note created: {note_path}")
    """
    today = date.today()

    # Query TaskWarrior
    overdue = get_overdue_tasks()
    due_today = get_due_today()
    recurring = get_recurring_today()

    # Warn if no tasks found
    if not overdue and not due_today and not recurring:
        print("⚠️  Warning: No tasks found. Is TaskWarrior installed?", file=sys.stderr)

    # Generate markdown content
    note_content = generate_daily_note_content(today, overdue, due_today, recurring)

    # Determine file path
    vault_path = Path(config["vault_path"])
    daily_dir = vault_path / "daily"
    ensure_directory(daily_dir)

    daily_path = daily_dir / f"{format_date_iso(today)}.md"

    # Check if file already exists
    if daily_path.exists():
        raise FileExistsError(
            f"❌ Daily note already exists: {daily_path}\n"
            f"💡 Use a text editor to modify it, or delete it to regenerate"
        )

    # Write file
    write_file(daily_path, note_content)

    # Print summary
    print(f"\n✅ Daily note generated")
    print(f"📄 {daily_path}")
    print(f"\nSummary:")
    print(f"  {len(overdue)} overdue tasks")
    print(f"  {len(due_today)} due today")
    print(f"  {len(recurring)} recurring tasks")
    print()

    return daily_path


def generate_daily_note_content(
    today: date, overdue: List[Dict], due_today: List[Dict], recurring: List[Dict]
) -> str:
    """
    Generate markdown content for daily note.

    Args:
        today: Date for the note
        overdue: List of overdue tasks
        due_today: List of tasks due today
        recurring: List of recurring tasks

    Returns:
        Complete markdown content with YAML front matter

    Example:
        >>> content = generate_daily_note_content(date.today(), [], [], [])
        >>> assert '---' in content  # Has front matter
        >>> assert '# Daily Note' in content
    """
    content = f"""---
date: {format_date_iso(today)}
type: daily
plorp_version: 1.0
---

# Daily Note - {format_date_long(today)}

"""

    if overdue:
        content += f"## Overdue ({len(overdue)})\n\n"
        for task in overdue:
            content += format_task_checkbox(task)
        content += "\n"
    elif not overdue and not due_today and not recurring:
        # No tasks at all - show help message
        content += "## Overdue (0)\n\n_No tasks found_\n\n"

    if due_today:
        content += f"## Due Today ({len(due_today)})\n\n"
        for task in due_today:
            content += format_task_checkbox(task)
        content += "\n"
    elif not overdue and not due_today and not recurring:
        content += "## Due Today (0)\n\n_No tasks found_\n\n"

    if recurring:
        content += f"## Recurring\n\n"
        for task in recurring:
            content += format_task_checkbox(task)
        content += "\n"
    elif not overdue and not due_today and not recurring:
        content += "## Recurring\n\n_No tasks found_\n\n"

    content += "---\n\n## Notes\n\n[Your thoughts, observations, decisions during the day]\n\n"
    content += "---\n\n## Review Section\n\n<!-- Auto-populated by `plorp review` -->\n"

    return content


def format_task_checkbox(task: Dict) -> str:
    """
    Format task as markdown checkbox with metadata.

    Args:
        task: Task dictionary from TaskWarrior

    Returns:
        Formatted checkbox line

    Example:
        >>> task = {'description': 'Buy milk', 'uuid': 'abc-123', 'project': 'home'}
        >>> checkbox = format_task_checkbox(task)
        >>> assert '- [ ] Buy milk' in checkbox
        >>> assert 'uuid: abc-123' in checkbox
    """
    desc = task["description"]
    uuid = task["uuid"]

    # Build metadata string
    meta = []

    if "due" in task:
        due_str = format_taskwarrior_date_short(task["due"])
        meta.append(f"due: {due_str}")

    if "project" in task:
        meta.append(f"project: {task['project']}")

    if "priority" in task:
        meta.append(f"priority: {task['priority']}")

    if "recur" in task:
        meta.append(f"recurring: {task['recur']}")

    meta.append(f"uuid: {uuid}")

    meta_str = ", ".join(meta)

    return f"- [ ] {desc} ({meta_str})\n"


def review(config: Dict[str, Any]) -> None:
    """
    Interactive end-of-day review.

    Status: STUB - To be implemented in Sprint 3

    Args:
        config: Configuration dictionary
    """
    print("⚠️  'review' functionality not yet implemented (coming in Sprint 3)")
