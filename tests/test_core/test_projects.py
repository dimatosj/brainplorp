# ABOUTME: Tests for core projects module - high-level project management operations
# ABOUTME: Tests project creation, task linking, and querying with TaskWarrior integration

import pytest
from unittest.mock import patch, MagicMock
from brainplorp.core.projects import (
    create_project,
    list_projects,
    get_project_info,
    update_project_state,
    delete_project,
    create_task_in_project,
    list_project_tasks,
    list_tasks_by_domain,
    list_orphaned_tasks,
)
from brainplorp.core.types import ProjectInfo, TaskInfo


def test_create_project_valid(tmp_path, monkeypatch):
    """Test creating a project with valid parameters."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Test: Create project
    project = create_project(
        name="website-redesign",
        domain="work",
        workstream="marketing",
        state="active",
        description="Test project"
    )

    # Assert: Project created
    assert project["full_path"] == "work.marketing.website-redesign"
    assert project["domain"] == "work"
    assert project["workstream"] == "marketing"
    assert project["state"] == "active"


def test_create_project_invalid_domain(tmp_path, monkeypatch):
    """Test creating project with invalid domain fails."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Should raise ValueError
    with pytest.raises(ValueError, match="Invalid domain"):
        create_project(
            name="test",
            domain="invalid",
            workstream="marketing"
        )


def test_create_task_in_project_success(tmp_path, monkeypatch):
    """Test creating task and linking to project."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Create project first
    project = create_project(
        name="website",
        domain="work",
        workstream="marketing"
    )

    # Mock TaskWarrior integration
    with patch("brainplorp.core.projects.create_task") as mock_create:
        with patch("brainplorp.core.projects.add_annotation") as mock_annotate:
            mock_create.return_value = "abc-123"  # Mock UUID

            # Test: Create task in project
            task_uuid = create_task_in_project(
                description="Design homepage",
                project_full_path="work.marketing.website",
                due="friday",
                priority="H"
            )

            # Assert: Task created with correct parameters
            mock_create.assert_called_once_with(
                description="Design homepage",
                project="work.marketing.website",
                due="friday",
                priority="H",
                tags=None
            )

            # Assert: Task annotated
            mock_annotate.assert_called_once_with(
                "abc-123",
                "plorp-project:work.marketing.website"
            )

            # Assert: UUID returned
            assert task_uuid == "abc-123"

    # Assert: Project note updated with task UUID
    updated_project = get_project_info("work.marketing.website")
    assert "abc-123" in updated_project["task_uuids"]


def test_create_task_in_project_not_found(tmp_path, monkeypatch):
    """Test creating task in non-existent project fails."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)
    (tmp_path / "projects").mkdir()

    # Should raise ValueError
    with pytest.raises(ValueError, match="Project not found"):
        create_task_in_project(
            description="Test",
            project_full_path="nonexistent.project"
        )


def test_create_task_in_project_taskwarrior_fails(tmp_path, monkeypatch):
    """Test handling when TaskWarrior fails to create task."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    create_project(name="website", domain="work", workstream="marketing")

    # Mock TaskWarrior to return None (failure)
    with patch("brainplorp.core.projects.create_task", return_value=None):
        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="Failed to create task"):
            create_task_in_project(
                description="Test",
                project_full_path="work.marketing.website"
            )


def test_list_project_tasks(tmp_path, monkeypatch):
    """Test listing tasks for a project."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Mock TaskWarrior get_tasks
    mock_tasks = [
        {
            "uuid": "abc-123",
            "description": "Design homepage",
            "status": "pending",
            "project": "work.marketing.website",
            "due": "2025-10-10",
            "priority": "H",
            "tags": [],
            "urgency": 10.5
        },
        {
            "uuid": "def-456",
            "description": "Review mockups",
            "status": "pending",
            "project": "work.marketing.website",
            "priority": "M",
            "tags": [],
            "urgency": 5.2
        }
    ]

    with patch("brainplorp.core.projects.get_tasks", return_value=mock_tasks):
        # Test: List tasks
        tasks = list_project_tasks("work.marketing.website")

        # Assert: Correct tasks returned
        assert len(tasks) == 2
        assert tasks[0]["uuid"] == "abc-123"
        assert tasks[0]["description"] == "Design homepage"
        assert tasks[0]["urgency"] == 10.5
        assert tasks[1]["uuid"] == "def-456"


