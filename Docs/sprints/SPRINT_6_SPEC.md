# Sprint 6 Spec: plorp v1.1 - MCP-First Rewrite

**Version:** 1.1.0
**Status:** ✅ COMPLETE (2025-10-06)
**Sprint:** 6
**Estimated Effort:** 17 hours
**Dependencies:** Sprints 0-5 (Complete)
**Architecture:** MCP-First with CLI Wrapper

---

## Executive Summary

**What Changed:**
- v1.0: CLI-first with workflow modules
- v1.1: **Core engine** returning structured data, exposed via MCP and CLI

**Why Rewrite:**
- Better agent integration (rich return values)
- Multiple interface support (MCP, CLI, future API/GUI)
- Cleaner testing (test pure functions, not CLI output)
- Future-proof architecture

**Breaking Changes:**
- `plorp.workflows.*` modules removed entirely
- Users importing plorp as library must migrate to `plorp.core.*`
- CLI commands remain compatible (refactored internally)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              Core Engine (Pure Python)              │
│                                                     │
│  plorp.core.daily                                   │
│  plorp.core.inbox                                   │
│  plorp.core.notes                                   │
│  plorp.core.tasks                                   │
│  plorp.core.review                                  │
│                                                     │
│  - Pure functions                                   │
│  - Return structured data (TypedDict)               │
│  - No I/O decisions (no click.echo, no print)       │
│  - Raise specific exceptions                        │
│  - Fully typed with type hints                      │
└──────────────┬──────────────────────────────────────┘
               │
               │ Used by both interfaces
               │
       ┌───────┴────────┐
       │                │
┌──────▼──────┐  ┌──────▼──────┐
│ MCP Server  │  │     CLI     │
│  (Primary)  │  │  (Wrapper)  │
│             │  │             │
│ Tools:      │  │ Commands:   │
│ - start_day │  │ - start     │
│ - review    │  │ - review    │
│ - inbox     │  │ - inbox     │
│ - tasks     │  │ - note      │
│ - notes     │  │ - link      │
│             │  │             │
│ Returns:    │  │ Formats:    │
│ Rich dicts  │  │ Human text  │
└─────────────┘  └─────────────┘

       Both use same integrations:

┌─────────────────────────────────────┐
│        Integrations Layer           │
│                                     │
│  plorp.integrations.taskwarrior     │
│  plorp.integrations.obsidian        │
│                                     │
│  - Subprocess/file operations       │
│  - Data normalization               │
└─────────────────────────────────────┘
```

---

## Core Principles (v1.1)

### 1. Structured Return Values

Every core function returns a TypedDict with complete information:

```python
class DailyStartResult(TypedDict):
    note_path: str
    created_at: str
    summary: TaskSummary
    tasks: list[TaskInfo]

def start_day(date: date, vault_path: Path) -> DailyStartResult:
    """Returns ALL the data, no printing"""
    ...
    return {
        "note_path": str(note_path),
        "created_at": datetime.now().isoformat(),
        "summary": {...},
        "tasks": [...]
    }
```

### 2. Interface Separation

```python
# Core (no I/O decisions)
result = core.daily.start_day(date.today(), vault_path)

# MCP wraps it
@server.call_tool()
async def plorp_start_day(date: str) -> dict:
    return core.daily.start_day(parse_date(date), get_vault())

# CLI wraps it
@cli.command()
def start():
    result = core.daily.start_day(date.today(), get_vault())
    click.echo(f"✅ Created: {result['note_path']}")
```

### 3. No Interactive Prompts in Core

Core functions don't prompt users. They either:
- Accept all parameters upfront
- Return data for caller to decide what to do

```python
# Core returns data, no prompting
def get_review_tasks(date: date, vault_path: Path) -> ReviewData:
    """Returns tasks needing review, no prompting"""
    return {
        "uncompleted_tasks": [...],
        "daily_note_path": "...",
        "date": "..."
    }

# MCP tool lets agent drive interaction
@server.call_tool()
async def plorp_get_review_tasks(date: str) -> dict:
    return core.review.get_review_tasks(...)

@server.call_tool()
async def plorp_mark_completed(uuid: str) -> dict:
    return core.tasks.mark_completed(uuid)

# CLI drives interaction itself
@cli.command()
def review():
    data = core.review.get_review_tasks(...)
    for task in data["uncompleted_tasks"]:
        choice = click.prompt(...)  # CLI does the prompting
        if choice == "1":
            core.tasks.mark_completed(task["uuid"])
```

---

## Project Structure (v1.1)

```
plorp/
├── pyproject.toml              # Updated with mcp dependency
├── README.md                   # Updated architecture docs
│
├── src/plorp/
│   ├── __init__.py
│   ├── __version__.py
│   │
│   ├── core/                   # NEW - Pure business logic
│   │   ├── __init__.py
│   │   ├── types.py           # TypedDict definitions
│   │   ├── daily.py           # Daily workflow core logic
│   │   ├── review.py          # Review workflow core logic
│   │   ├── inbox.py           # Inbox workflow core logic
│   │   ├── notes.py           # Note management core logic
│   │   ├── tasks.py           # Task operations core logic
│   │   └── exceptions.py      # Custom exceptions
│   │
│   ├── integrations/           # UNCHANGED - Keep as-is
│   │   ├── __init__.py
│   │   ├── taskwarrior.py
│   │   └── obsidian.py
│   │
│   ├── parsers/                # UNCHANGED - Keep as-is
│   │   ├── __init__.py
│   │   └── markdown.py
│   │
│   ├── prompts/                # UNCHANGED - Keep as-is
│   │   ├── __init__.py
│   │   └── interactive.py
│   │
│   ├── config.py               # UNCHANGED
│   │
│   ├── mcp_server.py           # NEW - MCP server entry point
│   ├── cli.py                  # REFACTORED - Thin wrapper around core
│   │
│   └── workflows/              # REMOVED - Deprecated in v1.1
│
├── tests/
│   ├── test_core/              # NEW - Test core functions
│   │   ├── test_daily.py
│   │   ├── test_review.py
│   │   ├── test_inbox.py
│   │   ├── test_notes.py
│   │   └── test_tasks.py
│   │
│   ├── test_mcp/               # NEW - Test MCP tools
│   │   └── test_tools.py
│   │
│   ├── test_cli.py             # UPDATED - Test CLI wrapper
│   │
│   └── test_integrations/      # UNCHANGED
│       ├── test_taskwarrior.py
│       └── test_obsidian.py
│
├── .claude/                    # NEW - Slash commands
│   └── commands/
│       ├── start-day.md
│       ├── review-day.md
│       ├── process-inbox.md
│       ├── create-note.md
│       └── link-note.md
│
└── Docs/
    ├── MCP_SETUP.md           # NEW - MCP installation guide
    ├── ARCHITECTURE.md         # NEW - v1.1 architecture deep dive
    ├── MIGRATION_GUIDE.md     # NEW - v1.0 → v1.1 migration
    ├── EXAMPLE_WORKFLOWS.md   # NEW - Common usage patterns
    └── sprints/               # Archive v1.0 sprints
        └── SPRINT_6_SPEC.md
```

---

## Implementation Phases

### Phase 0: Core Types & Exceptions

**Goal:** Define all TypedDict types and custom exceptions

**Files to create:**
- `src/plorp/core/__init__.py`
- `src/plorp/core/types.py` (~150 lines)
- `src/plorp/core/exceptions.py` (~80 lines)

**Key types:**
```python
# Task types
class TaskInfo(TypedDict):
    uuid: str
    description: str
    status: Literal["pending", "completed", "deleted"]
    due: str | None
    priority: Literal["H", "M", "L", ""] | None
    project: str | None
    tags: list[str]

class TaskSummary(TypedDict):
    overdue_count: int
    due_today_count: int
    recurring_count: int
    total_count: int

# Daily workflow types
class DailyStartResult(TypedDict):
    note_path: str
    created_at: str
    date: str
    summary: TaskSummary
    tasks: list[TaskInfo]

class ReviewData(TypedDict):
    date: str
    daily_note_path: str
    uncompleted_tasks: list[TaskInfo]
    total_tasks: int
    uncompleted_count: int

class ReviewResult(TypedDict):
    daily_note_path: str
    review_added_at: str
    reflections: dict[str, str]

# Inbox types
class InboxItem(TypedDict):
    text: str
    line_number: int

class InboxData(TypedDict):
    inbox_path: str
    unprocessed_items: list[InboxItem]
    item_count: int

class InboxProcessResult(TypedDict):
    item_text: str
    action: Literal["task", "note", "both", "discard"]
    task_uuid: str | None
    note_path: str | None

# Note types
class NoteCreateResult(TypedDict):
    note_path: str
    created_at: str
    title: str
    linked_task_uuid: str | None

class NoteLinkResult(TypedDict):
    note_path: str
    task_uuid: str
    linked_at: str
```

**Custom exceptions:**
```python
class PlorpError(Exception):
    """Base exception for all plorp errors."""
    pass

class VaultNotFoundError(PlorpError):
    def __init__(self, vault_path: str):
        self.vault_path = vault_path
        super().__init__(f"Vault not found: {vault_path}")

class DailyNoteExistsError(PlorpError):
    def __init__(self, date: str, note_path: str):
        self.date = date
        self.note_path = note_path
        super().__init__(f"Daily note already exists: {note_path}")

class DailyNoteNotFoundError(PlorpError):
    def __init__(self, date: str):
        self.date = date
        super().__init__(f"Daily note not found for: {date}")

class TaskNotFoundError(PlorpError):
    def __init__(self, uuid: str):
        self.uuid = uuid
        super().__init__(f"Task not found: {uuid}")

