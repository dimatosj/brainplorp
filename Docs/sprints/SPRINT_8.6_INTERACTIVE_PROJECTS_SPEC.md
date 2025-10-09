# Sprint 8.6 Spec: Interactive Project Notes & Scoped Workflows

**Version:** 2.1.0
**Status:** ✅ APPROVED - Ready for Implementation
**Sprint:** 8.6 (Enhancement sprint between 8.5 and 9)
**Estimated Effort:** 13-18 hours
**Dependencies:** Sprint 8 (Project Management), Sprint 8.5 (State Sync)
**Type:** Architectural Fix, State Sync Extension
**Date:** 2025-10-08

---

## Executive Summary

Sprint 8.6 completes the State Synchronization pattern for projects by ensuring that **project note bodies always reflect their frontmatter state**. This is not a new feature - it's fixing incomplete State Sync from Sprint 8.

**The Gap (Sprint 8):**
- Project frontmatter has `task_uuids: [abc-123, def-456]` ✅
- Project note body has no task section ❌
- User can't see tasks without calling MCP tools ❌
- State is incomplete: frontmatter exists, visual representation doesn't ❌

**The Fix (Sprint 8.6):**
- Every operation that modifies `task_uuids` updates the `## Tasks` section automatically ✅
- Project notes always show current tasks ✅
- User can check boxes to mark tasks done (like daily notes) ✅
- State Sync is complete: frontmatter ↔ note body ↔ TaskWarrior ✅

**This is State Synchronization, not "rendering":**
> When TaskWarrior changes → Obsidian frontmatter updates → Obsidian note body updates
>
> When Obsidian note changes → TaskWarrior updates → Obsidian frontmatter updates
>
> All three surfaces must stay synchronized.

---

## Goals

### Primary Goals (Must Have)

1. **Complete State Sync for Projects** ⭐ ARCHITECTURAL FIX
   - Internal helper: `_sync_project_task_section(vault, project_path)`
   - Called automatically by all project modification functions
   - Ensures note body always matches frontmatter
   - This is infrastructure, not a user-facing feature

2. **Retrofit Existing Project Functions** 🔧 CLEANUP
   - Update `create_task_in_project()` to sync task section
   - Update Sprint 8.5's auto-sync to update task section
   - Update `delete_project()`, `rename_project()`, etc.
   - Every `task_uuids` modification triggers section update

3. **Checkbox Sync for Project Notes** ⭐ USER-FACING
   - User checks box in project note → marks task done
   - `/process` can target project notes (not just daily notes)
   - Same UX as daily notes
   - Leverages Sprint 8.5 State Sync + new task section sync

4. **Scoped Workflows** 🎯 USER-FACING
   - `/process` by project: "process work.engineering.api-rewrite"
   - `/review` by project/domain/workstream
   - Enable focused work sessions

5. **Admin Sync-All Command** 🔧 MAINTENANCE
   - `plorp sync-all` - Sync all project notes
   - Idempotent bulk reconciliation
   - For migration, debugging, recovery

### Non-Goals (Explicitly Out of Scope)

- ❌ Manual "render" commands (this is automatic)
- ❌ User-triggered task section updates (this is infrastructure)
- ❌ Configuration for when to sync (always sync)
- ❌ Partial sync (all-or-nothing)

---

## Problem Statement

### The Incomplete State Sync

**Sprint 8 created project notes with frontmatter:**
```yaml
---
project: work.engineering.api-rewrite
task_uuids:
  - abc-123
  - def-456
  - ghi-789
---

# API Rewrite

Project description...
```

**Problem:** Frontmatter has state, but note body doesn't reflect it.

**This violates State Synchronization:**
- TaskWarrior knows about tasks ✅
- Frontmatter references tasks ✅
- Note body shows nothing ❌

**The user can't see tasks without:**
1. Calling `plorp_list_project_tasks` MCP tool
2. Reading TaskWarrior output
3. Mentally mapping UUIDs to descriptions

**This is a State Sync failure, not a missing feature.**

### The Correct Architecture

**State Synchronization requires THREE surfaces to stay in sync:**

```
┌─────────────────────────────────────────────────────┐
│                    TaskWarrior                      │
│         task abc-123 (description, due, etc.)       │
└──────────────────────┬──────────────────────────────┘
                       │
                       │ State Sync
                       │
┌──────────────────────▼──────────────────────────────┐
│              Obsidian Frontmatter                   │
│              task_uuids: [abc-123]                  │
└──────────────────────┬──────────────────────────────┘
                       │
                       │ State Sync (MISSING IN SPRINT 8)
                       │
┌──────────────────────▼──────────────────────────────┐
│               Obsidian Note Body                    │
│   ## Tasks (1)                                      │
│   - [ ] Description (due: X, uuid: abc-123)         │
└─────────────────────────────────────────────────────┘
```

**All three must update together. If frontmatter updates but note body doesn't, State Sync is broken.**

---

## Architecture: Automatic Task Section Sync

### Core Principle

> Every function that modifies `task_uuids` in frontmatter MUST call `_sync_project_task_section()` before returning.

This is not optional. This is not configurable. This is State Synchronization.

### The Pattern

**Before (Sprint 8 - WRONG):**
```python
def create_task_in_project(vault_path, project_path, task_data):
    # 1. Create task in TaskWarrior
    uuid = create_task(task_data)

    # 2. Add UUID to frontmatter
    add_uuid_to_project_frontmatter(vault_path, project_path, uuid)

    # 3. Add annotation
    annotate_task(uuid, f"plorp-project:{project_path}")

    return {"uuid": uuid}

    # ❌ Note body still empty - State Sync incomplete!
```

