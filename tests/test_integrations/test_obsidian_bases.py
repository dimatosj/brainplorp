# ABOUTME: Tests for Obsidian Bases integration - project note parsing and management
# ABOUTME: Tests YAML frontmatter handling, project creation, listing, updates, and deletions

import pytest
from pathlib import Path
from datetime import datetime
from brainplorp.integrations.obsidian_bases import (
    parse_project_note,
    create_project_note,
    list_projects,
    get_project_info,
    update_project_state,
    add_task_to_project,
    delete_project,
    get_projects_dir,
)
from brainplorp.core.types import ProjectInfo, ProjectListResult


def test_parse_project_note_valid(tmp_path, monkeypatch):
    """Test parsing a valid project note with frontmatter."""
    # Setup: Create a project note
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()

    note_content = """---
domain: work
workstream: marketing
project_name: website-redesign
full_path: work.marketing.website-redesign
state: active
created_at: '2025-10-07T10:30:00'
description: Redesign company website
task_uuids:
  - abc-123
  - def-456
needs_review: false
tags:
  - project
  - work
  - marketing
---

# Website Redesign

## Overview
Project description goes here.
"""

    note_path = projects_dir / "work.marketing.website-redesign.md"
    note_path.write_text(note_content)

    # Test: Parse the note
    project = parse_project_note(note_path)

    # Assert: Check all fields
    assert project["domain"] == "work"
    assert project["workstream"] == "marketing"
    assert project["project_name"] == "website-redesign"
    assert project["full_path"] == "work.marketing.website-redesign"
    assert project["state"] == "active"
    assert project["created_at"] == "2025-10-07T10:30:00"
    assert project["description"] == "Redesign company website"
    assert project["task_uuids"] == ["abc-123", "def-456"]
    assert project["needs_review"] is False
    assert project["tags"] == ["project", "work", "marketing"]
    assert project["note_path"] == str(note_path)


def test_parse_project_note_missing_frontmatter(tmp_path):
    """Test parsing fails gracefully when frontmatter missing."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()

    note_content = "# Just a heading\n\nNo frontmatter here."
    note_path = projects_dir / "invalid.md"
    note_path.write_text(note_content)

    # Should raise ValueError
    with pytest.raises(ValueError, match="missing frontmatter"):
        parse_project_note(note_path)


def test_parse_project_note_missing_required_fields(tmp_path):
    """Test parsing fails when required fields missing."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()

    # Missing 'domain' and 'state'
    note_content = """---
project_name: test
full_path: test
---

# Test
"""

    note_path = projects_dir / "test.md"
    note_path.write_text(note_content)

    # Should raise KeyError
    with pytest.raises(KeyError):
        parse_project_note(note_path)


