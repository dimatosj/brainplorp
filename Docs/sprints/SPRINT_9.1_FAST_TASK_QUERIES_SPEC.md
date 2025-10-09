# Sprint 9.1 Spec: Fast Task Query Commands

**Version:** 1.0.0
**Status:** DRAFT - Ready for Implementation
**Sprint:** 9.1 (Minor sprint - Polish)
**Estimated Effort:** 2-3 hours
**Dependencies:** Sprint 9 (MCP tools)
**Architecture:** CLI-First, Three-Tier Approach
**Date:** 2025-10-09

---

## Executive Summary

Sprint 9.1 addresses the "MCP slowness" problem for common task queries by implementing **instant CLI commands** that bypass the agent reasoning loop entirely. Users can now view their tasks in <100ms instead of waiting 5-8 seconds for Claude to orchestrate multiple MCP tools.

**Problem:**
```
You: "show me my urgent work tasks"
[Claude thinks... calls plorp_list_projects... thinks... calls plorp_list_project_tasks...
 thinks... filters... thinks... formats response...]
Total: 5-8 seconds 😫
```

**Solution:**
```bash
$ plorp tasks --urgent --project work
┌─────────────────────────────────────────────────┐
│ Urgent Work Tasks (3)                           │
├─────────────────────────────────────────────────┤
│ • Fix API auth bug (due: today)                 │
│ • Review PR #123 (due: 2025-10-10)             │
│ • Update client docs (due: 2025-10-11)         │
└─────────────────────────────────────────────────┘

Total: <100ms ✅
```

**What's New:**
- `plorp tasks` - List pending tasks with rich filtering
- `plorp focus` - Get/set focused project (already exists from Sprint 8)
- Slash commands: `/tasks`, `/urgent`, `/work-tasks`, `/today`, `/overdue`
- Optional MCP tools for programmatic access (deferred to future sprint if needed)

**User Experience:**
```bash
# Terminal workflows (instant)
plorp tasks                    # All pending tasks
plorp tasks --urgent           # Urgent only
plorp tasks --project work     # Work project tasks
plorp tasks --due today        # Due today
plorp tasks --overdue          # Overdue tasks

# Claude Desktop workflows (fast)
/tasks                         # Show all pending tasks
/urgent                        # Show urgent tasks
/today                         # Tasks due today
/overdue                       # Overdue tasks
```

**Performance Impact:**
- Terminal: <100ms (zero API calls)
- Slash commands: 1-2s (single API call to display)
- Natural language: Still works, but slower (5-8s for complex queries)

---

## Problem Statement

### Current User Pain

**Scenario:** User wants to check their task list in Claude Desktop

**Current Flow:**
1. User: "show me my urgent work tasks"
2. Claude Desktop → Anthropic API (200-400ms network)
3. Claude: "I need to list projects first" (500-1500ms generation)
4. API response → Desktop → MCP server: `plorp_list_projects()` (<50ms tool execution)
5. Desktop → Anthropic API with project list (200-400ms network)
6. Claude: "Now get tasks for 'work' project" (500-1500ms generation)
7. API response → Desktop → MCP server: `plorp_list_project_tasks('work')` (<50ms tool execution)
8. Desktop → Anthropic API with task list (200-400ms network)
9. Claude: "Filter urgent, format response" (500-1500ms generation)
10. API response → Desktop (200-400ms network)

**Total: 5-8 seconds** (99.7% agent reasoning, 0.3% tool execution)

### Why This Matters

**Frequency:**
- Users check tasks **multiple times per day**
- "Show me my tasks" is one of the **most common operations**
- Current 5-8s delay **feels broken** for such a simple query

**User Expectations:**
- Task list should feel **instant** (like `git status` or `ls`)
- No "thinking" required - it's a deterministic filter/display operation
- CLI tools should be **faster than the GUI** (not slower)

**Design Principle Violation:**
From `CLAUDE.md`:
> **Simplicity First**: Python scripts that call `task` CLI, not complex abstractions

The current flow violates this - we're forcing users through an agent for simple queries.

---

## Solution: Three-Tier Implementation

### Tier 1: CLI Commands (Instant - <100ms)

**Primary use case:** Terminal workflows, scripts, power users

```bash
plorp tasks [OPTIONS]

Options:
  --urgent              Show only urgent (priority:H) tasks
  --important           Show important (priority:M) tasks
  --project TEXT        Filter by project
  --due TEXT            Filter by due date (today, tomorrow, overdue, week)
  --limit INTEGER       Limit results (default: 50)
  --format TEXT         Output format (table, simple, json)
```

**Examples:**
```bash
plorp tasks                          # All pending tasks
plorp tasks --urgent                 # Urgent only
plorp tasks --project work           # Work project
plorp tasks --project work.api       # Specific subproject
plorp tasks --due today              # Due today
plorp tasks --overdue                # Overdue
plorp tasks --urgent --project work  # Combine filters
plorp tasks --format json            # JSON output for scripting
```