**After (Sprint 8.6 - CORRECT):**
```python
def create_task_in_project(vault_path, project_path, task_data):
    # 1. Create task in TaskWarrior
    uuid = create_task(task_data)

    # 2. Add UUID to frontmatter
    add_uuid_to_project_frontmatter(vault_path, project_path, uuid)

    # 3. Add annotation
    annotate_task(uuid, f"plorp-project:{project_path}")

    # 4. Sync note body (NEW - State Sync completion)
    _sync_project_task_section(vault_path, project_path)

    return {"uuid": uuid}

    # ✅ Frontmatter AND note body both updated - State Sync complete!
```

### Implementation

**New internal helper:** `src/plorp/core/projects.py`

```python
def _sync_project_task_section(
    vault_path: Path,
    project_path: str
) -> None:
    """
    Update the ## Tasks section in project note to match frontmatter.

    This is INTERNAL infrastructure called by all project modification
    functions. NOT a user-facing command.

    State Sync Pattern:
    - Frontmatter has task_uuids → note body shows those tasks
    - Frontmatter empty → note body has no task section
    - Always in sync

    Args:
        vault_path: Path to Obsidian vault
        project_path: Full project path (e.g., "work.engineering.api-rewrite")

    Returns:
        None (modifies file in place)

    Raises:
        ProjectNotFoundError: If project note doesn't exist
    """
    # 1. Read project note
    note_path = vault_path / "projects" / f"{project_path}.md"
    if not note_path.exists():
        raise ProjectNotFoundError(f"Project note not found: {note_path}")

    content = note_path.read_text()
    frontmatter, body = parse_frontmatter(content)

    # 2. Get task UUIDs from frontmatter
    task_uuids = frontmatter.get("task_uuids", [])

    # 3. Query TaskWarrior for task details
    tasks = []
    for uuid in task_uuids:
        try:
            task = get_task_by_uuid(uuid)
            tasks.append(task)
        except TaskNotFoundError:
            # Orphaned UUID - skip (Sprint 8.5 reconciliation will clean)
            continue

    # 4. Remove existing ## Tasks section from body
    body_without_tasks = _remove_section(body, "## Tasks")

    # 5. Build new Tasks section
    if tasks:
        task_lines = []
        for task in tasks:
            status = task.get("status", "pending")
            checkbox = "[x]" if status == "completed" else "[ ]"
            desc = task["description"]

            # Metadata
            metadata = []
            if "due" in task:
                due_str = _format_date(task["due"])
                metadata.append(f"due: {due_str}")
            if "priority" in task:
                metadata.append(f"priority: {task['priority']}")
            metadata.append(f"uuid: {task['uuid']}")

            meta_str = ", ".join(metadata)
            task_lines.append(f"- {checkbox} {desc} ({meta_str})")

        tasks_section = f"## Tasks ({len(tasks)})\n\n"
        tasks_section += "\n".join(task_lines)
        tasks_section += "\n"

        # Append to body
        new_body = body_without_tasks.rstrip() + "\n\n" + tasks_section
    else:
        # No tasks - don't add section
        new_body = body_without_tasks

    # 6. Write updated note
    new_content = _format_with_frontmatter(frontmatter, new_body)
    note_path.write_text(new_content)
```

**Helper functions:** `src/plorp/parsers/markdown.py`

```python
def _remove_section(content: str, section_heading: str) -> str:
    """
    Remove a markdown section from content.

    Section defined as:
    - Starts with heading (e.g., "## Tasks")
    - Ends at next same-level heading or end of document
    """
    lines = content.split("\n")
    result = []
    in_target_section = False
    section_level = None

    for line in lines:
        # Check if this is the target section heading
        if line.strip() == section_heading:
            in_target_section = True
            section_level = len(line) - len(line.lstrip("#"))
            continue

        # Check if we've reached next same-level heading
        if in_target_section and line.startswith("#"):
            current_level = len(line) - len(line.lstrip("#"))
            if current_level <= section_level:
                in_target_section = False

        # Include line if not in target section
        if not in_target_section:
            result.append(line)

    return "\n".join(result)


def _format_date(date_str: str) -> str:
    """Format TaskWarrior date for display (20251010T000000Z → 2025-10-10)"""
    # Implementation...


def _format_with_frontmatter(frontmatter: dict, body: str) -> str:
    """Combine frontmatter dict and body into markdown with --- delimiters"""
    # Implementation...
```

---

## Item 1: Retrofit Existing Functions

**Priority:** CRITICAL ⭐
**Effort:** 4-5 hours
**Dependencies:** `_sync_project_task_section()` implementation

### What This Fixes

Every Sprint 8 function that modifies `task_uuids` now calls `_sync_project_task_section()`.

**Functions to update:**