def test_create_project_note_3_segment(tmp_path, monkeypatch):
    """Test creating a 3-segment project note (domain.workstream.project)."""
    # Monkeypatch get_vault_path to use tmp_path
    monkeypatch.setattr("brainplorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Test: Create project
    project = create_project_note(
        domain="work",
        workstream="marketing",
        project_name="website-redesign",
        state="active",
        description="Redesign company website"
    )

    # Assert: Check returned ProjectInfo
    assert project["domain"] == "work"
    assert project["workstream"] == "marketing"
    assert project["project_name"] == "website-redesign"
    assert project["full_path"] == "work.marketing.website-redesign"
    assert project["state"] == "active"
    assert project["description"] == "Redesign company website"
    assert project["task_uuids"] == []
    assert project["needs_review"] is False
    assert project["tags"] == ["project", "work", "marketing"]

    # Assert: Check file was created
    note_path = tmp_path / "projects" / "work.marketing.website-redesign.md"
    assert note_path.exists()

    # Assert: Check file content
    content = note_path.read_text()
    assert "domain: work" in content
    assert "workstream: marketing" in content
    assert "# Website Redesign" in content


def test_create_project_note_2_segment(tmp_path, monkeypatch):
    """Test creating a 2-segment project (needs review)."""
    monkeypatch.setattr("brainplorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Test: Create project without workstream
    project = create_project_note(
        domain="work",
        workstream=None,
        project_name="quick-fix",
        state="active"
    )

    # Assert: Should be flagged for review
    assert project["full_path"] == "work.quick-fix"
    assert project["needs_review"] is True
    assert project["tags"] == ["project", "work"]

    # Assert: File created
    note_path = tmp_path / "projects" / "work.quick-fix.md"
    assert note_path.exists()


def test_create_project_note_invalid_domain(tmp_path, monkeypatch):
    """Test validation rejects invalid domain."""
    monkeypatch.setattr("brainplorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Should raise ValueError
    with pytest.raises(ValueError, match="Invalid domain"):
        create_project_note(
            domain="invalid",
            workstream=None,
            project_name="test"
        )


def test_create_project_note_already_exists(tmp_path, monkeypatch):
    """Test creating duplicate project fails."""
    monkeypatch.setattr("brainplorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Create first project
    create_project_note(
        domain="work",
        workstream="marketing",
        project_name="website"
    )

    # Try to create again - should fail
    with pytest.raises(ValueError, match="already exists"):
        create_project_note(
            domain="work",
            workstream="marketing",
            project_name="website"
        )


def test_list_projects_empty(tmp_path, monkeypatch):
    """Test listing projects when directory is empty."""
    monkeypatch.setattr("brainplorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Create empty projects directory
    (tmp_path / "projects").mkdir()

    # Test: List projects
    result = list_projects()

    # Assert: Should return empty result
    assert result["projects"] == []
    assert result["grouped_by_domain"] == {}


def test_list_projects_with_filters(tmp_path, monkeypatch):
    """Test filtering projects by domain and state."""
    monkeypatch.setattr("brainplorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Create multiple projects
    create_project_note("work", "marketing", "website", "active")
    create_project_note("work", "engineering", "api", "completed")
    create_project_note("home", "maintenance", "hvac", "planning")

    # Test: Filter by domain
    work_result = list_projects(domain="work")
    assert len(work_result["projects"]) == 2
    assert all(p["domain"] == "work" for p in work_result["projects"])

    # Test: Filter by state
    active_result = list_projects(state="active")
    assert len(active_result["projects"]) == 1
    assert active_result["projects"][0]["project_name"] == "website"

    # Test: Combined filters
    work_completed = list_projects(domain="work", state="completed")
    assert len(work_completed["projects"]) == 1
    assert work_completed["projects"][0]["project_name"] == "api"


def test_list_projects_grouped_by_domain(tmp_path, monkeypatch):
    """Test projects are grouped by domain."""
    monkeypatch.setattr("brainplorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Create projects in different domains
    create_project_note("work", "marketing", "website")
    create_project_note("work", "engineering", "api")
    create_project_note("home", "maintenance", "hvac")

    # Test: List all projects
    result = list_projects()

    # Assert: Check grouping
    assert "work" in result["grouped_by_domain"]
    assert "home" in result["grouped_by_domain"]
    assert len(result["grouped_by_domain"]["work"]) == 2
    assert len(result["grouped_by_domain"]["home"]) == 1


def test_get_project_info_exists(tmp_path, monkeypatch):
    """Test getting single project that exists."""
    monkeypatch.setattr("brainplorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Create project
    create_project_note("work", "marketing", "website")

    # Test: Get project
    project = get_project_info("work.marketing.website")

    # Assert: Returns correct project
    assert project is not None
    assert project["full_path"] == "work.marketing.website"
    assert project["domain"] == "work"


def test_get_project_info_not_found(tmp_path, monkeypatch):
    """Test getting project that doesn't exist returns None."""
    monkeypatch.setattr("brainplorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)
    (tmp_path / "projects").mkdir()

    # Test: Get non-existent project
    project = get_project_info("nonexistent.project")

    # Assert: Returns None
    assert project is None


def test_update_project_state(tmp_path, monkeypatch):
    """Test updating project state."""
    monkeypatch.setattr("brainplorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Create project
    create_project_note("work", "marketing", "website", state="planning")

    # Test: Update state
    updated = update_project_state("work.marketing.website", "active")

    # Assert: State changed
    assert updated["state"] == "active"

    # Assert: File updated
    project = get_project_info("work.marketing.website")
    assert project["state"] == "active"


def test_update_project_state_invalid_state(tmp_path, monkeypatch):
    """Test validation rejects invalid state."""
    monkeypatch.setattr("brainplorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    create_project_note("work", "marketing", "website")

    # Should raise ValueError
    with pytest.raises(ValueError, match="Invalid state"):
        update_project_state("work.marketing.website", "invalid_state")


def test_update_project_state_not_found(tmp_path, monkeypatch):
    """Test updating non-existent project fails."""
    monkeypatch.setattr("brainplorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)
    (tmp_path / "projects").mkdir()

    # Should raise ValueError
    with pytest.raises(ValueError, match="not found"):
        update_project_state("nonexistent.project", "active")


def test_add_task_to_project(tmp_path, monkeypatch):
    """Test adding task UUID to project."""
    monkeypatch.setattr("brainplorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Create project
    create_project_note("work", "marketing", "website")

    # Test: Add task
    updated = add_task_to_project("work.marketing.website", "abc-123")

    # Assert: UUID added
    assert "abc-123" in updated["task_uuids"]

    # Test: Add another task
    updated2 = add_task_to_project("work.marketing.website", "def-456")

    # Assert: Both UUIDs present
    assert "abc-123" in updated2["task_uuids"]
    assert "def-456" in updated2["task_uuids"]


def test_add_task_to_project_duplicate(tmp_path, monkeypatch):
    """Test adding same UUID twice doesn't duplicate."""
    monkeypatch.setattr("brainplorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    create_project_note("work", "marketing", "website")

    # Add task twice
    add_task_to_project("work.marketing.website", "abc-123")
    updated = add_task_to_project("work.marketing.website", "abc-123")

    # Assert: Only one instance
    assert updated["task_uuids"].count("abc-123") == 1


def test_delete_project(tmp_path, monkeypatch):
    """Test deleting project."""
    monkeypatch.setattr("brainplorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Create project
    create_project_note("work", "marketing", "website")
    note_path = tmp_path / "projects" / "work.marketing.website.md"
    assert note_path.exists()

    # Test: Delete project
    deleted = delete_project("work.marketing.website")

    # Assert: Returns True and file deleted
    assert deleted is True
    assert not note_path.exists()


def test_delete_project_not_found(tmp_path, monkeypatch):
    """Test deleting non-existent project returns False."""
    monkeypatch.setattr("brainplorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)
    (tmp_path / "projects").mkdir()

    # Test: Delete non-existent project
    deleted = delete_project("nonexistent.project")

    # Assert: Returns False
    assert deleted is False


def test_list_projects_skips_invalid_notes(tmp_path, monkeypatch, capsys):
    """Test that invalid notes are skipped with warning."""
    monkeypatch.setattr("brainplorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()

    # Create one valid project
    create_project_note("work", "marketing", "website")

    # Create invalid note (missing required fields)
    invalid_note = projects_dir / "invalid.md"
    invalid_note.write_text("---\nproject_name: test\n---\n# Test")

    # Test: List projects
    result = list_projects()

    # Assert: Only valid project returned
    assert len(result["projects"]) == 1
    assert result["projects"][0]["project_name"] == "website"

    # Assert: Warning printed
    captured = capsys.readouterr()
    assert "⚠️  Skipping invalid project note" in captured.out
    assert "invalid.md" in captured.out
