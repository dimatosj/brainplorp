# ABOUTME: Inbox processing workflow - interactive conversion of inbox items to tasks/notes
# ABOUTME: Prompts user for each unprocessed item and creates tasks or notes accordingly
"""
Inbox processing workflow.

Status: Implemented in Sprint 4
"""
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from brainplorp.parsers.markdown import parse_inbox_items, mark_item_processed
from brainplorp.integrations.taskwarrior import create_task
from brainplorp.integrations.obsidian import create_note, get_vault_path
from brainplorp.utils.prompts import prompt_choice, prompt, confirm
from brainplorp.utils.files import write_file, ensure_directory


def process(config: Dict[str, Any]) -> None:
    """
    Interactive inbox processing.

    Reads current month's inbox file, presents each unprocessed item,
    and prompts user to convert to task, note, or discard.

    Args:
        config: Configuration dictionary

    Example:
        >>> config = load_config()
        >>> process(config)
        # Interactive prompts follow...
    """
    inbox_path = get_current_inbox_path(config)

    # Auto-create inbox file if it doesn't exist (per Q3 answer)
    if not inbox_path.exists():
        ensure_directory(inbox_path.parent)
        month_name = datetime.now().strftime("%B %Y")
        initial_content = f"""# Inbox - {month_name}

## Unprocessed

<!-- Add items here -->

## Processed
"""
        write_file(inbox_path, initial_content)
        print(f"\n✨ Created inbox file: {inbox_path}")

    items = parse_inbox_items(inbox_path)

    if not items:
        print(f"\n✅ Inbox is empty! All items processed.")
        return

    print(f"\n📥 {len(items)} items in inbox\n")

    processed_count = 0

    for item in items:
        print(f"\n{'=' * 60}")
        print(f"📌 Item: {item}")
        print(f"{'=' * 60}")

        choice = prompt_choice(
            options=[
                "📋 Create task",
                "📝 Create note",
                "🗑️  Discard (delete)",
                "⏭️  Skip (process later)",
                "🚪 Quit processing",
            ],
            prompt_text="What would you like to do with this item?",
        )

        if choice == 0:  # Create task
            task_uuid, should_mark_failed = process_item_as_task(item, config)
            if task_uuid:
                mark_item_processed(inbox_path, item, f"Created task (uuid: {task_uuid})")
                processed_count += 1
                print(f"✅ Task created: {task_uuid}\n")
            elif should_mark_failed:
                # User chose to mark as processed despite failure (Q8)
                mark_item_processed(inbox_path, item, "Failed to create task")
                processed_count += 1
            else:
                print("❌ Task creation failed - item remains unprocessed\n")

        elif choice == 1:  # Create note
            note_path = process_item_as_note(item, config)
            if note_path:
                relative_path = note_path.relative_to(get_vault_path(config))
                mark_item_processed(inbox_path, item, f"Created note: {relative_path}")
                processed_count += 1
                print(f"✅ Note created: {relative_path}\n")
            else:
                print("❌ Failed to create note\n")

        elif choice == 2:  # Discard
            if confirm(f"Really discard '{item}'?", default=False):
                mark_item_processed(inbox_path, item, "Discarded")
                processed_count += 1
                print("🗑️  Discarded\n")
            else:
                print("❌ Discard cancelled\n")

        elif choice == 3:  # Skip
            print("⏭️  Skipped (will process later)\n")
            # No action

        elif choice == 4:  # Quit
            print("\n⚠️  Processing interrupted. Progress saved.")
            break

    print(f"\n{'=' * 60}")
    print(f"✅ Processed {processed_count} items")
    print(f"{'=' * 60}\n")


