# ABOUTME: Project management core module - high-level project operations
# ABOUTME: Combines Obsidian Bases integration with TaskWarrior for complete project workflows

"""
Project Management Core Module

High-level project operations using Obsidian Bases integration.
Provides unified API for project and task management.
"""

from typing import Optional
from pathlib import Path
from ..integrations.obsidian_bases import (
    create_project_note,
    list_projects as list_projects_bases,
    get_project_info as get_project_info_bases,
    update_project_state as update_project_state_bases,
    delete_project as delete_project_bases,
    add_task_to_project as add_task_to_project_bases,
    get_vault_path,
)
from ..integrations.taskwarrior import create_task, add_annotation, get_tasks
from ..config import get_config_dir
from .types import ProjectInfo, ProjectListResult, TaskInfo


# ============================================================================
# Workstream Validation (Sprint 8.5 Item 3)
# ============================================================================

SUGGESTED_WORKSTREAMS = {
    "work": ["engineering", "marketing", "finance", "operations", "hr"],
    "home": ["maintenance", "family", "health", "personal-dev"],
    "personal": ["learning", "creative", "fitness", "social"]
}


def validate_workstream(domain: str, workstream: str) -> Optional[str]:
    """
    Validate workstream against suggested list for domain.

    Sprint 8.5 Item 3: Warns about non-standard workstreams to help users
    maintain consistent project taxonomy.

    Args:
        domain: Project domain (work/home/personal)
        workstream: Workstream to validate

    Returns:
        Warning message if workstream not in suggested list, None if valid
    """
    if domain in SUGGESTED_WORKSTREAMS:
        if workstream not in SUGGESTED_WORKSTREAMS[domain]:
            return f"Workstream '{workstream}' not in suggested list for '{domain}'"
    return None


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

    Args:
        name: Project name
        domain: work/home/personal
        workstream: Workstream (optional)
        state: Project state (default: active)
        description: Short description (optional)

    Returns:
        ProjectInfo TypedDict

    Raises:
        ValueError: If domain invalid or project exists
    """
    # Validate domain
    valid_domains = ["work", "home", "personal"]
    if domain not in valid_domains:
        raise ValueError(f"Invalid domain: {domain}. Must be one of {valid_domains}")

    # TODO Sprint 9: Check suggested workstreams (hybrid validation)
    # For now, accept any workstream

    return create_project_note(domain, workstream, name, state, description)


def list_projects(
    domain: Optional[str] = None,
    state: Optional[str] = None
) -> ProjectListResult:
    """
    List projects with optional filters.

    Args:
        domain: Filter by domain (optional)
        state: Filter by state (optional)

    Returns:
        ProjectListResult with list and grouped dict
    """
    return list_projects_bases(domain=domain, state=state)


def get_project_info(full_path: str) -> Optional[ProjectInfo]:
    """
    Get single project by full path.

    Args:
        full_path: Full project path (e.g., "work.marketing.website")

    Returns:
        ProjectInfo or None if not found
    """
    return get_project_info_bases(full_path)


def update_project_state(full_path: str, state: str) -> ProjectInfo:
    """
    Update project state.

    Args:
        full_path: Full project path
        state: New state (active/planning/completed/blocked/archived)

    Returns:
        Updated ProjectInfo

    Raises:
        ValueError: If project not found or invalid state
    """
    return update_project_state_bases(full_path, state)


def delete_project(full_path: str) -> bool:
    """
    Delete project.

    Args:
        full_path: Full project path

    Returns:
        True if deleted, False if not found
    """
    return delete_project_bases(full_path)


def create_task_in_project(
    description: str,
    project_full_path: str,
    due: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[list[str]] = None
) -> str:
    """
    Create task in TaskWarrior and link to project.

    Sprint 8.6 State Sync:
    1. Creates task with project: field (TaskWarrior)
    2. Annotates task with project note path (TaskWarrior)
    3. Adds task UUID to project note frontmatter (Obsidian)
    4. Syncs Tasks section in note body (Obsidian)

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
        RuntimeError: If TaskWarrior fails
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
    # Format: plorp-project:work.marketing.website
    add_annotation(task_uuid, f"plorp-project:{project_full_path}")

    # Add task UUID to project note frontmatter
    add_task_to_project_bases(project_full_path, task_uuid)

    # Sprint 8.6: Sync note body Tasks section
    # Import locally to allow test mocking
    from ..integrations.obsidian_bases import get_vault_path as get_vault
    vault_path = get_vault()
    _sync_project_task_section(vault_path, project_full_path)

    return task_uuid


