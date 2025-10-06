# plorp Architecture

**Date:** October 6, 2025
**Purpose:** Technical implementation details for plorp

---

## Table of Contents

1. [Technology Stack](#technology-stack)
2. [Project Structure](#project-structure)
3. [Core Modules](#core-modules)
4. [Data Flow](#data-flow)
5. [TaskWarrior Integration](#taskwarrior-integration)
6. [Obsidian Integration](#obsidian-integration)
7. [Configuration Management](#configuration-management)
8. [Error Handling](#error-handling)
9. [Testing Strategy](#testing-strategy)
10. [Dependencies](#dependencies)

---

## Technology Stack

### Runtime

- **Python 3.8+** - Core language
- **TaskWarrior 3.4.1** - Task management (SQLite via TaskChampion)
- **Obsidian** - Note-taking (markdown files)

### Python Libraries

**Core:**
- `subprocess` - Call TaskWarrior CLI
- `json` - Parse TaskWarrior export
- `pathlib` - File path handling
- `datetime` - Date/time operations
- `re` - Regex for markdown parsing

**Optional:**
- `yaml` (PyYAML) - Parse Obsidian front matter
- `sqlite3` - Direct TaskWarrior DB reads (advanced)
- `click` - CLI framework (or argparse)
- `rich` - Terminal formatting (optional)

### External Tools

- **TaskWarrior** (`task`) - Must be installed and configured
- **Text editor** - For manual note editing (vim/vscode/obsidian)

---

## Project Structure

```
plorp/
├── README.md                  # Quick start guide
├── plorp_SPEC.md         # Specification (this lives in docs)
├── plorp_ARCHITECTURE.md  # Architecture (this file)
│
├── pyproject.toml            # Python project config
├── requirements.txt          # Python dependencies
│
├── src/
│   └── plorp/
│       ├── __init__.py
│       ├── __main__.py       # Entry point: python -m plorp
│       │
│       ├── cli.py            # CLI command routing
│       ├── config.py         # Configuration management
│       │
│       ├── workflows/        # Core workflow implementations
│       │   ├── __init__.py
│       │   ├── daily.py      # Daily start/review
│       │   ├── inbox.py      # Inbox processing
│       │   └── notes.py      # Note creation/linking
│       │
│       ├── integrations/     # External tool integrations
│       │   ├── __init__.py
│       │   ├── taskwarrior.py    # TaskWarrior CLI wrapper
│       │   └── obsidian.py       # Obsidian file operations
│       │
│       ├── parsers/          # Data parsing
│       │   ├── __init__.py
│       │   ├── markdown.py   # Markdown parsing
│       │   └── frontmatter.py    # YAML front matter
│       │
│       └── utils/            # Utilities
│           ├── __init__.py
│           ├── dates.py      # Date formatting
│           ├── prompts.py    # CLI prompts
│           └── files.py      # File I/O helpers
│
├── scripts/                  # External scripts
│   ├── email_to_inbox.py     # Email capture (cron)
│   └── install.sh            # Installation script
│
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── test_workflows/
│   ├── test_integrations/
│   └── test_parsers/
│
├── config/                   # Configuration templates
│   └── plorp.yaml.template
│
└── docs/                     # Documentation
    ├── GETTING_STARTED.md
    ├── COMMANDS.md
    └── WORKFLOWS.md
```

---

## Core Modules

### 1. `cli.py` - Command Line Interface

**Purpose:** Route commands to appropriate workflows

```python
"""
Main CLI entry point.
"""
import click
from plorp.workflows import daily, inbox, notes
from plorp.config import load_config

@click.group()
@click.pass_context
def cli(ctx):
    """plorp - Workflow automation for TaskWarrior + Obsidian"""
    ctx.obj = load_config()

@cli.command()
@click.pass_obj
def start(config):
    """Generate daily note for today"""
    daily.start(config)

@cli.command()
@click.pass_obj
def review(config):
    """Interactive end-of-day review"""
    daily.review(config)

@cli.command()
@click.argument('subcommand', default='process')
@click.pass_obj
def inbox(config, subcommand):
    """Process inbox items"""
    if subcommand == 'process':
        inbox.process(config)
    else:
        click.echo(f"Unknown inbox subcommand: {subcommand}")

@cli.command()
@click.argument('description', nargs=-1, required=True)
@click.option('--project', help='Project name')
@click.option('--due', help='Due date')
@click.option('--priority', help='Priority (H/M/L)')
@click.option('--tags', help='Comma-separated tags')
@click.pass_obj
def task(config, description, project, due, priority, tags):
    """Create task (wrapper for TaskWarrior)"""
    from plorp.integrations.taskwarrior import create_task

    desc = ' '.join(description)
    task_uuid = create_task(
        description=desc,
        project=project,
        due=due,
        priority=priority,
        tags=tags.split(',') if tags else None
    )

    click.echo(f"✅ Created task (uuid: {task_uuid})")

@cli.command()
@click.argument('title')
@click.option('--task', help='Link to task UUID')
@click.pass_obj
def note(config, title, task):
    """Create note with optional task linking"""
    notes.create_note(config, title, task_uuid=task)

if __name__ == '__main__':
    cli()
```

---

### 2. `workflows/daily.py` - Daily Workflow

**Purpose:** Generate daily notes and end-of-day review

```python
"""
Daily workflow: start and review
"""
from pathlib import Path
from datetime import date
from plorp.integrations.taskwarrior import (
    get_overdue_tasks,
    get_due_today,
    get_recurring_today,
    mark_done,
    defer_task
)
from plorp.utils.files import write_file, read_file
from plorp.utils.prompts import prompt_choice
from plorp.parsers.markdown import parse_daily_note_tasks

def start(config):
    """Generate daily note for today"""
    today = date.today()

    # Query TaskWarrior
    overdue = get_overdue_tasks()
    due_today = get_due_today()
    recurring = get_recurring_today()

    # Generate markdown
    note_content = generate_daily_note_content(
        today, overdue, due_today, recurring
    )

    # Write to file
    vault_path = Path(config['vault_path'])
    daily_path = vault_path / 'daily' / f'{today}.md'
    daily_path.parent.mkdir(parents=True, exist_ok=True)
    write_file(daily_path, note_content)

    # Print summary
    print(f"\n✅ Daily note generated")
    print(f"📄 {daily_path}")
    print(f"\nSummary:")
    print(f"  {len(overdue)} overdue tasks")
    print(f"  {len(due_today)} due today")
    print(f"  {len(recurring)} recurring tasks")
    print()

def generate_daily_note_content(today, overdue, due_today, recurring):
    """Generate markdown content for daily note"""
    content = f"""---
date: {today}
type: daily
plorp_version: 1.0
---

# Daily Note - {today.strftime('%B %d, %Y')}

"""

    if overdue:
        content += f"## Overdue ({len(overdue)})\n\n"
        for task in overdue:
            content += format_task_checkbox(task)

    if due_today:
        content += f"\n## Due Today ({len(due_today)})\n\n"
        for task in due_today:
            content += format_task_checkbox(task)

    if recurring:
        content += f"\n## Recurring\n\n"
        for task in recurring:
            content += format_task_checkbox(task)

    content += "\n---\n\n## Notes\n\n[Your thoughts]\n\n---\n\n## Review Section\n\n"

    return content

def format_task_checkbox(task):
    """Format task as markdown checkbox with metadata"""
    desc = task['description']
    uuid = task['uuid']

    # Build metadata string
    meta = []
    if 'due' in task:
        meta.append(f"due: {task['due']}")
    if 'project' in task:
        meta.append(f"project: {task['project']}")
    if 'priority' in task:
        meta.append(f"priority: {task['priority']}")

    meta_str = ', '.join(meta) if meta else ''

    return f"- [ ] {desc} ({meta_str}, uuid: {uuid})\n"

def review(config):
    """Interactive end-of-day review"""
    today = date.today()
    vault_path = Path(config['vault_path'])
    daily_path = vault_path / 'daily' / f'{today}.md'

    if not daily_path.exists():
        print(f"❌ No daily note for {today}")
        print(f"Run: plorp start")
        return

    # Parse uncompleted tasks
    uncompleted = parse_daily_note_tasks(daily_path)

    if not uncompleted:
        print("✅ All tasks completed!")
        return

    print(f"\n📋 {len(uncompleted)} tasks remaining from today\n")

    decisions = []

    for task_desc, task_uuid in uncompleted:
        # Get full task details
        from plorp.integrations.taskwarrior import get_task_info
        task = get_task_info(task_uuid)

        # Show task details
        print(f"\n{'='*60}")
        print(f"Task: {task['description']}")
        print(f"Project: {task.get('project', 'none')}")
        print(f"Due: {task.get('due', 'none')}")
        print(f"Priority: {task.get('priority', 'none')}")
        print(f"{'='*60}\n")

        # Prompt for action
        choice = prompt_choice([
            "Mark done",
            "Defer to tomorrow",
            "Defer to specific date",
            "Change priority",
            "Skip (keep as-is)",
            "Delete task",
            "Quit review"
        ])

        if choice == 0:  # Done
            mark_done(task_uuid)
            decisions.append(f"✅ {task_desc}")
            print("✅ Marked done\n")

        elif choice == 1:  # Tomorrow
            defer_task(task_uuid, 'tomorrow')
            decisions.append(f"📅 {task_desc} → tomorrow")
            print("📅 Deferred to tomorrow\n")

        elif choice == 2:  # Specific date
            new_due = input("New due date (YYYY-MM-DD or 'friday', etc): ")
            defer_task(task_uuid, new_due)
            decisions.append(f"📅 {task_desc} → {new_due}")
            print(f"📅 Deferred to {new_due}\n")

        elif choice == 3:  # Priority
            priority = input("Priority (H/M/L): ").upper()
            from plorp.integrations.taskwarrior import set_priority
            set_priority(task_uuid, priority)
            decisions.append(f"⚡ {task_desc} → priority {priority}")
            print(f"⚡ Priority set to {priority}\n")

        elif choice == 5:  # Delete
            confirm = input("Really delete? [y/n]: ")
            if confirm.lower() == 'y':
                from plorp.integrations.taskwarrior import delete_task
                delete_task(task_uuid)
                decisions.append(f"🗑️  {task_desc} (deleted)")
                print("🗑️  Deleted\n")

        elif choice == 6:  # Quit
            print("Review interrupted")
            break

        # choice == 4: skip

    # Append decisions to daily note
    if decisions:
        append_review_section(daily_path, decisions)

    print(f"\n{'='*60}")
    print("✅ Review complete")
    print(f"{'='*60}\n")

def append_review_section(daily_path, decisions):
    """Append review decisions to daily note"""
    from datetime import datetime

    content = read_file(daily_path)

    review_section = f"\n## Review Section\n\n"
    review_section += f"**Review completed:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

    for decision in decisions:
        review_section += f"- {decision}\n"

    # Replace existing review section
    import re
    if '## Review Section' in content:
        content = re.sub(
            r'## Review Section.*$',
            review_section,
            content,
            flags=re.DOTALL
        )
    else:
        content += review_section

    write_file(daily_path, content)
```

---

### 3. `integrations/taskwarrior.py` - TaskWarrior Integration

**Purpose:** Wrapper for TaskWarrior CLI

```python
"""
TaskWarrior CLI integration
"""
import subprocess
import json
from typing import List, Dict, Optional

def run_task_command(args: List[str], capture=True) -> subprocess.CompletedProcess:
    """Run task command and return result"""
    cmd = ['task'] + args

    if capture:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
    else:
        result = subprocess.run(cmd, check=False)

    return result

def get_tasks(filter_args: List[str]) -> List[Dict]:
    """Get tasks matching filter, return as list of dicts"""
    args = filter_args + ['export']
    result = run_task_command(args)

    if result.returncode != 0:
        return []

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

def get_overdue_tasks() -> List[Dict]:
    """Get all overdue tasks"""
    return get_tasks(['status:pending', 'due.before:today'])

def get_due_today() -> List[Dict]:
    """Get tasks due today"""
    return get_tasks(['status:pending', 'due:today'])

def get_recurring_today() -> List[Dict]:
    """Get recurring tasks due today"""
    return get_tasks(['status:pending', 'recur.any:', 'due:today'])

def get_task_info(uuid: str) -> Dict:
    """Get full info for a task"""
    tasks = get_tasks([uuid])
    return tasks[0] if tasks else {}

def create_task(description: str,
                project: Optional[str] = None,
                due: Optional[str] = None,
                priority: Optional[str] = None,
                tags: Optional[List[str]] = None) -> str:
    """Create a task, return UUID"""
    args = ['add', description]

    if project:
        args.append(f'project:{project}')
    if due:
        args.append(f'due:{due}')
    if priority:
        args.append(f'priority:{priority}')
    if tags:
        for tag in tags:
            args.append(f'+{tag}')

    result = run_task_command(args)

    # Parse UUID from output
    # TaskWarrior outputs: "Created task 123."
    # We need to get that task's UUID
    tasks = get_tasks(['status:pending'])
    if tasks:
        # Return most recently created task
        return tasks[-1]['uuid']

    return None

def mark_done(uuid: str):
    """Mark task as done"""
    run_task_command([uuid, 'done'], capture=False)

def defer_task(uuid: str, new_due: str):
    """Change task due date"""
    run_task_command([uuid, 'modify', f'due:{new_due}'], capture=False)

def set_priority(uuid: str, priority: str):
    """Set task priority"""
    run_task_command([uuid, 'modify', f'priority:{priority}'], capture=False)

def delete_task(uuid: str):
    """Delete task"""
    run_task_command([uuid, 'delete'], capture=False)

def add_annotation(uuid: str, text: str):
    """Add annotation to task"""
    run_task_command([uuid, 'annotate', text], capture=False)

def get_task_annotations(uuid: str) -> List[str]:
    """Get all annotations for a task"""
    result = run_task_command([uuid, 'info'])

    annotations = []
    for line in result.stdout.split('\n'):
        if 'Note:' in line:
            # Extract path after "Note:"
            parts = line.split('Note:', 1)
            if len(parts) == 2:
                annotations.append(parts[1].strip())

    return annotations
```

---

### 4. `parsers/markdown.py` - Markdown Parsing

**Purpose:** Parse markdown files for tasks, checkboxes, etc.

```python
"""
Markdown parsing utilities
"""
import re
from pathlib import Path
from typing import List, Tuple

def parse_daily_note_tasks(note_path: Path) -> List[Tuple[str, str]]:
    """
    Parse daily note for unchecked tasks.
    Returns list of (description, uuid) tuples.
    """
    content = note_path.read_text()

    # Pattern: - [ ] Description (metadata, uuid: abc-123)
    pattern = r'- \[ \] (.+?) \(.*?uuid: ([a-f0-9-]+)\)'
    matches = re.findall(pattern, content)

    return [(desc.strip(), uuid) for desc, uuid in matches]

def parse_frontmatter(content: str) -> dict:
    """Extract YAML front matter from markdown"""
    if not content.startswith('---'):
        return {}

    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}

    import yaml
    try:
        return yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return {}

def add_frontmatter_field(content: str, field: str, value) -> str:
    """Add or update field in front matter"""
    import yaml

    fm = parse_frontmatter(content)
    fm[field] = value

    # Rebuild content
    if content.startswith('---'):
        parts = content.split('---', 2)
        body = parts[2] if len(parts) > 2 else ''
    else:
        body = content

    new_fm = yaml.dump(fm, default_flow_style=False)
    return f"---\n{new_fm}---{body}"

def extract_task_uuids_from_note(note_path: Path) -> List[str]:
    """Extract all TaskWarrior UUIDs from note front matter"""
    content = note_path.read_text()
    fm = parse_frontmatter(content)

    return fm.get('tasks', [])
```

---

### 5. `config.py` - Configuration Management

**Purpose:** Load and manage plorp configuration

```python
"""
Configuration management
"""
import os
from pathlib import Path
import yaml

DEFAULT_CONFIG = {
    'vault_path': os.path.expanduser('~/vault'),
    'taskwarrior_data': os.path.expanduser('~/.task'),
    'inbox_email': None,
    'default_editor': os.environ.get('EDITOR', 'vim'),
}

def get_config_path() -> Path:
    """Get config file path"""
    # Try XDG_CONFIG_HOME first
    xdg_config = os.environ.get('XDG_CONFIG_HOME')
    if xdg_config:
        return Path(xdg_config) / 'plorp' / 'config.yaml'

    # Fallback to ~/.config
    return Path.home() / '.config' / 'plorp' / 'config.yaml'

def load_config() -> dict:
    """Load configuration from file or use defaults"""
    config_path = get_config_path()

    if not config_path.exists():
        # Create default config
        config_path.parent.mkdir(parents=True, exist_ok=True)
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    with open(config_path) as f:
        user_config = yaml.safe_load(f) or {}

    # Merge with defaults
    config = DEFAULT_CONFIG.copy()
    config.update(user_config)

    return config

def save_config(config: dict):
    """Save configuration to file"""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
```

---

## Data Flow

### Daily Start Flow

```
User: plorp start
    ↓
cli.py:start() → daily.py:start()
    ↓
Query TaskWarrior:
    taskwarrior.py:get_overdue_tasks()
    taskwarrior.py:get_due_today()
    taskwarrior.py:get_recurring_today()
    ↓
    subprocess → task export → JSON
    ↓
Generate markdown:
    daily.py:generate_daily_note_content()
    ↓
    Format each task as checkbox
    ↓
Write file:
    files.py:write_file()
    ↓
    vault/daily/YYYY-MM-DD.md
    ↓
Print summary to user
```

### Review Flow

```
User: plorp review
    ↓
cli.py:review() → daily.py:review()
    ↓
Read daily note:
    files.py:read_file()
    vault/daily/YYYY-MM-DD.md
    ↓
Parse unchecked tasks:
    markdown.py:parse_daily_note_tasks()
    Extract: [(desc, uuid), ...]
    ↓
For each task:
    Get details: taskwarrior.py:get_task_info(uuid)
    ↓
    subprocess → task UUID info → JSON
    ↓
    Show to user with prompts.py:prompt_choice()
    ↓
    User decision → Update TaskWarrior:
        taskwarrior.py:mark_done(uuid)
        taskwarrior.py:defer_task(uuid, date)
    ↓
    subprocess → task UUID done/modify
    ↓
Append decisions to daily note:
    daily.py:append_review_section()
    ↓
Show summary
```

### Inbox Processing Flow

```
User: plorp inbox process
    ↓
cli.py:inbox() → inbox.py:process()
    ↓
Read inbox file:
    files.py:read_file()
    vault/inbox/YYYY-MM.md
    ↓
Parse unprocessed items:
    markdown.py:parse_inbox_items()
    ↓
For each item:
    Show item to user
    prompts.py:prompt_choice() → [Task, Note, Discard, Skip]
    ↓
    If Task:
        prompts.py:prompt() for metadata
        taskwarrior.py:create_task()
        subprocess → task add
        ↓
        Optional: Link note
            notes.py:create_note()
            notes.py:link_note_to_task()
    ↓
    If Note:
        notes.py:create_note_interactive()
        obsidian.py:create_note_file()
        Write: vault/notes/...
    ↓
    Mark processed in inbox file:
        inbox.py:mark_processed()
```

---

## TaskWarrior Integration

### Access Methods

**1. CLI Subprocess (Primary)**

```python
import subprocess
import json

# Export tasks as JSON
result = subprocess.run(
    ['task', 'export', 'status:pending'],
    capture_output=True,
    text=True
)
tasks = json.loads(result.stdout)

# Modify task
subprocess.run(['task', uuid, 'done'])
subprocess.run(['task', uuid, 'modify', 'due:tomorrow'])
```

**Pros:**
- Official API
- Stable
- Respects TaskWarrior's logic/hooks

**Cons:**
- Slower (process spawn overhead)

**2. Direct SQLite (Advanced, Read-Only)**

```python
import sqlite3
import os

db_path = os.path.expanduser('~/.task/taskchampion.sqlite3')
conn = sqlite3.connect(db_path)

cursor = conn.execute('''
    SELECT uuid, description, status
    FROM tasks
    WHERE status = 'pending'
''')

for row in cursor:
    print(row)
```

**Pros:**
- Fast (no subprocess)
- Complex queries possible

**Cons:**
- Bypasses TaskWarrior logic
- Schema may change
- Read-only recommended

**Recommendation:** Use CLI for writes, consider direct SQLite for performance-critical reads.

---

## Obsidian Integration

### File Operations

**Create note:**
```python
from pathlib import Path

def create_note(vault_path, title, front_matter=None):
    notes_dir = Path(vault_path) / 'notes'
    notes_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d')
    slug = title.lower().replace(' ', '-')
    filename = f"{slug}-{timestamp}.md"

    note_path = notes_dir / filename

    # Build content
    content = ""
    if front_matter:
        import yaml
        content += "---\n"
        content += yaml.dump(front_matter, default_flow_style=False)
        content += "---\n\n"

    content += f"# {title}\n\n"

    note_path.write_text(content)

    return note_path
```

**Link note to task:**
```python
def link_note_to_task(note_path, task_uuid):
    # 1. Add UUID to note front matter
    content = note_path.read_text()

    fm = parse_frontmatter(content)
    if 'tasks' not in fm:
        fm['tasks'] = []

    if task_uuid not in fm['tasks']:
        fm['tasks'].append(task_uuid)

    # Update file
    new_content = rebuild_with_frontmatter(content, fm)
    note_path.write_text(new_content)

    # 2. Add annotation to TaskWarrior
    from plorp.integrations.taskwarrior import add_annotation
    relative_path = note_path.relative_to(vault_path)
    add_annotation(task_uuid, f"Note: {relative_path}")
```

---

## Configuration Management

### Config File Location

**Priority:**
1. `$XDG_CONFIG_HOME/plorp/config.yaml`
2. `~/.config/plorp/config.yaml`

### Config File Format

```yaml
# plorp Configuration

# Obsidian vault path
vault_path: ~/vault

# TaskWarrior data directory
taskwarrior_data: ~/.task

# Email for inbox capture (optional)
inbox_email: plorp@example.com

# Default text editor
default_editor: vim

# Optional: TaskWarrior context to use
taskwarrior_context: null
```

---

## Error Handling

### Principles

1. **Fail gracefully** - Don't lose data on errors
2. **Clear messages** - Tell user what went wrong
3. **Suggest fixes** - Provide actionable next steps

### Example

```python
def start(config):
    try:
        # Check TaskWarrior accessible
        result = subprocess.run(['task', 'version'],
                              capture_output=True)
        if result.returncode != 0:
            print("❌ Error: TaskWarrior not found")
            print("Install: brew install task")
            return

        # Check vault exists
        vault_path = Path(config['vault_path'])
        if not vault_path.exists():
            print(f"❌ Error: Vault not found: {vault_path}")
            print(f"Create: mkdir -p {vault_path}")
            return

        # Generate daily note
        # ...

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
```

---

## Testing Strategy

### Test Structure

```
tests/
├── test_workflows/
│   ├── test_daily.py
│   ├── test_inbox.py
│   └── test_review.py
│
├── test_integrations/
│   ├── test_taskwarrior.py
│   └── test_obsidian.py
│
├── test_parsers/
│   ├── test_markdown.py
│   └── test_frontmatter.py
│
└── fixtures/
    ├── sample_daily_note.md
    ├── sample_inbox.md
    └── taskwarrior_export.json
```

### Test Approach

**Unit tests:**
- Test parsers with sample markdown
- Test data formatting functions
- No external dependencies

**Integration tests:**
- Mock subprocess calls to TaskWarrior
- Test file I/O with temporary directories
- Verify correct commands generated

**Example:**
```python
import unittest
from unittest.mock import patch, MagicMock
from plorp.integrations.taskwarrior import get_overdue_tasks

class TestTaskWarrior(unittest.TestCase):

    @patch('subprocess.run')
    def test_get_overdue_tasks(self, mock_run):
        # Mock subprocess response
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='[{"uuid": "abc", "description": "Test"}]'
        )

        tasks = get_overdue_tasks()

        # Verify correct command called
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertIn('task', args)
        self.assertIn('export', args)

        # Verify result
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['description'], 'Test')
```

---

## Dependencies

### Required

```
# requirements.txt

# YAML parsing (for Obsidian front matter)
PyYAML>=6.0

# CLI framework
click>=8.0

# Optional: Rich terminal output
rich>=13.0
```

### System Requirements

- Python 3.8+
- TaskWarrior 3.4.1+
- Obsidian (or any markdown-compatible editor)

### Development

```
# requirements-dev.txt

pytest>=7.0
pytest-cov>=4.0
black>=23.0
mypy>=1.0
```

---

## Next Steps

1. **Review architecture** - Does this design make sense?
2. **Set up project** - Create directory structure
3. **Implement Phase 1** - Core daily workflow
4. **Write tests** - Unit + integration tests
5. **Document** - User-facing documentation

---

**Document Version:** 1.0
**Last Updated:** October 6, 2025
**Status:** Draft for review