class NoteNotFoundError(PlorpError):
    def __init__(self, note_path: str):
        self.note_path = note_path
        super().__init__(f"Note not found: {note_path}")

class NoteOutsideVaultError(PlorpError):
    def __init__(self, note_path: str, vault_path: str):
        self.note_path = note_path
        self.vault_path = vault_path
        super().__init__(f"Note outside vault: {note_path} (vault: {vault_path})")

class InboxNotFoundError(PlorpError):
    def __init__(self, inbox_path: str):
        self.inbox_path = inbox_path
        super().__init__(f"Inbox not found: {inbox_path}")
```

---

### Phase 1: Core Daily Workflow

**Goal:** Extract daily workflow logic into pure functions

**File to create:** `src/plorp/core/daily.py` (~250 lines)

**Key function:**
```python
def start_day(target_date: date, vault_path: Path) -> DailyStartResult:
    """
    Generate daily note for specified date.

    Pure function - no prompting, no printing, returns complete data.

    Args:
        target_date: Date for daily note
        vault_path: Absolute path to Obsidian vault

    Returns:
        DailyStartResult with note path, summary, and task list

    Raises:
        VaultNotFoundError: Vault directory doesn't exist
        DailyNoteExistsError: Daily note already exists for this date
    """
    # Validate vault exists
    vault_path = vault_path.expanduser().resolve()
    if not vault_path.exists():
        raise VaultNotFoundError(str(vault_path))

    # Check if daily note already exists
    daily_dir = vault_path / "daily"
    daily_dir.mkdir(exist_ok=True)

    note_path = daily_dir / f"{target_date}.md"
    if note_path.exists():
        raise DailyNoteExistsError(str(target_date), str(note_path))

    # Get tasks from TaskWarrior
    all_tasks = get_pending_tasks()

    # Categorize tasks
    overdue = []
    due_today = []
    recurring = []

    for task_data in all_tasks:
        task_info = _normalize_task(task_data)

        if _is_overdue(task_data, target_date):
            overdue.append(task_info)
        elif _is_due_today(task_data, target_date):
            due_today.append(task_info)
        elif _is_recurring(task_data):
            recurring.append(task_info)

    all_categorized = overdue + due_today + recurring

    # Create note content
    content = _format_daily_note(target_date, overdue, due_today, recurring)

    # Write note
    note_path.write_text(content)

    # Return structured result
    return {
        "note_path": str(note_path),
        "created_at": datetime.now().isoformat(),
        "date": str(target_date),
        "summary": {
            "overdue_count": len(overdue),
            "due_today_count": len(due_today),
            "recurring_count": len(recurring),
            "total_count": len(all_categorized)
        },
        "tasks": all_categorized
    }
```

**Helper functions:**
- `_normalize_task(task_data: dict) -> TaskInfo`
- `_is_overdue(task: dict, reference_date: date) -> bool`
- `_is_due_today(task: dict, reference_date: date) -> bool`
- `_is_recurring(task: dict) -> bool`
- `_format_daily_note(...) -> str`

---

### Phase 2: Core Review Workflow

**Goal:** Extract review workflow, split into read + write operations

**File to create:** `src/plorp/core/review.py` (~180 lines)

**Key functions:**
```python
def get_review_tasks(target_date: date, vault_path: Path) -> ReviewData:
    """
    Get uncompleted tasks for review.

    Pure read operation - returns data, no interaction.

    Args:
        target_date: Date to review
        vault_path: Path to vault

    Returns:
        ReviewData with uncompleted tasks

    Raises:
        VaultNotFoundError: Vault doesn't exist
        DailyNoteNotFoundError: No daily note for date
    """
    vault_path = vault_path.expanduser().resolve()
    if not vault_path.exists():
        raise VaultNotFoundError(str(vault_path))

    # Find daily note
    note_path = vault_path / "daily" / f"{target_date}.md"
    if not note_path.exists():
        raise DailyNoteNotFoundError(str(target_date))

    # Parse uncompleted tasks from note
    tasks_data = parse_daily_note_tasks(note_path)

    # Convert to TaskInfo with full data from TaskWarrior
    uncompleted_tasks = []
    for description, uuid in tasks_data:
        task_data = get_task_info(uuid)
        if task_data:
            uncompleted_tasks.append(_normalize_task(task_data))

    return {
        "date": str(target_date),
        "daily_note_path": str(note_path),
        "uncompleted_tasks": uncompleted_tasks,
        "total_tasks": len(tasks_data),
        "uncompleted_count": len(uncompleted_tasks)
    }

def add_review_notes(
    target_date: date,
    vault_path: Path,
    reflections: dict[str, str]
) -> ReviewResult:
    """
    Add review/reflection notes to daily note.

    Args:
        target_date: Date to add review for
        vault_path: Path to vault
        reflections: Dict with keys: went_well, could_improve, tomorrow

    Returns:
        ReviewResult with confirmation

    Raises:
        DailyNoteNotFoundError: No daily note for date
    """
    vault_path = vault_path.expanduser().resolve()
    note_path = vault_path / "daily" / f"{target_date}.md"

    if not note_path.exists():
        raise DailyNoteNotFoundError(str(target_date))

    # Read existing content
    content = note_path.read_text()

    # Append review section
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    review_section = f"\n## Review ({timestamp})\n\n"

    if "went_well" in reflections:
        review_section += f"**What went well:**\n{reflections['went_well']}\n\n"

    if "could_improve" in reflections:
        review_section += f"**What could improve:**\n{reflections['could_improve']}\n\n"

    if "tomorrow" in reflections:
        review_section += f"**Notes for tomorrow:**\n{reflections['tomorrow']}\n\n"

    # Append to file
    content += review_section
    note_path.write_text(content)

    return {
        "daily_note_path": str(note_path),
        "review_added_at": timestamp,
        "reflections": reflections
    }
```

---

### Phase 3: Core Task Operations

**Goal:** Task manipulation functions (complete, defer, drop, set priority)

**File to create:** `src/plorp/core/tasks.py` (~200 lines)

**Key functions:**
```python
def mark_completed(uuid: str) -> TaskCompleteResult:
    """
    Mark task as completed in TaskWarrior.

    Args:
        uuid: Task UUID

    Returns:
        TaskCompleteResult with confirmation

    Raises:
        TaskNotFoundError: Task doesn't exist
    """
    # Verify task exists
    task = get_task_info(uuid)
    if not task:
        raise TaskNotFoundError(uuid)

    description = task["description"]

    # Mark done
    mark_task_done(uuid)

    return {
        "uuid": uuid,
        "description": description,
        "completed_at": datetime.now().isoformat()
    }

def defer_task(uuid: str, new_due: date) -> TaskDeferResult:
    """
    Defer task to new date.

    Args:
        uuid: Task UUID
        new_due: New due date

    Returns:
        TaskDeferResult with confirmation

    Raises:
        TaskNotFoundError: Task doesn't exist
    """
    # Verify task exists
    task = get_task_info(uuid)
    if not task:
        raise TaskNotFoundError(uuid)

    description = task["description"]
    old_due = task.get("due")

    # Update due date
    modify_task(uuid, {"due": str(new_due)})

    return {
        "uuid": uuid,
        "description": description,
        "old_due": old_due,
        "new_due": str(new_due)
    }

def drop_task(uuid: str) -> TaskDropResult:
    """
    Drop/delete task from TaskWarrior.

    Args:
        uuid: Task UUID

    Returns:
        TaskDropResult with confirmation

    Raises:
        TaskNotFoundError: Task doesn't exist
    """
    # Verify task exists
    task = get_task_info(uuid)
    if not task:
        raise TaskNotFoundError(uuid)

    description = task["description"]

    # Delete task
    delete_task(uuid)

    return {
        "uuid": uuid,
        "description": description,
        "deleted_at": datetime.now().isoformat()
    }

def set_priority(uuid: str, priority: str) -> dict:
    """
    Set task priority.

    Args:
        uuid: Task UUID
        priority: Priority (H, M, L, or empty string for none)

    Returns:
        Confirmation dict

    Raises:
        TaskNotFoundError: Task doesn't exist
        ValueError: Invalid priority value
    """
    if priority not in ["H", "M", "L", ""]:
        raise ValueError(f"Invalid priority: {priority}")

    # Verify task exists
    task = get_task_info(uuid)
    if not task:
        raise TaskNotFoundError(uuid)

    # Set priority
    if priority == "":
        modify_task(uuid, {"priority": None})
    else:
        modify_task(uuid, {"priority": priority})

    return {
        "uuid": uuid,
        "description": task["description"],
        "priority": priority if priority else None
    }
```

---

### Phase 4: Core Inbox Workflow

**Goal:** Inbox read + process operations

**File to create:** `src/plorp/core/inbox.py` (~300 lines)

**Key functions:**
```python
def get_inbox_items(vault_path: Path) -> InboxData:
    """
    Get unprocessed inbox items.

    Pure read operation.

    Args:
        vault_path: Path to vault

    Returns:
        InboxData with unprocessed items

    Raises:
        VaultNotFoundError: Vault doesn't exist
        InboxNotFoundError: Inbox file doesn't exist
    """
    vault_path = vault_path.expanduser().resolve()
    if not vault_path.exists():
        raise VaultNotFoundError(str(vault_path))

    inbox_path = vault_path / "inbox.md"
    if not inbox_path.exists():
        raise InboxNotFoundError(str(inbox_path))

    # Parse unprocessed items
    items_text = parse_inbox_items(inbox_path)

    # Convert to InboxItem with line numbers
    items = []
    for idx, text in enumerate(items_text, start=1):
        items.append({
            "text": text,
            "line_number": idx
        })

    return {
        "inbox_path": str(inbox_path),
        "unprocessed_items": items,
        "item_count": len(items)
    }

