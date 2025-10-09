# ABOUTME: Tests for markdown parsing - validates task extraction and front matter parsing
# ABOUTME: Uses fixture files and constructed markdown to test various formats
"""Tests for markdown parsing."""
import pytest
from pathlib import Path
from unittest.mock import patch
from plorp.parsers.markdown import (
    parse_daily_note_tasks,
    parse_frontmatter,
    extract_task_uuids_from_note,
    parse_inbox_items,
    mark_item_processed,
    add_frontmatter_field,
    add_task_to_note_frontmatter,
    remove_task_from_note_frontmatter,
    _split_frontmatter_and_body,
    _format_with_frontmatter,
    _format_date,
    _remove_section,
)


def test_parse_daily_note_tasks_with_unchecked(tmp_path):
    """Test parsing daily note with unchecked tasks."""
    note = tmp_path / "daily.md"
    content = """---
date: 2025-10-06
---

# Daily Note

## Tasks

- [ ] Buy groceries (project: home, uuid: abc-123)
- [x] Call dentist (project: health, uuid: def-456)
- [ ] Write report (due: 2025-10-07, uuid: ghi-789)
"""
    note.write_text(content)

    tasks = parse_daily_note_tasks(note)

    assert len(tasks) == 2
    assert ("Buy groceries", "abc-123") in tasks
    assert ("Write report", "ghi-789") in tasks
    # Should NOT include checked task
    assert ("Call dentist", "def-456") not in tasks


def test_parse_daily_note_tasks_all_checked(tmp_path):
    """Test parsing note with all tasks checked."""
    note = tmp_path / "daily.md"
    content = """
- [x] Task 1 (uuid: abc-123)
- [x] Task 2 (uuid: def-456)
"""
    note.write_text(content)

    tasks = parse_daily_note_tasks(note)

    assert tasks == []


def test_parse_daily_note_tasks_no_uuid(tmp_path):
    """Test parsing note with checkboxes but no UUIDs."""
    note = tmp_path / "daily.md"
    content = """
- [ ] Task without UUID
- [ ] Another task
"""
    note.write_text(content)

    tasks = parse_daily_note_tasks(note)

    assert tasks == []


def test_parse_daily_note_tasks_file_not_found(tmp_path):
    """Test parsing non-existent file returns empty list."""
    note = tmp_path / "nonexistent.md"

    tasks = parse_daily_note_tasks(note)

    assert tasks == []


def test_parse_daily_note_tasks_sample_fixture(fixture_dir):
    """Test parsing the sample daily note fixture."""
    note = fixture_dir / "sample_daily_note.md"

    tasks = parse_daily_note_tasks(note)

    # Sample has 3 unchecked tasks
    assert len(tasks) == 3

    descriptions = [desc for desc, _ in tasks]
    assert "Call dentist" in descriptions
    assert "Buy groceries" in descriptions
    assert "Morning meditation" in descriptions


def test_parse_daily_note_tasks_flexible_whitespace(tmp_path):
    """Test parsing with variable whitespace (Q2 answer)."""
    note = tmp_path / "daily.md"
    content = """
-[ ]Task no spaces (uuid: abc-123)
- [  ] Task extra spaces (uuid: def-456)
-  [ ]  Weird spacing (uuid: ghi-789)
"""
    note.write_text(content)

    tasks = parse_daily_note_tasks(note)

    assert len(tasks) == 3
    assert ("Task no spaces", "abc-123") in tasks
    assert ("Task extra spaces", "def-456") in tasks
    assert ("Weird spacing", "ghi-789") in tasks


def test_parse_daily_note_tasks_uppercase_uuid(tmp_path):
    """Test parsing with uppercase UUIDs (Q2 answer)."""
    note = tmp_path / "daily.md"
    content = """
- [ ] Task 1 (uuid: ABC-123)
- [ ] Task 2 (uuid: DeF-456)
- [ ] Task 3 (uuid: a1B2c3D4-5678)
"""
    note.write_text(content)

    tasks = parse_daily_note_tasks(note)

    assert len(tasks) == 3
    assert ("Task 1", "ABC-123") in tasks
    assert ("Task 2", "DeF-456") in tasks
    assert ("Task 3", "a1B2c3D4-5678") in tasks