**Display Format (Rich Table):**
```
┌─────────────────────────────────────────────────────────────────┐
│ Tasks (8)                                                        │
├────────┬──────────────────────────────┬─────────┬──────────────┤
│ Pri    │ Description                  │ Project │ Due          │
├────────┼──────────────────────────────┼─────────┼──────────────┤
│ H [🔴] │ Fix API auth bug             │ work    │ today        │
│ H [🔴] │ Review PR #123               │ work    │ 2025-10-10   │
│ M [🟡] │ Update client docs           │ work    │ 2025-10-11   │
│   [  ] │ Refactor auth module         │ work    │ 2025-10-15   │
│   [  ] │ Buy groceries                │ home    │ today        │
└────────┴──────────────────────────────┴─────────┴──────────────┘
```

### Tier 2: Slash Commands (Fast - 1-2s)

**Primary use case:** Claude Desktop common workflows

Create `.claude/commands/`:

**`/tasks`** - Show all pending tasks
```markdown
Run the command: `plorp tasks`

Display the output in a formatted code block.
```

**`/urgent`** - Show urgent tasks
```markdown
Run the command: `plorp tasks --urgent`

Display the output showing urgent tasks only.
```

**`/today`** - Tasks due today
```markdown
Run the command: `plorp tasks --due today`

Display tasks due today.
```

**`/overdue`** - Overdue tasks
```markdown
Run the command: `plorp tasks --overdue`

Display overdue tasks that need attention.
```

**`/work-tasks`** - Work project tasks
```markdown
Run the command: `plorp tasks --project work`

Display all tasks in the work project.
```

### Tier 3: Natural Language (Flexible - 5-8s)

**Still works, but users know it's slower:**

```
You: "analyze my task distribution across projects and suggest what to focus on"
[Claude uses multiple MCP tools to analyze, takes 5-8s]
[This is EXPECTED for complex intelligence operations]
```

---

## Implementation Details

### Phase 1: CLI Command (1.5 hours)

**File:** `src/plorp/cli.py`

```python
@cli.command()
@click.option('--urgent', is_flag=True, help='Show only urgent (priority:H) tasks')
@click.option('--important', is_flag=True, help='Show important (priority:M) tasks')
@click.option('--project', help='Filter by project')
@click.option('--due', help='Filter by due date (today, tomorrow, overdue, week)')
@click.option('--limit', default=50, help='Limit number of results')
@click.option('--format', default='table', type=click.Choice(['table', 'simple', 'json']))
def tasks(urgent, important, project, due, limit, format):
    """
    List pending tasks with optional filters.

    Examples:
      plorp tasks                          # All pending tasks
      plorp tasks --urgent                 # Urgent only
      plorp tasks --project work           # Work project
      plorp tasks --due today              # Due today
      plorp tasks --overdue                # Overdue
      plorp tasks --urgent --project work  # Combine filters
    """
    try:
        config = load_config()

        # Build TaskWarrior filter
        filters = ['status:pending']

        if urgent:
            filters.append('priority:H')
        elif important:
            filters.append('priority:M')

        if project:
            filters.append(f'project:{project}')

        if due == 'today':
            filters.append('due:today')
        elif due == 'tomorrow':
            filters.append('due:tomorrow')
        elif due == 'overdue':
            filters.append('due.before:today')
        elif due == 'week':
            filters.append('due.before:eow')

        # Get tasks from TaskWarrior
        from plorp.integrations.taskwarrior import get_tasks
        tasks = get_tasks(filters)

        # Limit results
        if len(tasks) > limit:
            tasks = tasks[:limit]

        # Format output
        if format == 'json':
            import json
            click.echo(json.dumps(tasks, indent=2))
        elif format == 'simple':
            for task in tasks:
                pri = task.get('priority', ' ')
                desc = task.get('description', '')
                proj = task.get('project', '')
                click.echo(f"[{pri}] {desc} ({proj})")
        else:  # table
            from rich.console import Console
            from rich.table import Table

            console = Console()
            table = Table(title=f"Tasks ({len(tasks)})")

            table.add_column("Pri", width=6)
            table.add_column("Description", width=40)
            table.add_column("Project", width=15)
            table.add_column("Due", width=12)

            for task in tasks:
                pri = task.get('priority', '')
                pri_icon = '🔴' if pri == 'H' else '🟡' if pri == 'M' else '  '
                desc = task.get('description', '')
                proj = task.get('project', '')
                due = task.get('due', '')

                # Format due date
                if due:
                    from plorp.utils.dates import format_date
                    due = format_date(due, format='short')

                table.add_row(f"{pri} [{pri_icon}]", desc, proj, due)

            console.print(table)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
```

**New Utility Function:** `src/plorp/utils/dates.py`

```python
def format_date(date_str: str, format: str = 'short') -> str:
    """
    Format TaskWarrior date for display.

    Args:
        date_str: TaskWarrior date (20251009T000000Z)
        format: 'short', 'iso', or 'long'

    Returns:
        Formatted date string

    Examples:
        format_date('20251009T000000Z', 'short') -> 'today' or '2025-10-09'
        format_date('20251009T000000Z', 'iso') -> '2025-10-09'
        format_date('20251009T000000Z', 'long') -> 'Wednesday, October 9, 2025'
    """
    from datetime import datetime, date as dt_date

    if not date_str:
        return ''

    # Parse TaskWarrior date
    dt = datetime.strptime(date_str, '%Y%m%dT%H%M%SZ')
    today = dt_date.today()

    if format == 'short':
        if dt.date() == today:
            return 'today'
        elif dt.date() == today + timedelta(days=1):
            return 'tomorrow'
        elif dt.date() < today:
            return f'{(today - dt.date()).days}d ago'
        else:
            return dt.strftime('%Y-%m-%d')
    elif format == 'iso':
        return dt.strftime('%Y-%m-%d')
    else:  # long
        return dt.strftime('%A, %B %d, %Y')
```