def create_task_from_inbox(
    vault_path: Path,
    item_text: str,
    description: str,
    due: str | None = None,
    priority: str | None = None,
    project: str | None = None
) -> InboxProcessResult:
    """
    Create task from inbox item.

    Args:
        vault_path: Path to vault
        item_text: Original inbox item text
        description: Task description
        due: Due date (YYYY-MM-DD format)
        priority: Priority (H, M, L)
        project: Project name

    Returns:
        InboxProcessResult with task UUID
    """
    # Create task in TaskWarrior
    task_data = {"description": description}
    if due:
        task_data["due"] = due
    if priority:
        task_data["priority"] = priority
    if project:
        task_data["project"] = project

    uuid = create_task(**task_data)

    # Mark inbox item as processed
    inbox_path = vault_path / "inbox.md"
    mark_item_processed(inbox_path, item_text, f"Created task (uuid: {uuid})")

    return {
        "item_text": item_text,
        "action": "task",
        "task_uuid": uuid,
        "note_path": None
    }

def create_note_from_inbox(
    vault_path: Path,
    item_text: str,
    title: str,
    content: str = "",
    note_type: str = "general"
) -> InboxProcessResult:
    """
    Create note from inbox item.

    Args:
        vault_path: Path to vault
        item_text: Original inbox item text
        title: Note title
        content: Note content
        note_type: Note type (general, meeting, etc.)

    Returns:
        InboxProcessResult with note path
    """
    # Create note
    note_path = create_note(vault_path, title, note_type, content)

    # Mark inbox item as processed
    inbox_path = vault_path / "inbox.md"
    mark_item_processed(inbox_path, item_text, "Created note")

    return {
        "item_text": item_text,
        "action": "note",
        "task_uuid": None,
        "note_path": str(note_path)
    }

def create_both_from_inbox(
    vault_path: Path,
    item_text: str,
    task_description: str,
    note_title: str,
    note_content: str = "",
    due: str | None = None,
    priority: str | None = None,
    project: str | None = None
) -> InboxProcessResult:
    """
    Create both task and note from inbox item, linked together.

    Args:
        vault_path: Path to vault
        item_text: Original inbox item text
        task_description: Task description
        note_title: Note title
        note_content: Note content
        due: Task due date
        priority: Task priority
        project: Task project

    Returns:
        InboxProcessResult with both task UUID and note path
    """
    # Create task
    task_data = {"description": task_description}
    if due:
        task_data["due"] = due
    if priority:
        task_data["priority"] = priority
    if project:
        task_data["project"] = project

    uuid = create_task(**task_data)

    # Create note linked to task
    from plorp.core.notes import create_note_linked_to_task
    result = create_note_linked_to_task(
        vault_path=vault_path,
        title=note_title,
        task_uuid=uuid,
        note_type="general",
        content=note_content
    )

    # Mark inbox item as processed
    inbox_path = vault_path / "inbox.md"
    mark_item_processed(
        inbox_path,
        item_text,
        f"Created task and note (uuid: {uuid})"
    )

    return {
        "item_text": item_text,
        "action": "both",
        "task_uuid": uuid,
        "note_path": result["note_path"]
    }

def discard_inbox_item(vault_path: Path, item_text: str) -> InboxProcessResult:
    """
    Discard inbox item without creating anything.

    Args:
        vault_path: Path to vault
        item_text: Item to discard

    Returns:
        InboxProcessResult
    """
    inbox_path = vault_path / "inbox.md"
    mark_item_processed(inbox_path, item_text, "Discarded")

    return {
        "item_text": item_text,
        "action": "discard",
        "task_uuid": None,
        "note_path": None
    }
```

---

### Phase 5: Core Notes Workflow

**Goal:** Note creation and linking

**File to create:** `src/plorp/core/notes.py` (~250 lines)

**Key functions:**
```python
def create_note_standalone(
    vault_path: Path,
    title: str,
    note_type: str = "general",
    content: str = ""
) -> NoteCreateResult:
    """
    Create a standalone note (not linked to task).

    Args:
        vault_path: Path to vault
        title: Note title
        note_type: Note type (general, meeting, project)
        content: Note content

    Returns:
        NoteCreateResult

    Raises:
        VaultNotFoundError: Vault doesn't exist
    """
    vault_path = vault_path.expanduser().resolve()
    if not vault_path.exists():
        raise VaultNotFoundError(str(vault_path))

    # Create note
    note_path = create_note(vault_path, title, note_type, content)

    return {
        "note_path": str(note_path),
        "created_at": datetime.now().isoformat(),
        "title": title,
        "linked_task_uuid": None
    }

def create_note_linked_to_task(
    vault_path: Path,
    title: str,
    task_uuid: str,
    note_type: str = "general",
    content: str = ""
) -> NoteCreateResult:
    """
    Create note and link to task (bidirectional).

    Args:
        vault_path: Path to vault
        title: Note title
        task_uuid: Task UUID to link to
        note_type: Note type
        content: Note content

    Returns:
        NoteCreateResult

    Raises:
        VaultNotFoundError: Vault doesn't exist
        TaskNotFoundError: Task doesn't exist
    """
    vault_path = vault_path.expanduser().resolve()
    if not vault_path.exists():
        raise VaultNotFoundError(str(vault_path))

    # Verify task exists
    task = get_task_info(task_uuid)
    if not task:
        raise TaskNotFoundError(task_uuid)

    # Create note
    note_path = create_note(vault_path, title, note_type, content)

    # Link note to task (bidirectional)
    link_note_to_task(vault_path, note_path, task_uuid)

    return {
        "note_path": str(note_path),
        "created_at": datetime.now().isoformat(),
        "title": title,
        "linked_task_uuid": task_uuid
    }

def link_note_to_task(
    vault_path: Path,
    note_path: Path,
    task_uuid: str
) -> NoteLinkResult:
    """
    Link existing note to task (bidirectional).

    Args:
        vault_path: Path to vault
        note_path: Path to note
        task_uuid: Task UUID

    Returns:
        NoteLinkResult

    Raises:
        TaskNotFoundError: Task doesn't exist
        NoteNotFoundError: Note doesn't exist
        NoteOutsideVaultError: Note is outside vault
    """
    vault_path = vault_path.expanduser().resolve()
    note_path = note_path.expanduser().resolve()

    # Verify task exists
    task = get_task_info(task_uuid)
    if not task:
        raise TaskNotFoundError(task_uuid)

    # Verify note exists
    if not note_path.exists():
        raise NoteNotFoundError(str(note_path))

    # Verify note is inside vault
    if not note_path.is_relative_to(vault_path):
        raise NoteOutsideVaultError(str(note_path), str(vault_path))

    # Add task UUID to note front matter
    add_task_to_note_frontmatter(note_path, task_uuid)

    # Add note path as task annotation
    relative_path = note_path.relative_to(vault_path)
    normalized_path = str(relative_path.as_posix())
    annotation_text = f"plorp:note:{normalized_path}"

    # Check for duplicates before adding
    from plorp.integrations.taskwarrior import get_task_annotations
    existing = get_task_annotations(task_uuid)

    already_linked = False
    for ann in existing:
        if ann.startswith("plorp:note:"):
            existing_path = ann[11:]
            if Path(existing_path).as_posix() == normalized_path:
                already_linked = True
                break

    if not already_linked:
        add_annotation(task_uuid, annotation_text)

    return {
        "note_path": str(note_path),
        "task_uuid": task_uuid,
        "linked_at": datetime.now().isoformat()
    }
```

---

### Phase 6: MCP Server Implementation

**Goal:** Wrap core functions as MCP tools

**File to create:** `src/plorp/mcp_server.py` (~600 lines)

**MCP Tools (16 total):**

**Daily Workflow:**
1. `plorp_start_day(date: str) -> dict`

**Review Workflow:**
2. `plorp_get_review_tasks(date: str) -> dict`
3. `plorp_add_review_notes(date: str, went_well: str, could_improve: str, tomorrow: str) -> dict`

**Task Operations:**
4. `plorp_mark_task_completed(uuid: str) -> dict`
5. `plorp_defer_task(uuid: str, new_due: str) -> dict`
6. `plorp_drop_task(uuid: str) -> dict`
7. `plorp_set_task_priority(uuid: str, priority: str) -> dict`

**Inbox Workflow:**
8. `plorp_get_inbox_items() -> dict`
9. `plorp_create_task_from_inbox(item_text: str, description: str, due: str, priority: str, project: str) -> dict`
10. `plorp_create_note_from_inbox(item_text: str, title: str, content: str, note_type: str) -> dict`
11. `plorp_create_both_from_inbox(item_text: str, task_description: str, note_title: str, note_content: str, due: str, priority: str, project: str) -> dict`
12. `plorp_discard_inbox_item(item_text: str) -> dict`

**Note Operations:**
13. `plorp_create_note(title: str, note_type: str, content: str, task_uuid: str) -> dict`
14. `plorp_link_note_to_task(note_path: str, task_uuid: str) -> dict`

**Pattern for all tools:**
```python
@server.call_tool()
async def plorp_start_day(date_str: str) -> dict:
    """
    Generate daily note for specified date.

    Creates markdown file in vault/daily/{date}.md with tasks from TaskWarrior.

    Args:
        date_str: Date in ISO format (YYYY-MM-DD), e.g., "2025-10-06"

    Returns:
        {
            "note_path": str,
            "created_at": str (ISO timestamp),
            "date": str,
            "summary": {
                "overdue_count": int,
                "due_today_count": int,
                "recurring_count": int,
                "total_count": int
            },
            "tasks": [...]
        }

    Raises:
        ValueError: Daily note already exists or invalid date format
    """
    try:
        target_date = _parse_date(date_str)
        vault_path = _get_vault_path()
        result = daily.start_day(target_date, vault_path)
        return result
    except DailyNoteExistsError as e:
        raise ValueError(f"Daily note already exists: {e.note_path}")
    except ValueError as e:
        raise ValueError(f"Invalid date format: {date_str}")