def test_parse_frontmatter_valid():
    """Test parsing valid YAML front matter."""
    content = """---
date: 2025-10-06
type: daily
tags: [work, important]
---

# Content here
"""

    fm = parse_frontmatter(content)

    assert fm["date"] == "2025-10-06"
    assert fm["type"] == "daily"
    assert fm["tags"] == ["work", "important"]


def test_parse_frontmatter_no_frontmatter():
    """Test parsing content without front matter."""
    content = "# Just a title\n\nSome content"

    fm = parse_frontmatter(content)

    assert fm == {}


def test_parse_frontmatter_invalid_yaml():
    """Test parsing malformed YAML front matter."""
    content = """---
this is not: valid: yaml: structure
---

Content
"""

    fm = parse_frontmatter(content)

    assert fm == {}


def test_parse_frontmatter_incomplete():
    """Test parsing incomplete front matter (no closing ---)."""
    content = """---
date: 2025-10-06

Content without closing front matter
"""

    fm = parse_frontmatter(content)

    assert fm == {}


def test_extract_task_uuids_from_note(tmp_path):
    """Test extracting task UUIDs from note front matter."""
    note = tmp_path / "note.md"
    content = """---
title: Meeting Notes
tasks:
  - abc-123
  - def-456
  - ghi-789
---

# Meeting Notes
"""
    note.write_text(content)

    uuids = extract_task_uuids_from_note(note)

    assert len(uuids) == 3
    assert "abc-123" in uuids
    assert "def-456" in uuids
    assert "ghi-789" in uuids


def test_extract_task_uuids_no_tasks_field(tmp_path):
    """Test extracting UUIDs when no tasks field in front matter."""
    note = tmp_path / "note.md"
    content = """---
title: Regular Note
---

Content
"""
    note.write_text(content)

    uuids = extract_task_uuids_from_note(note)

    assert uuids == []


def test_extract_task_uuids_file_not_found(tmp_path):
    """Test extracting UUIDs from non-existent file."""
    note = tmp_path / "nonexistent.md"

    uuids = extract_task_uuids_from_note(note)

    assert uuids == []


# Inbox parsing tests (Sprint 4)


def test_parse_inbox_items(tmp_path):
    """Test parsing unprocessed items from inbox."""
    inbox = tmp_path / "inbox.md"
    content = """# Inbox - October 2025

## Unprocessed

- [ ] Email from boss: Q4 planning meeting tomorrow 3pm
- [ ] Idea: Research TaskWarrior hooks for automation
- [ ] Reminder: Buy groceries before weekend

## Processed

- [x] Call dentist - Created task (uuid: abc-123)
"""
    inbox.write_text(content)

    items = parse_inbox_items(inbox)

    assert len(items) == 3
    assert "Email from boss: Q4 planning meeting tomorrow 3pm" in items
    assert "Idea: Research TaskWarrior hooks for automation" in items
    assert "Reminder: Buy groceries before weekend" in items


def test_parse_inbox_items_empty(tmp_path):
    """Test parsing inbox with no unprocessed items."""
    inbox = tmp_path / "inbox.md"
    content = """# Inbox

## Unprocessed

## Processed

- [x] Something old
"""
    inbox.write_text(content)

    items = parse_inbox_items(inbox)

    assert items == []


def test_parse_inbox_items_no_section(tmp_path):
    """Test parsing inbox without Unprocessed section."""
    inbox = tmp_path / "inbox.md"
    content = "# Just a note\n\nNo inbox structure"
    inbox.write_text(content)

    items = parse_inbox_items(inbox)

    assert items == []


def test_parse_inbox_items_file_not_found(tmp_path):
    """Test parsing non-existent inbox file."""
    inbox = tmp_path / "inbox.md"

    items = parse_inbox_items(inbox)

    assert items == []


def test_mark_item_processed(tmp_path):
    """Test marking item as processed."""
    inbox = tmp_path / "inbox.md"
    content = """# Inbox

## Unprocessed

- [ ] Buy groceries
- [ ] Call dentist

## Processed

- [x] Old item
"""
    inbox.write_text(content)

    mark_item_processed(inbox, "Buy groceries", "Created task (uuid: abc-123)")

    updated = inbox.read_text()

    # Should be checked and have action
    assert "- [x] Buy groceries - Created task (uuid: abc-123)" in updated

    # Should be in Processed section
    processed_section = updated.split("## Processed")[1]
    assert "Buy groceries" in processed_section

    # Should not be in Unprocessed
    unprocessed_section = updated.split("## Unprocessed")[1].split("## Processed")[0]
    assert "Buy groceries" not in unprocessed_section


