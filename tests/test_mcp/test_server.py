"""
Tests for plorp.mcp.server module.

Tests MCP server tool implementations.
"""

import pytest
import json
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Import server components
from plorp.mcp.server import (
    _plorp_start_day,
    _plorp_get_review_tasks,
    _plorp_add_review_notes,
    _plorp_mark_task_completed,
    _plorp_defer_task,
    _plorp_drop_task,
    _plorp_set_task_priority,
    _plorp_get_inbox_items,
    _plorp_create_task_from_inbox,
    _plorp_create_note_from_inbox,
    _plorp_create_both_from_inbox,
    _plorp_discard_inbox_item,
    _plorp_create_note,
    _plorp_create_note_with_task,
    _plorp_link_note_to_task,
    _plorp_get_task_info,
    _plorp_process_daily_note,
    call_tool,
)
from plorp.core.exceptions import TaskNotFoundError


@pytest.mark.asyncio
async def test_plorp_start_day():
    """Test plorp_start_day tool."""
    with patch("plorp.mcp.server.start_day") as mock_start:
        with patch("plorp.mcp.server._get_vault_path") as mock_vault:
            mock_vault.return_value = Path("/vault")
            mock_start.return_value = {
                "note_path": "/vault/daily/2025-10-06.md",
                "date": "2025-10-06",
                "summary": {"total_count": 1},
                "tasks": [],
                "created_at": "2025-10-06T09:00:00",
            }

            result = await _plorp_start_day({"date": "2025-10-06"})

            assert len(result) == 1
            assert result[0].type == "text"
            data = json.loads(result[0].text)
            assert data["date"] == "2025-10-06"
            assert data["summary"]["total_count"] == 1


@pytest.mark.asyncio
async def test_plorp_get_review_tasks():
    """Test plorp_get_review_tasks tool."""
    with patch("plorp.mcp.server.get_review_tasks") as mock_review:
        with patch("plorp.mcp.server._get_vault_path") as mock_vault:
            mock_vault.return_value = Path("/vault")
            mock_review.return_value = {
                "date": "2025-10-06",
                "daily_note_path": "/vault/daily/2025-10-06.md",
                "uncompleted_tasks": [],
                "total_tasks": 5,
                "uncompleted_count": 0,
            }

            result = await _plorp_get_review_tasks({"date": "2025-10-06"})

            data = json.loads(result[0].text)
            assert data["uncompleted_count"] == 0
            assert data["total_tasks"] == 5


@pytest.mark.asyncio
async def test_plorp_add_review_notes():
    """Test plorp_add_review_notes tool."""
    with patch("plorp.mcp.server.add_review_notes") as mock_add:
        with patch("plorp.mcp.server._get_vault_path") as mock_vault:
            mock_vault.return_value = Path("/vault")
            mock_add.return_value = {
                "daily_note_path": "/vault/daily/2025-10-06.md",
                "review_added_at": "2025-10-06 17:00",
                "reflections": {"went_well": "Good day"},
            }

            result = await _plorp_add_review_notes(
                {
                    "date": "2025-10-06",
                    "went_well": "Good day",
                    "could_improve": "",
                    "tomorrow": "",
                }
            )

            data = json.loads(result[0].text)
            assert data["reflections"]["went_well"] == "Good day"


@pytest.mark.asyncio
async def test_plorp_mark_task_completed():
    """Test plorp_mark_task_completed tool."""
    with patch("plorp.mcp.server.mark_completed") as mock_mark:
        mock_mark.return_value = {
            "uuid": "abc-123",
            "description": "Test task",
            "completed_at": "2025-10-06T10:00:00",
        }

        result = await _plorp_mark_task_completed({"uuid": "abc-123"})

        data = json.loads(result[0].text)
        assert data["uuid"] == "abc-123"
        assert "completed_at" in data


@pytest.mark.asyncio
async def test_plorp_defer_task():
    """Test plorp_defer_task tool."""
    with patch("plorp.mcp.server.defer_task") as mock_defer:
        mock_defer.return_value = {
            "uuid": "abc-123",
            "description": "Test task",
            "old_due": "2025-10-06",
            "new_due": "2025-10-10",
        }

        result = await _plorp_defer_task({"uuid": "abc-123", "new_due": "2025-10-10"})

        data = json.loads(result[0].text)
        assert data["new_due"] == "2025-10-10"