### Phase 2: Slash Commands (30 minutes)

**Create files in `.claude/commands/`:**

**File:** `.claude/commands/tasks.md`
```markdown
Run the command: `plorp tasks`

Display the output showing all pending tasks.
```

**File:** `.claude/commands/urgent.md`
```markdown
Run the command: `plorp tasks --urgent`

Display urgent tasks only.
```

**File:** `.claude/commands/today.md`
```markdown
Run the command: `plorp tasks --due today`

Display tasks due today.
```

**File:** `.claude/commands/overdue.md`
```markdown
Run the command: `plorp tasks --overdue`

Display overdue tasks that need attention.
```

**File:** `.claude/commands/work-tasks.md`
```markdown
Run the command: `plorp tasks --project work`

Display all tasks in the work project.
```

### Phase 3: Tests (1 hour)

**File:** `tests/test_cli_tasks.py`

```python
"""
Tests for the plorp tasks command.
"""
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
import pytest

from plorp.cli import cli


@pytest.fixture
def sample_tasks():
    """Sample task data for testing."""
    return [
        {
            'uuid': 'abc-123',
            'description': 'Fix bug',
            'priority': 'H',
            'project': 'work',
            'due': '20251009T000000Z',
            'status': 'pending'
        },
        {
            'uuid': 'def-456',
            'description': 'Review PR',
            'priority': 'M',
            'project': 'work',
            'due': '20251010T000000Z',
            'status': 'pending'
        },
        {
            'uuid': 'ghi-789',
            'description': 'Buy groceries',
            'project': 'home',
            'due': '20251009T000000Z',
            'status': 'pending'
        }
    ]


@patch('plorp.cli.load_config')
@patch('plorp.cli.get_tasks')
def test_tasks_all_pending(mock_get_tasks, mock_load_config, sample_tasks):
    """Test tasks command shows all pending tasks."""
    mock_load_config.return_value = {'vault_path': '/tmp/vault'}
    mock_get_tasks.return_value = sample_tasks

    runner = CliRunner()
    result = runner.invoke(cli, ['tasks'])

    assert result.exit_code == 0
    assert 'Fix bug' in result.output
    assert 'Review PR' in result.output
    assert 'Buy groceries' in result.output
    mock_get_tasks.assert_called_once_with(['status:pending'])


@patch('plorp.cli.load_config')
@patch('plorp.cli.get_tasks')
def test_tasks_urgent_only(mock_get_tasks, mock_load_config, sample_tasks):
    """Test tasks --urgent shows only urgent tasks."""
    mock_load_config.return_value = {'vault_path': '/tmp/vault'}
    mock_get_tasks.return_value = [sample_tasks[0]]  # Only urgent task

    runner = CliRunner()
    result = runner.invoke(cli, ['tasks', '--urgent'])

    assert result.exit_code == 0
    assert 'Fix bug' in result.output
    assert 'Review PR' not in result.output
    mock_get_tasks.assert_called_once_with(['status:pending', 'priority:H'])


@patch('plorp.cli.load_config')
@patch('plorp.cli.get_tasks')
def test_tasks_project_filter(mock_get_tasks, mock_load_config, sample_tasks):
    """Test tasks --project filters by project."""
    mock_load_config.return_value = {'vault_path': '/tmp/vault'}
    mock_get_tasks.return_value = sample_tasks[:2]  # Work tasks

    runner = CliRunner()
    result = runner.invoke(cli, ['tasks', '--project', 'work'])

    assert result.exit_code == 0
    assert 'Fix bug' in result.output
    assert 'Review PR' in result.output
    assert 'Buy groceries' not in result.output
    mock_get_tasks.assert_called_once_with(['status:pending', 'project:work'])


@patch('plorp.cli.load_config')
@patch('plorp.cli.get_tasks')
def test_tasks_due_today(mock_get_tasks, mock_load_config, sample_tasks):
    """Test tasks --due today filters by due date."""
    mock_load_config.return_value = {'vault_path': '/tmp/vault'}
    mock_get_tasks.return_value = [sample_tasks[0], sample_tasks[2]]

    runner = CliRunner()
    result = runner.invoke(cli, ['tasks', '--due', 'today'])

    assert result.exit_code == 0
    mock_get_tasks.assert_called_once_with(['status:pending', 'due:today'])


@patch('plorp.cli.load_config')
@patch('plorp.cli.get_tasks')
def test_tasks_overdue(mock_get_tasks, mock_load_config, sample_tasks):
    """Test tasks --overdue shows overdue tasks."""
    mock_load_config.return_value = {'vault_path': '/tmp/vault'}
    mock_get_tasks.return_value = [sample_tasks[0]]

    runner = CliRunner()
    result = runner.invoke(cli, ['tasks', '--overdue'])

    assert result.exit_code == 0
    mock_get_tasks.assert_called_once_with(['status:pending', 'due.before:today'])


@patch('plorp.cli.load_config')
@patch('plorp.cli.get_tasks')
def test_tasks_json_format(mock_get_tasks, mock_load_config, sample_tasks):
    """Test tasks --format json outputs JSON."""
    mock_load_config.return_value = {'vault_path': '/tmp/vault'}
    mock_get_tasks.return_value = sample_tasks

    runner = CliRunner()
    result = runner.invoke(cli, ['tasks', '--format', 'json'])

    assert result.exit_code == 0
    import json
    output = json.loads(result.output)
    assert len(output) == 3
    assert output[0]['description'] == 'Fix bug'


@patch('plorp.cli.load_config')
@patch('plorp.cli.get_tasks')
def test_tasks_simple_format(mock_get_tasks, mock_load_config, sample_tasks):
    """Test tasks --format simple outputs simple format."""
    mock_load_config.return_value = {'vault_path': '/tmp/vault'}
    mock_get_tasks.return_value = sample_tasks

    runner = CliRunner()
    result = runner.invoke(cli, ['tasks', '--format', 'simple'])

    assert result.exit_code == 0
    assert '[H] Fix bug (work)' in result.output
    assert '[M] Review PR (work)' in result.output


@patch('plorp.cli.load_config')
@patch('plorp.cli.get_tasks')
def test_tasks_combine_filters(mock_get_tasks, mock_load_config, sample_tasks):
    """Test combining multiple filters."""
    mock_load_config.return_value = {'vault_path': '/tmp/vault'}
    mock_get_tasks.return_value = [sample_tasks[0]]

    runner = CliRunner()
    result = runner.invoke(cli, ['tasks', '--urgent', '--project', 'work'])

    assert result.exit_code == 0
    mock_get_tasks.assert_called_once_with(['status:pending', 'priority:H', 'project:work'])


@patch('plorp.cli.load_config')
@patch('plorp.cli.get_tasks')
def test_tasks_limit(mock_get_tasks, mock_load_config, sample_tasks):
    """Test tasks --limit restricts results."""
    mock_load_config.return_value = {'vault_path': '/tmp/vault'}
    mock_get_tasks.return_value = sample_tasks

    runner = CliRunner()
    result = runner.invoke(cli, ['tasks', '--limit', '2'])

    assert result.exit_code == 0
    # Should only show first 2 tasks
    assert result.output.count('│') >= 2  # At least 2 rows in table


@patch('plorp.cli.load_config')
@patch('plorp.cli.get_tasks')
def test_tasks_empty_result(mock_get_tasks, mock_load_config):
    """Test tasks command with no results."""
    mock_load_config.return_value = {'vault_path': '/tmp/vault'}
    mock_get_tasks.return_value = []

    runner = CliRunner()
    result = runner.invoke(cli, ['tasks'])

    assert result.exit_code == 0
    assert 'Tasks (0)' in result.output


def test_format_date_today():
    """Test format_date for today's date."""
    from plorp.utils.dates import format_date
    from datetime import datetime

    today = datetime.now().strftime('%Y%m%dT000000Z')
    result = format_date(today, 'short')
    assert result == 'today'


def test_format_date_iso():
    """Test format_date ISO format."""
    from plorp.utils.dates import format_date

    result = format_date('20251009T000000Z', 'iso')
    assert result == '2025-10-09'


def test_format_date_empty():
    """Test format_date with empty string."""
    from plorp.utils.dates import format_date

    result = format_date('', 'short')
    assert result == ''
```