def test_mark_item_processed_creates_section(tmp_path):
    """Test marking item when Processed section doesn't exist."""
    inbox = tmp_path / "inbox.md"
    content = """# Inbox

## Unprocessed

- [ ] Buy groceries
"""
    inbox.write_text(content)

    mark_item_processed(inbox, "Buy groceries", "Discarded")

    updated = inbox.read_text()

    # Should create Processed section
    assert "## Processed" in updated
    assert "- [x] Buy groceries - Discarded" in updated


def test_mark_item_processed_duplicate_items(tmp_path):
    """Test marking when same item appears twice (only first marked)."""
    inbox = tmp_path / "inbox.md"
    content = """# Inbox

## Unprocessed

- [ ] Buy groceries
- [ ] Buy groceries

## Processed
"""
    inbox.write_text(content)

    mark_item_processed(inbox, "Buy groceries", "Created task")

    updated = inbox.read_text()

    # Should mark only first occurrence
    unprocessed_section = updated.split("## Unprocessed")[1].split("## Processed")[0]
    # One should remain unchecked
    assert "- [ ] Buy groceries" in unprocessed_section


# Front matter editing tests (Sprint 5)


def test_add_frontmatter_field_new_field(tmp_path):
    """Test adding new field to existing front matter."""
    content = """---
title: Test Note
---

# Content
"""

    updated = add_frontmatter_field(content, "tags", ["work"])

    assert "tags:" in updated
    assert "- work" in updated
    assert "# Content" in updated


def test_add_frontmatter_field_update_existing(tmp_path):
    """Test updating existing field in front matter."""
    content = """---
title: Old Title
type: note
---

Body
"""

    updated = add_frontmatter_field(content, "title", "New Title")

    assert "title: New Title" in updated
    assert "Old Title" not in updated
    assert "type: note" in updated  # Other fields preserved


def test_add_frontmatter_field_create_frontmatter():
    """Test adding front matter to content without it."""
    content = "# Just a title\n\nSome content"

    updated = add_frontmatter_field(content, "created", "2025-10-06")

    assert updated.startswith("---")
    assert "created: " in updated
    assert "# Just a title" in updated


@patch("plorp.integrations.taskwarrior.get_task_info")
def test_add_task_to_note_frontmatter_new(mock_task_info, tmp_path):
    """Test adding task UUID to note without tasks field."""
    mock_task_info.return_value = {"uuid": "abc-123", "description": "Test task"}

    note = tmp_path / "note.md"
    content = """---
title: Meeting Notes
---

# Meeting
"""
    note.write_text(content)

    add_task_to_note_frontmatter(note, "abc-123")

    updated = note.read_text()
    assert "tasks:" in updated
    assert "- abc-123" in updated


@patch("plorp.integrations.taskwarrior.get_task_info")
def test_add_task_to_note_frontmatter_existing(mock_task_info, tmp_path):
    """Test adding task UUID to note with existing tasks."""
    mock_task_info.return_value = {"uuid": "abc-123", "description": "Test task"}

    note = tmp_path / "note.md"
    content = """---
title: Notes
tasks:
  - def-456
---

Content
"""
    note.write_text(content)

    add_task_to_note_frontmatter(note, "abc-123")

    updated = note.read_text()
    assert "- abc-123" in updated
    assert "- def-456" in updated


@patch("plorp.integrations.taskwarrior.get_task_info")
def test_add_task_to_note_frontmatter_duplicate(mock_task_info, tmp_path):
    """Test that duplicate UUIDs are not added."""
    mock_task_info.return_value = {"uuid": "abc-123", "description": "Test task"}

    note = tmp_path / "note.md"
    content = """---
tasks:
  - abc-123
---

Content
"""
    note.write_text(content)

    add_task_to_note_frontmatter(note, "abc-123")

    updated = note.read_text()
    # Should only appear once
    assert updated.count("abc-123") == 1


def test_remove_task_from_note_frontmatter(tmp_path):
    """Test removing task UUID from note."""
    note = tmp_path / "note.md"
    content = """---
tasks:
  - abc-123
  - def-456
---

Content
"""
    note.write_text(content)

    remove_task_from_note_frontmatter(note, "abc-123")

    updated = note.read_text()
    assert "abc-123" not in updated
    assert "- def-456" in updated


# Sprint 8.6 Helper Function Tests


