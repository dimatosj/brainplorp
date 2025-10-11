"""
Core inbox workflow logic.

Implements pure functions for inbox processing.
No I/O decisions - returns structured data for callers to format.
"""

from datetime import date
from pathlib import Path
from typing import Optional

from plorp.core.types import InboxData, InboxProcessResult
from plorp.core.exceptions import VaultNotFoundError, InboxNotFoundError
from plorp.parsers.markdown import parse_inbox_items, mark_item_processed
from plorp.integrations.taskwarrior import create_task
from plorp.integrations.obsidian import create_note


def get_inbox_items(vault_path: Path, target_date: Optional[date] = None) -> InboxData:
    """
    Get unprocessed inbox items.

    Pure read operation.
    Q14 decision: Use monthly files vault/inbox/YYYY-MM.md

    Args:
        vault_path: Path to vault
        target_date: Date for inbox file (defaults to today)

    Returns:
        InboxData with unprocessed items

    Raises:
        VaultNotFoundError: Vault doesn't exist
        InboxNotFoundError: Inbox file doesn't exist
    """
    vault_path = vault_path.expanduser().resolve()
    if not vault_path.exists():
        raise VaultNotFoundError(str(vault_path))

    # Use current month if no date specified
    if target_date is None:
        target_date = date.today()

    # Q14: Monthly inbox files - vault/inbox/YYYY-MM.md
    inbox_dir = vault_path / "inbox"
    inbox_path = inbox_dir / f"{target_date.strftime('%Y-%m')}.md"

    if not inbox_path.exists():
        raise InboxNotFoundError(str(inbox_path))

    # Parse unprocessed items
    items_text = parse_inbox_items(inbox_path)

    # Convert to InboxItem with line numbers
    items = []
    for idx, text in enumerate(items_text, start=1):
        items.append({"text": text, "line_number": idx})

    return {
        "inbox_path": str(inbox_path),
        "unprocessed_items": items,
        "item_count": len(items),
    }


def create_task_from_inbox(
    vault_path: Path,
    item_text: str,
    description: str,
    due: Optional[str] = None,
    priority: Optional[str] = None,
    project: Optional[str] = None,
    target_date: Optional[date] = None,
) -> InboxProcessResult:
    """
    Create task from inbox item.

    Args:
        vault_path: Path to vault
        item_text: Original inbox item text
        description: Task description
        due: Due date (YYYY-MM-DD format)
        priority: Priority (H, M, L)
        project: Project name
        target_date: Date for inbox file (defaults to today)

    Returns:
        InboxProcessResult with task UUID
    """
    # Create task in TaskWarrior
    uuid = create_task(
        description=description, project=project, due=due, priority=priority
    )

    if not uuid:
        raise RuntimeError(f"Failed to create task from inbox item: {item_text}")

    # Mark inbox item as processed
    if target_date is None:
        target_date = date.today()

    inbox_path = vault_path / "inbox" / f"{target_date.strftime('%Y-%m')}.md"
    mark_item_processed(inbox_path, item_text, f"Created task (uuid: {uuid})")

    return {
        "item_text": item_text,
        "action": "task",
        "task_uuid": uuid,
        "note_path": None,
    }


def create_note_from_inbox(
    vault_path: Path,
    item_text: str,
    title: str,
    content: str = "",
    note_type: str = "general",
    target_date: Optional[date] = None,
) -> InboxProcessResult:
    """
    Create note from inbox item.

    Args:
        vault_path: Path to vault
        item_text: Original inbox item text
        title: Note title
        content: Note content
        note_type: Note type (general, meeting, etc.)
        target_date: Date for inbox file (defaults to today)

    Returns:
        InboxProcessResult with note path
    """
    # Create note
    note_path = create_note(vault_path, title, note_type, content)

    # Mark inbox item as processed
    if target_date is None:
        target_date = date.today()

    inbox_path = vault_path / "inbox" / f"{target_date.strftime('%Y-%m')}.md"
    mark_item_processed(inbox_path, item_text, f"Created note: {note_path.name}")

    return {
        "item_text": item_text,
        "action": "note",
        "task_uuid": None,
        "note_path": str(note_path),
    }


def create_both_from_inbox(
    vault_path: Path,
    item_text: str,
    task_description: str,
    note_title: str,
    note_content: str = "",
    due: Optional[str] = None,
    priority: Optional[str] = None,
    project: Optional[str] = None,
    target_date: Optional[date] = None,
) -> InboxProcessResult:
    """
    Create both task and note from inbox item, linked together.

    Args:
        vault_path: Path to vault
        item_text: Original inbox item text
        task_description: Task description
        note_title: Note title
        note_content: Note content
        due: Task due date
        priority: Task priority
        project: Task project
        target_date: Date for inbox file (defaults to today)

    Returns:
        InboxProcessResult with both task UUID and note path
    """
    # Create task
    uuid = create_task(
        description=task_description, project=project, due=due, priority=priority
    )

    if not uuid:
        raise RuntimeError(f"Failed to create task from inbox item: {item_text}")

    # Create note linked to task
    # Import here to avoid circular dependency
    from plorp.core.notes import create_note_linked_to_task

    result = create_note_linked_to_task(
        vault_path=vault_path,
        title=note_title,
        task_uuid=uuid,
        note_type="general",
        content=note_content,
    )

    # Mark inbox item as processed
    if target_date is None:
        target_date = date.today()

    inbox_path = vault_path / "inbox" / f"{target_date.strftime('%Y-%m')}.md"
    mark_item_processed(
        inbox_path, item_text, f"Created task and note (uuid: {uuid})"
    )

    return {
        "item_text": item_text,
        "action": "both",
        "task_uuid": uuid,
        "note_path": result["note_path"],
    }


