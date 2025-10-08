# plorp v1.1 Architecture

This document describes the architecture of plorp v1.1, which introduces an MCP-first design while maintaining backward compatibility with the CLI interface.

## Design Philosophy

plorp v1.1 follows a **layered architecture** that separates concerns:

1. **Core Layer** - Pure business logic, deterministic, no I/O decisions
2. **MCP Layer** - Async wrappers, handles ambiguity and user interaction (stochastic)
3. **CLI Layer** - Thin wrapper around core functions, provides traditional CLI UX
4. **Integration Layer** - External tool adapters (TaskWarrior, Obsidian)

## Layer Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interfaces                           │
├──────────────────────┬──────────────────────────────────────┤
│   Claude Desktop     │          Terminal / Shell            │
│   (MCP Client)       │          (Direct CLI)                │
└──────────┬───────────┴──────────────────┬───────────────────┘
           │                              │
           │                              │
           ▼                              ▼
  ┌─────────────────┐          ┌──────────────────┐
  │   MCP Server    │          │   CLI Commands   │
  │  (plorp-mcp)    │          │   (plorp cli)    │
  └────────┬────────┘          └────────┬─────────┘
           │                            │
           │    ┌───────────────────────┘
           │    │
           ▼    ▼
    ┌─────────────────────────────────────────┐
    │           Core Business Logic           │
    │  (plorp.core.*)                         │
    │                                         │
    │  • daily.py    - Daily note generation │
    │  • review.py   - End-of-day review     │
    │  • tasks.py    - Task operations       │
    │  • inbox.py    - Inbox processing      │
    │  • notes.py    - Note creation/linking │
    │  • types.py    - TypedDict definitions │
    │  • exceptions.py - Custom exceptions   │
    └─────────────┬───────────────────────────┘
                  │
                  ▼
    ┌─────────────────────────────────────────┐
    │       Integration Layer                 │
    │  (plorp.integrations.*)                 │
    │                                         │
    │  • taskwarrior.py - TaskWarrior CLI    │
    │  • obsidian.py    - Markdown files     │
    └─────────────┬───────────────────────────┘
                  │
                  ▼
    ┌─────────────────────────────────────────┐
    │         External Systems                │
    │                                         │
    │  • TaskWarrior 3.x (SQLite)            │
    │  • Obsidian Vault (Markdown files)     │
    └─────────────────────────────────────────┘
```

## Core Layer

### Responsibilities

The core layer contains **pure business logic** with these characteristics:

- **Deterministic**: Same inputs → same outputs
- **No I/O decisions**: Doesn't prompt users or make ambiguous choices
- **Type-safe**: Uses TypedDict for all return values (JSON-serializable)
- **Exception-based**: Raises custom exceptions for error cases
- **Testable**: Can be fully tested with mocks, no external dependencies

### Modules

#### `plorp.core.types`

Defines all TypedDict return types:

```python
class TaskInfo(TypedDict):
    uuid: str
    description: str
    status: Literal["pending", "completed", "deleted", "missing"]
    due: str | None
    priority: Literal["H", "M", "L", ""] | None
    project: str | None
    tags: list[str]

class DailyStartResult(TypedDict):
    date: str
    note_path: str
    summary: TaskSummary
```

#### `plorp.core.exceptions`

Custom exceptions with structured data:

```python
class DailyNoteExistsError(PlorpError):
    def __init__(self, date: str, note_path: str):
        self.date = date
        self.note_path = note_path
        super().__init__(f"Daily note already exists: {note_path}")
```

#### `plorp.core.daily`

Daily note generation:

```python
def start_day(target_date: date, vault_path: Path) -> DailyStartResult:
    """Generate daily note with tasks from TaskWarrior."""
    # Pure logic - no prompts, no I/O decisions
    # Raises DailyNoteExistsError if note exists
    ...
```

#### `plorp.core.review`

End-of-day review:

```python
def get_review_tasks(review_date: date, vault_path: Path) -> ReviewData:
    """Get uncompleted tasks from daily note."""
    # Returns task list with status="missing" for deleted tasks
    ...

def add_review_notes(
    review_date: date,
    vault_path: Path,
    went_well: str,
    could_improve: str,
    notes_for_tomorrow: str,
) -> ReviewNotesResult:
    """Append review section to daily note."""
    ...
