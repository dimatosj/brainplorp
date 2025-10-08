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

    # Add task UUID to project note
    add_task_to_project_bases(project_full_path, task_uuid)

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