def test_split_frontmatter_and_body_with_frontmatter():
    """Test splitting content with frontmatter."""
    content = """---
date: 2025-10-08
type: daily
---
# Title

Body content"""

    fm, body = _split_frontmatter_and_body(content)

    assert fm["date"] == "2025-10-08"
    assert fm["type"] == "daily"
    assert body == "# Title\n\nBody content"


def test_split_frontmatter_and_body_without_frontmatter():
    """Test splitting content without frontmatter."""
    content = "# Title\n\nBody content"

    fm, body = _split_frontmatter_and_body(content)

    assert fm == {}
    assert body == "# Title\n\nBody content"


def test_split_frontmatter_and_body_empty_body():
    """Test splitting content with frontmatter but no body."""
    content = """---
date: 2025-10-08
---"""

    fm, body = _split_frontmatter_and_body(content)

    assert fm["date"] == "2025-10-08"
    assert body == ""


def test_format_with_frontmatter_simple():
    """Test formatting with simple frontmatter."""
    frontmatter = {"date": "2025-10-08", "type": "daily"}
    body = "# Title\n\nContent"

    result = _format_with_frontmatter(frontmatter, body)

    assert result.startswith("---\n")
    # YAML may add quotes, both formats are valid
    assert "date:" in result and "2025-10-08" in result
    assert "type: daily" in result
    assert "---\n" in result
    assert "# Title" in result
    assert "Content" in result


def test_format_with_frontmatter_list():
    """Test formatting with list in frontmatter."""
    frontmatter = {"tasks": ["abc-123", "def-456"]}
    body = "Content"

    result = _format_with_frontmatter(frontmatter, body)

    assert "tasks:" in result
    assert "- abc-123" in result
    assert "- def-456" in result


def test_format_with_frontmatter_strips_leading_newlines():
    """Test that leading newlines in body are stripped."""
    frontmatter = {"date": "2025-10-08"}
    body = "\n\n\nContent"

    result = _format_with_frontmatter(frontmatter, body)

    # Should not have extra newlines between --- and Content
    assert result.count("\n\n\n") == 0


def test_format_date_taskwarrior_format():
    """Test formatting TaskWarrior date."""
    result = _format_date("20251010T000000Z")

    assert result == "2025-10-10"


def test_format_date_already_formatted():
    """Test formatting already-formatted date."""
    result = _format_date("2025-10-10")

    assert result == "2025-10-10"


def test_format_date_empty():
    """Test formatting empty date."""
    result = _format_date("")

    assert result == ""


def test_format_date_none():
    """Test formatting None date."""
    result = _format_date(None)

    assert result == ""


def test_remove_section_removes_target():
    """Test removing target section."""
    content = """# Title

## Tasks

- Item 1
- Item 2

## Notes

Some notes"""

    result = _remove_section(content, "## Tasks")

    assert "## Tasks" not in result
    assert "- Item 1" not in result
    assert "- Item 2" not in result
    assert "## Notes" in result
    assert "Some notes" in result


def test_remove_section_preserves_other_sections():
    """Test that other sections are preserved."""
    content = """# Title

## Section 1

Content 1

## Section 2

Content 2

## Section 3

Content 3"""

    result = _remove_section(content, "## Section 2")

    assert "## Section 1" in result
    assert "Content 1" in result
    assert "## Section 2" not in result
    assert "Content 2" not in result
    assert "## Section 3" in result
    assert "Content 3" in result


def test_remove_section_handles_nested_headings():
    """Test removing section with nested headings."""
    content = """# Title

## Tasks

### Subtask 1

Details

### Subtask 2

More details

## Notes

Content"""

    result = _remove_section(content, "## Tasks")

    assert "## Tasks" not in result
    assert "### Subtask 1" not in result
    assert "### Subtask 2" not in result
    assert "## Notes" in result


def test_remove_section_nonexistent():
    """Test removing section that doesn't exist."""
    content = """# Title

## Section 1

Content"""

    result = _remove_section(content, "## Nonexistent")

    # Should return content unchanged
    assert result == content


def test_remove_section_at_end():
    """Test removing section at end of document."""
    content = """# Title

## Section 1

Content 1

## Section 2

Content 2"""

    result = _remove_section(content, "## Section 2")

    assert "## Section 1" in result
    assert "Content 1" in result
    assert "## Section 2" not in result
    assert "Content 2" not in result