def test_list_tasks_by_domain(tmp_path, monkeypatch):
    """Test listing all tasks in a domain."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Mock TaskWarrior get_tasks
    mock_tasks = [
        {
            "uuid": "abc-123",
            "description": "Work task 1",
            "status": "pending",
            "project": "work.marketing.website",
            "tags": [],
            "urgency": 5.0
        },
        {
            "uuid": "def-456",
            "description": "Work task 2",
            "status": "pending",
            "project": "work.engineering.api",
            "tags": [],
            "urgency": 3.0
        }
    ]

    with patch("brainplorp.core.projects.get_tasks", return_value=mock_tasks) as mock_get:
        # Test: List tasks in domain
        tasks = list_tasks_by_domain("work")

        # Assert: Called with correct filter
        mock_get.assert_called_once_with(["project.startswith:work"])

        # Assert: Tasks returned
        assert len(tasks) == 2
        assert tasks[0]["description"] == "Work task 1"


def test_list_orphaned_tasks():
    """Test listing tasks with no project."""
    # Mock TaskWarrior get_tasks
    mock_tasks = [
        {
            "uuid": "abc-123",
            "description": "Orphaned task",
            "status": "pending",
            "tags": [],
            "urgency": 2.0
        }
    ]

    with patch("brainplorp.core.projects.get_tasks", return_value=mock_tasks) as mock_get:
        # Test: List orphaned tasks
        tasks = list_orphaned_tasks()

        # Assert: Called with correct filter
        mock_get.assert_called_once_with(["project.none:"])

        # Assert: Task returned
        assert len(tasks) == 1
        assert tasks[0]["uuid"] == "abc-123"
        assert tasks[0]["project"] is None


def test_list_project_tasks_with_orphan_warning(tmp_path, monkeypatch, capsys):
    """Test warning when project has orphaned task references."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Create project with task UUIDs
    project = create_project(name="website", domain="work", workstream="marketing")

    # Manually add task UUIDs to project (simulating tasks that were deleted)
    from brainplorp.integrations.obsidian_bases import add_task_to_project as add_uuid
    add_uuid("work.marketing.website", "abc-123")
    add_uuid("work.marketing.website", "def-456")
    add_uuid("work.marketing.website", "ghi-789")

    # Mock TaskWarrior returning only 1 task (2 are missing)
    mock_tasks = [
        {
            "uuid": "abc-123",
            "description": "Still exists",
            "status": "pending",
            "project": "work.marketing.website",
            "tags": [],
            "urgency": 5.0
        }
    ]

    with patch("brainplorp.core.projects.get_tasks", return_value=mock_tasks):
        # Test: List project tasks
        tasks = list_project_tasks("work.marketing.website")

        # Assert: Warning printed
        captured = capsys.readouterr()
        assert "⚠️" in captured.out
        assert "3 task references" in captured.out
        assert "only 1 found" in captured.out
        assert "plorp project sync" in captured.out

        # Assert: Still returns found tasks
        assert len(tasks) == 1


def test_integration_create_project_and_tasks(tmp_path, monkeypatch):
    """Integration test: Create project and add multiple tasks."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Create project
    project = create_project(
        name="api-rewrite",
        domain="work",
        workstream="engineering",
        description="Rewrite API in Rust"
    )

    assert project["full_path"] == "work.engineering.api-rewrite"

    # Mock TaskWarrior for task creation
    with patch("brainplorp.core.projects.create_task") as mock_create:
        with patch("brainplorp.core.projects.add_annotation"):
            mock_create.side_effect = ["task-1", "task-2", "task-3"]

            # Add multiple tasks
            uuid1 = create_task_in_project("Setup project", "work.engineering.api-rewrite")
            uuid2 = create_task_in_project("Write tests", "work.engineering.api-rewrite")
            uuid3 = create_task_in_project("Implement endpoints", "work.engineering.api-rewrite")

    # Verify all tasks added to project
    updated_project = get_project_info("work.engineering.api-rewrite")
    assert len(updated_project["task_uuids"]) == 3
    assert "task-1" in updated_project["task_uuids"]
    assert "task-2" in updated_project["task_uuids"]
    assert "task-3" in updated_project["task_uuids"]


def test_list_projects_wrapper(tmp_path, monkeypatch):
    """Test list_projects wrapper function."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Create multiple projects
    create_project("website", "work", "marketing")
    create_project("api", "work", "engineering")
    create_project("hvac", "home", "maintenance")

    # Test: List all projects
    result = list_projects()
    assert len(result["projects"]) == 3

    # Test: Filter by domain
    work_result = list_projects(domain="work")
    assert len(work_result["projects"]) == 2
    assert all(p["domain"] == "work" for p in work_result["projects"])

    # Test: Filter by state
    result_all = create_project("test", "work", "admin", state="planning")
    planning_result = list_projects(state="planning")
    assert len(planning_result["projects"]) == 1


