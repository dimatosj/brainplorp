# Sprint 8 Spec: Project Management with Obsidian Bases

**Version:** 1.0.0
**Status:** 📋 READY FOR IMPLEMENTATION
**Sprint:** 8
**Estimated Effort:** 14-16 hours
**Dependencies:** Sprint 6 (MCP architecture), Sprint 7 (process workflow)
**Architecture:** Obsidian Bases + MCP-First
**Date:** 2025-10-07

---

## How to Use This Spec

### For Lead Engineers:
1. **Read entire spec first** - Understand scope, architecture, and requirements
2. **Check Q&A section** - All implementation questions are pre-answered
3. **Add new questions** - If you have questions during implementation, append to "Engineering Questions (During Implementation)" section
4. **Update Summary section** - When complete, add implementation summary with line counts, test results, key decisions
5. **Fill Handoff section** - Document any incomplete work, known issues, or context needed for next sprint

### For PM/Architect:
1. **Review new questions** - Check "Engineering Questions (During Implementation)" section regularly
2. **Answer questions** - Add answers with rationale to help unblock engineering
3. **Review handoff** - Use handoff section to plan next sprint or address issues

### For Both:
- **Status field** updates as work progresses (READY → IN PROGRESS → COMPLETE)
- **Version** increments with major changes (1.0 → 1.1)
- Keep spec updated as source of truth during implementation

---

## Executive Summary

Sprint 8 implements project management using **Obsidian Bases** as the storage layer, creating an elegant integration between plorp, TaskWarrior, and Obsidian. Instead of storing project metadata in separate YAML files, projects become markdown notes in the vault with YAML frontmatter, queryable via Obsidian's native Bases plugin.

**Key Innovation:** Projects are first-class notes in Obsidian, not just metadata. Users can add context, documentation, and links directly to project notes while plorp manages the TaskWarrior integration.

**What's New:**
- Project notes in `vault/projects/` with rich frontmatter
- Obsidian Base files (`.base`) for dashboard views
- Three-tier hierarchy: Domain → Workstream → Project
- Domain focus mechanism (CLI persistent, MCP conversation-scoped)
- TaskWarrior native filtering integration
- Bidirectional task-project linking

---

## Goals

1. **Project Management via Obsidian Bases**
   - Create project notes with structured frontmatter
   - List/filter projects using Bases views
   - Update project state (active/planning/completed/blocked/archived)
   - Delete/archive projects

2. **Three-Tier Hierarchy**
   - Domain (work/home/personal) - top level
   - Workstream (marketing, engineering, etc.) - middle tier
   - Project (website-redesign, api-rewrite) - bottom tier
   - Flexible: Allow 1, 2, or 3 segments with review workflow for orphans

3. **Domain Focus**
   - CLI: Persistent focus stored in `~/.config/plorp/focus.txt`
   - MCP: Conversation-scoped, defaults to "home", communicated in outputs
   - Commands default to focused domain unless overridden

4. **Task-Project Integration**
   - Add tasks to projects (via TaskWarrior `project:` field)
   - List tasks in a project
   - Filter tasks by domain/workstream/project
   - Bidirectional linking (project notes track task UUIDs, tasks annotate project path)

5. **Workstream Management**
   - Suggested workstreams per domain (in `config.yaml`)
   - Hybrid validation (suggest, but allow new with confirmation)
   - Track orphaned projects (2-segment, missing workstream)

6. **TaskWarrior Native Filtering**
   - Use TaskWarrior's filter syntax directly
   - Post-process for hierarchy-based filtering
   - Support sorting by urgency, due date, staleness

---

## Core Workflow

### Workflow 1: Create Project via MCP

**User in Claude Desktop:**
```
User: "Create a new project for website redesign in the work marketing workstream"

Claude: I'll create that project for you. What would you like to call it?

User: "website-redesign"

Claude: [calls plorp_create_project(
  name="website-redesign",
  domain="work",
  workstream="marketing",
  state="active"
)]

✅ Created project: work.marketing.website-redesign

I've created a project note at vault/projects/work.marketing.website-redesign.md.
You can view it in Obsidian or add it to your projects dashboard.

Would you like to add tasks to this project?
```

**Result in Obsidian:**

File: `vault/projects/work.marketing.website-redesign.md`
```markdown
---
domain: work
workstream: marketing
project_name: website-redesign
full_path: work.marketing.website-redesign
state: active
created_at: 2025-10-07T10:30:00
description: null
task_uuids: []
needs_review: false
tags:
  - project
  - work
  - marketing
---

# Website Redesign

## Overview
Project description goes here.

## Tasks
<!-- Tasks linked to this project will appear here -->

## Notes
<!-- Project documentation, meeting notes, research -->
```

### Workflow 2: View Projects in Obsidian

**User opens `vault/_bases/projects.base` in Obsidian:**

Sees interactive table:

| Full Path | Domain | Workstream | State | Tasks | Created |
|-----------|--------|------------|-------|-------|---------|
| work.marketing.website-redesign | work | marketing | active | 5 | 2025-10-07 |
| work.engineering.api-rewrite | work | engineering | active | 12 | 2025-10-05 |
| home.maintenance.hvac | home | maintenance | planning | 0 | 2025-10-06 |

**Can click any row to open project note, edit state inline, filter by domain/state.**

### Workflow 3: Add Task to Project

**Via CLI:**
```bash
# Set domain focus
plorp focus work

# Create task in project (uses focused domain)
plorp add "Design homepage mockups" project:marketing.website-redesign --due friday --priority H

# Created task: abc-123
# Added to project: work.marketing.website-redesign
```

**Result:**
- TaskWarrior task created with `project:work.marketing.website-redesign`
- Task annotated with `Note: vault/projects/work.marketing.website-redesign.md`
- Project note frontmatter updated: `task_uuids: [abc-123]`

### Workflow 4: List Tasks in Project

**Via MCP:**
```
User: "Show me all tasks for the website redesign project"

Claude: [calls plorp_list_project_tasks("work.marketing.website-redesign")]

Here are the 5 tasks for work.marketing.website-redesign:

📌 High Priority:
  • Design homepage mockups (due: Friday, uuid: abc-123)
  • Review brand guidelines (due: Today, uuid: def-456)

📋 Medium Priority:
  • Set up hosting (uuid: ghi-789)

📌 Overdue:
  • Stakeholder kickoff (due: 2 days ago, uuid: jkl-012)
```

### Workflow 5: Filter Tasks by Domain

**Via CLI with flags:**
```bash
# All tasks in work domain
plorp tasks --domain work

# Orphaned tasks (no project)
plorp tasks --orphaned

# Tasks with workstream but no project (2 segments)
plorp tasks --workstream-only

# Sort by urgency
plorp tasks --domain work --sort urgency
```

**Translates to TaskWarrior:**
```bash
# --domain work → task project.startswith:work export
# --orphaned → task project.none: export
# --workstream-only → task project.any: export + filter for 2-segment projects
```

### Workflow 6: Domain Focus (MCP)

**New Claude chat window:**
```
User: "/start"

Claude: [calls plorp_start_day(domain=None)]

Generated daily note for 2025-10-07.

📍 Domain Focus: home (default)
   All commands will use this domain unless you specify otherwise.
   To change: "set focus to work" or "switch to personal domain"

Found 3 tasks due today:
  • Call plumber (home.maintenance)
  • Buy groceries (no project)
  • Family budget review (home.finances)
```

**User switches focus:**
```
User: "Switch to work domain"

Claude: [calls plorp_set_focused_domain("work")]

✅ Focused on domain: work

All commands will now default to work domain.
```

### Workflow 7: Review Orphaned Projects

**Via Base View in Obsidian:**

User opens `vault/_bases/review-queue.base`:

| Full Path | Domain | Needs Review | Created |
|-----------|--------|--------------|---------|
| work.quick-fix | work | ✅ true | 2025-10-05 |
| personal.todo | personal | ✅ true | 2025-10-03 |

**These are 2-segment projects missing workstream - flagged for review.**

---

## Architecture

### Storage Architecture

```
vault/
├── projects/                           # Project notes (Obsidian Bases data source)
│   ├── work.marketing.website-redesign.md
│   ├── work.engineering.api-rewrite.md
│   ├── home.maintenance.hvac.md
│   └── work.quick-fix.md              # 2-segment (orphaned, needs review)
│
├── _bases/                             # Base definitions
│   ├── projects.base                   # All projects dashboard
│   ├── active-projects.base            # Filtered: state=active
│   ├── work-projects.base              # Filtered: domain=work
│   └── review-queue.base               # Filtered: needs_review=true
│
├── daily/                              # Daily notes
│   └── 2025-10-07.md
│
├── notes/                              # General notes
│
└── inbox/                              # Inbox files
    └── 2025-10.md
```