def list_project_tasks(project_full_path: str) -> list[TaskInfo]:
    """
    List all tasks for a project.

    Queries TaskWarrior with project: filter.
    Warns if project has orphaned task UUIDs.

    Args:
        project_full_path: Full project path

    Returns:
        List of TaskInfo dicts
    """
    # Get expected count from project note
    project = get_project_info_bases(project_full_path)
    expected_count = len(project["task_uuids"]) if project else 0

    # Query TaskWarrior
    tasks = get_tasks([f"project:{project_full_path}"])

    # Warn if mismatch (orphaned UUIDs)
    if expected_count != len(tasks):
        print(
            f"⚠️  Project has {expected_count} task references, "
            f"but only {len(tasks)} found in TaskWarrior. "
            f"Run 'plorp project sync {project_full_path}' to clean up."
        )

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
            urgency=t.get("urgency", 0.0)
        )
        for t in tasks
    ]


def list_tasks_by_domain(domain: str) -> list[TaskInfo]:
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
            urgency=t.get("urgency", 0.0)
        )
        for t in tasks
    ]


def list_orphaned_tasks() -> list[TaskInfo]:
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
            urgency=t.get("urgency", 0.0)
        )
        for t in tasks
    ]


# ============================================================================
# State Synchronization (Sprint 8.5)
# ============================================================================


def remove_task_from_all_projects(vault_path: Path, uuid: str) -> None:
    """
    Remove task UUID from all project frontmatter and sync note bodies.

    Part of State Synchronization pattern: when task is marked done or deleted
    in TaskWarrior, this function removes the UUID from all project notes.

    Sprint 8.6 State Sync:
    - Removes UUID from frontmatter
    - Syncs Tasks section in note body

    Handles edge cases gracefully:
    - No projects directory: silent return
    - UUID not in any project: no changes made
    - UUID in multiple projects: removed from ALL (data integrity fix per Q4)

    Args:
        vault_path: Path to Obsidian vault
        uuid: Task UUID to remove

    Sprint 8.5 Item 1: Critical State Sync function
    """
    from ..integrations.obsidian_bases import remove_task_from_project as remove_uuid

    projects_dir = vault_path / "projects"

    # Graceful handling: no projects directory
    if not projects_dir.exists():
        return

    # Track projects modified for sync
    modified_projects = []

    # Scan all project files
    for project_file in projects_dir.rglob("*.md"):
        # Extract full_path from filename (e.g., "work.marketing.website.md" → "work.marketing.website")
        full_path = project_file.stem

        # Get project info to check if UUID exists
        project = get_project_info_bases(full_path)
        if not project:
            continue

        # Remove UUID if present (obsidian_bases handles the frontmatter update)
        if uuid in project.get("task_uuids", []):
            remove_uuid(full_path, uuid)
            modified_projects.append(full_path)

    # Sprint 8.6: Sync all modified project note bodies
    for full_path in modified_projects:
        _sync_project_task_section(vault_path, full_path)


# ============================================================================
# Orphaned Project Management (Sprint 8.5 Items 4 & 5)
# ============================================================================