# ============================================================================
# Domain Focus Tests
# ============================================================================


def test_cli_focus_default(tmp_path, monkeypatch):
    """Test CLI focus defaults to 'home'."""
    from brainplorp.core.projects import get_focused_domain_cli

    # Mock config dir to use tmp_path
    monkeypatch.setattr("plorp.core.projects.get_config_dir", lambda: tmp_path)

    # No focus file exists
    domain = get_focused_domain_cli()

    # Should default to 'home'
    assert domain == "home"


def test_cli_focus_set_and_get(tmp_path, monkeypatch):
    """Test setting and getting CLI focus."""
    from brainplorp.core.projects import get_focused_domain_cli, set_focused_domain_cli

    monkeypatch.setattr("plorp.core.projects.get_config_dir", lambda: tmp_path)

    # Set focus to 'work'
    set_focused_domain_cli("work")

    # Get focus
    domain = get_focused_domain_cli()

    assert domain == "work"

    # Change focus
    set_focused_domain_cli("personal")

    domain = get_focused_domain_cli()
    assert domain == "personal"


def test_cli_focus_persists_across_calls(tmp_path, monkeypatch):
    """Test CLI focus persists in file."""
    from brainplorp.core.projects import set_focused_domain_cli, get_focused_domain_cli

    monkeypatch.setattr("plorp.core.projects.get_config_dir", lambda: tmp_path)

    # Set focus
    set_focused_domain_cli("work")

    # Verify file created
    focus_file = tmp_path / "cli_focus.txt"
    assert focus_file.exists()
    assert focus_file.read_text() == "work"

    # Get focus (reads from file)
    domain = get_focused_domain_cli()
    assert domain == "work"


def test_mcp_focus_default(tmp_path, monkeypatch):
    """Test MCP focus defaults to 'home'."""
    from brainplorp.core.projects import get_focused_domain_mcp

    monkeypatch.setattr("plorp.core.projects.get_config_dir", lambda: tmp_path)

    # No focus file exists
    domain = get_focused_domain_mcp()

    assert domain == "home"


def test_mcp_focus_set_and_get(tmp_path, monkeypatch):
    """Test setting and getting MCP focus."""
    from brainplorp.core.projects import get_focused_domain_mcp, set_focused_domain_mcp

    monkeypatch.setattr("plorp.core.projects.get_config_dir", lambda: tmp_path)

    # Set focus to 'work'
    set_focused_domain_mcp("work")

    # Get focus
    domain = get_focused_domain_mcp()

    assert domain == "work"


def test_cli_and_mcp_focus_independent(tmp_path, monkeypatch):
    """Test CLI and MCP focus are stored separately."""
    from brainplorp.core.projects import (
        set_focused_domain_cli,
        set_focused_domain_mcp,
        get_focused_domain_cli,
        get_focused_domain_mcp,
    )

    monkeypatch.setattr("plorp.core.projects.get_config_dir", lambda: tmp_path)

    # Set different focus for CLI and MCP
    set_focused_domain_cli("work")
    set_focused_domain_mcp("home")

    # Verify they're independent
    assert get_focused_domain_cli() == "work"
    assert get_focused_domain_mcp() == "home"

    # Verify separate files
    assert (tmp_path / "cli_focus.txt").read_text() == "work"
    assert (tmp_path / "mcp_focus.txt").read_text() == "home"


def test_focus_respects_xdg_config_home(tmp_path, monkeypatch):
    """Test focus files respect XDG_CONFIG_HOME."""
    from brainplorp.core.projects import set_focused_domain_cli, get_focused_domain_cli
    import os

    # Set XDG_CONFIG_HOME
    xdg_dir = tmp_path / "xdg_config"
    xdg_dir.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_dir))

    # get_config_dir should now use XDG_CONFIG_HOME
    from brainplorp.config import get_config_dir
    config_dir = get_config_dir()
    assert str(xdg_dir / "plorp") == str(config_dir)

    # Set focus (should use XDG path)
    set_focused_domain_cli("work")

    # Verify file in XDG location
    focus_file = xdg_dir / "plorp" / "cli_focus.txt"
    assert focus_file.exists()
    assert focus_file.read_text() == "work"


