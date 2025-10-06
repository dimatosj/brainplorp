# Sprint 2: Daily Note Generation

**Sprint ID:** SPRINT-2
**Status:** Ready for Implementation
**Dependencies:** Sprint 0, Sprint 1 complete
**Estimated Duration:** 1-2 days

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

Implement the `plorp start` command that queries TaskWarrior and generates a formatted daily note in Obsidian with all relevant tasks. This is the first core workflow and will be used daily by plorp users.

### What You're Building

The daily note generation system with:
- Configuration management (load/save user config)
- File utilities (read/write markdown files)
- Daily workflow (query tasks, generate markdown)
- Markdown generation with YAML front matter
- Task formatting as checkboxes with UUIDs
- CLI command wiring for `plorp start`
- Comprehensive tests with mocked TaskWarrior

### What You're NOT Building

- Review workflow (that's Sprint 3)
- Markdown parsing (that's Sprint 3)
- Interactive prompts (that's Sprint 3)
- Inbox processing (that's Sprint 4)

---

## Engineering Handoff Prompt

```
You are implementing Sprint 2 for plorp, a workflow automation tool for TaskWarrior and Obsidian.

PROJECT CONTEXT:
- plorp is a Python CLI tool that bridges TaskWarrior and Obsidian
- This is Sprint 2: You're building the daily note generation workflow
- Sprint 0 is complete: Project structure and test infrastructure ready
- Sprint 1 is complete: TaskWarrior integration available

YOUR TASK:
1. Read the full Sprint 2 specification: /Users/jsd/Documents/plorp/Docs/sprints/SPRINT_2_SPEC.md
2. Implement config.py - Configuration loading/saving
3. Implement utils/files.py - File I/O utilities
4. Implement utils/dates.py - Date formatting utilities
5. Implement workflows/daily.py - Daily note generation (start function only)
6. Update cli.py - Wire up the 'start' command
7. Write comprehensive tests for all modules
8. Follow TDD: Write tests BEFORE implementation
9. Mock TaskWarrior integration - use Sprint 1 functions
10. Document your work in the Completion Report section

IMPORTANT REQUIREMENTS:
- TDD approach: Write test first, then implement, then verify
- Mock all TaskWarrior calls using Sprint 1 functions
- Use tmp_path fixtures for file operations
- All functions must have type hints and docstrings
- All new files must start with ABOUTME comments
- Test with fixture data from tests/fixtures/

WORKING DIRECTORY: /Users/jsd/Documents/plorp/

AVAILABLE FROM SPRINT 1:
You can import and use these functions from Sprint 1:
- from plorp.integrations.taskwarrior import get_overdue_tasks, get_due_today, get_recurring_today

In tests, mock these functions to return fixture data.

CLARIFYING QUESTIONS:
If anything is unclear, add your questions to the Q&A section of this spec document and stop. The PM/Architect will answer them before you continue.

COMPLETION:
When done, fill out the Completion Report Template section in this document with details of your implementation.
```

---

## Technical Specifications

### Module 1: Configuration Management

**File:** `src/plorp/config.py`

```python
# ABOUTME: Configuration management for plorp - loads user settings from YAML config file
# ABOUTME: Handles default config creation, loading, saving, and merging with defaults
"""
Configuration management for plorp.

Loads configuration from YAML file, creates defaults if not found.
Config location: ~/.config/plorp/config.yaml (or $XDG_CONFIG_HOME/plorp/config.yaml)
"""
import os
from pathlib import Path
from typing import Dict, Any
import yaml


# Default configuration values
DEFAULT_CONFIG: Dict[str, Any] = {
    'vault_path': os.path.expanduser('~/vault'),
    'taskwarrior_data': os.path.expanduser('~/.task'),
    'inbox_email': None,
    'default_editor': os.environ.get('EDITOR', 'vim'),
}


def get_config_path() -> Path:
    """
    Get the path to the configuration file.

    Returns:
        Path to config file (e.g., ~/.config/plorp/config.yaml)

    Priority:
        1. $XDG_CONFIG_HOME/plorp/config.yaml
        2. ~/.config/plorp/config.yaml
    """
    xdg_config = os.environ.get('XDG_CONFIG_HOME')
    if xdg_config:
        return Path(xdg_config) / 'plorp' / 'config.yaml'

    return Path.home() / '.config' / 'plorp' / 'config.yaml'


def load_config() -> Dict[str, Any]:
    """
    Load configuration from file or create default.

    If config file doesn't exist, creates it with default values.

    Returns:
        Configuration dictionary with all settings.

    Example:
        >>> config = load_config()
        >>> vault_path = config['vault_path']
    """
    config_path = get_config_path()

    if not config_path.exists():
        # Create default config
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    with open(config_path) as f:
        user_config = yaml.safe_load(f) or {}

    # Merge with defaults (user config overrides defaults)
    config = DEFAULT_CONFIG.copy()
    config.update(user_config)

    return config


def save_config(config: Dict[str, Any]) -> None:
    """
    Save configuration to file.

    Args:
        config: Configuration dictionary to save

    Example:
        >>> config = load_config()
        >>> config['vault_path'] = '/custom/path'
        >>> save_config(config)
    """
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
```

**Tests to write for config.py:**

```python
# ABOUTME: Tests for configuration management - validates loading, saving, and defaults
# ABOUTME: Uses temporary directories to test config file creation without affecting system
"""Tests for configuration management."""
import pytest
from pathlib import Path
from plorp.config import get_config_path, load_config, save_config, DEFAULT_CONFIG


def test_default_config_structure():
    """Test that DEFAULT_CONFIG has required fields."""
    assert 'vault_path' in DEFAULT_CONFIG
    assert 'taskwarrior_data' in DEFAULT_CONFIG
    assert 'inbox_email' in DEFAULT_CONFIG
    assert 'default_editor' in DEFAULT_CONFIG


def test_get_config_path_with_xdg(monkeypatch):
    """Test config path uses XDG_CONFIG_HOME if set."""
    monkeypatch.setenv('XDG_CONFIG_HOME', '/custom/config')

    path = get_config_path()

    assert path == Path('/custom/config/plorp/config.yaml')


def test_get_config_path_default(monkeypatch):
    """Test config path falls back to ~/.config if XDG not set."""
    monkeypatch.delenv('XDG_CONFIG_HOME', raising=False)

    path = get_config_path()

    assert path == Path.home() / '.config' / 'plorp' / 'config.yaml'


def test_load_config_creates_default(tmp_path, monkeypatch):
    """Test that load_config creates default config if none exists."""
    config_dir = tmp_path / 'plorp'
    config_file = config_dir / 'config.yaml'

    # Mock get_config_path to return our tmp path
    monkeypatch.setattr('plorp.config.get_config_path', lambda: config_file)

    config = load_config()

    assert config_file.exists()
    assert config['vault_path'] == DEFAULT_CONFIG['vault_path']


def test_load_config_existing(tmp_path, monkeypatch):
    """Test loading existing config file."""
    config_dir = tmp_path / 'plorp'
    config_dir.mkdir()
    config_file = config_dir / 'config.yaml'

    # Write custom config
    custom_config = {
        'vault_path': '/custom/vault',
        'taskwarrior_data': '/custom/task'
    }

    import yaml
    with open(config_file, 'w') as f:
        yaml.dump(custom_config, f)

    monkeypatch.setattr('plorp.config.get_config_path', lambda: config_file)

    config = load_config()

    assert config['vault_path'] == '/custom/vault'
    assert config['taskwarrior_data'] == '/custom/task'
    # Should merge with defaults
    assert 'default_editor' in config


def test_save_config(tmp_path, monkeypatch):
    """Test saving configuration."""
    config_dir = tmp_path / 'plorp'
    config_file = config_dir / 'config.yaml'

    monkeypatch.setattr('plorp.config.get_config_path', lambda: config_file)

    test_config = {'vault_path': '/test/vault'}
    save_config(test_config)

    assert config_file.exists()

    # Verify saved content
    import yaml
    with open(config_file) as f:
        saved = yaml.safe_load(f)

    assert saved['vault_path'] == '/test/vault'
```

---

### Module 2: File Utilities

**File:** `src/plorp/utils/files.py`

```python
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
    return path.read_text(encoding='utf-8')


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
    path.write_text(content, encoding='utf-8')


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
```

**Tests to write for files.py:**

```python
# ABOUTME: Tests for file utilities - validates reading, writing, and directory operations
# ABOUTME: Uses pytest's tmp_path fixture to create isolated test environments
"""Tests for file utilities."""
import pytest
from pathlib import Path
from plorp.utils.files import read_file, write_file, ensure_directory


def test_write_and_read_file(tmp_path):
    """Test writing and reading a file."""
    test_file = tmp_path / 'test.txt'
    content = 'Hello, plorp!'

    write_file(test_file, content)

    assert test_file.exists()
    assert read_file(test_file) == content


def test_write_file_overwrites(tmp_path):
    """Test that write_file overwrites existing content."""
    test_file = tmp_path / 'test.txt'

    write_file(test_file, 'First content')
    write_file(test_file, 'Second content')

    assert read_file(test_file) == 'Second content'


def test_read_file_not_found(tmp_path):
    """Test read_file raises error for non-existent file."""
    nonexistent = tmp_path / 'nope.txt'

    with pytest.raises(FileNotFoundError):
        read_file(nonexistent)


def test_ensure_directory_creates(tmp_path):
    """Test ensure_directory creates directory."""
    new_dir = tmp_path / 'vault' / 'daily'

    ensure_directory(new_dir)

    assert new_dir.exists()
    assert new_dir.is_dir()


def test_ensure_directory_exists(tmp_path):
    """Test ensure_directory works if directory already exists."""
    existing_dir = tmp_path / 'vault'
    existing_dir.mkdir()

    # Should not raise error
    ensure_directory(existing_dir)

    assert existing_dir.exists()


def test_write_file_unicode(tmp_path):
    """Test writing and reading unicode content."""
    test_file = tmp_path / 'unicode.txt'
    content = '✓ Task completed! 日本語 Émojis: 🚀'

    write_file(test_file, content)

    assert read_file(test_file) == content
```

---

### Module 3: Date Utilities

**File:** `src/plorp/utils/dates.py`

```python
# ABOUTME: Date formatting utilities for consistent date handling across plorp
# ABOUTME: Converts between Python dates and TaskWarrior/Obsidian date formats
"""
Date utilities.

Helper functions for date formatting and conversion.
"""
from datetime import date, datetime
from typing import Optional


def format_date_iso(d: date) -> str:
    """
    Format date as ISO string (YYYY-MM-DD).

    Args:
        d: Date to format

    Returns:
        ISO formatted date string

    Example:
        >>> from datetime import date
        >>> format_date_iso(date(2025, 10, 6))
        '2025-10-06'
    """
    return d.strftime('%Y-%m-%d')


def format_date_long(d: date) -> str:
    """
    Format date as long string (Month DD, YYYY).

    Args:
        d: Date to format

    Returns:
        Long formatted date string

    Example:
        >>> format_date_long(date(2025, 10, 6))
        'October 06, 2025'
    """
    return d.strftime('%B %d, %Y')


def parse_taskwarrior_date(tw_date: str) -> Optional[date]:
    """
    Parse TaskWarrior date format (YYYYMMDDTHHMMSSZ) to Python date.

    Args:
        tw_date: TaskWarrior date string

    Returns:
        Python date object, or None if parsing fails

    Example:
        >>> parse_taskwarrior_date('20251006T120000Z')
        date(2025, 10, 6)
    """
    try:
        dt = datetime.strptime(tw_date, '%Y%m%dT%H%M%SZ')
        return dt.date()
    except (ValueError, AttributeError):
        return None


def format_taskwarrior_date_short(tw_date: str) -> str:
    """
    Format TaskWarrior date to short string (YYYY-MM-DD).

    Args:
        tw_date: TaskWarrior date string

    Returns:
        Short formatted date, or original string if parsing fails

    Example:
        >>> format_taskwarrior_date_short('20251006T120000Z')
        '2025-10-06'
    """
    parsed = parse_taskwarrior_date(tw_date)
    if parsed:
        return format_date_iso(parsed)
    return tw_date
```

**Tests to write for dates.py:**

```python
# ABOUTME: Tests for date utilities - validates date formatting and parsing
# ABOUTME: Tests conversion between Python dates and TaskWarrior date formats
"""Tests for date utilities."""
import pytest
from datetime import date
from plorp.utils.dates import (
    format_date_iso,
    format_date_long,
    parse_taskwarrior_date,
    format_taskwarrior_date_short
)


def test_format_date_iso():
    """Test ISO date formatting."""
    d = date(2025, 10, 6)
    assert format_date_iso(d) == '2025-10-06'


def test_format_date_long():
    """Test long date formatting."""
    d = date(2025, 10, 6)
    result = format_date_long(d)
    assert result == 'October 06, 2025'


def test_parse_taskwarrior_date_valid():
    """Test parsing valid TaskWarrior date."""
    tw_date = '20251006T120000Z'
    result = parse_taskwarrior_date(tw_date)
    assert result == date(2025, 10, 6)


def test_parse_taskwarrior_date_invalid():
    """Test parsing invalid TaskWarrior date."""
    assert parse_taskwarrior_date('invalid') is None
    assert parse_taskwarrior_date('') is None
    assert parse_taskwarrior_date('2025-10-06') is None


def test_format_taskwarrior_date_short_valid():
    """Test formatting valid TaskWarrior date."""
    tw_date = '20251006T120000Z'
    result = format_taskwarrior_date_short(tw_date)
    assert result == '2025-10-06'


def test_format_taskwarrior_date_short_invalid():
    """Test formatting invalid TaskWarrior date returns original."""
    invalid = 'not-a-date'
    result = format_taskwarrior_date_short(invalid)
    assert result == invalid
```

---

### Module 4: Daily Workflow (Start Only)

**File:** `src/plorp/workflows/daily.py`

**Replace the stub with:**

```python
# ABOUTME: Daily workflow implementation - generates daily notes from TaskWarrior tasks
# ABOUTME: Provides start() to create daily note and review() for end-of-day processing (Sprint 3)
"""
Daily workflow: start and review.

Status:
- start() - Implemented in Sprint 2
- review() - To be implemented in Sprint 3
"""
from pathlib import Path
from datetime import date
from typing import List, Dict, Any

from plorp.integrations.taskwarrior import (
    get_overdue_tasks,
    get_due_today,
    get_recurring_today,
)
from plorp.utils.files import write_file, ensure_directory
from plorp.utils.dates import format_date_iso, format_date_long, format_taskwarrior_date_short


def start(config: Dict[str, Any]) -> Path:
    """
    Generate daily note for today.

    Queries TaskWarrior for overdue, due today, and recurring tasks,
    then generates a formatted markdown daily note in the Obsidian vault.

    Args:
        config: Configuration dictionary with 'vault_path'

    Returns:
        Path to created daily note file

    Raises:
        FileNotFoundError: If vault_path doesn't exist
        IOError: If file can't be written

    Example:
        >>> config = load_config()
        >>> note_path = start(config)
        >>> print(f"Daily note created: {note_path}")
    """
    today = date.today()

    # Query TaskWarrior
    overdue = get_overdue_tasks()
    due_today = get_due_today()
    recurring = get_recurring_today()

    # Generate markdown content
    note_content = generate_daily_note_content(
        today, overdue, due_today, recurring
    )

    # Determine file path
    vault_path = Path(config['vault_path'])
    daily_dir = vault_path / 'daily'
    ensure_directory(daily_dir)

    daily_path = daily_dir / f'{format_date_iso(today)}.md'

    # Write file
    write_file(daily_path, note_content)

    # Print summary
    print(f"\n✅ Daily note generated")
    print(f"📄 {daily_path}")
    print(f"\nSummary:")
    print(f"  {len(overdue)} overdue tasks")
    print(f"  {len(due_today)} due today")
    print(f"  {len(recurring)} recurring tasks")
    print()

    return daily_path


def generate_daily_note_content(
    today: date,
    overdue: List[Dict],
    due_today: List[Dict],
    recurring: List[Dict]
) -> str:
    """
    Generate markdown content for daily note.

    Args:
        today: Date for the note
        overdue: List of overdue tasks
        due_today: List of tasks due today
        recurring: List of recurring tasks

    Returns:
        Complete markdown content with YAML front matter

    Example:
        >>> content = generate_daily_note_content(date.today(), [], [], [])
        >>> assert '---' in content  # Has front matter
        >>> assert '# Daily Note' in content
    """
    content = f"""---
date: {format_date_iso(today)}
type: daily
plorp_version: 1.0
---

# Daily Note - {format_date_long(today)}

"""

    if overdue:
        content += f"## Overdue ({len(overdue)})\n\n"
        for task in overdue:
            content += format_task_checkbox(task)
        content += "\n"

    if due_today:
        content += f"## Due Today ({len(due_today)})\n\n"
        for task in due_today:
            content += format_task_checkbox(task)
        content += "\n"

    if recurring:
        content += f"## Recurring\n\n"
        for task in recurring:
            content += format_task_checkbox(task)
        content += "\n"

    content += "---\n\n## Notes\n\n[Your thoughts, observations, decisions during the day]\n\n"
    content += "---\n\n## Review Section\n\n<!-- Auto-populated by `plorp review` -->\n"

    return content


def format_task_checkbox(task: Dict) -> str:
    """
    Format task as markdown checkbox with metadata.

    Args:
        task: Task dictionary from TaskWarrior

    Returns:
        Formatted checkbox line

    Example:
        >>> task = {'description': 'Buy milk', 'uuid': 'abc-123', 'project': 'home'}
        >>> checkbox = format_task_checkbox(task)
        >>> assert '- [ ] Buy milk' in checkbox
        >>> assert 'uuid: abc-123' in checkbox
    """
    desc = task['description']
    uuid = task['uuid']

    # Build metadata string
    meta = []

    if 'due' in task:
        due_str = format_taskwarrior_date_short(task['due'])
        meta.append(f"due: {due_str}")

    if 'project' in task:
        meta.append(f"project: {task['project']}")

    if 'priority' in task:
        meta.append(f"priority: {task['priority']}")

    if 'recur' in task:
        meta.append(f"recurring: {task['recur']}")

    meta.append(f"uuid: {uuid}")

    meta_str = ', '.join(meta)

    return f"- [ ] {desc} ({meta_str})\n"


def review(config: Dict[str, Any]) -> None:
    """
    Interactive end-of-day review.

    Status: STUB - To be implemented in Sprint 3

    Args:
        config: Configuration dictionary
    """
    print("⚠️  'review' functionality not yet implemented (coming in Sprint 3)")
```

**Tests to write for daily.py:**

```python
# ABOUTME: Tests for daily workflow - validates daily note generation and task formatting
# ABOUTME: Mocks TaskWarrior integration and uses fixtures to test markdown generation
"""Tests for daily workflow."""
import pytest
from pathlib import Path
from datetime import date
from unittest.mock import patch, MagicMock

from plorp.workflows.daily import (
    start,
    generate_daily_note_content,
    format_task_checkbox,
    review
)


@pytest.fixture
def mock_config(tmp_path):
    """Fixture for test configuration."""
    vault = tmp_path / 'vault'
    vault.mkdir()
    return {
        'vault_path': str(vault),
        'taskwarrior_data': '~/.task',
    }


@pytest.fixture
def sample_tasks(sample_taskwarrior_export):
    """Sample tasks from fixture."""
    return sample_taskwarrior_export


def test_format_task_checkbox_minimal():
    """Test formatting task with minimal metadata."""
    task = {
        'description': 'Simple task',
        'uuid': 'abc-123'
    }

    result = format_task_checkbox(task)

    assert '- [ ] Simple task' in result
    assert 'uuid: abc-123' in result


def test_format_task_checkbox_full():
    """Test formatting task with all metadata."""
    task = {
        'description': 'Complete task',
        'uuid': 'abc-123',
        'project': 'plorp',
        'due': '20251006T120000Z',
        'priority': 'H',
        'recur': 'daily'
    }

    result = format_task_checkbox(task)

    assert '- [ ] Complete task' in result
    assert 'uuid: abc-123' in result
    assert 'project: plorp' in result
    assert 'due: 2025-10-06' in result
    assert 'priority: H' in result
    assert 'recurring: daily' in result


def test_generate_daily_note_content_empty():
    """Test generating note with no tasks."""
    today = date(2025, 10, 6)

    content = generate_daily_note_content(today, [], [], [])

    assert '---' in content  # Has front matter
    assert 'date: 2025-10-06' in content
    assert 'type: daily' in content
    assert '# Daily Note - October 06, 2025' in content
    assert '## Notes' in content
    assert '## Review Section' in content


def test_generate_daily_note_content_with_tasks(sample_tasks):
    """Test generating note with tasks."""
    today = date(2025, 10, 6)
    overdue = [sample_tasks[1]]  # Call dentist
    due_today = [sample_tasks[0]]  # Buy groceries
    recurring = [sample_tasks[2]]  # Morning meditation

    content = generate_daily_note_content(today, overdue, due_today, recurring)

    assert '## Overdue (1)' in content
    assert 'Call dentist' in content

    assert '## Due Today (1)' in content
    assert 'Buy groceries' in content

    assert '## Recurring' in content
    assert 'Morning meditation' in content


@patch('plorp.workflows.daily.get_overdue_tasks')
@patch('plorp.workflows.daily.get_due_today')
@patch('plorp.workflows.daily.get_recurring_today')
def test_start_creates_note(mock_recurring, mock_due, mock_overdue, mock_config, sample_tasks):
    """Test start() creates daily note file."""
    # Mock TaskWarrior responses
    mock_overdue.return_value = [sample_tasks[1]]
    mock_due.return_value = [sample_tasks[0]]
    mock_recurring.return_value = [sample_tasks[2]]

    # Capture stdout
    import io
    import sys
    captured_output = io.StringIO()
    sys.stdout = captured_output

    note_path = start(mock_config)

    # Restore stdout
    sys.stdout = sys.__stdout__

    # Verify file created
    assert note_path.exists()
    assert note_path.name == f"{date.today().strftime('%Y-%m-%d')}.md"

    # Verify content
    content = note_path.read_text()
    assert 'Call dentist' in content
    assert 'Buy groceries' in content
    assert 'Morning meditation' in content

    # Verify output
    output = captured_output.getvalue()
    assert '✅ Daily note generated' in output
    assert '1 overdue tasks' in output
    assert '1 due today' in output
    assert '1 recurring tasks' in output


@patch('plorp.workflows.daily.get_overdue_tasks')
@patch('plorp.workflows.daily.get_due_today')
@patch('plorp.workflows.daily.get_recurring_today')
def test_start_creates_directory(mock_recurring, mock_due, mock_overdue, mock_config):
    """Test start() creates daily directory if not exists."""
    mock_overdue.return_value = []
    mock_due.return_value = []
    mock_recurring.return_value = []

    daily_dir = Path(mock_config['vault_path']) / 'daily'
    assert not daily_dir.exists()

    start(mock_config)

    assert daily_dir.exists()


def test_review_stub(mock_config, capsys):
    """Test review() shows not implemented message."""
    review(mock_config)

    captured = capsys.readouterr()
    assert 'not yet implemented' in captured.out
    assert 'Sprint 3' in captured.out
```

---

### Module 5: CLI Update

**File:** `src/plorp/cli.py`

**Update the `start` command:**

```python
# Find and replace the start command stub with:

@cli.command()
@click.pass_context
def start(ctx):
    """Generate daily note for today."""
    config = load_config()

    try:
        from plorp.workflows.daily import start as daily_start
        note_path = daily_start(config)
        # Output already printed by daily_start()
    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        click.echo(f"💡 Make sure vault directory exists: {config.get('vault_path')}", err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(f"❌ Error generating daily note: {e}", err=True)
        import traceback
        traceback.print_exc()
        ctx.exit(1)
```

**Add import at top of file:**

```python
from plorp.config import load_config
```

**Tests to update in test_cli.py:**

```python
# Update the existing test_start_stub test:

@patch('plorp.cli.load_config')
@patch('plorp.workflows.daily.start')
def test_start_command(mock_daily_start, mock_load_config, tmp_path):
    """Test start command calls daily workflow."""
    from click.testing import CliRunner
    from plorp.cli import cli

    mock_load_config.return_value = {'vault_path': str(tmp_path)}
    mock_daily_start.return_value = tmp_path / 'daily' / '2025-10-06.md'

    runner = CliRunner()
    result = runner.invoke(cli, ['start'])

    assert result.exit_code == 0
    mock_daily_start.assert_called_once()


@patch('plorp.cli.load_config')
def test_start_command_error(mock_load_config):
    """Test start command handles errors."""
    from click.testing import CliRunner
    from plorp.cli import cli

    mock_load_config.return_value = {'vault_path': '/nonexistent/path'}

    runner = CliRunner()
    result = runner.invoke(cli, ['start'])

    # Should exit with error
    assert result.exit_code != 0
    assert '❌' in result.output or 'Error' in result.output
```

---

## Test Requirements

### Test Coverage Goals

- **config.py:** >95% coverage
- **utils/files.py:** >95% coverage
- **utils/dates.py:** 100% coverage (pure functions)
- **workflows/daily.py:** >90% coverage
- **Overall Sprint 2 code:** >90% coverage

### Required Test Files

1. **tests/test_config.py** - Configuration tests
2. **tests/test_utils/test_files.py** - File utility tests
3. **tests/test_utils/test_dates.py** - Date utility tests
4. **tests/test_workflows/test_daily.py** - Daily workflow tests
5. **tests/test_cli.py** - CLI tests (update existing)

### Test Execution

```bash
# Run all Sprint 2 tests
pytest tests/test_config.py tests/test_utils/ tests/test_workflows/test_daily.py -v

# Run with coverage
pytest tests/test_config.py tests/test_utils/ tests/test_workflows/test_daily.py \
    --cov=src/plorp/config \
    --cov=src/plorp/utils \
    --cov=src/plorp/workflows/daily \
    --cov-report=term-missing

# Run integration test (full workflow)
pytest tests/test_workflows/test_daily.py::test_start_creates_note -v
```

---

## Success Criteria

### Installation and Import Check

```bash
cd /Users/jsd/Documents/plorp
source venv/bin/activate

# 1. All modules can be imported
python3 -c "
from plorp.config import load_config, save_config
from plorp.utils.files import read_file, write_file, ensure_directory
from plorp.utils.dates import format_date_iso, format_date_long
from plorp.workflows.daily import start, generate_daily_note_content
print('✓ All imports successful')
"
```

### Test Check

```bash
# 2. All tests pass
pytest tests/test_config.py \
       tests/test_utils/ \
       tests/test_workflows/test_daily.py \
       tests/test_cli.py::test_start_command \
       -v
# → All tests pass (30+ tests)

# 3. Coverage exceeds 90%
pytest tests/test_config.py tests/test_utils/ tests/test_workflows/test_daily.py \
    --cov=src/plorp/config \
    --cov=src/plorp/utils \
    --cov=src/plorp/workflows/daily \
    --cov-report=term
# → Coverage >90%
```

### CLI Check

```bash
# 4. CLI command works
plorp --help
# → Shows updated help with start command

plorp start --help
# → Shows start command help

# 5. Start command runs (requires config)
# First, set up minimal vault
mkdir -p ~/vault/daily

# Run start command
plorp start
# → Creates daily note
# → Prints summary
# → Exit code 0

# 6. Verify daily note created
ls ~/vault/daily/
# → Shows YYYY-MM-DD.md file

cat ~/vault/daily/$(date +%Y-%m-%d).md
# → Contains YAML front matter
# → Contains sections: Overdue, Due Today, Recurring
# → Contains task checkboxes with UUIDs
```

### Code Quality Check

```bash
# 7. Black formatting
black --check src/plorp/config.py \
              src/plorp/utils/ \
              src/plorp/workflows/daily.py \
              tests/test_config.py \
              tests/test_utils/ \
              tests/test_workflows/test_daily.py
# → All files properly formatted

# 8. ABOUTME comments present
head -2 src/plorp/config.py
head -2 src/plorp/utils/files.py
head -2 src/plorp/utils/dates.py
head -2 src/plorp/workflows/daily.py
# → Each shows ABOUTME comments
```

---

## Completion Report Template

**Instructions:** Fill this out when Sprint 2 is complete.

### Implementation Summary

**What was implemented:**
- [x] config.py - Complete with load/save/defaults and vault validation
- [x] utils/files.py - Read/write/ensure_directory
- [x] utils/dates.py - Date formatting and parsing
- [x] workflows/daily.py - start() and generate_daily_note_content()
- [x] cli.py - Updated start command with error handling
- [x] All files have ABOUTME comments
- [x] All functions have type hints and docstrings
- [x] Comprehensive test suite (36 tests for Sprint 2)
- [x] All tests pass (75 total including Sprint 1)
- [x] 100% test coverage on all Sprint 2 modules
- [x] CLI command works with proper error handling

**Lines of code added:**
- Production code: 463 lines (config.py: 109, files.py: 65, dates.py: 86, daily.py: 209, cli.py updates: ~25)
- Test code: 566 lines (test_config.py: 156, test_files.py: 107, test_dates.py: 90, test_daily.py: 194, test_cli.py updates: ~20)
- Total: 1,029 lines

**Test coverage achieved:** 100% on all Sprint 2 modules (config, utils, workflows/daily), 95% overall project

**Number of tests written:** 36 new tests for Sprint 2 (75 total with Sprint 1)

### Deviations from Spec

**Any changes from the specification?**

Minor deviations based on Q&A:
1. **Vault validation in load_config()**: Per Q1 answer, load_config() validates and auto-creates vault directory if missing, warns if it's a file.
2. **Daily note overwrite protection**: Per Q3 answer, start() raises FileExistsError if daily note already exists, protecting user's work.
3. **Warning messages for no tasks**: Per Q5 answer, when TaskWarrior returns empty lists, warns to stderr and includes "_No tasks found_" messages in markdown.
4. **YAML type validation**: Per Q6 answer, added isinstance() check to ensure yaml.safe_load() returns dict.
5. **Test organization**: Per Q7 answer, used nested test structure (tests/test_utils/, tests/test_workflows/).
6. **Stdout capture**: Per Q4 answer, chose capsys fixture over io.StringIO for cleaner test code.
7. **Date mocking**: Per Q8 answer, kept date.today() without mocking (tests remain date-dependent but assertions still pass).

### Verification Commands

**Commands run to verify Sprint 2 is complete:**

```bash
cd /Users/jsd/Documents/plorp
source venv/bin/activate

# Run all tests
pytest tests/test_config.py tests/test_utils/ tests/test_workflows/test_daily.py -v

# Coverage check
pytest tests/test_config.py tests/test_utils/ tests/test_workflows/test_daily.py \
    --cov=src/plorp/config --cov=src/plorp/utils --cov=src/plorp/workflows/daily \
    --cov-report=term

# CLI test
mkdir -p ~/vault/daily
plorp start
ls ~/vault/daily/
cat ~/vault/daily/$(date +%Y-%m-%d).md
```

**Output summary:**
- All 36 Sprint 2 tests pass
- 75 total tests pass (including Sprint 1)
- 100% coverage on config.py, utils/files.py, utils/dates.py, workflows/daily.py
- 95% overall project coverage
- CLI tests confirm start command properly wires to daily workflow with error handling

### Known Issues

**Any known limitations or issues:**

None. All functionality works as specified with comprehensive error handling and 100% test coverage on Sprint 2 modules.

### Handoff Notes for Sprint 3

**What Sprint 3 needs to know:**

- Daily note generation is complete and working
- File utilities available for reading daily notes
- Date utilities available for parsing
- Daily notes have standard format with task checkboxes
- Each checkbox includes UUID for task identification
- Config system is working

**Functions Sprint 3 will use:**
- `read_file()` - To read daily notes
- `write_file()` - To update daily notes with review section
- Daily note format:
  ```markdown
  - [ ] Task description (due: YYYY-MM-DD, project: xxx, priority: X, uuid: xxx-xxx)
  ```

**Files Sprint 3 will modify:**
- `workflows/daily.py` - Add review() function
- Will need to parse markdown checkboxes (Sprint 3 will implement parser)

**Files Sprint 3 should NOT modify:**
- `config.py` - Complete
- `utils/files.py` - Complete
- `utils/dates.py` - Complete
- `start()` function - Complete

### Questions for PM/Architect

[Add any questions or clarifications needed]

### Recommendations

**Suggestions for future sprints:**

[Any recommendations based on what you learned in Sprint 2]

### Sign-off

- **Implemented by:** [Claude Code Engineer Instance]
- **Date completed:** [Date]
- **Implementation time:** [Actual time taken]
- **Ready for Sprint 3:** [Yes/No]

---

## Q&A Section

### Questions from Engineering

**Format for questions:**

```
Q: [Your question here]
Status: PENDING
```

Add your questions here if anything is unclear. The PM/Architect will answer before you proceed.

---

**Q1: Config validation and error handling**
```
Q: Should load_config() validate that vault_path exists? Should we warn the user
   or create the vault directory automatically? What if vault_path points to a
   file instead of a directory?

Context: The spec shows load_config() can be called before vault exists, but
start() will fail if vault_path doesn't exist. Should validation happen at
config load time or workflow execution time?

Status: PENDING
```

**Q2: Directory structure initialization**
```
Q: The test __init__.py files for new test directories - should we create:
   - tests/test_utils/__init__.py (empty)
   - tests/test_workflows/__init__.py (empty)

   Following Sprint 1 pattern where we created tests/test_integrations/__init__.py?

Status: PENDING
```

**Q3: Daily note overwriting behavior**
```
Q: If a daily note already exists for today, should start() command:
   a) Overwrite the existing file (current behavior based on write_file)
   b) Append to existing file
   c) Refuse to overwrite and show error
   d) Back up existing file and create new one

Context: Users might run `plorp start` multiple times per day if tasks change.

Status: PENDING
```

**Q4: stdout capture in tests**
```
Q: The test_start_creates_note() uses io.StringIO to capture stdout, but this
   pattern is fragile. Should we instead:
   a) Use capsys fixture (pytest built-in)
   b) Remove the print output verification entirely
   c) Keep the io.StringIO pattern as specified

Status: PENDING
```

**Q5: Error handling for missing TaskWarrior**
```
Q: If TaskWarrior is not installed or returns errors, should start() command:
   a) Print to stderr and exit with code 1
   b) Create empty daily note with warning message
   c) Create daily note with just the template (no tasks)
   d) Fail completely and not create any file

Context: Sprint 1 functions print to stderr and return empty lists on error,
so start() will create a note with no tasks. Should we detect this and warn?

Status: PENDING
```

**Q6: Type hints for yaml.safe_load**
```
Q: yaml.safe_load() can return None, dict, list, etc. The spec shows:
   `user_config = yaml.safe_load(f) or {}`

   Is this the correct pattern? Should we add additional validation to ensure
   the loaded YAML is actually a dict and not a list/string/other type?

Status: PENDING
```

**Q7: Test directory structure - where to put test files**
```
Q: Should test files go in:
   tests/test_config.py (top level, like Sprint 0)
   OR
   tests/test_core/test_config.py (in subdirectory)

   Same question for test_utils/ and test_workflows/ - flat structure or nested?

   Looking at Sprint 0, we have tests/test_cli.py (flat), but Sprint 1 added
   tests/test_integrations/test_taskwarrior.py (nested). What's the pattern?

Status: PENDING
```

**Q8: Date.today() mocking in tests**
```
Q: Multiple tests use date.today() which will change each day. Should we:
   a) Mock date.today() in tests to return fixed date (e.g., 2025-10-06)
   b) Use parametrized dates and accept tests are date-dependent
   c) Accept that test output changes daily but assertions still pass

   Example: test_start_creates_note checks filename includes today's date.

Status: PENDING
```

---

### Answers from PM/Architect

**Q1: Config validation and error handling**
```
Q: Should load_config() validate that vault_path exists?
A: Yes. Validate vault_path and create the directory if it doesn't exist.

   Implementation:
   1. Load config (or create default)
   2. Validate that vault_path is set
   3. Check if vault_path exists:
      - If it exists but is a file (not directory): print warning to stderr
      - If it doesn't exist: create it with mkdir(parents=True, exist_ok=True)
        and print info message like "Created vault directory: /path/to/vault"

   This validation should happen in load_config() so the vault is ready before
   any workflow commands run.

Status: RESOLVED
```

**Q2: Directory structure initialization**
```
Q: Should we create __init__.py files in test subdirectories?
A: Yes. Create:
   - tests/test_utils/__init__.py (empty)
   - tests/test_workflows/__init__.py (empty)

   Follow the same pattern as Sprint 1 (tests/test_integrations/__init__.py).

Status: RESOLVED
```

**Q3: Daily note overwriting behavior**
```
Q: If daily note already exists, what should start() do?
A: Refuse and show error. Do not overwrite existing daily notes.

   Implementation:
   1. Check if daily note file already exists
   2. If exists: print error message to stderr and exit
      Example: "❌ Daily note already exists: /path/to/2025-10-06.md"
               "💡 Use a text editor to modify it, or delete it to regenerate"
   3. If not exists: create new file

   This protects user work if they've already started taking notes.

Status: RESOLVED
```

**Q4: stdout capture in tests**
```
Q: Which pattern for capturing stdout in tests?
A: Engineering choice - use whichever you prefer:
   - capsys fixture is more idiomatic pytest
   - io.StringIO works fine too

   Either approach is acceptable. Choose based on readability.

Status: RESOLVED
```

**Q5: Error handling for missing TaskWarrior**
```
Q: What if TaskWarrior is not installed or returns errors?
A: Create daily note with warning message in both stderr and the file.

   Implementation:
   1. If all three task queries return empty lists (could indicate TW error):
      - Print warning to stderr: "⚠️  Warning: No tasks found. Is TaskWarrior installed?"
      - Include warning in the markdown file under each section:
        "## Overdue (0)\n\n_No tasks found_\n\n"
   2. Still create the daily note file (users can add manual notes)
   3. Don't fail - just warn and continue

   This allows plorp to work even if TaskWarrior has issues.

Status: RESOLVED
```

**Q6: Type hints for yaml.safe_load**
```
Q: Should we validate yaml.safe_load() returns a dict?
A: Engineering decision: Add type validation for robustness.

   Recommended implementation:
   ```python
   user_config = yaml.safe_load(f)
   if not isinstance(user_config, dict):
       user_config = {}  # Handle None, list, string, etc.
   ```

   This is safer than just `or {}` and handles edge cases like YAML files
   containing lists or scalars.

Status: RESOLVED
```

**Q7: Test directory structure**
```
Q: Flat vs nested test structure?
A: Engineering decision: Use **nested structure** for organization.

   Convention for all sprints:
   - tests/test_<module_name>/test_<file>.py for modules with multiple files
   - tests/test_<file>.py for single-file modules

   Sprint 2 structure:
   - tests/test_config.py (single file, top-level)
   - tests/test_utils/test_files.py (module with multiple files)
   - tests/test_utils/test_dates.py
   - tests/test_workflows/test_daily.py (module with multiple files)
   - tests/test_integrations/test_taskwarrior.py (from Sprint 1)

   **Update for all future sprints:** Follow this nested convention where
   source code has subdirectories (utils/, workflows/, integrations/).

Status: RESOLVED
```

**Q8: Date.today() mocking in tests**
```
Q: Should we mock date.today() in tests?
A: No. Keep using date.today() - accept that tests are date-dependent.

   Rationale: The added complexity of mocking dates isn't worth it for these
   tests. The assertions will still pass regardless of the date. If specific
   date testing is needed, use parametrized dates for those specific tests.

Status: RESOLVED
```

---

**Document Version:** 1.0
**Last Updated:** October 6, 2025
**Status:** Ready for Implementation
**Next Sprint:** SPRINT-3 (Review Workflow)
