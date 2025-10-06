# plorp - TaskWarrior Integration Guide

**Date:** October 6, 2025
**Purpose:** Comprehensive guide to TaskWarrior 3.x integration

---

## Table of Contents

1. [TaskWarrior 3.x Overview](#taskwarrior-3x-overview)
2. [Storage Architecture](#storage-architecture)
3. [Integration Approaches](#integration-approaches)
4. [CLI Integration](#cli-integration)
5. [Direct SQLite Access](#direct-sqlite-access)
6. [Common Patterns](#common-patterns)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## TaskWarrior 3.x Overview

### What Changed in 3.x

**TaskWarrior 2.x:**
- Plain text files: `pending.data`, `completed.data`, `undo.data`
- Custom line-based format
- File I/O for all operations

**TaskWarrior 3.x:**
- **SQLite database** via TaskChampion library
- Location: `~/.task/taskchampion.sqlite3`
- Rust-based storage backend
- Transaction-based operations
- Improved sync capabilities

### Key Concepts

**Replica:** Local copy of task database
**Working Set:** Currently active tasks (numbered IDs)
**UUID:** Permanent task identifier (stable across sync)
**Operations:** Atomic changes to tasks (create, modify, delete)

---

## Storage Architecture

### Database Structure

**Location:** `~/.task/taskchampion.sqlite3`

**Files:**
```
~/.task/
├── taskchampion.sqlite3       # Main database
├── taskchampion.sqlite3-shm   # Shared memory (SQLite WAL mode)
└── taskchampion.sqlite3-wal   # Write-ahead log
```

### TaskChampion Library

**Written in:** Rust
**Binding:** C++ wrapper for TaskWarrior CLI
**Features:**
- ACID transactions
- Sync protocol implementation
- Working set management
- Operation history

### SQLite Schema (Simplified)

```sql
-- Core tables (simplified view)
tasks
├── uuid TEXT PRIMARY KEY
├── description TEXT
├── status TEXT  -- pending, completed, deleted, waiting
├── project TEXT
├── due TEXT     -- ISO 8601 datetime
├── priority TEXT
├── tags TEXT    -- JSON array
└── ...

operations
├── id INTEGER
├── uuid TEXT
├── operation_type TEXT
├── timestamp INTEGER
└── ...

working_set
├── index INTEGER
├── uuid TEXT
└── ...
```

**Note:** Actual schema is more complex. Use CLI for writes, SQLite for reads only.

---

## Integration Approaches

### Approach 1: CLI Wrapper (Recommended)

**Pros:**
- Official API
- Stable interface
- Respects TaskWarrior logic
- Handles transactions, hooks, etc.

**Cons:**
- Slower (subprocess overhead)
- Limited to CLI capabilities

**Use for:**
- All write operations
- Complex queries
- Production code

### Approach 2: Direct SQLite (Advanced)

**Pros:**
- Fast (no subprocess)
- Complex queries possible
- Direct access to data

**Cons:**
- Bypasses TaskWarrior logic
- Schema may change
- Risk of corruption if misused

**Use for:**
- Read-only operations
- Performance-critical paths
- Advanced analytics

### Approach 3: Hybrid (Best)

**Strategy:**
- Write operations → CLI
- Simple reads → CLI
- Performance-critical reads → Direct SQLite (with caching)

---

## CLI Integration

### Basic Command Execution

```python
import subprocess
import json

def run_task_command(args, capture=True):
    """Execute task command and return result"""
    cmd = ['task'] + args

    result = subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        check=False  # Don't raise on non-zero exit
    )

    return result
```

### Querying Tasks

**Export format:** JSON (most useful for integration)

```python
def get_tasks(filter_args):
    """Get tasks matching filter as list of dicts"""
    args = filter_args + ['export']
    result = run_task_command(args)

    if result.returncode != 0:
        return []

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

# Examples
overdue = get_tasks(['status:pending', 'due.before:today'])
due_today = get_tasks(['status:pending', 'due:today'])
project_tasks = get_tasks(['project:home', 'status:pending'])
```

### Task Export Format

```json
[
  {
    "id": 1,
    "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "description": "Buy groceries",
    "status": "pending",
    "project": "home",
    "due": "20251007T000000Z",
    "priority": "M",
    "tags": ["shopping", "errands"],
    "entry": "20251006T120000Z",
    "modified": "20251006T120000Z",
    "urgency": 8.2
  }
]
```

### Creating Tasks

```python
def create_task(description, **kwargs):
    """Create task with optional metadata"""
    args = ['add', description]

    # Add optional attributes
    if 'project' in kwargs:
        args.append(f"project:{kwargs['project']}")
    if 'due' in kwargs:
        args.append(f"due:{kwargs['due']}")
    if 'priority' in kwargs:
        args.append(f"priority:{kwargs['priority']}")
    if 'tags' in kwargs:
        for tag in kwargs['tags']:
            args.append(f"+{tag}")

    result = run_task_command(args, capture=False)

    if result.returncode == 0:
        # Get UUID of created task
        # TaskWarrior doesn't output UUID directly, so query
        tasks = get_tasks(['status:pending', f'description:{description}'])
        if tasks:
            return tasks[0]['uuid']

    return None

# Usage
uuid = create_task(
    "Buy milk",
    project="home",
    due="tomorrow",
    priority="M",
    tags=["shopping"]
)
```

### Modifying Tasks

```python
def modify_task(uuid, **changes):
    """Modify task attributes"""
    args = [uuid, 'modify']

    for key, value in changes.items():
        if key == 'tags_add':
            for tag in value:
                args.append(f"+{tag}")
        elif key == 'tags_remove':
            for tag in value:
                args.append(f"-{tag}")
        else:
            args.append(f"{key}:{value}")

    result = run_task_command(args, capture=False)
    return result.returncode == 0

# Usage
modify_task('abc-123', due='friday', priority='H')
modify_task('abc-123', tags_add=['urgent'])
```

### Completing Tasks

```python
def mark_done(uuid):
    """Mark task as done"""
    result = run_task_command([uuid, 'done'], capture=False)
    return result.returncode == 0

def delete_task(uuid):
    """Delete task"""
    result = run_task_command([uuid, 'delete'], capture=False)
    return result.returncode == 0
```

### Annotations

```python
def add_annotation(uuid, text):
    """Add annotation to task"""
    result = run_task_command([uuid, 'annotate', text], capture=False)
    return result.returncode == 0

def get_task_info(uuid):
    """Get detailed task info including annotations"""
    result = run_task_command([uuid, 'info'])

    if result.returncode != 0:
        return None

    # Parse info output (text format)
    info = {}
    annotations = []

    for line in result.stdout.split('\n'):
        if 'Description' in line:
            info['description'] = line.split('Description')[1].strip()
        elif line.strip().startswith('-'):
            # Annotation line
            annotations.append(line.strip()[2:])  # Remove "- "

    info['annotations'] = annotations
    return info
```

### Recurring Tasks

```python
def create_recurring_task(description, recur_pattern, due='today', **kwargs):
    """Create recurring task"""
    args = ['add', description, f'recur:{recur_pattern}', f'due:{due}']

    if 'until' in kwargs:
        args.append(f"until:{kwargs['until']}")

    for key, value in kwargs.items():
        if key != 'until':
            args.append(f"{key}:{value}")

    result = run_task_command(args, capture=False)
    return result.returncode == 0

# Usage
create_recurring_task(
    "Morning meditation",
    recur_pattern="daily",
    due="today",
    until="eoy",
    project="personal"
)
```

### Filter Syntax Reference

**Status:**
```python
get_tasks(['status:pending'])
get_tasks(['status:completed'])
get_tasks(['status:deleted'])
get_tasks(['status:waiting'])
```

**Date filters:**
```python
get_tasks(['due:today'])
get_tasks(['due:tomorrow'])
get_tasks(['due.before:today'])      # Overdue
get_tasks(['due.after:today'])
get_tasks(['due.before:eow'])        # End of week
get_tasks(['due:2025-10-15'])
```

**Project filters:**
```python
get_tasks(['project:home'])
get_tasks(['project:work.planning'])  # Hierarchical
get_tasks(['project.not:work'])
```

**Tag filters:**
```python
get_tasks(['+shopping'])              # Has tag
get_tasks(['-shopping'])              # Doesn't have tag
get_tasks(['+urgent', '+important'])  # AND
```

**Combined:**
```python
get_tasks([
    'status:pending',
    'project:work',
    '+urgent',
    'due.before:eow'
])
```

---

## Direct SQLite Access

### Connection

```python
import sqlite3
import os

def get_taskwarrior_db():
    """Get connection to TaskWarrior database"""
    db_path = os.path.expanduser('~/.task/taskchampion.sqlite3')

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"TaskWarrior database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Access columns by name

    return conn
```

### Reading Tasks

```python
def get_pending_tasks_direct():
    """Get pending tasks directly from SQLite"""
    conn = get_taskwarrior_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT uuid, description, project, due, priority, status
        FROM tasks
        WHERE status = 'pending'
        ORDER BY due ASC
    """)

    tasks = []
    for row in cursor:
        tasks.append(dict(row))

    conn.close()
    return tasks
```

### Complex Queries

```python
def get_tasks_by_project_summary():
    """Get task count by project"""
    conn = get_taskwarrior_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            project,
            COUNT(*) as task_count,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count
        FROM tasks
        WHERE status IN ('pending', 'completed')
        GROUP BY project
        ORDER BY task_count DESC
    """)

    summary = []
    for row in cursor:
        summary.append(dict(row))

    conn.close()
    return summary
```

### Warning: Write Operations

**❌ DO NOT write directly to SQLite**

```python
# BAD - Will corrupt database
conn = get_taskwarrior_db()
conn.execute("UPDATE tasks SET status='completed' WHERE uuid=?", [uuid])
conn.commit()
```

**✅ Use CLI for writes**

```python
# GOOD
run_task_command([uuid, 'done'])
```

**Why:**
- TaskChampion maintains operation log
- Working set needs updates
- Hooks need to fire
- Sync requires proper operations

---

## Common Patterns

### Pattern 1: Get Task Details with Fallback

```python
def get_task_safe(uuid):
    """Get task, return None if not found"""
    try:
        tasks = get_tasks([uuid])
        return tasks[0] if tasks else None
    except Exception as e:
        print(f"Error getting task {uuid}: {e}")
        return None
```

### Pattern 2: Batch Task Creation

```python
def create_tasks_batch(task_list):
    """Create multiple tasks efficiently"""
    created_uuids = []

    for task_data in task_list:
        desc = task_data.pop('description')
        uuid = create_task(desc, **task_data)

        if uuid:
            created_uuids.append(uuid)
        else:
            print(f"Failed to create: {desc}")

    return created_uuids

# Usage
tasks = [
    {'description': 'Buy milk', 'project': 'home', 'due': 'tomorrow'},
    {'description': 'Call dentist', 'project': 'health', 'priority': 'H'},
]
uuids = create_tasks_batch(tasks)
```

### Pattern 3: Query with Transform

```python
def get_tasks_formatted(filter_args, format_func):
    """Get tasks and apply formatting function"""
    tasks = get_tasks(filter_args)
    return [format_func(task) for task in tasks]

def task_to_markdown_checkbox(task):
    """Convert task to markdown checkbox"""
    desc = task['description']
    uuid = task['uuid']
    project = task.get('project', 'none')
    due = task.get('due', 'none')

    return f"- [ ] {desc} (project: {project}, due: {due}, uuid: {uuid})"

# Usage
checkboxes = get_tasks_formatted(
    ['status:pending', 'due:today'],
    task_to_markdown_checkbox
)
```

### Pattern 4: Cached Queries

```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=128)
def get_tasks_cached(filter_tuple, cache_time):
    """Get tasks with simple time-based caching"""
    # cache_time is just for cache key, not used
    filter_args = list(filter_tuple)
    return get_tasks(filter_args)

def get_pending_cached():
    """Get pending tasks with 5-minute cache"""
    # Round to 5-minute intervals
    cache_key = datetime.now().replace(second=0, microsecond=0)
    cache_key = cache_key - timedelta(minutes=cache_key.minute % 5)

    return get_tasks_cached(
        ('status:pending',),
        cache_key.isoformat()
    )
```

### Pattern 5: UUID Extraction from CLI Output

```python
def extract_uuid_from_add_output(output):
    """Extract UUID from 'task add' output"""
    # Output: "Created task 123."
    # We need to query for the task

    import re
    match = re.search(r'Created task (\d+)', output)

    if match:
        task_id = match.group(1)
        # Convert ID to UUID
        tasks = get_tasks([task_id])
        if tasks:
            return tasks[0]['uuid']

    return None
```

---

## Best Practices

### 1. Always Use UUIDs for Persistence

**❌ Bad:**
```python
# Task ID changes across sync
task_id = 1
run_task_command([str(task_id), 'done'])
```

**✅ Good:**
```python
# UUID is stable
task_uuid = 'abc-123-def-456'
run_task_command([task_uuid, 'done'])
```

### 2. Handle Missing Tasks Gracefully

```python
def mark_done_safe(uuid):
    """Mark done, handle if task doesn't exist"""
    result = run_task_command([uuid, 'done'])

    if result.returncode != 0:
        if 'No matches' in result.stderr:
            print(f"Task {uuid} not found (may be deleted)")
            return False
        else:
            print(f"Error: {result.stderr}")
            return False

    return True
```

### 3. Validate Before Operations

```python
def ensure_task_exists(uuid):
    """Check if task exists before operating on it"""
    tasks = get_tasks([uuid])
    return len(tasks) > 0

def modify_task_safe(uuid, **changes):
    """Only modify if task exists"""
    if not ensure_task_exists(uuid):
        print(f"Task {uuid} not found")
        return False

    return modify_task(uuid, **changes)
```

### 4. Parse CLI Output Defensively

```python
def parse_task_info_safe(info_output):
    """Parse task info output with error handling"""
    info = {}

    try:
        for line in info_output.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip().lower()] = value.strip()
    except Exception as e:
        print(f"Error parsing task info: {e}")

    return info
```

### 5. Use Context Managers for SQLite

```python
from contextlib import contextmanager

@contextmanager
def taskwarrior_db():
    """Context manager for database access"""
    conn = get_taskwarrior_db()
    try:
        yield conn
    finally:
        conn.close()

# Usage
with taskwarrior_db() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE status='pending'")
    tasks = cursor.fetchall()
```

### 6. Test TaskWarrior Availability

```python
def check_taskwarrior_installed():
    """Verify TaskWarrior is installed and accessible"""
    try:
        result = subprocess.run(
            ['task', '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except FileNotFoundError:
        print("❌ TaskWarrior not found")
        print("Install: brew install task")
        return False
    except subprocess.CalledProcessError:
        print("❌ TaskWarrior found but not working")
        return False
```

---

## Troubleshooting

### Issue: "task: command not found"

**Cause:** TaskWarrior not installed

**Fix:**
```bash
# macOS
brew install task

# Linux (Ubuntu/Debian)
sudo apt-get install taskwarrior

# Verify
task --version
```

### Issue: "No tasks" despite having tasks

**Cause:** Wrong data location or context active

**Fix:**
```bash
# Check data location
task config data.location
# Should show: ~/.task

# Check context
task context show
# If context is set, only tasks matching context are shown

# Clear context
task context none
```

### Issue: SQLite database locked

**Cause:** TaskWarrior process still running or crashed

**Fix:**
```bash
# Check for running task processes
ps aux | grep task

# Kill if necessary
killall task

# Check for lock files
ls ~/.task/*.lock

# Remove lock files (if no task process running)
rm ~/.task/*.lock
```

### Issue: JSON parse error from export

**Cause:** Invalid filter or empty result

**Fix:**
```python
def get_tasks_safe(filter_args):
    result = run_task_command(filter_args + ['export'])

    if result.returncode != 0:
        return []

    # Check for empty output
    if not result.stdout.strip():
        return []

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Output: {result.stdout[:200]}")
        return []
```

### Issue: UUIDs not found after sync

**Cause:** Task was deleted on another device

**Fix:**
```python
def get_task_with_fallback(uuid):
    # Try to get task
    tasks = get_tasks([uuid])

    if tasks:
        return tasks[0]

    # Check if task was deleted
    deleted = get_tasks([uuid, 'status:deleted'])

    if deleted:
        print(f"Task {uuid} was deleted")
        return None

    print(f"Task {uuid} not found")
    return None
```

### Issue: Subprocess timeout

**Cause:** TaskWarrior operation taking too long (large database, sync)

**Fix:**
```python
def run_task_command_with_timeout(args, timeout=30):
    cmd = ['task'] + args

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result
    except subprocess.TimeoutExpired:
        print(f"TaskWarrior command timed out after {timeout}s")
        return None
```

---

## Reference

### TaskWarrior Documentation

- Official docs: https://taskwarrior.org/docs/
- Man pages: `man task`, `man taskrc`
- GitHub: https://github.com/GothenburgBitFactory/taskwarrior

### TaskChampion

- GitHub: https://github.com/GothenburgBitFactory/taskchampion
- Docs: https://gothenburgbitfactory.org/taskchampion/

### Useful Commands

```bash
# Show all config
task config

# Show specific config
task config data.location

# Export all tasks
task export > all_tasks.json

# Export pending tasks
task status:pending export > pending.json

# Database stats
task stats

# Show database location
task diagnostics | grep "Data location"

# Verify database integrity
sqlite3 ~/.task/taskchampion.sqlite3 "PRAGMA integrity_check;"
```

---

**Document Version:** 1.0
**Last Updated:** October 6, 2025
**Status:** Complete reference guide
