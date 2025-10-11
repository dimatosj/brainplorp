# ABOUTME: File I/O utilities for reading and writing markdown files in the vault
# ABOUTME: Provides safe file operations with directory creation and error handling
"""
File I/O utilities.

Helper functions for reading and writing files in the Obsidian vault.
"""
from pathlib import Path
from typing import Union


def read_file(path: Union[str, Path]) -> str:
    """
    Read entire file content as string.

    Args:
        path: Path to file to read

    Returns:
        File content as string

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file can't be read

    Example:
        >>> content = read_file('vault/daily/2025-10-06.md')
        >>> print(content)
    """
    path = Path(path)
    return path.read_text(encoding="utf-8")


def write_file(path: Union[str, Path], content: str) -> None:
    """
    Write content to file, overwriting if exists.

    Args:
        path: Path to file to write
        content: Content to write

    Raises:
        IOError: If file can't be written

    Example:
        >>> write_file('vault/daily/2025-10-06.md', '# Daily Note\\n\\n...')
    """
    path = Path(path)
    path.write_text(content, encoding="utf-8")


def ensure_directory(path: Union[str, Path]) -> None:
    """
    Ensure directory exists, creating it and parents if needed.

    Args:
        path: Path to directory

    Example:
        >>> ensure_directory('vault/daily')
        >>> # vault/daily/ now exists
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