# Regression test for Bug #1: Race condition in task creation
def test_create_task_in_project_returns_uuid(tmp_path, monkeypatch):
    """Ensure project task creation returns valid UUID.

    Regression test for Bug #1: Verifies that create_task_in_project
    returns a valid UUID even with the race condition fix.
    """
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Create project
    from brainplorp.core.projects import create_project
    create_project(name="test-project", domain="work", workstream="test")

    # Mock TaskWarrior to return UUID
    with patch("brainplorp.core.projects.create_task") as mock_create:
        with patch("brainplorp.core.projects.add_annotation"):
            # Simulate successful task creation with valid UUID
            test_uuid = "a1b2c3d4-e5f6-7890-1234-567890abcdef"
            mock_create.return_value = test_uuid

            from brainplorp.core.projects import create_task_in_project

            # Create task in project
            uuid = create_task_in_project(
                description="Test task",
                project_full_path="work.test.test-project"
            )

            # Verify UUID returned and valid format
            assert uuid is not None
            assert len(uuid) == 36  # UUID format (with dashes)
            assert uuid == test_uuid


# ============================================================================
# Sprint 8.5: Auto-Sync Tests (Item 1)
# ============================================================================


def test_remove_task_from_all_projects_single_project(tmp_path, monkeypatch):
    """Test removing task UUID from single project frontmatter."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Create project with tasks
    create_project(name="website", domain="work", workstream="marketing")

    # Add task UUIDs to project
    from brainplorp.integrations.obsidian_bases import add_task_to_project
    add_task_to_project("work.marketing.website", "task-1")
    add_task_to_project("work.marketing.website", "task-2")
    add_task_to_project("work.marketing.website", "task-3")

    # Verify UUIDs added
    project = get_project_info("work.marketing.website")
    assert len(project["task_uuids"]) == 3
    assert "task-2" in project["task_uuids"]

    # Test: Remove task-2 from all projects
    from brainplorp.core.projects import remove_task_from_all_projects
    remove_task_from_all_projects(tmp_path, "task-2")

    # Assert: task-2 removed, others remain
    project = get_project_info("work.marketing.website")
    assert len(project["task_uuids"]) == 2
    assert "task-1" in project["task_uuids"]
    assert "task-3" in project["task_uuids"]
    assert "task-2" not in project["task_uuids"]


def test_remove_task_from_all_projects_multiple_projects(tmp_path, monkeypatch):
    """Test removing task UUID from multiple projects (cleanup orphaned refs)."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Create multiple projects
    create_project(name="website", domain="work", workstream="marketing")
    create_project(name="api", domain="work", workstream="engineering")
    create_project(name="garden", domain="home", workstream="maintenance")

    # Add same UUID to multiple projects (shouldn't happen, but test data integrity fix per Q4)
    from brainplorp.integrations.obsidian_bases import add_task_to_project
    add_task_to_project("work.marketing.website", "orphaned-uuid")
    add_task_to_project("work.engineering.api", "orphaned-uuid")
    add_task_to_project("work.marketing.website", "task-1")
    add_task_to_project("home.maintenance.garden", "orphaned-uuid")

    # Verify UUID in all projects
    assert "orphaned-uuid" in get_project_info("work.marketing.website")["task_uuids"]
    assert "orphaned-uuid" in get_project_info("work.engineering.api")["task_uuids"]
    assert "orphaned-uuid" in get_project_info("home.maintenance.garden")["task_uuids"]

    # Test: Remove orphaned UUID from ALL projects
    from brainplorp.core.projects import remove_task_from_all_projects
    remove_task_from_all_projects(tmp_path, "orphaned-uuid")

    # Assert: UUID removed from ALL projects (per Q4 answer)
    assert "orphaned-uuid" not in get_project_info("work.marketing.website")["task_uuids"]
    assert "orphaned-uuid" not in get_project_info("work.engineering.api")["task_uuids"]
    assert "orphaned-uuid" not in get_project_info("home.maintenance.garden")["task_uuids"]

    # Assert: Other UUIDs preserved
    assert "task-1" in get_project_info("work.marketing.website")["task_uuids"]


def test_remove_task_from_all_projects_no_projects(tmp_path, monkeypatch):
    """Test removing task UUID when no projects exist (graceful handling)."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # No projects created, but projects directory exists
    (tmp_path / "projects").mkdir()

    # Test: Should not raise error
    from brainplorp.core.projects import remove_task_from_all_projects
    remove_task_from_all_projects(tmp_path, "nonexistent-uuid")

    # Assert: No error raised (graceful handling)


def test_remove_task_from_all_projects_uuid_not_found(tmp_path, monkeypatch):
    """Test removing task UUID that doesn't exist in any project."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Create project with different UUIDs
    create_project(name="website", domain="work", workstream="marketing")
    from brainplorp.integrations.obsidian_bases import add_task_to_project
    add_task_to_project("work.marketing.website", "task-1")
    add_task_to_project("work.marketing.website", "task-2")

    # Test: Remove UUID that doesn't exist
    from brainplorp.core.projects import remove_task_from_all_projects
    remove_task_from_all_projects(tmp_path, "nonexistent-uuid")

    # Assert: Project unchanged
    project = get_project_info("work.marketing.website")
    assert len(project["task_uuids"]) == 2
    assert "task-1" in project["task_uuids"]
    assert "task-2" in project["task_uuids"]


