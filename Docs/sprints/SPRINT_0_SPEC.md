# Sprint 0: Project Setup & Test Infrastructure

**Sprint ID:** SPRINT-0
**Status:** Ready for Implementation
**Dependencies:** None
**Estimated Duration:** 2-4 hours

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

Create the complete Python project structure and test infrastructure for plorp. This sprint establishes the foundation that all subsequent sprints will build upon.

### What You're Building

A working Python package with:
- Complete project structure
- pytest test infrastructure
- Code formatting and type checking
- Basic CLI entry point (no functionality yet)
- Fixtures and test utilities
- CI/CD configuration

### What You're NOT Building

- Any business logic
- TaskWarrior integration
- Workflow implementations
- Configuration management (beyond structure)

---

## Engineering Handoff Prompt

```
You are implementing Sprint 0 for plorp, a workflow automation tool for TaskWarrior and Obsidian.

PROJECT CONTEXT:
- plorp is a Python CLI tool that bridges TaskWarrior (task management) and Obsidian (note-taking)
- This is Sprint 0: You're creating the project foundation
- No business logic yet - just structure and test infrastructure

YOUR TASK:
1. Read the full Sprint 0 specification: /Users/jsd/Documents/plorp/Docs/sprints/SPRINT_0_SPEC.md
2. Create the complete project structure with all directories and files
3. Set up pytest with fixtures and utilities
4. Configure black, mypy, and coverage
5. Create a minimal CLI entry point that shows help text
6. Write smoke tests to verify everything works
7. Document your work in the Completion Report section

IMPORTANT REQUIREMENTS:
- Follow TDD: Write tests before implementation where applicable
- Use pytest for all testing
- All code must pass black formatting
- Project must be installable via: pip install -e .
- All tests must pass: pytest tests/ -v

WORKING DIRECTORY: /Users/jsd/Documents/plorp/

CLARIFYING QUESTIONS:
If anything is unclear, add your questions to the Q&A section of this spec document and stop. The PM/Architect will answer them before you continue.

COMPLETION:
When done, fill out the Completion Report Template section in this document with details of your implementation.
```

---

## Technical Specifications

### Directory Structure to Create

```
/Users/jsd/Documents/plorp/
├── .github/
│   └── workflows/
│       └── test.yml                    # CI/CD configuration
├── src/
│   └── plorp/
│       ├── __init__.py                 # Package version
│       ├── __main__.py                 # Entry point for python -m plorp
│       ├── cli.py                      # CLI framework (click)
│       ├── config.py                   # [STUB] Config management
│       ├── workflows/
│       │   ├── __init__.py
│       │   ├── daily.py                # [STUB] Daily workflow
│       │   ├── inbox.py                # [STUB] Inbox workflow
│       │   └── notes.py                # [STUB] Note workflow
│       ├── integrations/
│       │   ├── __init__.py
│       │   ├── taskwarrior.py          # [STUB] TaskWarrior integration
│       │   └── obsidian.py             # [STUB] Obsidian integration
│       ├── parsers/
│       │   ├── __init__.py
│       │   ├── markdown.py             # [STUB] Markdown parser
│       │   └── frontmatter.py          # [STUB] YAML front matter
│       └── utils/
│           ├── __init__.py
│           ├── files.py                # [STUB] File utilities
│           ├── dates.py                # [STUB] Date utilities
│           └── prompts.py              # [STUB] CLI prompts
├── tests/
│   ├── __init__.py
│   ├── conftest.py                     # pytest configuration and fixtures
│   ├── fixtures/
│   │   ├── __init__.py
│   │   ├── taskwarrior_export.json     # Sample TaskWarrior data
│   │   ├── sample_daily_note.md        # Sample daily note
│   │   └── sample_inbox.md             # Sample inbox file
│   ├── test_cli.py                     # CLI smoke tests
│   └── test_smoke.py                   # Basic smoke tests
├── scripts/
│   ├── install.sh                      # [STUB] Installation script
│   └── email_to_inbox.py               # [STUB] Email capture
├── docs/
│   └── .gitkeep                        # Placeholder
├── .gitignore                          # Python gitignore
├── pyproject.toml                      # Project configuration
├── README.md                           # Basic README
├── .python-version                     # Python version (3.8)
└── venv/                               # Virtual environment (not committed)
```

### File Specifications

