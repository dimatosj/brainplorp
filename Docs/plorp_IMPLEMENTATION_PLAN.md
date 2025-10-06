# plorp Implementation Plan

**Date:** October 6, 2025
**Purpose:** Phase-by-phase build plan for plorp

---

## Table of Contents

1. [Overview](#overview)
2. [Phase 0: Setup](#phase-0-setup)
3. [Phase 1: Core Daily Workflow](#phase-1-core-daily-workflow)
4. [Phase 2: Review Workflow](#phase-2-review-workflow)
5. [Phase 3: Inbox Workflow](#phase-3-inbox-workflow)
6. [Phase 4: Note Linking](#phase-4-note-linking)
7. [Phase 5: Polish & Documentation](#phase-5-polish--documentation)
8. [Testing Strategy](#testing-strategy)
9. [Timeline](#timeline)
10. [Success Criteria](#success-criteria)

---

## Overview

### Build Strategy

**Incremental delivery:** Each phase produces working functionality

**Test-driven:** Write tests alongside implementation

**User validation:** Test with real workflow after each phase

### Phase Dependencies

```
Phase 0: Setup
    ↓
Phase 1: Core Daily
    ↓
Phase 2: Review ← Can start Phase 3 in parallel
    ↓
Phase 3: Inbox
    ↓
Phase 4: Note Linking
    ↓
Phase 5: Polish
```

---

## Phase 0: Setup

**Duration:** 1-2 hours

**Goal:** Project structure and dependencies

### Tasks

#### 1. Create Project Structure

```bash
mkdir -p plorp/{src/plorp/{workflows,integrations,parsers,utils},tests,scripts,config,docs}
cd plorp

# Create all __init__.py files
touch src/plorp/__init__.py
touch src/plorp/workflows/__init__.py
touch src/plorp/integrations/__init__.py
touch src/plorp/parsers/__init__.py
touch src/plorp/utils/__init__.py
touch tests/__init__.py

# Create entry points
touch src/plorp/__main__.py
touch src/plorp/cli.py

# Create config
touch pyproject.toml
touch requirements.txt
touch requirements-dev.txt

# Create README
touch README.md
```

#### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install PyYAML click rich pytest pytest-cov black mypy
pip freeze > requirements.txt
```

#### 3. Create `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "plorp"
version = "1.0.0"
description = "Workflow automation for TaskWarrior + Obsidian"
authors = [{name = "Your Name", email = "you@example.com"}]
readme = "README.md"
requires-python = ">=3.8"
dependencies = [
    "PyYAML>=6.0",
    "click>=8.0",
    "rich>=13.0",
]

[project.scripts]
plorp = "plorp.cli:cli"

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=23.0",
    "mypy>=1.0",
]

[tool.black]
line-length = 100
target-version = ['py38', 'py39', 'py310', 'py311']

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
```

#### 4. Create Basic README

```markdown
# plorp

Workflow automation layer for TaskWarrior + Obsidian.

## Installation

```bash
pip install -e .
```

## Quick Start

```bash
# Generate daily note
plorp start

# Review incomplete tasks
plorp review

# Process inbox
plorp inbox process
```

## Documentation

See `docs/` for full documentation.
```

#### 5. Initialize Git

```bash
git init
git add .
git commit -m "Initial project structure for plorp"
```

### Deliverables

- ✅ Project structure created
- ✅ Python environment set up
- ✅ Dependencies installed
- ✅ Git repository initialized

---

## Phase 1: Core Daily Workflow

**Duration:** 2-3 days

**Goal:** `plorp start` generates daily note from TaskWarrior

### Tasks

#### 1. Implement TaskWarrior Integration (Day 1)

**File:** `src/plorp/integrations/taskwarrior.py`

**Functions to implement:**
```python
def run_task_command(args, capture=True)
def get_tasks(filter_args)
def get_overdue_tasks()
def get_due_today()
def get_recurring_today()
```

**Test:**
```python
# tests/test_integrations/test_taskwarrior.py
def test_get_overdue_tasks()
def test_get_due_today()
def test_task_command_execution()
```

**Manual verification:**
```bash
python3 -c "
from plorp.integrations.taskwarrior import get_due_today
tasks = get_due_today()
print(f'Found {len(tasks)} tasks')
for task in tasks:
    print(f\"  - {task['description']}\")
"
```

#### 2. Implement File Utilities (Day 1)

**File:** `src/plorp/utils/files.py`

```python
def read_file(path)
def write_file(path, content)
def ensure_directory(path)
```

**Test:**
```python
# tests/test_utils/test_files.py
def test_write_and_read_file(tmp_path)
def test_ensure_directory(tmp_path)
```

#### 3. Implement Daily Note Generation (Day 2)

**File:** `src/plorp/workflows/daily.py`

```python
def start(config)
def generate_daily_note_content(today, overdue, due_today, recurring)
def format_task_checkbox(task)
```

**Test:**
```python
# tests/test_workflows/test_daily.py
def test_generate_daily_note_content()
def test_format_task_checkbox()
```

#### 4. Implement CLI (Day 2)

**File:** `src/plorp/cli.py`

```python
@cli.group()
def cli(ctx)

@cli.command()
def start(config)
```

**Test:**
```bash
# Manual test
plorp start

# Should output:
# ✅ Daily note generated
# 📄 /path/to/vault/daily/2025-10-06.md
```

#### 5. Implement Config Management (Day 2)

**File:** `src/plorp/config.py`

```python
def get_config_path()
def load_config()
def save_config(config)
```

**Test:**
```python
# tests/test_config.py
def test_load_default_config()
def test_save_and_load_config(tmp_path)
```

#### 6. Integration Test (Day 3)

**Create real workflow test:**

```bash
# Setup
task add "Test task 1" due:today
task add "Test task 2" due:yesterday
task add "Test recurring" due:today recur:daily

# Run plorp start
plorp start

# Verify daily note exists
ls ~/vault/daily/$(date +%Y-%m-%d).md

# Verify content
cat ~/vault/daily/$(date +%Y-%m-%d).md | grep "Test task"

# Cleanup
task "Test task 1" delete
task "Test task 2" delete
task "Test recurring" delete
```

### Deliverables

- ✅ `plorp start` command works
- ✅ Queries TaskWarrior for tasks
- ✅ Generates daily note in vault/daily/
- ✅ Tests pass
- ✅ Config system works

### Success Criteria

```bash
# User can run:
plorp start

# And get:
# - vault/daily/YYYY-MM-DD.md created
# - Contains overdue tasks
# - Contains due today tasks
# - Contains recurring tasks
# - Formatted as markdown checkboxes with UUIDs
```

---

## Phase 2: Review Workflow

**Duration:** 2-3 days

**Goal:** `plorp review` processes incomplete tasks interactively

### Tasks

#### 1. Implement Markdown Parser (Day 1)

**File:** `src/plorp/parsers/markdown.py`

```python
def parse_daily_note_tasks(note_path)
def parse_frontmatter(content)
```

**Test:**
```python
# tests/test_parsers/test_markdown.py
def test_parse_daily_note_tasks()
def test_parse_frontmatter()
```

**Sample fixture:**
```markdown
<!-- tests/fixtures/sample_daily_note.md -->
---
date: 2025-10-06
type: daily
---

# Daily Note

## Due Today

- [ ] Buy groceries (project: home, uuid: abc-123)
- [x] Call dentist (uuid: def-456)
- [ ] Review PR #45 (project: dev, uuid: ghi-789)
```

#### 2. Implement Prompt Utilities (Day 1)

**File:** `src/plorp/utils/prompts.py`

```python
def prompt(message)
def prompt_choice(options)
def confirm(message)
```

**Test:**
```python
# tests/test_utils/test_prompts.py
# Mock input for automated testing
def test_prompt_choice()
def test_confirm()
```

#### 3. Extend TaskWarrior Integration (Day 2)

**Add to:** `src/plorp/integrations/taskwarrior.py`

```python
def get_task_info(uuid)
def mark_done(uuid)
def defer_task(uuid, new_due)
def set_priority(uuid, priority)
def delete_task(uuid)
```

**Test:**
```python
def test_mark_done()
def test_defer_task()
def test_set_priority()
```

#### 4. Implement Review Workflow (Day 2-3)

**File:** `src/plorp/workflows/daily.py`

```python
def review(config)
def append_review_section(daily_path, decisions)
```

**Test:**
```python
# tests/test_workflows/test_review.py
def test_review_parsing()
def test_append_review_section()
```

#### 5. Add CLI Command (Day 3)

**Add to:** `src/plorp/cli.py`

```python
@cli.command()
def review(config)
```

#### 6. Integration Test (Day 3)

**Manual workflow test:**

```bash
# Setup
task add "Test review 1" due:today
task add "Test review 2" due:today
plorp start

# Run review (manually mark done, defer, etc.)
plorp review

# Verify TaskWarrior updated
task list

# Verify daily note has review section
cat ~/vault/daily/$(date +%Y-%m-%d).md | grep "Review Section"
```

### Deliverables

- ✅ `plorp review` command works
- ✅ Parses daily note for uncompleted tasks
- ✅ Interactive prompts for each task
- ✅ Updates TaskWarrior based on decisions
- ✅ Appends summary to daily note

### Success Criteria

```bash
# User can run:
plorp review

# And get:
# - Interactive prompts for each uncompleted task
# - Options: done, defer, change priority, skip, delete
# - TaskWarrior updated with decisions
# - Daily note updated with review section
```

---

## Phase 3: Inbox Workflow

**Duration:** 3-4 days

**Goal:** `plorp inbox process` converts inbox items to tasks/notes

### Tasks

#### 1. Create Inbox Parser (Day 1)

**File:** `src/plorp/parsers/markdown.py`

```python
def parse_inbox_items(inbox_path)
def mark_item_processed(inbox_path, item_index)
```

**Test:**
```python
def test_parse_inbox_items()
def test_mark_item_processed()
```

#### 2. Extend TaskWarrior Integration (Day 1)

**Add to:** `src/plorp/integrations/taskwarrior.py`

```python
def create_task(description, project, due, priority, tags) -> str
    # Returns UUID of created task
```

**Test:**
```python
def test_create_task()
def test_create_task_with_metadata()
```

#### 3. Implement Obsidian Integration (Day 2)

**File:** `src/plorp/integrations/obsidian.py`

```python
def create_note(vault_path, title, note_type, metadata)
def get_vault_path(config)
```

**Test:**
```python
def test_create_note(tmp_path)
def test_note_front_matter()
```

#### 4. Implement Inbox Workflow (Day 2-3)

**File:** `src/plorp/workflows/inbox.py`

```python
def process(config)
def process_item_as_task(item, config)
def process_item_as_note(item, config)
```

**Test:**
```python
def test_process_as_task()
def test_process_as_note()
```

#### 5. Add CLI Command (Day 3)

**Add to:** `src/plorp/cli.py`

```python
@cli.command()
@click.argument('subcommand', default='process')
def inbox(config, subcommand)
```

#### 6. Email Capture Script (Day 4)

**File:** `scripts/email_to_inbox.py`

```python
#!/usr/bin/env python3
"""
Email capture script for plorp inbox.
Run via cron: */30 * * * * ~/plorp/scripts/email_to_inbox.py
"""
import imaplib
import email
from datetime import datetime
from pathlib import Path

def fetch_emails(config):
    # Connect to IMAP server
    # Fetch unread emails
    # Parse subject/body
    # Append to inbox file

def main():
    config = load_config()
    emails = fetch_emails(config)

    vault_path = Path(config['vault_path'])
    inbox_path = vault_path / 'inbox' / f'{datetime.now():%Y-%m}.md'

    for subject, body in emails:
        append_to_inbox(inbox_path, subject, body)
```

**Note:** Email integration is optional for plorp. Can be deferred to Phase 6.

#### 7. Integration Test (Day 4)

```bash
# Create sample inbox
cat > ~/vault/inbox/2025-10.md << 'EOF'
# Inbox - October 2025

## Unprocessed

- [ ] Buy groceries for weekend
- [ ] Research TaskWarrior hooks
- [ ] Meeting notes: Q4 planning discussion

## Processed
EOF

# Run inbox processing
plorp inbox process
# Interactively choose: task, note, discard

# Verify tasks created
task list | grep "groceries"

# Verify notes created
ls ~/vault/notes/ | grep "plorp-hooks"

# Verify inbox updated
cat ~/vault/inbox/2025-10.md | grep "Processed"
```

### Deliverables

- ✅ `plorp inbox process` command works
- ✅ Reads monthly inbox file
- ✅ Interactive prompts for each item
- ✅ Creates tasks in TaskWarrior
- ✅ Creates notes in Obsidian
- ✅ Marks items as processed
- ⚠️ Email capture (optional, can defer)

### Success Criteria

```bash
# User can run:
plorp inbox process

# And get:
# - Interactive prompts for each unprocessed item
# - Options: create task, create note, discard, skip
# - Tasks created in TaskWarrior
# - Notes created in Obsidian
# - Inbox file updated (items marked processed)
```

---

## Phase 4: Note Linking

**Duration:** 2-3 days

**Goal:** Bidirectional task-note linking

### Tasks

#### 1. Extend Markdown Parser for Front Matter (Day 1)

**Add to:** `src/plorp/parsers/markdown.py`

```python
def add_frontmatter_field(content, field, value)
def extract_task_uuids_from_note(note_path)
```

**Test:**
```python
def test_add_frontmatter_field()
def test_extract_task_uuids()
```

#### 2. Extend TaskWarrior Integration (Day 1)

**Add to:** `src/plorp/integrations/taskwarrior.py`

```python
def add_annotation(uuid, text)
def get_task_annotations(uuid)
```

**Test:**
```python
def test_add_annotation()
def test_get_annotations()
```

#### 3. Implement Note Linking Workflow (Day 2)

**File:** `src/plorp/workflows/notes.py`

```python
def create_note(config, title, task_uuid=None)
def link_note_to_task(note_path, task_uuid)
def get_linked_notes(task_uuid)
```

**Test:**
```python
def test_create_note_with_task_link()
def test_link_existing_note()
def test_get_linked_notes()
```

#### 4. Add CLI Commands (Day 2)

**Add to:** `src/plorp/cli.py`

```python
@cli.command()
@click.argument('title')
@click.option('--task', help='Link to task UUID')
def note(config, title, task)

@cli.command()
@click.argument('task_uuid')
@click.argument('note_path')
def link(config, task_uuid, note_path)
```

#### 5. Update Review to Show Linked Notes (Day 3)

**Modify:** `src/plorp/workflows/daily.py:review()`

```python
# In review loop, show linked notes
notes = get_linked_notes(task_uuid)
if notes:
    print("Linked notes:")
    for note in notes:
        print(f"  • {note}")
```

#### 6. Integration Test (Day 3)

```bash
# Create task
task add "Write documentation" project:plorp due:today

# Get UUID (assuming it's abc-123)
TASK_UUID=$(task export | jq -r '.[0].uuid')

# Create linked note
plorp note "Documentation Plan" --task $TASK_UUID

# Verify note has UUID in front matter
cat ~/vault/notes/documentation-plan-*.md | grep $TASK_UUID

# Verify task has annotation
task $TASK_UUID info | grep "Note:"

# Link existing note
plorp link $TASK_UUID ~/vault/notes/existing-note.md

# Verify bidirectional link
task $TASK_UUID info
cat ~/vault/notes/existing-note.md | head -10

# Test in review workflow
plorp review
# Should show linked notes for task
```

### Deliverables

- ✅ `plorp note` command creates notes
- ✅ `plorp link` command links existing notes
- ✅ Bidirectional linking works
- ✅ Note front matter includes task UUIDs
- ✅ TaskWarrior annotations include note paths
- ✅ Review workflow shows linked notes

### Success Criteria

```bash
# User can:
# 1. Create note linked to task
plorp note "Meeting Notes" --task abc-123

# 2. Link existing note to task
plorp link abc-123 vault/notes/existing.md

# 3. See links in review
plorp review
# Shows: "Linked notes: vault/notes/meeting-notes.md"

# 4. Verify in TaskWarrior
task abc-123 info
# Shows: "Note: vault/notes/meeting-notes.md"

# 5. Verify in Obsidian
cat vault/notes/meeting-notes.md
# Front matter includes: tasks: [abc-123]
```

---

## Phase 5: Polish & Documentation

**Duration:** 2-3 days

**Goal:** Production-ready release

### Tasks

#### 1. Error Handling (Day 1)

**Audit all commands for error handling:**

```python
# Check TaskWarrior installed
try:
    subprocess.run(['task', '--version'], capture_output=True, check=True)
except FileNotFoundError:
    print("❌ Error: TaskWarrior not found")
    print("Install: brew install task")
    sys.exit(1)

# Check vault exists
vault_path = Path(config['vault_path'])
if not vault_path.exists():
    print(f"❌ Error: Vault not found: {vault_path}")
    print(f"Create: mkdir -p {vault_path}")
    sys.exit(1)

# Check TaskWarrior has tasks
# etc.
```

#### 2. Help Text & Documentation (Day 1-2)

**Add help text to all commands:**

```python
@cli.command()
@click.pass_obj
def start(config):
    """
    Generate daily note for today.

    Queries TaskWarrior for:
    - Overdue tasks (due before today)
    - Tasks due today
    - Recurring tasks due today

    Creates: vault/daily/YYYY-MM-DD.md

    Example:
        plorp start
    """
    # ...
```

**Create user documentation:**

```bash
docs/
├── GETTING_STARTED.md     # 5-minute quick start
├── COMMANDS.md            # Full command reference
├── WORKFLOWS.md           # Workflow guides
├── CONFIGURATION.md       # Config file reference
└── TROUBLESHOOTING.md     # Common issues
```

#### 3. Config Command (Day 2)

**Add to:** `src/plorp/cli.py`

```python
@cli.command()
@click.argument('subcommand', default='show')
@click.argument('key', required=False)
@click.argument('value', required=False)
def config(subcommand, key, value):
    """
    Show or edit configuration.

    Examples:
        plorp config show
        plorp config set vault_path ~/Documents/vault
        plorp config get vault_path
    """
    cfg = load_config()

    if subcommand == 'show':
        for k, v in cfg.items():
            print(f"{k}: {v}")

    elif subcommand == 'get':
        print(cfg.get(key, 'Not set'))

    elif subcommand == 'set':
        cfg[key] = value
        save_config(cfg)
        print(f"✅ Set {key} = {value}")
```

#### 4. Installation Script (Day 2)

**File:** `scripts/install.sh`

```bash
#!/bin/bash
set -e

echo "🚀 plorp Installation"
echo "========================"
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found: Python $PYTHON_VERSION"

# Check TaskWarrior
echo "Checking TaskWarrior..."
if ! command -v task &> /dev/null; then
    echo "❌ TaskWarrior not found"
    echo "Install: brew install task"
    exit 1
fi
TASK_VERSION=$(task --version 2>&1)
echo "Found: TaskWarrior $TASK_VERSION"

# Install plorp
echo ""
echo "Installing plorp..."
pip install -e .

# Create config
echo ""
echo "Creating config..."
plorp config set vault_path ~/vault

# Test installation
echo ""
echo "Testing installation..."
plorp --version

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Run: plorp config show"
echo "  2. Run: plorp start"
echo "  3. Read: docs/GETTING_STARTED.md"
```

#### 5. Testing & Bug Fixes (Day 3)

**Run full test suite:**

```bash
# Unit tests
pytest tests/ -v

# Coverage
pytest tests/ --cov=src/plorp --cov-report=html

# Manual integration tests
./tests/integration/test_full_workflow.sh
```

**Fix any bugs found**

#### 6. Version & Release (Day 3)

**Tag release:**

```bash
git tag -a v1.0.0 -m "plorp v1.0.0 - Workflow layer on TaskWarrior + Obsidian"
git push origin v1.0.0
```

### Deliverables

- ✅ Error handling complete
- ✅ Help text on all commands
- ✅ User documentation complete
- ✅ Installation script works
- ✅ All tests pass
- ✅ Version 1.0.0 tagged

### Success Criteria

```bash
# New user can:
# 1. Install
./scripts/install.sh

# 2. Configure
plorp config show
plorp config set vault_path ~/my-vault

# 3. Use
plorp start
plorp review
plorp inbox process

# 4. Get help
plorp --help
plorp start --help

# 5. Troubleshoot
cat docs/TROUBLESHOOTING.md
```

---

## Testing Strategy

### Test Pyramid

```
       ┌────────────┐
       │   Manual   │  Integration tests (10%)
       │    Tests   │
       └────────────┘
      ┌──────────────┐
      │ Integration  │  Module integration (30%)
      │    Tests     │
      └──────────────┘
    ┌──────────────────┐
    │   Unit Tests     │  Function-level tests (60%)
    └──────────────────┘
```

### Unit Tests

**Coverage:** 60% of tests

**Focus:** Individual functions

```python
# tests/test_parsers/test_markdown.py
def test_parse_daily_note_tasks():
    content = """
    - [ ] Task 1 (uuid: abc-123)
    - [x] Task 2 (uuid: def-456)
    - [ ] Task 3 (uuid: ghi-789)
    """
    tasks = parse_daily_note_tasks_from_content(content)
    assert len(tasks) == 2  # Only unchecked
    assert tasks[0] == ('Task 1', 'abc-123')
```

### Integration Tests

**Coverage:** 30% of tests

**Focus:** Module interactions

```python
# tests/test_integrations/test_taskwarrior.py
@patch('subprocess.run')
def test_create_and_query_task(mock_run):
    # Mock task add
    mock_run.return_value = MagicMock(returncode=0, stdout='Created task 1.\n')
    uuid = create_task('Test task')

    # Mock task export
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout='[{"uuid": "abc", "description": "Test task"}]'
    )
    tasks = get_tasks(['abc'])

    assert len(tasks) == 1
    assert tasks[0]['description'] == 'Test task'
```

### Manual Tests

**Coverage:** 10% of tests

**Focus:** End-to-end workflows

```bash
# tests/integration/test_full_workflow.sh
#!/bin/bash
set -e

echo "Testing full plorp workflow..."

# Setup
task add "Integration test 1" due:today project:test
task add "Integration test 2" due:yesterday project:test

# Test start
plorp start
TODAY=$(date +%Y-%m-%d)
if [ ! -f ~/vault/daily/$TODAY.md ]; then
    echo "❌ Daily note not created"
    exit 1
fi
echo "✅ Daily note created"

# Test review (automated input)
echo -e "1\n1\nq\n" | plorp review
echo "✅ Review completed"

# Cleanup
task project:test delete
echo "✅ Test complete"
```

### CI/CD

**GitHub Actions:**

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install TaskWarrior
      run: |
        sudo apt-get update
        sudo apt-get install -y taskwarrior

    - name: Install dependencies
      run: |
        pip install -e .
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        pytest tests/ --cov=src/plorp --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## Timeline

### Optimistic (Dedicated Work)

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 0: Setup | 2 hours | 2 hours |
| Phase 1: Core Daily | 2 days | 2 days |
| Phase 2: Review | 2 days | 4 days |
| Phase 3: Inbox | 3 days | 7 days |
| Phase 4: Note Linking | 2 days | 9 days |
| Phase 5: Polish | 2 days | 11 days |

**Total: ~2 weeks**

### Realistic (Part-Time Work)

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 0: Setup | 1 evening | 1 day |
| Phase 1: Core Daily | 1 week | 8 days |
| Phase 2: Review | 1 week | 15 days |
| Phase 3: Inbox | 1.5 weeks | 26 days |
| Phase 4: Note Linking | 1 week | 33 days |
| Phase 5: Polish | 1 week | 40 days |

**Total: ~6 weeks part-time**

### Aggressive (MVP)

**Goal:** Get to working daily workflow ASAP

| Phase | Duration | Focus |
|-------|----------|-------|
| Phase 0+1 | 1 day | Setup + plorp start |
| Phase 2 | 1 day | plorp review (basic) |
| Test | 1 day | Use in real workflow |

**MVP: 3 days** (start + review only)

Then iterate:
- Week 2: Add inbox
- Week 3: Add note linking
- Week 4: Polish

---

## Success Criteria

### Phase 1 Success

```bash
✅ plorp start works
✅ Daily note generated
✅ Contains tasks from TaskWarrior
✅ I can use it every morning
```

### Phase 2 Success

```bash
✅ plorp review works
✅ Processes incomplete tasks
✅ Updates TaskWarrior
✅ I can use it every evening
```

### Phase 3 Success

```bash
✅ plorp inbox process works
✅ Converts inbox items to tasks/notes
✅ I can process inbox weekly
```

### Phase 4 Success

```bash
✅ Task-note linking works
✅ Bidirectional links
✅ Shows in review workflow
```

### Phase 5 Success

```bash
✅ Documentation complete
✅ Installation script works
✅ Ready to share with others
```

### Overall v1.0 Success

**Daily workflow works seamlessly:**

```bash
# Morning
plorp start
# → Daily note generated

# During day
# → Work in Obsidian, check off tasks

# Evening
plorp review
# → Process incomplete items

# Weekly
plorp inbox process
# → Convert inbox to tasks/notes
```

**Integration works:**
- Tasks in TaskWarrior show in plorp
- Tasks created in plorp show in TaskWarrior
- Notes link to tasks bidirectionally
- Native TaskWarrior commands still work

**Less complex than V1:**
- No custom database
- Clearer architecture
- Easier to maintain

**Extensible:**
- Easy to add new workflows
- Can leverage TaskWarrior ecosystem
- Compatible with Obsidian plugins

---

## Next Steps

1. **Review implementation plan**
2. **Start Phase 0** - Set up project structure
3. **Begin Phase 1** - Build core daily workflow
4. **Test with real workflow** - Use plorp for actual daily work
5. **Iterate** - Add features based on real usage

---

**Document Version:** 1.0
**Last Updated:** October 6, 2025
**Status:** Ready to begin implementation