def find_orphaned_projects(vault_path: Path) -> list[ProjectInfo]:
    """
    Find all projects with needs_review flag (2-segment projects).

    Sprint 8.5 Item 4: Returns projects that need workstream assignment.

    Args:
        vault_path: Path to Obsidian vault

    Returns:
        List of ProjectInfo dicts with needs_review: true
    """
    projects_dir = vault_path / "projects"

    if not projects_dir.exists():
        return []

    orphaned = []
    for project_file in projects_dir.rglob("*.md"):
        # Extract full_path from filename
        full_path = project_file.stem

        # Get project info
        project = get_project_info_bases(full_path)
        if not project:
            continue

        # Check if needs review
        if project.get("needs_review", False):
            orphaned.append(project)

    return orphaned


def rename_project(vault_path: Path, old_path: str, new_path: str) -> ProjectInfo:
    """
    Rename project file and update all related state (State Sync).

    Sprint 8.5 Item 4: Renames 2-segment to 3-segment project.

    State Sync includes:
    1. Rename project file (old_path.md → new_path.md)
    2. Update frontmatter (full_path, workstream, needs_review)
    3. Update ALL task projects in TaskWarrior (bidirectional sync)

    Args:
        vault_path: Path to Obsidian vault
        old_path: Old full project path (e.g., "work.api")
        new_path: New full project path (e.g., "work.engineering.api")

    Returns:
        Updated ProjectInfo

    Raises:
        ValueError: If old project not found
        RuntimeError: If TaskWarrior update fails
    """
    from ..integrations.taskwarrior import modify_task

    # 1. Get existing project info
    project = get_project_info_bases(old_path)
    if not project:
        raise ValueError(f"Project not found: {old_path}")

    # 2. Parse new path components
    parts = new_path.split(".")
    if len(parts) < 2:
        raise ValueError(f"Invalid new path (must be at least domain.workstream): {new_path}")

    domain = parts[0]
    workstream = parts[1] if len(parts) >= 2 else None
    name = parts[2] if len(parts) >= 3 else parts[1]

    # 3. Rename file
    old_file = vault_path / "projects" / f"{old_path}.md"
    new_file = vault_path / "projects" / f"{new_path}.md"

    if not old_file.exists():
        raise ValueError(f"Project file not found: {old_file}")

    if new_file.exists():
        raise ValueError(f"Project already exists: {new_path}")

    # Read old content
    old_content = old_file.read_text()

    # Update frontmatter
    import re
    import yaml

    # Parse frontmatter
    fm_match = re.match(r'^---\n(.*?)\n---\n(.*)$', old_content, re.DOTALL)
    if fm_match:
        frontmatter = yaml.safe_load(fm_match.group(1))
        body = fm_match.group(2)

        # Update frontmatter fields
        frontmatter["full_path"] = new_path
        frontmatter["domain"] = domain
        frontmatter["workstream"] = workstream
        frontmatter["name"] = name
        frontmatter["needs_review"] = False  # No longer needs review

        # Serialize back
        new_content = "---\n" + yaml.dump(frontmatter, default_flow_style=False) + "---\n" + body
    else:
        # No frontmatter, keep content as-is
        new_content = old_content

    # Write to new file
    new_file.write_text(new_content)

    # Delete old file
    old_file.unlink()

    # 4. Update TaskWarrior for all tasks in project (State Sync)
    from ..integrations.taskwarrior import add_annotation

    for task_uuid in project.get("task_uuids", []):
        # Update project field
        success = modify_task(task_uuid, project=new_path)
        if not success:
            # Warning, but don't fail the whole operation
            print(f"⚠️  Warning: Could not update TaskWarrior project for task {task_uuid}")

        # Add annotation with new project path (bidirectional link)
        add_annotation(task_uuid, f"plorp-project:{new_path}")

    # 5. Return updated project info
    return get_project_info_bases(new_path)