### Project Note Schema

**Frontmatter (YAML):**
```yaml
domain: work                            # Required: work/home/personal
workstream: marketing                   # Optional: area of responsibility
project_name: website-redesign          # Required: project identifier
full_path: work.marketing.website-redesign  # Computed: full TaskWarrior project path
state: active                           # Required: active/planning/completed/blocked/archived
created_at: 2025-10-07T10:30:00        # Auto: ISO timestamp
description: "Redesign company website" # Optional: short description
task_uuids: [abc-123, def-456]         # Auto: linked TaskWarrior task UUIDs
needs_review: false                     # Auto: true if missing workstream
tags: [project, work, marketing]        # Auto: for filtering
```

### Base File Schema

**Example: `vault/_bases/projects.base`**
```yaml
name: Project Dashboard
description: All projects across domains
views:
  - name: All Projects
    type: table
    sort:
      - property: created_at
        direction: desc
    columns:
      - property: full_path
        width: 300
      - property: domain
        width: 100
      - property: workstream
        width: 150
      - property: state
        width: 100
      - property: task_uuids
        display: count
        label: Tasks
      - property: created_at
        width: 120

  - name: Active Projects
    type: table
    filters:
      - property: state
        operator: equals
        value: active
    columns:
      - full_path
      - domain
      - workstream
      - task_uuids

  - name: Work Domain
    type: table
    filters:
      - property: domain
        operator: equals
        value: work
    columns:
      - full_path
      - workstream
      - state
      - task_uuids

  - name: Needs Review
    type: table
    filters:
      - property: needs_review
        operator: equals
        value: true
    columns:
      - full_path
      - domain
      - state
      - created_at
```

### Domain Focus Storage

**CLI:** `~/.config/plorp/focus.txt`
```
work
```

**MCP:** Conversation context (ephemeral, defaults to "home")

**Implementation:**
```python
# CLI reads/writes focus.txt
def get_focused_domain_cli() -> str:
    focus_file = Path.home() / ".config/plorp/focus.txt"
    if focus_file.exists():
        return focus_file.read_text().strip()
    return "home"  # Default

# MCP accepts domain parameter, uses default
@mcp.tool()
async def plorp_list_tasks(domain: str = "home"):
    # domain defaults to "home" if not specified
    # Claude tracks user's preference in conversation
```

---

## Module Architecture

### New Module: `src/plorp/integrations/obsidian_bases.py`

```python
"""
Obsidian Bases Integration

Manages project notes as Obsidian Bases data source.
Projects are markdown notes in vault/projects/ with YAML frontmatter.
"""

from pathlib import Path
from datetime import datetime
import yaml
from typing import Optional
from ..core.types import ProjectInfo, ProjectListResult


def get_projects_dir() -> Path:
    """Get vault/projects/ directory."""
    from ..config import get_vault_path
    return get_vault_path() / "projects"


def parse_project_note(note_path: Path) -> ProjectInfo:
    """
    Parse project note frontmatter into ProjectInfo.

    Returns:
        ProjectInfo with all metadata fields
    """
    content = note_path.read_text()

    # Split frontmatter and body
    if content.startswith("---"):
        parts = content.split("---", 2)
        frontmatter_text = parts[1]
        frontmatter = yaml.safe_load(frontmatter_text)
    else:
        raise ValueError(f"Project note missing frontmatter: {note_path}")

    return ProjectInfo(
        domain=frontmatter["domain"],
        workstream=frontmatter.get("workstream"),
        project_name=frontmatter["project_name"],
        full_path=frontmatter["full_path"],
        state=frontmatter["state"],
        created_at=frontmatter["created_at"],
        description=frontmatter.get("description"),
        task_uuids=frontmatter.get("task_uuids", []),
        needs_review=frontmatter.get("needs_review", False),
        tags=frontmatter.get("tags", []),
        note_path=str(note_path)
    )


def create_project_note(
    domain: str,
    workstream: Optional[str],
    project_name: str,
    state: str = "active",
    description: Optional[str] = None
) -> ProjectInfo:
    """
    Create new project note in vault/projects/.

    Args:
        domain: work/home/personal
        workstream: Area of responsibility (optional)
        project_name: Project identifier
        state: active/planning/completed/blocked/archived
        description: Short description (optional)

    Returns:
        ProjectInfo for created project

    Raises:
        ValueError: If domain invalid or project already exists
    """
    # Validate domain
    if domain not in ["work", "home", "personal"]:
        raise ValueError(f"Invalid domain: {domain}. Must be work/home/personal")

    # Construct full path
    if workstream:
        full_path = f"{domain}.{workstream}.{project_name}"
    else:
        full_path = f"{domain}.{project_name}"
        # 2-segment projects need review

    # Check if project exists
    projects_dir = get_projects_dir()
    projects_dir.mkdir(parents=True, exist_ok=True)
    note_path = projects_dir / f"{full_path}.md"

    if note_path.exists():
        raise ValueError(f"Project already exists: {full_path}")

    # Build frontmatter
    frontmatter = {
        "domain": domain,
        "workstream": workstream,
        "project_name": project_name,
        "full_path": full_path,
        "state": state,
        "created_at": datetime.now().isoformat(),
        "description": description,
        "task_uuids": [],
        "needs_review": workstream is None,  # Flag 2-segment projects
        "tags": ["project", domain] + ([workstream] if workstream else [])
    }

    # Build note content
    content = f"""---
{yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)}---

# {project_name.replace('-', ' ').title()}

## Overview
{description or "Project description goes here."}

## Tasks
<!-- Tasks linked to this project will appear here -->

## Notes
<!-- Project documentation, meeting notes, research -->
"""

    note_path.write_text(content)

    return ProjectInfo(**frontmatter, note_path=str(note_path))


def list_projects(
    domain: Optional[str] = None,
    state: Optional[str] = None,
    needs_review: Optional[bool] = None
) -> ProjectListResult:
    """
    List projects by querying vault/projects/ notes.

    Args:
        domain: Filter by domain (optional)
        state: Filter by state (optional)
        needs_review: Filter by needs_review flag (optional)

    Returns:
        ProjectListResult with list and grouped dict
    """
    projects_dir = get_projects_dir()

    if not projects_dir.exists():
        return ProjectListResult(projects=[], grouped_by_domain={})

    projects = []

    for note_path in projects_dir.glob("*.md"):
        try:
            project = parse_project_note(note_path)

            # Apply filters
            if domain and project["domain"] != domain:
                continue
            if state and project["state"] != state:
                continue
            if needs_review is not None and project["needs_review"] != needs_review:
                continue

            projects.append(project)
        except Exception as e:
            # Skip invalid project notes
            print(f"Warning: Failed to parse {note_path}: {e}")
            continue

    # Group by domain
    grouped = {}
    for project in projects:
        d = project["domain"]
        if d not in grouped:
            grouped[d] = []
        grouped[d].append(project)

    return ProjectListResult(
        projects=projects,
        grouped_by_domain=grouped
    )


def get_project_info(full_path: str) -> Optional[ProjectInfo]:
    """
    Get single project by full path.

    Args:
        full_path: Project identifier (e.g., "work.marketing.website")

    Returns:
        ProjectInfo or None if not found
    """
    projects_dir = get_projects_dir()
    note_path = projects_dir / f"{full_path}.md"

    if not note_path.exists():
        return None

    return parse_project_note(note_path)


def update_project_state(full_path: str, state: str) -> ProjectInfo:
    """
    Update project state in frontmatter.

    Args:
        full_path: Project identifier
        state: New state (active/planning/completed/blocked/archived)

    Returns:
        Updated ProjectInfo

    Raises:
        ValueError: If project not found or invalid state
    """
    valid_states = ["active", "planning", "completed", "blocked", "archived"]
    if state not in valid_states:
        raise ValueError(f"Invalid state: {state}. Must be one of {valid_states}")

    projects_dir = get_projects_dir()
    note_path = projects_dir / f"{full_path}.md"

    if not note_path.exists():
        raise ValueError(f"Project not found: {full_path}")

    # Parse note
    content = note_path.read_text()
    parts = content.split("---", 2)
    frontmatter = yaml.safe_load(parts[1])
    body = parts[2]

    # Update state
    frontmatter["state"] = state

    # Write back
    updated_content = f"""---
{yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)}---{body}"""

    note_path.write_text(updated_content)

    return ProjectInfo(**frontmatter, note_path=str(note_path))


def add_task_to_project(full_path: str, task_uuid: str) -> ProjectInfo:
    """
    Add task UUID to project's task_uuids list.

    Args:
        full_path: Project identifier
        task_uuid: TaskWarrior task UUID

    Returns:
        Updated ProjectInfo
    """
    projects_dir = get_projects_dir()
    note_path = projects_dir / f"{full_path}.md"

    if not note_path.exists():
        raise ValueError(f"Project not found: {full_path}")

    # Parse note
    content = note_path.read_text()
    parts = content.split("---", 2)
    frontmatter = yaml.safe_load(parts[1])
    body = parts[2]

    # Add UUID if not already present
    task_uuids = frontmatter.get("task_uuids", [])
    if task_uuid not in task_uuids:
        task_uuids.append(task_uuid)
        frontmatter["task_uuids"] = task_uuids

    # Write back
    updated_content = f"""---
{yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)}---{body}"""

    note_path.write_text(updated_content)

    return ProjectInfo(**frontmatter, note_path=str(note_path))


def delete_project(full_path: str) -> bool:
    """
    Delete project note.

    Args:
        full_path: Project identifier

    Returns:
        True if deleted, False if not found
    """
    projects_dir = get_projects_dir()
    note_path = projects_dir / f"{full_path}.md"

    if not note_path.exists():
        return False

    note_path.unlink()
    return True
```