@pytest.mark.asyncio
async def test_plorp_drop_task():
    """Test plorp_drop_task tool."""
    with patch("plorp.mcp.server.drop_task") as mock_drop:
        mock_drop.return_value = {
            "uuid": "abc-123",
            "description": "Test task",
            "deleted_at": "2025-10-06T10:00:00",
        }

        result = await _plorp_drop_task({"uuid": "abc-123"})

        data = json.loads(result[0].text)
        assert data["uuid"] == "abc-123"
        assert "deleted_at" in data


@pytest.mark.asyncio
async def test_plorp_set_task_priority():
    """Test plorp_set_task_priority tool."""
    with patch("plorp.mcp.server.set_priority") as mock_priority:
        mock_priority.return_value = {
            "uuid": "abc-123",
            "description": "Test task",
            "priority": "H",
        }

        result = await _plorp_set_task_priority({"uuid": "abc-123", "priority": "H"})

        data = json.loads(result[0].text)
        assert data["priority"] == "H"


@pytest.mark.asyncio
async def test_plorp_get_inbox_items():
    """Test plorp_get_inbox_items tool."""
    with patch("plorp.mcp.server.get_inbox_items") as mock_inbox:
        with patch("plorp.mcp.server._get_vault_path") as mock_vault:
            mock_vault.return_value = Path("/vault")
            mock_inbox.return_value = {
                "inbox_path": "/vault/inbox/2025-10.md",
                "unprocessed_items": [{"text": "Item 1", "line_number": 1}],
                "item_count": 1,
            }

            result = await _plorp_get_inbox_items({})

            data = json.loads(result[0].text)
            assert data["item_count"] == 1


@pytest.mark.asyncio
async def test_plorp_create_task_from_inbox():
    """Test plorp_create_task_from_inbox tool."""
    with patch("plorp.mcp.server.create_task_from_inbox") as mock_create:
        with patch("plorp.mcp.server._get_vault_path") as mock_vault:
            mock_vault.return_value = Path("/vault")
            mock_create.return_value = {
                "item_text": "Buy groceries",
                "action": "task",
                "task_uuid": "abc-123",
                "note_path": None,
            }

            result = await _plorp_create_task_from_inbox(
                {"item_text": "Buy groceries", "description": "Buy groceries and supplies"}
            )

            data = json.loads(result[0].text)
            assert data["action"] == "task"
            assert data["task_uuid"] == "abc-123"


@pytest.mark.asyncio
async def test_plorp_create_note_from_inbox():
    """Test plorp_create_note_from_inbox tool."""
    with patch("plorp.mcp.server.create_note_from_inbox") as mock_create:
        with patch("plorp.mcp.server._get_vault_path") as mock_vault:
            mock_vault.return_value = Path("/vault")
            mock_create.return_value = {
                "item_text": "Research topic",
                "action": "note",
                "task_uuid": None,
                "note_path": "/vault/notes/research.md",
            }

            result = await _plorp_create_note_from_inbox(
                {"item_text": "Research topic", "title": "Research Notes"}
            )

            data = json.loads(result[0].text)
            assert data["action"] == "note"
            assert data["note_path"] is not None


@pytest.mark.asyncio
async def test_plorp_create_both_from_inbox():
    """Test plorp_create_both_from_inbox tool."""
    with patch("plorp.mcp.server.create_both_from_inbox") as mock_create:
        with patch("plorp.mcp.server._get_vault_path") as mock_vault:
            mock_vault.return_value = Path("/vault")
            mock_create.return_value = {
                "item_text": "Plan meeting",
                "action": "both",
                "task_uuid": "abc-123",
                "note_path": "/vault/notes/meeting.md",
            }

            result = await _plorp_create_both_from_inbox(
                {
                    "item_text": "Plan meeting",
                    "task_description": "Schedule meeting",
                    "note_title": "Meeting Notes",
                }
            )

            data = json.loads(result[0].text)
            assert data["action"] == "both"
            assert data["task_uuid"] is not None
            assert data["note_path"] is not None