def assign_task_to_project(uuid: str, project_full_path: str, vault_path: Path) -> None:
    """
    Assign orphaned task to project with bidirectional State Sync.

    Sprint 8.5 Item 5: Assigns task without project to a specific project.

    State Sync includes:
    1. Update TaskWarrior project field
    2. Add annotation to task (plorp-project:...)
    3. Add UUID to project frontmatter

    Args:
        uuid: Task UUID
        project_full_path: Full project path (e.g., "work.marketing.website")
        vault_path: Path to Obsidian vault

    Raises:
        ValueError: If project not found
        RuntimeError: If TaskWarrior update fails
    """
    from ..integrations.taskwarrior import modify_task, add_annotation

    # 1. Verify project exists
    project = get_project_info_bases(project_full_path)
    if not project:
        raise ValueError(f"Project not found: {project_full_path}")

    # 2. Update TaskWarrior (State Sync part 1)
    success = modify_task(uuid, project=project_full_path)
    if not success:
        raise RuntimeError(f"Failed to update TaskWarrior project for task {uuid}")

    # 3. Add annotation (State Sync part 2)
    add_annotation(uuid, f"plorp-project:{project_full_path}")

    # 4. Add UUID to project frontmatter (State Sync part 3)
    add_task_to_project_bases(project_full_path, uuid)


# ============================================================================
# Domain Focus Management
# ============================================================================


def get_focused_domain_cli() -> str:
    """
    Get focused domain for CLI (file-based persistence).

    Returns:
        Domain name (default: "home")
    """
    focus_file = get_config_dir() / "cli_focus.txt"
    if focus_file.exists():
        return focus_file.read_text().strip()
    return "home"


def set_focused_domain_cli(domain: str) -> None:
    """
    Set focused domain for CLI.

    Args:
        domain: Domain to focus (work/home/personal)
    """
    focus_file = get_config_dir() / "cli_focus.txt"
    focus_file.parent.mkdir(parents=True, exist_ok=True)
    focus_file.write_text(domain)


def get_focused_domain_mcp() -> str:
    """
    Get focused domain for MCP (file-based persistence).

    Returns:
        Domain name (default: "home")
    """
    focus_file = get_config_dir() / "mcp_focus.txt"
    if focus_file.exists():
        return focus_file.read_text().strip()
    return "home"


def set_focused_domain_mcp(domain: str) -> None:
    """
    Set focused domain for MCP.

    Args:
        domain: Domain to focus (work/home/personal)
    """
    focus_file = get_config_dir() / "mcp_focus.txt"
    focus_file.parent.mkdir(parents=True, exist_ok=True)
    focus_file.write_text(domain)


# ============================================================================
# Sprint 8.6: Auto-Sync Infrastructure
# ============================================================================


def process_project_note(vault_path: Path, project_path: str) -> int:
    """
    Process checked tasks in project note (mark done, sync state).

    Sprint 8.6: Checkbox processing for project notes - similar to daily note
    review but for project-based task completion.

    Workflow:
    1. Parse checked tasks from project note
    2. Mark each as done in TaskWarrior
    3. Remove UUIDs from frontmatter (State Sync)
    4. Re-sync note body to reflect changes

    Args:
        vault_path: Path to Obsidian vault
        project_path: Full project path (e.g., "work.marketing.website")

    Returns:
        Number of tasks marked as done

    Raises:
        ProjectNotFoundError: If project note doesn't exist
    """
    from ..parsers.markdown import parse_checked_tasks
    from ..integrations.taskwarrior import mark_done
    from .exceptions import ProjectNotFoundError

    # 1. Read project note
    note_path = vault_path / "projects" / f"{project_path}.md"
    if not note_path.exists():
        raise ProjectNotFoundError(project_path)

    # 2. Parse checked tasks
    checked_uuids = parse_checked_tasks(note_path)

    if not checked_uuids:
        return 0  # No checked tasks

    # 3. Mark each task as done in TaskWarrior
    count = 0
    for uuid in checked_uuids:
        try:
            mark_done(uuid)
            count += 1
        except Exception as e:
            # Log but continue processing other tasks
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to mark task {uuid} as done: {e}")
            continue

    # 4. State Sync: Remove completed task UUIDs from ALL project frontmatter
    # (This handles the case where a task might be in multiple projects)
    for uuid in checked_uuids:
        remove_task_from_all_projects(vault_path, uuid)

    # Note: remove_task_from_all_projects already calls _sync_project_task_section
    # for each modified project, so we don't need to call it again here.

    return count


