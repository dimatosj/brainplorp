"""
Tests for integrations/obsidian_notes.py

Tests pure I/O functions for reading and writing notes in Obsidian vault.
Uses synthetic test vault (per Q17) - does not modify user's real vault.
"""

import pytest
from pathlib import Path
from datetime import datetime

from brainplorp.integrations.obsidian_notes import (
    _read_note_file,
    _read_folder,
    _append_to_note_file,
    _update_note_section_file,
    _search_notes_by_metadata_file,
    _create_note_in_folder_file,
    _split_frontmatter_and_body,
    _extract_title,
    _extract_header_list,
)


@pytest.fixture
def test_vault(tmp_path):
    """Create synthetic test vault with known structure."""
    vault = tmp_path / "test_vault"
    vault.mkdir()

    # Create folder structure
    (vault / "notes").mkdir()
    (vault / "projects").mkdir()
    (vault / "Docs").mkdir()
    (vault / "archive").mkdir()  # For exclusion testing

    # Create test note with frontmatter
    (vault / "notes" / "test.md").write_text(
        "---\ntags: [SEO, test]\ntitle: Test Note\n---\n\n"
        "# Test Note\n\n"
        "Content here.\n\n"
        "## Section 1\n\n"
        "Some content.\n\n"
        "## Section 2\n\n"
        "More content."
    )

    # Create note without frontmatter
    (vault / "notes" / "simple.md").write_text(
        "# Simple Note\n\nJust content, no frontmatter."
    )

    # Create large note (for warning testing)
    large_content = "---\ntitle: Large Doc\n---\n\n" + ("word " * 11000)
    (vault / "Docs" / "large.md").write_text(large_content)

    # Create note in archive folder (for exclusion testing)
    (vault / "archive" / "old.md").write_text("# Old Note\n\nArchived content.")

    # Create multiple notes with SEO tag
    (vault / "notes" / "seo1.md").write_text(
        "---\ntags: SEO\ntitle: SEO Note 1\n---\n\nSEO content 1"
    )
    (vault / "notes" / "seo2.md").write_text(
        "---\ntags: [SEO, marketing]\ntitle: SEO Note 2\n---\n\nSEO content 2"
    )

    return vault


# ============================================================================
# Test _read_note_file
# ============================================================================


def test_read_note_full_mode(test_vault):
    """Test reading note in full mode."""
    result = _read_note_file(test_vault, "notes/test.md", "full")

    assert result["path"] == "notes/test.md"
    assert result["title"] == "Test Note"
    assert "Content here" in result["content"]
    assert result["metadata"]["tags"] == ["SEO", "test"]
    assert result["word_count"] > 0
    assert "Section 1" in result["headers"]
    assert "Section 2" in result["headers"]
    assert result["mode"] == "full"


def test_read_note_preview_mode(test_vault):
    """Test reading note in preview mode (truncated)."""
    # Create a note with >1000 characters
    long_content = "# Long Note\n\n" + ("word " * 500)
    (test_vault / "notes" / "long.md").write_text(long_content)

    result = _read_note_file(test_vault, "notes/long.md", "preview")

    assert result["mode"] == "preview"
    assert result["content"].endswith("...")
    assert len(result["content"]) <= 1003  # 1000 + "..."


def test_read_note_metadata_mode(test_vault):
    """Test reading note in metadata mode (no content)."""
    result = _read_note_file(test_vault, "notes/test.md", "metadata")

    assert result["mode"] == "metadata"
    assert result["content"] == ""  # No content in metadata mode
    assert result["metadata"]["tags"] == ["SEO", "test"]
    assert result["word_count"] > 0  # Still calculated


def test_read_note_structure_mode(test_vault):
    """Test reading note in structure mode (headers only)."""
    result = _read_note_file(test_vault, "notes/test.md", "structure")

    assert result["mode"] == "structure"
    assert "Section 1" in result["content"]
    assert "Section 2" in result["content"]
    # Body content should not be in result
    assert "Content here" not in result["content"]