### Enhanced Module: `src/plorp/core/projects.py`

```python
"""
Project Management Core Module

High-level project operations using Obsidian Bases integration.
"""

from typing import Optional, List
from pathlib import Path
from ..integrations.obsidian_bases import (
    create_project_note,
    list_projects as list_projects_bases,
    get_project_info as get_project_info_bases,
    update_project_state as update_project_state_bases,
    delete_project as delete_project_bases,
    add_task_to_project as add_task_to_project_bases
)
from ..integrations.taskwarrior import create_task, add_annotation, get_tasks
from .types import ProjectInfo, ProjectListResult, TaskInfo


def create_project(
    name: str,
    domain: str,
    workstream: Optional[str] = None,
    state: str = "active",
    description: Optional[str] = None
) -> ProjectInfo:
    """
    Create new project.

    Validates domain, checks suggested workstreams, creates project note.

    Returns:
        ProjectInfo TypedDict
    """
    # Validate domain
    valid_domains = ["work", "home", "personal"]
    if domain not in valid_domains:
        raise ValueError(f"Invalid domain: {domain}. Must be one of {valid_domains}")

    # TODO: Check suggested workstreams (hybrid validation)
    # For now, accept any workstream

    return create_project_note(domain, workstream, name, state, description)


def list_projects(
    domain: Optional[str] = None,
    state: Optional[str] = None
) -> ProjectListResult:
    """
    List projects with optional filters.

    Returns:
        ProjectListResult with list and grouped dict
    """
    return list_projects_bases(domain=domain, state=state)


def get_project_info(full_path: str) -> Optional[ProjectInfo]:
    """Get single project by full path."""
    return get_project_info_bases(full_path)


def update_project_state(full_path: str, state: str) -> ProjectInfo:
    """Update project state."""
    return update_project_state_bases(full_path, state)


def delete_project(full_path: str) -> bool:
    """Delete project."""
    return delete_project_bases(full_path)


def create_task_in_project(
    description: str,
    project_full_path: str,
    due: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> str:
    """
    Create task in TaskWarrior and link to project.

    1. Creates task with project: field
    2. Annotates task with project note path
    3. Adds task UUID to project note frontmatter

    Args:
        description: Task description
        project_full_path: Full project path (e.g., "work.marketing.website")
        due: Due date (optional)
        priority: Priority (H/M/L, optional)
        tags: Tags (optional)

    Returns:
        Task UUID

    Raises:
        ValueError: If project not found
    """
    # Verify project exists
    project = get_project_info_bases(project_full_path)
    if not project:
        raise ValueError(f"Project not found: {project_full_path}")

    # Create task in TaskWarrior
    task_uuid = create_task(
        description=description,
        project=project_full_path,
        due=due,
        priority=priority,
        tags=tags
    )

    if not task_uuid:
        raise RuntimeError("Failed to create task in TaskWarrior")

    # Add annotation to task (bidirectional link)
    project_note_path = f"vault/projects/{project_full_path}.md"
    add_annotation(task_uuid, f"Project: {project_note_path}")

    # Add task UUID to project note
    add_task_to_project_bases(project_full_path, task_uuid)

    return task_uuid


def list_project_tasks(project_full_path: str) -> List[TaskInfo]:
    """
    List all tasks for a project.

    Queries TaskWarrior with project: filter.

    Args:
        project_full_path: Full project path

    Returns:
        List of TaskInfo dicts
    """
    tasks = get_tasks([f"project:{project_full_path}"])

    # Convert to TaskInfo TypedDict
    return [
        TaskInfo(
            uuid=t["uuid"],
            description=t["description"],
            status=t["status"],
            project=t.get("project"),
            due=t.get("due"),
            priority=t.get("priority"),
            tags=t.get("tags", []),
            urgency=t.get("urgency", 0)
        )
        for t in tasks
    ]


def list_tasks_by_domain(domain: str) -> List[TaskInfo]:
    """
    List all tasks in a domain (domain.*).

    Uses TaskWarrior project.startswith filter.

    Args:
        domain: work/home/personal

    Returns:
        List of TaskInfo dicts
    """
    # TaskWarrior filter: project.startswith:domain
    tasks = get_tasks([f"project.startswith:{domain}"])

    return [
        TaskInfo(
            uuid=t["uuid"],
            description=t["description"],
            status=t["status"],
            project=t.get("project"),
            due=t.get("due"),
            priority=t.get("priority"),
            tags=t.get("tags", []),
            urgency=t.get("urgency", 0)
        )
        for t in tasks
    ]


def list_orphaned_tasks() -> List[TaskInfo]:
    """
    List tasks with no project.

    Uses TaskWarrior project.none filter.

    Returns:
        List of TaskInfo dicts
    """
    tasks = get_tasks(["project.none:"])

    return [
        TaskInfo(
            uuid=t["uuid"],
            description=t["description"],
            status=t["status"],
            project=None,
            due=t.get("due"),
            priority=t.get("priority"),
            tags=t.get("tags", []),
            urgency=t.get("urgency", 0)
        )
        for t in tasks
    ]
```

### Updated Types: `src/plorp/core/types.py`

```python
# Add to existing types.py

class ProjectInfo(TypedDict):
    """Project metadata from Obsidian note frontmatter."""
    domain: str                    # work/home/personal
    workstream: Optional[str]      # Area of responsibility
    project_name: str              # Project identifier
    full_path: str                 # Full TaskWarrior project path
    state: str                     # active/planning/completed/blocked/archived
    created_at: str                # ISO timestamp
    description: Optional[str]     # Short description
    task_uuids: List[str]          # Linked TaskWarrior task UUIDs
    needs_review: bool             # True if missing workstream
    tags: List[str]                # Tags for filtering
    note_path: str                 # Path to project note


class ProjectListResult(TypedDict):
    """Result from list_projects()."""
    projects: List[ProjectInfo]
    grouped_by_domain: dict[str, List[ProjectInfo]]  # Grouped by domain


class TaskInfo(TypedDict):
    """Task information from TaskWarrior."""
    uuid: str
    description: str
    status: str                    # pending/completed/waiting/deleted
    project: Optional[str]         # TaskWarrior project path
    due: Optional[str]             # Due date
    priority: Optional[str]        # H/M/L
    tags: List[str]
    urgency: float                 # TaskWarrior urgency score
```

---

## MCP Tools (8 New Tools)

### Tool 1: `plorp_create_project`

```python
@mcp.tool()
async def plorp_create_project(
    name: str,
    domain: str,
    workstream: str = None,
    state: str = "active",
    description: str = None
) -> dict:
    """
    Create new project in vault/projects/.

    Args:
        name: Project name (e.g., "website-redesign")
        domain: Domain (work/home/personal)
        workstream: Workstream (optional, e.g., "marketing")
        state: Project state (default: "active")
        description: Short description (optional)

    Returns:
        {"full_path": str, "note_path": str, "needs_review": bool}
    """
    project = create_project(name, domain, workstream, state, description)

    return {
        "full_path": project["full_path"],
        "note_path": project["note_path"],
        "domain": project["domain"],
        "workstream": project["workstream"],
        "state": project["state"],
        "needs_review": project["needs_review"]
    }
```

### Tool 2: `plorp_list_projects`

```python
@mcp.tool()
async def plorp_list_projects(
    domain: str = None,
    state: str = None
) -> dict:
    """
    List projects with optional filters.

    Args:
        domain: Filter by domain (optional)
        state: Filter by state (optional)

    Returns:
        {"projects": list, "count": int, "grouped_by_domain": dict}
    """
    result = list_projects(domain, state)

    return {
        "projects": result["projects"],
        "count": len(result["projects"]),
        "grouped_by_domain": result["grouped_by_domain"]
    }
```