#### `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "plorp"
version = "1.0.0"
description = "Workflow automation for TaskWarrior + Obsidian"
authors = [{name = "plorp contributors"}]
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
markers = [
    "integration: marks tests as integration tests (may require external tools)",
]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false  # Relaxed for initial development
```

#### `src/plorp/__init__.py`

```python
# ABOUTME: Package initialization for plorp - defines version and package metadata
# ABOUTME: This module is imported when you "import plorp" and provides __version__
"""
plorp - Workflow automation for TaskWarrior + Obsidian
"""

__version__ = "1.0.0"
```

#### `src/plorp/cli.py`

```python
# ABOUTME: Main CLI entry point using Click framework - defines all plorp commands
# ABOUTME: Handles command routing, help text, and version display for the plorp tool
"""
Main CLI entry point for plorp.
"""
import click
from plorp import __version__


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx):
    """
    plorp - Workflow automation for TaskWarrior + Obsidian

    plorp helps you manage daily workflows by bridging TaskWarrior
    (task management) and Obsidian (note-taking).

    Key commands:
      start   - Generate daily note from TaskWarrior tasks
      review  - Interactive end-of-day task review
      inbox   - Process inbox items into tasks/notes
    """
    ctx.ensure_object(dict)


@cli.command()
def start():
    """Generate daily note for today."""
    click.echo("⚠️  'start' command not yet implemented (coming in a future sprint)")


@cli.command()
def review():
    """Interactive end-of-day review."""
    click.echo("⚠️  'review' command not yet implemented (coming in a future sprint)")


@cli.command()
def inbox():
    """Process inbox items."""
    click.echo("⚠️  'inbox' command not yet implemented (coming in a future sprint)")


if __name__ == "__main__":
    cli()
```

#### `src/plorp/__main__.py`

```python
# ABOUTME: Entry point module for running plorp via "python -m plorp" command
# ABOUTME: Simply imports and invokes the CLI - enables module execution
"""
Entry point for python -m plorp
"""
from plorp.cli import cli

if __name__ == "__main__":
    cli()
```

#### All Stub Files (`workflows/`, `integrations/`, `parsers/`, `utils/`)

Each stub file should have:

```python
"""
[Module description]

Status: STUB - To be implemented in Sprint N
"""

# TODO: Sprint N - Implement this module
```

#### `tests/conftest.py`

```python
# ABOUTME: Pytest configuration file defining shared fixtures for all tests
# ABOUTME: Provides fixtures for test data, sample files, and temporary vault structures
"""
pytest configuration and shared fixtures.
"""
import pytest
from pathlib import Path
import json


@pytest.fixture
def fixture_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_taskwarrior_export(fixture_dir):
    """Load sample TaskWarrior export JSON."""
    with open(fixture_dir / "taskwarrior_export.json") as f:
        return json.load(f)


@pytest.fixture
def sample_daily_note(fixture_dir):
    """Load sample daily note content."""
    with open(fixture_dir / "sample_daily_note.md") as f:
        return f.read()


@pytest.fixture
def sample_inbox(fixture_dir):
    """Load sample inbox content."""
    with open(fixture_dir / "sample_inbox.md") as f:
        return f.read()


@pytest.fixture
def tmp_vault(tmp_path):
    """Create a temporary vault structure."""
    vault = tmp_path / "vault"
    (vault / "daily").mkdir(parents=True)
    (vault / "inbox").mkdir(parents=True)
    (vault / "notes").mkdir(parents=True)
    (vault / "projects").mkdir(parents=True)
    return vault
```

#### `tests/fixtures/taskwarrior_export.json`

```json
[
  {
    "id": 1,
    "uuid": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "description": "Buy groceries",
    "status": "pending",
    "project": "home",
    "due": "20251007T000000Z",
    "priority": "M",
    "tags": ["shopping", "errands"],
    "entry": "20251006T120000Z",
    "modified": "20251006T120000Z",
    "urgency": 8.2
  },
  {
    "id": 2,
    "uuid": "b2c3d4e5-f6a7-8901-2345-678901bcdefg",
    "description": "Call dentist",
    "status": "pending",
    "project": "health",
    "due": "20251005T000000Z",
    "priority": "H",
    "tags": ["health"],
    "entry": "20251001T100000Z",
    "modified": "20251001T100000Z",
    "urgency": 12.5
  },
  {
    "id": 3,
    "uuid": "c3d4e5f6-a7b8-9012-3456-789012cdefgh",
    "description": "Morning meditation",
    "status": "pending",
    "recur": "daily",
    "due": "20251007T080000Z",
    "project": "personal",
    "entry": "20250101T000000Z",
    "modified": "20251006T000000Z",
    "urgency": 5.0
  }
]
```

#### `tests/fixtures/sample_daily_note.md`

```markdown
---
date: 2025-10-06
type: daily
plorp_version: 1.0
---

