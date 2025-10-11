# ABOUTME: Note management workflow - creates notes and manages task-note linking
# ABOUTME: Provides bidirectional linking between Obsidian notes and TaskWarrior tasks
"""
Note workflow: creation and linking.

Status: Implemented in Sprint 5
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

from brainplorp.integrations.obsidian import create_note, get_vault_path
from brainplorp.integrations.taskwarrior import (
    add_annotation,
    get_task_info,
    get_task_annotations,
)
from brainplorp.parsers.markdown import (
    add_task_to_note_frontmatter,
    extract_task_uuids_from_note,
)


def create_note_with_task_link(
    config: Dict[str, Any],
    title: str,
    task_uuid: Optional[str] = None,
    note_type: str = "general",
    content: str = "",
) -> Path:
    """
    Create a new note and optionally link it to a task.

    Creates bidirectional link:
    - Adds task UUID to note's front matter
    - Adds note path as annotation to task

    Args:
        config: Configuration dictionary
        title: Note title
        task_uuid: Optional task UUID to link
        note_type: Note type (default: 'general')
            Valid types:
            - 'meeting': Stored in vault/meetings/
            - 'general', 'project', or any other: Stored in vault/notes/
        content: Note content (default: '')

    Returns:
        Path to created note

    Raises:
        ValueError: If task_uuid provided but task doesn't exist

    Example:
        >>> config = load_config()
        >>> note = create_note_with_task_link(
        ...     config,
        ...     "Sprint Planning Notes",
        ...     task_uuid="abc-123"
        ... )
        >>> print(f"Created: {note}")
    """
    vault = get_vault_path(config)

    # Verify task exists if UUID provided
    if task_uuid:
        task = get_task_info(task_uuid)
        if not task:
            raise ValueError(f"Task not found: {task_uuid}")

    # Create the note
    note_path = create_note(vault_path=vault, title=title, note_type=note_type, content=content)

    # Link to task if UUID provided
    if task_uuid:
        link_note_to_task(note_path, task_uuid, vault)

    return note_path


def link_note_to_task(note_path: Path, task_uuid: str, vault_path: Path) -> None:
    """
    Create bidirectional link between note and task.

    Updates:
    1. Note front matter: adds task UUID to 'tasks' list
    2. Task annotation: adds note path (format: plorp:note:path)

    Args:
        note_path: Path to note file
        task_uuid: Task UUID to link
        vault_path: Path to vault root (for relative path calculation)

    Raises:
        FileNotFoundError: If note doesn't exist
        ValueError: If task doesn't exist or note is outside vault

    Example:
        >>> link_note_to_task(
        ...     Path('vault/notes/meeting.md'),
        ...     'abc-123',
        ...     Path('vault')
        ... )
    """
    # Verify task exists
    task = get_task_info(task_uuid)
    if not task:
        raise ValueError(f"Task not found: {task_uuid}")

    # Verify note exists
    if not note_path.exists():
        raise FileNotFoundError(f"Note not found: {note_path}")

    # Resolve symlinks and check if note is inside vault (per Q8 answer)
    note_path_resolved = note_path.resolve()
    vault_path_resolved = vault_path.resolve()

    if not note_path_resolved.is_relative_to(vault_path_resolved):
        raise ValueError(
            f"Note must be inside vault. Note: {note_path_resolved}, Vault: {vault_path_resolved}"
        )

    # 1. Add task UUID to note front matter
    add_task_to_note_frontmatter(note_path, task_uuid)

    # 2. Add note path as task annotation
    # Per Q4 answer: Use "plorp:note:" prefix and normalize to forward slashes
    relative_path = note_path_resolved.relative_to(vault_path_resolved)
    normalized_path = str(relative_path.as_posix())
    annotation_text = f"plorp:note:{normalized_path}"

    # Check if already annotated (avoid duplicates)
    # Per Q5 answer: Normalize paths before comparison
    existing_annotations = get_task_annotations(task_uuid)
    for annotation in existing_annotations:
        if annotation.startswith("plorp:note:"):
            existing_path = annotation[11:]  # Remove "plorp:note:" prefix
            normalized_existing = str(Path(existing_path).as_posix())
            if normalized_path == normalized_existing:
                # Already linked, skip adding annotation
                return

    add_annotation(task_uuid, annotation_text)


def unlink_note_from_task(note_path: Path, task_uuid: str) -> None:
    """
    Remove bidirectional link between note and task.

    Note: Only removes from note's front matter. TaskWarrior annotations
    cannot be removed programmatically via CLI. User must manually remove
    using: task <uuid> edit

    Args:
        note_path: Path to note file
        task_uuid: Task UUID to unlink

    Raises:
        FileNotFoundError: If note doesn't exist

    Example:
        >>> unlink_note_from_task(Path('notes/old-meeting.md'), 'abc-123')
    """
    from brainplorp.parsers.markdown import remove_task_from_note_frontmatter

    if not note_path.exists():
        raise FileNotFoundError(f"Note not found: {note_path}")

    remove_task_from_note_frontmatter(note_path, task_uuid)

    # Per Q9 answer: Print warning about manual annotation removal
    print(f"\n✅ Removed task link from note", file=sys.stderr)
    print(
        f"⚠️  Note: TaskWarrior annotation cannot be removed automatically",
        file=sys.stderr,
    )
    print(f"💡 To remove annotation from task, run: task {task_uuid} edit", file=sys.stderr)


def get_linked_notes(task_uuid: str, vault_path: Path) -> List[Path]:
    """
    Get all notes linked to a task.

    Parses task annotations to find note paths.

    Args:
        task_uuid: Task UUID
        vault_path: Path to vault root

    Returns:
        List of note paths linked to this task.
        Empty list if task not found or no linked notes.

    Example:
        >>> notes = get_linked_notes('abc-123', Path('~/vault'))
        >>> for note in notes:
        ...     print(f"Linked: {note}")
    """
    annotations = get_task_annotations(task_uuid)

    note_paths = []

    for annotation in annotations:
        # Annotations are formatted: "plorp:note:relative/path/to/note.md"
        # Per Q4 answer: Use "plorp:note:" prefix
        if annotation.startswith("plorp:note:"):
            relative_path = annotation[11:]  # Remove "plorp:note:" prefix
            full_path = vault_path / relative_path

            if full_path.exists():
                note_paths.append(full_path)

    return note_paths


def get_linked_tasks(note_path: Path) -> List[str]:
    """
    Get all task UUIDs linked to a note.

    Reads task UUIDs from note's front matter.

    Args:
        note_path: Path to note file

    Returns:
        List of task UUIDs linked to this note.
        Empty list if note not found or no linked tasks.

    Example:
        >>> tasks = get_linked_tasks(Path('notes/meeting.md'))
        >>> for uuid in tasks:
        ...     print(f"Task: {uuid}")
    """
    return extract_task_uuids_from_note(note_path)
