# ABOUTME: Tests for core projects module - high-level project management operations
# ABOUTME: Tests project creation, task linking, and querying with TaskWarrior integration

import pytest
from unittest.mock import patch, MagicMock
from plorp.core.projects import (
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
from plorp.core.types import ProjectInfo, TaskInfo


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
    with patch("plorp.core.projects.create_task") as mock_create:
        with patch("plorp.core.projects.add_annotation") as mock_annotate:
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
    with patch("plorp.core.projects.create_task", return_value=None):
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

    with patch("plorp.core.projects.get_tasks", return_value=mock_tasks):
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

    with patch("plorp.core.projects.get_tasks", return_value=mock_tasks) as mock_get:
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

    with patch("plorp.core.projects.get_tasks", return_value=mock_tasks) as mock_get:
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
    from plorp.integrations.obsidian_bases import add_task_to_project as add_uuid
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

    with patch("plorp.core.projects.get_tasks", return_value=mock_tasks):
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
    with patch("plorp.core.projects.create_task") as mock_create:
        with patch("plorp.core.projects.add_annotation"):
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
    from plorp.core.projects import get_focused_domain_cli

    # Mock config dir to use tmp_path
    monkeypatch.setattr("plorp.core.projects.get_config_dir", lambda: tmp_path)

    # No focus file exists
    domain = get_focused_domain_cli()

    # Should default to 'home'
    assert domain == "home"


def test_cli_focus_set_and_get(tmp_path, monkeypatch):
    """Test setting and getting CLI focus."""
    from plorp.core.projects import get_focused_domain_cli, set_focused_domain_cli

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
    from plorp.core.projects import set_focused_domain_cli, get_focused_domain_cli

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
    from plorp.core.projects import get_focused_domain_mcp

    monkeypatch.setattr("plorp.core.projects.get_config_dir", lambda: tmp_path)

    # No focus file exists
    domain = get_focused_domain_mcp()

    assert domain == "home"


def test_mcp_focus_set_and_get(tmp_path, monkeypatch):
    """Test setting and getting MCP focus."""
    from plorp.core.projects import get_focused_domain_mcp, set_focused_domain_mcp

    monkeypatch.setattr("plorp.core.projects.get_config_dir", lambda: tmp_path)

    # Set focus to 'work'
    set_focused_domain_mcp("work")

    # Get focus
    domain = get_focused_domain_mcp()

    assert domain == "work"


def test_cli_and_mcp_focus_independent(tmp_path, monkeypatch):
    """Test CLI and MCP focus are stored separately."""
    from plorp.core.projects import (
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
    from plorp.core.projects import set_focused_domain_cli, get_focused_domain_cli
    import os

    # Set XDG_CONFIG_HOME
    xdg_dir = tmp_path / "xdg_config"
    xdg_dir.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_dir))

    # get_config_dir should now use XDG_CONFIG_HOME
    from plorp.config import get_config_dir
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
    from plorp.core.projects import create_project
    create_project(name="test-project", domain="work", workstream="test")

    # Mock TaskWarrior to return UUID
    with patch("plorp.core.projects.create_task") as mock_create:
        with patch("plorp.core.projects.add_annotation"):
            # Simulate successful task creation with valid UUID
            test_uuid = "a1b2c3d4-e5f6-7890-1234-567890abcdef"
            mock_create.return_value = test_uuid

            from plorp.core.projects import create_task_in_project

            # Create task in project
            uuid = create_task_in_project(
                description="Test task",
                project_full_path="work.test.test-project"
            )

            # Verify UUID returned and valid format
            assert uuid is not None
            assert len(uuid) == 36  # UUID format (with dashes)
            assert uuid == test_uuid