# ============================================================================
# Sprint 8.5: Workstream Validation (Item 3)
# ============================================================================


def test_validate_workstream_returns_warning_for_unknown():
    """Test that validation warns about non-standard workstreams (Sprint 8.5 Item 3)."""
    from brainplorp.core.projects import validate_workstream

    # Test: Unknown workstream for 'work' domain
    warning = validate_workstream("work", "foobar")

    # Assert: Warning message returned
    assert warning is not None
    assert "foobar" in warning
    assert "work" in warning


def test_validate_workstream_passes_for_known():
    """Test that validation passes for standard workstreams."""
    from brainplorp.core.projects import validate_workstream

    # Test: Known workstreams for each domain
    assert validate_workstream("work", "engineering") is None
    assert validate_workstream("work", "marketing") is None
    assert validate_workstream("home", "maintenance") is None
    assert validate_workstream("personal", "learning") is None


def test_validate_workstream_handles_unknown_domain():
    """Test that validation passes for unknown domains (no validation rules)."""
    from brainplorp.core.projects import validate_workstream

    # Test: Unknown domain with any workstream
    warning = validate_workstream("custom-domain", "any-workstream")

    # Assert: No warning (no validation for unknown domains)
    assert warning is None


# ============================================================================
# Sprint 8.5: Orphaned Project Review (Item 4)
# ============================================================================


def test_find_orphaned_projects(tmp_path, monkeypatch):
    """Test finding projects with needs_review flag (Sprint 8.5 Item 4)."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)
    from brainplorp.core.projects import find_orphaned_projects

    # Create projects - 2 with needs_review, 1 without
    create_project("api", "work")  # 2-segment, needs_review=true
    create_project("website", "work", "marketing")  # 3-segment, needs_review=false
    create_project("garden", "home")  # 2-segment, needs_review=true

    # Test: Find orphaned projects
    orphaned = find_orphaned_projects(tmp_path)

    # Assert: Found 2 orphaned projects
    assert len(orphaned) == 2
    full_paths = [p["full_path"] for p in orphaned]
    assert "work.api" in full_paths
    assert "home.garden" in full_paths
    assert "work.marketing.website" not in full_paths  # Has workstream


def test_rename_project(tmp_path, monkeypatch):
    """Test renaming project file and updating frontmatter (Sprint 8.5 Item 4)."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)
    from brainplorp.core.projects import rename_project

    # Create 2-segment project
    create_project("api", "work", description="API rewrite project")

    # Test: Rename to 3-segment
    result = rename_project(tmp_path, "work.api", "work.engineering.api")

    # Assert: Old file removed, new file created
    old_file = tmp_path / "projects" / "work.api.md"
    new_file = tmp_path / "projects" / "work.engineering.api.md"
    assert not old_file.exists()
    assert new_file.exists()

    # Assert: Frontmatter updated
    assert result["full_path"] == "work.engineering.api"
    assert result["workstream"] == "engineering"
    assert result["needs_review"] is False  # Flag removed
    assert result["description"] == "API rewrite project"  # Preserved


def test_rename_project_preserves_task_uuids(tmp_path, monkeypatch):
    """Test that rename preserves task UUIDs and updates TaskWarrior (Sprint 8.5 Item 4)."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)
    from brainplorp.core.projects import rename_project

    # Create project with tasks
    create_project("api", "work")
    from brainplorp.integrations.obsidian_bases import add_task_to_project
    add_task_to_project("work.api", "task-1")
    add_task_to_project("work.api", "task-2")

    # Mock TaskWarrior modify and annotate
    from unittest.mock import patch
    with patch("brainplorp.integrations.taskwarrior.modify_task") as mock_modify, \
         patch("plorp.integrations.taskwarrior.add_annotation") as mock_annotate:

        # Test: Rename project
        result = rename_project(tmp_path, "work.api", "work.engineering.api")

        # Assert: Task UUIDs preserved
        assert len(result["task_uuids"]) == 2
        assert "task-1" in result["task_uuids"]
        assert "task-2" in result["task_uuids"]

        # Assert: TaskWarrior updated for both tasks (State Sync per Q8)
        assert mock_modify.call_count == 2
        assert mock_annotate.call_count == 2


# ============================================================================
# Sprint 8.5: Orphaned Task Review (Item 5)
# ============================================================================


def test_assign_orphaned_task_to_project(tmp_path, monkeypatch):
    """Test assigning orphaned task to project with State Sync (Sprint 8.5 Item 5)."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)
    from brainplorp.core.projects import assign_task_to_project

    # Create project
    create_project("website", "work", "marketing")

    # Mock TaskWarrior
    from unittest.mock import patch
    with patch("brainplorp.integrations.taskwarrior.modify_task") as mock_modify, \
         patch("plorp.integrations.taskwarrior.add_annotation") as mock_annotate:

        # Test: Assign orphaned task to project
        assign_task_to_project("orphan-uuid-123", "work.marketing.website", tmp_path)

        # Assert: TaskWarrior updated (State Sync per Q9)
        mock_modify.assert_called_once_with("orphan-uuid-123", project="work.marketing.website")
        mock_annotate.assert_called_once()

        # Assert: Obsidian updated (State Sync)
        project = get_project_info("work.marketing.website")
        assert "orphan-uuid-123" in project["task_uuids"]


