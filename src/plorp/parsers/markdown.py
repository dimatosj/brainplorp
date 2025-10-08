# ABOUTME: Markdown parsing utilities for daily notes and inbox processing
# ABOUTME: Parses checkboxes, front matter, and inbox item structure using regex and PyYAML
"""
Markdown parsing utilities.

Provides functions to parse daily notes, extract unchecked tasks,
parse YAML front matter, and process inbox items.
"""
import re
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import yaml


def parse_daily_note_tasks(note_path: Path) -> List[Tuple[str, str]]:
    """
    Parse daily note for unchecked tasks.

    Extracts all unchecked checkboxes that contain TaskWarrior UUIDs.

    Args:
        note_path: Path to daily note markdown file

    Returns:
        List of (description, uuid) tuples for unchecked tasks.
        Empty list if no unchecked tasks or file not found.

    Example:
        >>> tasks = parse_daily_note_tasks(Path('vault/daily/2025-10-06.md'))
        >>> for desc, uuid in tasks:
        ...     print(f"{desc} -> {uuid}")
    """
    try:
        content = note_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []

    # Pattern: - [ ] Description (metadata, uuid: abc-123)
    # Flexible pattern per Q2 answer: handles variable whitespace, case-insensitive UUIDs
    # [^(]+ matches description (everything except opening paren)
    # [\w-]+ matches UUID (alphanumeric and hyphens)
    pattern = r"-\s*\[\s*\]\s*([^(]+)\(.*?uuid:\s*([\w-]+)\)"
    matches = re.findall(pattern, content)

    return [(desc.strip(), uuid) for desc, uuid in matches]


def parse_frontmatter(content: str) -> Dict[str, Any]:
    """
    Extract YAML front matter from markdown content.

    Args:
        content: Markdown content string

    Returns:
        Dictionary of front matter fields. Empty dict if no front matter.

    Example:
        >>> content = "---\\ndate: 2025-10-06\\n---\\n# Title"
        >>> fm = parse_frontmatter(content)
        >>> fm['date']
        '2025-10-06'
    """
    if not content.startswith("---"):
        return {}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}

    try:
        # Use BaseLoader to preserve all values as strings (don't auto-convert dates)
        result = yaml.load(parts[1], Loader=yaml.BaseLoader)
        # Validate that result is a dict (per Sprint 2 Q6 pattern)
        if not isinstance(result, dict):
            return {}
        return result or {}
    except yaml.YAMLError:
        return {}


def extract_task_uuids_from_note(note_path: Path) -> List[str]:
    """
    Extract all TaskWarrior UUIDs from a note's front matter.

    Used for note-task linking (Sprint 5).

    Args:
        note_path: Path to markdown note

    Returns:
        List of task UUIDs. Empty list if no front matter or tasks field.

    Example:
        >>> uuids = extract_task_uuids_from_note(Path('vault/notes/meeting.md'))
        >>> for uuid in uuids:
        ...     print(f"Linked task: {uuid}")
    """
    try:
        content = note_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []

    fm = parse_frontmatter(content)
    return fm.get("tasks", [])


def parse_inbox_items(inbox_path: Path) -> List[str]:
    """
    Parse unprocessed items from inbox file.

    Extracts unchecked checkboxes from "## Unprocessed" section.

    Args:
        inbox_path: Path to inbox markdown file

    Returns:
        List of unprocessed item strings (without checkbox markers).
        Empty list if no unprocessed items or file not found.

    Example:
        >>> items = parse_inbox_items(Path('vault/inbox/2025-10.md'))
        >>> for item in items:
        ...     print(f"Process: {item}")
    """
    try:
        content = inbox_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []

    # Find "## Unprocessed" section
    unprocessed_match = re.search(r"## Unprocessed\s*\n(.*?)(?=##|\Z)", content, re.DOTALL)

    if not unprocessed_match:
        return []

    unprocessed_section = unprocessed_match.group(1)

    # Extract unchecked items: - [ ] Item text
    pattern = r"- \[ \] (.+?)(?:\n|$)"
    matches = re.findall(pattern, unprocessed_section)

    return [item.strip() for item in matches]


