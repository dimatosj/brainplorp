# ABOUTME: Integration layer for general note I/O operations in Obsidian vault
# ABOUTME: Pure file operations with no permissions or business logic - called by core layer
"""
Integration for reading and writing notes in Obsidian vault.

This module provides low-level file I/O operations. It does NOT:
- Check permissions (core layer does that)
- Validate config (core layer does that)
- Add context warnings (core layer does that)

All functions are internal (_prefixed) and should only be called by core layer.
"""

import os
import re
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


def _read_note_file(vault_path: Path, note_path: str, mode: str) -> Dict[str, Any]:
    """
    Read markdown note from vault (pure I/O).

    Args:
        vault_path: Vault root path
        note_path: Relative path to note (e.g., "notes/ideas.md")
        mode: "full", "preview", "metadata", or "structure"

    Returns:
        Dict with path, content, metadata, word_count, headers, mode

    Raises:
        FileNotFoundError: If note doesn't exist
        UnicodeDecodeError: If file is not UTF-8
    """
    file_path = vault_path / note_path

    if not file_path.exists():
        raise FileNotFoundError(f"Note not found: {note_path}")

    # Read full content (UTF-8 only, per Q16)
    content = file_path.read_text(encoding="utf-8")

    # Split frontmatter and body
    frontmatter, body = _split_frontmatter_and_body(content)

    # Extract title (from frontmatter or first # header)
    title = _extract_title(frontmatter, body)

    # Extract headers
    headers = _extract_header_list(body)

    # Calculate word count
    word_count = len(body.split())

    # Apply mode (full/preview/metadata/structure)
    if mode == "preview":
        content = content[:1000] + "..." if len(content) > 1000 else content
    elif mode == "metadata":
        content = ""  # Metadata only, no content
    elif mode == "structure":
        content = "\n".join(headers)  # Headers only

    return {
        "path": str(note_path),
        "title": title,
        "content": content,
        "metadata": frontmatter if frontmatter else {},
        "word_count": word_count,
        "headers": headers,
        "mode": mode,
        "warnings": [],  # Empty here, core layer adds warnings
    }