---

## Success Criteria

### Functional Requirements

- [ ] `plorp tasks` command exists and shows all pending tasks
- [ ] `--urgent` flag filters to priority:H tasks
- [ ] `--important` flag filters to priority:M tasks
- [ ] `--project` option filters by project
- [ ] `--due` option filters by due date (today, tomorrow, overdue, week)
- [ ] `--limit` option restricts result count
- [ ] `--format` option supports table, simple, json
- [ ] Slash commands work in Claude Desktop (`/tasks`, `/urgent`, `/today`, `/overdue`, `/work-tasks`)
- [ ] Rich table output looks good (colors, emojis, alignment)
- [ ] JSON output is valid and complete
- [ ] Simple format is readable and concise

### Performance Requirements

- [ ] CLI command completes in <100ms for typical task lists (10-50 tasks)
- [ ] CLI command completes in <500ms for large task lists (500+ tasks)
- [ ] Slash commands display results in 1-2 seconds
- [ ] No network calls to Anthropic API for CLI usage
- [ ] TaskWarrior filter performance is acceptable

### Testing Requirements

- [ ] 12+ tests covering all filter combinations
- [ ] Test all output formats (table, simple, json)
- [ ] Test empty results
- [ ] Test error handling (TaskWarrior not installed, etc.)
- [ ] No regressions in existing tests

### Documentation Requirements

- [ ] CLI help text is clear (`plorp tasks --help`)
- [ ] Slash command files created with descriptions
- [ ] Update `CLAUDE.md` with performance guidance
- [ ] Update `MCP_ARCHITECTURE_GUIDE.md` with this example
- [ ] Add section to `README.md` or `MCP_USER_MANUAL.md`

---

## Dependencies

### Required from Previous Sprints

**Sprint 1-2 (Core Workflows):**
- TaskWarrior integration (`integrations/taskwarrior.py`)
- `get_tasks()` function

**Sprint 8 (Project Management):**
- Project filtering logic
- `plorp focus` command (already exists)