# Daily Note - October 6, 2025

## Overdue (1)

- [ ] Call dentist (due: 2025-10-05, project: health, priority: H, uuid: b2c3d4e5-f6a7-8901-2345-678901bcdefg)

## Due Today (1)

- [ ] Buy groceries (project: home, priority: M, uuid: a1b2c3d4-e5f6-7890-1234-567890abcdef)

## Recurring

- [ ] Morning meditation (recurring: daily, project: personal, uuid: c3d4e5f6-a7b8-9012-3456-789012cdefgh)

---

## Notes

[Your thoughts, observations, decisions during the day]

---

## Review Section

<!-- Auto-populated by `plorp review` -->
```

#### `tests/fixtures/sample_inbox.md`

```markdown
# Inbox - October 2025

## Unprocessed

- [ ] Email from boss: Q4 planning meeting tomorrow 3pm
- [ ] Idea: Research TaskWarrior hooks for automation
- [ ] Reminder: Buy groceries before weekend

## Processed

- [x] Call dentist - Created task (uuid: b2c3d4e5-f6a7-8901-2345-678901bcdefg)
- [x] Meeting notes idea - Created note: vault/notes/meeting-2025-10-05.md
```

#### `tests/test_smoke.py`

```python
# ABOUTME: Basic smoke tests to verify the project structure is correct
# ABOUTME: Tests package imports, version, and that all modules are accessible
"""
Basic smoke tests to verify project structure.
"""
import plorp
from plorp import __version__


def test_version():
    """Test that version is defined."""
    assert __version__ == "1.0.0"


def test_package_imports():
    """Test that main package can be imported."""
    import plorp.cli
    import plorp.workflows
    import plorp.integrations
    import plorp.parsers
    import plorp.utils

    assert plorp.cli is not None
```

#### `tests/test_cli.py`

```python
# ABOUTME: Tests for the CLI interface - validates commands, help text, and version output
# ABOUTME: Uses Click's CliRunner to test command behavior without actually running plorp
"""
CLI smoke tests.
"""
from click.testing import CliRunner
from plorp.cli import cli


def test_cli_help():
    """Test that CLI help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "plorp" in result.output
    assert "Workflow automation" in result.output


def test_cli_version():
    """Test that version flag works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert "1.0.0" in result.output


def test_start_stub():
    """Test that start command shows not implemented message."""
    runner = CliRunner()
    result = runner.invoke(cli, ["start"])

    assert result.exit_code == 0
    assert "not yet implemented" in result.output
    assert "future sprint" in result.output


def test_review_stub():
    """Test that review command shows not implemented message."""
    runner = CliRunner()
    result = runner.invoke(cli, ["review"])

    assert result.exit_code == 0
    assert "not yet implemented" in result.output


def test_inbox_stub():
    """Test that inbox command shows not implemented message."""
    runner = CliRunner()
    result = runner.invoke(cli, ["inbox"])

    assert result.exit_code == 0
    assert "not yet implemented" in result.output
```

#### `.github/workflows/test.yml`

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install -e .
        pip install -e ".[dev]"

    - name: Run black check
      run: |
        black --check src/ tests/

    - name: Run tests with coverage
      run: |
        pytest tests/ -v --cov=src/plorp --cov-report=xml --cov-report=term

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      if: matrix.python-version == '3.11'
```

#### `.python-version`

```
3.8
```

(Single line file containing just the Python version)

#### `.gitignore`

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Type checking
.mypy_cache/
.dmypy.json
dmypy.json
```

#### `README.md`

```markdown
# plorp

Workflow automation layer for TaskWarrior + Obsidian.

## Status

🚧 **Under Development** - Sprint 0 Complete

plorp is currently in active development. The project structure and test infrastructure are in place.

## What is plorp?

plorp bridges TaskWarrior (task management) and Obsidian (note-taking) through three core workflows:

