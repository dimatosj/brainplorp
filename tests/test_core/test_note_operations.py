"""
Tests for core/note_operations.py

Tests high-level API with permission checks, warnings, and business logic.
"""

import pytest
from pathlib import Path
import yaml

from plorp.core.note_operations import (
    read_note,
    read_folder,
    append_to_note,
    update_note_section,
    search_notes_by_metadata,
    create_note_in_folder,
    list_vault_folders,
    _validate_note_access,
    _get_allowed_folders,
    _add_context_warnings,
)
from plorp.core.exceptions import HeaderNotFoundError


@pytest.fixture
def test_vault_with_config(tmp_path):
    """Create test vault and config file."""
    vault = tmp_path / "test_vault"
    vault.mkdir()

    # Create folder structure
    (vault / "notes").mkdir()
    (vault / "projects").mkdir()
    (vault / "Docs").mkdir()
    (vault / "forbidden").mkdir()  # Not in allowed list

    # Create test notes
    (vault / "notes" / "test.md").write_text(
        "---\ntags: [test]\ntitle: Test\n---\n\n# Test\n\nContent"
    )

    (vault / "forbidden" / "secret.md").write_text("# Secret\n\nNot allowed")

    # Create large note (>10k words)
    large_content = "---\ntitle: Large\n---\n\n" + ("word " * 11000)
    (vault / "Docs" / "large.md").write_text(large_content)

    # Create config file
    config_dir = tmp_path / ".config" / "plorp"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.yaml"

    config = {
        "vault_path": str(vault),
        "note_access": {
            "allowed_folders": ["notes", "projects", "Docs"],
            "excluded_folders": [".obsidian", ".trash"],
            "max_folder_read": 50,
            "warn_large_file_words": 10000,
        },
    }

    with open(config_path, "w") as f:
        yaml.dump(config, f)

    # Set XDG_CONFIG_HOME for config loading
    import os

    os.environ["XDG_CONFIG_HOME"] = str(tmp_path / ".config")

    return vault


# ============================================================================
# Test Permission Validation
# ============================================================================


def test_validate_note_access_allowed(test_vault_with_config):
    """Test accessing note in allowed folder succeeds."""
    # Should not raise
    _validate_note_access(test_vault_with_config, "notes/test.md")


def test_validate_note_access_denied(test_vault_with_config):
    """Test accessing note in forbidden folder raises PermissionError."""
    with pytest.raises(PermissionError, match="Access denied"):
        _validate_note_access(test_vault_with_config, "forbidden/secret.md")


def test_read_note_permission_check(test_vault_with_config):
    """Test read_note enforces permissions."""
    # Allowed
    result = read_note(test_vault_with_config, "notes/test.md")
    assert result["path"] == "notes/test.md"

    # Forbidden
    with pytest.raises(PermissionError, match="Access denied"):
        read_note(test_vault_with_config, "forbidden/secret.md")


def test_append_to_note_permission_check(test_vault_with_config):
    """Test append_to_note enforces permissions."""
    # Allowed
    append_to_note(test_vault_with_config, "notes/test.md", "Appended")
    content = (test_vault_with_config / "notes" / "test.md").read_text()
    assert "Appended" in content

    # Forbidden
    with pytest.raises(PermissionError, match="Access denied"):
        append_to_note(test_vault_with_config, "forbidden/secret.md", "Content")


def test_create_note_permission_check(test_vault_with_config):
    """Test create_note_in_folder enforces permissions."""
    # Allowed
    path = create_note_in_folder(
        test_vault_with_config, "notes", "New Note", "Content"
    )
    assert path == Path("notes/New Note.md")

    # Forbidden
    with pytest.raises(PermissionError, match="Access denied"):
        create_note_in_folder(test_vault_with_config, "forbidden", "Note", "Content")


# ============================================================================
# Test Context Warnings
# ============================================================================


def test_add_context_warnings_large_file():
    """Test adding warnings for large files."""
    result = {"word_count": 15000, "warnings": []}
    config = {"note_access": {"warn_large_file_words": 10000}}

    result = _add_context_warnings(result, config)

    assert len(result["warnings"]) > 0
    assert "Large file" in result["warnings"][0]
    assert "15000 words" in result["warnings"][0]


def test_add_context_warnings_small_file():
    """Test no warnings for small files."""
    result = {"word_count": 5000, "warnings": []}
    config = {"note_access": {"warn_large_file_words": 10000}}

    result = _add_context_warnings(result, config)

    assert len(result["warnings"]) == 0


def test_read_note_adds_warning_for_large_file(test_vault_with_config):
    """Test read_note adds warning for large file."""
    result = read_note(test_vault_with_config, "Docs/large.md", mode="full")

    assert len(result["warnings"]) > 0
    assert "Large file" in result["warnings"][0]


# ============================================================================
# Test Folder Operations
# ============================================================================


def test_read_folder_respects_max_limit(test_vault_with_config):
    """Test read_folder enforces max limit from config."""
    # Request 100, but config max is 50
    result = read_folder(test_vault_with_config, "notes", limit=100)

    # Should be capped at 50
    assert result["returned_count"] <= 50


def test_read_folder_merges_config_excludes(test_vault_with_config):
    """Test read_folder merges user excludes with config excludes."""
    result = read_folder(
        test_vault_with_config, "", recursive=True, exclude=["archive"]
    )

    # Should include both user excludes and config excludes
    assert "archive" in result["excluded_folders"]
    assert ".obsidian" in result["excluded_folders"]  # From config


# ============================================================================
# Test Search Operations
# ============================================================================


def test_search_notes_by_metadata(test_vault_with_config):
    """Test searching notes by metadata field."""
    results = search_notes_by_metadata(test_vault_with_config, "tags", "test")

    assert len(results) >= 1
    assert any(r["title"] == "Test" for r in results)


# ============================================================================
# Test Update Operations
# ============================================================================


def test_update_note_section_converts_to_header_not_found_error(
    test_vault_with_config,
):
    """Test update_note_section converts ValueError to HeaderNotFoundError."""
    # Create note without the header
    (test_vault_with_config / "notes" / "no_header.md").write_text(
        "# Title\n\nContent"
    )

    with pytest.raises(HeaderNotFoundError, match="Missing Section"):
        update_note_section(
            test_vault_with_config, "notes/no_header.md", "Missing Section", "Content"
        )


# ============================================================================
# Test List Vault Folders
# ============================================================================


def test_list_vault_folders(test_vault_with_config):
    """Test listing vault directory structure."""
    result = list_vault_folders(test_vault_with_config)

    assert result["vault_path"] == str(test_vault_with_config)
    assert "notes" in result["allowed_folders"]
    assert ".obsidian" in result["excluded_folders"]
    assert result["total_folders"] > 0
