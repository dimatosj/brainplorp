# ABOUTME: Core layer for note operations - adds permissions, validation, warnings
# ABOUTME: High-level API that wraps integration layer - called by MCP tools
"""
Core note operations for plorp.

This module provides high-level note management functions with:
- Permission checks (allowed_folders validation)
- Context usage warnings (large files)
- Business logic (config loading, error handling)

MCP tools should call these functions, not the integration layer directly.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any

from ..config import load_config, get_vault_path
from ..core.types import NoteContent, NoteInfo, FolderReadResult
from ..core.exceptions import HeaderNotFoundError
from ..integrations.obsidian_notes import (
    _read_note_file,
    _read_folder,
    _append_to_note_file,
    _update_note_section_file,
    _search_notes_by_metadata_file,
    _create_note_in_folder_file,
)

logger = logging.getLogger(__name__)

# Default allowed folders (per Q12)
DEFAULT_ALLOWED_FOLDERS = ["daily", "inbox", "projects", "notes", "Docs"]


def _get_allowed_folders(config: dict) -> List[str]:
    """
    Get allowed folders from config, or return safe defaults.

    Args:
        config: Configuration dictionary

    Returns:
        List of allowed folder names
    """
    if "note_access" not in config:
        logger.warning(
            f"note_access not configured in config.yaml. "
            f"Using defaults: {DEFAULT_ALLOWED_FOLDERS}. "
            f"Configure explicitly: note_access.allowed_folders"
        )
        return DEFAULT_ALLOWED_FOLDERS

    return config["note_access"].get("allowed_folders", DEFAULT_ALLOWED_FOLDERS)


def _validate_note_access(vault_path: Path, note_path: str) -> None:
    """
    Validate note path is in allowed_folders.

    Args:
        vault_path: Vault root path
        note_path: Relative note path

    Raises:
        PermissionError: If path outside allowed folders
    """
    config = load_config()
    allowed = _get_allowed_folders(config)

    # Extract first path component (folder name)
    parts = Path(note_path).parts
    if not parts:
        raise PermissionError(f"Invalid note path: {note_path}")

    folder = parts[0]

    if folder not in allowed:
        raise PermissionError(
            f"Access denied: '{folder}' not in allowed_folders. "
            f"Add to config: note_access.allowed_folders = {allowed + [folder]}"
        )


def _add_context_warnings(result: Dict[str, Any], config: dict) -> Dict[str, Any]:
    """
    Add context usage warnings to result if file is large.

    Args:
        result: Result dict from integration layer
        config: Configuration dictionary

    Returns:
        Result dict with warnings added
    """
    word_count = result.get("word_count", 0)
    warn_threshold = config.get("note_access", {}).get("warn_large_file_words", 10000)

    warnings = result.get("warnings", [])

    if word_count > warn_threshold:
        estimated_tokens = int(word_count * 1.3)
        context_percent = int((estimated_tokens / 200000) * 100)
        warnings.append(
            f"Large file ({word_count} words, ~{estimated_tokens} tokens). "
            f"Will use ~{context_percent}% of 200k context budget. "
            f"Consider mode='preview' or 'structure' to save context."
        )

    if warnings:
        result["warnings"] = warnings

    return result


# ============================================================================
# Public API Functions
# ============================================================================


def read_note(vault_path: Path, note_path: str, mode: str = "full") -> NoteContent:
    """
    Read any markdown note in vault.

    Args:
        vault_path: Vault root path
        note_path: Relative path to note (e.g., "notes/ideas.md")
        mode: "full" (entire content), "preview" (first 1000 chars),
              "metadata" (frontmatter only), "structure" (headers only)

    Returns:
        NoteContent TypedDict with path, content, metadata, word_count

    Raises:
        FileNotFoundError: If note doesn't exist
        PermissionError: If note outside allowed folders
    """
    # 1. Validate permission
    _validate_note_access(vault_path, note_path)

    # 2. Call integration layer
    result = _read_note_file(vault_path, note_path, mode)

    # 3. Add context warnings if large
    config = load_config()
    result = _add_context_warnings(result, config)

    return result


def read_folder(
    vault_path: Path,
    folder_path: str,
    recursive: bool = False,
    exclude: List[str] | None = None,
    limit: int = 10,
    mode: str = "metadata",
) -> FolderReadResult:
    """
    Read all notes in folder with filtering.

    Args:
        vault_path: Vault root path
        folder_path: Relative folder path (e.g., "notes" or "Docs")
        recursive: Include subdirectories
        exclude: Folder names to skip (e.g., ["archive", "templates"])
        limit: Max notes to return (default 10, max 50)
        mode: Content mode (default "metadata" to avoid context exhaustion)

    Returns:
        FolderReadResult with notes list, total_count, has_more flag

    Raises:
        FileNotFoundError: If folder doesn't exist
        PermissionError: If folder outside allowed folders
    """
    # 1. Validate permission (check folder itself is allowed)
    if folder_path:  # Empty string means root, skip validation
        _validate_note_access(vault_path, folder_path)

    # 2. Enforce max limit
    config = load_config()
    max_limit = config.get("note_access", {}).get("max_folder_read", 50)
    if limit > max_limit:
        logger.warning(f"Requested limit {limit} exceeds max {max_limit}, using max")
        limit = max_limit

    # 3. Add default excludes from config
    config_excludes = config.get("note_access", {}).get("excluded_folders", [])
    all_excludes = list(set((exclude or []) + config_excludes))

    # 4. Call integration layer
    result = _read_folder(vault_path, folder_path, recursive, all_excludes, limit, mode)

    return result


def append_to_note(vault_path: Path, note_path: str, content: str) -> None:
    """
    Append content to end of note.

    Args:
        vault_path: Vault root path
        note_path: Relative path to note
        content: Content to append (will add newlines for spacing)

    Raises:
        FileNotFoundError: If note doesn't exist
        PermissionError: If note outside allowed folders
    """
    # 1. Validate permission
    _validate_note_access(vault_path, note_path)

    # 2. Call integration layer
    _append_to_note_file(vault_path, note_path, content)


def update_note_section(
    vault_path: Path, note_path: str, header: str, content: str
) -> None:
    """
    Replace content under specific header (## Header).

    Args:
        vault_path: Vault root path
        note_path: Relative path to note
        header: Header text (without ## prefix)
        content: New content for section (replaces everything until next header)

    Raises:
        FileNotFoundError: If note doesn't exist
        HeaderNotFoundError: If header doesn't exist in note
        PermissionError: If note outside allowed folders
    """
    # 1. Validate permission
    _validate_note_access(vault_path, note_path)

    # 2. Call integration layer (converts ValueError to HeaderNotFoundError)
    try:
        _update_note_section_file(vault_path, note_path, header, content)
    except ValueError as e:
        # Convert ValueError to HeaderNotFoundError for consistent API
        raise HeaderNotFoundError(header, note_path) from e


def search_notes_by_metadata(
    vault_path: Path, field: str, value: Any, limit: int = 20
) -> List[NoteInfo]:
    """
    Find notes where frontmatter[field] == value.

    Args:
        vault_path: Vault root path
        field: Frontmatter field name (e.g., "tags", "project", "status")
        value: Value to match (e.g., "SEO", "active", "work")
        limit: Max results (default 20)

    Returns:
        List of NoteInfo with path, title, metadata preview
    """
    # No permission check needed - searches within allowed folders only
    # Integration layer will skip files outside vault

    # Call integration layer
    results = _search_notes_by_metadata_file(vault_path, field, value, limit)

    return results


def create_note_in_folder(
    vault_path: Path,
    folder_path: str,
    title: str,
    content: str = "",
    metadata: Dict[str, Any] | None = None,
) -> Path:
    """
    Create note in arbitrary vault folder (not just notes/).

    Args:
        vault_path: Vault root path
        folder_path: Target folder (e.g., "Docs", "projects/work")
        title: Note title
        content: Note body (optional)
        metadata: Frontmatter fields (optional)

    Returns:
        Path to created note (relative to vault)

    Raises:
        FileExistsError: If note already exists
        PermissionError: If folder outside allowed folders
    """
    # 1. Validate permission
    _validate_note_access(vault_path, folder_path)

    # 2. Call integration layer
    note_path = _create_note_in_folder_file(
        vault_path, folder_path, title, content, metadata
    )

    return note_path


def list_vault_folders(vault_path: Path) -> Dict[str, Any]:
    """
    Get vault directory structure.

    Args:
        vault_path: Vault root path

    Returns:
        Dict with allowed_folders, excluded_folders, total_folders
    """
    config = load_config()
    allowed = _get_allowed_folders(config)
    excluded = config.get("note_access", {}).get("excluded_folders", [])

    # Count total folders in vault
    all_folders = [
        str(p.relative_to(vault_path))
        for p in vault_path.rglob("*")
        if p.is_dir() and not p.is_symlink()
    ]

    return {
        "vault_path": str(vault_path),
        "allowed_folders": allowed,
        "excluded_folders": excluded,
        "total_folders": len(all_folders),
        "all_folders": all_folders[:50],  # Limit to first 50 for context
    }