@pytest.mark.asyncio
async def test_plorp_discard_inbox_item():
    """Test plorp_discard_inbox_item tool."""
    with patch("plorp.mcp.server.discard_inbox_item") as mock_discard:
        with patch("plorp.mcp.server._get_vault_path") as mock_vault:
            mock_vault.return_value = Path("/vault")
            mock_discard.return_value = {
                "item_text": "Old idea",
                "action": "discard",
                "task_uuid": None,
                "note_path": None,
            }

            result = await _plorp_discard_inbox_item({"item_text": "Old idea"})

            data = json.loads(result[0].text)
            assert data["action"] == "discard"


@pytest.mark.asyncio
async def test_plorp_create_note():
    """Test plorp_create_note tool."""
    with patch("plorp.mcp.server.create_note_standalone") as mock_create:
        with patch("plorp.mcp.server._get_vault_path") as mock_vault:
            mock_vault.return_value = Path("/vault")
            mock_create.return_value = {
                "note_path": "/vault/notes/test.md",
                "created_at": "2025-10-06T10:00:00",
                "title": "Test Note",
                "linked_task_uuid": None,
            }

            result = await _plorp_create_note({"title": "Test Note"})

            data = json.loads(result[0].text)
            assert data["title"] == "Test Note"
            assert data["linked_task_uuid"] is None


@pytest.mark.asyncio
async def test_plorp_create_note_with_task():
    """Test plorp_create_note_with_task tool."""
    with patch("plorp.mcp.server.create_note_linked_to_task") as mock_create:
        with patch("plorp.mcp.server._get_vault_path") as mock_vault:
            mock_vault.return_value = Path("/vault")
            mock_create.return_value = {
                "note_path": "/vault/notes/test.md",
                "created_at": "2025-10-06T10:00:00",
                "title": "Test Note",
                "linked_task_uuid": "abc-123",
            }

            result = await _plorp_create_note_with_task(
                {"title": "Test Note", "task_uuid": "abc-123"}
            )

            data = json.loads(result[0].text)
            assert data["linked_task_uuid"] == "abc-123"


@pytest.mark.asyncio
async def test_plorp_link_note_to_task():
    """Test plorp_link_note_to_task tool."""
    with patch("plorp.mcp.server.link_note_to_task") as mock_link:
        with patch("plorp.mcp.server._get_vault_path") as mock_vault:
            mock_vault.return_value = Path("/vault")
            mock_link.return_value = {
                "note_path": "/vault/notes/test.md",
                "task_uuid": "abc-123",
                "linked_at": "2025-10-06T10:00:00",
            }

            result = await _plorp_link_note_to_task(
                {"note_path": "notes/test.md", "task_uuid": "abc-123"}
            )

            data = json.loads(result[0].text)
            assert data["task_uuid"] == "abc-123"


@pytest.mark.asyncio
async def test_plorp_get_task_info():
    """Test plorp_get_task_info tool."""
    with patch("plorp.mcp.server.tw_get_task_info") as mock_get:
        mock_get.return_value = {
            "uuid": "abc-123",
            "description": "Test task",
            "status": "pending",
            "due": "20251006T000000Z",
        }

        result = await _plorp_get_task_info({"uuid": "abc-123"})

        data = json.loads(result[0].text)
        assert data["uuid"] == "abc-123"
        assert data["description"] == "Test task"


@pytest.mark.asyncio
async def test_plorp_get_task_info_not_found():
    """Test plorp_get_task_info with non-existent task."""
    with patch("plorp.mcp.server.tw_get_task_info") as mock_get:
        mock_get.return_value = None

        with pytest.raises(ValueError, match="Task not found"):
            await _plorp_get_task_info({"uuid": "nonexistent"})