**Sprint 9 (General Note Management):**
- Rich table formatting patterns
- CLI command structure

### External Dependencies

**Already Present:**
- `rich` library (for beautiful tables)
- `click` library (for CLI)
- TaskWarrior 3.4.1+

---

## Technical Design

### Architecture

```
User Input → CLI Parser → Filter Builder → TaskWarrior Query → Format Output
     ↓           ↓              ↓                ↓                    ↓
  "plorp      Parse          Build          subprocess         Rich Table
   tasks      options        TW             task export        or JSON
   --urgent"  into dict      filter         (instant)          (pretty)
```

**No MCP, No API, No Agent - Just Direct Query**

### TaskWarrior Filter Translation

| CLI Option | TaskWarrior Filter |
|------------|-------------------|
| `--urgent` | `priority:H` |
| `--important` | `priority:M` |
| `--project work` | `project:work` |
| `--due today` | `due:today` |
| `--due tomorrow` | `due:tomorrow` |
| `--due overdue` | `due.before:today` |
| `--due week` | `due.before:eow` |

All filters are combined with AND logic.

### Output Formats

**Table (default):**
- Uses `rich.table.Table`
- Color-coded priority (red=H, yellow=M)
- Emoji indicators (🔴=urgent, 🟡=important)
- Truncated descriptions (40 chars)
- Human-readable dates ("today", "tomorrow", "3d ago")

**Simple:**
- Plain text, one line per task
- Format: `[Priority] Description (Project)`
- Easy to grep/awk/sed

**JSON:**
- Full task objects from TaskWarrior
- Suitable for scripting and automation
- Can pipe to `jq` for complex queries

---

## Implementation Phases

### Phase 1: Core CLI Command (1.5 hours)

**Tasks:**
1. Add `tasks` command to `src/plorp/cli.py`
2. Implement filter building logic
3. Add `format_date()` to `src/plorp/utils/dates.py`
4. Implement table formatting with rich
5. Implement simple and JSON formats
6. Manual testing

**Deliverables:**
- Working `plorp tasks` command
- All filter options functional
- All output formats working

### Phase 2: Slash Commands (30 minutes)

**Tasks:**
1. Create `.claude/commands/tasks.md`
2. Create `.claude/commands/urgent.md`
3. Create `.claude/commands/today.md`
4. Create `.claude/commands/overdue.md`
5. Create `.claude/commands/work-tasks.md`
6. Test in Claude Desktop

**Deliverables:**
- 5 slash commands working in Claude Desktop

### Phase 3: Tests (1 hour)

**Tasks:**
1. Create `tests/test_cli_tasks.py`
2. Write tests for all filter combinations
3. Write tests for all output formats
4. Write tests for edge cases (empty, errors)
5. Run full test suite

**Deliverables:**
- 12+ passing tests
- 100% code coverage for new code
- Zero regressions

### Phase 4: Documentation (30 minutes)

**Tasks:**
1. Update `CLAUDE.md` with performance guidance
2. Add example to `MCP_ARCHITECTURE_GUIDE.md`
3. Update `MCP_USER_MANUAL.md` with slash commands
4. Add section to README (optional)

**Deliverables:**
- Documentation complete
- Examples added

---

## User Stories

### Story 1: Quick Task Check

**As a** plorp user
**I want** to check my task list instantly
**So that** I can quickly see what needs attention without waiting

**Acceptance Criteria:**
- Run `plorp tasks` and see results in <100ms
- See all pending tasks in a readable format
- See priority, project, and due date at a glance

### Story 2: Focus on Urgent Work

**As a** plorp user
**I want** to see only urgent work tasks
**So that** I can focus on what's critical

**Acceptance Criteria:**
- Run `plorp tasks --urgent --project work`
- See only priority:H tasks in work project
- Results appear instantly (<100ms)

### Story 3: Daily Planning in Claude Desktop

**As a** Claude Desktop user
**I want** slash commands for common task queries
**So that** I can quickly check tasks without typing long prompts

**Acceptance Criteria:**
- Type `/urgent` and see urgent tasks in 1-2 seconds
- Type `/today` and see tasks due today
- Type `/overdue` and see overdue tasks
- No need to wait 5-8 seconds for agent reasoning

### Story 4: Scripting and Automation

**As a** power user
**I want** JSON output for task queries
**So that** I can pipe to other tools and scripts

**Acceptance Criteria:**
- Run `plorp tasks --format json` and get valid JSON
- Can pipe to `jq` for complex queries
- Can use in shell scripts for automation

---

## Performance Targets

| Operation | Target | Measured |
|-----------|--------|----------|
| `plorp tasks` (10 tasks) | <100ms | TBD |
| `plorp tasks` (100 tasks) | <200ms | TBD |
| `plorp tasks` (500 tasks) | <500ms | TBD |
| Slash command `/tasks` | 1-2s | TBD |
| Natural language "show tasks" | 5-8s | Known |

---

## Risk Assessment

### Low Risk

**Why:**
- Simple feature, no complex logic
- Uses existing TaskWarrior integration
- No state changes, read-only operation
- No MCP changes, pure CLI addition

**Mitigation:**
- Comprehensive tests
- Manual testing on various task list sizes
- Performance measurement

---