def test_read_note_not_found(test_vault):
    """Test reading non-existent note raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Note not found"):
        _read_note_file(test_vault, "notes/missing.md", "full")


def test_read_note_without_frontmatter(test_vault):
    """Test reading note without frontmatter."""
    result = _read_note_file(test_vault, "notes/simple.md", "full")

    assert result["path"] == "notes/simple.md"
    assert result["title"] == "Simple Note"  # From # header
    assert result["metadata"] == {}  # Empty dict (per Q25)
    assert "Just content" in result["content"]


# ============================================================================
# Test _read_folder
# ============================================================================


def test_read_folder_with_limit(test_vault):
    """Test reading folder respects limit."""
    result = _read_folder(
        test_vault,
        "notes",
        recursive=False,
        exclude=None,
        limit=2,
        mode="metadata",
    )

    assert result["folder_path"] == "notes"
    assert result["returned_count"] == 2
    assert result["total_count"] >= 2
    assert result["has_more"] is True  # We have more than 2 notes


def test_read_folder_recursive(test_vault):
    """Test reading folder recursively includes subdirectories."""
    # Create subdirectory with note
    (test_vault / "notes" / "sub").mkdir()
    (test_vault / "notes" / "sub" / "nested.md").write_text("# Nested\n\nContent")

    result = _read_folder(
        test_vault,
        "notes",
        recursive=True,
        exclude=None,
        limit=50,
        mode="metadata",
    )

    paths = [note["path"] for note in result["notes"]]
    assert any("sub/nested.md" in path for path in paths)


def test_read_folder_with_exclude(test_vault):
    """Test reading folder excludes specified folders."""
    result = _read_folder(
        test_vault,
        "",  # Root folder
        recursive=True,
        exclude=["archive"],
        limit=50,
        mode="metadata",
    )

    paths = [note["path"] for note in result["notes"]]
    # Should not include archived note
    assert not any("archive" in path for path in paths)


def test_read_folder_not_found(test_vault):
    """Test reading non-existent folder raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Folder not found"):
        _read_folder(test_vault, "missing", False, None, 10, "metadata")


# ============================================================================
# Test _append_to_note_file
# ============================================================================


def test_append_to_note(test_vault):
    """Test appending content to existing note."""
    original = (test_vault / "notes" / "test.md").read_text()

    _append_to_note_file(test_vault, "notes/test.md", "Appended content")

    updated = (test_vault / "notes" / "test.md").read_text()
    assert "Appended content" in updated
    assert updated.startswith(original.rstrip())
    # Check for blank line separator (per Q23)
    assert "\n\nAppended content" in updated


def test_append_to_note_not_found(test_vault):
    """Test appending to non-existent note raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Note not found"):
        _append_to_note_file(test_vault, "notes/missing.md", "Content")


# ============================================================================
# Test _update_note_section_file
# ============================================================================


def test_update_note_section(test_vault):
    """Test updating section under header."""
    _update_note_section_file(
        test_vault, "notes/test.md", "Section 1", "New content for section 1"
    )

    content = (test_vault / "notes" / "test.md").read_text()
    assert "New content for section 1" in content
    # Section 2 should still exist
    assert "## Section 2" in content


def test_update_note_section_header_not_found(test_vault):
    """Test updating non-existent header raises ValueError."""
    with pytest.raises(ValueError, match="Header .* not found"):
        _update_note_section_file(
            test_vault, "notes/test.md", "Missing Section", "Content"
        )


def test_update_note_section_replaces_until_next_same_level(test_vault):
    """Test section update replaces until next same-level header (per Q8)."""
    # Create note with nested headers
    (test_vault / "notes" / "nested.md").write_text(
        "## Sprint 9\n\n"
        "Content\n\n"
        "### Goals\n\n"
        "- Goal 1\n\n"
        "### Architecture\n\n"
        "- Design 1\n\n"
        "## Sprint 10\n\n"
        "Next sprint"
    )

    _update_note_section_file(
        test_vault, "notes/nested.md", "Sprint 9", "New sprint 9 content"
    )

    content = (test_vault / "notes" / "nested.md").read_text()
    assert "New sprint 9 content" in content
    # Subsections should be removed (replaced)
    assert "### Goals" not in content
    assert "### Architecture" not in content
    # Next section should still exist
    assert "## Sprint 10" in content
    assert "Next sprint" in content


# ============================================================================
# Test _search_notes_by_metadata_file
# ============================================================================


def test_search_notes_by_tag(test_vault):
    """Test searching notes by tag."""
    results = _search_notes_by_metadata_file(test_vault, "tags", "SEO", limit=20)

    assert len(results) >= 2  # seo1.md and seo2.md
    titles = [r["title"] for r in results]
    assert "SEO Note 1" in titles or "SEO Note 2" in titles


def test_search_notes_by_field_list_value(test_vault):
    """Test searching with list value (per Q14 - smart match)."""
    # seo2.md has tags: [SEO, marketing]
    results = _search_notes_by_metadata_file(test_vault, "tags", "marketing", limit=20)

    assert len(results) >= 1
    assert any(r["title"] == "SEO Note 2" for r in results)


def test_search_notes_by_field_scalar_value(test_vault):
    """Test searching with scalar value (per Q14 - smart match)."""
    # seo1.md has tags: SEO (scalar, not list)
    results = _search_notes_by_metadata_file(test_vault, "tags", "SEO", limit=20)

    assert len(results) >= 2  # Should find both seo1 and seo2


def test_search_notes_respects_limit(test_vault):
    """Test search respects limit parameter."""
    results = _search_notes_by_metadata_file(test_vault, "tags", "SEO", limit=1)

    assert len(results) == 1


# ============================================================================
# Test _create_note_in_folder_file
# ============================================================================


def test_create_note_in_folder(test_vault):
    """Test creating note in folder."""
    metadata = {"tags": ["test"], "created": "2025-10-09"}
    path = _create_note_in_folder_file(
        test_vault, "notes", "New Note", "Content here", metadata
    )

    assert path == Path("notes/New Note.md")
    content = (test_vault / "notes" / "New Note.md").read_text()
    assert "tags:" in content
    assert "Content here" in content


def test_create_note_without_metadata(test_vault):
    """Test creating note without metadata."""
    path = _create_note_in_folder_file(
        test_vault, "notes", "No Meta", "Just content", None
    )

    assert path == Path("notes/No Meta.md")
    content = (test_vault / "notes" / "No Meta.md").read_text()
    assert not content.startswith("---")  # No frontmatter
    assert content == "Just content"


def test_create_note_already_exists(test_vault):
    """Test creating note that already exists raises FileExistsError (per Q24)."""
    with pytest.raises(FileExistsError, match="Note already exists"):
        _create_note_in_folder_file(test_vault, "notes", "test", "Content", None)


def test_create_note_creates_folder_if_missing(test_vault):
    """Test creating note creates folder if it doesn't exist."""
    path = _create_note_in_folder_file(
        test_vault, "new_folder", "Note", "Content", None
    )

    assert (test_vault / "new_folder").exists()
    assert (test_vault / "new_folder" / "Note.md").exists()


