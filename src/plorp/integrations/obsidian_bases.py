# ABOUTME: Obsidian Bases integration - manages project notes as Obsidian Bases data source
# ABOUTME: Projects are markdown notes in vault/projects/ with YAML frontmatter

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
from ..config import get_vault_path


def get_projects_dir() -> Path:
    """Get vault/projects/ directory."""
    return get_vault_path() / "projects"


def parse_project_note(note_path: Path) -> ProjectInfo:
    """
    Parse project note frontmatter into ProjectInfo.

    Args:
        note_path: Path to project note file

    Returns:
        ProjectInfo with all metadata fields

    Raises:
        ValueError: If frontmatter missing or malformed
        KeyError: If required fields missing
    """
    content = note_path.read_text()

    # Split frontmatter and body
    if not content.startswith("---"):
        raise ValueError(f"Project note missing frontmatter: {note_path}")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Project note missing frontmatter: {note_path}")

    frontmatter_text = parts[1]
    frontmatter = yaml.safe_load(frontmatter_text)

    if not isinstance(frontmatter, dict):
        raise ValueError(f"Invalid frontmatter in {note_path}")

    # Return ProjectInfo TypedDict (required fields will raise KeyError if missing)
    return ProjectInfo(
        domain=frontmatter["domain"],  # Required
        workstream=frontmatter.get("workstream"),  # Optional
        project_name=frontmatter["project_name"],  # Required
        full_path=frontmatter["full_path"],  # Required
        state=frontmatter["state"],  # Required
        created_at=frontmatter.get("created_at", datetime.now().isoformat()),  # Optional with default
        description=frontmatter.get("description"),  # Optional
        task_uuids=frontmatter.get("task_uuids", []),  # Optional with default
        needs_review=frontmatter.get("needs_review", False),  # Optional with default
        tags=frontmatter.get("tags", []),  # Optional with default
        note_path=str(note_path)  # Computed
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
    heading_title = project_name.replace('-', ' ').title()
    content = f"""---
{yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)}---

# {heading_title}

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
            print(f"⚠️  Skipping invalid project note: {note_path.name} ({e})")
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

    # Write back (preserve field order with sort_keys=False)
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

    Raises:
        ValueError: If project not found
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

    # Write back (preserve field order)
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
