# Sprint 1: TaskWarrior Integration Layer

**Sprint ID:** SPRINT-1
**Status:** Ready for Implementation
**Dependencies:** Sprint 0 complete
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

Create a comprehensive Python wrapper around the TaskWarrior CLI that provides clean, testable interfaces for all task operations needed by plorp. This integration layer will be the foundation for all plorp workflows.

### What You're Building

A complete TaskWarrior integration module with:
- Subprocess wrapper for TaskWarrior CLI
- JSON parsing for task export data
- Query functions for filtering tasks (overdue, due today, recurring)
- CRUD operations (create, read, update, delete tasks)
- Task modification functions (mark done, defer, set priority)
- Annotation management for task-note linking
- Comprehensive error handling
- 90%+ test coverage with mocked subprocess calls

### What You're NOT Building

- Direct SQLite database access (future optimization)
- TaskWarrior configuration management
- UI or CLI commands (those are in other sprints)
- Obsidian integration (that's Sprint 4)

---

## Engineering Handoff Prompt

```
You are implementing Sprint 1 for plorp, a workflow automation tool for TaskWarrior and Obsidian.

PROJECT CONTEXT:
- plorp is a Python CLI tool that bridges TaskWarrior (task management) and Obsidian (note-taking)
- This is Sprint 1: You're creating the TaskWarrior integration layer
- Sprint 0 is complete: Project structure, test infrastructure, and fixtures are ready

YOUR TASK:
1. Read the full Sprint 1 specification: /Users/jsd/Documents/plorp/Docs/sprints/SPRINT_1_SPEC.md
2. Implement src/plorp/integrations/taskwarrior.py with 12+ functions
3. Write comprehensive tests in tests/test_integrations/test_taskwarrior.py
4. Follow TDD: Write tests BEFORE implementation for each function
5. Mock all subprocess calls - do NOT require TaskWarrior to be installed
6. Achieve 90%+ test coverage
7. Document your work in the Completion Report section

IMPORTANT REQUIREMENTS:
- TDD approach: Write test first, then implement function, then verify
- Mock subprocess.run() for all TaskWarrior interactions
- Use fixture data from tests/fixtures/taskwarrior_export.json
- All functions must have type hints
- All functions must have docstrings
- Handle errors gracefully (task not found, invalid filter, etc.)
- File must start with ABOUTME comments

WORKING DIRECTORY: /Users/jsd/Documents/plorp/

CLARIFYING QUESTIONS:
If anything is unclear, add your questions to the Q&A section of this spec document and stop. The PM/Architect will answer them before you continue.

COMPLETION:
When done, fill out the Completion Report Template section in this document with details of your implementation.
```

---

## Technical Specifications

### Module Overview

**File:** `src/plorp/integrations/taskwarrior.py`

**Purpose:** Provide a clean Python API for TaskWarrior operations using subprocess calls to the `task` CLI.

**Dependencies:**
- `subprocess` - Execute TaskWarrior commands
- `json` - Parse TaskWarrior export format
- `typing` - Type hints for function signatures

### Complete Function Specifications

#### 1. `run_task_command(args: List[str], capture: bool = True) -> subprocess.CompletedProcess`

```python
# ABOUTME: TaskWarrior CLI integration layer - provides Python wrapper around task command
# ABOUTME: All functions use subprocess to call TaskWarrior and parse JSON output for type safety
"""
TaskWarrior CLI integration.

Provides Python wrappers around TaskWarrior command-line operations.
All functions use subprocess to execute 'task' commands and parse JSON output.
"""
import subprocess
import json
from typing import List, Dict, Optional
from datetime import date


def run_task_command(args: List[str], capture: bool = True) -> subprocess.CompletedProcess:
    """
    Execute a TaskWarrior command and return the result.

    Args:
        args: Command arguments to pass to 'task' (e.g., ['export', 'status:pending'])
        capture: If True, capture stdout/stderr; if False, show to user

    Returns:
        subprocess.CompletedProcess with returncode, stdout, stderr

    Example:
        >>> result = run_task_command(['export', 'status:pending'])
        >>> tasks = json.loads(result.stdout)
    """
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
```

**Tests to write:**
- Test command construction with various args
- Test capture=True returns stdout/stderr
- Test capture=False doesn't capture output
- Mock subprocess.run to verify correct calls

---

#### 2. `get_tasks(filter_args: List[str]) -> List[Dict]`

```python
def get_tasks(filter_args: List[str]) -> List[Dict]:
    """
    Get tasks matching filter, returned as list of dicts.

    Args:
        filter_args: TaskWarrior filter arguments (e.g., ['status:pending', 'due:today'])

    Returns:
        List of task dictionaries. Empty list if no tasks match or error occurs.
        Each dict contains TaskWarrior fields: uuid, description, status, due, etc.

    Example:
        >>> tasks = get_tasks(['status:pending', 'project:home'])
        >>> for task in tasks:
        ...     print(task['description'], task['uuid'])
    """
    args = filter_args + ['export']
    result = run_task_command(args)

    if result.returncode != 0:
        return []

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
```

**Tests to write:**
- Test with valid filter returns parsed JSON
- Test with invalid filter returns empty list
- Test with empty result returns empty list
- Test JSON parsing error returns empty list
- Verify 'export' is appended to filter args

---

#### 3. `get_overdue_tasks() -> List[Dict]`

```python
def get_overdue_tasks() -> List[Dict]:
    """
    Get all overdue tasks (due date before today).

    Returns:
        List of overdue task dictionaries.

    Example:
        >>> overdue = get_overdue_tasks()
        >>> print(f"{len(overdue)} tasks are overdue")
    """
    return get_tasks(['status:pending', 'due.before:today'])
```

**Tests to write:**
- Test correct filter arguments passed
- Test returns expected task list
- Mock get_tasks and verify call

---

#### 4. `get_due_today() -> List[Dict]`

```python
def get_due_today() -> List[Dict]:
    """
    Get tasks due today.

    Returns:
        List of task dictionaries due today.

    Example:
        >>> due_today = get_due_today()
        >>> for task in due_today:
        ...     print(f"Due today: {task['description']}")
    """
    return get_tasks(['status:pending', 'due:today'])
```

**Tests to write:**
- Test correct filter arguments
- Test returns task list
- Verify 'status:pending' and 'due:today' used

---

#### 5. `get_recurring_today() -> List[Dict]`

```python
def get_recurring_today() -> List[Dict]:
    """
    Get recurring tasks due today.

    Returns:
        List of recurring task dictionaries due today.

    Example:
        >>> recurring = get_recurring_today()
        >>> for task in recurring:
        ...     print(f"Recurring: {task['description']}")
    """
    return get_tasks(['status:pending', 'recur.any:', 'due:today'])
```

**Tests to write:**
- Test correct filter for recurring tasks
- Verify 'recur.any:' is included in filter

---

#### 6. `get_task_info(uuid: str) -> Optional[Dict]`

```python
def get_task_info(uuid: str) -> Optional[Dict]:
    """
    Get full information for a specific task by UUID.

    Args:
        uuid: Task UUID (full or short form)

    Returns:
        Task dictionary if found, None if not found.

    Example:
        >>> task = get_task_info('abc-123')
        >>> if task:
        ...     print(task['description'])
    """
    tasks = get_tasks([uuid])
    return tasks[0] if tasks else None
```

**Tests to write:**
- Test with valid UUID returns task
- Test with invalid UUID returns None
- Test with empty result returns None

---

#### 7. `create_task(description: str, project: Optional[str] = None, due: Optional[str] = None, priority: Optional[str] = None, tags: Optional[List[str]] = None) -> Optional[str]`

```python
def create_task(
    description: str,
    project: Optional[str] = None,
    due: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Optional[str]:
    """
    Create a new task in TaskWarrior.

    Args:
        description: Task description (required)
        project: Project name (optional)
        due: Due date in TaskWarrior format (e.g., 'today', '2025-10-15', 'friday')
        priority: Priority level ('H', 'M', 'L')
        tags: List of tags to add (without '+' prefix)

    Returns:
        UUID of created task, or None if creation failed.

    Example:
        >>> uuid = create_task(
        ...     "Buy groceries",
        ...     project="home",
        ...     due="friday",
        ...     priority="M",
        ...     tags=["shopping", "errands"]
        ... )
        >>> print(f"Created task: {uuid}")
    """
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

    if result.returncode != 0:
        return None

    # Get the most recently created task
    # TaskWarrior outputs: "Created task N." but we need UUID
    all_tasks = get_tasks(['status:pending'])
    if all_tasks:
        # Sort by entry time (most recent first) and return UUID
        all_tasks.sort(key=lambda t: t.get('entry', ''), reverse=True)
        return all_tasks[0]['uuid']

    return None
```

**Tests to write:**
- Test basic task creation with just description
- Test with project parameter
- Test with due date parameter
- Test with priority parameter
- Test with tags parameter
- Test with all parameters combined
- Test failure handling (returncode != 0)
- Mock subprocess and verify command construction

---

#### 8. `mark_done(uuid: str) -> bool`

```python
def mark_done(uuid: str) -> bool:
    """
    Mark a task as completed.

    Args:
        uuid: Task UUID to mark done

    Returns:
        True if successful, False otherwise.

    Example:
        >>> success = mark_done('abc-123')
        >>> if success:
        ...     print("Task completed!")
    """
    result = run_task_command([uuid, 'done'], capture=False)
    return result.returncode == 0
```

**Tests to write:**
- Test successful completion (returncode 0)
- Test failure (returncode != 0)
- Verify correct command arguments

---

#### 9. `defer_task(uuid: str, new_due: str) -> bool`

```python
def defer_task(uuid: str, new_due: str) -> bool:
    """
    Change a task's due date.

    Args:
        uuid: Task UUID
        new_due: New due date in TaskWarrior format ('tomorrow', '2025-10-15', 'friday', etc.)

    Returns:
        True if successful, False otherwise.

    Example:
        >>> success = defer_task('abc-123', 'tomorrow')
        >>> if success:
        ...     print("Task deferred to tomorrow")
    """
    result = run_task_command([uuid, 'modify', f'due:{new_due}'], capture=False)
    return result.returncode == 0
```

**Tests to write:**
- Test with 'tomorrow'
- Test with specific date
- Test failure handling
- Verify command format

---

#### 10. `set_priority(uuid: str, priority: str) -> bool`

```python
def set_priority(uuid: str, priority: str) -> bool:
    """
    Set task priority.

    Args:
        uuid: Task UUID
        priority: Priority level ('H', 'M', 'L', or '' to remove)

    Returns:
        True if successful, False otherwise.

    Example:
        >>> success = set_priority('abc-123', 'H')
        >>> if success:
        ...     print("Priority set to HIGH")
    """
    result = run_task_command([uuid, 'modify', f'priority:{priority}'], capture=False)
    return result.returncode == 0
```

**Tests to write:**
- Test setting each priority level (H, M, L)
- Test removing priority (empty string)
- Test failure handling

---

#### 11. `delete_task(uuid: str) -> bool`

```python
def delete_task(uuid: str) -> bool:
    """
    Delete a task permanently.

    Args:
        uuid: Task UUID to delete

    Returns:
        True if successful, False otherwise.

    Example:
        >>> success = delete_task('abc-123')
        >>> if success:
        ...     print("Task deleted")
    """
    result = run_task_command([uuid, 'delete'], capture=False)
    return result.returncode == 0
```

**Tests to write:**
- Test successful deletion
- Test failure handling
- Verify command format

---

#### 12. `add_annotation(uuid: str, text: str) -> bool`

```python
def add_annotation(uuid: str, text: str) -> bool:
    """
    Add an annotation (note) to a task.

    Used for linking tasks to notes in Obsidian.

    Args:
        uuid: Task UUID
        text: Annotation text (e.g., "Note: vault/notes/meeting-2025-10-06.md")

    Returns:
        True if successful, False otherwise.

    Example:
        >>> success = add_annotation('abc-123', 'Note: vault/notes/project-ideas.md')
        >>> if success:
        ...     print("Note link added to task")
    """
    result = run_task_command([uuid, 'annotate', text], capture=False)
    return result.returncode == 0
```

**Tests to write:**
- Test annotation added successfully
- Test with various text formats
- Test failure handling

---

#### 13. `get_task_annotations(uuid: str) -> List[str]` (Bonus)

```python
def get_task_annotations(uuid: str) -> List[str]:
    """
    Get all annotations for a task.

    Args:
        uuid: Task UUID

    Returns:
        List of annotation strings. Empty list if none or task not found.

    Example:
        >>> annotations = get_task_annotations('abc-123')
        >>> for note in annotations:
        ...     print(f"Linked note: {note}")
    """
    task = get_task_info(uuid)
    if not task:
        return []

    # TaskWarrior stores annotations in 'annotations' field
    # Format: [{"entry": "...", "description": "..."}]
    annotations = task.get('annotations', [])

    return [ann['description'] for ann in annotations if isinstance(ann, dict)]
```

**Tests to write:**
- Test with task that has annotations
- Test with task that has no annotations
- Test with task not found
- Test parsing annotation structure

---

## Test Requirements

### Test Structure

**File:** `tests/test_integrations/test_taskwarrior.py`

**Required setup:**
```python
# ABOUTME: Comprehensive tests for TaskWarrior integration using mocked subprocess calls
# ABOUTME: Tests all CRUD operations, filtering, and error handling without requiring TaskWarrior installation
"""
Tests for TaskWarrior integration.

All tests use mocked subprocess calls - no actual TaskWarrior required.
"""
import pytest
from unittest.mock import patch, MagicMock, call
import json
from plorp.integrations.taskwarrior import (
    run_task_command,
    get_tasks,
    get_overdue_tasks,
    get_due_today,
    get_recurring_today,
    get_task_info,
    create_task,
    mark_done,
    defer_task,
    set_priority,
    delete_task,
    add_annotation,
    get_task_annotations
)


@pytest.fixture
def mock_subprocess():
    """Fixture to mock subprocess.run calls."""
    with patch('plorp.integrations.taskwarrior.subprocess.run') as mock:
        yield mock


@pytest.fixture
def sample_task_data(sample_taskwarrior_export):
    """Return sample TaskWarrior task data from fixtures."""
    return sample_taskwarrior_export
```

### Test Coverage Requirements

- **Overall coverage:** >90% for taskwarrior.py
- **Each function:** 100% coverage (all code paths tested)
- **Error cases:** All error paths tested
- **Integration points:** Mock all subprocess calls

### Required Test Cases

#### Test `run_task_command()`

```python
def test_run_task_command_with_capture(mock_subprocess):
    """Test running task command with output capture."""
    mock_subprocess.return_value = MagicMock(
        returncode=0,
        stdout='{"test": "output"}',
        stderr=''
    )

    result = run_task_command(['export'], capture=True)

    mock_subprocess.assert_called_once()
    call_args = mock_subprocess.call_args[0][0]
    assert call_args == ['task', 'export']
    assert result.stdout == '{"test": "output"}'


def test_run_task_command_without_capture(mock_subprocess):
    """Test running task command without capture (for user interaction)."""
    mock_subprocess.return_value = MagicMock(returncode=0)

    result = run_task_command(['done'], capture=False)

    mock_subprocess.assert_called_once()
    call_args = mock_subprocess.call_args
    assert 'capture_output' not in call_args[1]
```

#### Test `get_tasks()`

```python
def test_get_tasks_success(mock_subprocess, sample_task_data):
    """Test getting tasks with valid filter."""
    mock_subprocess.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps(sample_task_data)
    )

    tasks = get_tasks(['status:pending'])

    assert len(tasks) == 3
    assert tasks[0]['description'] == 'Buy groceries'
    mock_subprocess.assert_called_once()


def test_get_tasks_empty_result(mock_subprocess):
    """Test getting tasks when no matches."""
    mock_subprocess.return_value = MagicMock(
        returncode=0,
        stdout='[]'
    )

    tasks = get_tasks(['status:pending', 'project:nonexistent'])

    assert tasks == []


def test_get_tasks_command_failure(mock_subprocess):
    """Test get_tasks handles command failure gracefully."""
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout=''
    )

    tasks = get_tasks(['invalid:filter'])

    assert tasks == []


def test_get_tasks_json_parse_error(mock_subprocess):
    """Test get_tasks handles malformed JSON."""
    mock_subprocess.return_value = MagicMock(
        returncode=0,
        stdout='not valid json'
    )

    tasks = get_tasks(['status:pending'])

    assert tasks == []
```

#### Test Query Functions

```python
def test_get_overdue_tasks(mock_subprocess, sample_task_data):
    """Test getting overdue tasks."""
    # Filter sample data to only overdue task
    overdue_task = [t for t in sample_task_data if t['id'] == 2]

    mock_subprocess.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps(overdue_task)
    )

    tasks = get_overdue_tasks()

    assert len(tasks) == 1
    assert tasks[0]['description'] == 'Call dentist'

    # Verify correct filter used
    call_args = mock_subprocess.call_args[0][0]
    assert 'status:pending' in call_args
    assert 'due.before:today' in call_args


def test_get_due_today(mock_subprocess):
    """Test getting tasks due today."""
    mock_subprocess.return_value = MagicMock(
        returncode=0,
        stdout='[{"uuid": "test", "description": "Today task", "due": "20251006T000000Z"}]'
    )

    tasks = get_due_today()

    assert len(tasks) == 1
    assert 'due:today' in mock_subprocess.call_args[0][0]


def test_get_recurring_today(mock_subprocess):
    """Test getting recurring tasks due today."""
    mock_subprocess.return_value = MagicMock(
        returncode=0,
        stdout='[{"uuid": "test", "description": "Recurring", "recur": "daily"}]'
    )

    tasks = get_recurring_today()

    call_args = mock_subprocess.call_args[0][0]
    assert 'recur.any:' in call_args
    assert 'due:today' in call_args
```

#### Test `get_task_info()`

```python
def test_get_task_info_found(mock_subprocess, sample_task_data):
    """Test getting info for existing task."""
    task_data = [sample_task_data[0]]
    mock_subprocess.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps(task_data)
    )

    task = get_task_info('a1b2c3d4-e5f6-7890-1234-567890abcdef')

    assert task is not None
    assert task['description'] == 'Buy groceries'


def test_get_task_info_not_found(mock_subprocess):
    """Test getting info for non-existent task."""
    mock_subprocess.return_value = MagicMock(
        returncode=0,
        stdout='[]'
    )

    task = get_task_info('nonexistent-uuid')

    assert task is None
```

#### Test `create_task()`

```python
def test_create_task_minimal(mock_subprocess, sample_task_data):
    """Test creating task with just description."""
    mock_subprocess.return_value = MagicMock(returncode=0)

    # Mock the get_tasks call that happens after creation
    with patch('plorp.integrations.taskwarrior.get_tasks') as mock_get:
        mock_get.return_value = [sample_task_data[0]]

        uuid = create_task("Test task")

        assert uuid == 'a1b2c3d4-e5f6-7890-1234-567890abcdef'

        # Verify command
        call_args = mock_subprocess.call_args[0][0]
        assert call_args[0] == 'task'
        assert call_args[1] == 'add'
        assert call_args[2] == 'Test task'


def test_create_task_with_metadata(mock_subprocess, sample_task_data):
    """Test creating task with project, due, priority, tags."""
    mock_subprocess.return_value = MagicMock(returncode=0)

    with patch('plorp.integrations.taskwarrior.get_tasks') as mock_get:
        mock_get.return_value = [sample_task_data[0]]

        uuid = create_task(
            "Complete sprint",
            project="plorp",
            due="friday",
            priority="H",
            tags=["development", "urgent"]
        )

        call_args = mock_subprocess.call_args[0][0]
        assert 'project:plorp' in call_args
        assert 'due:friday' in call_args
        assert 'priority:H' in call_args
        assert '+development' in call_args
        assert '+urgent' in call_args


def test_create_task_failure(mock_subprocess):
    """Test create_task handles failure."""
    mock_subprocess.return_value = MagicMock(returncode=1)

    uuid = create_task("This will fail")

    assert uuid is None
```

#### Test Modification Functions

```python
def test_mark_done_success(mock_subprocess):
    """Test marking task as done."""
    mock_subprocess.return_value = MagicMock(returncode=0)

    success = mark_done('abc-123')

    assert success is True
    call_args = mock_subprocess.call_args[0][0]
    assert call_args == ['task', 'abc-123', 'done']


def test_mark_done_failure(mock_subprocess):
    """Test mark_done handles failure."""
    mock_subprocess.return_value = MagicMock(returncode=1)

    success = mark_done('invalid-uuid')

    assert success is False


def test_defer_task(mock_subprocess):
    """Test deferring task to new date."""
    mock_subprocess.return_value = MagicMock(returncode=0)

    success = defer_task('abc-123', 'tomorrow')

    assert success is True
    call_args = mock_subprocess.call_args[0][0]
    assert 'modify' in call_args
    assert 'due:tomorrow' in call_args


def test_set_priority(mock_subprocess):
    """Test setting task priority."""
    mock_subprocess.return_value = MagicMock(returncode=0)

    success = set_priority('abc-123', 'H')

    assert success is True
    call_args = mock_subprocess.call_args[0][0]
    assert 'priority:H' in call_args


def test_delete_task(mock_subprocess):
    """Test deleting task."""
    mock_subprocess.return_value = MagicMock(returncode=0)

    success = delete_task('abc-123')

    assert success is True
    call_args = mock_subprocess.call_args[0][0]
    assert call_args == ['task', 'abc-123', 'delete']
```

#### Test Annotation Functions

```python
def test_add_annotation(mock_subprocess):
    """Test adding annotation to task."""
    mock_subprocess.return_value = MagicMock(returncode=0)

    success = add_annotation('abc-123', 'Note: vault/notes/meeting.md')

    assert success is True
    call_args = mock_subprocess.call_args[0][0]
    assert 'annotate' in call_args
    assert 'Note: vault/notes/meeting.md' in call_args


def test_get_task_annotations(mock_subprocess):
    """Test getting annotations from task."""
    task_with_annotations = {
        'uuid': 'abc-123',
        'description': 'Test task',
        'annotations': [
            {'entry': '20251006T120000Z', 'description': 'Note: meeting.md'},
            {'entry': '20251006T130000Z', 'description': 'Note: ideas.md'}
        ]
    }

    with patch('plorp.integrations.taskwarrior.get_task_info') as mock_get:
        mock_get.return_value = task_with_annotations

        annotations = get_task_annotations('abc-123')

        assert len(annotations) == 2
        assert 'Note: meeting.md' in annotations
        assert 'Note: ideas.md' in annotations


def test_get_task_annotations_no_annotations(mock_subprocess):
    """Test getting annotations from task with none."""
    task_no_annotations = {
        'uuid': 'abc-123',
        'description': 'Test task'
    }

    with patch('plorp.integrations.taskwarrior.get_task_info') as mock_get:
        mock_get.return_value = task_no_annotations

        annotations = get_task_annotations('abc-123')

        assert annotations == []


def test_get_task_annotations_task_not_found(mock_subprocess):
    """Test getting annotations when task doesn't exist."""
    with patch('plorp.integrations.taskwarrior.get_task_info') as mock_get:
        mock_get.return_value = None

        annotations = get_task_annotations('invalid-uuid')

        assert annotations == []
```

### Test Execution

```bash
# Run all TaskWarrior integration tests
pytest tests/test_integrations/test_taskwarrior.py -v

# Run with coverage
pytest tests/test_integrations/test_taskwarrior.py --cov=src/plorp/integrations/taskwarrior --cov-report=term

# Run specific test
pytest tests/test_integrations/test_taskwarrior.py::test_create_task_with_metadata -v
```

---

## Success Criteria

### Code Quality Check

```bash
cd /Users/jsd/Documents/plorp
source venv/bin/activate

# 1. Black formatting passes
black --check src/plorp/integrations/taskwarrior.py tests/test_integrations/test_taskwarrior.py
# → Should pass with no changes needed

# 2. File exists and has ABOUTME comments
head -5 src/plorp/integrations/taskwarrior.py
# → Should show ABOUTME comments at top
```

### Test Check

```bash
# 3. All tests pass
pytest tests/test_integrations/test_taskwarrior.py -v
# → 25+ tests pass
# → No failures or errors

# 4. Coverage exceeds 90%
pytest tests/test_integrations/test_taskwarrior.py \
    --cov=src/plorp/integrations/taskwarrior \
    --cov-report=term-missing
# → Coverage >90%
# → Shows which lines not covered (if any)

# 5. No actual subprocess calls during tests
pytest tests/test_integrations/test_taskwarrior.py -v -s
# → Should complete quickly (< 1 second)
# → No actual TaskWarrior commands executed
```

### Import Check

```bash
# 6. Module can be imported
python3 -c "from plorp.integrations.taskwarrior import get_due_today; print('✓ Import successful')"
# → Prints: ✓ Import successful

# 7. All functions available
python3 -c "
from plorp.integrations import taskwarrior
funcs = ['run_task_command', 'get_tasks', 'get_overdue_tasks', 'get_due_today',
         'get_recurring_today', 'get_task_info', 'create_task', 'mark_done',
         'defer_task', 'set_priority', 'delete_task', 'add_annotation', 'get_task_annotations']
for func in funcs:
    assert hasattr(taskwarrior, func), f'Missing: {func}'
print('✓ All functions present')
"
# → Prints: ✓ All functions present
```

### Type Checking (Optional)

```bash
# 8. mypy type checking (if you want extra credit)
mypy src/plorp/integrations/taskwarrior.py
# → Should pass or show only minor issues
```

### Integration Test (Optional, requires TaskWarrior)

```bash
# 9. Optional: Test with real TaskWarrior
pytest tests/test_integrations/test_taskwarrior.py -v -m integration
# → Only runs if TaskWarrior installed
# → Tests actual subprocess interaction
```

---

## Completion Report Template

**Instructions:** Fill this out when Sprint 1 is complete.

### Implementation Summary

**What was implemented:**
- [ ] `run_task_command()` - Subprocess wrapper
- [ ] `get_tasks()` - Generic task query with filter
- [ ] `get_overdue_tasks()` - Query overdue tasks
- [ ] `get_due_today()` - Query tasks due today
- [ ] `get_recurring_today()` - Query recurring tasks
- [ ] `get_task_info()` - Get single task by UUID
- [ ] `create_task()` - Create new task with metadata
- [ ] `mark_done()` - Mark task completed
- [ ] `defer_task()` - Change task due date
- [ ] `set_priority()` - Set task priority
- [ ] `delete_task()` - Delete task
- [ ] `add_annotation()` - Add note to task
- [ ] `get_task_annotations()` - Retrieve task notes
- [ ] ABOUTME comments at top of file
- [ ] All functions have type hints
- [ ] All functions have docstrings with examples
- [ ] Comprehensive test suite (25+ tests)
- [ ] All tests use mocked subprocess
- [ ] >90% test coverage achieved

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

**Commands run to verify Sprint 1 is complete:**

```bash
# All verification commands from Success Criteria section
cd /Users/jsd/Documents/plorp
source venv/bin/activate

# Formatting check
black --check src/plorp/integrations/taskwarrior.py tests/test_integrations/test_taskwarrior.py

# Run tests
pytest tests/test_integrations/test_taskwarrior.py -v

# Coverage check
pytest tests/test_integrations/test_taskwarrior.py \
    --cov=src/plorp/integrations/taskwarrior \
    --cov-report=term-missing

# Import check
python3 -c "from plorp.integrations.taskwarrior import get_due_today; print('✓ Works')"
```

**Output summary:** [Describe what each command showed]

### Known Issues

**Any known limitations or issues:**

[List any issues that need to be addressed in future sprints]

Examples:
- Edge case not handled: [describe]
- Performance concern: [describe]
- Future enhancement needed: [describe]

### Testing Insights

**What you learned during testing:**

[Describe any insights about mocking, error handling, or TaskWarrior behavior]

### Handoff Notes for Sprint 2

**What Sprint 2 needs to know:**

- TaskWarrior integration is complete and tested
- All query functions return List[Dict] with standard TaskWarrior fields
- UUIDs are strings in format: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
- All modification functions return bool (True = success, False = failure)
- Subprocess calls are isolated and can be mocked easily
- Use `sample_taskwarrior_export` fixture for test data

**Functions Sprint 2 will use:**
- `get_overdue_tasks()` - For daily note generation
- `get_due_today()` - For daily note generation
- `get_recurring_today()` - For daily note generation

**Task data structure:**
```python
{
    'uuid': str,           # Unique identifier
    'description': str,    # Task description
    'status': str,         # 'pending', 'completed', 'deleted'
    'project': str,        # Optional project name
    'due': str,           # ISO format: '20251006T000000Z'
    'priority': str,       # 'H', 'M', 'L', or missing
    'tags': List[str],    # List of tags
    'urgency': float,     # TaskWarrior urgency score
    'entry': str,         # Creation timestamp
    'modified': str,      # Last modified timestamp
    # ... other TaskWarrior fields
}
```

**Files Sprint 2 should NOT modify:**
- `src/plorp/integrations/taskwarrior.py` (this is complete)
- `tests/test_integrations/test_taskwarrior.py` (this is complete)

### Questions for PM/Architect

[Add any questions or clarifications needed]

### Recommendations

**Suggestions for future sprints:**

[Any recommendations based on what you learned in Sprint 1]

Examples:
- Consider caching task queries for performance
- Add TaskWarrior version detection
- Add support for TaskWarrior contexts
- Consider direct SQLite access for read operations

### Sign-off

- **Implemented by:** [Claude Code Engineer Instance]
- **Date completed:** [Date]
- **Implementation time:** [Actual time taken]
- **Ready for Sprint 2:** [Yes/No]

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

### Answers from PM/Architect

**Q1: Example question placeholder**
```
Q: Should we implement direct SQLite access as an alternative to subprocess?
A: No, Sprint 1 should only use subprocess. Direct SQLite access can be
   added in a future optimization sprint if needed. Keep it simple for now.
Status: RESOLVED
```

---

**Document Version:** 1.0
**Last Updated:** October 6, 2025
**Status:** Ready for Implementation
**Next Sprint:** SPRINT-2 (Daily Note Generation)