### Tool 3: `plorp_get_project_info`

```python
@mcp.tool()
async def plorp_get_project_info(full_path: str) -> dict:
    """
    Get detailed project information.

    Args:
        full_path: Full project path (e.g., "work.marketing.website")

    Returns:
        ProjectInfo dict or error if not found
    """
    project = get_project_info(full_path)

    if not project:
        raise ValueError(f"Project not found: {full_path}")

    return project
```

### Tool 4: `plorp_update_project_state`

```python
@mcp.tool()
async def plorp_update_project_state(
    full_path: str,
    state: str
) -> dict:
    """
    Update project state.

    Args:
        full_path: Full project path
        state: New state (active/planning/completed/blocked/archived)

    Returns:
        Updated ProjectInfo dict
    """
    project = update_project_state(full_path, state)

    return project
```

### Tool 5: `plorp_delete_project`

```python
@mcp.tool()
async def plorp_delete_project(full_path: str) -> dict:
    """
    Delete project note.

    Args:
        full_path: Full project path

    Returns:
        {"deleted": bool, "full_path": str}
    """
    deleted = delete_project(full_path)

    return {
        "deleted": deleted,
        "full_path": full_path
    }
```

### Tool 6: `plorp_create_task_in_project`

```python
@mcp.tool()
async def plorp_create_task_in_project(
    description: str,
    project_full_path: str,
    due: str = None,
    priority: str = None,
    domain: str = "home"
) -> dict:
    """
    Create task in project.

    Creates TaskWarrior task, links to project bidirectionally.

    Args:
        description: Task description
        project_full_path: Full project path (e.g., "work.marketing.website")
        due: Due date (optional, TaskWarrior format)
        priority: Priority (H/M/L, optional)
        domain: Domain for context (default: "home")

    Returns:
        {"task_uuid": str, "project": str}
    """
    task_uuid = create_task_in_project(
        description,
        project_full_path,
        due,
        priority
    )

    return {
        "task_uuid": task_uuid,
        "project": project_full_path
    }
```

### Tool 7: `plorp_list_project_tasks`

```python
@mcp.tool()
async def plorp_list_project_tasks(project_full_path: str) -> dict:
    """
    List all tasks for a project.

    Args:
        project_full_path: Full project path

    Returns:
        {"tasks": list, "count": int, "project": str}
    """
    tasks = list_project_tasks(project_full_path)

    return {
        "tasks": tasks,
        "count": len(tasks),
        "project": project_full_path
    }
```

### Tool 8: `plorp_set_focused_domain`

```python
@mcp.tool()
async def plorp_set_focused_domain(domain: str) -> dict:
    """
    Set focused domain for this conversation.

    Note: This is conversation-scoped. New chat windows reset to "home".

    Args:
        domain: Domain to focus (work/home/personal)

    Returns:
        {"focused_domain": str, "message": str}
    """
    valid_domains = ["work", "home", "personal"]

    if domain not in valid_domains:
        raise ValueError(f"Invalid domain: {domain}. Must be one of {valid_domains}")

    # Store in conversation context (implementation depends on MCP framework)
    # For now, just return confirmation

    return {
        "focused_domain": domain,
        "message": f"Focused on domain: {domain}. All commands will default to this domain."
    }
```

### Tool 9: `plorp_get_focused_domain`

```python
@mcp.tool()
async def plorp_get_focused_domain() -> dict:
    """
    Get current focused domain.

    Returns:
        {"focused_domain": str, "is_default": bool}
    """
    # In MCP context, default to "home"
    # Real implementation would check conversation state

    return {
        "focused_domain": "home",
        "is_default": True
    }
```

---

## CLI Commands

### Command Group: `plorp project`

```bash
# Create project
plorp project create <name> --domain <domain> --workstream <workstream> [--state <state>] [--description <desc>]

# List projects
plorp project list [--domain <domain>] [--state <state>]

# Show project
plorp project show <full-path>

# Update project state
plorp project set-state <full-path> <state>

# Delete project
plorp project delete <full-path>
```

### Command Group: `plorp focus`

```bash
# Set focused domain (CLI persistent)
plorp focus <domain>

# Show current focus
plorp focus

# Clear focus (back to default)
plorp focus clear
```

### Enhanced: `plorp add`

```bash
# Add task to project (uses focused domain if not specified)
plorp add "<description>" project:<project-path> [--due <date>] [--priority <H|M|L>]

# Examples:
plorp add "Design mockups" project:marketing.website --due friday --priority H
# → Creates in work.marketing.website (if work is focused)

plorp add "Buy groceries"
# → Creates orphaned task (no project)
```

### Enhanced: `plorp tasks`

```bash
# List tasks with filters
plorp tasks [--domain <domain>] [--project <full-path>] [--orphaned] [--sort <field>]

# Examples:
plorp tasks --domain work
# → All tasks in work.* projects

plorp tasks --project work.marketing.website
# → Tasks in specific project

plorp tasks --orphaned
# → Tasks with no project

plorp tasks --domain work --sort urgency
# → Work tasks sorted by urgency
```

---

## Implementation Phases

### Phase 0: Setup & Dependencies (1h)

**Tasks:**
- Create `vault/projects/` directory structure
- Create `vault/_bases/` directory
- Add Obsidian Bases as dependency note in docs
- Update config schema for workstream suggestions

**Deliverables:**
- `vault/projects/.gitkeep`
- `vault/_bases/.gitkeep`
- Updated `Docs/VAULT_SETUP.md`

---

### Phase 1: Obsidian Bases Integration (3h)

**Tasks:**
- Implement `src/plorp/integrations/obsidian_bases.py`
  - `parse_project_note()`
  - `create_project_note()`
  - `list_projects()`
  - `get_project_info()`
  - `update_project_state()`
  - `add_task_to_project()`
  - `delete_project()`

**Testing:**
- Unit tests for note parsing
- Unit tests for YAML frontmatter handling
- Integration tests for file operations

**Deliverables:**
- `src/plorp/integrations/obsidian_bases.py` (~400 lines)
- `tests/test_integrations/test_obsidian_bases.py` (~200 lines)

---

### Phase 2: Core Projects Module (2h)

**Tasks:**
- Implement `src/plorp/core/projects.py`
  - `create_project()`
  - `list_projects()`
  - `get_project_info()`
  - `update_project_state()`
  - `delete_project()`
  - `create_task_in_project()`
  - `list_project_tasks()`
  - `list_tasks_by_domain()`
  - `list_orphaned_tasks()`

**Testing:**
- Unit tests for core functions
- Integration tests with TaskWarrior

**Deliverables:**
- `src/plorp/core/projects.py` (~300 lines)
- `tests/test_core/test_projects.py` (~250 lines)

---

### Phase 3: Domain Focus (1h)

**Tasks:**
- CLI focus storage (`~/.config/plorp/focus.txt`)
- CLI helper functions (get/set/clear)
- MCP conversation-scoped focus (default to "home")

**Testing:**
- Unit tests for focus file operations
- Integration tests with CLI commands

**Deliverables:**
- Focus management in `src/plorp/core/projects.py`
- Tests in `tests/test_core/test_projects.py`

---

### Phase 4: MCP Tools (3h)

**Tasks:**
- Add 9 MCP tools to `src/plorp/mcp/server.py`
- Error handling and validation
- Response formatting

**Testing:**
- MCP integration tests
- Mock conversation context for focus

**Deliverables:**
- Updated `src/plorp/mcp/server.py` (+~250 lines, total 26 tools)
- `tests/test_mcp/test_projects.py` (~150 lines)

---

### Phase 5: CLI Commands (2.5h)

**Tasks:**
- Add `plorp project` command group
- Add `plorp focus` command group
- Enhance `plorp add` for project support
- Enhance `plorp tasks` for filtering

**Testing:**
- CLI command tests
- Integration tests with core functions

**Deliverables:**
- Updated `src/plorp/cli.py` (+~200 lines)
- `tests/test_cli_projects.py` (~150 lines)

---

### Phase 6: Base Files & Templates (1h)

**Tasks:**
- Create default `.base` files
  - `vault/_bases/projects.base`
  - `vault/_bases/active-projects.base`
  - `vault/_bases/review-queue.base`
- Create project note template
- Document Base file structure

**Deliverables:**
- 3 `.base` files in `vault/_bases/`
- Updated `Docs/VAULT_SETUP.md`
- Example project notes

---

### Phase 7: Slash Commands (1h)

**Tasks:**
- Create `/create-project` command
- Create `/list-projects` command
- Create `/focus-domain` command
- Update existing commands to support domain

**Deliverables:**
- `.claude/commands/create-project.md`
- `.claude/commands/list-projects.md`
- `.claude/commands/focus-domain.md`
- Updated other slash commands

