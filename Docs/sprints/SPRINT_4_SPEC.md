# Sprint 4: Inbox Processing

**Sprint ID:** SPRINT-4
**Status:** Ready for Implementation
**Dependencies:** Sprint 0, 1, 2, 3 complete (Sprint 3 REQUIRED for prompts module)
**Estimated Duration:** 2-3 days

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

Implement the `brainplorp inbox process` command that provides an interactive workflow for processing captured inbox items (typically from email) and converting them into TaskWarrior tasks or Obsidian notes.

### What You're Building

The inbox processing system with:
- Obsidian integration for note file creation
- Inbox markdown parser for extracting unprocessed items
- Inbox workflow with interactive processing
- Task creation from inbox items
- Note creation from inbox items
- Marking items as processed in the inbox file
- CLI command wiring for `brainplorp inbox process`

### What You're NOT Building

- Email capture automation (that's scripts/email_to_inbox.py - future work)
- Note linking (that's Sprint 5)
- Advanced note templates (future enhancement)
- Inbox file generation (users create manually or via email script)

---

## Engineering Handoff Prompt

```
You are implementing Sprint 4 for plorp, a workflow automation tool for TaskWarrior and Obsidian.

PROJECT CONTEXT:
- brainplorp is a Python CLI tool that bridges TaskWarrior and Obsidian
- This is Sprint 4: You're building the inbox processing workflow
- Sprint 0 is complete: Project structure and test infrastructure ready
- Sprint 1 is complete: TaskWarrior integration available
- Sprint 2 is complete: Daily note generation, file utilities, config available
- Sprint 3 is complete (optional): Markdown parsing and prompts available

YOUR TASK:
1. Read the full Sprint 4 specification: /Users/jsd/Documents/plorp/Docs/sprints/SPRINT_4_SPEC.md
2. Implement integrations/obsidian.py - Note file creation in vault
3. Implement workflows/inbox.py - Inbox processing workflow
4. Add inbox parsing to parsers/markdown.py
5. Update cli.py - Wire up 'inbox' command
6. Write comprehensive tests for all modules
7. Follow TDD: Write tests BEFORE implementation
8. Mock all external operations (TaskWarrior, file I/O) in tests
9. Document your work in the Completion Report section

IMPORTANT REQUIREMENTS:
- TDD approach: Write test first, then implement, then verify
- Mock TaskWarrior calls using Sprint 1 functions
- Mock file I/O where appropriate
- Use prompts from Sprint 3 (or implement simple versions if needed)
- All functions must have type hints and docstrings
- All new files must start with ABOUTME comments
- Handle edge cases: empty inbox, all items processed, invalid input

WORKING DIRECTORY: /Users/jsd/Documents/plorp/

AVAILABLE FROM PREVIOUS SPRINTS:
- Sprint 1: create_task(), all TaskWarrior functions
- Sprint 2: read_file(), write_file(), ensure_directory(), config
- Sprint 3: prompt(), prompt_choice(), confirm() (if Sprint 3 complete)

CLARIFYING QUESTIONS:
If anything is unclear, add your questions to the Q&A section of this spec document and stop. The PM/Architect will answer them before you continue.

COMPLETION:
When done, fill out the Completion Report Template section in this document with details of your implementation.
```

---

## Technical Specifications

### Module 1: Obsidian Integration

**File:** `src/plorp/integrations/obsidian.py`

**Replace stub with:**

```python
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
    note_type: str = 'general',
    content: str = '',
    metadata: Optional[Dict[str, Any]] = None
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
    note_dir = vault_path / 'notes'

    # Create directory if needed
    ensure_directory(note_dir)

    # Generate filename from title and timestamp
    slug = generate_slug(title)
    timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
    filename = f"{slug}-{timestamp}.md"

    note_path = note_dir / filename

    # Build front matter
    front_matter = {
        'title': title,
        'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'type': note_type,
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
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)

    # Remove leading/trailing hyphens
    slug = slug.strip('-')

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
    if 'vault_path' not in config:
        raise ValueError("vault_path not configured")

    return Path(config['vault_path']).expanduser()
```

**Tests for obsidian.py:**

```python
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
    vault = tmp_path / 'vault'
    vault.mkdir()

    note_path = create_note(vault, "Test Note")

    assert note_path.exists()
    assert note_path.parent == vault / 'notes'
    assert 'test-note' in note_path.name
    assert note_path.suffix == '.md'


def test_create_note_content(tmp_path):
    """Test note contains correct content."""
    vault = tmp_path / 'vault'
    vault.mkdir()

    note_path = create_note(
        vault,
        "Meeting Notes",
        note_type="meeting",
        content="Discussed project timeline."
    )

    content = note_path.read_text()

    assert '---' in content  # Has front matter
    assert 'title: Meeting Notes' in content
    assert 'type: meeting' in content
    assert '# Meeting Notes' in content
    assert 'Discussed project timeline.' in content


def test_create_note_with_metadata(tmp_path):
    """Test creating note with custom metadata."""
    vault = tmp_path / 'vault'
    vault.mkdir()

    metadata = {
        'project': 'plorp',
        'tags': ['development', 'planning']
    }

    note_path = create_note(vault, "Sprint Planning", metadata=metadata)

    content = note_path.read_text()

    assert 'project: plorp' in content
    assert 'tags:' in content
    assert '- development' in content
    assert '- planning' in content


def test_create_note_creates_directory(tmp_path):
    """Test that create_note creates notes directory if not exists."""
    vault = tmp_path / 'vault'
    vault.mkdir()

    notes_dir = vault / 'notes'
    assert not notes_dir.exists()

    create_note(vault, "Test")

    assert notes_dir.exists()


def test_get_vault_path_valid():
    """Test getting vault path from config."""
    config = {'vault_path': '~/vault'}

    vault = get_vault_path(config)

    assert isinstance(vault, Path)
    assert str(vault) != '~/vault'  # Should be expanded


def test_get_vault_path_missing():
    """Test get_vault_path with missing vault_path."""
    config = {}

    with pytest.raises(ValueError, match="vault_path"):
        get_vault_path(config)
```

---

### Module 2: Inbox Parsing (Add to markdown.py)

**File:** `src/plorp/parsers/markdown.py`

**Add these functions:**

```python
def parse_inbox_items(inbox_path: Path) -> List[str]:
    """
    Parse unprocessed items from inbox file.

    Extracts unchecked checkboxes from "## Unprocessed" section.

    Args:
        inbox_path: Path to inbox markdown file

    Returns:
        List of unprocessed item strings (without checkbox markers).
        Empty list if no unprocessed items or file not found.

    Example:
        >>> items = parse_inbox_items(Path('vault/inbox/2025-10.md'))
        >>> for item in items:
        ...     print(f"Process: {item}")
    """
    try:
        content = inbox_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        return []

    # Find "## Unprocessed" section
    unprocessed_match = re.search(
        r'## Unprocessed\s*\n(.*?)(?=##|\Z)',
        content,
        re.DOTALL
    )

    if not unprocessed_match:
        return []

    unprocessed_section = unprocessed_match.group(1)

    # Extract unchecked items: - [ ] Item text
    pattern = r'- \[ \] (.+?)(?:\n|$)'
    matches = re.findall(pattern, unprocessed_section)

    return [item.strip() for item in matches]


def mark_item_processed(
    inbox_path: Path,
    item_text: str,
    action: str
) -> None:
    """
    Mark an inbox item as processed.

    Changes the item from unchecked to checked and moves it to
    the "## Processed" section with an action note.

    Args:
        inbox_path: Path to inbox file
        item_text: Text of item to mark processed
        action: Description of action taken (e.g., "Created task abc-123")

    Raises:
        FileNotFoundError: If inbox file doesn't exist

    Example:
        >>> mark_item_processed(
        ...     Path('inbox/2025-10.md'),
        ...     'Buy groceries',
        ...     'Created task (uuid: abc-123)'
        ... )
    """
    from plorp.utils.files import read_file, write_file

    content = read_file(inbox_path)

    # Find and replace the unchecked item
    old_line = f"- [ ] {item_text}"
    new_line = f"- [x] {item_text} - {action}"

    # Replace in content
    content = content.replace(old_line, new_line)

    # Move from Unprocessed to Processed section
    # Find the new_line in Unprocessed section
    unprocessed_pattern = r'(## Unprocessed\s*\n)(.*?)(##|\Z)'

    def move_to_processed(match):
        header = match.group(1)
        section_content = match.group(2)
        next_section = match.group(3)

        # Remove the processed item from unprocessed
        section_content = section_content.replace(new_line + '\n', '')

        return header + section_content + next_section

    content = re.sub(unprocessed_pattern, move_to_processed, content, flags=re.DOTALL)

    # Add to Processed section
    processed_pattern = r'(## Processed\s*\n)'

    def add_to_processed(match):
        return match.group(1) + f"{new_line}\n"

    if '## Processed' in content:
        content = re.sub(processed_pattern, add_to_processed, content)
    else:
        # Add Processed section if not exists
        content += f"\n## Processed\n\n{new_line}\n"

    write_file(inbox_path, content)
```

**Tests for inbox parsing:**

```python
# Add to tests/test_parsers/test_markdown.py:

def test_parse_inbox_items(tmp_path):
    """Test parsing unprocessed items from inbox."""
    inbox = tmp_path / 'inbox.md'
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
    assert 'Email from boss: Q4 planning meeting tomorrow 3pm' in items
    assert 'Idea: Research TaskWarrior hooks for automation' in items
    assert 'Reminder: Buy groceries before weekend' in items


def test_parse_inbox_items_empty(tmp_path):
    """Test parsing inbox with no unprocessed items."""
    inbox = tmp_path / 'inbox.md'
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
    inbox = tmp_path / 'inbox.md'
    content = "# Just a note\n\nNo inbox structure"
    inbox.write_text(content)

    items = parse_inbox_items(inbox)

    assert items == []


def test_mark_item_processed(tmp_path):
    """Test marking item as processed."""
    inbox = tmp_path / 'inbox.md'
    content = """# Inbox

## Unprocessed

- [ ] Buy groceries
- [ ] Call dentist

## Processed

- [x] Old item
"""
    inbox.write_text(content)

    mark_item_processed(inbox, 'Buy groceries', 'Created task (uuid: abc-123)')

    updated = inbox.read_text()

    # Should be checked and have action
    assert '- [x] Buy groceries - Created task (uuid: abc-123)' in updated

    # Should be in Processed section
    processed_section = updated.split('## Processed')[1]
    assert 'Buy groceries' in processed_section

    # Should not be in Unprocessed
    unprocessed_section = updated.split('## Unprocessed')[1].split('## Processed')[0]
    assert 'Buy groceries' not in unprocessed_section


def test_mark_item_processed_sample_fixture(fixture_dir, tmp_path):
    """Test marking item in sample inbox fixture."""
    # Copy fixture to tmp
    import shutil
    sample = fixture_dir / 'sample_inbox.md'
    inbox = tmp_path / 'inbox.md'
    shutil.copy(sample, inbox)

    # Get original unprocessed items
    original_items = parse_inbox_items(inbox)
    first_item = original_items[0]

    # Mark first item processed
    mark_item_processed(inbox, first_item, 'Created task')

    # Verify item marked
    updated_items = parse_inbox_items(inbox)
    assert len(updated_items) == len(original_items) - 1
    assert first_item not in updated_items
```

---

### Module 3: Inbox Workflow

**File:** `src/plorp/workflows/inbox.py`

**Replace stub with:**

```python
# ABOUTME: Inbox processing workflow - interactive conversion of inbox items to tasks/notes
# ABOUTME: Prompts user for each unprocessed item and creates tasks or notes accordingly
"""
Inbox processing workflow.

Status: Implemented in Sprint 4
"""
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from plorp.parsers.markdown import parse_inbox_items, mark_item_processed
from plorp.integrations.taskwarrior import create_task
from plorp.integrations.obsidian import create_note, get_vault_path


def process(config: Dict[str, Any]) -> None:
    """
    Interactive inbox processing.

    Reads current month's inbox file, presents each unprocessed item,
    and prompts user to convert to task, note, or discard.

    Args:
        config: Configuration dictionary

    Example:
        >>> config = load_config()
        >>> process(config)
        # Interactive prompts follow...
    """
    # Import prompts (handle if Sprint 3 not complete)
    try:
        from plorp.utils.prompts import prompt_choice, prompt, confirm
    except ImportError:
        print("❌ Error: Prompt utilities not available")
        print("💡 Complete Sprint 3 or implement simple prompts")
        return

    inbox_path = get_current_inbox_path(config)

    if not inbox_path.exists():
        print(f"❌ No inbox file found: {inbox_path}")
        print(f"💡 Create inbox file with '## Unprocessed' section")
        return

    items = parse_inbox_items(inbox_path)

    if not items:
        print(f"\n✅ Inbox is empty! All items processed.")
        return

    print(f"\n📥 {len(items)} items in inbox\n")

    processed_count = 0

    for item in items:
        print(f"\n{'=' * 60}")
        print(f"📌 Item: {item}")
        print(f"{'=' * 60}")

        choice = prompt_choice(
            options=[
                "📋 Create task",
                "📝 Create note",
                "🗑️  Discard (delete)",
                "⏭️  Skip (process later)",
                "🚪 Quit processing"
            ],
            prompt_text="What would you like to do with this item?"
        )

        if choice == 0:  # Create task
            task_uuid = process_item_as_task(item, config)
            if task_uuid:
                mark_item_processed(inbox_path, item, f"Created task (uuid: {task_uuid})")
                processed_count += 1
                print(f"✅ Task created: {task_uuid}\n")
            else:
                print("❌ Failed to create task\n")

        elif choice == 1:  # Create note
            note_path = process_item_as_note(item, config)
            if note_path:
                relative_path = note_path.relative_to(get_vault_path(config))
                mark_item_processed(inbox_path, item, f"Created note: {relative_path}")
                processed_count += 1
                print(f"✅ Note created: {relative_path}\n")
            else:
                print("❌ Failed to create note\n")

        elif choice == 2:  # Discard
            if confirm(f"Really discard '{item}'?", default=False):
                mark_item_processed(inbox_path, item, "Discarded")
                processed_count += 1
                print("🗑️  Discarded\n")
            else:
                print("❌ Discard cancelled\n")

        elif choice == 3:  # Skip
            print("⏭️  Skipped (will process later)\n")
            # No action

        elif choice == 4:  # Quit
            print("\n⚠️  Processing interrupted. Progress saved.")
            break

    print(f"\n{'=' * 60}")
    print(f"✅ Processed {processed_count} items")
    print(f"{'=' * 60}\n")


def get_current_inbox_path(config: Dict[str, Any]) -> Path:
    """
    Get path to current month's inbox file.

    Args:
        config: Configuration dictionary

    Returns:
        Path to inbox file (e.g., vault/inbox/2025-10.md)

    Example:
        >>> inbox = get_current_inbox_path(config)
        >>> print(inbox)
        Path('/Users/user/vault/inbox/2025-10.md')
    """
    vault = get_vault_path(config)
    inbox_dir = vault / 'inbox'

    # Current month file: YYYY-MM.md
    current_month = datetime.now().strftime('%Y-%m')
    inbox_file = inbox_dir / f'{current_month}.md'

    return inbox_file


def process_item_as_task(item: str, config: Dict[str, Any]) -> Optional[str]:
    """
    Process inbox item as TaskWarrior task.

    Prompts user for task metadata and creates task.

    Args:
        item: Inbox item text
        config: Configuration dictionary

    Returns:
        Task UUID if created, None if failed or cancelled

    Example:
        >>> uuid = process_item_as_task("Buy groceries", config)
    """
    from plorp.utils.prompts import prompt, confirm

    print(f"\n📋 Creating task from: {item}")

    # Use item as default description, allow editing
    description = prompt("Task description", default=item)

    if not description:
        print("❌ Description required")
        return None

    # Gather metadata
    project = prompt("Project (optional)", default="")
    due = prompt("Due date (optional, e.g., 'tomorrow', '2025-10-15')", default="")
    priority = prompt("Priority (H/M/L, optional)", default="").upper()
    tags_str = prompt("Tags (comma-separated, optional)", default="")

    tags = [t.strip() for t in tags_str.split(',') if t.strip()] if tags_str else None

    # Confirm creation
    print(f"\n📋 Task summary:")
    print(f"   Description: {description}")
    if project:
        print(f"   Project: {project}")
    if due:
        print(f"   Due: {due}")
    if priority:
        print(f"   Priority: {priority}")
    if tags:
        print(f"   Tags: {', '.join(tags)}")

    if not confirm("Create this task?", default=True):
        return None

    # Create task
    uuid = create_task(
        description=description,
        project=project if project else None,
        due=due if due else None,
        priority=priority if priority else None,
        tags=tags
    )

    return uuid


def process_item_as_note(item: str, config: Dict[str, Any]) -> Optional[Path]:
    """
    Process inbox item as Obsidian note.

    Prompts user for note details and creates note.

    Args:
        item: Inbox item text
        config: Configuration dictionary

    Returns:
        Path to created note, or None if failed or cancelled

    Example:
        >>> note = process_item_as_note("Meeting ideas", config)
    """
    from plorp.utils.prompts import prompt, confirm

    print(f"\n📝 Creating note from: {item}")

    # Use item as default title
    title = prompt("Note title", default=item)

    if not title:
        print("❌ Title required")
        return None

    # Note type
    note_type = prompt("Note type", default="general")

    # Initial content
    print("Note content (press Ctrl+D when done, or leave empty):")
    try:
        lines = []
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass

    content = '\n'.join(lines) if lines else ''

    # Confirm creation
    print(f"\n📝 Note summary:")
    print(f"   Title: {title}")
    print(f"   Type: {note_type}")
    if content:
        print(f"   Content: {len(content)} characters")

    if not confirm("Create this note?", default=True):
        return None

    # Create note
    vault = get_vault_path(config)
    note_path = create_note(
        vault_path=vault,
        title=title,
        note_type=note_type,
        content=content
    )

    return note_path
```

**Tests for inbox.py:**

```python
# ABOUTME: Tests for inbox workflow - validates inbox processing with mocked interactions
# ABOUTME: Uses monkeypatch to mock user input and verify task/note creation
"""Tests for inbox workflow."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from plorp.workflows.inbox import (
    process,
    get_current_inbox_path,
    process_item_as_task,
    process_item_as_note
)


@pytest.fixture
def inbox_file(tmp_path):
    """Create sample inbox file."""
    vault = tmp_path / 'vault'
    inbox_dir = vault / 'inbox'
    inbox_dir.mkdir(parents=True)

    inbox = inbox_dir / '2025-10.md'
    content = """# Inbox - October 2025

## Unprocessed

- [ ] Buy groceries
- [ ] Research TaskWarrior hooks
- [ ] Meeting notes: Sprint planning

## Processed

- [x] Old item
"""
    inbox.write_text(content)

    return vault, inbox


def test_get_current_inbox_path(tmp_path, monkeypatch):
    """Test getting current inbox path."""
    vault = tmp_path / 'vault'
    vault.mkdir()

    config = {'vault_path': str(vault)}

    # Mock datetime to control current month
    from datetime import datetime
    mock_dt = MagicMock()
    mock_dt.now.return_value.strftime.return_value = '2025-10'
    monkeypatch.setattr('plorp.workflows.inbox.datetime', mock_dt)

    inbox_path = get_current_inbox_path(config)

    assert inbox_path == vault / 'inbox' / '2025-10.md'


@patch('plorp.workflows.inbox.create_task')
@patch('plorp.workflows.inbox.prompt')
@patch('plorp.workflows.inbox.confirm')
def test_process_item_as_task(mock_confirm, mock_prompt, mock_create_task, tmp_path):
    """Test processing inbox item as task."""
    mock_prompt.side_effect = [
        'Buy groceries',  # description
        'home',           # project
        'tomorrow',       # due
        'M',             # priority
        'shopping'       # tags
    ]
    mock_confirm.return_value = True
    mock_create_task.return_value = 'abc-123'

    config = {'vault_path': str(tmp_path)}

    uuid = process_item_as_task('Buy groceries', config)

    assert uuid == 'abc-123'
    mock_create_task.assert_called_once()
    call_kwargs = mock_create_task.call_args[1]
    assert call_kwargs['description'] == 'Buy groceries'
    assert call_kwargs['project'] == 'home'
    assert call_kwargs['due'] == 'tomorrow'
    assert call_kwargs['priority'] == 'M'
    assert call_kwargs['tags'] == ['shopping']


@patch('plorp.workflows.inbox.create_task')
@patch('plorp.workflows.inbox.prompt')
@patch('plorp.workflows.inbox.confirm')
def test_process_item_as_task_cancelled(mock_confirm, mock_prompt, mock_create_task):
    """Test cancelling task creation."""
    mock_prompt.side_effect = ['Task', '', '', '', '']
    mock_confirm.return_value = False  # User cancels

    uuid = process_item_as_task('Item', {})

    assert uuid is None
    mock_create_task.assert_not_called()


@patch('plorp.workflows.inbox.create_note')
@patch('plorp.workflows.inbox.prompt')
@patch('plorp.workflows.inbox.confirm')
@patch('builtins.input')
def test_process_item_as_note(mock_input, mock_confirm, mock_prompt, mock_create_note, tmp_path):
    """Test processing inbox item as note."""
    vault = tmp_path / 'vault'
    vault.mkdir()

    mock_prompt.side_effect = [
        'Meeting Notes',  # title
        'meeting'        # note_type
    ]
    mock_input.side_effect = EOFError()  # No content
    mock_confirm.return_value = True

    expected_path = vault / 'notes' / 'meeting-notes.md'
    mock_create_note.return_value = expected_path

    config = {'vault_path': str(vault)}

    note_path = process_item_as_note('Meeting item', config)

    assert note_path == expected_path
    mock_create_note.assert_called_once()


@patch('plorp.workflows.inbox.prompt_choice')
@patch('plorp.workflows.inbox.process_item_as_task')
@patch('plorp.workflows.inbox.mark_item_processed')
def test_process_create_task(mock_mark, mock_task, mock_choice, inbox_file):
    """Test full inbox processing creating task."""
    vault, inbox = inbox_file

    # User chooses "Create task" then "Quit"
    mock_choice.side_effect = [0, 4]  # 0 = Create task, 4 = Quit

    mock_task.return_value = 'abc-123'

    config = {'vault_path': str(vault)}

    import io, sys
    captured = io.StringIO()
    sys.stdout = captured

    process(config)

    sys.stdout = sys.__stdout__

    # Verify task created and marked
    mock_task.assert_called_once()
    mock_mark.assert_called_once()

    output = captured.getvalue()
    assert '✅ Task created' in output


@patch('plorp.workflows.inbox.prompt_choice')
@patch('plorp.workflows.inbox.confirm')
@patch('plorp.workflows.inbox.mark_item_processed')
def test_process_discard_item(mock_mark, mock_confirm, mock_choice, inbox_file):
    """Test discarding inbox item."""
    vault, inbox = inbox_file

    # User chooses "Discard" then "Quit"
    mock_choice.side_effect = [2, 4]  # 2 = Discard, 4 = Quit
    mock_confirm.return_value = True

    config = {'vault_path': str(vault)}

    import io, sys
    captured = io.StringIO()
    sys.stdout = captured

    process(config)

    sys.stdout = sys.__stdout__

    # Verify item marked as discarded
    mock_mark.assert_called_once()
    assert 'Discarded' in mock_mark.call_args[0][2]


def test_process_empty_inbox(tmp_path, capsys):
    """Test processing when inbox is empty."""
    vault = tmp_path / 'vault'
    inbox_dir = vault / 'inbox'
    inbox_dir.mkdir(parents=True)

    inbox = inbox_dir / '2025-10.md'
    content = """# Inbox

## Unprocessed

## Processed

- [x] Old items
"""
    inbox.write_text(content)

    config = {'vault_path': str(vault)}

    with patch('plorp.workflows.inbox.get_current_inbox_path', return_value=inbox):
        process(config)

    captured = capsys.readouterr()
    assert 'Inbox is empty' in captured.out


def test_process_no_inbox_file(tmp_path, capsys):
    """Test processing when inbox file doesn't exist."""
    vault = tmp_path / 'vault'
    vault.mkdir()

    inbox = vault / 'inbox' / '2025-10.md'

    config = {'vault_path': str(vault)}

    with patch('plorp.workflows.inbox.get_current_inbox_path', return_value=inbox):
        process(config)

    captured = capsys.readouterr()
    assert '❌ No inbox file found' in captured.out
```

---

### Module 4: CLI Update

**File:** `src/plorp/cli.py`

**Replace the `inbox` command stub:**

```python
@cli.command()
@click.argument('subcommand', default='process')
@click.pass_context
def inbox(ctx, subcommand):
    """Process inbox items."""
    if subcommand != 'process':
        click.echo(f"❌ Unknown inbox subcommand: {subcommand}")
        click.echo("💡 Available: brainplorp inbox process")
        ctx.exit(1)

    config = load_config()

    try:
        from plorp.workflows.inbox import process as inbox_process
        inbox_process(config)
    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        ctx.exit(1)
    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Inbox processing interrupted by user", err=True)
        ctx.exit(0)
    except Exception as e:
        click.echo(f"❌ Error during inbox processing: {e}", err=True)
        import traceback
        traceback.print_exc()
        ctx.exit(1)
```

**Update test_cli.py:**

```python
# Add to tests/test_cli.py:

@patch('plorp.cli.load_config')
@patch('plorp.workflows.inbox.process')
def test_inbox_command(mock_inbox_process, mock_load_config, tmp_path):
    """Test inbox command calls inbox workflow."""
    from click.testing import CliRunner
    from plorp.cli import cli

    mock_load_config.return_value = {'vault_path': str(tmp_path)}

    runner = CliRunner()
    result = runner.invoke(cli, ['inbox', 'process'])

    assert result.exit_code == 0
    mock_inbox_process.assert_called_once()


def test_inbox_command_invalid_subcommand():
    """Test inbox command with invalid subcommand."""
    from click.testing import CliRunner
    from plorp.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ['inbox', 'invalid'])

    assert result.exit_code == 1
    assert 'Unknown' in result.output
```

---

## Test Requirements

### Test Coverage Goals

- **integrations/obsidian.py:** >90% coverage
- **workflows/inbox.py:** >85% coverage (interactive paths are complex)
- **parsers/markdown.py (inbox functions):** 100% coverage
- **Overall Sprint 4 code:** >85% coverage

### Test Execution

```bash
# Run all Sprint 4 tests
pytest tests/test_integrations/test_obsidian.py \
       tests/test_workflows/test_inbox.py \
       tests/test_parsers/test_markdown.py::test_parse_inbox* \
       tests/test_parsers/test_markdown.py::test_mark_item* \
       -v

# Run with coverage
pytest tests/test_integrations/test_obsidian.py tests/test_workflows/test_inbox.py \
    --cov=src/plorp/integrations/obsidian \
    --cov=src/plorp/workflows/inbox \
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
from plorp.integrations.obsidian import create_note, generate_slug
from plorp.workflows.inbox import process
from plorp.parsers.markdown import parse_inbox_items, mark_item_processed
print('✓ All imports successful')
"

# 2. Tests pass
pytest tests/test_integrations/test_obsidian.py tests/test_workflows/test_inbox.py -v

# 3. Coverage check
pytest tests/test_integrations/test_obsidian.py tests/test_workflows/test_inbox.py \
    --cov=src/plorp/integrations/obsidian --cov=src/plorp/workflows/inbox \
    --cov-report=term
```

### CLI and Workflow Check

```bash
# 4. Create inbox file
mkdir -p ~/vault/inbox
cat > ~/vault/inbox/$(date +%Y-%m).md << 'EOF'
# Inbox - $(date +%B %Y)

## Unprocessed

- [ ] Test item: Buy groceries
- [ ] Another item: Research project

## Processed
EOF

# 5. Run inbox processing (interactive)
brainplorp inbox process
# → Shows items
# → Prompts for actions
# → Creates tasks/notes
# → Marks items processed

# 6. Verify items marked
cat ~/vault/inbox/$(date +%Y-%m).md
# → Items moved to Processed section
# → Marked with [x] and action description

# 7. Test empty inbox
# Process all items first, then:
brainplorp inbox process
# → Shows "Inbox is empty!"
```

### Code Quality Check

```bash
# 8. Black formatting
black --check src/plorp/integrations/obsidian.py src/plorp/workflows/inbox.py

# 9. ABOUTME comments
head -2 src/plorp/integrations/obsidian.py
head -2 src/plorp/workflows/inbox.py
```

---

## Completion Report Template

**Instructions:** Fill this out when Sprint 4 is complete.

### Implementation Summary

**What was implemented:**
- [x] integrations/obsidian.py - Note creation in vault
- [x] workflows/inbox.py - Interactive inbox processing
- [x] parsers/markdown.py - Inbox parsing functions added
- [x] cli.py - Updated inbox command
- [x] All files have ABOUTME comments
- [x] All functions have type hints and docstrings
- [x] Comprehensive test suite
- [x] All tests pass (149 total)
- [x] >85% test coverage achieved (91% overall)
- [x] CLI command works end-to-end

**Lines of code added:**
- Production code: ~540 lines
  - integrations/obsidian.py: 143 lines
  - workflows/inbox.py: 284 lines
  - parsers/markdown.py: ~110 lines (added to existing file)
  - cli.py updates: ~3 lines
- Test code: ~580 lines
  - test_integrations/test_obsidian.py: 170 lines
  - test_workflows/test_inbox.py: 344 lines
  - test_parsers/test_markdown.py: ~66 lines (added to existing)
  - test_cli.py updates: ~3 lines
- Total: ~1,120 lines

**Test coverage achieved:** 91% overall project coverage
- integrations/obsidian.py: 100%
- workflows/inbox.py: 90%
- parsers/markdown.py: 98%

**Number of tests written:** 40 new tests for Sprint 4 (149 total project tests)

### Deviations from Spec

**Minor deviations based on Q&A resolutions:**

1. **Sprint 3 dependency made required (Q1):** Updated from "optional but helpful" to hard dependency. Removed try/except ImportError handling for prompts module.

2. **Inbox file auto-creation (Q3):** Implemented automatic creation of inbox file with proper structure when user runs `brainplorp inbox process` for the first time.

3. **Shorter timestamp format (Q7):** Used date-only format for note filenames (`YYYY-MM-DD`) instead of full timestamp. Counter suffix for same-day duplicates.

4. **Meetings directory (Q10):** Meeting notes go in `vault/meetings/`, all other notes in `vault/notes/`.

5. **Interactive retry on failure (Q8):** Implemented full retry flow for task creation failures with "mark as processed anyway" option.

6. **Multi-line input preserved (Q5):** Kept Ctrl+D multi-line input for note content as specified, despite testing complexity.

All deviations were approved in Q&A section.

### Verification Commands

```bash
# Full verification from Success Criteria
cd /Users/jsd/Documents/plorp
source venv/bin/activate

# Run Sprint 4 tests
pytest tests/test_integrations/test_obsidian.py tests/test_workflows/test_inbox.py tests/test_parsers/test_markdown.py -v

# Check coverage
pytest tests/ --cov=src/brainplorp --cov-report=term

# Format check
black --check src/plorp/integrations/obsidian.py src/plorp/workflows/inbox.py src/plorp/parsers/markdown.py

# Test imports
python3 -c "from plorp.integrations.obsidian import create_note, generate_slug, get_vault_path; from plorp.workflows.inbox import process; from plorp.parsers.markdown import parse_inbox_items, mark_item_processed; print('✓ All imports successful')"
```

**Output summary:**
- All 149 tests pass (40 new for Sprint 4, 109 from previous sprints)
- 91% overall test coverage
- Sprint 4 modules: obsidian (100%), inbox (90%), markdown (98%)
- All code properly formatted with black
- All imports successful
- CLI command `brainplorp inbox process` works end-to-end

### Known Issues

None. All functionality works as specified with comprehensive error handling and test coverage exceeding targets.

### Handoff Notes for Sprint 5

**What Sprint 5 needs to know:**

- Note creation working via `create_note()`
- Obsidian integration complete
- Markdown parsing extended
- TaskWarrior integration from Sprint 1 available
- File utilities from Sprint 2 available

**Functions Sprint 5 will use:**
- `create_note()` - For creating notes with task links
- TaskWarrior `add_annotation()` - For bidirectional linking
- Markdown front matter functions - For adding task UUIDs to notes

**Note structure:**
```yaml
---
title: Note Title
created: 2025-10-06 14:30:00
type: general
tasks: []  # Sprint 5 will add task UUIDs here
---

# Note Title

Content here
```

**Files Sprint 5 should NOT modify:**
- `integrations/obsidian.py` - Complete (except potential enhancements)
- `workflows/inbox.py` - Complete

### Questions for PM/Architect

None - all Q&A questions were resolved before implementation.

### Recommendations

**For future sprints:**

1. **Error recovery:** The retry mechanism in inbox processing works well. Consider applying similar patterns to other interactive workflows.

2. **Note organization:** The meetings/notes directory split is simple but effective. Sprint 5 could enhance this with configurable directory structures if users request it.

3. **Test structure:** The nested test directory structure (test_workflows/, test_integrations/) is working well and should continue.

4. **Slug generation:** Current implementation keeps unicode characters. This works but may cause issues on some filesystems. Monitor for feedback.

5. **Inbox file auto-creation:** Auto-creating the inbox file on first use provides good UX. Consider similar patterns for other missing files/directories.

### Sign-off

- **Implemented by:** Claude Code Engineer Instance
- **Date completed:** October 6, 2025
- **Implementation time:** ~2 hours
- **Ready for Sprint 5:** Yes

---

## Q&A Section

### Questions from Engineering

**Q1: Sprint 3 dependency - prompts module**
```
Q: The spec states "Sprint 3 is complete (optional but helpful)" and has a try/except
   for importing prompts. However, the workflow critically depends on prompt_choice(),
   prompt(), and confirm() for user interaction.

   Should we:
   a) Require Sprint 3 to be complete before starting Sprint 4
   b) Implement minimal inline prompt functions in inbox.py if Sprint 3 not available
   c) Skip Sprint 4 if Sprint 3 isn't complete

Context: The current spec has error handling that returns early if prompts aren't
available, which means the inbox workflow simply won't work. This seems inconsistent
with marking Sprint 4 as "Ready for Implementation" if it has a hard dependency.

Status: PENDING
```

**Q2: parsers/markdown.py - existing vs new implementation**
```
Q: Sprint 4 adds parse_inbox_items() and mark_item_processed() to parsers/markdown.py.

   Should we:
   a) Replace the stub file completely with ABOUTME comments and all functions
   b) Add these functions to existing stub, keeping TODO comment
   c) Remove stub status since we're implementing part of it

   Also, should the ABOUTME comments describe what the full module will do (including
   Sprint 3 daily note parsing) or just what's implemented in Sprint 4?

Status: PENDING
```

**Q3: Inbox file structure - creation and initialization**
```
Q: The spec assumes inbox files exist with the correct structure (## Unprocessed /
   ## Processed sections).

   Should we:
   a) Provide a helper function to create/initialize inbox files
   b) Have process() auto-create the structure if file exists but sections are missing
   c) Require users to manually create files with correct structure
   d) Add a `brainplorp inbox init` command to create the current month's file

Context: User experience - if they run `brainplorp inbox process` and the file doesn't
exist, the error message suggests creating it manually. Should we make this easier?

Status: PENDING
```

**Q4: Inbox item text matching for mark_item_processed()**
```
Q: mark_item_processed() uses simple string replacement:
   `content.replace(old_line, new_line)`

   What if the same item text appears multiple times in the inbox? For example:
   - [ ] Buy groceries
   - [ ] Buy groceries  (duplicate)

   Should we:
   a) Replace only the first occurrence (current behavior)
   b) Add index/position parameter to specify which occurrence
   c) Warn user about duplicates
   d) Use a more robust identifier (line number, unique ID)

Status: PENDING
```

**Q5: Note content input - Ctrl+D vs simpler approach**
```
Q: The spec shows process_item_as_note() reading multi-line content via input()
   with EOFError handling (Ctrl+D). This is complex for testing and UX.

   Should we:
   a) Keep the Ctrl+D approach as specified
   b) Use a simpler single-line prompt for initial content
   c) Skip content input and let user add content in Obsidian after creation
   d) Prompt for just the first line, suggest editing in Obsidian for more

Context: The workflow is already interactive with many prompts. Adding multi-line
input increases complexity. Also, mocking EOFError in tests is fragile.

Status: PENDING
```

**Q6: Test directory structure**
```
Q: Should test files go in:
   - tests/test_integrations/test_obsidian.py (nested, following Sprint 1 pattern)
   - tests/test_workflows/test_inbox.py (nested, following Sprint 2 pattern)
   - tests/test_parsers/test_markdown.py (already exists from Sprint 3?)

   Confirming this follows the nested structure established in Sprint 2 Q&A.

Status: PENDING
```

**Q7: Slug generation with timestamps**
```
Q: The spec shows filenames as: "{slug}-{timestamp}.md"
   Example: "project-ideas-2025-10-06-143000.md"

   This creates very long filenames. Should we:
   a) Use full timestamp as specified (YYYY-MM-DD-HHMMSS)
   b) Use shorter timestamp (YYYYMMDD-HHMM)
   c) Use date only (YYYY-MM-DD)
   d) Just use slug with counter for uniqueness (project-ideas-1.md)

   Also, do we need seconds precision? Multiple notes in same minute seems unlikely.

Status: PENDING
```

**Q8: Error handling when TaskWarrior creation fails**
```
Q: If create_task() returns None (failure), process() prints "❌ Failed to create task"
   but doesn't mark the item as processed. User will see it again next time.

   Should we:
   a) Keep item unprocessed (current behavior - user can retry)
   b) Mark as processed with "Failed to create task" action
   c) Offer to retry or skip
   d) Move to a "## Failed" section

Context: What if TaskWarrior is broken/unavailable? User might be stuck unable to
process their inbox.

Status: PENDING
```

**Q9: Front matter YAML formatting**
```
Q: The spec shows:
   yaml.dump(front_matter, default_flow_style=False, sort_keys=False)

   The sort_keys=False is important to preserve field order, but yaml.dump() adds
   trailing newlines and may format differently than expected.

   Should we:
   a) Use yaml.dump() as specified
   b) Manually format the YAML for consistency (like daily note generation does)
   c) Add explicit formatting parameters (e.g., width, indent)

Status: PENDING
```

**Q10: Obsidian note subdirectory structure**
```
Q: The spec creates all notes in vault/notes/ regardless of note_type.

   Should we:
   a) Keep flat structure (vault/notes/)
   b) Create subdirectories by type (vault/notes/meeting/, vault/notes/project/)
   c) Make it configurable in config.yaml
   d) Leave for future enhancement

Context: Obsidian users often organize notes into subdirectories. Current approach
will mix all note types together.

Status: PENDING
```

---

### Answers from PM/Architect

**Q1: Sprint 3 dependency - prompts module**
```
Q: Should Sprint 3 be required before Sprint 4?
A: Yes. Make Sprint 3 a HARD DEPENDENCY.

   Rationale:
   - Sprint 4 inbox workflow is fundamentally interactive
   - Cannot function without prompt_choice(), prompt(), confirm()
   - Duplicating prompts in Sprint 4 violates DRY principle
   - Better engineering to have clean dependency

   Implementation:
   - Update dependencies: "Sprint 0, 1, 2, 3 complete"
   - Remove try/except ImportError handling for prompts
   - Engineering instances must complete Sprint 3 first

Status: RESOLVED
```

**Q2: parsers/markdown.py - existing vs new implementation**
```
Q: Should we replace stub or add to existing file?
A: Engineering decision - add functions to existing parsers/markdown.py from Sprint 3.

   Sprint 3 already implements parse_daily_note_tasks() and parse_frontmatter().
   Sprint 4 adds parse_inbox_items() and mark_item_processed() to the same file.

   Update ABOUTME comments to reflect full module purpose (both daily note and
   inbox parsing).

Status: RESOLVED
```

**Q3: Inbox file structure - creation and initialization**
```
Q: Should we auto-create inbox structure?
A: Yes, auto-create on first use.

   Implementation:
   When user runs `brainplorp inbox process`:
   1. Check if inbox file exists (vault/inbox/YYYY-MM.md)
   2. If not exists, auto-create with proper structure:
      ```markdown
      # Inbox - Month YYYY

      ## Unprocessed

      <!-- Add items here -->

      ## Processed
      ```
   3. Show message: "✨ Created inbox file: vault/inbox/2025-10.md"
   4. Then proceed with processing (will be empty, but structure is ready)

   This provides good UX - user doesn't need to manually create files.

Status: RESOLVED
```

**Q4: Inbox item text matching for mark_item_processed()**
```
Q: What if same item text appears multiple times?
A: Accept this edge case - replace() hits first occurrence only.

   This is a rare edge case (duplicate inbox items). Document in code comments
   that users should avoid duplicate items. Not worth the complexity of line
   number tracking.

Status: RESOLVED
```

**Q5: Note content input - Ctrl+D vs simpler approach**
```
Q: Should we use Ctrl+D multi-line input or simplify?
A: Keep multi-line input with Ctrl+D.

   Implementation as specified in original spec:
   - Read lines in loop until EOFError (Ctrl+D)
   - Join lines with newlines
   - This allows users to add initial content during inbox processing

   For testing, mock the input appropriately with EOFError handling.

Status: RESOLVED
```

**Q6: Test directory structure**
```
Q: Confirming nested structure?
A: Engineering decision - yes, use nested structure.

   Following Sprint 2 Q&A established convention:
   - tests/test_integrations/test_obsidian.py
   - tests/test_workflows/test_inbox.py
   - Create __init__.py files in test subdirectories

Status: RESOLVED
```

**Q7: Slug generation with timestamps**
```
Q: Full timestamp seems long - use shorter format?
A: Yes, use shorter format.

   Use date only (no time): `{slug}-{YYYY-MM-DD}.md`
   Example: `project-ideas-2025-10-06.md`

   If user creates multiple notes with same title on same day, add counter:
   - project-ideas-2025-10-06.md
   - project-ideas-2025-10-06-2.md
   - project-ideas-2025-10-06-3.md

   This is cleaner than full timestamps while handling uniqueness.

Status: RESOLVED
```

**Q8: Error handling when TaskWarrior creation fails**
```
Q: What to do if create_task() fails?
A: Interactive retry, then mark based on user choice (Option 2).

   Implementation:
   1. When create_task() returns None, print: "❌ Failed to create task"
   2. Prompt user: "Retry? (y/n)"
   3. If yes: retry create_task() once more
   4. If no OR second failure: prompt "Mark as processed anyway? (y/n)"
      - If yes: mark as processed with action "Failed to create task"
      - If no: leave unprocessed (user will see again next time)

   This gives user control over how to handle failures.

Status: RESOLVED
```

**Q9: Front matter YAML formatting**
```
Q: Use yaml.dump() or manually format?
A: Engineering decision - use yaml.dump() for correctness.

   Use: yaml.dump(front_matter, default_flow_style=False, sort_keys=False)

   This is cleaner than manual formatting and handles edge cases. The output
   might have minor formatting differences but will be valid YAML.

Status: RESOLVED
```

**Q10: Obsidian note subdirectory structure**
```
Q: Should notes go in subdirectories by type?
A: Meetings get special folder; everything else is flat.

   Implementation:
   - Meeting notes: vault/meetings/{slug}-{date}.md
   - All other notes: vault/notes/{slug}-{date}.md

   Update create_note() to check note_type:
   ```python
   if note_type == 'meeting':
       subdir = vault_path / 'meetings'
   else:
       subdir = vault_path / 'notes'
   ```

   This provides organization for meetings (common use case) while keeping
   other notes simple.

Status: RESOLVED
```

---

**Document Version:** 1.0
**Last Updated:** October 6, 2025
**Status:** Ready for Implementation
**Next Sprint:** SPRINT-5 (Note Linking)