## Future Enhancements (Out of Scope)

**Sprint 9.2 or later:**

1. **MCP Query Tools** - Programmatic access for complex workflows
   - `plorp_query_tasks(filters: dict)`
   - Still slower than CLI, but faster than multi-tool orchestration

2. **Saved Filters** - User-defined task views
   - `plorp tasks --view my-urgent-work`
   - Stored in config: `~/.config/plorp/views.yaml`

3. **Interactive Mode** - TUI for task exploration
   - `plorp tasks --interactive`
   - Arrow keys to navigate, enter to view details

4. **Task Counts** - Quick summary without full list
   - `plorp tasks --count`
   - Output: `Pending: 42 | Urgent: 5 | Due today: 3`

5. **Custom Columns** - User-defined table columns
   - `plorp tasks --columns priority,description,tags,due`

---

## Version Management

**Current Version:** 1.5.0 (Sprint 9)
**Next Version:** 1.5.1 (Sprint 9.1 - minor sprint, PATCH bump)

**Files to Update:**
- `src/plorp/__init__.py` - `__version__ = "1.5.1"`
- `pyproject.toml` - `version = "1.5.1"`
- `tests/test_cli.py` - Update version assertion
- `tests/test_smoke.py` - Update version assertion

---

## PM/Architect Q&A

### Q1: Why not add MCP tools instead of CLI commands?

**A:** MCP tools still require 2-3 seconds for agent reasoning and network round trips. The whole point is to bypass the agent for frequent, deterministic queries. CLI is instant (<100ms).

We can add MCP query tools in a future sprint if there's a use case for programmatic access, but CLI solves the immediate user pain.

---

### Q2: Should we update the existing MCP project tools to be faster?

**A:** No, they're already fast (tool execution <50ms). The slowness is agent orchestration, not tool execution. The solution is to provide a faster path (CLI) for common operations, not to "speed up" already-fast tools.

---

### Q3: What about users who only use Claude Desktop, not terminal?

**A:** Slash commands! They call the fast CLI commands and display results in Claude Desktop. Still faster than natural language (1-2s vs 5-8s).

Users get:
- Instant CLI for terminal workflows
- Fast slash commands for Claude Desktop workflows
- Natural language still works for complex queries

---

### Q4: How does this relate to the Three-Tier Architecture?

**A:** This is a **perfect example** of the three-tier approach in action:

**Tier 1 (CLI):** Instant, deterministic, no AI needed → `plorp tasks --urgent`
**Tier 2 (Slash):** Reliable, tested workflows → `/urgent`
**Tier 3 (Natural):** Flexible, intelligent → "analyze my task distribution"

Each tier has its use case. This sprint adds Tier 1 and Tier 2 for task queries.

---

### Q5: Will this break existing workflows?

**A:** No, 100% additive. All existing commands and MCP tools remain unchanged. This just adds a faster path for common operations.

---

### Q6: What about focus workflow? Doesn't `plorp focus` already exist?

**A:** Yes! `plorp focus` was added in Sprint 8 for CLI and MCP. This sprint adds `plorp tasks` as the complement - `focus` sets context, `tasks` queries based on context.

Example workflow:
```bash
plorp focus work.api-rewrite    # Set context
plorp tasks --urgent            # See urgent tasks in focused project
```

---

### Q7: Should we add filtering by tags?

**A:** Not in Sprint 9.1 (keep scope small), but easy to add later:
```bash
plorp tasks --tag bug
plorp tasks --tag +urgent -bug
```

Add in Sprint 9.2 if users request it.

---

### Q8: What about Windows compatibility?

**A:** The `rich` library works cross-platform, and we're using `subprocess` for TaskWarrior (already cross-platform). Should work on Windows if TaskWarrior is installed.

Manual testing on Windows recommended but not blocking.

---

### Q9: How do we handle very large task lists (1000+ tasks)?

**A:** The `--limit` option (default 50) prevents overwhelming output. For power users who want more, they can increase the limit or use `--format json | jq`.

Performance target: <500ms for 500+ tasks. If slower, we can add pagination in future sprint.

---

### Q10: Should we add sorting options?

**A:** Not in 9.1 (keep scope small). TaskWarrior already returns tasks in a reasonable order (urgent first, then by due date). If users request custom sorting, add in 9.2:
```bash
plorp tasks --sort due
plorp tasks --sort priority
```

---

## Success Metrics

**Must Have:**
- [ ] CLI command completes in <100ms
- [ ] All filter options work correctly
- [ ] Slash commands work in Claude Desktop
- [ ] 12+ tests passing
- [ ] Zero regressions

**Nice to Have:**
- [ ] Performance measurements documented
- [ ] User feedback positive
- [ ] Reduced "show me tasks" natural language queries (users use slash commands instead)

---

## Implementation Checklist

### Before Starting
- [ ] Read Sprint 9.1 spec
- [ ] Confirm Sprint 9 is complete and signed off
- [ ] Review existing `plorp focus` implementation (Sprint 8)

### Phase 1: CLI Command
- [ ] Add `tasks()` command to `src/plorp/cli.py`
- [ ] Implement filter building
- [ ] Add `format_date()` to `src/plorp/utils/dates.py`
- [ ] Implement table format (rich)
- [ ] Implement simple format
- [ ] Implement JSON format
- [ ] Manual testing (10 tasks, 100 tasks, various filters)