---

### Phase 8: Testing & Documentation (1.5h)

**Tasks:**
- Comprehensive test suite
- End-to-end workflow tests
- Update README
- Update architecture docs

**Deliverables:**
- Full test coverage
- Updated docs

---

## Testing Strategy

### Unit Tests

**Obsidian Bases Integration:**
```python
def test_create_project_note(tmp_path):
    """Test project note creation with frontmatter."""

def test_parse_project_note(tmp_path):
    """Test parsing project note frontmatter."""

def test_list_projects_filter_by_domain(tmp_path):
    """Test filtering projects by domain."""

def test_add_task_to_project(tmp_path):
    """Test adding task UUID to project."""
```

**Core Projects Module:**
```python
def test_create_project_validates_domain():
    """Test domain validation."""

def test_create_task_in_project_links_bidirectionally():
    """Test task-project bidirectional linking."""

def test_list_tasks_by_domain_uses_taskwarrior_filter():
    """Test TaskWarrior integration."""

def test_orphaned_tasks_filtering():
    """Test project.none filter."""
```

**Domain Focus:**
```python
def test_focus_file_persistence(tmp_path):
    """Test CLI focus storage."""

def test_mcp_focus_defaults_to_home():
    """Test MCP default domain."""
```

### Integration Tests

**MCP Integration:**
```python
def test_mcp_create_project():
    """Test project creation via MCP."""

def test_mcp_list_projects_with_filters():
    """Test project listing via MCP."""

def test_mcp_create_task_in_project():
    """Test task creation with project linking."""
```

**CLI Integration:**
```python
def test_cli_project_create():
    """Test project create command."""

def test_cli_tasks_domain_filter():
    """Test task filtering by domain."""

def test_cli_focus_persistence():
    """Test focus command."""
```

### End-to-End Tests

```python
def test_full_workflow_mcp():
    """
    Full workflow:
    1. Create project via MCP
    2. Add tasks to project
    3. List tasks in project
    4. Update project state
    5. Verify in Obsidian vault
    """

def test_full_workflow_cli():
    """
    Full workflow:
    1. Set focus
    2. Create project via CLI
    3. Add tasks with implicit domain
    4. Filter tasks by domain
    5. Update project state
    """
```

---

## Success Criteria

- [ ] Projects stored as markdown notes in `vault/projects/`
- [ ] Project notes have correct YAML frontmatter
- [ ] Base files (`.base`) created with multiple views
- [ ] 9 MCP tools working (create, list, get, update, delete, create-task, list-tasks, focus-set, focus-get)
- [ ] CLI commands working (`project create/list/show/set-state/delete`, `focus`, enhanced `add`/`tasks`)
- [ ] Domain focus persistent in CLI (`~/.config/plorp/focus.txt`)
- [ ] Domain focus conversation-scoped in MCP (defaults to "home")
- [ ] TaskWarrior filtering working (`.none`, `.any`, `.startswith`, `.is`)
- [ ] Bidirectional task-project linking (project tracks UUIDs, task annotates project path)
- [ ] Orphaned projects flagged (`needs_review: true` for 2-segment projects)
- [ ] Workstream suggestions loaded from config
- [ ] 3 slash commands created (`/create-project`, `/list-projects`, `/focus-domain`)
- [ ] Comprehensive test coverage (unit + integration + e2e)
- [ ] Documentation updated (README, VAULT_SETUP, architecture docs)
- [ ] Migration path from YAML (if applicable)

---

## Out of Scope (Future Sprints)

**Sprint 9+ Candidates:**
- Orphaned project review workflow (interactive prompt to assign workstream)
- Orphaned task review workflow (interactive prompt to assign project)
- "Quick tasks" pattern (default workstream for one-off tasks)
- Automated metadata cleanup (weekly/monthly review prompts)
- Enhanced Base views (list view, card view when available)
- Bases API integration (when Obsidian releases API)
- Project templates (different frontmatter schemas per domain)
- Project archiving workflow (move to archive folder, update state)
- Task migration between projects (reassign project field)
- Bulk operations (archive all completed projects)

---

## Engineering Q&A (Pre-Implementation)

**Purpose:** Questions identified during spec planning, before implementation starts.
**Status:** ✅ ALL RESOLVED (4/4)

### Q1: Folder structure approval

**Question:** Use this structure?
```
vault/
├── projects/           # All project notes
├── _bases/            # Base definitions
├── daily/
└── notes/
```

**Answer:** ✅ APPROVED

**Rationale:** Clean separation. `_bases/` prefix keeps it at top of file tree. `projects/` is parallel to `daily/` and `notes/`.

---

### Q2: Default Base views

**Question:** Include these default views?
- All Projects
- Active Projects
- By Domain (work/home/personal)
- Needs Review (orphaned projects)

**Answer:** ✅ APPROVED

**Rationale:** Covers primary use cases. Users can create custom views later.

---

### Q3: Task-Project Linking approach

**Question:** How to link tasks and projects bidirectionally?

**Options:**
- A: Project note tracks task UUIDs in frontmatter
- B: TaskWarrior task annotates project note path
- C: Both (bidirectional)

**Answer:** ✅ Option C (Both)

**Implementation:**
```python
# 1. Create task with project: field
task_uuid = create_task(description, project="work.marketing.website")

# 2. Annotate task with project note path
add_annotation(task_uuid, "Project: vault/projects/work.marketing.website.md")

# 3. Add UUID to project note frontmatter
add_task_to_project("work.marketing.website", task_uuid)
```

**Rationale:** Bidirectional linking is the Obsidian way. Enables navigation from both directions.

---

### Q4: Workstream suggestions storage

**Question:** Where to store suggested workstreams?

**Options:**
- A: In `~/.config/plorp/config.yaml` (configuration)
- B: In `vault/_config/workstreams.md` note (vault data)

**Answer:** ✅ Option A (config.yaml)

**Implementation:**
```yaml
# ~/.config/plorp/config.yaml
domains:
  work:
    suggested_workstreams:
      - engineering
      - marketing
      - operations
      - finance
      - sales
      - admin
  home:
    suggested_workstreams:
      - maintenance
      - family
      - health
      - finances
      - errands
  personal:
    suggested_workstreams:
      - health
      - learning
      - hobbies
      - finance
      - relationships
      - travel
```

**Rationale:** Configuration lives in config file. Can migrate to vault later if needed. YAGNI for now.

---

## Design Decisions Summary

**Storage:** Obsidian Bases (project notes with YAML frontmatter) ✅

**Hierarchy:** Flexible (1, 2, or 3 segments allowed) ✅

**Orphan handling:** Flag 2-segment projects with `needs_review: true` ✅

**Domain focus:** CLI persistent, MCP conversation-scoped (defaults to "home") ✅

**Task-project linking:** Bidirectional (project tracks UUIDs, task annotates path) ✅

**Workstreams:** Suggested list in config.yaml, hybrid validation ✅

**TaskWarrior filtering:** Use native filters (`.none`, `.any`, `.startswith`) ✅

**Base views:** All Projects, Active, By Domain, Needs Review ✅

---

## Engineering Questions (During Implementation)

**Purpose:** Questions that arise during implementation. Lead engineer adds questions here, PM/Architect answers.

**Instructions:**
- Lead Engineer: Append new questions as you encounter blockers or need clarification
- PM/Architect: Add answers with rationale below each question
- Format: `### Q[N]: [Question title]` with Context, Question, Answer, Status

**Status:** ✅ ALL RESOLVED (15/15 questions answered)

---

### Q1: YAML frontmatter field order consistency

**Context:** The spec shows `create_project_note()` using `yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)` to preserve insertion order. However, `update_project_state()` and `add_task_to_project()` also rebuild frontmatter but don't specify whether to preserve order.

**Question:** Should we:
- A: Always preserve field order when updating (use `sort_keys=False` everywhere)
- B: Allow alphabetical sorting when updating (simpler, but changes file on every update)
- C: Use a canonical field order (define explicit order, enforce on all writes)

If A or C, should we also preserve comments in YAML frontmatter, or strip them on updates?

**Answer:** ✅ **Option A: Always preserve field order with `sort_keys=False`**

**Implementation:**
```python
# Use this pattern in ALL functions that write frontmatter:
yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
```

**Comments:** Strip comments on updates (PyYAML limitation). Comments are lost when parsing to dict, and preserving them requires complex round-trip parsing libraries (like `ruamel.yaml`). Not worth the complexity for Sprint 8.

**Rationale:**
- Consistent field order makes git diffs readable
- Users can manually edit frontmatter and order is preserved on next update
- Alphabetical sorting creates noisy diffs (fields jump around)
- Comments are nice-to-have but not essential (user can re-add after manual edits)