def mark_item_processed(inbox_path: Path, item_text: str, action: str) -> None:
    """
    Mark an inbox item as processed.

    Changes the item from unchecked to checked and moves it to
    the "## Processed" section with an action note.

    Note: If the same item text appears multiple times, only the
    first occurrence is marked (users should avoid duplicate items).

    Args:
        inbox_path: Path to inbox file
        item_text: Text of item to mark processed
        action: Description of action taken (e.g., "Created task abc-123")

    Raises:
        FileNotFoundError: If inbox file doesn't exist

    Example:
        >>> mark_item_processed(
        ...     Path('inbox/2025-10.md'),
        ...     'Buy groceries',
        ...     'Created task (uuid: abc-123)'
        ... )
    """
    from plorp.utils.files import read_file, write_file

    content = read_file(inbox_path)

    # Find and replace the unchecked item
    old_line = f"- [ ] {item_text}"
    new_line = f"- [x] {item_text} - {action}"

    # Replace in content (only first occurrence per Q4 answer)
    content = content.replace(old_line, new_line, 1)

    # Move from Unprocessed to Processed section
    # Find the new_line in Unprocessed section
    unprocessed_pattern = r"(## Unprocessed\s*\n)(.*?)(##|\Z)"

    def move_to_processed(match):
        header = match.group(1)
        section_content = match.group(2)
        next_section = match.group(3)

        # Remove the processed item from unprocessed
        section_content = section_content.replace(new_line + "\n", "")

        return header + section_content + next_section

    content = re.sub(unprocessed_pattern, move_to_processed, content, flags=re.DOTALL)

    # Add to Processed section
    processed_pattern = r"(## Processed\s*\n)"

    def add_to_processed(match):
        return match.group(1) + f"{new_line}\n"

    if "## Processed" in content:
        content = re.sub(processed_pattern, add_to_processed, content)
    else:
        # Add Processed section if not exists
        content += f"\n## Processed\n\n{new_line}\n"

    write_file(inbox_path, content)


def add_frontmatter_field(content: str, field: str, value: Any) -> str:
    """
    Add or update a field in YAML front matter.

    If front matter doesn't exist, creates it. If field exists, updates it.
    Uses block style (not flow style) and preserves field order.

    Args:
        content: Markdown content (with or without front matter)
        field: Field name to add/update
        value: Field value (will be serialized to YAML)

    Returns:
        Updated markdown content with modified front matter

    Example:
        >>> content = "# Note\\n\\nSome content"
        >>> updated = add_frontmatter_field(content, 'tags', ['work', 'important'])
        >>> print(updated)
        ---
        tags:
          - work
          - important
        ---
        # Note

        Some content
    """
    fm = parse_frontmatter(content)

    # Update field
    fm[field] = value

    # Extract body (everything after front matter)
    # Per Q2 answer: strip leading newlines for consistency
    if content.startswith("---"):
        parts = content.split("---", 2)
        body = parts[2].lstrip("\n") if len(parts) > 2 else ""
    else:
        body = content.lstrip("\n")

    # Rebuild with updated front matter
    # Per Q1 answer: block style, preserve order, no blank line after ---
    new_fm = yaml.dump(fm, default_flow_style=False, sort_keys=False)
    return f"---\n{new_fm}---\n{body}"


def add_task_to_note_frontmatter(note_path: Path, task_uuid: str) -> None:
    """
    Add a task UUID to a note's front matter tasks list.

    Creates 'tasks' field if it doesn't exist. Avoids duplicates.
    Validates that task exists in TaskWarrior (per Q3 answer).

    Args:
        note_path: Path to note file
        task_uuid: Task UUID to add

    Raises:
        FileNotFoundError: If note doesn't exist
        ValueError: If task doesn't exist in TaskWarrior

    Example:
        >>> add_task_to_note_frontmatter(Path('notes/meeting.md'), 'abc-123')
        # Note now has tasks: [abc-123] in front matter
    """
    from plorp.utils.files import read_file, write_file
    from plorp.integrations.taskwarrior import get_task_info

    # Validate task exists (per Q3 answer)
    task = get_task_info(task_uuid)
    if not task:
        raise ValueError(f"Task not found in TaskWarrior: {task_uuid}")

    content = read_file(note_path)
    fm = parse_frontmatter(content)

    # Get existing tasks or create empty list
    tasks = fm.get("tasks", [])

    # Add UUID if not already present
    if task_uuid not in tasks:
        tasks.append(task_uuid)

    # Update front matter
    updated_content = add_frontmatter_field(content, "tasks", tasks)

    write_file(note_path, updated_content)


def remove_task_from_note_frontmatter(note_path: Path, task_uuid: str) -> None:
    """
    Remove a task UUID from a note's front matter tasks list.

    Args:
        note_path: Path to note file
        task_uuid: Task UUID to remove

    Raises:
        FileNotFoundError: If note doesn't exist

    Example:
        >>> remove_task_from_note_frontmatter(Path('notes/meeting.md'), 'abc-123')
    """
    from plorp.utils.files import read_file, write_file

    content = read_file(note_path)
    fm = parse_frontmatter(content)

    tasks = fm.get("tasks", [])

    if task_uuid in tasks:
        tasks.remove(task_uuid)
        updated_content = add_frontmatter_field(content, "tasks", tasks)
        write_file(note_path, updated_content)