@pytest.mark.asyncio
async def test_call_tool_converts_plorp_error_to_value_error():
    """Test that PlorpError is converted to ValueError (Q3 decision)."""
    with patch("plorp.mcp.server.mark_completed") as mock_mark:
        mock_mark.side_effect = TaskNotFoundError("abc-123")

        with pytest.raises(ValueError, match="Task not found"):
            await call_tool("plorp_mark_task_completed", {"uuid": "abc-123"})


@pytest.mark.asyncio
async def test_call_tool_unknown_tool():
    """Test that unknown tool raises ValueError."""
    with pytest.raises(ValueError, match="Unknown tool"):
        await call_tool("nonexistent_tool", {})


@pytest.mark.asyncio
async def test_date_defaults_to_today():
    """Test that date parameters default to today when not specified."""
    with patch("plorp.mcp.server.start_day") as mock_start:
        with patch("plorp.mcp.server._get_vault_path") as mock_vault:
            mock_vault.return_value = Path("/vault")
            mock_start.return_value = {
                "note_path": "/vault/daily/today.md",
                "date": str(date.today()),
                "summary": {"total_count": 0},
                "tasks": [],
                "created_at": "2025-10-06T09:00:00",
            }

            # Call without date argument
            result = await _plorp_start_day({})

            # Should call start_day with today's date
            mock_start.assert_called_once()
            call_args = mock_start.call_args[0]
            assert call_args[0] == date.today()


@pytest.mark.asyncio
async def test_plorp_process_daily_note_step1():
    """Test plorp_process_daily_note tool - Step 1 (no TBD section)."""
    with patch("plorp.mcp.server.process_daily_note_step1") as mock_step1:
        with patch("plorp.mcp.server._get_vault_path") as mock_vault:
            mock_vault.return_value = Path("/vault")
            
            # Mock step1 return value
            mock_step1.return_value = {
                "proposals_count": 3,
                "needs_review_count": 1,
                "tbd_section_content": "## TBD Processing\n...",
            }

            # Create test note without TBD section
            test_content = "# Daily Note\n\n## Notes\n- [ ] task 1"
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.read_text", return_value=test_content):
                    result = await _plorp_process_daily_note({"date": "2025-10-07"})

                    assert len(result) == 1
                    data = json.loads(result[0].text)
                    assert data["step"] == "1"
                    assert data["action"] == "generated_proposals"
                    assert data["proposals_count"] == 3
                    assert data["needs_review_count"] == 1
                    assert "next_steps" in data


@pytest.mark.asyncio
async def test_plorp_process_daily_note_step2():
    """Test plorp_process_daily_note tool - Step 2 (TBD section exists)."""
    with patch("plorp.mcp.server.process_daily_note_step2") as mock_step2:
        with patch("plorp.mcp.server._get_vault_path") as mock_vault:
            mock_vault.return_value = Path("/vault")
            
            # Mock step2 return value
            mock_step2.return_value = {
                "created_tasks": [
                    {
                        "uuid": "uuid-1",
                        "description": "task 1",
                        "status": "pending",
                        "due": "20251007T000000Z",
                        "priority": "L",
                        "project": None,
                        "tags": [],
                    }
                ],
                "approved_count": 1,
                "rejected_count": 0,
                "errors": [],
                "needs_review_remaining": False,
            }

            # Create test note WITH TBD section
            test_content = "# Daily Note\n\n## TBD Processing\n- [Y] **[Y/N]** task 1"
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.read_text", return_value=test_content):
                    result = await _plorp_process_daily_note({"date": "2025-10-07"})

                    assert len(result) == 1
                    data = json.loads(result[0].text)
                    assert data["step"] == "2"
                    assert data["action"] == "created_tasks_from_approvals"
                    assert data["approved_count"] == 1
                    assert data["rejected_count"] == 0
                    assert len(data["created_tasks"]) == 1
                    assert data["needs_review_remaining"] is False


@pytest.mark.asyncio
async def test_plorp_process_daily_note_no_daily_note():
    """Test plorp_process_daily_note tool when daily note doesn't exist."""
    with patch("plorp.mcp.server._get_vault_path") as mock_vault:
        mock_vault.return_value = Path("/vault")
        
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(ValueError, match="Daily note not found"):
                await _plorp_process_daily_note({"date": "2025-10-07"})