**Status:** ✅ RESOLVED

---

### Q2: TaskWarrior project field validation

**Context:** The spec shows TaskWarrior integration using `project:work.marketing.website` format. TaskWarrior 3.x has specific rules for project names (e.g., no spaces, certain special chars).

**Question:** Should we validate project names before creating the TaskWarrior task, or trust TaskWarrior to reject invalid names and handle the error?

If validating, what regex pattern should we use? Something like `^[a-z0-9-]+(\.[a-z0-9-]+)*$`?

**Answer:** ✅ **Validate project names before TaskWarrior call**

**Implementation:**
```python
import re

PROJECT_NAME_PATTERN = re.compile(r'^[a-z0-9-]+$')
FULL_PATH_PATTERN = re.compile(r'^[a-z0-9-]+(\.[a-z0-9-]+)*$')

def validate_project_name(name: str) -> None:
    """Validate project name segment."""
    if not PROJECT_NAME_PATTERN.match(name):
        raise ValueError(
            f"Invalid project name: '{name}'. "
            f"Must contain only lowercase letters, numbers, and hyphens."
        )

def validate_full_path(full_path: str) -> None:
    """Validate complete project path."""
    if not FULL_PATH_PATTERN.match(full_path):
        raise ValueError(
            f"Invalid project path: '{full_path}'. "
            f"Must be dot-separated segments of lowercase letters, numbers, and hyphens."
        )
```

**Rationale:**
- Fail fast with helpful error messages
- Prevents cryptic TaskWarrior errors
- Enforces consistent naming (lowercase, hyphens for spaces)
- User sees clear validation error instead of TaskWarrior error

**Status:** ✅ RESOLVED

---

### Q3: Handling TaskWarrior task deletion

**Context:** When user deletes a task in TaskWarrior (via `task <uuid> delete`), the project note's `task_uuids` list will contain orphaned UUIDs.

**Question:** Should we:
- A: Ignore orphaned UUIDs (they just become dead references)
- B: Periodically validate UUIDs and remove dead ones (requires periodic sync job)
- C: Add a `plorp project sync <full-path>` command to clean up orphaned UUIDs on demand
- D: Warn in MCP/CLI output when listing project tasks (e.g., "3 of 5 tasks found, 2 missing")

**Answer:** ✅ **Option D: Warn in output** + **Option C: Add sync command (future sprint)**

**Implementation for Sprint 8:**
```python
def list_project_tasks(project_full_path: str) -> List[TaskInfo]:
    """List all tasks for a project with orphan detection."""
    # Get UUIDs from project note
    project = get_project_info(project_full_path)
    expected_count = len(project["task_uuids"]) if project else 0

    # Query TaskWarrior
    tasks = get_tasks([f"project:{project_full_path}"])

    # Warn if mismatch
    if expected_count != len(tasks):
        print(f"⚠️  Project has {expected_count} task references, "
              f"but only {len(tasks)} found in TaskWarrior. "
              f"Run 'plorp project sync {project_full_path}' to clean up.")

    return tasks
```

**Defer to Sprint 9:**
- `plorp project sync <full-path>` command
- Validates all UUIDs, removes orphaned ones from frontmatter

**Rationale:**
- Don't break workflows (orphaned UUIDs are harmless)
- Surface issue to user (warning visible but non-blocking)
- Provide tool for cleanup when needed (manual, on-demand)
- Avoids complexity of background sync jobs

**Status:** ✅ RESOLVED

---

### Q4: Project note filename conflicts

**Context:** Project notes are named `{full_path}.md`. If user creates:
1. `work.marketing.website-redesign`
2. `work.marketing-website.redesign`

Both would try to create `work.marketing-website.redesign.md` (if we naively replace dots with hyphens).

**Question:** The spec shows filenames as `work.marketing.website-redesign.md` (preserving dots). Is this correct? Should we:
- A: Use dots in filenames: `work.marketing.website-redesign.md` (matches spec)
- B: Escape dots: `work_marketing_website-redesign.md` (avoids confusion with file extensions)
- C: Use folders: `work/marketing/website-redesign.md` (hierarchical filesystem structure)

If A (dots in filenames), are we okay with filenames like `work.website.md` (looks like file with extension)?

**Answer:** ✅ **Option A: Use dots in filenames** (matches spec, already works)

**Implementation:**
```python
# Filename = full_path + ".md"
note_path = projects_dir / f"{full_path}.md"

# Examples:
# work.marketing.website-redesign → work.marketing.website-redesign.md
# work.website → work.website.md  # Valid, not confusing in practice
```

**Edge case handling:**
The scenario in your question (`work.marketing.website-redesign` vs `work.marketing-website.redesign`) creates **different filenames** because we preserve dots:
- `work.marketing.website-redesign` → `work.marketing.website-redesign.md`
- `work.marketing-website.redesign` → `work.marketing-website.redesign.md`

These are different files (note the dot vs hyphen in middle). No conflict.