def get_current_inbox_path(config: Dict[str, Any]) -> Path:
    """
    Get path to current month's inbox file.

    Args:
        config: Configuration dictionary

    Returns:
        Path to inbox file (e.g., vault/inbox/2025-10.md)

    Example:
        >>> inbox = get_current_inbox_path(config)
        >>> print(inbox)
        Path('/Users/user/vault/inbox/2025-10.md')
    """
    vault = get_vault_path(config)
    inbox_dir = vault / "inbox"

    # Current month file: YYYY-MM.md
    current_month = datetime.now().strftime("%Y-%m")
    inbox_file = inbox_dir / f"{current_month}.md"

    return inbox_file


def process_item_as_task(item: str, config: Dict[str, Any]) -> Tuple[Optional[str], bool]:
    """
    Process inbox item as TaskWarrior task.

    Prompts user for task metadata and creates task.
    Per Q8 answer: Interactive retry on failure.

    Args:
        item: Inbox item text
        config: Configuration dictionary

    Returns:
        Tuple of (task_uuid, should_mark_failed):
        - task_uuid: Task UUID if created, None otherwise
        - should_mark_failed: True if user wants to mark as processed despite failure

    Example:
        >>> uuid, mark_failed = process_item_as_task("Buy groceries", config)
    """
    print(f"\n📋 Creating task from: {item}")

    # Use item as default description, allow editing
    description = prompt("Task description", default=item)

    if not description:
        print("❌ Description required")
        return None, False

    # Gather metadata
    project = prompt("Project (optional)", default="")
    due = prompt("Due date (optional, e.g., 'tomorrow', '2025-10-15')", default="")
    priority = prompt("Priority (H/M/L, optional)", default="").upper()
    tags_str = prompt("Tags (comma-separated, optional)", default="")

    tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else None

    # Confirm creation
    print(f"\n📋 Task summary:")
    print(f"   Description: {description}")
    if project:
        print(f"   Project: {project}")
    if due:
        print(f"   Due: {due}")
    if priority:
        print(f"   Priority: {priority}")
    if tags:
        print(f"   Tags: {', '.join(tags)}")

    if not confirm("Create this task?", default=True):
        return None, False

    # Create task
    uuid = create_task(
        description=description,
        project=project if project else None,
        due=due if due else None,
        priority=priority if priority else None,
        tags=tags,
    )

    # Handle failure with retry (per Q8 answer)
    if not uuid:
        print("❌ Failed to create task")
        if confirm("Retry?", default=True):
            # Retry once
            uuid = create_task(
                description=description,
                project=project if project else None,
                due=due if due else None,
                priority=priority if priority else None,
                tags=tags,
            )
            if not uuid:
                print("❌ Second attempt failed")
                # Q8: If second failure, offer to mark as processed
                if confirm("Mark as processed anyway?", default=False):
                    return None, True  # Mark as failed
                else:
                    return None, False  # Leave unprocessed

    return uuid, False


def process_item_as_note(item: str, config: Dict[str, Any]) -> Optional[Path]:
    """
    Process inbox item as Obsidian note.

    Prompts user for note details and creates note.
    Per Q5 answer: Multi-line input with Ctrl+D.

    Args:
        item: Inbox item text
        config: Configuration dictionary

    Returns:
        Path to created note, or None if failed or cancelled

    Example:
        >>> note = process_item_as_note("Meeting ideas", config)
    """
    print(f"\n📝 Creating note from: {item}")

    # Use item as default title
    title = prompt("Note title", default=item)

    if not title:
        print("❌ Title required")
        return None

    # Note type
    note_type = prompt("Note type", default="general")

    # Initial content (multi-line with Ctrl+D per Q5 answer)
    print("Note content (press Ctrl+D when done, or leave empty):")
    try:
        lines = []
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass

    content = "\n".join(lines) if lines else ""

    # Confirm creation
    print(f"\n📝 Note summary:")
    print(f"   Title: {title}")
    print(f"   Type: {note_type}")
    if content:
        print(f"   Content: {len(content)} characters")

    if not confirm("Create this note?", default=True):
        return None

    # Create note
    vault = get_vault_path(config)
    note_path = create_note(vault_path=vault, title=title, note_type=note_type, content=content)

    return note_path
