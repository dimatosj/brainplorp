# ABOUTME: Tests for file utilities - validates reading, writing, and directory operations
# ABOUTME: Uses pytest's tmp_path fixture to create isolated test environments
"""Tests for file utilities."""
import pytest
from pathlib import Path
from brainplorp.utils.files import read_file, write_file, ensure_directory


def test_write_and_read_file(tmp_path):
    """Test writing and reading a file."""
    test_file = tmp_path / "test.txt"
    content = "Hello, plorp!"

    write_file(test_file, content)

    assert test_file.exists()
    assert read_file(test_file) == content


def test_write_file_overwrites(tmp_path):
    """Test that write_file overwrites existing content."""
    test_file = tmp_path / "test.txt"

    write_file(test_file, "First content")
    write_file(test_file, "Second content")

    assert read_file(test_file) == "Second content"


def test_read_file_not_found(tmp_path):
    """Test read_file raises error for non-existent file."""
    nonexistent = tmp_path / "nope.txt"

    with pytest.raises(FileNotFoundError):
        read_file(nonexistent)


def test_ensure_directory_creates(tmp_path):
    """Test ensure_directory creates directory."""
    new_dir = tmp_path / "vault" / "daily"

    ensure_directory(new_dir)

    assert new_dir.exists()
    assert new_dir.is_dir()


def test_ensure_directory_exists(tmp_path):
    """Test ensure_directory works if directory already exists."""
    existing_dir = tmp_path / "vault"
    existing_dir.mkdir()

    # Should not raise error
    ensure_directory(existing_dir)

    assert existing_dir.exists()


def test_write_file_unicode(tmp_path):
    """Test writing and reading unicode content."""
    test_file = tmp_path / "unicode.txt"
    content = "✓ Task completed! 日本語 Émojis: 🚀"

    write_file(test_file, content)

    assert read_file(test_file) == content


def test_read_file_with_str_path(tmp_path):
    """Test read_file accepts string path."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")

    # Pass as string, not Path
    result = read_file(str(test_file))

    assert result == "content"


def test_write_file_with_str_path(tmp_path):
    """Test write_file accepts string path."""
    test_file = tmp_path / "test.txt"

    # Pass as string, not Path
    write_file(str(test_file), "content")

    assert test_file.read_text() == "content"


def test_ensure_directory_with_str_path(tmp_path):
    """Test ensure_directory accepts string path."""
    new_dir = tmp_path / "newdir"

    ensure_directory(str(new_dir))

    assert new_dir.exists()
