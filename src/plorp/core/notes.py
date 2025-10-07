"""
Core notes workflow logic.

Implements pure functions for note creation and linking.
No I/O decisions - returns structured data for callers to format.
"""

from datetime import datetime
from pathlib import Path

from plorp.core.types import NoteCreateResult, NoteLinkResult
from plorp.core.exceptions import (
    VaultNotFoundError,
    TaskNotFoundError,
    NoteNotFoundError,
    NoteOutsideVaultError,
)
from plorp.integrations.taskwarrior import get_task_info, add_annotation, get_task_annotations
from plorp.integrations.obsidian import create_note
from plorp.parsers.markdown import add_task_to_note_frontmatter


def create_note_standalone(
    vault_path: Path, title: str, note_type: str = "general", content: str = ""
) -> NoteCreateResult:
    """
    Create a standalone note (not linked to task).

    Args:
        vault_path: Path to vault
        title: Note title
        note_type: Note type (general, meeting, project)
        content: Note content

    Returns:
        NoteCreateResult

    Raises:
        VaultNotFoundError: Vault doesn't exist
    """
    vault_path = vault_path.expanduser().resolve()
    if not vault_path.exists():
        raise VaultNotFoundError(str(vault_path))

    # Create note
    note_path = create_note(vault_path, title, note_type, content)

    return {
        "note_path": str(note_path),
        "created_at": datetime.now().isoformat(),
        "title": title,
        "linked_task_uuid": None,
    }


def create_note_linked_to_task(
    vault_path: Path,
    title: str,
    task_uuid: str,
    note_type: str = "general",
    content: str = "",
) -> NoteCreateResult:
    """
    Create note and link to task (bidirectional).

    Args:
        vault_path: Path to vault
        title: Note title
        task_uuid: Task UUID to link to
        note_type: Note type
        content: Note content

    Returns:
        NoteCreateResult

    Raises:
        VaultNotFoundError: Vault doesn't exist
        TaskNotFoundError: Task doesn't exist
    """
    vault_path = vault_path.expanduser().resolve()
    if not vault_path.exists():
        raise VaultNotFoundError(str(vault_path))

    # Verify task exists
    task = get_task_info(task_uuid)
    if not task:
        raise TaskNotFoundError(task_uuid)

    # Create note
    note_path = create_note(vault_path, title, note_type, content)

    # Link note to task (bidirectional)
    link_note_to_task(vault_path, note_path, task_uuid)

    return {
        "note_path": str(note_path),
        "created_at": datetime.now().isoformat(),
        "title": title,
        "linked_task_uuid": task_uuid,
    }


def link_note_to_task(vault_path: Path, note_path: Path, task_uuid: str) -> NoteLinkResult:
    """
    Link existing note to task (bidirectional).

    Args:
        vault_path: Path to vault
        note_path: Path to note
        task_uuid: Task UUID

    Returns:
        NoteLinkResult

    Raises:
        TaskNotFoundError: Task doesn't exist
        NoteNotFoundError: Note doesn't exist
        NoteOutsideVaultError: Note is outside vault
    """
    vault_path = vault_path.expanduser().resolve()
    note_path = note_path.expanduser().resolve()

    # Verify task exists
    task = get_task_info(task_uuid)
    if not task:
        raise TaskNotFoundError(task_uuid)

    # Verify note exists
    if not note_path.exists():
        raise NoteNotFoundError(str(note_path))

    # Verify note is inside vault
    try:
        note_path.relative_to(vault_path)
    except ValueError:
        raise NoteOutsideVaultError(str(note_path), str(vault_path))

    # Add task UUID to note front matter
    add_task_to_note_frontmatter(note_path, task_uuid)

    # Add note path as task annotation
    relative_path = note_path.relative_to(vault_path)
    normalized_path = str(relative_path.as_posix())
    annotation_text = f"plorp:note:{normalized_path}"

    # Check for duplicates before adding
    existing = get_task_annotations(task_uuid)

    already_linked = False
    for ann in existing:
        if ann.startswith("plorp:note:"):
            existing_path = ann[11:]
            if Path(existing_path).as_posix() == normalized_path:
                already_linked = True
                break

    if not already_linked:
        add_annotation(task_uuid, annotation_text)

    return {
        "note_path": str(note_path),
        "task_uuid": task_uuid,
        "linked_at": datetime.now().isoformat(),
    }