### Phase 2: Slash Commands
- [ ] Create `.claude/commands/tasks.md`
- [ ] Create `.claude/commands/urgent.md`
- [ ] Create `.claude/commands/today.md`
- [ ] Create `.claude/commands/overdue.md`
- [ ] Create `.claude/commands/work-tasks.md`
- [ ] Test each command in Claude Desktop

### Phase 3: Tests
- [ ] Create `tests/test_cli_tasks.py`
- [ ] Test all filter combinations
- [ ] Test all output formats
- [ ] Test edge cases (empty, errors, large lists)
- [ ] Run full test suite (should be 500+ passing)

### Phase 4: Documentation
- [ ] Update `CLAUDE.md` with performance guidance
- [ ] Add example to `MCP_ARCHITECTURE_GUIDE.md`
- [ ] Update `MCP_USER_MANUAL.md` with slash commands
- [ ] Update version in `__init__.py` and `pyproject.toml`
- [ ] Update test version assertions

### Final
- [ ] Performance measurements documented
- [ ] All tests passing (500+)
- [ ] Ready for PM review

---

## Final Status

**Sprint 9.1: DRAFT**

**Ready for Implementation:** YES

**Estimated Time:** 2-3 hours (actual time may vary)

**Next Steps:**
1. Lead engineer reviews spec and confirms scope
2. Implementation begins with Phase 1
3. PM reviews and signs off when complete

---

**Spec Version:** 1.0.0
**Date:** 2025-10-09
**Author:** PM/Architect Instance (Session 14)
**Status:** Ready for Lead Engineer Review

---

## Lead Engineer Clarifying Questions

**Status:** PENDING ANSWERS
**Date Added:** 2025-10-09
**Engineer:** Lead Engineer Instance (Session XX)

### Q1: Date Utility Import
**Question:** The `format_date()` function in `src/plorp/utils/dates.py` (line 340) uses `timedelta` but doesn't import it. Should the import block include `from datetime import datetime, date as dt_date, timedelta`?

**Impact:** Compilation error without import
**Severity:** High (blocks implementation)
**Suggested Answer:** Yes, add `timedelta` to imports

---

### Q2: TaskWarrior Not Installed Error Handling
**Question:** What should `plorp tasks` output if TaskWarrior is not installed or returns an error? Should we:
- (A) Show friendly error message and exit with code 1
- (B) Show empty table with warning
- (C) Show error and suggest installation instructions

**Impact:** User experience when TaskWarrior missing
**Severity:** Medium
**Suggested Answer:** (A) - Clear error message pointing to installation docs

---

### Q3: Terminal Compatibility for Emojis
**Question:** Line 287 uses emoji indicators (🔴, 🟡). Should we:
- (A) Always show emojis (assume UTF-8 terminal)
- (B) Detect terminal capabilities and fall back to ASCII
- (C) Add config option for emoji display

**Impact:** Users on non-UTF-8 terminals see garbage characters
**Severity:** Low (most modern terminals support UTF-8)
**Suggested Answer:** (A) for Sprint 9.1, document UTF-8 requirement

---

### Q4: Invalid Filter Combinations
**Question:** Are there any invalid combinations of filters we should prevent or warn about? For example:
- `--urgent --important` (mutually exclusive?)
- `--due today --overdue` (contradictory?)

**Impact:** User confusion if filters conflict
**Severity:** Low
**Suggested Answer:** Allow all combinations (user responsibility), document behavior

---

### Q5: Testing Strategy for TaskWarrior Integration
**Question:** Should we:
- (A) Mock `get_tasks()` in all tests (as shown in spec)
- (B) Use real TaskWarrior with test data
- (C) Both (unit tests mock, integration tests real)

**Impact:** Test reliability and coverage
**Severity:** Medium
**Suggested Answer:** (A) for Sprint 9.1 - All tests mock for speed/isolation

---

### Q6: Existing `get_tasks()` Function Signature
**Question:** The spec assumes `get_tasks(filters: list[str])` exists in `integrations/taskwarrior.py`. Can you confirm:
- Exact function signature?
- Does it return list of dict (as assumed)?
- What exception types does it raise?

**Impact:** Integration correctness
**Severity:** High (blocks implementation)
**Action Required:** Verify in codebase before implementing

---

### Q7: Rich Library Dependency
**Question:** Is `rich` already in `pyproject.toml` dependencies? If not, should we:
- (A) Add it as required dependency
- (B) Add it as optional dependency
- (C) Fall back to basic output if not installed

**Impact:** Installation requirements
**Severity:** Medium
**Action Required:** Check `pyproject.toml` and confirm approach

---

### Q8: Slash Command Testing
**Question:** How should we verify slash commands work? The spec says "Test in Claude Desktop" (line 756) but no automated tests. Should we:
- (A) Manual testing only (document in handoff)
- (B) Add E2E tests that verify slash command files exist
- (C) Defer slash command testing to PM review

**Impact:** Quality assurance completeness
**Severity:** Low (slash commands are simple file creation)
**Suggested Answer:** (A) - Manual test each one, document results in handoff

---

### Q9: Performance Measurement Implementation
**Question:** Should we add timing/profiling code to verify <100ms performance target, or just rely on manual testing with `time` command? If adding code:
- Where should timing code live?
- Should it be always-on or debug-only?
- How do we report results?

