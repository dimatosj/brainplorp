# Sprint 5: Note Linking

**Sprint ID:** SPRINT-5
**Status:** ✅ COMPLETED
**Dependencies:** Sprint 0, 1, 2, 4 complete (Sprint 3 helpful)
**Estimated Duration:** 1-2 days
**Actual Duration:** ~2 hours
**Completion Date:** 2025-10-06

---

## Table of Contents

1. [Overview](#overview)
2. [Engineering Handoff Prompt](#engineering-handoff-prompt)
3. [Technical Specifications](#technical-specifications)
4. [Test Requirements](#test-requirements)
5. [Success Criteria](#success-criteria)
6. [Completion Report Template](#completion-report-template)
7. [Q&A Section](#qa-section)

---

## Overview

### Goal

Implement bidirectional linking between Obsidian notes and TaskWarrior tasks. This allows users to create notes linked to tasks and vice versa, enabling seamless navigation between task management and note-taking.

### What You're Building

The note linking system with:
- Note creation workflow with optional task linking
- Bidirectional link management (note → task, task → note)
- Front matter manipulation for adding task UUIDs to notes
- TaskWarrior annotation for adding note paths to tasks
- CLI commands: `brainplorp note` and `brainplorp link`
- Comprehensive tests for linking operations

### What You're NOT Building

- Advanced note templates (future enhancement)
- Bulk linking operations (future enhancement)
- Note search or discovery (use Obsidian for that)
- Task dependencies or relationships (TaskWarrior handles that)

---

## Engineering Handoff Prompt

```
You are implementing Sprint 5 for plorp, a workflow automation tool for TaskWarrior and Obsidian.

PROJECT CONTEXT:
- brainplorp is a Python CLI tool that bridges TaskWarrior and Obsidian
- This is Sprint 5: You're building note-task linking functionality
- Sprint 0 is complete: Project structure and test infrastructure ready
- Sprint 1 is complete: TaskWarrior integration with annotations available
- Sprint 2 is complete: File utilities and config available
- Sprint 4 is complete: Note creation in Obsidian vault working
- Sprint 3 is complete (optional): Prompts available

YOUR TASK:
1. Read the full Sprint 5 specification: /Users/jsd/Documents/plorp/Docs/sprints/SPRINT_5_SPEC.md
2. Implement workflows/notes.py - Note creation and linking workflow
3. Add front matter editing to parsers/markdown.py
4. Update cli.py - Add 'note' and 'link' commands
5. Write comprehensive tests for all modules
6. Follow TDD: Write tests BEFORE implementation
7. Mock TaskWarrior and file operations in tests
8. Document your work in the Completion Report section

IMPORTANT REQUIREMENTS:
- TDD approach: Write test first, then implement, then verify
- Mock all TaskWarrior calls (add_annotation, get_task_info)
- Use file utilities from Sprint 2
- Use note creation from Sprint 4
- All functions must have type hints and docstrings
- All new files must start with ABOUTME comments
- Handle edge cases: task not found, note not found, already linked

WORKING DIRECTORY: /Users/jsd/Documents/plorp/

AVAILABLE FROM PREVIOUS SPRINTS:
- Sprint 1: add_annotation(), get_task_info(), get_task_annotations()
- Sprint 2: read_file(), write_file(), config
- Sprint 4: create_note(), get_vault_path()
- Sprint 3: prompt(), confirm() (if available)

CLARIFYING QUESTIONS:
If anything is unclear, add your questions to the Q&A section of this spec document and stop. The PM/Architect will answer them before you continue.

COMPLETION:
When done, fill out the Completion Report Template section in this document with details of your implementation.
```

---

## Technical Specifications

### Module 1: Front Matter Editing (Add to markdown.py)

**File:** `src/plorp/parsers/markdown.py`

**Add these functions:**

```python
def add_frontmatter_field(content: str, field: str, value: Any) -> str:
    """
    Add or update a field in YAML front matter.

    If front matter doesn't exist, creates it. If field exists, updates it.

    Args:
        content: Markdown content (with or without front matter)
        field: Field name to add/update
        value: Field value (will be serialized to YAML)

    Returns:
        Updated markdown content with modified front matter

    Example:
        >>> content = "# Note\\n\\nSome content"
        >>> updated = add_frontmatter_field(content, 'tags', ['work', 'important'])
        >>> print(updated)
        ---
        tags:
          - work
          - important
        ---
        # Note

        Some content
    """
    fm = parse_frontmatter(content)

    # Update field
    fm[field] = value

    # Extract body (everything after front matter)
    if content.startswith('---'):
        parts = content.split('---', 2)
        body = parts[2] if len(parts) > 2 else ''
    else:
        body = content

    # Rebuild with updated front matter
    new_fm = yaml.dump(fm, default_flow_style=False, sort_keys=False)
    return f"---\n{new_fm}---{body}"


def add_task_to_note_frontmatter(note_path: Path, task_uuid: str) -> None:
    """
    Add a task UUID to a note's front matter tasks list.

    Creates 'tasks' field if it doesn't exist. Avoids duplicates.

    Args:
        note_path: Path to note file
        task_uuid: Task UUID to add

    Raises:
        FileNotFoundError: If note doesn't exist

    Example:
        >>> add_task_to_note_frontmatter(Path('notes/meeting.md'), 'abc-123')
        # Note now has tasks: [abc-123] in front matter
    """
    from plorp.utils.files import read_file, write_file

    content = read_file(note_path)
    fm = parse_frontmatter(content)

    # Get existing tasks or create empty list
    tasks = fm.get('tasks', [])

    # Add UUID if not already present
    if task_uuid not in tasks:
        tasks.append(task_uuid)

    # Update front matter
    updated_content = add_frontmatter_field(content, 'tasks', tasks)

    write_file(note_path, updated_content)


def remove_task_from_note_frontmatter(note_path: Path, task_uuid: str) -> None:
    """
    Remove a task UUID from a note's front matter tasks list.

    Args:
        note_path: Path to note file
        task_uuid: Task UUID to remove

    Raises:
        FileNotFoundError: If note doesn't exist

    Example:
        >>> remove_task_from_note_frontmatter(Path('notes/meeting.md'), 'abc-123')
    """
    from plorp.utils.files import read_file, write_file

    content = read_file(note_path)
    fm = parse_frontmatter(content)

    tasks = fm.get('tasks', [])

    if task_uuid in tasks:
        tasks.remove(task_uuid)
        updated_content = add_frontmatter_field(content, 'tasks', tasks)
        write_file(note_path, updated_content)
```

**Tests for front matter editing:**

```python
# Add to tests/test_parsers/test_markdown.py:

def test_add_frontmatter_field_new_field(tmp_path):
    """Test adding new field to existing front matter."""
    content = """---
title: Test Note
---

# Content
"""

    updated = add_frontmatter_field(content, 'tags', ['work'])

    assert 'tags:' in updated
    assert '- work' in updated
    assert '# Content' in updated


def test_add_frontmatter_field_update_existing(tmp_path):
    """Test updating existing field in front matter."""
    content = """---
title: Old Title
type: note
---

Body
"""

    updated = add_frontmatter_field(content, 'title', 'New Title')

    assert 'title: New Title' in updated
    assert 'Old Title' not in updated
    assert 'type: note' in updated  # Other fields preserved


def test_add_frontmatter_field_create_frontmatter():
    """Test adding front matter to content without it."""
    content = "# Just a title\n\nSome content"

    updated = add_frontmatter_field(content, 'created', '2025-10-06')

    assert content.startswith('---')
    assert 'created: 2025-10-06' in updated or 'created: \'2025-10-06\'' in updated
    assert '# Just a title' in updated


def test_add_task_to_note_frontmatter_new(tmp_path):
    """Test adding task UUID to note without tasks field."""
    note = tmp_path / 'note.md'
    content = """---
title: Meeting Notes
---

# Meeting
"""
    note.write_text(content)

    add_task_to_note_frontmatter(note, 'abc-123')

    updated = note.read_text()
    assert 'tasks:' in updated
    assert '- abc-123' in updated


def test_add_task_to_note_frontmatter_existing(tmp_path):
    """Test adding task UUID to note with existing tasks."""
    note = tmp_path / 'note.md'
    content = """---
title: Notes
tasks:
  - def-456
---

Content
"""
    note.write_text(content)

    add_task_to_note_frontmatter(note, 'abc-123')

    updated = note.read_text()
    assert '- abc-123' in updated
    assert '- def-456' in updated


def test_add_task_to_note_frontmatter_duplicate(tmp_path):
    """Test that duplicate UUIDs are not added."""
    note = tmp_path / 'note.md'
    content = """---
tasks:
  - abc-123
---

Content
"""
    note.write_text(content)

    add_task_to_note_frontmatter(note, 'abc-123')

    updated = note.read_text()
    # Should only appear once
    assert updated.count('abc-123') == 1


def test_remove_task_from_note_frontmatter(tmp_path):
    """Test removing task UUID from note."""
    note = tmp_path / 'note.md'
    content = """---
tasks:
  - abc-123
  - def-456
---

Content
"""
    note.write_text(content)

    remove_task_from_note_frontmatter(note, 'abc-123')

    updated = note.read_text()
    assert 'abc-123' not in updated
    assert '- def-456' in updated
```

---

### Module 2: Note Workflow

**File:** `src/plorp/workflows/notes.py`

**Replace stub with:**

```python
# ABOUTME: Note management workflow - creates notes and manages task-note linking
# ABOUTME: Provides bidirectional linking between Obsidian notes and TaskWarrior tasks
"""
Note workflow: creation and linking.

Status: Implemented in Sprint 5
"""
from pathlib import Path
from typing import Dict, Any, Optional, List

from plorp.integrations.obsidian import create_note, get_vault_path
from plorp.integrations.taskwarrior import add_annotation, get_task_info, get_task_annotations
from plorp.parsers.markdown import (
    add_task_to_note_frontmatter,
    extract_task_uuids_from_note
)


def create_note_with_task_link(
    config: Dict[str, Any],
    title: str,
    task_uuid: Optional[str] = None,
    note_type: str = 'general',
    content: str = ''
) -> Path:
    """
    Create a new note and optionally link it to a task.

    Creates bidirectional link:
    - Adds task UUID to note's front matter
    - Adds note path as annotation to task

    Args:
        config: Configuration dictionary
        title: Note title
        task_uuid: Optional task UUID to link
        note_type: Note type (default: 'general')
        content: Note content (default: '')

    Returns:
        Path to created note

    Raises:
        ValueError: If task_uuid provided but task doesn't exist

    Example:
        >>> config = load_config()
        >>> note = create_note_with_task_link(
        ...     config,
        ...     "Sprint Planning Notes",
        ...     task_uuid="abc-123"
        ... )
        >>> print(f"Created: {note}")
    """
    vault = get_vault_path(config)

    # Verify task exists if UUID provided
    if task_uuid:
        task = get_task_info(task_uuid)
        if not task:
            raise ValueError(f"Task not found: {task_uuid}")

    # Create the note
    note_path = create_note(
        vault_path=vault,
        title=title,
        note_type=note_type,
        content=content
    )

    # Link to task if UUID provided
    if task_uuid:
        link_note_to_task(note_path, task_uuid, vault)

    return note_path


def link_note_to_task(note_path: Path, task_uuid: str, vault_path: Path) -> None:
    """
    Create bidirectional link between note and task.

    Updates:
    1. Note front matter: adds task UUID to 'tasks' list
    2. Task annotation: adds note path

    Args:
        note_path: Path to note file
        task_uuid: Task UUID to link
        vault_path: Path to vault root (for relative path calculation)

    Raises:
        FileNotFoundError: If note doesn't exist
        ValueError: If task doesn't exist

    Example:
        >>> link_note_to_task(
        ...     Path('vault/notes/meeting.md'),
        ...     'abc-123',
        ...     Path('vault')
        ... )
    """
    # Verify task exists
    task = get_task_info(task_uuid)
    if not task:
        raise ValueError(f"Task not found: {task_uuid}")

    # Verify note exists
    if not note_path.exists():
        raise FileNotFoundError(f"Note not found: {note_path}")

    # 1. Add task UUID to note front matter
    add_task_to_note_frontmatter(note_path, task_uuid)

    # 2. Add note path as task annotation
    relative_path = note_path.relative_to(vault_path)
    annotation_text = f"Note: {relative_path}"

    # Check if already annotated (avoid duplicates)
    existing_annotations = get_task_annotations(task_uuid)
    if annotation_text not in existing_annotations:
        add_annotation(task_uuid, annotation_text)


def unlink_note_from_task(note_path: Path, task_uuid: str) -> None:
    """
    Remove bidirectional link between note and task.

    Note: Currently only removes from note's front matter.
    TaskWarrior annotations cannot be easily removed via CLI.

    Args:
        note_path: Path to note file
        task_uuid: Task UUID to unlink

    Raises:
        FileNotFoundError: If note doesn't exist

    Example:
        >>> unlink_note_from_task(Path('notes/old-meeting.md'), 'abc-123')
    """
    from plorp.parsers.markdown import remove_task_from_note_frontmatter

    if not note_path.exists():
        raise FileNotFoundError(f"Note not found: {note_path}")

    remove_task_from_note_frontmatter(note_path, task_uuid)

    # Note: TaskWarrior annotations can't be easily removed via CLI
    # This is a limitation of TaskWarrior's annotation system
    # Users can manually edit .taskrc or use `task <uuid> edit`


def get_linked_notes(task_uuid: str, vault_path: Path) -> List[Path]:
    """
    Get all notes linked to a task.

    Parses task annotations to find note paths.

    Args:
        task_uuid: Task UUID
        vault_path: Path to vault root

    Returns:
        List of note paths linked to this task.
        Empty list if task not found or no linked notes.

    Example:
        >>> notes = get_linked_notes('abc-123', Path('~/vault'))
        >>> for note in notes:
        ...     print(f"Linked: {note}")
    """
    annotations = get_task_annotations(task_uuid)

    note_paths = []

    for annotation in annotations:
        # Annotations are formatted: "Note: relative/path/to/note.md"
        if annotation.startswith('Note: '):
            relative_path = annotation[6:]  # Remove "Note: " prefix
            full_path = vault_path / relative_path

            if full_path.exists():
                note_paths.append(full_path)

    return note_paths


def get_linked_tasks(note_path: Path) -> List[str]:
    """
    Get all task UUIDs linked to a note.

    Reads task UUIDs from note's front matter.

    Args:
        note_path: Path to note file

    Returns:
        List of task UUIDs linked to this note.
        Empty list if note not found or no linked tasks.

    Example:
        >>> tasks = get_linked_tasks(Path('notes/meeting.md'))
        >>> for uuid in tasks:
        ...     print(f"Task: {uuid}")
    """
    return extract_task_uuids_from_note(note_path)
```

**Tests for notes.py:**

```python
# ABOUTME: Tests for note workflow - validates note creation and task-note linking
# ABOUTME: Mocks TaskWarrior operations and uses temporary files for testing
"""Tests for note workflow."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from plorp.workflows.notes import (
    create_note_with_task_link,
    link_note_to_task,
    unlink_note_from_task,
    get_linked_notes,
    get_linked_tasks
)


@pytest.fixture
def test_vault(tmp_path):
    """Create test vault structure."""
    vault = tmp_path / 'vault'
    (vault / 'notes').mkdir(parents=True)
    return vault


@patch('plorp.workflows.notes.get_task_info')
@patch('plorp.workflows.notes.add_annotation')
def test_create_note_with_task_link(mock_annotation, mock_task_info, test_vault):
    """Test creating note with task link."""
    mock_task_info.return_value = {'uuid': 'abc-123', 'description': 'Test task'}

    config = {'vault_path': str(test_vault)}

    note_path = create_note_with_task_link(
        config,
        "Meeting Notes",
        task_uuid='abc-123'
    )

    assert note_path.exists()
    assert note_path.parent == test_vault / 'notes'

    # Verify front matter has task UUID
    content = note_path.read_text()
    assert 'tasks:' in content
    assert 'abc-123' in content

    # Verify annotation added
    mock_annotation.assert_called_once()


@patch('plorp.workflows.notes.get_task_info')
def test_create_note_with_invalid_task(mock_task_info, test_vault):
    """Test creating note with non-existent task."""
    mock_task_info.return_value = None  # Task not found

    config = {'vault_path': str(test_vault)}

    with pytest.raises(ValueError, match="Task not found"):
        create_note_with_task_link(config, "Note", task_uuid='invalid-uuid')


def test_create_note_without_task(test_vault):
    """Test creating note without task link."""
    config = {'vault_path': str(test_vault)}

    note_path = create_note_with_task_link(config, "Simple Note")

    assert note_path.exists()

    content = note_path.read_text()
    # Should not have tasks field
    assert 'tasks:' not in content or 'tasks: []' in content


@patch('plorp.workflows.notes.get_task_info')
@patch('plorp.workflows.notes.add_annotation')
@patch('plorp.workflows.notes.get_task_annotations')
def test_link_note_to_task(mock_annotations, mock_add_ann, mock_task_info, test_vault):
    """Test linking existing note to task."""
    mock_task_info.return_value = {'uuid': 'abc-123', 'description': 'Test'}
    mock_annotations.return_value = []  # No existing annotations

    # Create a note
    note_path = test_vault / 'notes' / 'test-note.md'
    note_path.write_text("""---
title: Test Note
---

Content
""")

    link_note_to_task(note_path, 'abc-123', test_vault)

    # Verify task UUID added to front matter
    content = note_path.read_text()
    assert 'tasks:' in content
    assert 'abc-123' in content

    # Verify annotation added
    mock_add_ann.assert_called_once()
    annotation = mock_add_ann.call_args[0][1]
    assert 'Note:' in annotation
    assert 'test-note.md' in annotation


@patch('plorp.workflows.notes.get_task_info')
def test_link_note_to_invalid_task(mock_task_info, test_vault):
    """Test linking note to non-existent task."""
    mock_task_info.return_value = None

    note_path = test_vault / 'notes' / 'test.md'
    note_path.write_text("# Test")

    with pytest.raises(ValueError, match="Task not found"):
        link_note_to_task(note_path, 'invalid-uuid', test_vault)


def test_link_note_not_found(test_vault):
    """Test linking non-existent note."""
    note_path = test_vault / 'notes' / 'nonexistent.md'

    with pytest.raises(FileNotFoundError):
        link_note_to_task(note_path, 'abc-123', test_vault)


@patch('plorp.workflows.notes.get_task_info')
@patch('plorp.workflows.notes.add_annotation')
@patch('plorp.workflows.notes.get_task_annotations')
def test_link_note_to_task_already_linked(mock_annotations, mock_add_ann, mock_task_info, test_vault):
    """Test linking note that's already linked (should not duplicate)."""
    mock_task_info.return_value = {'uuid': 'abc-123'}
    mock_annotations.return_value = ['Note: notes/test-note.md']  # Already linked

    note_path = test_vault / 'notes' / 'test-note.md'
    note_path.write_text("---\ntitle: Test\n---\n\nContent")

    link_note_to_task(note_path, 'abc-123', test_vault)

    # Annotation should not be added again
    mock_add_ann.assert_not_called()


def test_unlink_note_from_task(test_vault):
    """Test unlinking note from task."""
    note_path = test_vault / 'notes' / 'test.md'
    content = """---
title: Test
tasks:
  - abc-123
  - def-456
---

Content
"""
    note_path.write_text(content)

    unlink_note_from_task(note_path, 'abc-123')

    updated = note_path.read_text()
    assert 'abc-123' not in updated
    assert 'def-456' in updated  # Other task preserved


@patch('plorp.workflows.notes.get_task_annotations')
def test_get_linked_notes(mock_annotations, test_vault):
    """Test getting notes linked to task."""
    # Create some notes
    note1 = test_vault / 'notes' / 'meeting-1.md'
    note2 = test_vault / 'notes' / 'meeting-2.md'
    note1.write_text("# Note 1")
    note2.write_text("# Note 2")

    # Mock task annotations
    mock_annotations.return_value = [
        'Note: notes/meeting-1.md',
        'Note: notes/meeting-2.md',
        'Some other annotation'
    ]

    notes = get_linked_notes('abc-123', test_vault)

    assert len(notes) == 2
    assert note1 in notes
    assert note2 in notes


@patch('plorp.workflows.notes.get_task_annotations')
def test_get_linked_notes_nonexistent(mock_annotations, test_vault):
    """Test getting linked notes when note files don't exist."""
    mock_annotations.return_value = [
        'Note: notes/deleted-note.md'
    ]

    notes = get_linked_notes('abc-123', test_vault)

    # Should not include non-existent notes
    assert len(notes) == 0


def test_get_linked_tasks(test_vault):
    """Test getting tasks linked to note."""
    note_path = test_vault / 'notes' / 'test.md'
    content = """---
title: Test Note
tasks:
  - abc-123
  - def-456
  - ghi-789
---

Content
"""
    note_path.write_text(content)

    tasks = get_linked_tasks(note_path)

    assert len(tasks) == 3
    assert 'abc-123' in tasks
    assert 'def-456' in tasks
    assert 'ghi-789' in tasks


def test_get_linked_tasks_no_tasks(test_vault):
    """Test getting tasks from note with no linked tasks."""
    note_path = test_vault / 'notes' / 'test.md'
    note_path.write_text("---\ntitle: Test\n---\n\nContent")

    tasks = get_linked_tasks(note_path)

    assert tasks == []
```

---

### Module 3: CLI Commands

**File:** `src/plorp/cli.py`

**Add these commands:**

```python
@cli.command()
@click.argument('title', nargs=-1, required=True)
@click.option('--task', help='Link to task UUID')
@click.option('--type', 'note_type', default='general', help='Note type (default: general)')
@click.pass_context
def note(ctx, title, task, note_type):
    """Create a new note, optionally linked to a task."""
    config = load_config()

    title_str = ' '.join(title)

    try:
        from plorp.workflows.notes import create_note_with_task_link

        note_path = create_note_with_task_link(
            config,
            title_str,
            task_uuid=task,
            note_type=note_type
        )

        # Get relative path for display
        from plorp.integrations.obsidian import get_vault_path
        vault = get_vault_path(config)
        relative_path = note_path.relative_to(vault)

        click.echo(f"\n✅ Note created: {relative_path}")

        if task:
            click.echo(f"🔗 Linked to task: {task}")

        click.echo(f"📄 Full path: {note_path}\n")

    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(f"❌ Error creating note: {e}", err=True)
        import traceback
        traceback.print_exc()
        ctx.exit(1)


@cli.command()
@click.argument('task_uuid')
@click.argument('note_path', type=click.Path(exists=True))
@click.pass_context
def link(ctx, task_uuid, note_path):
    """Link an existing note to a task."""
    config = load_config()

    try:
        from plorp.workflows.notes import link_note_to_task
        from plorp.integrations.obsidian import get_vault_path
        from pathlib import Path

        vault = get_vault_path(config)
        note_path_obj = Path(note_path).resolve()

        link_note_to_task(note_path_obj, task_uuid, vault)

        relative_path = note_path_obj.relative_to(vault) if note_path_obj.is_relative_to(vault) else note_path_obj

        click.echo(f"\n✅ Linked successfully")
        click.echo(f"📝 Note: {relative_path}")
        click.echo(f"📋 Task: {task_uuid}\n")

    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
        ctx.exit(1)
    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(f"❌ Error linking note: {e}", err=True)
        import traceback
        traceback.print_exc()
        ctx.exit(1)
```

**Tests for CLI commands:**

```python
# Add to tests/test_cli.py:

@patch('plorp.cli.load_config')
@patch('plorp.workflows.notes.create_note_with_task_link')
@patch('plorp.integrations.obsidian.get_vault_path')
def test_note_command(mock_vault_path, mock_create, mock_load_config, tmp_path):
    """Test note command creates note."""
    from click.testing import CliRunner
    from plorp.cli import cli

    vault = tmp_path / 'vault'
    vault.mkdir()
    mock_vault_path.return_value = vault

    note_path = vault / 'notes' / 'test-note.md'
    mock_create.return_value = note_path

    mock_load_config.return_value = {'vault_path': str(vault)}

    runner = CliRunner()
    result = runner.invoke(cli, ['note', 'Test', 'Note', 'Title'])

    assert result.exit_code == 0
    assert '✅ Note created' in result.output
    mock_create.assert_called_once()


@patch('plorp.cli.load_config')
@patch('plorp.workflows.notes.create_note_with_task_link')
@patch('plorp.integrations.obsidian.get_vault_path')
def test_note_command_with_task(mock_vault_path, mock_create, mock_load_config, tmp_path):
    """Test note command with task link."""
    from click.testing import CliRunner
    from plorp.cli import cli

    vault = tmp_path / 'vault'
    vault.mkdir()
    mock_vault_path.return_value = vault

    note_path = vault / 'notes' / 'test.md'
    mock_create.return_value = note_path

    mock_load_config.return_value = {'vault_path': str(vault)}

    runner = CliRunner()
    result = runner.invoke(cli, ['note', 'Meeting', '--task', 'abc-123'])

    assert result.exit_code == 0
    assert '🔗 Linked to task' in result.output
    assert 'abc-123' in result.output

    # Verify task UUID passed to create function
    call_kwargs = mock_create.call_args[1]
    assert call_kwargs['task_uuid'] == 'abc-123'


@patch('plorp.cli.load_config')
@patch('plorp.workflows.notes.link_note_to_task')
@patch('plorp.integrations.obsidian.get_vault_path')
def test_link_command(mock_vault_path, mock_link, mock_load_config, tmp_path):
    """Test link command links note to task."""
    from click.testing import CliRunner
    from plorp.cli import cli

    vault = tmp_path / 'vault'
    notes_dir = vault / 'notes'
    notes_dir.mkdir(parents=True)

    note = notes_dir / 'existing.md'
    note.write_text("# Existing note")

    mock_vault_path.return_value = vault
    mock_load_config.return_value = {'vault_path': str(vault)}

    runner = CliRunner()
    result = runner.invoke(cli, ['link', 'abc-123', str(note)])

    assert result.exit_code == 0
    assert '✅ Linked successfully' in result.output
    assert 'abc-123' in result.output
    mock_link.assert_called_once()


@patch('plorp.cli.load_config')
@patch('plorp.workflows.notes.link_note_to_task')
def test_link_command_note_not_found(mock_link, mock_load_config):
    """Test link command with non-existent note."""
    from click.testing import CliRunner
    from plorp.cli import cli

    mock_load_config.return_value = {'vault_path': '/tmp/vault'}

    runner = CliRunner()
    result = runner.invoke(cli, ['link', 'abc-123', '/nonexistent/note.md'])

    # Should fail because file doesn't exist
    assert result.exit_code != 0
```

---

## Test Requirements

### Test Coverage Goals

- **workflows/notes.py:** >90% coverage
- **parsers/markdown.py (new functions):** 100% coverage
- **Overall Sprint 5 code:** >90% coverage

### Test Execution

```bash
# Run all Sprint 5 tests
pytest tests/test_workflows/test_notes.py \
       tests/test_parsers/test_markdown.py::test_add_frontmatter* \
       tests/test_parsers/test_markdown.py::test_add_task* \
       tests/test_parsers/test_markdown.py::test_remove_task* \
       tests/test_cli.py::test_note* \
       tests/test_cli.py::test_link* \
       -v

# Run with coverage
pytest tests/test_workflows/test_notes.py \
    --cov=src/plorp/workflows/notes \
    --cov=src/plorp/parsers/markdown \
    --cov-report=term-missing
```

---

## Success Criteria

### Import and Test Check

```bash
cd /Users/jsd/Documents/plorp
source venv/bin/activate

# 1. Imports work
python3 -c "
from plorp.workflows.notes import create_note_with_task_link, link_note_to_task
from plorp.parsers.markdown import add_frontmatter_field, add_task_to_note_frontmatter
print('✓ All imports successful')
"

# 2. Tests pass
pytest tests/test_workflows/test_notes.py -v

# 3. Coverage check
pytest tests/test_workflows/test_notes.py \
    --cov=src/plorp/workflows/notes --cov-report=term
```

### CLI and Workflow Check

```bash
# 4. Create note without task link
brainplorp note "Simple Note"
# → Creates note
# → Shows path

# 5. Create note with task link
# First create a task
task add "Test linking" project:plorp
# Get the UUID from output

brainplorp note "Meeting Notes" --task <UUID>
# → Creates note
# → Links to task
# → Shows confirmation

# 6. Verify link in TaskWarrior
task <UUID> info
# → Should show annotation: "Note: notes/meeting-notes-*.md"

# 7. Verify link in note
cat ~/vault/notes/meeting-notes-*.md
# → Front matter should contain:
#   tasks:
#     - <UUID>

# 8. Link existing note
echo "# Existing note" > ~/vault/notes/existing.md
brainplorp link <UUID> ~/vault/notes/existing.md
# → Links successfully
# → Shows confirmation

# 9. Verify bidirectional link
task <UUID> info
# → Shows both note annotations
cat ~/vault/notes/existing.md
# → Has task UUID in front matter
```

### Code Quality Check

```bash
# 10. Black formatting
black --check src/plorp/workflows/notes.py

# 11. ABOUTME comments
head -2 src/plorp/workflows/notes.py
```

---

## Completion Report Template

**Instructions:** Fill this out when Sprint 5 is complete.

### Implementation Summary

**What was implemented:**
- [x] workflows/notes.py - Note creation and linking
- [x] parsers/markdown.py - Front matter editing functions added
- [x] cli.py - Added 'note' and 'link' commands
- [x] All files have ABOUTME comments
- [x] All functions have type hints and docstrings
- [x] Comprehensive test suite
- [x] All tests pass
- [x] >90% test coverage achieved
- [x] CLI commands work end-to-end
- [x] Bidirectional linking verified

**Lines of code added:**
- Production code: +426 lines
- Test code: +472 lines
- Total: +898 lines

**Test coverage achieved:**
- parsers/markdown.py: 98%
- workflows/notes.py: 97%
- cli.py: 100% (Sprint 5 commands)

**Number of tests written:** 23 new tests (7 front matter + 12 workflow + 4 CLI)

**Test results:**
```
44 tests total - ALL PASSING ✅
Platform: darwin (Python 3.13.7)
Time: 0.08s
```

### Implementation Details

**Module 1: Front Matter Editing (`parsers/markdown.py`)**
- Added 3 functions for YAML manipulation (+118 lines)
- Functions: `add_frontmatter_field()`, `add_task_to_note_frontmatter()`, `remove_task_from_note_frontmatter()`
- 7 comprehensive tests
- Block-style YAML, preserved field order, no blank lines after ---
- Task validation before adding to front matter
- Duplicate prevention

**Module 2: Notes Workflow (`workflows/notes.py`)**
- New file: 237 lines
- 5 functions: `create_note_with_task_link()`, `link_note_to_task()`, `unlink_note_from_task()`, `get_linked_notes()`, `get_linked_tasks()`
- 12 comprehensive tests covering all edge cases
- Annotation format: `plorp:note:` prefix with forward slashes
- Path normalization and validation (must be inside vault)
- Duplicate link prevention

**Module 3: CLI Commands (`cli.py`)**
- Added `brainplorp note <title> [--task <uuid>] [--type <type>]` (+71 lines)
- Added `brainplorp link <task_uuid> <note_path>`
- 4 CLI tests with error handling verification
- User-friendly output with emojis

**All 13 Q&A answers implemented:**
- Q1: Block style YAML ✅
- Q2: No blank line after --- ✅
- Q3: Task validation ✅
- Q4: Annotation format ✅
- Q5: Path normalization ✅
- Q6: Error handling ✅
- Q7: Note types ✅
- Q8: Vault validation ✅
- Q9: Unlink warning ✅
- Q10: Mock strategy ✅
- Q11: Title sanitization ✅
- Q12: Field naming ✅
- Q13: Sprint 4 deps ✅

### Deviations from Spec

No deviations. All functionality implemented as specified.

### Verification Commands

```bash
cd /Users/jsd/Documents/plorp
source venv/bin/activate

# Run all Sprint 5 tests
pytest tests/test_parsers/test_markdown.py tests/test_workflows/test_notes.py tests/test_cli.py::test_note_command tests/test_cli.py::test_note_command_with_task tests/test_cli.py::test_link_command tests/test_cli.py::test_link_command_note_not_found -v

# Check coverage
pytest tests/test_parsers/test_markdown.py tests/test_workflows/test_notes.py tests/test_cli.py::test_note_command tests/test_cli.py::test_note_command_with_task tests/test_cli.py::test_link_command tests/test_cli.py::test_link_command_note_not_found --cov=plorp.parsers.markdown --cov=plorp.workflows.notes --cov=plorp.cli --cov-report=term-missing

# Verify code formatting
black --check src/plorp/parsers/markdown.py src/plorp/workflows/notes.py src/plorp/cli.py tests/test_parsers/test_markdown.py tests/test_workflows/test_notes.py tests/test_cli.py
```

**Output summary:**
All 44 tests pass in 0.08s. Coverage: 97-98% for Sprint 5 modules. Code formatted with black (3 files reformatted, 3 unchanged).

### Known Issues

**Any known limitations or issues:**

1. **TaskWarrior annotation removal limitation:** The `unlink_note_from_task()` function removes the task UUID from the note's front matter, but cannot automatically remove the note annotation from TaskWarrior. This is a limitation of TaskWarrior's CLI - annotations can't be easily removed programmatically. Users must manually edit tasks if they want to remove note annotations. Implementation includes warning message to user (Q9).

No other issues identified. All functionality working as specified.

### Handoff Notes

**What works:**
- Complete note-task linking system
- Bidirectional links maintained (note front matter ↔ task annotations)
- CLI commands functional (`brainplorp note`, `brainplorp link`)
- All previous sprint functionality preserved
- Duplicate link prevention
- Path validation (notes must be inside vault)
- Error handling for missing tasks/notes
- All 13 Q&A requirements implemented

**Integration points:**
- Uses Sprint 1 TaskWarrior integration: `add_annotation()`, `get_task_info()`, `get_task_annotations()`
- Uses Sprint 2 file utilities: `read_file()`, `write_file()`
- Uses Sprint 4 note creation: `create_note()`, `get_vault_path()`
- Extends markdown parsing from previous sprints

**Future enhancements:**
- Bulk linking operations (link multiple notes/tasks at once)
- Link verification/repair tool (`brainplorp verify-links`)
- Note templates with task-specific sections
- Link visualization graph
- Annotation removal via TaskWarrior API (if available)
- Orphan detection (tasks without notes, notes without tasks)

### Questions for PM/Architect

None. All questions answered in Q&A section.

### Recommendations

**Suggestions for future work:**

1. **Link health checker:** Create `brainplorp verify-links` command to check:
   - Tasks referenced in notes still exist
   - Notes referenced in task annotations still exist
   - Bidirectional links are consistent

2. **Bulk operations:** Support batch operations:
   ```bash
   brainplorp link-batch <task_uuid> notes/*.md
   brainplorp note-batch --task <uuid> "Note 1" "Note 2" "Note 3"
   ```

3. **Link visualization:** Generate Obsidian-compatible graph:
   ```bash
   brainplorp graph --output vault/graphs/task-links.md
   ```

4. **Note templates:** Task-specific note templates:
   ```bash
   brainplorp note "Sprint Planning" --task <uuid> --template sprint-planning
   ```

5. **Advanced annotation handling:** Investigate TaskChampion API for programmatic annotation removal

6. **Link statistics:** Show linking metrics:
   ```bash
   brainplorp stats links
   # Output: 45 notes linked to 23 tasks
   ```

### Sign-off

- **Implemented by:** Claude Code (Sprint 5 Implementation)
- **Date completed:** 2025-10-06
- **Implementation time:** ~2 hours (including Q&A, TDD, testing, documentation)
- **Ready for production:** Yes

**Acceptance Criteria Status:**
- ✅ AC1: Create note linked to task
- ✅ AC2: Link existing note to task
- ✅ AC3: Bidirectional linking maintained
- ✅ AC4: Duplicate links prevented
- ✅ AC5: Query linked notes for task
- ✅ AC6: Query linked tasks for note
- ✅ AC7: Error handling for missing tasks/notes

**All Sprint 5 requirements met and verified.**

---

## Q&A Section

### Questions from Engineering

**Q1: YAML serialization for front matter updates**
```
Q: The add_frontmatter_field() function uses yaml.dump() to serialize the updated
   front matter. Questions:

   1. Should we use default_flow_style=False (block style) or allow flow style?
      Block style:
        tags:
          - work
          - important

      Flow style:
        tags: [work, important]

   2. Should we use sort_keys=False to preserve field order, or allow alphabetical
      sorting?

   3. In Sprint 3, we used yaml.BaseLoader to avoid date conversion. Should we
      continue using BaseLoader for parse_frontmatter(), or switch back to
      safe_load() since we're now using yaml.dump() which will serialize properly?

   4. What about string quoting - should dates like "2025-10-06" be quoted or not?

Status: RESOLVED (see Answers section below)
```

**Q2: Front matter creation for notes without front matter**
```
Q: When add_frontmatter_field() is called on content without existing front matter:

   Current spec:
   - Creates new front matter with just the one field
   - Preserves original content after front matter

   Questions:
   1. Should we add any default fields when creating front matter from scratch?
      Examples: created date, type: note, etc.

   2. Should there be a blank line between the closing "---" and the content?
      Option A: "---\nfield: value\n---\n# Content"
      Option B: "---\nfield: value\n---\n\n# Content"

   3. The body extraction code: `body = parts[2] if len(parts) > 2 else ''`
      Should we preserve leading newlines from the original content?

Status: RESOLVED (see Answers section below)
```

**Q3: Task UUID validation in front matter**
```
Q: When adding task UUIDs to note front matter via add_task_to_note_frontmatter():

   Should we:
   1. Validate that the UUID is in TaskWarrior before adding to note?
      Pro: Prevents broken links
      Con: Requires TaskWarrior call, slower

   2. Or just add any UUID string and trust the caller?
      Pro: Faster, allows offline operation
      Con: Could create broken links

   Note: create_note_with_task_link() validates the task exists, but
   add_task_to_note_frontmatter() is a standalone function that could be
   called directly.

Status: RESOLVED (see Answers section below)
```

**Q4: Annotation format and conflicts**
```
Q: The annotation format is: "Note: relative/path/to/note.md"

   Questions:
   1. What if a note path contains a colon ":" character?
      Example: "Note: notes/Meeting: Client A.md"
      Could this break parsing in get_linked_notes()?

   2. Should we validate note paths to disallow certain characters?

   3. The get_linked_notes() function uses annotation.startswith('Note: ')
      What if user manually adds an annotation like "Note to self: call Bob"?
      Should we use a more specific prefix like "LinkedNote:" or "plorp:note:"?

   4. What about Windows paths with backslashes? Should we normalize to forward
      slashes for cross-platform compatibility?

Status: RESOLVED (see Answers section below)
```

**Q5: Duplicate link detection**
```
Q: The spec says "Check if already annotated (avoid duplicates)" in link_note_to_task().

   Current implementation:
   ```python
   existing_annotations = get_task_annotations(task_uuid)
   if annotation_text not in existing_annotations:
       add_annotation(task_uuid, annotation_text)
   ```

   Questions:
   1. Is string equality sufficient, or could there be path variations?
      Examples:
      - "Note: notes/meeting.md" vs "Note: ./notes/meeting.md"
      - "Note: notes/meeting.md" vs "Note: notes//meeting.md"
      - Absolute vs relative paths

   2. Should we normalize paths before comparison?

   3. What about case sensitivity on macOS (case-insensitive) vs Linux?

Status: RESOLVED (see Answers section below)
```

**Q6: Error handling for file operations**
```
Q: Several functions do file operations that could fail:

   1. add_task_to_note_frontmatter() calls read_file() which could raise:
      - FileNotFoundError (documented)
      - PermissionError (not documented)
      - UnicodeDecodeError (not documented)

      Should we catch and re-raise with better error messages, or let them propagate?

   2. write_file() could fail with disk full, permissions, etc.
      Should these functions guarantee atomicity (write to temp file, then rename)?
      Or trust the Sprint 2 file utilities to handle this?

   3. The spec shows FileNotFoundError in docstrings but not IOError or PermissionError.
      Should we document all possible exceptions?

Status: RESOLVED (see Answers section below)
```

**Q7: Note type and directory structure**
```
Q: The create_note_with_task_link() function accepts note_type parameter:

   Current spec:
   ```python
   note_path = create_note(
       vault_path=vault,
       title=title,
       note_type=note_type,
       content=content
   )
   ```

   Questions:
   1. What note_types are valid? The spec shows 'general' as default but doesn't
      list valid types. Is this from Sprint 4's create_note()?

   2. Does note_type affect the directory structure?
      - general → vault/notes/
      - meeting → vault/meetings/
      - project → vault/projects/

      If so, should we document this in Sprint 5 spec?

   3. Should the CLI --type option validate against allowed types, or accept any string?

Status: RESOLVED (see Answers section below)
```

**Q8: Relative path calculation edge cases**
```
Q: In link_note_to_task(), we calculate relative path:
   ```python
   relative_path = note_path.relative_to(vault_path)
   ```

   Questions:
   1. What if the note is OUTSIDE the vault (symlink, or user error)?
      relative_to() will raise ValueError. Should we:
      a) Let it raise and fail
      b) Catch and use absolute path instead
      c) Refuse to link notes outside vault

   2. In the CLI link command, we have:
      ```python
      relative_path = note_path_obj.relative_to(vault) if note_path_obj.is_relative_to(vault) else note_path_obj
      ```
      This handles it. Should link_note_to_task() do the same?

   3. What about symlinks within the vault? Should we resolve them first?

Status: RESOLVED (see Answers section below)
```

**Q9: Unlinking behavior and TaskWarrior annotation removal**
```
Q: The unlink_note_from_task() function only removes from note front matter,
   not from TaskWarrior annotations (documented as limitation).

   Questions:
   1. Should we print a warning when unlink is called, telling user they need
      to manually remove the annotation?

   2. Or is silent removal from note sufficient, documented in the limitation?

   3. Should we provide a helper message in the docstring or CLI output showing
      how to manually remove (task <uuid> edit)?

   4. Could we use `task <uuid> modify` to remove annotations programmatically?
      Need to research TaskWarrior CLI for this.

Status: RESOLVED (see Answers section below)
```

**Q10: Testing note creation integration**
```
Q: The tests mock create_note() from Sprint 4's obsidian.py module.

   Questions:
   1. Should we verify that Sprint 4 is actually complete before implementing
      Sprint 5? The spec says "Dependencies: Sprint 0, 1, 2, 4 complete"

   2. If Sprint 4 is not complete, should we:
      a) Wait for Sprint 4
      b) Create a minimal create_note() stub for testing
      c) Fully mock it in tests (current approach)

   3. Should we have integration tests that use the real create_note()
      function, or are unit tests with mocks sufficient?

Status: RESOLVED (see Answers section below)
```

**Q11: CLI argument parsing for multi-word titles**
```
Q: The note command uses:
   ```python
   @click.argument('title', nargs=-1, required=True)
   ```
   Then joins with: `title_str = ' '.join(title)`

   Questions:
   1. This works for: `brainplorp note Meeting Notes` → "Meeting Notes"
      But what about quotes: `brainplorp note "Meeting Notes"` → also "Meeting Notes"?
      Should we document both forms work?

   2. What about edge cases:
      - `brainplorp note "" ` (empty string after join)
      - `brainplorp note "  "` (whitespace only)

      Should we validate title is not empty/whitespace?

   3. Should we sanitize titles for filesystem safety?
      Examples: remove/replace: / \ : * ? " < > |

Status: RESOLVED (see Answers section below)
```

**Q12: Front matter field naming conventions**
```
Q: The spec uses 'tasks' field for storing task UUIDs:
   ```yaml
   tasks:
     - abc-123
     - def-456
   ```

   Questions:
   1. Should this be 'tasks' (plural) or 'task_uuids' (more descriptive)?

   2. Is 'tasks' field reserved only for plorp, or could it conflict with
      other Obsidian plugins or user conventions?

   3. Should we namespace it as 'plorp_tasks' or 'plorp:tasks'?

   4. What about other metadata we might add in future (created, modified, etc)?
      Should we establish a naming convention now?

Status: RESOLVED (see Answers section below)
```

**Q13: Test fixture dependencies and Sprint 4**
```
Q: Sprint 5 depends on Sprint 4 for create_note() and get_vault_path().

   Current approach in tests:
   - Mock these functions with @patch decorators
   - Don't actually call real implementations

   Questions:
   1. Should we verify Sprint 4 completion before starting Sprint 5?
      How to check: Try importing from plorp.integrations.obsidian?

   2. If Sprint 4 is incomplete, should Sprint 5 implementation fail fast
      with clear error message?

   3. Or is it acceptable to proceed with Sprint 5 assuming Sprint 4 will
      be complete before integration testing?

Status: RESOLVED (see Answers section below)
```

---

### Answers from PM/Architect

**Q5: Duplicate link detection**
```
Q: Path variations that mean the same thing - should we normalize?
A: Engineering decision - YES, normalize paths before comparison.

   Implementation:
   ```python
   from pathlib import Path

   # Normalize both paths before comparing
   relative_path = note_path.relative_to(vault_path)
   normalized_new = str(Path(relative_path).as_posix())  # Forward slashes

   existing_annotations = get_task_annotations(task_uuid)
   for annotation in existing_annotations:
       if annotation.startswith('Note: '):
           existing_path = annotation[6:]
           normalized_existing = str(Path(existing_path).as_posix())
           if normalized_new == normalized_existing:
               # Already linked, skip
               return

   add_annotation(task_uuid, f"Note: {normalized_new}")
   ```

   This handles:
   - `./notes/meeting.md` vs `notes/meeting.md`
   - Double slashes: `notes//meeting.md`
   - Backslashes on Windows: converts to forward slashes

   Note: Case sensitivity handled by filesystem - macOS (case-insensitive) vs
   Linux (case-sensitive). We preserve case as-is, let OS handle.

Status: RESOLVED
```

**Q6: Error handling for file operations**
```
Q: Should we document all exceptions or add enhanced error handling?
A: Engineering decision - Document common exceptions, let others propagate.

   Implementation:
   1. Document FileNotFoundError in docstrings (most common)
   2. Let PermissionError, UnicodeDecodeError, IOError propagate naturally
   3. Python's error messages are clear enough for these cases
   4. Trust Sprint 2 file utilities - they're already tested

   Rationale: Over-catching exceptions hides bugs. Let Python handle edge cases
   with its built-in error messages. Users can file issues if messages unclear.

Status: RESOLVED
```

**Q8: Relative path calculation edge cases**
```
Q: What if note is outside vault?
A: Engineering decision - Refuse to link with clear error message.

   Implementation:
   ```python
   # In link_note_to_task()
   if not note_path.is_relative_to(vault_path):
       raise ValueError(
           f"Note must be inside vault. "
           f"Note: {note_path}, Vault: {vault_path}"
       )

   relative_path = note_path.relative_to(vault_path)
   ```

   Symlinks: Resolve before checking
   ```python
   note_path = note_path.resolve()  # Follow symlinks
   if not note_path.is_relative_to(vault_path):
       raise ValueError(...)
   ```

   Rationale:
   - Clear policy: only vault notes can be linked
   - Prevents confusion with absolute paths in annotations
   - Symlinks resolved automatically - they work if target is in vault

Status: RESOLVED
```

**Q10: Testing note creation integration**
```
Q: How to test Sprint 4 dependencies?
A: Engineering decision - Mock for unit tests, verify imports at runtime.

   Approach:
   1. Unit tests: Mock create_note() and get_vault_path() as shown in spec
   2. Runtime verification: Let Python ImportError happen naturally if Sprint 4 incomplete
   3. No integration tests in Sprint 5 - assume Sprint 4 works

   At module import time, Python will fail with clear error if Sprint 4 missing:
   ```
   ImportError: cannot import name 'create_note' from 'plorp.integrations.obsidian'
   ```

   This is clearer than custom checking. If Sprint 4 incomplete, engineer will
   know immediately when running tests or CLI.

Status: RESOLVED
```

**Q1: YAML serialization for front matter updates**
```
Q: Block vs flow style, sort keys, loader choice, string quoting?
A: Use block style, preserve order, keep BaseLoader (consistency with Sprint 3).

   Implementation:
   ```python
   # In add_frontmatter_field()
   new_fm = yaml.dump(fm, default_flow_style=False, sort_keys=False)
   ```

   For parsing, continue using yaml.BaseLoader from Sprint 3:
   ```python
   # In parse_frontmatter() - already implemented in Sprint 3
   yaml.load(parts[1], Loader=yaml.BaseLoader)
   ```

   Rationale:
   1. Block style is more readable in Obsidian
   2. Preserving order respects user's field organization
   3. BaseLoader consistency with Sprint 3 - avoids date conversion issues
   4. String quoting handled automatically by yaml.dump()

   This maintains consistency with Sprint 3's YAML handling approach.

Status: RESOLVED
```

**Q2: Front matter creation for notes without front matter**
```
Q: Add default fields? Blank line after front matter? Preserve leading newlines?
A: No default fields (keep minimal), no blank line after front matter (cleaner).

   Implementation:
   ```python
   # In add_frontmatter_field()
   new_fm = yaml.dump(fm, default_flow_style=False, sort_keys=False)
   return f"---\n{new_fm}---{body}"  # No blank line
   ```

   For body extraction, strip leading newlines for consistency:
   ```python
   if content.startswith('---'):
       parts = content.split('---', 2)
       body = parts[2].lstrip('\n') if len(parts) > 2 else ''
   else:
       body = content.lstrip('\n')
   ```

   Rationale:
   1. No default fields - keep front matter minimal, only add what's needed
   2. No blank line - cleaner, consistent with Sprint 4's note creation
   3. Strip leading newlines - consistent formatting

Status: RESOLVED
```

**Q3: Task UUID validation in front matter**
```
Q: Validate task exists in TaskWarrior before adding to note?
A: YES, validate - safer, clearer errors outweigh speed cost.

   Implementation:
   ```python
   def add_task_to_note_frontmatter(note_path: Path, task_uuid: str) -> None:
       """Add task UUID to note front matter with validation."""
       from plorp.integrations.taskwarrior import get_task_info
       from plorp.utils.files import read_file, write_file

       # Validate task exists
       task = get_task_info(task_uuid)
       if not task:
           raise ValueError(f"Task not found in TaskWarrior: {task_uuid}")

       content = read_file(note_path)
       fm = parse_frontmatter(content)

       # Get existing tasks or create empty list
       tasks = fm.get('tasks', [])

       # Add UUID if not already present
       if task_uuid not in tasks:
           tasks.append(task_uuid)

       # Update front matter
       updated_content = add_frontmatter_field(content, 'tasks', tasks)
       write_file(note_path, updated_content)
   ```

   Rationale:
   1. Prevents broken links - data integrity is more important than speed
   2. Clear error messages immediately, not later when user discovers broken link
   3. TaskWarrior call is fast enough for typical use
   4. Consistent with link_note_to_task() which also validates

   Note: create_note_with_task_link() already validates, so this adds validation
   for direct calls to add_task_to_note_frontmatter().

Status: RESOLVED
```

**Q4: Annotation format and conflicts**
```
Q: What prefix to use? "Note:" vs "plorp:note:"? Windows path handling?
A: Use "plorp:note:" prefix and normalize to forward slashes.

   Implementation:
   ```python
   # In link_note_to_task()
   relative_path = note_path.relative_to(vault_path)
   # Normalize to forward slashes for cross-platform compatibility
   normalized_path = str(relative_path.as_posix())
   annotation_text = f"plorp:note:{normalized_path}"

   # Check if already annotated
   existing_annotations = get_task_annotations(task_uuid)
   if annotation_text not in existing_annotations:
       add_annotation(task_uuid, annotation_text)
   ```

   ```python
   # In get_linked_notes()
   for annotation in annotations:
       if annotation.startswith('plorp:note:'):
           relative_path = annotation[11:]  # Remove "plorp:note:" prefix
           full_path = vault_path / relative_path
           if full_path.exists():
               note_paths.append(full_path)
   ```

   Rationale:
   1. "plorp:note:" is unique - prevents conflicts with user annotations like "Note to self:"
   2. Forward slashes work on all platforms (Windows converts automatically)
   3. Clear namespace ownership - annotations are plorp-managed

Status: RESOLVED
```

**Q7: Note type and directory structure**
```
Q: What note_types are valid? Document from Sprint 4?
A: Engineering decision - Document valid types from Sprint 4.

   From Sprint 4 Q&A resolution:
   - `meeting` → vault/meetings/
   - All others → vault/notes/

   Implementation:
   1. Add to Sprint 5 docstrings:
      ```python
      note_type: Note type (default: 'general')
          Valid types:
          - 'meeting': Stored in vault/meetings/
          - 'general', 'project', or any other: Stored in vault/notes/
      ```

   2. CLI accepts any string - no validation
      Sprint 4's create_note() handles the directory routing

   Rationale: Sprint 4 defines this behavior, Sprint 5 just documents it.

Status: RESOLVED
```

**Q9: Unlinking behavior and TaskWarrior annotation removal**
```
Q: Should we print warning about manual annotation removal?
A: YES, print warning - better UX, sets expectations.

   Implementation:
   ```python
   def unlink_note_from_task(note_path: Path, task_uuid: str) -> None:
       """
       Remove bidirectional link between note and task.

       Note: Only removes from note's front matter. TaskWarrior annotations
       cannot be removed programmatically via CLI. User must manually remove
       using: task <uuid> edit

       Args:
           note_path: Path to note file
           task_uuid: Task UUID to unlink

       Raises:
           FileNotFoundError: If note doesn't exist
       """
       from plorp.parsers.markdown import remove_task_from_note_frontmatter
       import sys

       if not note_path.exists():
           raise FileNotFoundError(f"Note not found: {note_path}")

       remove_task_from_note_frontmatter(note_path, task_uuid)

       # Print warning about manual annotation removal
       print(f"\n✅ Removed task link from note", file=sys.stderr)
       print(f"⚠️  Note: TaskWarrior annotation cannot be removed automatically", file=sys.stderr)
       print(f"💡 To remove annotation from task, run: task {task_uuid} edit", file=sys.stderr)
   ```

   Rationale:
   1. Sets user expectations immediately
   2. Provides clear instructions for manual cleanup
   3. Prevents confusion about asymmetric unlinking
   4. Documented limitation becomes actionable guidance

Status: RESOLVED
```

**Q11: CLI argument parsing for multi-word titles**
```
Q: Title validation and sanitization?
A: Sanitize by replacing unsafe characters with hyphens.

   Implementation:
   ```python
   @cli.command()
   @click.argument('title', nargs=-1, required=True)
   @click.option('--task', help='Link to task UUID')
   @click.option('--type', 'note_type', default='general', help='Note type (default: general)')
   @click.pass_context
   def note(ctx, title, task, note_type):
       """Create a new note, optionally linked to a task."""
       config = load_config()

       # Join title parts
       title_str = ' '.join(title)

       # Validate not empty
       if not title_str.strip():
           click.echo("❌ Error: Title cannot be empty", err=True)
           ctx.exit(1)

       # Sanitize filesystem-unsafe characters
       unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
       sanitized_title = title_str
       for char in unsafe_chars:
           sanitized_title = sanitized_title.replace(char, '-')

       # Show warning if title was sanitized
       if sanitized_title != title_str:
           click.echo(f"ℹ️  Note: Title sanitized for filesystem safety")
           click.echo(f"   Original: {title_str}")
           click.echo(f"   Sanitized: {sanitized_title}")

       try:
           from plorp.workflows.notes import create_note_with_task_link

           note_path = create_note_with_task_link(
               config,
               sanitized_title,
               task_uuid=task,
               note_type=note_type
           )

           # ... rest of command
   ```

   Rationale:
   1. Just works - no user friction with filesystem errors
   2. Cross-platform safety (Windows restrictions handled)
   3. User informed if title changed
   4. Empty title validation prevents confusion

Status: RESOLVED
```

**Q12: Front matter field naming conventions**
```
Q: Use 'tasks' or 'plorp_tasks' or 'task_uuids'?
A: Keep 'tasks' - simple, clear, low conflict risk.

   Implementation:
   ```python
   # In front matter:
   ---
   title: Note Title
   tasks:
     - abc-123
     - def-456
   ---
   ```

   ```python
   # In code:
   tasks = fm.get('tasks', [])
   ```

   Rationale:
   1. 'tasks' is intuitive and concise
   2. Low conflict risk - most Obsidian users won't have this field
   3. If conflicts arise, users can work around it
   4. Simpler than 'plorp_tasks' (less namespace pollution)
   5. More user-friendly than 'task_uuids' (less technical)

   If future conflicts arise, we can add namespacing in v2.0, but start simple.

Status: RESOLVED
```

**Q13: Test fixture dependencies and Sprint 4**
```
Q: Verify Sprint 4 completion before starting?
A: Engineering decision - Assume Sprint 4 complete, fail naturally if not.

   Approach:
   1. No explicit verification check
   2. If Sprint 4 incomplete, Python import errors will be clear:
      ```
      ImportError: cannot import name 'create_note' from 'plorp.integrations.obsidian'
      ```
   3. Engineer discovers immediately when running first test

   This is simpler than custom checking and provides clear error message.
   Sprint dependencies are documented in spec header: "Dependencies: Sprint 0, 1, 2, 4 complete"

Status: RESOLVED
```

---

**Document Version:** 1.0
**Last Updated:** October 6, 2025
**Status:** Ready for Implementation
**Next Sprint:** None (Sprint 5 completes core functionality)

---

## Epilogue: brainplorp 1.0 Complete

With Sprint 5 complete, brainplorp 1.0 is fully functional. The three core workflows are operational:

1. **Daily workflow** (Sprints 2-3)
   - `brainplorp start` - Generate daily notes
   - `brainplorp review` - End-of-day task processing

2. **Inbox workflow** (Sprint 4)
   - `brainplorp inbox process` - Convert inbox items to tasks/notes

3. **Note linking** (Sprint 5)
   - `brainplorp note` - Create linked notes
   - `brainplorp link` - Link existing notes to tasks

**Future enhancements** beyond Sprint 5:
- Email capture automation (scripts/email_to_inbox.py)
- TaskWarrior hooks integration
- Advanced reporting and analytics
- Mobile sync capabilities
- Custom workflows and plugins

**Congratulations** to all engineering instances who implemented these sprints! 🎉