**`src/plorp/core/projects.py`:**
1. `create_task_in_project()` - After adding UUID to frontmatter
2. `delete_project()` - N/A (whole note deleted)
3. `update_project_state()` - N/A (doesn't affect tasks)

**`src/plorp/core/review.py` (from Sprint 8.5):**
4. After calling `remove_task_from_all_projects()` - sync affected projects

**`src/plorp/core/process.py` (from Sprint 8.5):**
5. After syncing checkboxes in daily note - if task belongs to project, sync that project

**`scripts/reconcile_taskwarrior.py` (from Sprint 8.5):**
6. After removing UUIDs from projects - sync affected projects

### Implementation

**Example: `create_task_in_project()`**

```python
def create_task_in_project(
    vault_path: Path,
    project_path: str,
    description: str,
    due: Optional[date] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create task in TaskWarrior and link to project.

    State Sync (3 surfaces):
    1. TaskWarrior: Create task
    2. Obsidian frontmatter: Add UUID
    3. Obsidian note body: Update task section  ← NEW
    """
    # Validate project exists
    project_info = get_project_info(vault_path, project_path)

    # Create task in TaskWarrior
    uuid = create_task(
        description=description,
        project=f"project.{project_path}",
        due=due,
        priority=priority,
        tags=tags
    )

    # Add UUID to project frontmatter
    _add_uuid_to_project_frontmatter(vault_path, project_path, uuid)

    # Add annotation
    note_rel_path = f"projects/{project_path}.md"
    annotate_task(uuid, f"plorp-project:{note_rel_path}")

    # STATE SYNC: Update note body to match frontmatter (NEW)
    _sync_project_task_section(vault_path, project_path)

    return {
        "uuid": uuid,
        "description": description,
        "project": project_path,
        "created": True
    }
```

**Example: Sprint 8.5's `remove_task_from_all_projects()`**

```python
def remove_task_from_all_projects(vault_path: Path, uuid: str) -> List[str]:
    """
    Remove task UUID from all project frontmatter.

    Called by:
    - /review when marking task done
    - /review when deleting task
    - Undo log reconciliation

    State Sync:
    - Remove from frontmatter
    - Update note body (NEW)
    """
    projects_dir = vault_path / "projects"
    affected_projects = []

    for project_file in projects_dir.rglob("*.md"):
        content = project_file.read_text()

        if not content.startswith("---"):
            continue

        frontmatter, body = parse_frontmatter(content)
        task_uuids = frontmatter.get("task_uuids", [])

        if uuid in task_uuids:
            # Remove UUID
            task_uuids.remove(uuid)
            frontmatter["task_uuids"] = task_uuids

            # Write updated frontmatter
            new_content = _format_with_frontmatter(frontmatter, body)
            project_file.write_text(new_content)

            # Track which project was affected
            project_path = project_file.stem  # e.g., "work.engineering.api-rewrite"
            affected_projects.append(project_path)

    # STATE SYNC: Update note bodies for all affected projects (NEW)
    for project_path in affected_projects:
        _sync_project_task_section(vault_path, project_path)

    return affected_projects
```

### Tests

**New tests in `tests/test_core/test_projects.py`:**

1. `test_sync_project_task_section_creates_section()` - Adds Tasks section
2. `test_sync_project_task_section_updates_existing()` - Replaces old section
3. `test_sync_project_task_section_preserves_content()` - User content safe
4. `test_sync_project_task_section_formats_correctly()` - Checkbox format
5. `test_sync_project_task_section_handles_empty()` - No tasks case
6. `test_sync_project_task_section_skips_orphaned()` - Missing UUIDs
7. `test_create_task_in_project_syncs_note_body()` - Integration test
8. `test_remove_task_from_all_projects_syncs_note_body()` - Integration test

**Expected test count:** +8 tests

### Success Criteria

- [ ] `_sync_project_task_section()` implemented
- [ ] All Sprint 8 functions updated to call sync
- [ ] All Sprint 8.5 functions updated to call sync
- [ ] Note bodies always match frontmatter
- [ ] User content preserved during sync
- [ ] All tests pass

---

## Item 2: Checkbox Sync for Project Notes

**Priority:** CRITICAL ⭐
**Effort:** 3-4 hours
**Dependencies:** Item 1 (auto-sync infrastructure)

### User Experience

**Workflow:**
1. User opens `vault/projects/work.engineering.api-rewrite.md`
2. Sees tasks (automatically synced from previous operations):
   ```markdown
   ## Tasks (3)
   - [ ] Design API schema (due: 2025-10-10, uuid: abc-123)
   - [ ] Implement auth (due: 2025-10-12, uuid: def-456)
   - [ ] Write migration (uuid: ghi-789)
   ```
3. User checks first task:
   ```markdown
   - [x] Design API schema (due: 2025-10-10, uuid: abc-123)
   ```
4. User runs `/process` targeting this project:
   ```
   User: "Process work.engineering.api-rewrite project"
   Claude: *calls plorp_process_project_note("work.engineering.api-rewrite")*
   Result: "1 task marked done and synced"
   ```

**This is the same UX as daily notes.**

### Implementation

**New function:** `src/plorp/core/projects.py`

```python
def process_project_note(
    vault_path: Path,
    project_path: str
) -> Dict[str, Any]:
    """
    Process project note checkboxes (sync Obsidian → TaskWarrior).

    Same pattern as process_daily_note_step2, but for project notes.

    State Sync (3 surfaces):
    1. User checks box in Obsidian note body
    2. This function marks task done in TaskWarrior
    3. Removes UUID from frontmatter (Sprint 8.5 pattern)
    4. Updates note body to reflect new frontmatter (Item 1)

    Returns:
        {
            "project_path": "work.engineering.api-rewrite",
            "tasks_synced": 2,
            "tasks_completed": ["abc-123", "def-456"],
            "errors": []
        }
    """
    # 1. Read project note
    note_path = vault_path / "projects" / f"{project_path}.md"
    if not note_path.exists():
        raise ProjectNotFoundError(f"Project note not found: {note_path}")

    content = note_path.read_text()
    frontmatter, body = parse_frontmatter(content)

    # 2. Find checked boxes in Tasks section
    checked_uuids = []

    for line in body.split("\n"):
        # Match: - [x] Description (...uuid: abc-123...)
        match = re.search(r'-\s*\[x\]\s+.*uuid:\s*([a-f0-9-]+)', line, re.IGNORECASE)
        if match:
            uuid = match.group(1)
            checked_uuids.append(uuid)

    if not checked_uuids:
        return {
            "project_path": project_path,
            "tasks_synced": 0,
            "tasks_completed": [],
            "errors": []
        }

    # 3. Mark tasks done in TaskWarrior
    synced = []
    errors = []

    for uuid in checked_uuids:
        try:
            # State Sync: TaskWarrior update
            mark_done(uuid)
            synced.append(uuid)
        except TaskNotFoundError as e:
            errors.append({"uuid": uuid, "error": str(e)})

    # 4. State Sync: Remove from project frontmatter (Sprint 8.5 pattern)
    task_uuids = frontmatter.get("task_uuids", [])
    for uuid in synced:
        if uuid in task_uuids:
            task_uuids.remove(uuid)

    frontmatter["task_uuids"] = task_uuids

    # Write updated frontmatter
    new_content = _format_with_frontmatter(frontmatter, body)
    note_path.write_text(new_content)

    # 5. State Sync: Update note body to match frontmatter
    _sync_project_task_section(vault_path, project_path)

    return {
        "project_path": project_path,
        "tasks_synced": len(synced),
        "tasks_completed": synced,
        "errors": errors
    }
```

### MCP Integration

**New tool:** `src/plorp/mcp/server.py`

```python
@server.call_tool()
async def plorp_process_project_note(
    project_path: str
) -> list[TextContent]:
    """
    Process project note checkboxes (sync to TaskWarrior).

    Same as daily note processing, but for project notes.

    Args:
        project_path: Full project path (e.g., "work.engineering.api-rewrite")

    Returns:
        JSON with sync summary
    """
    vault = _get_vault_path()
    result = process_project_note(vault, project_path)

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]
```

### CLI Integration

**New command:** `src/plorp/cli.py`

```python
@project_group.command()
@click.argument('project_path')
def process(project_path: str):
    """
    Process project note checkboxes (sync to TaskWarrior).

    Example:
        plorp project process work.engineering.api-rewrite
    """
    config = load_config()
    result = process_project_note(config.vault_path, project_path)

    click.echo(f"✅ Processed: {result['project_path']}")
    click.echo(f"   - {result['tasks_synced']} tasks marked done")

    if result['errors']:
        click.echo(f"   ⚠️  {len(result['errors'])} errors")
        for err in result['errors']:
            click.echo(f"      - {err['uuid']}: {err['error']}")
```

### Tests

**New tests in `tests/test_core/test_projects.py`:**

1. `test_process_project_note_syncs_checked()` - Marks tasks done
2. `test_process_project_note_removes_from_frontmatter()` - State Sync
3. `test_process_project_note_updates_note_body()` - Task section updated
4. `test_process_project_note_handles_no_checkboxes()` - No-op case
5. `test_process_project_note_handles_deleted_tasks()` - Graceful errors

**Expected test count:** +5 tests

### Success Criteria

- [ ] Detects checked boxes in project notes
- [ ] Marks tasks done in TaskWarrior
- [ ] Removes UUIDs from frontmatter
- [ ] Updates note body (auto-syncs via Item 1)
- [ ] Handles errors gracefully
- [ ] CLI command works
- [ ] MCP tool works
- [ ] All tests pass

---

## Item 3: Scoped Workflows (Process/Review by Scope)

**Priority:** HIGH 🎯
**Effort:** 4-5 hours
**Dependencies:** Item 2 (project processing)

### User Experience

**Use cases:**

1. **Review single project:**
   ```
   User: "Review tasks for work.engineering.api-rewrite"
   Claude: *calls plorp_review_project("work.engineering.api-rewrite")*

   Returns tasks from that project only
   ```

2. **Process single project:**
   ```
   User: "Process the API rewrite project"
   Claude: *calls plorp_process_project_note("work.engineering.api-rewrite")*

   Syncs checkboxes in that project note only
   ```

3. **Review by domain:**
   ```
   User: "Review all work tasks"
   Claude: *calls plorp_review_domain("work")*

   Returns tasks from all work.* projects
   ```

4. **Review by workstream:**
   ```
   User: "Review engineering tasks"
   Claude: *calls plorp_review_workstream("work.engineering")*

   Returns tasks from work.engineering.* projects
   ```

### Implementation

**New function:** `src/plorp/core/review.py`

```python
def get_review_tasks_scoped(
    scope_type: str,
    scope_value: str
) -> List[Dict[str, Any]]:
    """
    Get tasks for review filtered by scope.

    Args:
        scope_type: "project", "workstream", "domain", or "all"
        scope_value: Scope identifier

    Returns:
        List of task dicts (same format as get_review_tasks)

    Examples:
        get_review_tasks_scoped("project", "work.engineering.api-rewrite")
        get_review_tasks_scoped("workstream", "work.engineering")
        get_review_tasks_scoped("domain", "work")
        get_review_tasks_scoped("all", "")
    """
    # Build TaskWarrior filter
    if scope_type == "project":
        tw_filter = f"project:{scope_value}"
    elif scope_type == "workstream":
        tw_filter = f"project:{scope_value}."  # Matches work.engineering.*
    elif scope_type == "domain":
        tw_filter = f"project:{scope_value}."  # Matches work.*
    elif scope_type == "all":
        tw_filter = ""
    else:
        raise ValueError(f"Invalid scope_type: {scope_type}")

    # Query TaskWarrior
    cmd = ["task", "status:pending"]
    if tw_filter:
        cmd.append(tw_filter)
    cmd.append("export")

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    tasks = json.loads(result.stdout)

    return [_format_task_for_review(t) for t in tasks]
```

### MCP Integration

**New tools:** `src/plorp/mcp/server.py`

```python
@server.call_tool()
async def plorp_review_project(
    project_path: str
) -> list[TextContent]:
    """
    Get tasks for reviewing specific project.

    Args:
        project_path: Full project path (e.g., "work.engineering.api-rewrite")

    Returns:
        JSON with tasks for review
    """
    tasks = get_review_tasks_scoped("project", project_path)

    import json
    return [TextContent(type="text", text=json.dumps({
        "project_path": project_path,
        "tasks": tasks,
        "task_count": len(tasks)
    }, indent=2))]


@server.call_tool()
async def plorp_review_domain(
    domain: str
) -> list[TextContent]:
    """
    Get tasks for reviewing entire domain.

    Args:
        domain: Domain name (e.g., "work", "home", "personal")

    Returns:
        JSON with tasks from all projects in domain
    """
    tasks = get_review_tasks_scoped("domain", domain)

    import json
    return [TextContent(type="text", text=json.dumps({
        "domain": domain,
        "tasks": tasks,
        "task_count": len(tasks)
    }, indent=2))]


@server.call_tool()
async def plorp_review_workstream(
    workstream: str
) -> list[TextContent]:
    """
    Get tasks for reviewing entire workstream.

    Args:
        workstream: Workstream path (e.g., "work.engineering")

    Returns:
        JSON with tasks from all projects in workstream
    """
    tasks = get_review_tasks_scoped("workstream", workstream)

    import json
    return [TextContent(type="text", text=json.dumps({
        "workstream": workstream,
        "tasks": tasks,
        "task_count": len(tasks)
    }, indent=2))]
```

### CLI Integration

**New command:** `src/plorp/cli.py`

```python
@click.group()
def review():
    """Review tasks."""
    pass

@review.command()
@click.option('--project', help='Review specific project')
@click.option('--domain', help='Review domain')
@click.option('--workstream', help='Review workstream')
def scoped(project, domain, workstream):
    """
    Review tasks with scope filter.

    Examples:
        plorp review scoped --project work.engineering.api-rewrite
        plorp review scoped --domain work
        plorp review scoped --workstream work.engineering
    """
    config = load_config()

    # Determine scope
    if project:
        tasks = get_review_tasks_scoped("project", project)
        scope_label = f"project {project}"
    elif domain:
        tasks = get_review_tasks_scoped("domain", domain)
        scope_label = f"domain {domain}"
    elif workstream:
        tasks = get_review_tasks_scoped("workstream", workstream)
        scope_label = f"workstream {workstream}"
    else:
        click.echo("Error: Specify --project, --domain, or --workstream")
        return

    if not tasks:
        click.echo(f"No tasks for {scope_label}")
        return

    click.echo(f"Reviewing {len(tasks)} tasks for {scope_label}\n")

    # Interactive review (reuse existing review logic)
    for task in tasks:
        # Same prompts as regular review
        # Done / Defer / Skip / Delete
        pass
```

### Tests

**New tests in `tests/test_core/test_review.py`:**

1. `test_get_review_tasks_scoped_project()` - Filters by project
2. `test_get_review_tasks_scoped_domain()` - Filters by domain
3. `test_get_review_tasks_scoped_workstream()` - Filters by workstream
4. `test_get_review_tasks_scoped_all()` - No filter

**Expected test count:** +4 tests

### Success Criteria

- [ ] Scoped queries filter TaskWarrior correctly
- [ ] Project/domain/workstream filters work
- [ ] CLI scoped review works
- [ ] MCP tools work
- [ ] All tests pass

---

## Item 4: Admin Sync-All Command

**Priority:** MEDIUM 🔧
**Effort:** 1-2 hours
**Dependencies:** Item 1 (sync infrastructure)

### Purpose

Admin/maintenance command to ensure all project note bodies are in sync with their frontmatter. This is for:
- **Initial migration:** Upgrading from Sprint 8 → 8.6 (all existing projects need sync)
- **Debugging:** Verify entire system is in consistent state
- **Recovery:** Fix any drift from manual edits or system errors
- **Scheduled maintenance:** Run periodically via cron

**This is different from:**
- Automatic sync (happens per-operation) - this is bulk reconciliation
- Sprint 8.5 reconciliation (handles external TaskWarrior changes) - this handles Obsidian surfaces

### User Experience

**CLI:**
```bash
plorp sync-all

# Output:
Syncing all project notes...

✅ work.engineering.api-rewrite - 5 tasks synced
✅ work.marketing.campaign - 2 tasks synced
✅ home.maintenance.kitchen - 0 tasks synced
✅ personal.learning.rust - 3 tasks synced

Summary:
- 4 projects synced
- 10 total tasks rendered
- 0 errors
```

**MCP:**
```
User: "Sync all projects"
Claude: *calls plorp_sync_all_projects()*

Result:
{
  "projects_synced": 4,
  "total_tasks": 10,
  "errors": []
}
```

### Implementation

**New function:** `src/plorp/core/projects.py`

```python
def sync_all_projects(vault_path: Path) -> Dict[str, Any]:
    """
    Sync all project note bodies to match their frontmatter.

    Admin/maintenance command for:
    - Initial migration (Sprint 8 → 8.6)
    - Debugging/verification
    - Recovery from manual edits

    Returns:
        {
            "projects_synced": 4,
            "total_tasks_rendered": 10,
            "projects": [
                {"project_path": "work.engineering.api-rewrite", "tasks": 5},
                {"project_path": "work.marketing.campaign", "tasks": 2},
                ...
            ],
            "errors": []
        }
    """
    projects_dir = vault_path / "projects"
    if not projects_dir.exists():
        return {
            "projects_synced": 0,
            "total_tasks_rendered": 0,
            "projects": [],
            "errors": []
        }

    synced_projects = []
    total_tasks = 0
    errors = []

    # Find all project notes
    for project_file in projects_dir.rglob("*.md"):
        project_path = project_file.stem  # e.g., "work.engineering.api-rewrite"

        try:
            # Read frontmatter to count tasks
            content = project_file.read_text()
            if not content.startswith("---"):
                continue

            frontmatter, _ = parse_frontmatter(content)
            task_uuids = frontmatter.get("task_uuids", [])
            task_count = len(task_uuids)

            # Sync note body
            _sync_project_task_section(vault_path, project_path)

            synced_projects.append({
                "project_path": project_path,
                "tasks": task_count
            })
            total_tasks += task_count

        except Exception as e:
            errors.append({
                "project_path": project_path,
                "error": str(e)
            })

    return {
        "projects_synced": len(synced_projects),
        "total_tasks_rendered": total_tasks,
        "projects": synced_projects,
        "errors": errors
    }
```

### MCP Integration

**New tool:** `src/plorp/mcp/server.py`

```python
@server.call_tool()
async def plorp_sync_all_projects() -> list[TextContent]:
    """
    Sync all project note bodies to match frontmatter.

    Admin command for:
    - Initial migration (Sprint 8 → 8.6)
    - Debugging/verification
    - Recovery from manual edits

    Returns:
        JSON with sync summary
    """
    vault = _get_vault_path()
    result = sync_all_projects(vault)

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]
```

### CLI Integration

**New command:** `src/plorp/cli.py`

```python
@cli.command()
def sync_all():
    """
    Sync all project note bodies to match frontmatter.

    Admin command for:
    - Initial migration (Sprint 8 → 8.6)
    - Debugging/verification
    - Recovery from manual edits

    Example:
        plorp sync-all
    """
    config = load_config()

    click.echo("Syncing all project notes...")
    result = sync_all_projects(config.vault_path)

    # Show per-project results
    for project in result['projects']:
        click.echo(f"✅ {project['project_path']} - {project['tasks']} tasks synced")

    # Show summary
    click.echo(f"\nSummary:")
    click.echo(f"- {result['projects_synced']} projects synced")
    click.echo(f"- {result['total_tasks_rendered']} total tasks rendered")

    if result['errors']:
        click.echo(f"- {len(result['errors'])} errors")
        for err in result['errors']:
            click.echo(f"  ⚠️  {err['project_path']}: {err['error']}")
```

### Tests

**New tests in `tests/test_core/test_projects.py`:**

1. `test_sync_all_projects_syncs_all_notes()` - Syncs all projects
2. `test_sync_all_projects_handles_empty_dir()` - No projects case
3. `test_sync_all_projects_handles_errors_gracefully()` - Partial failures

**Expected test count:** +3 tests

### Use Cases

**1. Initial migration (Sprint 8 → 8.6):**
```bash
# After upgrading plorp
plorp sync-all

# All existing projects now have task sections
```

**2. Debugging:**
```bash
# Verify entire system is in sync
plorp sync-all

# Check output - should be idempotent (no changes if already synced)
```

**3. Recovery:**
```bash
# After manual edits to frontmatter
plorp sync-all

# Note bodies updated to match
```

**4. Scheduled maintenance (optional):**
```bash
# Add to crontab
0 */6 * * * /path/to/plorp sync-all

# Run every 6 hours to ensure sync
```

### Success Criteria

- [ ] `sync_all_projects()` implemented
- [ ] Iterates through all project notes
- [ ] Calls `_sync_project_task_section()` for each
- [ ] Handles errors gracefully (continues even if one fails)
- [ ] Returns summary with counts
- [ ] CLI command works
- [ ] MCP tool works
- [ ] Idempotent (safe to run multiple times)
- [ ] All tests pass

---

## Implementation Plan

### Phase 1: Auto-Sync Infrastructure (Day 1, 4-5 hours)

1. Implement `_sync_project_task_section()` helper
2. Implement `_remove_section()` markdown helper
3. Implement `_format_date()`, `_format_with_frontmatter()` helpers
4. Write 6 tests for sync infrastructure
5. Verify: Can sync task section manually

### Phase 2: Retrofit Existing Functions (Day 2, 2-3 hours)

1. Update `create_task_in_project()` to call sync
2. Update `remove_task_from_all_projects()` to call sync
3. Update reconciliation script to call sync
4. Write 2 integration tests
5. Verify: Creating task auto-updates note body

### Phase 3: Checkbox Sync (Day 2-3, 3-4 hours)

1. Implement `process_project_note()`
2. Add MCP tool `plorp_process_project_note`
3. Add CLI command `plorp project process`
4. Write 5 tests
5. Verify: Check box → process → TaskWarrior done → note updated

### Phase 4: Scoped Workflows (Day 3, 4-5 hours)

1. Implement `get_review_tasks_scoped()`
2. Add 3 MCP tools (review project/domain/workstream)
3. Add CLI `plorp review scoped`
4. Write 4 tests
5. Verify: Scoped review filters correctly

### Phase 5: Admin Sync-All (Day 3-4, 1-2 hours)

1. Implement `sync_all_projects()`
2. Add MCP tool `plorp_sync_all_projects`
3. Add CLI command `plorp sync-all`
4. Write 3 tests
5. Verify: Can sync all projects, idempotent

### Phase 6: Documentation & Polish (Day 4, 1 hour)

1. Update MCP User Manual
2. Update PM_HANDOFF.md
3. Run full test suite
4. Manual end-to-end testing

### Files to Create

None (all in existing files)

### Files to Modify

1. `src/plorp/core/projects.py` - Add sync helper, process function, sync-all function
2. `src/plorp/core/review.py` - Add scoped review function
3. `src/plorp/parsers/markdown.py` - Add section removal helper
4. `src/plorp/mcp/server.py` - Add 5 MCP tools
5. `src/plorp/cli.py` - Add 3 CLI commands
6. `tests/test_core/test_projects.py` - Add 16 tests
7. `tests/test_core/test_review.py` - Add 4 tests
8. `scripts/reconcile_taskwarrior.py` - Call sync after UUID removal
9. `Docs/MCP_USER_MANUAL.md` - Document new workflow

### Tests to Add

**Total new tests:** 20

- Sync infrastructure (6): Create, update, preserve, format, empty, orphaned
- Integration (2): Create task syncs, remove syncs
- Checkbox sync (5): Sync, state sync, update, no-op, errors
- Scoped review (4): Project, domain, workstream, all
- Sync-all (3): Sync all, empty dir, error handling

**Expected final test count:** 370 + 20 = 390 tests

---

## Testing Strategy

### Unit Tests

**`tests/test_core/test_projects.py`** (+16)
- `_sync_project_task_section()` behavior (6 tests)
- State Sync integration (2 tests)
- Checkbox processing (5 tests)
- Admin sync-all command (3 tests)

**`tests/test_core/test_review.py`** (+4)
- Scoped filtering

### Integration Tests

**Manual Testing:**
1. Create project: `plorp project create "Test" work.test`
2. Create task: Call `plorp_create_task_in_project`
3. Verify: Open project note, Tasks section exists ✅
4. Check box in Obsidian
5. Process: `plorp project process work.test`
6. Verify: TaskWarrior shows done, frontmatter updated, note body updated ✅
7. Review scoped: `plorp review scoped --project work.test`
8. Verify: Only shows work.test tasks ✅
9. Sync all: `plorp sync-all`
10. Verify: All project notes have task sections, idempotent ✅

### State Sync Verification

**Three-surface check:**
- [ ] TaskWarrior task exists
- [ ] Frontmatter has UUID
- [ ] Note body shows task

**After any operation:**
- [ ] All three surfaces in sync
- [ ] No orphaned data
- [ ] User content preserved

### Regression Testing

- [ ] All 370 existing tests pass
- [ ] Sprint 8 project management works
- [ ] Sprint 8.5 auto-sync works
- [ ] Daily note workflows unaffected

---

## Success Criteria

### Functional Requirements

- [ ] Project note bodies always match frontmatter
- [ ] Creating task updates note body automatically
- [ ] Marking task done updates note body automatically
- [ ] External changes update note body (via reconciliation)
- [ ] Checkbox sync works for project notes
- [ ] Scoped review works (project/domain/workstream)

### Quality Requirements

- [ ] 20 new tests passing
- [ ] All 370 existing tests pass
- [ ] Code follows patterns (TypedDict, pure functions)
- [ ] Documentation updated

### State Sync Requirements

- [ ] TaskWarrior ↔ Frontmatter ↔ Note Body all in sync
- [ ] Bidirectional sync enforced
- [ ] No manual "render" commands needed
- [ ] No stale state possible

---

## Documentation Updates

### Files to Update

1. **`Docs/MCP_USER_MANUAL.md`**
   - Update project management section
   - Explain automatic task section updates
   - Document 5 new MCP tools:
     - `plorp_process_project_note`
     - `plorp_review_project`
     - `plorp_review_domain`
     - `plorp_review_workstream`
     - `plorp_sync_all_projects`
   - Add workflow: "Project-Focused Work Session"
   - Add admin section: "System Sync & Maintenance"

2. **`Docs/PM_HANDOFF.md`**
   - Add Sprint 8.6 session entry
   - Update sprint completion registry

3. **`CLAUDE.md`**
   - Add Sprint 8.6 to version history (v1.5.0)
   - Clarify State Sync includes note body

---

## Dependencies

### Required from Previous Sprints

**Sprint 8:**
- ✅ Project notes with frontmatter
- ✅ `create_task_in_project()`
- ✅ TaskWarrior project filtering

**Sprint 8.5:**
- ✅ State Sync pattern
- ✅ `remove_task_from_all_projects()`
- ✅ Auto-sync infrastructure

### External Dependencies

- TaskWarrior 3.4.1+ (existing)
- Python 3.8+ (existing)
- Obsidian vault (existing)

---

## Risks & Mitigation

### Risk 1: File Churn (Frequent Note Updates)

**Risk:** Every task operation updates project notes → lots of file writes.

**Mitigation:**
- Acceptable - Obsidian handles this fine
- User sees real-time updates (good UX)
- Git sees meaningful changes (task state changes)
- Not a performance issue for typical usage

### Risk 2: User Edits Task Section Manually

**Risk:** User manually edits `## Tasks` section, next sync overwrites.

**Mitigation:**
- Document: "Task section is auto-managed - don't edit"
- Consider: Add comment `<!-- Managed by plorp - changes will be overwritten -->`
- User can add content in other sections (preserved)

### Risk 3: Large Projects (100+ tasks)

**Risk:** Project with many tasks → large note file, slow sync.

**Mitigation:**
- Only render pending tasks (not completed)
- Acceptable for Sprint 8.6 (typical projects <50 tasks)
- Future: Pagination if needed

### Risk 4: Concurrent Modifications

**Risk:** User edits note while plorp is syncing.

**Mitigation:**
- File writes are atomic (OS-level)
- Worst case: User's Obsidian shows update a second later
- Not a critical issue for manual workflows

---

## Open Questions

### Q1: Should completed tasks be shown in note body?

**Options:**

**A) Only pending tasks** (Recommended)
- Matches daily notes
- Keeps notes focused
- Query completed via TaskWarrior