**Impact:** Success criteria verification
**Severity:** Low (can manually test with `time plorp tasks`)
**Suggested Answer:** Use `time` command for manual verification, no embedded timing

---

### Q10: `plorp focus` Integration Details
**Question:** Line 956 shows:
```bash
plorp focus work.api-rewrite    # Set context
plorp tasks --urgent            # See urgent tasks in focused project
```

Should `plorp tasks` automatically respect focused project, or is this showing a future feature? If automatic:
- Where is focus stored?
- How do we read it?
- Does it override `--project` flag?

**Impact:** Feature completeness and user expectations
**Severity:** Medium
**Suggested Answer:** Clarify - I believe this is showing manual workflow, not automatic filtering

---

### Q11: Version Bump Timing
**Question:** The spec says update version in Phase 4 (Documentation), but tests in Phase 3 will fail if they check version (test_cli.py, test_smoke.py expect 1.5.0, not 1.5.1). Should we:
- (A) Update version in Phase 1 (before tests)
- (B) Update tests to expect 1.5.1 in Phase 3
- (C) Update version and tests together in Phase 4

**Impact:** Test execution order
**Severity:** Low
**Suggested Answer:** (C) - Update version + test assertions together in Phase 4

---

### Q12: `.claude/commands/` Directory Creation
**Question:** Should Phase 2 include creating the `.claude/commands/` directory if it doesn't exist? Or assume it already exists from previous work?

**Impact:** Slash command file creation
**Severity:** Low
**Action Required:** Check if directory exists, create if needed

---

### Q13: TaskWarrior Export vs. Custom Formatting
**Question:** The spec uses `get_tasks(filters)` which presumably calls `task export`. Do we need any additional formatting/parsing of TaskWarrior's JSON output, or can we use it directly?

**Impact:** Implementation complexity
**Severity:** Low
**Action Required:** Verify existing `get_tasks()` returns ready-to-use format

---

### Q14: Error Messages for Empty Results
**Question:** Line 583 shows `Tasks (0)` for empty results. Should we add a helpful message like "No tasks found matching filters" or keep it minimal?

**Impact:** User experience
**Severity:** Low
**Suggested Answer:** Keep minimal for 9.1, users can infer empty list

---

### Q15: Due Date Edge Cases
**Question:** For `--due overdue`, should we show:
- (A) Tasks with due date in the past
- (B) Tasks with due date in the past AND not completed
- (C) Same as (B) but also include tasks due today

**Impact:** User expectations for "overdue"
**Severity:** Low
**Suggested Answer:** (A) - `due.before:today` handles this (TaskWarrior interprets correctly)

---

### Q16: JSON Format Output - Full Object or Filtered?
**Question:** Line 265 shows `json.dumps(tasks, indent=2)` which outputs full TaskWarrior objects. Should we:
- (A) Output full objects (all fields)
- (B) Filter to relevant fields (description, priority, project, due, uuid)
- (C) Make it configurable

**Impact:** JSON output size and usability
**Severity:** Low
**Suggested Answer:** (A) - Full objects for maximum flexibility

---

### Q17: CLI Import Placement
**Question:** Line 256 shows `from plorp.integrations.taskwarrior import get_tasks` inside the function. Should this be:
- (A) At top of file (standard practice)
- (B) Inside function (lazy import for performance)
- (C) Either is fine

**Impact:** Code style consistency
**Severity:** Very Low
**Suggested Answer:** (A) - Import at top of file for consistency

---

### Q18: Table Width and Truncation
**Question:** Line 282 sets `Description` column width to 40 chars. Should we:
- (A) Hard-code 40 chars (as shown)
- (B) Auto-detect terminal width and adjust
- (C) Make configurable

**Impact:** User experience on wide/narrow terminals
**Severity:** Low
**Suggested Answer:** (A) for 9.1 - Hard-code, add auto-width in future sprint if requested

---

### Q19: Priority Display Consistency
**Question:** What should display for tasks with no priority? Spec shows `' '` (line 286). Should we:
- (A) Show empty space: `[  ]`
- (B) Show 'L' for low: `[L]`
- (C) Show '-' or 'N': `[-]` or `[N]`

**Impact:** User understanding of task priorities
**Severity:** Low
**Suggested Answer:** (A) - Empty space is clearest for "no priority set"

---

### Q20: Documentation Updates - Where Exactly?
**Question:** Phase 4 says "Update CLAUDE.md with performance guidance" (line 777). What specific sections should be updated:
- Add new section "Performance Optimization"?
- Update "Development Commands" section?
- Update "Core Workflows" section?

**Impact:** Documentation clarity
**Severity:** Low
**Action Required:** PM should specify exact sections to update

---

**Summary of Blocking Questions:**
- Q1: Missing import (timedelta) - HIGH PRIORITY
- Q6: Verify `get_tasks()` signature - HIGH PRIORITY
- Q7: Verify `rich` dependency - MEDIUM PRIORITY

**Summary of Clarifications:**
- 17 low-severity questions about implementation details
- Most have suggested answers that can be confirmed or adjusted

**Next Steps:**
1. PM/User reviews questions and provides answers
2. Spec updated with confirmed answers
3. Lead Engineer proceeds with implementation