```

#### `plorp.core.tasks`

Task manipulation operations:

```python
def mark_completed(task_uuid: str) -> TaskCompleteResult:
    """Mark task as done in TaskWarrior."""
    ...

def defer_task(task_uuid: str, new_due_date: str) -> TaskDeferResult:
    """Defer task to new date."""
    ...
```

#### `plorp.core.inbox`

Inbox processing:

```python
def get_inbox_items(vault_path: Path, target_date: date | None = None) -> InboxData:
    """Get unprocessed inbox items from monthly file."""
    # Uses YYYY-MM.md format
    ...

def create_task_from_inbox(
    vault_path: Path,
    item_text: str,
    description: str,
    due: str | None = None,
    priority: str | None = None,
    project: str | None = None,
) -> InboxTaskResult:
    """Create TaskWarrior task from inbox item."""
    ...
```

#### `plorp.core.notes`

Note creation and linking:

```python
def create_note_standalone(
    vault_path: Path,
    title: str,
    content: str = "",
    note_type: str = "general",
) -> NoteCreateResult:
    """Create standalone note."""
    ...

def create_note_linked_to_task(
    vault_path: Path,
    title: str,
    task_uuid: str,
    content: str = "",
    note_type: str = "general",
) -> NoteLinkResult:
    """Create note with bidirectional link to task."""
    ...
```

## MCP Layer

### Responsibilities

The MCP server (`plorp.mcp.server`) handles:

- **Ambiguity resolution**: When core raises exceptions, decide how to respond
- **Async coordination**: Wraps synchronous core functions in async
- **Error conversion**: Converts PlorpError → ValueError for MCP protocol
- **Configuration caching**: Loads config once on startup
- **Logging**: Writes to `~/.config/plorp/mcp.log`

### Tool Design

Each tool follows this pattern:

```python
@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    try:
        if name == "plorp_start_day":
            return await _plorp_start_day(arguments)
        ...
    except PlorpError as e:
        # Convert to ValueError for MCP protocol
        raise ValueError(str(e))

async def _plorp_start_day(args: Dict[str, Any]) -> list[TextContent]:
    """Generate daily note."""
    date_str = args.get("date")
    target_date = date.fromisoformat(date_str) if date_str else date.today()

    # Call core function
    result = start_day(target_date, VAULT_PATH)

    # Return JSON result
    return [TextContent(type="text", text=json.dumps(result, indent=2))]
```

### Error Handling

The MCP layer converts core exceptions to user-friendly messages:

```python
try:
    result = start_day(target_date, vault_path)
except DailyNoteExistsError as e:
    raise ValueError(
        f"Daily note already exists at {e.note_path}. "
        f"Open the existing note or delete it first."
    )
```

## CLI Layer

### Responsibilities

The CLI (`plorp.cli`) provides:

- **Traditional UX**: Command-line interface for direct usage
- **Interactive prompts**: Uses rich for formatted output
- **Configuration loading**: Reads `~/.config/plorp/config.yaml`
- **Error formatting**: Displays errors with colors and emojis

### Command Structure

Each CLI command is a thin wrapper around core functions:

```python
@cli.command()
@click.option("--date", "date_str", default=None, help="Date (YYYY-MM-DD)")
@click.pass_context
def start(ctx, date_str):
    """Generate daily note for today."""
    config = load_config()
    vault_path = Path(config["vault_path"]).expanduser().resolve()
    target_date = date.fromisoformat(date_str) if date_str else date.today()

    try:
        result = start_day(target_date, vault_path)

        # Rich formatting
        console.print(f"[green]✅ Created daily note:[/green] {result['note_path']}")
        console.print()

        summary = result["summary"]
        console.print(f"[yellow]📊 Task Summary:[/yellow]")
        console.print(f"  Overdue: {summary['overdue_count']}")
        console.print(f"  Due today: {summary['due_today_count']}")
        console.print(f"  Recurring: {summary['recurring_count']}")

    except DailyNoteExistsError as e:
        console.print(f"[red]❌ Daily note already exists:[/red] {e.note_path}")
        console.print("[dim]💡 Tip: Open the existing note or delete it first[/dim]")
        ctx.exit(1)