**B) Pending + completed (separate section)**
- Shows history
- Longer notes

**C) Configurable in frontmatter**
- `show_completed: true/false`
- More complexity

**Recommendation:** Option A - Only pending tasks.

**Rationale:** Consistent with daily notes, keeps notes actionable.

---

### Q2: Should note body sync be optional?

**Options:**

**A) Always sync** (Recommended)
- State Sync is mandatory
- No configuration needed
- Predictable behavior

**B) Opt-in per project**
- `auto_sync_body: true/false` in frontmatter
- More flexibility
- More complexity
- Violates State Sync principle

**Recommendation:** Option A - Always sync.

**Rationale:** State Sync is not optional. If frontmatter has state, note body must reflect it.

---

### Q3: Error handling when TaskWarrior task is deleted?

**Options:**

**A) Skip orphaned UUIDs silently** (Recommended)
- Log warning
- Continue syncing other tasks
- Reconciliation will clean frontmatter eventually

**B) Fail entire sync**
- Safer, but breaks on edge cases
- Poor UX

**C) Remove orphaned UUIDs immediately**
- Extra complexity
- Reconciliation already handles this

**Recommendation:** Option A - Skip gracefully.

**Rationale:** Sprint 8.5's reconciliation cleans orphaned UUIDs. Sync should be resilient.