def _read_folder(
    vault_path: Path,
    folder_path: str,
    recursive: bool,
    exclude: List[str],
    limit: int,
    mode: str,
) -> Dict[str, Any]:
    """
    Read all notes in folder (pure I/O).

    Args:
        vault_path: Vault root path
        folder_path: Relative folder path (e.g., "notes")
        recursive: Include subdirectories
        exclude: Folder names to skip
        limit: Max notes to return
        mode: Content mode for each note

    Returns:
        Dict with folder_path, notes, total_count, returned_count, has_more

    Raises:
        FileNotFoundError: If folder doesn't exist
    """
    folder = vault_path / folder_path

    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    if not folder.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder_path}")

    # Find all markdown files
    pattern = "**/*.md" if recursive else "*.md"
    all_paths = []

    for path in folder.glob(pattern):
        # Skip symlinks (per Q20)
        if path.is_symlink():
            continue

        # Skip excluded folders
        if exclude:
            rel_path = path.relative_to(vault_path)
            if any(excluded in rel_path.parts for excluded in exclude):
                continue

        all_paths.append(path)

    total_count = len(all_paths)

    # Limit results
    paths_to_read = all_paths[:limit]
    has_more = total_count > limit

    # Read each note
    notes = []
    for path in paths_to_read:
        rel_path = path.relative_to(vault_path)
        note_data = _read_note_file(vault_path, str(rel_path), mode)

        # Convert to NoteInfo format (metadata only)
        stat = path.stat()
        notes.append(
            {
                "path": str(rel_path),
                "title": note_data["title"],
                "metadata": note_data["metadata"],
                "word_count": note_data["word_count"],
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
        )

    return {
        "folder_path": folder_path,
        "notes": notes,
        "total_count": total_count,
        "returned_count": len(notes),
        "has_more": has_more,
        "excluded_folders": exclude if exclude else [],
    }


def _append_to_note_file(vault_path: Path, note_path: str, content: str) -> None:
    """
    Append content to end of note (pure I/O).

    Args:
        vault_path: Vault root path
        note_path: Relative path to note
        content: Content to append

    Raises:
        FileNotFoundError: If note doesn't exist
    """
    file_path = vault_path / note_path

    if not file_path.exists():
        raise FileNotFoundError(f"Note not found: {note_path}")

    current = file_path.read_text(encoding="utf-8")

    # Always add two newlines (blank line separator, per Q23)
    new_content = current.rstrip() + "\n\n" + content

    file_path.write_text(new_content, encoding="utf-8")


def _update_note_section_file(
    vault_path: Path, note_path: str, header: str, content: str
) -> None:
    """
    Replace content under specific header (pure I/O).

    Args:
        vault_path: Vault root path
        note_path: Relative path to note
        header: Header text (without ## prefix)
        content: New content for section

    Raises:
        FileNotFoundError: If note doesn't exist
        ValueError: If header not found (core layer converts to HeaderNotFoundError)
    """
    file_path = vault_path / note_path

    if not file_path.exists():
        raise FileNotFoundError(f"Note not found: {note_path}")

    file_content = file_path.read_text(encoding="utf-8")
    lines = file_content.split("\n")

    # Find header (per Q8: replace until next same-level header)
    header_pattern = re.compile(r"^(#{1,6})\s+" + re.escape(header) + r"\s*$")
    header_line = None
    header_level = None

    for i, line in enumerate(lines):
        match = header_pattern.match(line)
        if match:
            header_line = i
            header_level = len(match.group(1))  # Count # symbols
            break

    if header_line is None:
        raise ValueError(f"Header '{header}' not found in note")

    # Find next header at same level (or end of file)
    next_header = len(lines)  # Default to end of file
    for i in range(header_line + 1, len(lines)):
        if lines[i].startswith("#" * header_level + " "):
            next_header = i
            break

    # Replace section
    new_lines = (
        lines[: header_line + 1]  # Keep header line
        + [content]  # New content
        + lines[next_header:]  # Keep rest
    )

    file_path.write_text("\n".join(new_lines), encoding="utf-8")


def _search_notes_by_metadata_file(
    vault_path: Path, field: str, value: Any, limit: int
) -> List[Dict[str, Any]]:
    """
    Find notes where frontmatter[field] == value (pure I/O).

    Args:
        vault_path: Vault root path
        field: Frontmatter field name
        value: Value to match
        limit: Max results

    Returns:
        List of NoteInfo dicts
    """
    results = []

    for md_file in vault_path.rglob("*.md"):
        # Skip symlinks (per Q20)
        if md_file.is_symlink():
            continue

        # Read only frontmatter (per Q9 - performance optimization)
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                lines = []
                in_frontmatter = False
                found_opening = False

                for line in f:
                    if line.strip() == "---":
                        if not found_opening:
                            found_opening = True
                            in_frontmatter = True
                            continue
                        else:
                            # End of frontmatter, stop reading
                            break

                    if in_frontmatter:
                        lines.append(line)

            # Parse YAML from collected lines
            if lines:
                frontmatter = yaml.safe_load("".join(lines))
                if frontmatter and isinstance(frontmatter, dict):
                    fm_value = frontmatter.get(field)

                    # Smart matching (per Q14)
                    if isinstance(fm_value, list):
                        match = value in fm_value
                    else:
                        match = fm_value == value

                    if match:
                        # Get title and word count
                        content = md_file.read_text(encoding="utf-8")
                        _, body = _split_frontmatter_and_body(content)
                        title = _extract_title(frontmatter, body)
                        word_count = len(body.split())

                        rel_path = md_file.relative_to(vault_path)
                        stat = md_file.stat()

                        results.append(
                            {
                                "path": str(rel_path),
                                "title": title,
                                "metadata": frontmatter,
                                "word_count": word_count,
                                "created": datetime.fromtimestamp(
                                    stat.st_ctime
                                ).isoformat(),
                                "modified": datetime.fromtimestamp(
                                    stat.st_mtime
                                ).isoformat(),
                            }
                        )

                        if len(results) >= limit:
                            return results

        except (UnicodeDecodeError, yaml.YAMLError):
            # Skip files with encoding or YAML errors (per Q5 - lenient)
            continue

    return results


def _create_note_in_folder_file(
    vault_path: Path,
    folder_path: str,
    title: str,
    content: str,
    metadata: Dict[str, Any] | None,
) -> Path:
    """
    Create note in folder (pure I/O).

    Args:
        vault_path: Vault root path
        folder_path: Target folder
        title: Note title
        content: Note body
        metadata: Frontmatter fields

    Returns:
        Path to created note

    Raises:
        FileExistsError: If note already exists (per Q24)
    """
    folder = vault_path / folder_path
    folder.mkdir(parents=True, exist_ok=True)

    note_path = folder / f"{title}.md"

    if note_path.exists():
        raise FileExistsError(
            f"Note already exists: {folder_path}/{title}.md. "
            "Use append_to_note() or update_note_section() to modify."
        )

    # Build note content with frontmatter
    note_content = ""
    if metadata:
        note_content = "---\n"
        note_content += yaml.dump(metadata, default_flow_style=False)
        note_content += "---\n\n"

    note_content += content

    note_path.write_text(note_content, encoding="utf-8")

    return note_path.relative_to(vault_path)


# ============================================================================
# Helper Functions
# ============================================================================


def _split_frontmatter_and_body(content: str) -> tuple[Dict[str, Any] | None, str]:
    """
    Split markdown content into frontmatter and body.

    Returns:
        (frontmatter_dict, body_text)
        frontmatter_dict is None if no valid frontmatter found
    """
    lines = content.split("\n")

    if not lines or lines[0].strip() != "---":
        return None, content

    # Find closing ---
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return None, content

    # Parse frontmatter
    fm_lines = lines[1:end_idx]
    body_lines = lines[end_idx + 1 :]

    try:
        frontmatter = yaml.safe_load("\n".join(fm_lines))
        if not isinstance(frontmatter, dict):
            frontmatter = None
    except yaml.YAMLError:
        frontmatter = None  # Per Q5 - lenient parsing

    return frontmatter, "\n".join(body_lines)


def _extract_title(frontmatter: Dict[str, Any] | None, body: str) -> str:
    """
    Extract note title from frontmatter or first # header.

    Returns:
        Title string (or "Untitled" if none found)
    """
    # Try frontmatter first
    if frontmatter and "title" in frontmatter:
        return str(frontmatter["title"])

    # Try first # header
    lines = body.split("\n")
    for line in lines:
        if line.startswith("# "):
            return line[2:].strip()

    return "Untitled"


def _extract_header_list(body: str) -> List[str]:
    """
    Extract list of header texts (## level and below).

    Returns:
        List of header texts (without # prefix)
    """
    headers = []
    lines = body.split("\n")

    for line in lines:
        match = re.match(r"^(#{2,6})\s+(.+)$", line)
        if match:
            headers.append(match.group(2).strip())

    return headers
