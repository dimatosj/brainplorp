# ABOUTME: Tests for Obsidian integration - validates note creation and slug generation
# ABOUTME: Uses temporary directories to test file creation without affecting real vault
"""Tests for Obsidian integration."""
import pytest
from pathlib import Path
from plorp.integrations.obsidian import create_note, generate_slug, get_vault_path


def test_generate_slug_basic():
    """Test basic slug generation."""
    assert generate_slug("Simple Title") == "simple-title"


def test_generate_slug_special_chars():
    """Test slug with special characters."""
    assert generate_slug("Project: Ideas & TODOs!") == "project-ideas-todos"


def test_generate_slug_multiple_spaces():
    """Test slug with multiple spaces."""
    assert generate_slug("Too    Many     Spaces") == "too-many-spaces"


def test_generate_slug_leading_trailing():
    """Test slug with leading/trailing spaces and hyphens."""
    assert generate_slug("  - Title -  ") == "title"


def test_create_note_basic(tmp_path):
    """Test creating basic note."""
    vault = tmp_path / "vault"
    vault.mkdir()

    note_path = create_note(vault, "Test Note")

    assert note_path.exists()
    assert note_path.parent == vault / "notes"
    assert "test-note" in note_path.name
    assert note_path.suffix == ".md"


def test_create_note_meeting_type(tmp_path):
    """Test creating meeting note in meetings directory."""
    vault = tmp_path / "vault"
    vault.mkdir()

    note_path = create_note(vault, "Team Meeting", note_type="meeting")

    assert note_path.exists()
    assert note_path.parent == vault / "meetings"
    assert "team-meeting" in note_path.name


def test_create_note_content(tmp_path):
    """Test note contains correct content."""
    vault = tmp_path / "vault"
    vault.mkdir()

    note_path = create_note(
        vault, "Meeting Notes", note_type="meeting", content="Discussed project timeline."
    )

    content = note_path.read_text()

    assert "---" in content  # Has front matter
    assert "title: Meeting Notes" in content
    assert "type: meeting" in content
    assert "# Meeting Notes" in content
    assert "Discussed project timeline." in content


def test_create_note_with_metadata(tmp_path):
    """Test creating note with custom metadata."""
    vault = tmp_path / "vault"
    vault.mkdir()

    metadata = {"project": "plorp", "tags": ["development", "planning"]}

    note_path = create_note(vault, "Sprint Planning", metadata=metadata)

    content = note_path.read_text()

    assert "project: plorp" in content
    assert "tags:" in content
    assert "- development" in content
    assert "- planning" in content


def test_create_note_creates_directory(tmp_path):
    """Test that create_note creates notes directory if not exists."""
    vault = tmp_path / "vault"
    vault.mkdir()

    notes_dir = vault / "notes"
    assert not notes_dir.exists()

    create_note(vault, "Test")

    assert notes_dir.exists()


def test_create_note_duplicate_handling(tmp_path):
    """Test that duplicate note names get counters."""
    vault = tmp_path / "vault"
    vault.mkdir()

    # Create first note
    note1 = create_note(vault, "Same Title")
    assert "same-title" in note1.name
    # First note has date but no counter suffix like -2, -3
    assert note1.name.count("-") == 4  # same-title-YYYY-MM-DD.md has 4 hyphens

    # Create second note with same title on same day
    note2 = create_note(vault, "Same Title")
    assert "same-title" in note2.name
    # Second note should have -2 suffix
    assert note2.name.endswith("-2.md")

    # Create third note
    note3 = create_note(vault, "Same Title")
    assert "same-title" in note3.name
    # Third note should have -3 suffix
    assert note3.name.endswith("-3.md")

    # All should exist
    assert note1.exists()
    assert note2.exists()
    assert note3.exists()


def test_get_vault_path_valid():
    """Test getting vault path from config."""
    config = {"vault_path": "~/vault"}

    vault = get_vault_path(config)

    assert isinstance(vault, Path)
    assert str(vault) != "~/vault"  # Should be expanded


def test_get_vault_path_missing():
    """Test get_vault_path with missing vault_path."""
    config = {}

    with pytest.raises(ValueError, match="vault_path"):
        get_vault_path(config)


def test_create_note_empty_content(tmp_path):
    """Test creating note with no content."""
    vault = tmp_path / "vault"
    vault.mkdir()

    note_path = create_note(vault, "Empty Note", content="")

    content = note_path.read_text()

    assert "# Empty Note" in content
    # Should have front matter and title, but no body content beyond that


def test_generate_slug_unicode():
    """Test slug generation with unicode characters."""
    # Python's \w includes unicode letters by default
    assert generate_slug("Café Notes") == "café-notes"


def test_generate_slug_numbers():
    """Test slug with numbers."""
    assert generate_slug("Sprint 4 Planning") == "sprint-4-planning"
