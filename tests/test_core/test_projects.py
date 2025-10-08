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