```

## Integration Layer

### TaskWarrior Integration

Strategy: **CLI-based writes, subprocess-based reads**

```python
def create_task(description: str, due: str | None = None, ...) -> TaskInfo:
    """Create task via TaskWarrior CLI."""
    cmd = ["task", "add", description]
    if due:
        cmd.extend([f"due:{due}"])

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    # Parse UUID from output, then export to get full task data
    uuid = _extract_uuid(result.stdout)
    task_data = get_task_info(uuid)
    return _normalize_task(task_data)
```

**Never write directly to SQLite** - this bypasses TaskChampion's operation log.

### Obsidian Integration

Strategy: **Direct markdown file manipulation**

```python
def create_note(vault_path: Path, title: str, content: str, ...) -> Path:
    """Create markdown note in vault."""
    slug = generate_slug(title)
    note_dir = vault_path / _get_subdir_for_type(note_type)
    note_path = note_dir / f"{slug}.md"

    # Generate frontmatter
    frontmatter = {
        "title": title,
        "created": date.today().isoformat(),
        "type": note_type,
    }

    # Write markdown file
    note_content = _format_note(frontmatter, content)
    ensure_directory(note_dir)
    write_file(note_path, note_content)

    return note_path
```

## Data Flow Examples

### Example 1: Daily Start via MCP

```
User (Claude Desktop)
  ↓
  Types: "/start"
  ↓
Claude calls: plorp_start_day(date=null)
  ↓
MCP Server
  ↓
  Calls: start_day(date.today(), vault_path)
  ↓
Core Layer
  ↓
  1. Query TaskWarrior for tasks (Integration Layer)
  2. Categorize overdue, due_today, recurring
  3. Generate markdown content
  4. Write to vault/daily/YYYY-MM-DD.md
  5. Return DailyStartResult
  ↓
MCP Server
  ↓
  Converts to JSON, returns to Claude
  ↓
User sees: Summary of tasks + file path
```

### Example 2: Review via CLI

```
User (Terminal)
  ↓
  Types: plorp review
  ↓
CLI Command
  ↓
  Calls: get_review_tasks(date.today(), vault_path)
  ↓
Core Layer
  ↓
  1. Parse daily note markdown
  2. Extract unchecked tasks with UUIDs
  3. Query TaskWarrior for each UUID
  4. Mark deleted tasks as status="missing"
  5. Return ReviewData
  ↓
CLI Command
  ↓
  For each uncompleted task:
    1. Display task details
    2. Prompt user: done, defer, priority, skip, delete
    3. Call core function (mark_completed, defer_task, etc.)
  ↓
  Prompt for reflections (went_well, could_improve, notes)
  ↓
  Call: add_review_notes(date, vault, reflections)
  ↓
User sees: "✅ Review complete!"
```

## Design Decisions

### Why TypedDict?

TypedDict ensures JSON serialization compatibility for MCP while providing type hints for development.

### Why Separate Core from MCP/CLI?

- **Testability**: Core can be tested without MCP server or CLI infrastructure
- **Reusability**: Core functions can be used by any interface
- **Separation of concerns**: Business logic vs. user interaction

### Why Both MCP and CLI?

- **MCP**: AI-first interface, natural language interaction
- **CLI**: Traditional interface, scripting, automation

Both share the same core logic.

### Why Custom Exceptions?

Custom exceptions carry structured data (e.g., `DailyNoteExistsError.note_path`) that layers above can use for better error messages.

## Performance Considerations

- **Config caching**: MCP server loads config once on startup
- **TaskWarrior subprocess**: Fast for individual operations, would need optimization for bulk operations
- **File I/O**: Direct file access is fast, no database overhead

## Security Considerations

- **TaskWarrior CLI**: Uses subprocess, respects TaskWarrior's security model
- **File paths**: All vault paths resolved and validated against vault root
- **No SQL injection**: TaskWarrior CLI handles escaping

## Future Extensibility

The layered architecture allows:

- **New interfaces**: Web UI, mobile app (just add new layer calling core)
- **New integrations**: Todoist, Notion (add to integration layer)
- **New workflows**: Archive, search (add to core layer)

The core layer remains stable while interfaces evolve.