```

**Server entry point:**
```python
async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Phase 7: CLI Refactor (Thin Wrapper)

**Goal:** Refactor CLI to call core functions

**File to update:** `src/plorp/cli.py` (~400 lines)

**Remove:** All workflow logic from CLI commands
**Add:** Calls to core functions with formatting

**Example refactor:**
```python
# OLD (v1.0):
@cli.command()
def start():
    config = load_config()
    from plorp.workflows.daily import start as daily_start
    note_path = daily_start(config)
    # Output already printed by workflow

# NEW (v1.1):
@cli.command()
def start():
    """Generate daily note for today."""
    config = load_config()
    vault_path = Path(config["vault_path"])

    try:
        result = daily.start_day(date.today(), vault_path)

        # Format for humans
        click.echo(f"✅ Daily note created: {result['note_path']}")

        summary = result['summary']
        total = summary['total_count']

        if total == 0:
            click.echo("📋 No pending tasks")
        else:
            click.echo(f"📋 Added {total} tasks:")
            if summary['overdue_count'] > 0:
                click.echo(f"  • {summary['overdue_count']} overdue")
            if summary['due_today_count'] > 0:
                click.echo(f"  • {summary['due_today_count']} due today")
            if summary['recurring_count'] > 0:
                click.echo(f"  • {summary['recurring_count']} recurring")

    except DailyNoteExistsError as e:
        click.echo(f"❌ Daily note already exists: {e.note_path}", err=True)
        raise click.Abort()
```

**All CLI commands refactored:**
- `plorp start` → calls `core.daily.start_day()`
- `plorp review` → calls `core.review.get_review_tasks()` + task operations
- `plorp inbox process` → calls `core.inbox.get_inbox_items()` + process functions
- `plorp note` → calls `core.notes.create_note_**()`
- `plorp link` → calls `core.notes.link_note_to_task()`

**New command:**
```python
@cli.command()
def init_claude():
    """Install slash commands for Claude Desktop."""
    import shutil

    source = Path(__file__).parent.parent.parent / ".claude" / "commands"
    dest = Path.home() / ".claude" / "commands"

    if not source.exists():
        click.echo("❌ Slash command templates not found", err=True)
        click.echo(f"💡 Expected at: {source}", err=True)
        raise click.Abort()

    dest.mkdir(parents=True, exist_ok=True)

    installed = []
    for cmd_file in source.glob("*.md"):
        shutil.copy(cmd_file, dest / cmd_file.name)
        installed.append(cmd_file.stem)

    if installed:
        click.echo(f"✅ Installed {len(installed)} slash commands:")
        for cmd in installed:
            click.echo(f"  • /{cmd}")
        click.echo(f"\n📁 Location: {dest}")
        click.echo("💡 Restart Claude Desktop to see them")
    else:
        click.echo("⚠️  No slash commands found to install")
```

---

### Phase 8: Slash Commands

**Goal:** Create recommended slash commands for Claude Desktop

**Files to create in `.claude/commands/`:**

**1. `start-day.md`**
```markdown
Call plorp_start_day with today's date in ISO format (YYYY-MM-DD).

Present the results in this exact format:

✅ Daily note created: {note_path}

Tasks for today:
• {overdue_count} overdue
• {due_today_count} due today
• {recurring_count} recurring
• {total_count} total

Do not add any additional commentary, analysis, or suggestions unless I specifically ask.
Do not call any other tools.
```

**2. `review-day.md`**
```markdown
Help me review my day interactively.

1. Call plorp_get_review_tasks with today's date
2. For each uncompleted task, ask me what happened:
   - Options: Done / Defer / Skip / Drop
3. Based on my answer:
   - Done → call plorp_mark_task_completed
   - Defer → ask for new date, call plorp_defer_task
   - Skip → ask for priority (H/M/L/none), call plorp_set_task_priority
   - Drop → call plorp_drop_task
4. After all tasks, ask for reflection:
   - What went well today?
   - What could be improved?
   - Notes for tomorrow
5. Call plorp_add_review_notes with my reflections

Keep the interaction concise and focused. Don't add commentary unless I ask for it.
```

**3. `process-inbox.md`**
```markdown
Help me process my inbox interactively.

1. Call plorp_get_inbox_items
2. For each item, show me the text and ask what to do:
   - Options: Task / Note / Both / Discard
3. Based on my answer:
   - Task → ask for description, due date, project, then call plorp_create_task_from_inbox
   - Note → ask for title and content, then call plorp_create_note_from_inbox
   - Both → ask for task and note details, then call plorp_create_both_from_inbox
   - Discard → call plorp_discard_inbox_item
4. After all items, confirm completion

Keep it concise and efficient. Don't suggest or analyze unless I ask.
```

**4. `create-note.md`**
```markdown
Help me create a new note.

Ask me:
1. Note title
2. Note type (general, meeting, or project)
3. Should this be linked to a task? (if yes, ask for task UUID)

Then call plorp_create_note with the provided information.

Confirm creation and show the note path.
```

**5. `link-note.md`**
```markdown
Help me link an existing note to a task.

Ask me:
1. Path to the note file
2. Task UUID to link to

Then call plorp_link_note_to_task.

Confirm the link was created successfully.
```

---

### Phase 9: Dependencies & Configuration

**Goal:** Update project dependencies and configuration

**File to update:** `pyproject.toml`

```toml
[project]
name = "plorp"
version = "1.1.0"
description = "Workflow automation for TaskWarrior + Obsidian (MCP-first architecture)"
authors = [{name = "John", email = "jsd@example.com"}]
readme = "README.md"
requires-python = ">=3.10"

dependencies = [
    "click>=8.1.0",
    "PyYAML>=6.0.0",
    "mcp>=1.0.0",  # NEW - MCP SDK
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",  # NEW - for async MCP tests
    "black>=23.7.0",
]

[project.scripts]
plorp = "plorp.cli:cli"
plorp-mcp = "plorp.mcp_server:main"  # NEW - MCP server entry point

[build-system]
requires = ["setuptools>=68.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--strict-markers --cov=src/plorp --cov-report=term-missing"
asyncio_mode = "auto"  # NEW - for async tests

[tool.black]
line-length = 100
target-version = ["py310"]
```

**Claude Desktop Configuration:**

Location: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "plorp": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/jsd/Documents/plorp",
        "run",
        "plorp-mcp"
      ]
    }
  }
}
```

---

### Phase 10: Testing

**Goal:** Comprehensive test coverage for core and MCP

**Test Coverage Targets:**
- `plorp.core.*`: 90%+ coverage
- `plorp.mcp_server`: 85%+ coverage
- `plorp.cli`: 70%+ coverage

**Files to create:**

**Core Tests:**
- `tests/test_core/test_types.py` (~50 lines) - Test TypedDict validation
- `tests/test_core/test_exceptions.py` (~50 lines) - Test exception behavior
- `tests/test_core/test_daily.py` (~200 lines) - Test daily workflow
- `tests/test_core/test_review.py` (~150 lines) - Test review workflow
- `tests/test_core/test_tasks.py` (~150 lines) - Test task operations
- `tests/test_core/test_inbox.py` (~200 lines) - Test inbox workflow
- `tests/test_core/test_notes.py` (~200 lines) - Test note operations

**MCP Tests:**
- `tests/test_mcp/test_tools.py` (~200 lines) - Test all 16 MCP tools

**CLI Tests:**
- `tests/test_cli.py` (~200 lines, updated) - Test CLI wrapper

**Example core test:**
```python
# tests/test_core/test_daily.py
def test_start_day_creates_note(tmp_path):
    """Test that start_day creates daily note with correct structure."""
    vault = tmp_path / "vault"
    vault.mkdir()

    from datetime import date
    from plorp.core.daily import start_day

    with patch('plorp.integrations.taskwarrior.get_pending_tasks') as mock_tasks:
        mock_tasks.return_value = [
            {
                "uuid": "abc-123",
                "description": "Test task",
                "status": "pending",
                "due": "20251006T000000Z"
            }
        ]

        result = start_day(date(2025, 10, 6), vault)

        # Assert structured return
        assert result["note_path"].endswith("2025-10-06.md")
        assert result["summary"]["total_count"] == 1
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["uuid"] == "abc-123"

        # Assert file created
        note_path = Path(result["note_path"])
        assert note_path.exists()
        content = note_path.read_text()
        assert "# Daily Note - 2025-10-06" in content

def test_start_day_raises_on_existing_note(tmp_path):
    """Test that start_day raises error if note already exists."""
    vault = tmp_path / "vault"
    vault.mkdir()

    daily_dir = vault / "daily"
    daily_dir.mkdir()

    # Create existing note
    existing_note = daily_dir / "2025-10-06.md"
    existing_note.write_text("# Existing")

    from datetime import date
    from plorp.core.daily import start_day
    from plorp.core.exceptions import DailyNoteExistsError

    with pytest.raises(DailyNoteExistsError) as exc:
        start_day(date(2025, 10, 6), vault)

    assert exc.value.date == "2025-10-06"
    assert str(existing_note) in exc.value.note_path
