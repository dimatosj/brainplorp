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

from brainplorp.integrations.taskwarrior import (
    get_overdue_tasks,
    get_due_today,
    get_recurring_today,
)
from brainplorp.utils.files import write_file, ensure_directory
from brainplorp.utils.dates import (
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

    Reads today's daily note, finds uncompleted tasks, and prompts user
    for action on each task. Updates TaskWarrior and appends decisions
    to the daily note.

    Args:
        config: Configuration dictionary

    Example:
        >>> config = load_config()
        >>> review(config)
        # Interactive prompts follow...
    """
    from brainplorp.parsers.markdown import parse_daily_note_tasks
    from brainplorp.utils.prompts import prompt_choice, prompt, confirm
    from brainplorp.integrations.taskwarrior import (
        get_task_info,
        mark_done,
        defer_task,
        set_priority,
        delete_task,
    )

    today = date.today()
    vault_path = Path(config["vault_path"])
    daily_path = vault_path / "daily" / f"{format_date_iso(today)}.md"

    if not daily_path.exists():
        print(f"❌ No daily note found for {format_date_long(today)}")
        print(f"💡 Run: plorp start")
        return

    # Parse uncompleted tasks
    uncompleted = parse_daily_note_tasks(daily_path)

    if not uncompleted:
        print(f"\n✅ All tasks completed! Great work on {format_date_long(today)}")
        return

    print(f"\n📋 {len(uncompleted)} tasks remaining from {format_date_long(today)}\n")

    decisions = []

    for task_desc, task_uuid in uncompleted:
        # Get full task details from TaskWarrior
        task = get_task_info(task_uuid)

        if not task:
            # Per Q3 answer: print warning, add to decisions, add inline comment to note
            print(f"\n⚠️  Task not found in TaskWarrior: {task_desc}")
            print(f"    UUID: {task_uuid}")
            print("    (Task may have been deleted or modified outside plorp)")
            decisions.append(
                f"⚠️ {task_desc} - task not found in TaskWarrior (may have been deleted)"
            )
            continue

        # Show task details
        print(f"\n{'=' * 60}")
        print(f"📌 Task: {task['description']}")
        if "project" in task:
            print(f"   Project: {task['project']}")
        if "due" in task:
            due_str = format_taskwarrior_date_short(task["due"])
            print(f"   Due: {due_str}")
        if "priority" in task:
            print(f"   Priority: {task['priority']}")
        print(f"{'=' * 60}")

        # Prompt for action
        choice = prompt_choice(
            options=[
                "✅ Mark done",
                "📅 Defer to tomorrow",
                "📆 Defer to specific date",
                "⚡ Change priority",
                "⏭️  Skip (keep as-is)",
                "🗑️  Delete task",
                "🚪 Quit review",
            ],
            prompt_text="What would you like to do with this task?",
        )

        if choice == 0:  # Mark done
            if mark_done(task_uuid):
                decisions.append(f"✅ {task_desc}")
                print("✅ Marked done\n")
            else:
                print("❌ Failed to mark done\n")

        elif choice == 1:  # Defer to tomorrow
            if defer_task(task_uuid, "tomorrow"):
                decisions.append(f"📅 {task_desc} → tomorrow")
                print("📅 Deferred to tomorrow\n")
            else:
                print("❌ Failed to defer\n")

        elif choice == 2:  # Defer to specific date
            # Per Q6: Trust TaskWarrior date parsing
            new_due = prompt("New due date (YYYY-MM-DD or 'friday', etc)")
            if new_due and defer_task(task_uuid, new_due):
                decisions.append(f"📅 {task_desc} → {new_due}")
                print(f"📅 Deferred to {new_due}\n")
            else:
                print("❌ Failed to defer\n")

        elif choice == 3:  # Change priority
            # Per Q5: Validate priority input with loop
            while True:
                priority = prompt("Priority (H/M/L or blank to remove)", default="").upper()
                if priority in ("H", "M", "L", ""):
                    break
                print("❌ Invalid priority. Use H, M, L, or blank")

            if set_priority(task_uuid, priority):
                priority_display = priority if priority else "none"
                decisions.append(f"⚡ {task_desc} → priority {priority_display}")
                print(f"⚡ Priority set to {priority_display}\n")
            else:
                print("❌ Failed to set priority\n")

        elif choice == 4:  # Skip
            print("⏭️  Skipped (no changes)\n")
            # No action, just continue

        elif choice == 5:  # Delete
            if confirm(f"Really delete '{task_desc}'?", default=False):
                if delete_task(task_uuid):
                    decisions.append(f"🗑️  {task_desc} (deleted)")
                    print("🗑️  Deleted\n")
                else:
                    print("❌ Failed to delete\n")
            else:
                print("❌ Delete cancelled\n")

        elif choice == 6:  # Quit
            print("\n⚠️  Review interrupted. Progress saved so far.")
            break

    # Append decisions to daily note
    if decisions:
        append_review_section(daily_path, decisions)

    print(f"\n{'=' * 60}")
    print(f"✅ Review complete - processed {len(decisions)} tasks")
    print(f"{'=' * 60}\n")


def append_review_section(daily_path: Path, decisions: List[str]) -> None:
    """
    Append review decisions to daily note.

    Per Q4 answer: Appends to existing review section with new timestamp.
    Never replaces or deletes previous review content.

    Args:
        daily_path: Path to daily note
        decisions: List of decision strings to append

    Example:
        >>> decisions = ["✅ Task completed", "📅 Task deferred"]
        >>> append_review_section(Path('daily/2025-10-06.md'), decisions)
    """
    from datetime import datetime
    from brainplorp.utils.files import read_file, write_file

    content = read_file(daily_path)

    # Build review entry
    review_entry = f"\n**Review completed:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    for decision in decisions:
        review_entry += f"- {decision}\n"

    # Per Q4: APPEND to review section, don't replace
    if "## Review Section" in content:
        # Find the review section and append after it
        # Insert review entry after the "## Review Section" header
        parts = content.split("## Review Section", 1)
        if len(parts) == 2:
            # Keep everything before, add header, add old content + new entry
            content = parts[0] + "## Review Section" + parts[1].rstrip() + "\n" + review_entry
    else:
        # No review section exists, add it
        content += f"\n\n## Review Section\n{review_entry}"

    write_file(daily_path, content)