def sync_all_projects(vault_path: Path) -> dict:
    """
    Sync ALL project note bodies with their frontmatter (bulk reconciliation).

    Sprint 8.6: Admin command for reconciling state after external TaskWarrior
    changes (e.g., tasks marked done via CLI, mobile apps, etc.).

    Use cases:
    - After bulk TaskWarrior operations
    - After TaskWarrior sync from other devices
    - Periodic maintenance to ensure state consistency

    Args:
        vault_path: Path to Obsidian vault

    Returns:
        Dict with sync statistics:
        {
            "synced": int,  # Number of projects synced
            "errors": list  # List of (project_path, error_msg) tuples
        }
    """
    import logging
    logger = logging.getLogger(__name__)

    projects_dir = vault_path / "projects"
    stats = {
        "synced": 0,
        "errors": []
    }

    # Graceful handling: no projects directory
    if not projects_dir.exists():
        return stats

    # Sync all project files
    for project_file in projects_dir.rglob("*.md"):
        # Extract full_path from filename
        full_path = project_file.stem

        try:
            # Sync this project's task section
            _sync_project_task_section(vault_path, full_path)
            stats["synced"] += 1
        except Exception as e:
            # Log error but continue with other projects
            error_msg = f"{type(e).__name__}: {str(e)}"
            stats["errors"].append((full_path, error_msg))
            logger.error(f"Failed to sync project '{full_path}': {error_msg}")
            continue

    return stats


def _sync_project_task_section(vault_path: Path, project_path: str) -> None:
    """
    Update the ## Tasks section in project note to match frontmatter.

    Sprint 8.6: This is INTERNAL infrastructure called by all project
    modification functions. NOT a user-facing command.

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
    import logging
    from ..parsers.markdown import (
        _split_frontmatter_and_body,
        _format_with_frontmatter,
        _format_date,
        _remove_section,
    )
    from ..integrations.taskwarrior import get_task_info
    from .exceptions import ProjectNotFoundError, TaskNotFoundError

    logger = logging.getLogger(__name__)

    # 1. Read project note
    note_path = vault_path / "projects" / f"{project_path}.md"
    if not note_path.exists():
        raise ProjectNotFoundError(project_path)

    content = note_path.read_text()
    frontmatter, body = _split_frontmatter_and_body(content)

    # 2. Get task UUIDs from frontmatter
    task_uuids = frontmatter.get("task_uuids", [])

    # 3. Query TaskWarrior for task details
    tasks = []
    for uuid in task_uuids:
        try:
            task = get_task_info(uuid)
            # Only include pending tasks (per Q1/Q20 decision)
            if task and task.get("status") == "pending":
                tasks.append(task)
        except TaskNotFoundError:
            # Orphaned UUID - skip (Sprint 8.5 reconciliation will clean)
            logger.warning(
                f"Orphaned UUID '{uuid}' in project '{project_path}' - skipping. "
                f"Run 'plorp sync-all' to clean up."
            )
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

            # Metadata (Q14: order is due, priority, uuid)
            metadata = []
            if "due" in task:
                due_str = _format_date(task["due"])
                metadata.append(f"due: {due_str}")
            if "priority" in task:
                metadata.append(f"priority: {task['priority']}")
            # UUID always last
            metadata.append(f"uuid: {task['uuid']}")

            meta_str = ", ".join(metadata)
            task_lines.append(f"- {checkbox} {desc} ({meta_str})")

        tasks_section = f"## Tasks ({len(tasks)})\n\n"
        tasks_section += "\n".join(task_lines)
        tasks_section += "\n"

        # Append to body
        new_body = body_without_tasks.rstrip() + "\n\n" + tasks_section
    else:
        # No tasks - don't add section (per Q1)
        new_body = body_without_tasks

    # 6. Write updated note
    new_content = _format_with_frontmatter(frontmatter, new_body)
    note_path.write_text(new_content)