```

**Example MCP test:**
```python
# tests/test_mcp/test_tools.py
@pytest.mark.asyncio
async def test_plorp_start_day_tool(tmp_path):
    """Test MCP tool wrapper for start_day."""
    from plorp.mcp_server import plorp_start_day

    with patch('plorp.mcp_server._get_vault_path') as mock_vault:
        mock_vault.return_value = tmp_path

        with patch('plorp.core.daily.start_day') as mock_start:
            mock_start.return_value = {
                "note_path": "/vault/daily/2025-10-06.md",
                "created_at": "2025-10-06T09:00:00",
                "date": "2025-10-06",
                "summary": {
                    "overdue_count": 0,
                    "due_today_count": 1,
                    "recurring_count": 0,
                    "total_count": 1
                },
                "tasks": []
            }

            result = await plorp_start_day("2025-10-06")

            assert result["note_path"] == "/vault/daily/2025-10-06.md"
            assert result["summary"]["total_count"] == 1
            mock_start.assert_called_once()

@pytest.mark.asyncio
async def test_plorp_start_day_error_handling():
    """Test MCP tool handles errors correctly."""
    from plorp.mcp_server import plorp_start_day
    from plorp.core.exceptions import DailyNoteExistsError

    with patch('plorp.mcp_server._get_vault_path'):
        with patch('plorp.core.daily.start_day') as mock_start:
            mock_start.side_effect = DailyNoteExistsError(
                "2025-10-06",
                "/vault/daily/2025-10-06.md"
            )

            with pytest.raises(ValueError, match="already exists"):
                await plorp_start_day("2025-10-06")
```

**Total test lines: ~1200**

---

### Phase 11: Documentation

**Goal:** Comprehensive documentation for v1.1

**1. MCP_SETUP.md** (~500 lines)

```markdown
# plorp MCP Server Setup

## Prerequisites
- plorp v1.1 installed
- Claude Desktop installed
- TaskWarrior 3.x configured
- Obsidian vault configured in plorp config

## Installation

1. Install plorp v1.1:
```bash
cd /Users/jsd/Documents/plorp
pip install -e .
```

2. Verify installation:
```bash
plorp --version  # Should show 1.1.0
plorp-mcp --help  # Should show MCP server info
```

3. Configure Claude Desktop:

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "plorp": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/jsd/Documents/plorp",
        "run",
        "plorp-mcp"
      ]
    }
  }
}
```

4. Install slash commands:
```bash
plorp init-claude
```

5. Restart Claude Desktop

6. Verify in Claude Desktop:
```
What plorp tools do you have available?
```

Claude should list all 16 plorp_* tools.

## Available Tools

[Detailed documentation of all 16 tools with args, returns, examples]

## Slash Commands

[Documentation of all 5 slash commands]

## Usage Patterns

[Examples of common workflows]

## Troubleshooting

[Common issues and solutions]
```

**2. ARCHITECTURE.md** (~300 lines)

```markdown
# plorp v1.1 Architecture

## Design Philosophy

plorp v1.1 is built on MCP-first architecture...

## Core Principles

1. Structured Return Values
2. Interface Separation
3. No Interactive Prompts in Core

## Module Architecture

[Detailed breakdown of each module]

## Data Flow

[Diagrams and examples]

## Design Decisions

[Rationale for key decisions]

## Extension Points

[How to extend plorp]
```

**3. MIGRATION_GUIDE.md** (~200 lines)

```markdown
# Migrating from plorp v1.0 to v1.1

## Breaking Changes

### Removed: plorp.workflows.*

All `plorp.workflows.*` modules have been removed.

**v1.0 code (no longer works):**
```python
from plorp.workflows.daily import start as daily_start
from plorp.config import load_config

config = load_config()
daily_start(config)
```

**v1.1 replacement:**
```python
from plorp.core.daily import start_day
from plorp.config import load_config
from pathlib import Path
from datetime import date

config = load_config()
result = start_day(date.today(), Path(config["vault_path"]))
```

### CLI Commands (No Changes)

All CLI commands work identically:
```bash
plorp start
plorp review
plorp inbox process
plorp note "Title"
plorp link <uuid> <path>
```

## Migration Steps

1. Update plorp: `pip install --upgrade plorp`
2. If you only use CLI: No changes needed
3. If you import plorp in scripts: Update imports to `plorp.core.*`
4. Test your workflows
5. Setup MCP if desired (optional)

## Feature Comparison

[Table showing v1.0 vs v1.1 features]

## New Capabilities

- MCP server with 16 tools
- Slash commands for Claude Desktop
- Rich structured data from all functions
- Better testability
```

**4. EXAMPLE_WORKFLOWS.md** (~200 lines)

```markdown
# plorp Example Workflows

## Daily Routine Workflows

### Morning Startup

**Via CLI:**
```bash
plorp start
```

**Via Claude Desktop (slash command):**
```
/start-day
```

**Via Claude Desktop (natural language):**
```
Start my day
```

**Expected output:**
```
✅ Daily note created: /vault/daily/2025-10-06.md

Tasks for today:
• 2 overdue
• 5 due today
• 3 recurring
• 10 total
```

### Evening Review

[Detailed walkthrough]

## Inbox Processing

[Examples]

## Note Management

[Examples]

## Advanced Workflows

### Custom Agent Workflows

**Example: Weekly planning**
```
User: "Help me plan next week"

Claude:
1. Calls plorp_get_review_tasks for each day of past week
2. Analyzes task completion patterns
3. Suggests time blocking for next week
4. Offers to create tasks for planning
```

### Combining Multiple Tools

[Examples of agent orchestrating multiple plorp tools]

## Troubleshooting Common Workflows

[Solutions to common issues]
```

**5. README.md Update** (~200 lines added)

Update existing README with:
- v1.1 architecture overview
- Quick start guide for MCP
- Links to new docs
- Migration notice

---

## Implementation Checklist

### Phase 0: Core Types & Exceptions
- [ ] Create `src/plorp/core/__init__.py`
- [ ] Create `src/plorp/core/types.py` (150 lines)
  - [ ] Define TaskInfo, TaskSummary
  - [ ] Define DailyStartResult, ReviewData, ReviewResult
  - [ ] Define InboxItem, InboxData, InboxProcessResult
  - [ ] Define NoteCreateResult, NoteLinkResult
- [ ] Create `src/plorp/core/exceptions.py` (80 lines)
  - [ ] Define PlorpError base class
  - [ ] Define VaultNotFoundError
  - [ ] Define DailyNoteExistsError, DailyNoteNotFoundError
  - [ ] Define TaskNotFoundError
  - [ ] Define NoteNotFoundError, NoteOutsideVaultError
  - [ ] Define InboxNotFoundError
- [ ] Write tests: `tests/test_core/test_types.py` (50 lines)
- [ ] Write tests: `tests/test_core/test_exceptions.py` (50 lines)

### Phase 1: Core Daily Workflow
- [ ] Create `src/plorp/core/daily.py` (250 lines)
  - [ ] Implement `start_day()` function
  - [ ] Implement `_normalize_task()` helper
  - [ ] Implement `_is_overdue()`, `_is_due_today()`, `_is_recurring()` helpers
  - [ ] Implement `_format_daily_note()` helper
- [ ] Write tests: `tests/test_core/test_daily.py` (200 lines)
  - [ ] Test successful daily note creation
  - [ ] Test error when note already exists
  - [ ] Test task categorization (overdue, due today, recurring)
  - [ ] Test empty task list
  - [ ] Test vault not found error

### Phase 2: Core Review Workflow
- [ ] Create `src/plorp/core/review.py` (180 lines)
  - [ ] Implement `get_review_tasks()` function
  - [ ] Implement `add_review_notes()` function
- [ ] Write tests: `tests/test_core/test_review.py` (150 lines)
  - [ ] Test getting uncompleted tasks
  - [ ] Test adding review notes
  - [ ] Test daily note not found error
  - [ ] Test multiple review sections (appending)

### Phase 3: Core Task Operations
- [ ] Create `src/plorp/core/tasks.py` (200 lines)
  - [ ] Implement `mark_completed()` function
  - [ ] Implement `defer_task()` function
  - [ ] Implement `drop_task()` function
  - [ ] Implement `set_priority()` function
- [ ] Write tests: `tests/test_core/test_tasks.py` (150 lines)
  - [ ] Test marking task completed
  - [ ] Test deferring task
  - [ ] Test dropping task
  - [ ] Test setting priority
  - [ ] Test task not found errors

### Phase 4: Core Inbox Workflow
- [ ] Create `src/plorp/core/inbox.py` (300 lines)
  - [ ] Implement `get_inbox_items()` function
  - [ ] Implement `create_task_from_inbox()` function
  - [ ] Implement `create_note_from_inbox()` function
  - [ ] Implement `create_both_from_inbox()` function
  - [ ] Implement `discard_inbox_item()` function
- [ ] Write tests: `tests/test_core/test_inbox.py` (200 lines)
  - [ ] Test getting inbox items
  - [ ] Test creating task from inbox
  - [ ] Test creating note from inbox
  - [ ] Test creating both from inbox
  - [ ] Test discarding item
  - [ ] Test inbox not found error

### Phase 5: Core Notes Workflow
- [ ] Create `src/plorp/core/notes.py` (250 lines)
  - [ ] Implement `create_note_standalone()` function
  - [ ] Implement `create_note_linked_to_task()` function
  - [ ] Implement `link_note_to_task()` function
- [ ] Write tests: `tests/test_core/test_notes.py` (200 lines)
  - [ ] Test creating standalone note
  - [ ] Test creating note linked to task
  - [ ] Test linking existing note to task
  - [ ] Test note outside vault error
  - [ ] Test duplicate link prevention

