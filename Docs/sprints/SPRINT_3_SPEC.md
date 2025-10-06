# Sprint 3: Review Workflow

**Sprint ID:** SPRINT-3
**Status:** Ready for Implementation
**Dependencies:** Sprint 0, 1, 2 complete
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

Implement the `plorp review` command that provides an interactive end-of-day workflow for processing uncompleted tasks from the daily note. This is the second core workflow and closes the daily task management loop.

### What You're Building

The review workflow system with:
- Markdown parser to extract unchecked tasks from daily notes
- YAML front matter parsing
- Interactive CLI prompts for user decisions
- Task update operations (mark done, defer, change priority, delete)
- Review section appending to daily note
- Comprehensive tests with mocked user input

### What You're NOT Building

- Daily note generation (that's Sprint 2 - already complete)
- Inbox processing (that's Sprint 4)
- Note linking (that's Sprint 5)
- Front matter editing (that's Sprint 5)

---

## Engineering Handoff Prompt

```
You are implementing Sprint 3 for plorp, a workflow automation tool for TaskWarrior and Obsidian.

PROJECT CONTEXT:
- plorp is a Python CLI tool that bridges TaskWarrior and Obsidian
- This is Sprint 3: You're building the review workflow for end-of-day task processing
- Sprint 0 is complete: Project structure and test infrastructure ready
- Sprint 1 is complete: TaskWarrior integration available
- Sprint 2 is complete: Daily note generation working, file utilities available

YOUR TASK:
1. Read the full Sprint 3 specification: /Users/jsd/Documents/plorp/Docs/sprints/SPRINT_3_SPEC.md
2. Implement parsers/markdown.py - Parse daily notes and extract tasks
3. Implement utils/prompts.py - Interactive CLI prompts for user input
4. Implement review() function in workflows/daily.py
5. Update cli.py - Wire up the 'review' command
6. Write comprehensive tests for all modules
7. Follow TDD: Write tests BEFORE implementation
8. Mock user input and TaskWarrior calls in tests
9. Document your work in the Completion Report section

IMPORTANT REQUIREMENTS:
- TDD approach: Write test first, then implement, then verify
- Mock all TaskWarrior operations using Sprint 1 functions
- Mock all user input in tests (use monkeypatch for input())
- Use sample_daily_note fixture from tests/fixtures/
- All functions must have type hints and docstrings
- All new files must start with ABOUTME comments
- Handle edge cases: no daily note, all tasks complete, invalid input

WORKING DIRECTORY: /Users/jsd/Documents/plorp/

AVAILABLE FROM PREVIOUS SPRINTS:
- Sprint 1: taskwarrior.mark_done(), defer_task(), set_priority(), delete_task(), get_task_info()
- Sprint 2: read_file(), write_file(), config system, daily note format

CLARIFYING QUESTIONS:
If anything is unclear, add your questions to the Q&A section of this spec document and stop. The PM/Architect will answer them before you continue.

COMPLETION:
When done, fill out the Completion Report Template section in this document with details of your implementation.
```

---

## Technical Specifications

### Module 1: Markdown Parser

**File:** `src/plorp/parsers/markdown.py`

**Replace stub with:**

```python
# ABOUTME: Markdown parsing utilities for extracting tasks and front matter from daily notes
# ABOUTME: Uses regex to parse checkbox format and PyYAML for front matter parsing
"""
Markdown parsing utilities.

Provides functions to parse daily notes, extract unchecked tasks,
and parse YAML front matter.
"""
import re
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import yaml


def parse_daily_note_tasks(note_path: Path) -> List[Tuple[str, str]]:
    """
    Parse daily note for unchecked tasks.

    Extracts all unchecked checkboxes that contain TaskWarrior UUIDs.

    Args:
        note_path: Path to daily note markdown file

    Returns:
        List of (description, uuid) tuples for unchecked tasks.
        Empty list if no unchecked tasks or file not found.

    Example:
        >>> tasks = parse_daily_note_tasks(Path('vault/daily/2025-10-06.md'))
        >>> for desc, uuid in tasks:
        ...     print(f"{desc} -> {uuid}")
    """
    try:
        content = note_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        return []

    # Pattern: - [ ] Description (metadata, uuid: abc-123)
    # Matches unchecked checkboxes with UUID in metadata
    pattern = r'- \[ \] (.+?) \(.*?uuid: ([a-f0-9-]+)\)'
    matches = re.findall(pattern, content)

    return [(desc.strip(), uuid) for desc, uuid in matches]


def parse_frontmatter(content: str) -> Dict[str, Any]:
    """
    Extract YAML front matter from markdown content.

    Args:
        content: Markdown content string

    Returns:
        Dictionary of front matter fields. Empty dict if no front matter.

    Example:
        >>> content = "---\\ndate: 2025-10-06\\n---\\n# Title"
        >>> fm = parse_frontmatter(content)
        >>> fm['date']
        '2025-10-06'
    """
    if not content.startswith('---'):
        return {}

    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}

    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}


def extract_task_uuids_from_note(note_path: Path) -> List[str]:
    """
    Extract all TaskWarrior UUIDs from a note's front matter.

    Used for note-task linking (Sprint 5).

    Args:
        note_path: Path to markdown note

    Returns:
        List of task UUIDs. Empty list if no front matter or tasks field.

    Example:
        >>> uuids = extract_task_uuids_from_note(Path('vault/notes/meeting.md'))
        >>> for uuid in uuids:
        ...     print(f"Linked task: {uuid}")
    """
    try:
        content = note_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        return []

    fm = parse_frontmatter(content)
    return fm.get('tasks', [])
```

**Tests to write for markdown.py:**

```python
# ABOUTME: Tests for markdown parsing - validates task extraction and front matter parsing
# ABOUTME: Uses fixture files and constructed markdown to test various formats
"""Tests for markdown parsing."""
import pytest
from pathlib import Path
from plorp.parsers.markdown import (
    parse_daily_note_tasks,
    parse_frontmatter,
    extract_task_uuids_from_note
)


def test_parse_daily_note_tasks_with_unchecked(tmp_path):
    """Test parsing daily note with unchecked tasks."""
    note = tmp_path / 'daily.md'
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
    assert ('Buy groceries', 'abc-123') in tasks
    assert ('Write report', 'ghi-789') in tasks
    # Should NOT include checked task
    assert ('Call dentist', 'def-456') not in tasks


def test_parse_daily_note_tasks_all_checked(tmp_path):
    """Test parsing note with all tasks checked."""
    note = tmp_path / 'daily.md'
    content = """
- [x] Task 1 (uuid: abc-123)
- [x] Task 2 (uuid: def-456)
"""
    note.write_text(content)

    tasks = parse_daily_note_tasks(note)

    assert tasks == []


def test_parse_daily_note_tasks_no_uuid(tmp_path):
    """Test parsing note with checkboxes but no UUIDs."""
    note = tmp_path / 'daily.md'
    content = """
- [ ] Task without UUID
- [ ] Another task
"""
    note.write_text(content)

    tasks = parse_daily_note_tasks(note)

    assert tasks == []


def test_parse_daily_note_tasks_file_not_found(tmp_path):
    """Test parsing non-existent file returns empty list."""
    note = tmp_path / 'nonexistent.md'

    tasks = parse_daily_note_tasks(note)

    assert tasks == []


def test_parse_daily_note_tasks_sample_fixture(fixture_dir):
    """Test parsing the sample daily note fixture."""
    note = fixture_dir / 'sample_daily_note.md'

    tasks = parse_daily_note_tasks(note)

    # Sample has 3 unchecked tasks
    assert len(tasks) == 3

    descriptions = [desc for desc, _ in tasks]
    assert 'Call dentist' in descriptions
    assert 'Buy groceries' in descriptions
    assert 'Morning meditation' in descriptions


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

    assert fm['date'] == '2025-10-06'
    assert fm['type'] == 'daily'
    assert fm['tags'] == ['work', 'important']


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
    note = tmp_path / 'note.md'
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
    assert 'abc-123' in uuids
    assert 'def-456' in uuids
    assert 'ghi-789' in uuids


def test_extract_task_uuids_no_tasks_field(tmp_path):
    """Test extracting UUIDs when no tasks field in front matter."""
    note = tmp_path / 'note.md'
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
    note = tmp_path / 'nonexistent.md'

    uuids = extract_task_uuids_from_note(note)

    assert uuids == []
```

---

### Module 2: Interactive Prompts

**File:** `src/plorp/utils/prompts.py`

**Replace stub with:**

```python
# ABOUTME: Interactive CLI prompt utilities for user input during workflows
# ABOUTME: Provides simple prompt, choice menu, and confirmation functions with validation
"""
Interactive CLI prompts.

Utilities for getting user input during interactive workflows.
"""
from typing import List, Optional


def prompt(message: str, default: Optional[str] = None) -> str:
    """
    Prompt user for text input.

    Args:
        message: Prompt message to display
        default: Default value if user presses enter (optional)

    Returns:
        User input string, or default if provided and user pressed enter

    Example:
        >>> name = prompt("Enter your name: ")
        >>> date = prompt("Due date: ", default="tomorrow")
    """
    if default:
        message = f"{message} [{default}]: "
    else:
        message = f"{message}: "

    response = input(message).strip()

    if not response and default:
        return default

    return response


def prompt_choice(options: List[str], prompt_text: str = "Choose an option") -> int:
    """
    Prompt user to choose from a list of options.

    Args:
        options: List of option strings to display
        prompt_text: Custom prompt text (default: "Choose an option")

    Returns:
        Index of chosen option (0-based)

    Example:
        >>> choice = prompt_choice(['Task', 'Note', 'Skip'])
        >>> if choice == 0:
        ...     print("Creating task")
    """
    print(f"\n{prompt_text}:")
    for i, option in enumerate(options):
        print(f"  {i + 1}. {option}")

    while True:
        try:
            response = input(f"\nEnter choice (1-{len(options)}): ").strip()
            choice_num = int(response)

            if 1 <= choice_num <= len(options):
                return choice_num - 1  # Return 0-based index

            print(f"❌ Invalid choice. Please enter 1-{len(options)}.")

        except ValueError:
            print(f"❌ Invalid input. Please enter a number 1-{len(options)}.")
        except (EOFError, KeyboardInterrupt):
            # Handle Ctrl+C or EOF gracefully
            print("\n\n⚠️  Interrupted")
            return len(options) - 1  # Return last option (typically "Quit" or "Skip")


def confirm(message: str, default: bool = False) -> bool:
    """
    Prompt user for yes/no confirmation.

    Args:
        message: Confirmation message
        default: Default value if user presses enter

    Returns:
        True if user confirmed, False otherwise

    Example:
        >>> if confirm("Delete this task?"):
        ...     delete_task(uuid)
    """
    default_str = "Y/n" if default else "y/N"
    response = input(f"{message} [{default_str}]: ").strip().lower()

    if not response:
        return default

    return response in ('y', 'yes')
```

**Tests to write for prompts.py:**

```python
# ABOUTME: Tests for interactive prompts - validates user input handling
# ABOUTME: Uses monkeypatch to mock input() and test various user responses
"""Tests for interactive prompts."""
import pytest
from plorp.utils.prompts import prompt, prompt_choice, confirm


def test_prompt_basic(monkeypatch):
    """Test basic prompt with user input."""
    monkeypatch.setattr('builtins.input', lambda _: 'test response')

    result = prompt("Enter text")

    assert result == 'test response'


def test_prompt_with_default_used(monkeypatch):
    """Test prompt with default when user presses enter."""
    monkeypatch.setattr('builtins.input', lambda _: '')

    result = prompt("Enter date", default="tomorrow")

    assert result == 'tomorrow'


def test_prompt_with_default_overridden(monkeypatch):
    """Test prompt with default when user provides value."""
    monkeypatch.setattr('builtins.input', lambda _: 'friday')

    result = prompt("Enter date", default="tomorrow")

    assert result == 'friday'


def test_prompt_choice_valid(monkeypatch):
    """Test prompt_choice with valid input."""
    monkeypatch.setattr('builtins.input', lambda _: '2')

    choice = prompt_choice(['Option 1', 'Option 2', 'Option 3'])

    assert choice == 1  # 0-based index


def test_prompt_choice_first_option(monkeypatch):
    """Test prompt_choice selecting first option."""
    monkeypatch.setattr('builtins.input', lambda _: '1')

    choice = prompt_choice(['First', 'Second'])

    assert choice == 0


def test_prompt_choice_last_option(monkeypatch):
    """Test prompt_choice selecting last option."""
    monkeypatch.setattr('builtins.input', lambda _: '3')

    choice = prompt_choice(['One', 'Two', 'Three'])

    assert choice == 2


def test_prompt_choice_invalid_then_valid(monkeypatch):
    """Test prompt_choice with invalid input then valid."""
    inputs = iter(['0', '5', 'abc', '2'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    choice = prompt_choice(['One', 'Two', 'Three'])

    assert choice == 1


def test_prompt_choice_keyboard_interrupt(monkeypatch):
    """Test prompt_choice handles KeyboardInterrupt."""
    monkeypatch.setattr('builtins.input', lambda _: raise_keyboard_interrupt())

    def raise_keyboard_interrupt():
        raise KeyboardInterrupt()

    choice = prompt_choice(['One', 'Two', 'Quit'])

    # Should return last option (Quit)
    assert choice == 2


def test_confirm_yes(monkeypatch):
    """Test confirm with 'yes' input."""
    monkeypatch.setattr('builtins.input', lambda _: 'y')

    result = confirm("Proceed?")

    assert result is True


def test_confirm_no(monkeypatch):
    """Test confirm with 'no' input."""
    monkeypatch.setattr('builtins.input', lambda _: 'n')

    result = confirm("Proceed?")

    assert result is False


def test_confirm_default_true(monkeypatch):
    """Test confirm with default True and empty input."""
    monkeypatch.setattr('builtins.input', lambda _: '')

    result = confirm("Proceed?", default=True)

    assert result is True


def test_confirm_default_false(monkeypatch):
    """Test confirm with default False and empty input."""
    monkeypatch.setattr('builtins.input', lambda _: '')

    result = confirm("Proceed?", default=False)

    assert result is False


def test_confirm_various_yes_forms(monkeypatch):
    """Test confirm accepts 'yes', 'Y', 'YES'."""
    for response in ['yes', 'Y', 'YES', 'Yes']:
        monkeypatch.setattr('builtins.input', lambda _, r=response: r)

        result = confirm("Proceed?")

        assert result is True, f"Failed for input: {response}"
```

---

### Module 3: Review Workflow Implementation

**File:** `src/plorp/workflows/daily.py`

**Replace the `review()` stub with:**

```python
def review(config: Dict[str, Any]) -> None:
    """
    Interactive end-of-day review.

    Reads today's daily note, finds uncompleted tasks, and prompts user
    for action on each task. Updates TaskWarrior and appends decisions
    to the daily note.

    Args:
        config: Configuration dictionary

    Example:
        >>> config = load_config()
        >>> review(config)
        # Interactive prompts follow...
    """
    from plorp.parsers.markdown import parse_daily_note_tasks
    from plorp.utils.prompts import prompt_choice, prompt, confirm
    from plorp.integrations.taskwarrior import (
        get_task_info, mark_done, defer_task, set_priority, delete_task
    )

    today = date.today()
    vault_path = Path(config['vault_path'])
    daily_path = vault_path / 'daily' / f'{format_date_iso(today)}.md'

    if not daily_path.exists():
        print(f"❌ No daily note found for {format_date_long(today)}")
        print(f"💡 Run: plorp start")
        return

    # Parse uncompleted tasks
    uncompleted = parse_daily_note_tasks(daily_path)

    if not uncompleted:
        print(f"\n✅ All tasks completed! Great work on {format_date_long(today)}")
        return

    print(f"\n📋 {len(uncompleted)} tasks remaining from {format_date_long(today)}\n")

    decisions = []

    for task_desc, task_uuid in uncompleted:
        # Get full task details from TaskWarrior
        task = get_task_info(task_uuid)

        if not task:
            print(f"\n⚠️  Task not found in TaskWarrior: {task_desc}")
            print(f"    UUID: {task_uuid}")
            print("    (Task may have been deleted or modified outside plorp)")
            continue

        # Show task details
        print(f"\n{'=' * 60}")
        print(f"📌 Task: {task['description']}")
        if 'project' in task:
            print(f"   Project: {task['project']}")
        if 'due' in task:
            due_str = format_taskwarrior_date_short(task['due'])
            print(f"   Due: {due_str}")
        if 'priority' in task:
            print(f"   Priority: {task['priority']}")
        print(f"{'=' * 60}")

        # Prompt for action
        choice = prompt_choice(
            options=[
                "✅ Mark done",
                "📅 Defer to tomorrow",
                "📆 Defer to specific date",
                "⚡ Change priority",
                "⏭️  Skip (keep as-is)",
                "🗑️  Delete task",
                "🚪 Quit review"
            ],
            prompt_text="What would you like to do with this task?"
        )

        if choice == 0:  # Mark done
            if mark_done(task_uuid):
                decisions.append(f"✅ {task_desc}")
                print("✅ Marked done\n")
            else:
                print("❌ Failed to mark done\n")

        elif choice == 1:  # Defer to tomorrow
            if defer_task(task_uuid, 'tomorrow'):
                decisions.append(f"📅 {task_desc} → tomorrow")
                print("📅 Deferred to tomorrow\n")
            else:
                print("❌ Failed to defer\n")

        elif choice == 2:  # Defer to specific date
            new_due = prompt("New due date (YYYY-MM-DD or 'friday', etc)")
            if new_due and defer_task(task_uuid, new_due):
                decisions.append(f"📅 {task_desc} → {new_due}")
                print(f"📅 Deferred to {new_due}\n")
            else:
                print("❌ Failed to defer\n")

        elif choice == 3:  # Change priority
            priority = prompt("Priority (H/M/L or blank to remove)", default="").upper()
            if set_priority(task_uuid, priority):
                priority_display = priority if priority else "none"
                decisions.append(f"⚡ {task_desc} → priority {priority_display}")
                print(f"⚡ Priority set to {priority_display}\n")
            else:
                print("❌ Failed to set priority\n")

        elif choice == 4:  # Skip
            print("⏭️  Skipped (no changes)\n")
            # No action, just continue

        elif choice == 5:  # Delete
            if confirm(f"Really delete '{task_desc}'?", default=False):
                if delete_task(task_uuid):
                    decisions.append(f"🗑️  {task_desc} (deleted)")
                    print("🗑️  Deleted\n")
                else:
                    print("❌ Failed to delete\n")
            else:
                print("❌ Delete cancelled\n")

        elif choice == 6:  # Quit
            print("\n⚠️  Review interrupted. Progress saved so far.")
            break

    # Append decisions to daily note
    if decisions:
        append_review_section(daily_path, decisions)

    print(f"\n{'=' * 60}")
    print(f"✅ Review complete - processed {len(decisions)} tasks")
    print(f"{'=' * 60}\n")


def append_review_section(daily_path: Path, decisions: List[str]) -> None:
    """
    Append review decisions to daily note.

    Replaces the "## Review Section" with a summary of user decisions.

    Args:
        daily_path: Path to daily note
        decisions: List of decision strings to append

    Example:
        >>> decisions = ["✅ Task completed", "📅 Task deferred"]
        >>> append_review_section(Path('daily/2025-10-06.md'), decisions)
    """
    from datetime import datetime
    from plorp.utils.files import read_file, write_file

    content = read_file(daily_path)

    # Build review section
    review_section = f"\n## Review Section\n\n"
    review_section += f"**Review completed:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

    for decision in decisions:
        review_section += f"- {decision}\n"

    # Replace existing review section (or append if not found)
    if '## Review Section' in content:
        # Replace from "## Review Section" to end of file
        content = re.sub(
            r'## Review Section.*$',
            review_section.strip(),
            content,
            flags=re.DOTALL
        )
    else:
        content += f"\n{review_section}"

    write_file(daily_path, content)
```

**Add import at top of daily.py:**

```python
import re
```

**Tests to write for review workflow:**

```python
# Add to tests/test_workflows/test_daily.py:

@pytest.fixture
def daily_note_with_uncompleted_tasks(tmp_path):
    """Create a daily note with uncompleted tasks."""
    vault = tmp_path / 'vault'
    daily_dir = vault / 'daily'
    daily_dir.mkdir(parents=True)

    note_path = daily_dir / '2025-10-06.md'
    content = """---
date: 2025-10-06
type: daily
---

# Daily Note - October 06, 2025

## Tasks

- [ ] Buy groceries (project: home, uuid: abc-123)
- [x] Call dentist (project: health, uuid: def-456)
- [ ] Write report (due: 2025-10-07, uuid: ghi-789)

---

## Notes

Made good progress today.

---

## Review Section

<!-- Auto-populated by `plorp review` -->
"""
    note_path.write_text(content)

    return vault, note_path


@patch('plorp.workflows.daily.get_task_info')
@patch('plorp.workflows.daily.mark_done')
@patch('plorp.workflows.daily.prompt_choice')
def test_review_mark_task_done(mock_prompt, mock_mark_done, mock_get_task,
                                daily_note_with_uncompleted_tasks, monkeypatch):
    """Test review workflow marking task as done."""
    from datetime import date
    from plorp.workflows.daily import review

    vault, note_path = daily_note_with_uncompleted_tasks

    # Mock date.today()
    monkeypatch.setattr('plorp.workflows.daily.date', type('obj', (), {'today': lambda: date(2025, 10, 6)})())

    # Mock task info
    mock_get_task.side_effect = [
        {'uuid': 'abc-123', 'description': 'Buy groceries', 'project': 'home'},
        {'uuid': 'ghi-789', 'description': 'Write report', 'due': '20251007T000000Z'}
    ]

    # Mock user choosing "Mark done" for both tasks
    mock_prompt.side_effect = [0, 0]  # Choice 0 = Mark done

    # Mock mark_done success
    mock_mark_done.return_value = True

    config = {'vault_path': str(vault)}

    # Capture stdout
    import io, sys
    captured = io.StringIO()
    sys.stdout = captured

    review(config)

    sys.stdout = sys.__stdout__

    # Verify mark_done called twice
    assert mock_mark_done.call_count == 2

    # Verify review section appended
    updated_content = note_path.read_text()
    assert '## Review Section' in updated_content
    assert '✅ Buy groceries' in updated_content
    assert '✅ Write report' in updated_content


@patch('plorp.workflows.daily.get_task_info')
@patch('plorp.workflows.daily.defer_task')
@patch('plorp.workflows.daily.prompt_choice')
def test_review_defer_task(mock_prompt, mock_defer, mock_get_task,
                           daily_note_with_uncompleted_tasks, monkeypatch):
    """Test review workflow deferring task."""
    from datetime import date
    from plorp.workflows.daily import review

    vault, note_path = daily_note_with_uncompleted_tasks

    monkeypatch.setattr('plorp.workflows.daily.date', type('obj', (), {'today': lambda: date(2025, 10, 6)})())

    mock_get_task.return_value = {
        'uuid': 'abc-123',
        'description': 'Buy groceries',
        'project': 'home'
    }

    # Mock user choosing "Defer to tomorrow" then "Quit"
    mock_prompt.side_effect = [1, 6]  # 1 = Defer to tomorrow, 6 = Quit

    mock_defer.return_value = True

    config = {'vault_path': str(vault)}

    import io, sys
    captured = io.StringIO()
    sys.stdout = captured

    review(config)

    sys.stdout = sys.__stdout__

    # Verify defer_task called
    mock_defer.assert_called_once_with('abc-123', 'tomorrow')

    # Verify review section
    updated_content = note_path.read_text()
    assert '📅 Buy groceries → tomorrow' in updated_content


def test_review_no_daily_note(tmp_path, capsys, monkeypatch):
    """Test review when no daily note exists."""
    from datetime import date
    from plorp.workflows.daily import review

    vault = tmp_path / 'vault'
    vault.mkdir()

    monkeypatch.setattr('plorp.workflows.daily.date', type('obj', (), {'today': lambda: date(2025, 10, 6)})())

    config = {'vault_path': str(vault)}

    review(config)

    captured = capsys.readouterr()
    assert '❌ No daily note found' in captured.out
    assert 'plorp start' in captured.out


def test_review_all_tasks_complete(tmp_path, capsys, monkeypatch):
    """Test review when all tasks are checked."""
    from datetime import date
    from plorp.workflows.daily import review

    vault = tmp_path / 'vault'
    daily_dir = vault / 'daily'
    daily_dir.mkdir(parents=True)

    note_path = daily_dir / '2025-10-06.md'
    content = """---
date: 2025-10-06
---

# Daily Note

- [x] All tasks (uuid: abc-123)
- [x] Are complete (uuid: def-456)
"""
    note_path.write_text(content)

    monkeypatch.setattr('plorp.workflows.daily.date', type('obj', (), {'today': lambda: date(2025, 10, 6)})())

    config = {'vault_path': str(vault)}

    review(config)

    captured = capsys.readouterr()
    assert '✅ All tasks completed' in captured.out


def test_append_review_section_new(tmp_path):
    """Test appending review section to note without one."""
    from plorp.workflows.daily import append_review_section

    note = tmp_path / 'daily.md'
    content = """# Daily Note

## Tasks

Some tasks here
"""
    note.write_text(content)

    decisions = ['✅ Task 1 done', '📅 Task 2 deferred']
    append_review_section(note, decisions)

    updated = note.read_text()
    assert '## Review Section' in updated
    assert '✅ Task 1 done' in updated
    assert '📅 Task 2 deferred' in updated


def test_append_review_section_replace_existing(tmp_path):
    """Test replacing existing review section."""
    from plorp.workflows.daily import append_review_section

    note = tmp_path / 'daily.md'
    content = """# Daily Note

## Review Section

Old content here
Should be replaced
"""
    note.write_text(content)

    decisions = ['✅ New decision']
    append_review_section(note, decisions)

    updated = note.read_text()
    assert 'Old content' not in updated
    assert '✅ New decision' in updated
```

---

### Module 4: CLI Update

**File:** `src/plorp/cli.py`

**Replace the `review` command stub:**

```python
@cli.command()
@click.pass_context
def review(ctx):
    """Interactive end-of-day review."""
    config = load_config()

    try:
        from plorp.workflows.daily import review as daily_review
        daily_review(config)
    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        ctx.exit(1)
    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Review interrupted by user", err=True)
        ctx.exit(0)
    except Exception as e:
        click.echo(f"❌ Error during review: {e}", err=True)
        import traceback
        traceback.print_exc()
        ctx.exit(1)
```

**Update test_cli.py:**

```python
# Add to tests/test_cli.py:

@patch('plorp.cli.load_config')
@patch('plorp.workflows.daily.review')
def test_review_command(mock_daily_review, mock_load_config, tmp_path):
    """Test review command calls daily review workflow."""
    from click.testing import CliRunner
    from plorp.cli import cli

    mock_load_config.return_value = {'vault_path': str(tmp_path)}

    runner = CliRunner()
    result = runner.invoke(cli, ['review'])

    assert result.exit_code == 0
    mock_daily_review.assert_called_once()


@patch('plorp.cli.load_config')
@patch('plorp.workflows.daily.review')
def test_review_command_keyboard_interrupt(mock_daily_review, mock_load_config):
    """Test review command handles keyboard interrupt."""
    from click.testing import CliRunner
    from plorp.cli import cli

    mock_load_config.return_value = {'vault_path': '/tmp/vault'}
    mock_daily_review.side_effect = KeyboardInterrupt()

    runner = CliRunner()
    result = runner.invoke(cli, ['review'])

    # Should exit gracefully
    assert result.exit_code == 0
    assert 'interrupted' in result.output.lower()
```

---

## Test Requirements

### Test Coverage Goals

- **parsers/markdown.py:** 100% coverage
- **utils/prompts.py:** >95% coverage (KeyboardInterrupt paths optional)
- **workflows/daily.py review():** >90% coverage
- **Overall Sprint 3 code:** >90% coverage

### Required Test Files

1. **tests/test_parsers/test_markdown.py** - Markdown parsing tests
2. **tests/test_utils/test_prompts.py** - Prompt utility tests
3. **tests/test_workflows/test_daily.py** - Review workflow tests (add to existing)
4. **tests/test_cli.py** - CLI tests (update existing)

### Test Execution

```bash
# Run all Sprint 3 tests
pytest tests/test_parsers/ tests/test_utils/test_prompts.py tests/test_workflows/test_daily.py::test_review* -v

# Run with coverage
pytest tests/test_parsers/ tests/test_utils/test_prompts.py tests/test_workflows/test_daily.py \
    --cov=src/plorp/parsers \
    --cov=src/plorp/utils/prompts \
    --cov=src/plorp/workflows/daily \
    --cov-report=term-missing

# Test interactively (manual test)
plorp review
```

---

## Success Criteria

### Import and Test Check

```bash
cd /Users/jsd/Documents/plorp
source venv/bin/activate

# 1. All modules can be imported
python3 -c "
from plorp.parsers.markdown import parse_daily_note_tasks, parse_frontmatter
from plorp.utils.prompts import prompt, prompt_choice, confirm
from plorp.workflows.daily import review
print('✓ All imports successful')
"

# 2. All tests pass
pytest tests/test_parsers/ \
       tests/test_utils/test_prompts.py \
       tests/test_workflows/test_daily.py -v
# → All tests pass (40+ tests)

# 3. Coverage exceeds 90%
pytest tests/test_parsers/ tests/test_utils/test_prompts.py tests/test_workflows/test_daily.py \
    --cov=src/plorp/parsers --cov=src/plorp/utils/prompts --cov=src/plorp/workflows/daily \
    --cov-report=term
# → Coverage >90%
```

### CLI and Workflow Check

```bash
# 4. Generate daily note first
plorp start

# 5. Run review (interactive)
plorp review
# → Shows uncompleted tasks
# → Prompts for actions
# → Updates TaskWarrior
# → Appends review section to daily note

# 6. Verify review section added
cat ~/vault/daily/$(date +%Y-%m-%d).md
# → Contains "## Review Section"
# → Contains timestamp
# → Contains decisions

# 7. Test with no uncompleted tasks
# Check all tasks in daily note first, then:
plorp review
# → Shows "All tasks completed!"

# 8. Test with no daily note
rm ~/vault/daily/$(date +%Y-%m-%d).md
plorp review
# → Shows error message
# → Suggests running "plorp start"
```

### Code Quality Check

```bash
# 9. Black formatting
black --check src/plorp/parsers/ src/plorp/utils/prompts.py src/plorp/workflows/daily.py
# → All files properly formatted

# 10. ABOUTME comments
head -2 src/plorp/parsers/markdown.py
head -2 src/plorp/utils/prompts.py
# → Shows ABOUTME comments
```

---

## Completion Report Template

**Instructions:** Fill this out when Sprint 3 is complete.

### Implementation Summary

**What was implemented:**
- [ ] parsers/markdown.py - Task parsing and front matter extraction
- [ ] utils/prompts.py - Interactive prompt utilities
- [ ] workflows/daily.py review() - Complete review workflow
- [ ] cli.py - Updated review command
- [ ] All files have ABOUTME comments
- [ ] All functions have type hints and docstrings
- [ ] Comprehensive test suite (40+ tests)
- [ ] All tests pass
- [ ] >90% test coverage achieved
- [ ] CLI command works interactively

**Lines of code added:**
- Production code: [Fill in]
- Test code: [Fill in]
- Total: [Fill in]

**Test coverage achieved:** [Fill in]%

**Number of tests written:** [Fill in]

### Deviations from Spec

**Any changes from the specification?**

[Describe any intentional deviations and why they were necessary]

### Verification Commands

```bash
cd /Users/jsd/Documents/plorp
source venv/bin/activate

# All verification commands from Success Criteria
pytest tests/test_parsers/ tests/test_utils/test_prompts.py tests/test_workflows/test_daily.py -v

plorp start
plorp review
cat ~/vault/daily/$(date +%Y-%m-%d).md
```

**Output summary:** [Describe what each command showed]

### Known Issues

**Any known limitations or issues:**

[List any issues]

### Handoff Notes for Sprint 4

**What Sprint 4 needs to know:**

- Markdown parser available for parsing various note formats
- Front matter parsing available
- File utilities available from Sprint 2
- TaskWarrior operations available from Sprint 1
- Prompt utilities available for interactive workflows

**Functions Sprint 4 will use:**
- `parse_frontmatter()` - May use for inbox file structure
- `prompt_choice()` - For inbox processing decisions
- `prompt()` - For gathering task/note metadata
- File utilities from Sprint 2

**Markdown parsing patterns:**
- Checkboxes: `- [ ] Description (metadata, uuid: xxx)`
- Front matter: YAML between `---` delimiters

**Files Sprint 4 should NOT modify:**
- `parsers/markdown.py` - Can add new functions but don't modify existing
- `utils/prompts.py` - Complete

### Questions for PM/Architect

[Add any questions]

### Recommendations

**Suggestions for future sprints:**

[Recommendations]

### Sign-off

- **Implemented by:** [Claude Code Engineer Instance]
- **Date completed:** [Date]
- **Implementation time:** [Actual time taken]
- **Ready for Sprint 4:** [Yes/No]

---

## Q&A Section

### Questions from Engineering

[Add questions here]

---

### Answers from PM/Architect

[Answers will be added here]

---

**Document Version:** 1.0
**Last Updated:** October 6, 2025
**Status:** Ready for Implementation
**Next Sprint:** SPRINT-4 (Inbox Processing)
