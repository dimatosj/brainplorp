# ABOUTME: Obsidian vault integration - creates and manages note files in the vault
# ABOUTME: Handles note file naming, front matter generation, and directory management
"""
Obsidian integration.

Provides functions for creating and managing notes in an Obsidian vault.
"""
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import yaml


def create_note(
    vault_path: Path,
    title: str,
    note_type: str = "general",
    content: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Create a new note in the Obsidian vault.

    Args:
        vault_path: Path to Obsidian vault root
        title: Note title
        note_type: Type of note ('general', 'meeting', 'project', etc.)
        content: Note body content (optional)
        metadata: Additional front matter fields (optional)

    Returns:
        Path to created note file

    Raises:
        IOError: If note can't be written

    Example:
        >>> vault = Path('~/vault')
        >>> note = create_note(vault, "Project Ideas", note_type="project")
        >>> print(f"Created: {note}")
    """
    from plorp.utils.files import write_file, ensure_directory

    # Determine subdirectory based on note type
    if note_type == "meeting":
        note_dir = vault_path / "meetings"
    else:
        note_dir = vault_path / "notes"

    # Create directory if needed
    ensure_directory(note_dir)

    # Generate filename from title and date
    slug = generate_slug(title)
    date_str = datetime.now().strftime("%Y-%m-%d")

    # Check for existing files and add counter if needed
    base_filename = f"{slug}-{date_str}"
    filename = f"{base_filename}.md"
    note_path = note_dir / filename

    counter = 2
    while note_path.exists():
        filename = f"{base_filename}-{counter}.md"
        note_path = note_dir / filename
        counter += 1

    # Build front matter
    front_matter = {
        "title": title,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": note_type,
    }

    # Merge with provided metadata
    if metadata:
        front_matter.update(metadata)

    # Build note content
    note_content = "---\n"
    note_content += yaml.dump(front_matter, default_flow_style=False, sort_keys=False)
    note_content += "---\n\n"
    note_content += f"# {title}\n\n"

    if content:
        note_content += f"{content}\n"

    # Write note
    write_file(note_path, note_content)

    return note_path


def generate_slug(title: str) -> str:
    """
    Generate URL-friendly slug from title.

    Args:
        title: Note title

    Returns:
        Slugified string (lowercase, hyphens, alphanumeric)

    Example:
        >>> generate_slug("Project Ideas & TODOs")
        'project-ideas-todos'
    """
    import re

    # Convert to lowercase
    slug = title.lower()

    # Replace spaces and special chars with hyphens
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)

    # Remove leading/trailing hyphens
    slug = slug.strip("-")

    return slug


def get_vault_path(config: Dict[str, Any]) -> Path:
    """
    Get vault path from config.

    Args:
        config: Configuration dictionary

    Returns:
        Path to vault

    Raises:
        ValueError: If vault_path not in config

    Example:
        >>> config = load_config()
        >>> vault = get_vault_path(config)
    """
    if "vault_path" not in config:
        raise ValueError("vault_path not configured")

    return Path(config["vault_path"]).expanduser()