### Phase 6: MCP Server Implementation
- [ ] Create `src/plorp/mcp_server.py` (600 lines)
  - [ ] Setup MCP server boilerplate
  - [ ] Implement helper functions (_get_vault_path, _parse_date)
  - [ ] Implement daily workflow tools (1 tool)
    - [ ] `plorp_start_day`
  - [ ] Implement review workflow tools (2 tools)
    - [ ] `plorp_get_review_tasks`
    - [ ] `plorp_add_review_notes`
  - [ ] Implement task operation tools (4 tools)
    - [ ] `plorp_mark_task_completed`
    - [ ] `plorp_defer_task`
    - [ ] `plorp_drop_task`
    - [ ] `plorp_set_task_priority`
  - [ ] Implement inbox workflow tools (5 tools)
    - [ ] `plorp_get_inbox_items`
    - [ ] `plorp_create_task_from_inbox`
    - [ ] `plorp_create_note_from_inbox`
    - [ ] `plorp_create_both_from_inbox`
    - [ ] `plorp_discard_inbox_item`
  - [ ] Implement note operation tools (2 tools)
    - [ ] `plorp_create_note`
    - [ ] `plorp_link_note_to_task`
  - [ ] Implement server main() function
- [ ] Write tests: `tests/test_mcp/test_tools.py` (200 lines)
  - [ ] Test all 16 MCP tools
  - [ ] Test error handling in tools
  - [ ] Test date parsing
  - [ ] Test config loading

### Phase 7: CLI Refactor
- [ ] Update `src/plorp/cli.py` (400 lines)
  - [ ] Refactor `start` command to use `core.daily.start_day()`
  - [ ] Refactor `review` command to use `core.review.*` and `core.tasks.*`
  - [ ] Refactor `inbox` command to use `core.inbox.*`
  - [ ] Refactor `note` command to use `core.notes.*`
  - [ ] Refactor `link` command to use `core.notes.link_note_to_task()`
  - [ ] Add new `init-claude` command
- [ ] Update tests: `tests/test_cli.py` (200 lines)
  - [ ] Test all refactored CLI commands
  - [ ] Test `init-claude` command
  - [ ] Test error handling and formatting

### Phase 8: Slash Commands
- [ ] Create `.claude/commands/` directory
- [ ] Create `.claude/commands/start-day.md`
- [ ] Create `.claude/commands/review-day.md`
- [ ] Create `.claude/commands/process-inbox.md`
- [ ] Create `.claude/commands/create-note.md`
- [ ] Create `.claude/commands/link-note.md`

### Phase 9: Dependencies & Configuration
- [ ] Update `pyproject.toml`
  - [ ] Bump version to 1.1.0
  - [ ] Add `mcp>=1.0.0` dependency
  - [ ] Add `pytest-asyncio>=0.21.0` dev dependency
  - [ ] Add `plorp-mcp` entry point
  - [ ] Add `asyncio_mode = "auto"` to pytest config
- [ ] Document Claude Desktop config in setup docs

### Phase 10: Testing
- [ ] Run all tests: `pytest tests/`
- [ ] Verify coverage: `pytest tests/ --cov=src/plorp --cov-report=term`
- [ ] Ensure coverage targets met:
  - [ ] `plorp.core.*`: 90%+
  - [ ] `plorp.mcp_server`: 85%+
  - [ ] `plorp.cli`: 70%+
- [ ] Fix any failing tests
- [ ] Add missing test cases

### Phase 11: Documentation
- [ ] Create `Docs/MCP_SETUP.md` (500 lines)
  - [ ] Installation instructions
  - [ ] Claude Desktop configuration
  - [ ] Tool reference (all 16 tools)
  - [ ] Slash command documentation
  - [ ] Usage patterns
  - [ ] Troubleshooting
- [ ] Create `Docs/ARCHITECTURE.md` (300 lines)
  - [ ] Design philosophy
  - [ ] Core principles
  - [ ] Module architecture
  - [ ] Data flow diagrams
  - [ ] Design decisions
  - [ ] Extension points
- [ ] Create `Docs/MIGRATION_GUIDE.md` (200 lines)
  - [ ] Breaking changes
  - [ ] Migration steps
  - [ ] Feature comparison
  - [ ] New capabilities
- [ ] Create `Docs/EXAMPLE_WORKFLOWS.md` (200 lines)
  - [ ] Daily routine workflows
  - [ ] Inbox processing examples
  - [ ] Note management examples
  - [ ] Advanced agent workflows
  - [ ] Troubleshooting common workflows
- [ ] Update `README.md` (200 lines added)
  - [ ] v1.1 overview
  - [ ] Quick start for MCP
  - [ ] Links to new docs
  - [ ] Migration notice

### Phase 12: Integration Testing
- [ ] Test full workflows end-to-end
  - [ ] Test `plorp start` CLI command
  - [ ] Test `plorp review` CLI command
  - [ ] Test `plorp inbox process` CLI command
  - [ ] Test `plorp note` and `plorp link` CLI commands
  - [ ] Test `plorp init-claude` command
- [ ] Test MCP server manually
  - [ ] Start `plorp-mcp` server
  - [ ] Configure in Claude Desktop
  - [ ] Test all 16 tools via Claude
  - [ ] Test slash commands
- [ ] Test error scenarios
  - [ ] Missing vault
  - [ ] Duplicate daily notes
  - [ ] Invalid task UUIDs
  - [ ] Network/TaskWarrior failures

### Phase 13: Final Cleanup
- [ ] Remove deprecated `src/plorp/workflows/` directory
- [ ] Update `.gitignore` if needed
- [ ] Run linter: `black src/ tests/`
- [ ] Final test run: `pytest tests/`
- [ ] Verify all docs are complete
- [ ] Tag release: `git tag v1.1.0`

---

## Engineering Q&A

### Questions for Lead Engineer

**Q1: TypedDict vs Dataclass?**

**Context:** Core functions return structured data. Spec uses TypedDict.

**Options:**
- **A)** TypedDict (spec'd) - Simple, compatible with JSON serialization, no runtime overhead
- **B)** Dataclass - Better IDE support, runtime validation, more pythonic
- **C)** Pydantic models - Full validation, great for APIs, adds dependency

**Recommendation:** TypedDict for simplicity and MCP compatibility.

**Answer:** ✅ **Option A - TypedDict** (as spec'd). JSON-friendly, no extra dependencies.

**Status:** RESOLVED

---

**Q2: Date handling in core functions?**

**Context:** Core functions accept `date` objects. MCP tools accept ISO strings.

**Options:**
- **A)** Core uses `datetime.date`, MCP parses strings (spec'd)
- **B)** Core accepts strings, validates internally
- **C)** Core accepts both (overloading)

**Recommendation:** Option A - clean separation, type safety in core.

**Answer:** ✅ **Option A - Core uses `date` objects, MCP parses ISO strings**. Clean type safety.

**Status:** RESOLVED

---

**Q3: Error handling - raise or return?**

**Context:** When task not found, note already exists, etc.

**Options:**
- **A)** Raise exceptions (spec'd) - Pythonic, clear error path
- **B)** Return error dicts - Easier for MCP tools, no exception handling
- **C)** Hybrid - exceptions in core, error dicts in MCP

**Recommendation:** Option A - exceptions in core, MCP converts to ValueError.

**Answer:** ✅ **Option A - Raise exceptions in core**. MCP tools catch and convert to ValueError.

**Status:** RESOLVED

---

**Q4: Async core functions?**

**Context:** MCP tools are async. Core functions are sync.

**Options:**
- **A)** Core functions sync, MCP wraps with async (spec'd) - Simple, works fine
- **B)** Core functions async - More consistent, but unnecessary complexity
- **C)** Separate sync/async implementations - Duplication

**Recommendation:** Option A - core sync, MCP async wrapper is fine.

**Answer:** ✅ **Option A - Core sync, MCP async wrappers**. No unnecessary async complexity in core.

**Status:** RESOLVED

---

**Q5: TaskWarrior integration - subprocess or library?**

**Context:** Current v1.0 uses subprocess. Any reason to change?

**Options:**
- **A)** Keep subprocess (spec assumes this) - Works, stable, no new deps
- **B)** Use taskw library - More pythonic, but another dependency
- **C)** Direct SQLite - Faster, but fragile (TaskWarrior schema changes)

**Recommendation:** Option A - keep subprocess, it works.

**Answer:** ✅ **Option A - Keep subprocess**. Stable, works, no new dependencies.

**Status:** RESOLVED

---

**Q6: Testing - mock or real TaskWarrior?**

**Context:** Core tests need TaskWarrior data.

**Options:**
- **A)** Mock TaskWarrior calls (like v1.0) - Fast, isolated
- **B)** Use real TaskWarrior test database - Realistic, but slower
- **C)** Both - Mock for unit tests, real for integration tests

**Recommendation:** Option A for core tests, Option C if time allows.

**Answer:** ✅ **Option A - Mock TaskWarrior calls**. Fast, isolated unit tests. Can add real integration tests later if needed.

**Status:** RESOLVED

---

**Q7: MCP tool docstrings - how detailed?**

**Context:** MCP tool docstrings are visible to Claude.

**Options:**
- **A)** Detailed with examples (spec'd) - Better agent understanding
- **B)** Minimal one-liners - Faster to write
- **C)** Auto-generate from core docstrings - DRY, but may lose MCP-specific info

**Recommendation:** Option A - detailed docstrings help the agent.

**Answer:** ✅ **Option A - Detailed docstrings with args, returns, examples**. Critical for agent understanding.

**Status:** RESOLVED

---

**Q8: Slash command installation - overwrite or skip existing?**

**Context:** `plorp init-claude` copies slash commands to `~/.claude/commands/`.