# ============================================================================
# Test Helper Functions
# ============================================================================


def test_split_frontmatter_and_body_with_frontmatter():
    """Test splitting content with valid frontmatter."""
    content = "---\ntitle: Test\ntags: [a, b]\n---\n\n# Body\n\nContent"
    frontmatter, body = _split_frontmatter_and_body(content)

    assert frontmatter is not None
    assert frontmatter["title"] == "Test"
    assert frontmatter["tags"] == ["a", "b"]
    assert body.startswith("\n# Body")


def test_split_frontmatter_and_body_without_frontmatter():
    """Test splitting content without frontmatter."""
    content = "# Just Content\n\nNo frontmatter here"
    frontmatter, body = _split_frontmatter_and_body(content)

    assert frontmatter is None
    assert body == content


def test_split_frontmatter_and_body_invalid_yaml():
    """Test splitting with invalid YAML (per Q5 - lenient)."""
    content = "---\ninvalid: yaml: structure\n---\n\nContent"
    frontmatter, body = _split_frontmatter_and_body(content)

    assert frontmatter is None  # Invalid YAML returns None
    assert "Content" in body


def test_extract_title_from_frontmatter():
    """Test extracting title from frontmatter."""
    frontmatter = {"title": "My Title"}
    body = "# Different Header\n\nContent"
    title = _extract_title(frontmatter, body)

    assert title == "My Title"


def test_extract_title_from_header():
    """Test extracting title from # header when no frontmatter."""
    frontmatter = None
    body = "# Header Title\n\nContent"
    title = _extract_title(frontmatter, body)

    assert title == "Header Title"


def test_extract_title_no_title():
    """Test extracting title when none found returns 'Untitled'."""
    frontmatter = {}
    body = "Just content, no header"
    title = _extract_title(frontmatter, body)

    assert title == "Untitled"


def test_extract_header_list():
    """Test extracting list of headers."""
    body = "# Title\n\n## Section 1\n\nContent\n\n### Subsection\n\n## Section 2"
    headers = _extract_header_list(body)

    assert "Section 1" in headers
    assert "Subsection" in headers
    assert "Section 2" in headers
    assert "Title" not in headers  # Only ## and below


def test_extract_header_list_no_headers():
    """Test extracting headers when none exist."""
    body = "Just content, no headers"
    headers = _extract_header_list(body)

    assert headers == []