1. **Daily workflow** - Generate daily notes with tasks from TaskWarrior
2. **Review workflow** - End-of-day processing of incomplete tasks
3. **Inbox workflow** - Email → Markdown → TaskWarrior/Obsidian

## Installation

```bash
# Clone the repository
cd /Users/jsd/Documents/plorp

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

## Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Unix/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install plorp in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

## Quick Start

```bash
# Show help
plorp --help

# Commands (coming in future sprints)
plorp start    # Generate daily note
plorp review   # Review incomplete tasks
plorp inbox    # Process inbox
```

## Development

```bash
# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src/plorp --cov-report=html

# Format code
black src/ tests/

# Type check
mypy src/
```

## Project Structure

See `Docs/plorp_ARCHITECTURE.md` for detailed architecture documentation.

## Documentation

- `Docs/plorp_SPEC.md` - Complete specification
- `Docs/plorp_ARCHITECTURE.md` - Technical architecture
- `Docs/SPRINT_BREAKDOWN.md` - Implementation plan

## License

[To be determined]
```

---

## Test Requirements

### Test Coverage Goals

- **Overall coverage:** >80% (just structure for now)
- **CLI module:** 100% (it's minimal)
- **Smoke tests:** Must all pass

### Required Tests

1. **Smoke tests** (`test_smoke.py`):
   - Package version is correct
   - All modules can be imported

2. **CLI tests** (`test_cli.py`):
   - Help text displays correctly
   - Version flag works
   - All stub commands return "not implemented" messages
   - Exit codes are correct

3. **Fixture tests** (in `conftest.py`):
   - Fixtures load correctly
   - tmp_vault fixture creates proper structure

### Test Execution

```bash
# All tests must pass
pytest tests/ -v

# Coverage report must generate
pytest tests/ --cov=src/plorp --cov-report=html

# Black formatting must pass
black --check src/ tests/
```

---

## Success Criteria

### Git Initialization Check

```bash
cd /Users/jsd/Documents/plorp
git status
# → Should show "On branch main" or "On branch master"
# → Should show clean working tree after initial commit

git log --oneline
# → Should show initial commit: "Sprint 0: Initial project structure and test infrastructure"
```

### Virtual Environment Check

```bash
ls -la venv/
# → Virtual environment directory exists
# → Contains bin/ (or Scripts/ on Windows), lib/, etc.

source venv/bin/activate
which python
# → Should point to venv/bin/python
```

### Installation Check

```bash
cd /Users/jsd/Documents/plorp
source venv/bin/activate
pip install -e .
# → Must succeed without errors
```

### CLI Check

```bash
plorp --help
# → Shows help text
# → Lists commands: start, review, inbox
# → Shows version 1.0.0

plorp --version
# → Shows: plorp, version 1.0.0

plorp start
# → Shows: "not yet implemented (coming in Sprint 2)"
# → Exit code 0
```

### Test Check

```bash
pytest tests/ -v
# → All tests pass
# → No failures or errors

pytest tests/ --cov=src/plorp --cov-report=term
# → Coverage >80%
# → Report generated
```

### Structure Check

```bash
# All directories exist
ls -la src/plorp/workflows/
ls -la src/plorp/integrations/
ls -la tests/fixtures/

# All fixture files exist
cat tests/fixtures/taskwarrior_export.json
cat tests/fixtures/sample_daily_note.md
cat tests/fixtures/sample_inbox.md
```

### Code Quality Check

```bash
black --check src/ tests/
# → All files properly formatted

python -c "import plorp; print(plorp.__version__)"
# → Outputs: 1.0.0
```

---

## Completion Report Template

**Instructions:** Fill this out when Sprint 0 is complete.

### Implementation Summary

**What was implemented:**
- [ ] Git repository initialized with initial commit
- [ ] Virtual environment created (venv/)
- [ ] Complete directory structure created
- [ ] All stub files created with proper docstrings and ABOUTME comments
- [ ] pyproject.toml configured (using modern Python packaging)
- [ ] .python-version file created
- [ ] CLI entry point working with all stub commands
- [ ] Test fixtures created (TaskWarrior export, daily note, inbox)
- [ ] pytest configuration complete with shared fixtures
- [ ] CI/CD workflow configured (.github/workflows/test.yml)
- [ ] All smoke tests passing
- [ ] Black formatting applied
- [ ] Package installable via pip install -e .

**Lines of code added:** [Fill in]

**Test coverage achieved:** [Fill in]

### Deviations from Spec

**Any changes from the specification?**

[Describe any intentional deviations and why they were necessary]

### Verification Commands

**Commands to verify Sprint 0 is complete:**

```bash
# 1. Git initialized
cd /Users/jsd/Documents/plorp
git status
git log --oneline

# 2. Virtual environment created
ls -la venv/
source venv/bin/activate

# 3. Installation works
pip install -e .

# 4. CLI works
plorp --help
plorp --version
plorp start
plorp review
plorp inbox

# 5. Tests pass
pytest tests/ -v

# 6. Coverage adequate
pytest tests/ --cov=src/plorp --cov-report=term

# 7. Formatting correct
black --check src/ tests/

# 8. Project structure correct
ls -la src/plorp/
ls -la tests/fixtures/
cat .python-version
```

**Expected output:** [Describe what each command should output]

### Known Issues

**Any known limitations or issues:**

[List any issues that need to be addressed in future sprints]

### Handoff Notes for Sprint 1

**What Sprint 1 needs to know:**

- Fixture files available in `tests/fixtures/`
- Test utilities available in `conftest.py`
- Use `tmp_vault` fixture for file operations
- All stub files are in place and ready for implementation

**Files Sprint 1 will modify:**
- `src/plorp/integrations/taskwarrior.py`
- `tests/test_integrations/test_taskwarrior.py` (create)

**Files Sprint 1 should NOT modify:**
- Project structure
- Fixtures
- CLI (except to wire up new functionality)

### Questions for PM/Architect

[Add any questions or clarifications needed]

### Recommendations

**Suggestions for future sprints:**

[Any recommendations based on what you learned in Sprint 0]

### Sign-off

- **Implemented by:** [Claude Code Engineer Instance]
- **Date completed:** [Date]
- **Implementation time:** [Actual time taken]
- **Ready for Sprint 1:** [Yes/No]

---

## Q&A Section

### Questions from Engineering

**Format for questions:**

```
Q: [Your question here]
Status: PENDING
```

---

**Q1: Git initialization and initial commit**
```
Q: Should Sprint 0 include initializing a git repository and making an initial commit?
   The implementation plan (Phase 0) mentions "Initialize Git" but the Sprint 0 spec
   doesn't explicitly list it. Should we:
   a) Initialize git repo and make initial commit as part of Sprint 0
   b) Assume git is already initialized (since we're working in /Users/jsd/Documents/plorp)
   c) Skip git entirely for Sprint 0
Status: PENDING
```

**Q2: Python virtual environment**
```
Q: Should Sprint 0 create a virtual environment (venv/) or assume the developer will
   manage this themselves? The .gitignore includes venv/ which suggests it shouldn't
   be committed, but should the sprint create it or document the expectation?
Status: PENDING
```

**Q3: requirements.txt vs pyproject.toml dependencies**
```
Q: The spec shows both requirements.txt and requirements-dev.txt files, but also
   shows dependencies in pyproject.toml. Should we:
   a) Generate requirements.txt from pyproject.toml via pip freeze
   b) Manually duplicate the dependencies in requirements.txt
   c) Skip requirements.txt and rely only on pyproject.toml

   (Note: Modern Python packaging typically uses only pyproject.toml, but the spec
   includes both)
Status: PENDING
```

**Q4: .python-version file format**
```
Q: What should the .python-version file contain? Just "3.8" or the full version
   like "3.8.0"? This file is typically used by pyenv.
Status: PENDING
```

**Q5: ABOUTME comments requirement**
```
Q: The Lead Engineer prompt specifies that "All code files MUST start with a brief
   2-line comment explaining what the file does. Each line MUST start with 'ABOUTME: '".

   However, the Sprint 0 spec shows stub files with only TODO comments. Should we:
   a) Add ABOUTME comments to all stub files now (even though they're stubs)
   b) Wait until each file is implemented in its respective sprint
   c) Add ABOUTME to only the implemented files (cli.py, __init__.py, __main__.py)
Status: PENDING
```

**Q6: Coverage target clarification**
```
Q: The spec states ">80% coverage (just structure for now)" but we're only creating
   stubs and minimal CLI. Is the 80% target:
   a) For the actual code we're writing (cli.py, __init__.py) - likely achievable
   b) For all stub files too - unlikely to be achievable since stubs have no logic
   c) Just a future goal, not a Sprint 0 requirement

   What's the actual coverage threshold for Sprint 0 to be considered complete?
Status: PENDING
```

**Q7: Sprint numbering in stub messages**
```
Q: The stub commands reference "Sprint 2", "Sprint 3", "Sprint 4" for start, review,
   and inbox respectively. Should we confirm these sprint numbers are correct, or should
   we use "future sprint" to avoid committing to a specific timeline?
Status: PENDING
```

### Answers from PM/Architect

**Q1: Git initialization and initial commit**
```
Q: Should Sprint 0 include initializing a git repository and making an initial commit?
A: Yes, Sprint 0 should initialize the git repository and make an initial commit.
   Steps:
   1. Run: git init
   2. Create initial commit with all Sprint 0 files
   3. Commit message: "Sprint 0: Initial project structure and test infrastructure"

   This establishes version control from the start and future sprints can reference
   git history.
Status: RESOLVED
```

**Q2: Python virtual environment**
```
Q: Should Sprint 0 create a virtual environment (venv/) or assume the developer will
   manage this themselves?
A: Sprint 0 should create the virtual environment. Add these steps:
   1. python3 -m venv venv
   2. Document activation in README: source venv/bin/activate (Unix) or venv\Scripts\activate (Windows)
   3. The venv/ directory is already in .gitignore, so it won't be committed

   Include verification that the venv was created successfully in the completion report.
Status: RESOLVED
```

**Q3: requirements.txt vs pyproject.toml dependencies**
```
Q: Should we use requirements.txt or rely only on pyproject.toml?
A: Use only pyproject.toml. This is the modern Python packaging standard.
   Remove requirements.txt and requirements-dev.txt from the file list.

   Installation becomes:
   - pip install -e .              (runtime deps)
   - pip install -e ".[dev]"       (dev deps)

   This is cleaner and avoids duplicate dependency management.
Status: RESOLVED
```

**Q4: .python-version file format**
```
Q: What should the .python-version file contain?
A: Use "3.8" (major.minor only). This is the standard format for pyenv and other
   version managers. The file should contain exactly:
   3.8

   (One line, no quotes, major.minor version)
Status: RESOLVED
```

**Q5: ABOUTME comments requirement**
```
Q: Should we add ABOUTME comments to all files?
A: Add ABOUTME comments to all non-stub Python files that contain actual implementation:
   - src/plorp/__init__.py
   - src/plorp/__main__.py
   - src/plorp/cli.py
   - tests/conftest.py
   - tests/test_smoke.py
   - tests/test_cli.py

   Format:
   # ABOUTME: [First line describing what this file does]
   # ABOUTME: [Second line with additional context]

   For stub files (workflows/, integrations/, parsers/, utils/), add ABOUTME comments
   when they are implemented in their respective sprints. For now, just the TODO comment
   is sufficient.
Status: RESOLVED
```

**Q6: Coverage target clarification**
```
Q: What's the actual coverage threshold for Sprint 0?
A: For Sprint 0, aim for 90%+ coverage on the actual implemented code (cli.py, __init__.py).
   Stub files don't need coverage since they have no logic.

   Specifically:
   - cli.py: 100% coverage (all commands tested)
   - __init__.py: 100% coverage (just version import)
   - Test utilities: Don't worry about coverage of test infrastructure itself

   The overall project coverage will be low (~20-30%) because of all the stubs, and
   that's expected. Sprint 0 is considered complete if the implemented modules have
   high coverage.
Status: RESOLVED
```

**Q7: Sprint numbering in stub messages**
```
Q: Should stub commands reference specific sprint numbers or use generic language?
A: Use generic "future sprint" language. Change the stub messages to:

   start:  "⚠️  'start' command not yet implemented (coming in a future sprint)"
   review: "⚠️  'review' command not yet implemented (coming in a future sprint)"
   inbox:  "⚠️  'inbox' command not yet implemented (coming in a future sprint)"

   This avoids committing to a specific timeline in the code.
Status: RESOLVED
```

---

**Document Version:** 1.0
**Last Updated:** October 6, 2025
**Status:** Ready for Implementation
**Next Sprint:** SPRINT-1 (TaskWarrior Integration)
