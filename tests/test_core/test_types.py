"""
Tests for plorp.core.types module.

Tests TypedDict definitions to ensure they work correctly
and accept/reject appropriate values.
"""

import pytest
from plorp.core.types import (
    TaskInfo,
    TaskSummary,
    DailyStartResult,
    ReviewData,
    InboxItem,
    InboxData,
    NoteCreateResult,
    TaskCompleteResult,
)


def test_task_info_structure():
    """Test TaskInfo TypedDict structure."""
    task: TaskInfo = {
        "uuid": "abc-123",
        "description": "Test task",
        "status": "pending",
        "due": "2025-10-06",
        "priority": "H",
        "project": "work",
        "tags": ["important", "urgent"],
    }

    assert task["uuid"] == "abc-123"
    assert task["status"] == "pending"
    assert task["tags"] == ["important", "urgent"]


def test_task_summary_structure():
    """Test TaskSummary TypedDict structure."""
    summary: TaskSummary = {
        "overdue_count": 2,
        "due_today_count": 5,
        "recurring_count": 3,
        "total_count": 10,
    }

    assert summary["overdue_count"] == 2
    assert summary["total_count"] == 10


def test_daily_start_result_structure():
    """Test DailyStartResult TypedDict structure."""
    result: DailyStartResult = {
        "note_path": "/vault/daily/2025-10-06.md",
        "created_at": "2025-10-06T09:00:00",
        "date": "2025-10-06",
        "summary": {
            "overdue_count": 0,
            "due_today_count": 1,
            "recurring_count": 0,
            "total_count": 1,
        },
        "tasks": [],
    }

    assert result["note_path"] == "/vault/daily/2025-10-06.md"
    assert result["summary"]["total_count"] == 1


def test_review_data_structure():
    """Test ReviewData TypedDict structure."""
    data: ReviewData = {
        "date": "2025-10-06",
        "daily_note_path": "/vault/daily/2025-10-06.md",
        "uncompleted_tasks": [],
        "total_tasks": 10,
        "uncompleted_count": 3,
    }

    assert data["date"] == "2025-10-06"
    assert data["uncompleted_count"] == 3


def test_inbox_item_structure():
    """Test InboxItem TypedDict structure."""
    item: InboxItem = {"text": "Follow up with client", "line_number": 5}

    assert item["text"] == "Follow up with client"
    assert item["line_number"] == 5


def test_inbox_data_structure():
    """Test InboxData TypedDict structure."""
    data: InboxData = {
        "inbox_path": "/vault/inbox/2025-10.md",
        "unprocessed_items": [{"text": "Item 1", "line_number": 1}],
        "item_count": 1,
    }

    assert data["item_count"] == 1
    assert len(data["unprocessed_items"]) == 1


def test_note_create_result_structure():
    """Test NoteCreateResult TypedDict structure."""
    result: NoteCreateResult = {
        "note_path": "/vault/notes/meeting.md",
        "created_at": "2025-10-06T10:00:00",
        "title": "Team Meeting",
        "linked_task_uuid": "abc-123",
    }

    assert result["title"] == "Team Meeting"
    assert result["linked_task_uuid"] == "abc-123"


def test_task_complete_result_structure():
    """Test TaskCompleteResult TypedDict structure."""
    result: TaskCompleteResult = {
        "uuid": "abc-123",
        "description": "Completed task",
        "completed_at": "2025-10-06T11:00:00",
    }

    assert result["uuid"] == "abc-123"
    assert "completed_at" in result