def test_assign_orphaned_task_to_project_not_found(tmp_path, monkeypatch):
    """Test assigning task to non-existent project raises error."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)
    from brainplorp.core.projects import assign_task_to_project

    # Test: Should raise ValueError
    with pytest.raises(ValueError, match="Project not found"):
        assign_task_to_project("uuid-123", "nonexistent.project", tmp_path)


# ============================================================================
# Sprint 8.6: Auto-Sync Infrastructure Tests
# ============================================================================


def test_sync_project_task_section_creates_section(tmp_path, monkeypatch):
    """Test that sync creates Tasks section when none exists (Sprint 8.6)."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)
    from brainplorp.core.projects import _sync_project_task_section

    # Create project
    create_project("website", "work", "marketing", description="Test project")

    # Add task UUID to project frontmatter
    from brainplorp.integrations.obsidian_bases import add_task_to_project
    add_task_to_project("work.marketing.website", "task-1")

    # Mock TaskWarrior to return task details
    with patch("brainplorp.integrations.taskwarrior.get_task_info") as mock_get_task:
        mock_get_task.return_value = {
            "uuid": "task-1",
            "description": "Design homepage",
            "status": "pending",
            "due": "20251010T000000Z",
            "priority": "H"
        }

        # Test: Sync project task section
        _sync_project_task_section(tmp_path, "work.marketing.website")

        # Assert: Tasks section created in note body
        note_path = tmp_path / "projects" / "work.marketing.website.md"
        content = note_path.read_text()

        assert "## Tasks (1)" in content
        assert "- [ ] Design homepage" in content
        assert "due: 2025-10-10" in content
        assert "priority: H" in content
        assert "uuid: task-1" in content


def test_sync_project_task_section_updates_existing(tmp_path, monkeypatch):
    """Test that sync replaces old Tasks section (Sprint 8.6)."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)
    from brainplorp.core.projects import _sync_project_task_section

    # Create project with existing Tasks section
    create_project("website", "work", "marketing")

    # Manually add old Tasks section
    note_path = tmp_path / "projects" / "work.marketing.website.md"
    content = note_path.read_text()
    content += "\n## Tasks (0)\n\nNo tasks\n"
    note_path.write_text(content)

    # Add task to frontmatter
    from brainplorp.integrations.obsidian_bases import add_task_to_project
    add_task_to_project("work.marketing.website", "task-new")

    # Mock TaskWarrior
    with patch("brainplorp.integrations.taskwarrior.get_task_info") as mock_get_task:
        mock_get_task.return_value = {
            "uuid": "task-new",
            "description": "New task",
            "status": "pending"
        }

        # Test: Sync should replace old section
        _sync_project_task_section(tmp_path, "work.marketing.website")

        # Assert: Old section gone, new section present
        updated_content = note_path.read_text()
        assert updated_content.count("## Tasks") == 1  # Only one Tasks section
        assert "No tasks" not in updated_content
        assert "New task" in updated_content


def test_sync_project_task_section_preserves_content(tmp_path, monkeypatch):
    """Test that sync preserves other sections and content (Sprint 8.6)."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)
    from brainplorp.core.projects import _sync_project_task_section

    # Create project
    create_project("website", "work", "marketing", description="Test")

    # Add other sections to note
    note_path = tmp_path / "projects" / "work.marketing.website.md"
    content = note_path.read_text()
    content += "\n## Notes\n\nImportant user notes here\n\n## Resources\n\n- Link 1\n- Link 2\n"
    note_path.write_text(content)

    # Add task
    from brainplorp.integrations.obsidian_bases import add_task_to_project
    add_task_to_project("work.marketing.website", "task-1")

    with patch("brainplorp.integrations.taskwarrior.get_task_info") as mock_get_task:
        mock_get_task.return_value = {
            "uuid": "task-1",
            "description": "Test task",
            "status": "pending"
        }

        # Test: Sync
        _sync_project_task_section(tmp_path, "work.marketing.website")

        # Assert: Other sections preserved
        updated_content = note_path.read_text()
        assert "## Notes" in updated_content
        assert "Important user notes here" in updated_content
        assert "## Resources" in updated_content
        assert "- Link 1" in updated_content