---

## Version History

- **v2.1.0** (2025-10-08) - Added sync-all command
  - Added Item 4: Admin sync-all command
  - CLI: `plorp sync-all`
  - MCP: `plorp_sync_all_projects`
  - For migration, debugging, recovery
  - 13-18 hours estimated effort
  - 20 new tests

- **v2.0.0** (2025-10-08) - Architectural rewrite
  - Removed "rendering" as user-facing feature
  - Implemented as automatic State Sync infrastructure
  - Retrofits Sprint 8 functions
  - Adds checkbox sync for project notes
  - Adds scoped workflows
  - 12-16 hours estimated effort
  - 17 new tests

- **v1.0.0** (2025-10-08) - Initial spec (DEPRECATED)
  - Had "rendering" as manual user action
  - Architectural flaw identified
  - Replaced by v2.0.0

---

## PM Sign-Off Checklist

**Pre-Implementation:**
- [ ] Architecture correct (State Sync enforced)
- [ ] No manual "render" commands
- [ ] All modifications trigger auto-sync
- [ ] Effort estimate (13-18 hours) reasonable
- [ ] No conflicts with Sprint 9
- [ ] Open questions resolved

**Post-Implementation:**
- [ ] All 20 tests passing
- [ ] 370 existing tests pass (no regressions)
- [ ] State Sync verified (3 surfaces in sync)
- [ ] CLI commands work (3 new: process, scoped review, sync-all)
- [ ] MCP tools work (5 new)
- [ ] `plorp sync-all` runs successfully
- [ ] Sync-all is idempotent (safe to run multiple times)
- [ ] Documentation updated
- [ ] Manual testing complete
- [ ] Version bumped (1.4.0 → 1.5.0)

**Sign-Off:** _______________  Date: ___________

---

## Document Status

**Version:** 2.1.0
**Status:** ✅ APPROVED - Ready for Implementation
**Last Updated:** 2025-10-08
**Approved By:** PM/Architect Instance (Session 9)

**Outstanding Items:**
- Q1: Completed task rendering (Recommendation: pending only)
- Q2: Optional sync (Recommendation: always sync)
- Q3: Orphaned UUID handling (Recommendation: skip gracefully)

**Changes in v2.1.0:**
- Added Item 4: Admin sync-all command (`plorp sync-all`)
- Updated effort estimate: 13-18 hours (was 12-16)
- Updated test count: 20 new tests (was 17)
- Updated MCP tools: 5 new tools (was 4)

---

**End of Sprint 8.6 Interactive Projects Spec**