**Options:**
- **A)** Always overwrite - Simple, ensures latest version
- **B)** Skip if exists - Preserves user customizations
- **C)** Prompt user for each file - Tedious but safest
- **D)** Add `--force` flag, default skip - Best of both worlds

**Recommendation:** Option D - skip by default, `--force` to overwrite.

**Answer:** ✅ **Option D - Skip by default, add `--force` flag**. Preserves customizations, allows updates.

**Status:** RESOLVED

---

**Q9: Inbox item identification - by text or line number?**

**Context:** When processing inbox items, need to identify which item to mark processed.

**Current spec:** By text matching (item_text parameter)

**Concern:** What if user has duplicate items in inbox?

**Options:**
- **A)** Keep text matching, mark only first occurrence - Simple, spec'd
- **B)** Add line_number parameter - More precise, more complex
- **C)** Use item index (0, 1, 2...) - Simpler API, but brittle if inbox changes

**Recommendation:** Option A - text matching is fine, duplicates are edge case.

**Answer:** ✅ **Option A - Text matching, mark first occurrence**. Duplicates are edge case, keep it simple.

**Status:** RESOLVED

---

**Q10: Note type validation?**

**Context:** Notes can be "general", "meeting", "project". Should we validate?

**Options:**
- **A)** No validation - Accept any string, flexible
- **B)** Validate against enum - Type-safe, but rigid
- **C)** Warn on unknown types - Middle ground

**Recommendation:** Option A - flexibility for user extensions.

**Answer:** ✅ **Option A - No validation**. Accept any string, allows user extensions.

**Status:** RESOLVED

---

**Q11: Return value consistency - paths as strings or Path objects?**

**Context:** Core functions work with Path objects internally.

**Options:**
- **A)** Return strings (spec'd) - JSON-serializable, MCP-friendly
- **B)** Return Path objects - More pythonic, but not JSON-serializable
- **C)** Return both (dict with both formats) - Redundant

**Recommendation:** Option A - strings for JSON compatibility.

**Answer:** ✅ **Option A - Return paths as strings**. JSON-serializable, MCP-compatible.

**Status:** RESOLVED

---

**Q12: Integration test fixtures - shared or per-module?**

**Context:** Tests need vault, TaskWarrior data, etc.

**Options:**
- **A)** Shared fixtures in conftest.py - DRY, consistent
- **B)** Per-module fixtures - More isolated, easier to debug
- **C)** Mix - Shared for common setup, per-module for specific cases

**Recommendation:** Option C - shared vault/config, module-specific data.

**Answer:** ✅ **Option C - Hybrid approach**. Shared fixtures for vault/config in conftest.py, module-specific test data.

**Status:** RESOLVED

---

**Q13: MCP server error messages - technical or user-friendly?**

**Context:** When MCP tool raises ValueError, what message format?

**Options:**
- **A)** Technical: "Task not found: abc-123" (spec'd) - Clear, actionable
- **B)** User-friendly: "I couldn't find that task. Would you like to create it?" - Helpful, but verbose
- **C)** Error codes: "ERROR_TASK_NOT_FOUND: abc-123" - Structured, but ugly

**Recommendation:** Option A - clear technical messages, let agent make them friendly.

**Answer:** ✅ **Option A - Technical messages**. Clear and actionable, let Claude make them friendly in conversation.

**Status:** RESOLVED

---

**Q14: Inbox file structure - single inbox.md or monthly files?**

**Context:** Spec Phase 4 shows `vault_path / "inbox.md"`, but CLAUDE.md references "Monthly inbox files (YYYY-MM.md)" in `vault/inbox/` directory.

**Conflict:** Spec assumes single file, but existing v1.0 uses monthly files.

**Options:**
- **A)** Single `inbox.md` file - Simpler, matches Phase 4 code
- **B)** Monthly files `inbox/YYYY-MM.md` - Matches CLAUDE.md, better organization
- **C)** Make it configurable - Most flexible, more complex

**Question:** Which structure should v1.1 use?

**Answer:** ✅ **Option B - Monthly files `vault/inbox/YYYY-MM.md`**

**Implementation change:** Update Phase 4 code to use:
```python
inbox_path = vault_path / "inbox" / f"{date.today().strftime('%Y-%m')}.md"
```

**Status:** RESOLVED

---

**Q15: Daily note format - Task UUID visibility in markdown?**

**Context:** CLAUDE.md says daily notes include "markdown checkboxes with task metadata in parentheses including UUID" with format `- [ ] Description (project: X, due: Y, uuid: Z)`.

**Question:** Should `_format_daily_note()` helper include:
- **A)** Full metadata with UUID visible (as CLAUDE.md suggests) - More transparent, allows manual editing
- **B)** Minimal format with UUID hidden in HTML comment - Cleaner markdown
- **C)** No UUID in daily note, rely only on description matching - Simpler but fragile

**Recommendation:** Option A for transparency and robustness.

**Answer:** ✅ **Option A - Full metadata visible** including UUID. Format: `- [ ] Description (project: X, due: Y, uuid: Z)`

**Status:** RESOLVED

---

**Q16: Review workflow - Parse tasks from daily note or query TaskWarrior?**

**Context:** Phase 2 `get_review_tasks()` shows parsing daily note for uncompleted checkboxes, then fetching full data from TaskWarrior.

**Question:** What if task was deleted from TaskWarrior after daily note creation?
- **A)** Skip missing tasks silently
- **B)** Return task info with `status: "missing"`
- **C)** Raise TaskNotFoundError

**Recommendation:** Option A - skip silently, it's a valid edge case.

**Answer:** ✅ **Option B - Return task with `status: "missing"`** so user can see it during review and decide what to do.

**Implementation:**
```python
task_data = get_task_info(uuid)
if task_data:
    uncompleted_tasks.append(_normalize_task(task_data))
else:
    # Task deleted from TaskWarrior
    uncompleted_tasks.append({
        "uuid": uuid,
        "description": description,
        "status": "missing",
        "due": None,
        "priority": None,
        "project": None,
        "tags": []
    })
```

**Status:** RESOLVED

---

**Q17: Note creation - Where do different note types go?**

**Context:** `create_note_standalone()` accepts `note_type: str = "general"` with examples "general", "meeting", "project".

**Question:** Should note type determine subdirectory?
- **A)** All notes in `vault/notes/` regardless of type - Simple
- **B)** Type determines subdirectory: `vault/notes/general/`, `vault/notes/meetings/`, etc. - Organized
- **C)** Follow existing v1.0 pattern (check integration/obsidian.py) - Consistent

**Question:** What does v1.0 `create_note()` in `integrations/obsidian.py` do currently?

**Answer:** ✅ **Option C - Follow v1.0 pattern**

v1.0 pattern (from `integrations/obsidian.py`):
- `note_type="meeting"` → `vault/meetings/`
- All other types → `vault/notes/`

This is already implemented in the integration layer, so core functions automatically get this behavior.

**Status:** RESOLVED

---

**Q18: Bidirectional linking - Annotation format?**

**Context:** Phase 5 shows annotation format `plorp:note:{normalized_path}` added to tasks.

**Question:** Should we also add a prefix to note frontmatter for symmetry?
- **A)** Note frontmatter uses `tasks: [uuid1, uuid2]` (simpler, spec'd)
- **B)** Note frontmatter uses `plorp_tasks: [uuid1, uuid2]` (namespaced, safer)
- **C)** Use both for backward compatibility

**Recommendation:** Option A - simple `tasks:` field is fine, unlikely to conflict.

**Answer:** ✅ **Option A - Use `tasks:` field** in note frontmatter. Simple, clean, unlikely to conflict with Obsidian conventions.

**Status:** RESOLVED

---

**Q19: MCP server configuration - Load once or per-call?**

**Context:** MCP tools call `_get_vault_path()` helper to get vault location.

**Options:**
- **A)** Load config once on server startup, cache vault_path - Faster
- **B)** Load config on every tool call - Respects live config changes
- **C)** Hybrid - Cache with TTL or file watch - Complex

**Recommendation:** Option A - load once, restart server if config changes.

**Answer:** ✅ **Option A - Load config once on server startup**. User can restart MCP server if they change config. Simpler and faster.

**Status:** RESOLVED

---

**Q20: CLI review command - Behavior change from v1.0?**

**Context:** v1.0 `plorp review` is interactive (prompts for each task). v1.1 refactor should maintain same UX.

**Question:** Confirm CLI `review` command should:
1. Call `core.review.get_review_tasks()` to get task list
2. Loop through tasks with interactive prompts (using `prompts.interactive`)
3. Call appropriate `core.tasks.*` functions based on user choice
4. Call `core.review.add_review_notes()` for final reflection

**This matches v1.0 behavior but uses core functions instead of workflow module, correct?**

**Answer:** ✅ **Confirmed - matches v1.0 UX, uses core functions**. UX is fine for now, will refine later.

**Status:** RESOLVED

---

**Q21: MCP tool granularity - 16 tools or fewer with parameters?**

**Context:** Spec defines 16 separate tools. Alternative would be fewer tools with "action" parameters.

**Example alternative:**
- `plorp_process_task(uuid, action, params)` instead of separate `plorp_mark_task_completed`, `plorp_defer_task`, etc.

**Options:**
- **A)** 16 focused tools (spec'd) - More discoverable, clearer to agent
- **B)** Fewer tools with action params - More flexible, less code
- **C)** Hybrid - Group related tools

**Recommendation:** Option A - focused tools are clearer for LLM.

**Answer:** ✅ **Option A - 16 focused tools**. Better discoverability for the agent, clearer semantics.

**Status:** RESOLVED

---

**Q22: Testing strategy - Missing integrations/obsidian.py functions?**