def test_sync_project_task_section_handles_empty(tmp_path, monkeypatch):
    """Test sync with no tasks removes Tasks section (Sprint 8.6)."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)
    from brainplorp.core.projects import _sync_project_task_section

    # Create project with existing Tasks section but no task UUIDs
    create_project("website", "work", "marketing")
    note_path = tmp_path / "projects" / "work.marketing.website.md"
    content = note_path.read_text()
    content += "\n## Tasks (1)\n\n- [ ] Old task\n"
    note_path.write_text(content)

    # Test: Sync with empty task_uuids
    _sync_project_task_section(tmp_path, "work.marketing.website")

    # Assert: Tasks section removed (no pending tasks)
    updated_content = note_path.read_text()
    assert "## Tasks" not in updated_content
    assert "Old task" not in updated_content


def test_sync_project_task_section_skips_orphaned(tmp_path, monkeypatch):
    """Test sync gracefully skips orphaned UUIDs (Sprint 8.6)."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)
    from brainplorp.core.projects import _sync_project_task_section

    # Create project with orphaned UUID
    create_project("website", "work", "marketing")
    from brainplorp.integrations.obsidian_bases import add_task_to_project
    add_task_to_project("work.marketing.website", "orphaned-uuid")
    add_task_to_project("work.marketing.website", "valid-uuid")

    # Mock TaskWarrior - orphaned returns None, valid returns task
    with patch("brainplorp.integrations.taskwarrior.get_task_info") as mock_get_task:
        def side_effect(uuid):
            if uuid == "orphaned-uuid":
                from brainplorp.core.exceptions import TaskNotFoundError
                raise TaskNotFoundError(uuid)
            return {
                "uuid": "valid-uuid",
                "description": "Valid task",
                "status": "pending"
            }

        mock_get_task.side_effect = side_effect

        # Test: Sync should skip orphaned, include valid
        _sync_project_task_section(tmp_path, "work.marketing.website")

        # Assert: Only valid task in Tasks section
        note_path = tmp_path / "projects" / "work.marketing.website.md"
        content = note_path.read_text()

        assert "## Tasks (1)" in content
        assert "Valid task" in content
        # Orphaned UUID remains in frontmatter (Sprint 8.5 reconciliation will clean)
        # but is NOT rendered in the Tasks section body
        tasks_section = content.split("## Tasks")[1].split("##")[0] if "## Tasks" in content else ""
        assert "orphaned-uuid" not in tasks_section  # Not in Tasks section
        assert "valid-uuid" in tasks_section  # Valid task IS in Tasks section


def test_sync_project_task_section_formats_correctly(tmp_path, monkeypatch):
    """Test sync formats task lines correctly (Sprint 8.6)."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)
    from brainplorp.core.projects import _sync_project_task_section

    # Create project with task
    create_project("website", "work", "marketing")
    from brainplorp.integrations.obsidian_bases import add_task_to_project
    add_task_to_project("work.marketing.website", "task-1")

    with patch("brainplorp.integrations.taskwarrior.get_task_info") as mock_get_task:
        # Task with all metadata fields
        mock_get_task.return_value = {
            "uuid": "task-1",
            "description": "Complete design",
            "status": "pending",
            "due": "20251015T120000Z",
            "priority": "M"
        }

        _sync_project_task_section(tmp_path, "work.marketing.website")

        note_path = tmp_path / "projects" / "work.marketing.website.md"
        content = note_path.read_text()

        # Assert: Correct format (due, priority, uuid order per Q14)
        assert "- [ ] Complete design (due: 2025-10-15, priority: M, uuid: task-1)" in content


def test_sync_project_task_section_project_not_found(tmp_path):
    """Test sync raises error for non-existent project (Sprint 8.6)."""
    from brainplorp.core.projects import _sync_project_task_section
    from brainplorp.core.exceptions import ProjectNotFoundError

    # Test: Should raise ProjectNotFoundError
    with pytest.raises(ProjectNotFoundError, match="Project not found"):
        _sync_project_task_section(tmp_path, "nonexistent.project")


# ============================================================================
# Sprint 8.6: Checkbox Processing for Project Notes
# ============================================================================


def test_process_project_note_marks_tasks_done(tmp_path, monkeypatch):
    """Test processing project note marks checked tasks as done (Sprint 8.6)."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)
    from brainplorp.core.projects import process_project_note

    # Create project with task
    create_project("website", "work", "marketing")
    from brainplorp.integrations.obsidian_bases import add_task_to_project
    add_task_to_project("work.marketing.website", "task-1")

    # Manually add checked task to Tasks section
    note_path = tmp_path / "projects" / "work.marketing.website.md"
    content = note_path.read_text()
    content += "\n## Tasks (1)\n\n- [x] Complete task (uuid: task-1)\n"
    note_path.write_text(content)

    # Mock TaskWarrior
    with patch("brainplorp.integrations.taskwarrior.mark_done") as mock_done:
        # Test: Process project note
        process_project_note(tmp_path, "work.marketing.website")

        # Assert: Task marked done in TaskWarrior
        mock_done.assert_called_once_with("task-1")