def discard_inbox_item(
    vault_path: Path, item_text: str, target_date: Optional[date] = None
) -> InboxProcessResult:
    """
    Discard inbox item without creating anything.

    Args:
        vault_path: Path to vault
        item_text: Item to discard
        target_date: Date for inbox file (defaults to today)

    Returns:
        InboxProcessResult
    """
    if target_date is None:
        target_date = date.today()

    inbox_path = vault_path / "inbox" / f"{target_date.strftime('%Y-%m')}.md"
    mark_item_processed(inbox_path, item_text, "Discarded")

    return {
        "item_text": item_text,
        "action": "discard",
        "task_uuid": None,
        "note_path": None,
    }


def append_emails_to_inbox(emails: list, vault_path: Path) -> dict:
    """
    Append fetched emails to monthly inbox file as markdown bullets.

    Args:
        emails: List of email dicts from fetch_unread_emails()
                Each email has: id, body_text, body_html
        vault_path: Path to Obsidian vault

    Returns:
        Dict with:
            - appended_count: Number of emails appended
            - inbox_path: Path to inbox file
            - total_unprocessed: Total unprocessed items in inbox

    Example:
        {
            "appended_count": 3,
            "inbox_path": "/vault/inbox/2025-10.md",
            "total_unprocessed": 15
        }
    """
    from plorp.integrations.email_imap import convert_email_body_to_bullets

    # Get current month's inbox file
    today = date.today()
    inbox_dir = vault_path / "inbox"
    inbox_file = inbox_dir / f"{today.year}-{today.month:02d}.md"

    # Ensure inbox directory exists
    inbox_dir.mkdir(parents=True, exist_ok=True)

    # Read existing inbox (create if doesn't exist)
    if inbox_file.exists():
        content = inbox_file.read_text(encoding="utf-8")
    else:
        content = (
            f"# Inbox {today.year}-{today.month:02d}\n\n## Unprocessed\n\n## Processed\n"
        )

    # Find "## Unprocessed" section
    unprocessed_section_start = content.find("## Unprocessed")
    processed_section_start = content.find("## Processed")

    if unprocessed_section_start == -1:
        # Create sections if missing
        content += "\n## Unprocessed\n\n## Processed\n"
        unprocessed_section_start = content.find("## Unprocessed")
        processed_section_start = content.find("## Processed")

    # Build email markdown bullets (no subject, no metadata)
    email_lines = []
    for email in emails:
        # Convert email body to markdown bullets
        bullets = convert_email_body_to_bullets(email["body_text"], email["body_html"])
        if bullets:
            email_lines.append(bullets)

    # Insert emails at end of Unprocessed section (before ## Processed)
    insertion_point = processed_section_start
    new_content = (
        content[:insertion_point].rstrip()
        + "\n\n"  # Double newline for proper spacing
        + "\n".join(email_lines)
        + "\n\n"
        + content[insertion_point:]
    )

    # Write back
    inbox_file.write_text(new_content, encoding="utf-8")

    # Count total unprocessed items (count all bullets in Unprocessed section)
    # Need to recalculate section positions in new_content
    new_unprocessed_start = new_content.find("## Unprocessed")
    new_processed_start = new_content.find("## Processed")
    unprocessed_section = new_content[new_unprocessed_start:new_processed_start]
    unprocessed_count = len(
        [line for line in unprocessed_section.split("\n") if line.strip().startswith("-")]
    )

    return {
        "appended_count": len(emails),
        "inbox_path": str(inbox_file),
        "total_unprocessed": unprocessed_count,
    }


def quick_add_to_inbox(text: str, vault_path: Path, urgent: bool = False) -> dict:
    """
    Quick-add text to inbox file.

    Pure capture - no metadata besides optional urgent flag.
    Project assignment, tags, and due dates happen during '/process' workflow.

    Args:
        text: Item text to add
        vault_path: Path to Obsidian vault
        urgent: Mark as urgent (adds 🔴 indicator for visual priority)

    Returns:
        Dict with:
            - added: Boolean success
            - inbox_path: Path to inbox file
            - item: Formatted item that was added

    Example:
        {
            "added": True,
            "inbox_path": "/vault/inbox/2025-10.md",
            "item": "- Buy milk"
        }
    """
    # Get current month's inbox file
    today = date.today()
    inbox_dir = vault_path / "inbox"
    inbox_file = inbox_dir / f"{today.year}-{today.month:02d}.md"

    # Ensure inbox directory exists
    inbox_dir.mkdir(parents=True, exist_ok=True)

    # Read existing inbox (create if doesn't exist)
    if inbox_file.exists():
        content = inbox_file.read_text(encoding="utf-8")
    else:
        content = (
            f"# Inbox {today.year}-{today.month:02d}\n\n## Unprocessed\n\n## Processed\n"
        )

    # Find "## Unprocessed" section
    unprocessed_section_start = content.find("## Unprocessed")
    processed_section_start = content.find("## Processed")

    if unprocessed_section_start == -1:
        # Create sections if missing
        content += "\n## Unprocessed\n\n## Processed\n"
        unprocessed_section_start = content.find("## Unprocessed")
        processed_section_start = content.find("## Processed")

    # Format item (simple bullet, with optional urgent indicator)
    if urgent:
        item = f"- 🔴 {text}"
    else:
        item = f"- {text}"

    # Insert item at end of Unprocessed section (before ## Processed)
    insertion_point = processed_section_start
    new_content = (
        content[:insertion_point].rstrip() + "\n" + item + "\n\n" + content[insertion_point:]
    )

    # Write back
    inbox_file.write_text(new_content, encoding="utf-8")

    return {"added": True, "inbox_path": str(inbox_file), "item": item}