**Rationale:**
- Spec is correct: dots in filenames work fine
- Obsidian handles `work.website.md` correctly (doesn't treat `.website` as extension)
- File systems support multiple dots (`.tar.gz` is common)
- Preserving dots keeps filename matching TaskWarrior `project:` field exactly
- Simpler than escaping (no conversion logic needed)

**Status:** ✅ RESOLVED

---

### Q5: Domain focus MCP conversation state storage

**Context:** Spec says "Store in conversation context (implementation depends on MCP framework)" for `plorp_set_focused_domain()`.

**Question:** How do we actually persist domain focus across MCP tool calls within a conversation? Options:
- A: Use module-level global variable (simple, works for single conversation)
- B: Use file-based storage like CLI (`~/.config/plorp/mcp_focus.txt`, updated on each call)
- C: Return focused domain in every MCP response and expect Claude to remember (no persistence)
- D: Accept that MCP focus is ephemeral and always defaults to "home" (spec default behavior)

Which approach is correct for plorp's MCP architecture?

**Answer:** ✅ **Option B: File-based storage** (`~/.config/plorp/mcp_focus.txt`)

**Implementation:**
```python
def get_focused_domain_mcp() -> str:
    """Get focused domain for MCP (file-based, survives server restarts)."""
    focus_file = get_config_dir() / "mcp_focus.txt"
    if focus_file.exists():
        return focus_file.read_text().strip()
    return "home"  # Default

def set_focused_domain_mcp(domain: str) -> None:
    """Set focused domain for MCP."""
    focus_file = get_config_dir() / "mcp_focus.txt"
    focus_file.write_text(domain)

@mcp.tool()
async def plorp_set_focused_domain(domain: str) -> dict:
    set_focused_domain_mcp(domain)
    return {"focused_domain": domain}
```

**Rationale:**
- **Module-level variable (A)**: Lost on MCP server restart
- **File-based (B)**: Persists across server restarts, simple implementation
- **Claude memory (C)**: Unreliable, Claude may forget between long conversations
- **Always default (D)**: Poor UX, user has to set focus every conversation

File-based storage is the sweet spot: simple, persistent, reliable.

**Status:** ✅ RESOLVED

---

### Q6: Project name transformation to title

**Context:** Spec shows `create_project_note()` converting `project_name` to title: `project_name.replace('-', ' ').title()`. This converts `website-redesign` → `Website Redesign`.

**Question:** What about edge cases:
- `api-v2` → `Api V2` (should be `API v2`)
- `seo-optimization` → `Seo Optimization` (should be `SEO Optimization`)
- `hvac-repair` → `Hvac Repair` (should be `HVAC Repair`)

Should we:
- A: Use simple `.replace('-', ' ').title()` (spec approach, predictable but naive)
- B: Implement smart title casing (complex, requires acronym dictionary)
- C: Keep original project_name as-is in heading (user can edit manually)
- D: Prompt user for title during creation (interactive, breaks MCP flow)

**Answer:** ✅ **Option A: Simple `.replace('-', ' ').title()`**

**Implementation:**
```python
# In create_project_note()
heading_title = project_name.replace('-', ' ').title()
content = f"""# {heading_title}

## Overview
{description or "Project description goes here."}
"""
```

**Rationale:**
- **YAGNI**: Smart casing is complex, brings marginal value
- **Predictable**: User knows exactly what transformation happens
- **Editable**: User can manually fix acronyms in Obsidian (it's markdown!)
- **Consistent**: Same transformation applied to all projects
- **Good enough**: Most project names work fine with simple title case

User can edit heading to `# API v2` or `# SEO Optimization` after creation if they care.

**Status:** ✅ RESOLVED

---

### Q7: Workstream validation behavior

**Context:** Spec says "Hybrid validation (suggest, but allow new with confirmation)" for workstreams. But the code shows no confirmation logic:

```python
# TODO: Check suggested workstreams (hybrid validation)
# For now, accept any workstream
```

**Question:** Should we implement hybrid validation in Sprint 8, or defer to future sprint?

If implementing now:
- Where does confirmation happen? (CLI can prompt, but MCP tools can't interact)
- Should MCP tools skip validation and allow any workstream?
- Should MCP tools reject non-suggested workstreams with error message?

**Answer:** ✅ **Defer hybrid validation to Sprint 9**

**Implementation for Sprint 8:**
```python
# Accept any workstream (no validation)
# TODO Sprint 9: Implement hybrid validation
#   - CLI: Prompt for confirmation if not in suggested list
#   - MCP: Accept any workstream (Claude decides, can suggest corrections)
```

**Rationale:**
- **Complexity**: Hybrid validation adds significant complexity (different behavior CLI vs MCP)
- **MCP architecture**: MCP tools shouldn't prompt/interact - they return data, Claude interprets
- **Low friction**: Allowing any workstream for now matches user requirement ("low friction capture")
- **Future sprint**: Can add validation workflow later when we have clearer patterns

**For Sprint 9:**
- CLI: `plorp project create website --workstream marketing-new`
  → "Workstream 'marketing-new' not in suggested list. Create anyway? [Y/n]"
- MCP: Claude can warn user if workstream looks unusual, suggest correction
  → "Did you mean 'marketing' instead of 'marketing-new'?"

**Status:** ✅ RESOLVED

---

### Q8: Parsing project notes with missing required fields

**Context:** `parse_project_note()` assumes all required fields exist in frontmatter:
```python
frontmatter["domain"]  # KeyError if missing
frontmatter["project_name"]
frontmatter["full_path"]
frontmatter["state"]
```

**Question:** How should we handle manually-edited project notes with missing fields?
- A: Raise ValueError (strict, breaks on user edits)
- B: Provide defaults for missing fields (e.g., `state` defaults to "active")
- C: Skip invalid notes in `list_projects()` but raise error in `get_project_info()`
- D: Add `is_valid` field to ProjectInfo to flag incomplete projects

Spec shows option C in `list_projects()`:
```python
except Exception as e:
    # Skip invalid project notes
    print(f"Warning: Failed to parse {note_path}: {e}")
    continue
```

Is this the correct approach for all parsing functions?

**Answer:** ✅ **Option C: Skip in list, error in get** (spec approach is correct)

**Implementation:**
```python
def parse_project_note(note_path: Path) -> ProjectInfo:
    """Parse project note, raise ValueError if invalid."""
    # Strict parsing - raises KeyError/ValueError on missing required fields
    frontmatter = yaml.safe_load(...)
    return ProjectInfo(
        domain=frontmatter["domain"],  # Required
        project_name=frontmatter["project_name"],  # Required
        full_path=frontmatter["full_path"],  # Required
        state=frontmatter["state"],  # Required
        # Optional fields with defaults:
        workstream=frontmatter.get("workstream"),
        description=frontmatter.get("description"),
        task_uuids=frontmatter.get("task_uuids", []),
        needs_review=frontmatter.get("needs_review", False),
        tags=frontmatter.get("tags", []),
        created_at=frontmatter.get("created_at", datetime.now().isoformat())
    )

def list_projects(...):
    """List projects, skip invalid notes with warning."""
    for note_path in projects_dir.glob("*.md"):
        try:
            project = parse_project_note(note_path)
            projects.append(project)
        except Exception as e:
            print(f"⚠️  Skipping invalid project note: {note_path.name} ({e})")
            continue

def get_project_info(full_path: str):
    """Get single project, raise error if invalid."""
    note_path = projects_dir / f"{full_path}.md"
    if not note_path.exists():
        return None
    return parse_project_note(note_path)  # Raises on invalid
```

**Rationale:**
- **List**: Defensive (don't break entire list because one note is corrupted)
- **Get**: Strict (user requested specific project, should know if it's broken)
- **Warning visible**: User sees which notes are problematic
- **User can fix**: Manual edits that break schema are surfaced, not silently ignored

**Status:** ✅ RESOLVED

---

### Q9: TypedDict vs dataclass for ProjectInfo

**Context:** Spec uses `TypedDict` for `ProjectInfo` following Sprint 6 patterns. But TypedDict doesn't enforce types at runtime, just static checking.

**Question:** Should we:
- A: Keep TypedDict (matches architecture, lightweight)
- B: Switch to `@dataclass` with validation (runtime checks, more robust)
- C: Add runtime validation in functions that create ProjectInfo (hybrid)

Given that `ProjectInfo` has 11 fields with specific types, is TypedDict sufficient for catching bugs?

**Answer:** ✅ **Option A: Keep TypedDict** (matches architecture)

**Rationale:**
- **Architectural consistency**: Sprint 6 established TypedDict pattern for all return types
- **Static checking is enough**: `mypy` catches type errors at dev time
- **Performance**: TypedDict has zero runtime overhead (it's just a dict)
- **Simplicity**: No need for `.asdict()` conversions, JSON serialization works directly
- **MCP-first design**: TypedDicts serialize cleanly to JSON for MCP responses

**Where bugs are caught:**
1. **Static analysis**: `mypy` checks function signatures, return types
2. **Testing**: Comprehensive tests validate data integrity
3. **Runtime**: `parse_project_note()` validates required fields exist (KeyError if missing)

**When to use dataclass:**
- If we need methods on ProjectInfo (we don't - pure data)
- If we need immutability (TypedDict dicts are mutable, but that's fine for our use case)
- If runtime validation is critical (we validate at parse time instead)

TypedDict is the right choice for plorp's architecture.

**Status:** ✅ RESOLVED

---

### Q10: Base file creation timing

**Context:** Phase 6 creates `.base` files. But these are vault data, not code.

**Question:** Should we:
- A: Create `.base` files programmatically in `create_project_note()` if missing
- B: Ship `.base` files as templates in `src/plorp/templates/` and copy on first run
- C: Document manual creation in VAULT_SETUP.md (user's responsibility)
- D: Create `.base` files in test fixtures only (not production code)

The spec shows templates but doesn't specify creation mechanism. What's the plorp pattern?

**Answer:** ✅ **Option C: Document in VAULT_SETUP.md** (user's vault, user's responsibility)

**Implementation:**

**In `Docs/VAULT_SETUP.md`:**
```markdown
## Obsidian Bases Setup

### Install Bases Plugin
1. Open Obsidian Settings
2. Go to Core Plugins
3. Enable "Bases"

### Create Project Dashboard

Create `vault/_bases/projects.base` with this content:

[Include full YAML template from spec]
```

**Optionally:** Provide example `.base` files in `examples/` directory for copy-paste.

**Rationale:**
- **Vault ownership**: User's vault structure is their choice
- **Flexibility**: User may want different Base views than our defaults
- **Simplicity**: No code complexity for file creation
- **Documentation**: VAULT_SETUP.md is the right place for setup instructions
- **Examples**: Providing templates for copy-paste is helpful without being invasive

**Future enhancement**: Could add `plorp init-bases` command to copy templates if users request it.

**Status:** ✅ RESOLVED

---

### Q11: CLI focus file location

**Context:** Spec uses `~/.config/plorp/focus.txt` for persistent CLI focus. But existing config uses:
- `~/.config/plorp/config.yaml` for configuration
- What about `$XDG_CONFIG_HOME` override?

**Question:** Should focus file respect `XDG_CONFIG_HOME` like config does?

```python
# Current pattern from config.py:
config_dir = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config")) / "plorp"

# Should focus be:
focus_file = config_dir / "focus.txt"  # Respects XDG
# or:
focus_file = Path.home() / ".config/plorp/focus.txt"  # Spec example
```

**Answer:** ✅ **Respect `XDG_CONFIG_HOME`** (consistency with existing pattern)

**Implementation:**
```python
from ..config import get_config_dir  # Reuse existing function

def get_focus_file_cli() -> Path:
    """Get CLI focus file path (respects XDG_CONFIG_HOME)."""
    return get_config_dir() / "cli_focus.txt"

def get_focus_file_mcp() -> Path:
    """Get MCP focus file path (respects XDG_CONFIG_HOME)."""
    return get_config_dir() / "mcp_focus.txt"

def get_focused_domain_cli() -> str:
    """Get focused domain for CLI."""
    focus_file = get_focus_file_cli()
    if focus_file.exists():
        return focus_file.read_text().strip()
    return "home"

def set_focused_domain_cli(domain: str) -> None:
    """Set focused domain for CLI."""
    focus_file = get_focus_file_cli()
    focus_file.parent.mkdir(parents=True, exist_ok=True)
    focus_file.write_text(domain)
```

**File naming:**
- `cli_focus.txt` (CLI persistent focus)
- `mcp_focus.txt` (MCP persistent focus)

**Rationale:**
- Consistency with existing config pattern
- Respects user's `$XDG_CONFIG_HOME` preference
- Separate files for CLI vs MCP (independent focus contexts)

**Status:** ✅ RESOLVED

---

### Q12: Task annotation format for project linking

**Context:** Spec shows:
```python
add_annotation(task_uuid, f"Project: vault/projects/{project_full_path}.md")
```

**Question:** Should the annotation path be:
- A: Relative to vault root: `vault/projects/work.marketing.website.md` (spec approach)
- B: Absolute path: `/Users/jsd/vault/projects/work.marketing.website.md` (unambiguous)
- C: Obsidian link format: `[[work.marketing.website]]` (clickable in Obsidian if task exported)
- D: Just the full_path: `work.marketing.website` (minimal, can reconstruct path)

Which format is most useful for cross-referencing?

**Answer:** ✅ **Option D: Just the full_path** (minimal, portable)

**Implementation:**
```python
def create_task_in_project(description, project_full_path, ...):
    # Create task
    task_uuid = create_task(description, project=project_full_path, ...)

    # Add annotation (just the project path)
    add_annotation(task_uuid, f"plorp-project:{project_full_path}")

    return task_uuid
```

**Format:** `plorp-project:work.marketing.website`

**Rationale:**
- **Minimal**: Just the data needed to identify project
- **Portable**: Works regardless of vault location
- **Reconstructable**: Can always build full path: `{vault_path}/projects/{full_path}.md`
- **Prefix**: `plorp-project:` makes it machine-parsable (can filter annotations)
- **No ambiguity**: `full_path` uniquely identifies project

**Usage:**
```python
# Later, to find project note from task annotation:
annotations = get_task_annotations(task_uuid)
for ann in annotations:
    if ann.startswith("plorp-project:"):
        project_path = ann.split(":", 1)[1]  # "work.marketing.website"
        note_path = vault_path / "projects" / f"{project_path}.md"
```

**Status:** ✅ RESOLVED

---

### Q13: Handling project state transitions

**Context:** Spec defines states: `active/planning/completed/blocked/archived`. But no validation on transitions (e.g., can you go from `completed` → `active`?).

**Question:** Should we:
- A: Allow any state transition (spec approach, flexible)
- B: Validate state machine (e.g., archived → active requires "unarchive" flag)
- C: Log state changes with timestamps (audit trail in frontmatter)
- D: Warn on suspicious transitions (completed → active) but allow

If C, should we add `state_history` field to frontmatter?

**Answer:** ✅ **Option A: Allow any state transition** (flexibility over constraints)

**Implementation:**
```python
VALID_STATES = ["active", "planning", "completed", "blocked", "archived"]

def update_project_state(full_path: str, state: str) -> ProjectInfo:
    """Update project state (no transition validation)."""
    if state not in VALID_STATES:
        raise ValueError(f"Invalid state: {state}. Must be one of {VALID_STATES}")

    # Update frontmatter (allow any transition)
    # ...
```

**Rationale:**
- **User knows best**: User understands their workflow, don't constrain them
- **Flexibility**: "Completed" → "Active" is valid (project reopened, new phase)
- **YAGNI**: State machine validation adds complexity without clear benefit
- **Simplicity**: Just validate state is in allowed list, no transition rules

**Future enhancement (Sprint 9+):**
- If user requests audit trail: Add `last_state_change: timestamp` field
- If user requests warnings: CLI can warn "⚠️  Unusual transition: completed → active"
- But for Sprint 8: Keep it simple

**Status:** ✅ RESOLVED

---

### Q14: Error handling for vault directory missing

**Context:** `get_projects_dir()` calls `get_vault_path() / "projects"`. If vault doesn't exist or is misconfigured:

```python
def get_projects_dir() -> Path:
    from ..config import get_vault_path
    return get_vault_path() / "projects"
```

**Question:** Should we:
- A: Trust `get_vault_path()` to exist (assume config is valid)
- B: Add explicit check and raise helpful error if vault missing
- C: Auto-create `vault/projects/` directory on first use (spec shows this in Phase 0)
- D: Return None and handle gracefully in callers

Spec shows:
```python
projects_dir.mkdir(parents=True, exist_ok=True)  # In create_project_note()
```

Should all functions auto-create the directory, or just creation functions?

**Answer:** ✅ **Option C: Auto-create in write functions only** (spec approach)

**Implementation:**
```python
def get_projects_dir() -> Path:
    """Get projects directory (doesn't create it)."""
    from ..config import get_vault_path
    return get_vault_path() / "projects"

def create_project_note(...):
    """Create project note (creates directory if missing)."""
    projects_dir = get_projects_dir()
    projects_dir.mkdir(parents=True, exist_ok=True)  # Auto-create
    # ...

def list_projects(...):
    """List projects (returns empty list if directory missing)."""
    projects_dir = get_projects_dir()

    if not projects_dir.exists():
        return ProjectListResult(projects=[], grouped_by_domain={})

    # ...

def get_project_info(full_path: str):
    """Get project (returns None if directory missing)."""
    projects_dir = get_projects_dir()
    note_path = projects_dir / f"{full_path}.md"

    if not note_path.exists():
        return None
    # ...
```

**Rationale:**
- **Write functions**: Auto-create directory (good UX, defensive)
- **Read functions**: Handle missing directory gracefully (empty results, not errors)
- **Spec is correct**: Shows auto-create in `create_project_note()`
- **Defensive programming**: Don't error on missing directory, handle it

**Status:** ✅ RESOLVED

---

### Q15: Filtering tasks by workstream (2-segment projects)

**Context:** Spec mentions filtering tasks by workstream:
```bash
plorp tasks --workstream-only
# → task project.any: export + filter for 2-segment projects
```

**Question:** How do we actually filter for "2-segment projects" in TaskWarrior?

TaskWarrior doesn't have a "count dots in project field" filter. Should we:
- A: Export all tasks with `project.any:` and post-filter in Python (check `project.count('.') == 1`)
- B: Maintain a separate filter for each workstream pattern (e.g., `project:work.marketing project:work.engineering`)
- C: Use regex if TaskWarrior supports it
- D: This feature is actually for listing projects (not tasks), and the spec is unclear

Clarify the intended behavior of `--workstream-only` flag.

**Answer:** ✅ **Option A: Post-filter in Python** (simple, works for all cases)

**Implementation:**
```python
def list_tasks_with_filters(
    domain: str = None,
    orphaned: bool = False,
    workstream_only: bool = False,
    sort_by: str = "urgency"
) -> List[TaskInfo]:
    """List tasks with hierarchy-based filtering."""

    # Build TaskWarrior filter
    if orphaned:
        tw_filter = ["project.none:"]
    elif domain:
        tw_filter = [f"project.startswith:{domain}"]
    else:
        tw_filter = ["project.any:"]

    # Query TaskWarrior
    tasks = get_tasks(tw_filter)

    # Post-filter for segment count
    if workstream_only:
        # Filter for 2-segment projects (domain.workstream)
        tasks = [t for t in tasks if t.get("project", "").count(".") == 1]

    # Sort
    if sort_by == "urgency":
        tasks.sort(key=lambda t: t.get("urgency", 0), reverse=True)
    elif sort_by == "due":
        tasks.sort(key=lambda t: t.get("due", ""))
    # ...

    return tasks
```

**CLI usage:**
```bash
# Show all 2-segment projects (domain.workstream, no project name)
plorp tasks --workstream-only

# Show 2-segment projects in work domain
plorp tasks --domain work --workstream-only
```

**Rationale:**
- **Simple**: Python post-filtering is straightforward
- **Flexible**: Can combine with other filters
- **No TaskWarrior limitations**: Works without regex/complex queries
- **Performance**: Acceptable for typical task counts (<10k tasks)

**Status:** ✅ RESOLVED

---

## Implementation Summary

**Purpose:** Lead engineer fills this after implementation is complete.

**Status:** (To be filled during implementation)

---

## Handoff to Next Sprint

**Purpose:** Context for next sprint or future work related to this feature.

**Status:** (To be filled during implementation)

---

## Document Status

**Version:** 1.0.0
**Status:** 📋 READY FOR IMPLEMENTATION
**Q&A Status (Pre-Implementation):** ✅ ALL RESOLVED (4/4)
**Q&A Status (During Implementation):** (TBD)
**Implementation Status:** (TBD)
**Reviewed By:** PM (2025-10-07)
**Date:** 2025-10-07

---

**Sprint 8: READY FOR IMPLEMENTATION**

Project management with Obsidian Bases integration - an elegant, unified system for managing projects, tasks, and documentation in a single vault.