**Context:** Phase 4 inbox and Phase 5 notes call functions like:
- `parse_inbox_items(inbox_path)`
- `mark_item_processed(inbox_path, item_text, annotation)`
- `create_note(vault_path, title, note_type, content)`
- `add_task_to_note_frontmatter(note_path, task_uuid)`

**Question:** Do these functions exist in current `integrations/obsidian.py`?

If not, should we:
- **A)** Add them to `integrations/obsidian.py` (keeps integrations layer intact)
- **B)** Implement them in core modules directly (more self-contained)
- **C)** Verify existing functions first before deciding

**Recommendation:** Option C - read `integrations/obsidian.py` to see what exists.

**Answer:** ✅ **Verified - functions exist:**
- `create_note()` exists in `integrations/obsidian.py` ✓
- `add_task_to_note_frontmatter()` exists in `parsers/markdown.py` ✓
- `parse_inbox_items()` exists in `parsers/markdown.py` ✓
- `mark_item_processed()` exists in `parsers/markdown.py` ✓

All required functions already exist from v1.0. Core will use them as-is.

**Status:** RESOLVED

---

**Q23: Error messages - Include suggestions or just facts?**

**Context:** Exception messages like `DailyNoteExistsError`.

**Options:**
- **A)** Just facts: "Daily note already exists: {path}" (spec'd)
- **B)** With suggestions: "Daily note already exists: {path}. Use --force to overwrite or open existing note."
- **C)** Suggestions in CLI formatting only, exceptions stay factual

**Recommendation:** Option C - exceptions factual, CLI adds helpful suggestions.

**Answer:** ✅ **Option C - Factual exceptions, helpful CLI**. Exceptions contain facts only, CLI can add suggestions when displaying to user.

**Status:** RESOLVED

---

**Q24: Recurring tasks - Special handling needed?**

**Context:** Daily workflow categorizes tasks as overdue, due today, or recurring.

**Question:** For recurring tasks:
- **A)** Include them every day in daily note - User sees them consistently
- **B)** Only include if "due today" according to recurrence - Less noise
- **C)** Make it configurable

**Recommendation:** Check v1.0 `workflows/daily.py` behavior and maintain compatibility.

**Answer:** ✅ **Option B - Only show when due** (matches v1.0)

v1.0 uses `get_recurring_today()` which queries `["status:pending", "recur.any:", "due:today"]` - only shows recurring tasks that are due today.

**Status:** RESOLVED

---

**Q25: MCP server - Error logging strategy?**

**Context:** MCP server runs in background, errors may not be visible to user.

**Options:**
- **A)** Log errors to file (`~/.config/plorp/mcp.log`) - Debuggable
- **B)** No logging, rely on MCP protocol error returns - Simpler
- **C)** Optional logging via config flag - Flexible

**Recommendation:** Option A - background services should log errors.

**Answer:** ✅ **Option A - Log to `~/.config/plorp/mcp.log`**. Background services need error logging for debugging.

**Implementation:** Add basic logging setup in `mcp_server.py`:
```python
import logging

logging.basicConfig(
    filename=Path.home() / ".config" / "plorp" / "mcp.log",
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

**Status:** RESOLVED

---

## Summary

**Total Estimated Effort:** 17 hours

**Code to Write:**
- Core modules: ~1400 lines
- MCP server: ~600 lines
- CLI refactor: ~400 lines
- Tests: ~1200 lines
- Slash commands: ~100 lines
- Docs: ~1400 lines
- **Total: ~5100 lines**

**Coverage Targets:**
- Core: 90%+
- MCP: 85%+
- CLI: 70%+

**Deliverables:**
1. Working MCP server with 16 tools
2. Refactored CLI using core functions
3. Comprehensive test suite
4. Complete documentation (5 docs)
5. Slash commands for Claude Desktop

**Migration Impact:**
- Breaking: `plorp.workflows.*` removed
- Compatible: All CLI commands work identically
- New: MCP server, slash commands, rich return values

**Q&A Status:**
- ✅ All 25 questions RESOLVED
- Technical decisions documented
- User experience decisions confirmed
- Implementation details specified

**Key Decisions:**
- Monthly inbox files: `vault/inbox/YYYY-MM.md`
- Full task metadata visible in daily notes
- Missing tasks shown with `status: "missing"` during review
- v1.0 note directory pattern maintained
- Recurring tasks only shown when due (matches v1.0)
- MCP error logging to `~/.config/plorp/mcp.log`

---

---

## Implementation Summary

**Implementation Complete:** 2025-10-06
**Time Spent:** ~17 hours (full rewrite)

**Lines Written:**
- Core modules (`src/plorp/core/*.py`): ~2,063 lines total
  - `daily.py`: Core daily note generation logic
  - `review.py`: End-of-day review workflow
  - `tasks.py`: Task operations (complete, defer, priority, drop)
  - `inbox.py`: Inbox processing workflow
  - `notes.py`: Note creation and task linking
  - `types.py`: TypedDict definitions for all return values
  - `exceptions.py`: Custom exception hierarchy
- MCP server (`src/plorp/mcp/server.py`): 741 lines
  - 16 tools exposed to Claude Desktop
  - Async wrappers around core functions
  - Error handling and logging
- CLI refactor (`src/plorp/cli.py`): Refactored to use core functions
- Tests: 22 test files with comprehensive coverage
- Slash commands: 5 commands for Claude Desktop
- **Total: ~5,100+ lines (as estimated)**

**Test Coverage:**
- All existing tests passing (270+ tests before Sprint 7)
- Core modules: 90%+ coverage achieved
- MCP integration: Tested via 3 integration tests
- CLI: Regression tests confirm compatibility

**MCP Tools Implemented (16):**
1. `plorp_start_day` - Generate daily note
2. `plorp_get_review_tasks` - Get tasks for review
3. `plorp_add_review_notes` - Add review notes to daily note
4. `plorp_mark_task_completed` - Complete a task
5. `plorp_defer_task` - Defer task to new date
6. `plorp_drop_task` - Delete a task
7. `plorp_set_task_priority` - Change task priority
8. `plorp_get_inbox_items` - Get unprocessed inbox items
9. `plorp_create_task_from_inbox` - Convert inbox item to task
10. `plorp_create_note_from_inbox` - Convert inbox item to note
11. `plorp_create_both_from_inbox` - Create task and note from inbox item
12. `plorp_discard_inbox_item` - Mark inbox item as processed (discarded)
13. `plorp_create_note` - Create standalone note
14. `plorp_create_note_with_task` - Create note linked to new task
15. `plorp_link_note_to_task` - Link existing note to existing task
16. `plorp_get_task_info` - Get detailed task information

**Key Architectural Decisions:**
1. **TypedDict Pattern** - All core functions return structured dictionaries
2. **MCP-First Design** - Core functions optimized for rich data return
3. **Pure Functions** - No I/O decisions in core layer (no print, no click.echo)
4. **Exception Hierarchy** - Custom exceptions for error handling
5. **Async MCP Layer** - MCP server uses async wrappers for integration
6. **CLI Compatibility** - All existing CLI commands work identically

**Manual Testing:**
- ✅ CLI: All commands (`start`, `review`, `inbox process`, `note`, `link`) working
- ✅ MCP: All 16 tools responding correctly in Claude Desktop
- ✅ Integration: TaskWarrior and Obsidian operations verified
- ✅ Regression: Existing workflows continue to function

**Migration Notes:**
- ✅ Breaking: `plorp.workflows.*` removed (as documented)
- ✅ Compatible: CLI commands remain identical for end users
- ✅ New: MCP server enables Claude Desktop integration
- ✅ Tested: All slash commands work in Claude Desktop

---

## Lead Engineer Handoff

**Completion Status:** ✅ ALL PHASES COMPLETE (0-10)

**What Was Built:**
This sprint was a complete architectural rewrite from v1.0 to v1.1:

1. **Core Engine** - Pure Python functions returning TypedDict structures
2. **MCP Server** - 16 tools for Claude Desktop integration
3. **CLI Wrapper** - Refactored to consume core functions
4. **Type System** - Complete TypedDict definitions for all interfaces
5. **Documentation** - Architecture guide, migration guide, MCP setup guide

**How to Verify:**
```bash
# Check MCP tools exist (should show 16 before Sprint 7's addition)
grep -c "name=\"plorp_" src/plorp/mcp/server.py

# Check core modules
ls src/plorp/core/

# Run tests
pytest tests/ -v

# Test MCP server (requires Claude Desktop config)
# See Docs/MCP_SETUP.md for configuration
```

**Key Files:**
- `src/plorp/core/*.py` - Core business logic (pure functions)
- `src/plorp/mcp/server.py` - MCP server with 16 tools
- `src/plorp/cli.py` - Refactored CLI (thin wrapper)
- `Docs/ARCHITECTURE.md` - Architecture documentation
- `Docs/MCP_SETUP.md` - Claude Desktop setup guide
- `Docs/MIGRATION_GUIDE.md` - v1.0 to v1.1 migration

**Known Issues:**
- None at completion

**Next Sprint Dependencies:**
Sprint 7 depends on this MCP foundation to add the `/process` command.

**Engineer Notes:**
This rewrite establishes the pattern for all future development:
1. Write core function returning TypedDict
2. Add MCP tool as async wrapper
3. Add/update CLI command as thin wrapper
4. Test both interfaces

The architecture is now stable and extensible.

---

**STATUS: ✅ COMPLETE (2025-10-06)**

**Document Version:** 1.2
**Last Updated:** 2025-10-07 (completion notes added by PM)
**PM Approval:** ✅ APPROVED
**Q&A Status:** ✅ ALL RESOLVED
**Implementation:** ✅ COMPLETE