def test_process_project_note_syncs_after_marking_done(tmp_path, monkeypatch):
    """Test processing syncs note body after marking tasks done (Sprint 8.6)."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)
    from brainplorp.core.projects import process_project_note

    # Create project with task
    create_project("website", "work", "marketing")
    from brainplorp.integrations.obsidian_bases import add_task_to_project
    add_task_to_project("work.marketing.website", "task-1")

    # Add checked task to Tasks section
    note_path = tmp_path / "projects" / "work.marketing.website.md"
    content = note_path.read_text()
    content += "\n## Tasks (1)\n\n- [x] Complete task (uuid: task-1)\n"
    note_path.write_text(content)

    # Mock TaskWarrior
    with patch("brainplorp.integrations.taskwarrior.mark_done") as mock_done, \
         patch("plorp.integrations.taskwarrior.get_task_info") as mock_get:

        # After marking done, task status changes to completed
        mock_get.return_value = {
            "uuid": "task-1",
            "description": "Complete task",
            "status": "completed"  # Now completed
        }

        # Test: Process
        process_project_note(tmp_path, "work.marketing.website")

        # Assert: Note body synced (completed tasks removed from Tasks section per Q1)
        updated_content = note_path.read_text()
        # Completed task should not be in Tasks section anymore
        if "## Tasks" in updated_content:
            tasks_section = updated_content.split("## Tasks")[1].split("##")[0] if "## Tasks" in updated_content else ""
            assert "task-1" not in tasks_section


def test_process_project_note_removes_from_frontmatter(tmp_path, monkeypatch):
    """Test processing removes completed task UUIDs from frontmatter (Sprint 8.6)."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)
    from brainplorp.core.projects import process_project_note, get_project_info

    # Create project with task
    create_project("website", "work", "marketing")
    from brainplorp.integrations.obsidian_bases import add_task_to_project
    add_task_to_project("work.marketing.website", "task-1")

    # Add checked task
    note_path = tmp_path / "projects" / "work.marketing.website.md"
    content = note_path.read_text()
    content += "\n## Tasks (1)\n\n- [x] Complete task (uuid: task-1)\n"
    note_path.write_text(content)

    # Mock TaskWarrior
    with patch("brainplorp.integrations.taskwarrior.mark_done"):
        # Test: Process
        process_project_note(tmp_path, "work.marketing.website")

        # Assert: UUID removed from frontmatter (State Sync)
        project = get_project_info("work.marketing.website")
        assert "task-1" not in project["task_uuids"]


def test_process_project_note_handles_no_checkboxes(tmp_path, monkeypatch):
    """Test processing with no checked tasks does nothing (Sprint 8.6)."""
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)
    from brainplorp.core.projects import process_project_note

    # Create project with unchecked task
    create_project("website", "work", "marketing")
    from brainplorp.integrations.obsidian_bases import add_task_to_project
    add_task_to_project("work.marketing.website", "task-1")

    # Add UNchecked task
    note_path = tmp_path / "projects" / "work.marketing.website.md"
    content = note_path.read_text()
    content += "\n## Tasks (1)\n\n- [ ] Pending task (uuid: task-1)\n"
    note_path.write_text(content)

    # Mock TaskWarrior
    with patch("brainplorp.integrations.taskwarrior.mark_done") as mock_done:
        # Test: Process
        process_project_note(tmp_path, "work.marketing.website")

        # Assert: mark_done not called (no checked tasks)
        mock_done.assert_not_called()
