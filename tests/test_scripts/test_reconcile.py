# ABOUTME: Tests for TaskWarrior reconciliation script
# ABOUTME: Sprint 8.5 Item 2 - External change reconciliation via TaskChampion operations log
"""
Tests for reconcile_taskwarrior.py script.

Tests the reconciliation logic that detects external TaskWarrior changes
and updates Obsidian project frontmatter accordingly.
"""
import json
import sqlite3
from pathlib import Path
from unittest.mock import patch
import pytest


# ============================================================================
# Test Helpers
# ============================================================================


def create_test_operations_db(tmp_path: Path) -> Path:
    """Create a test TaskWarrior operations database."""
    db_path = tmp_path / "taskchampion.sqlite3"
    conn = sqlite3.connect(db_path)

    # Create schema matching TaskWarrior 3.x
    conn.execute("""
        CREATE TABLE operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data STRING,
            uuid GENERATED ALWAYS AS (
                coalesce(
                    json_extract(data, "$.Update.uuid"),
                    json_extract(data, "$.Create.uuid"),
                    json_extract(data, "$.Delete.uuid")
                )
            ) VIRTUAL,
            synced bool DEFAULT false
        )
    """)

    conn.commit()
    conn.close()
    return db_path


def insert_operation(db_path: Path, operation_data: dict) -> int:
    """Insert operation into test database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "INSERT INTO operations (data) VALUES (?)",
        (json.dumps(operation_data),)
    )
    op_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return op_id


# ============================================================================
# Unit Tests: Parse Operations
# ============================================================================


def test_parse_operations_detects_completions(tmp_path):
    """Test that parser detects tasks marked completed (Sprint 8.5 Item 2)."""
    from scripts.reconcile_taskwarrior import parse_operations

    # Setup: Create test database
    db_path = create_test_operations_db(tmp_path)

    # Insert operations: Create task, then mark it completed
    task_uuid = "abc-123-def-456"
    insert_operation(db_path, {"Create": {"uuid": task_uuid}})
    insert_operation(db_path, {
        "Update": {
            "uuid": task_uuid,
            "property": "status",
            "value": "completed",
            "old_value": "pending",
            "timestamp": "2025-10-08T12:00:00Z"
        }
    })

    # Test: Parse operations since ID 0
    completed_uuids, latest_id = parse_operations(db_path, since_id=0)

    # Assert: UUID detected
    assert task_uuid in completed_uuids
    assert latest_id == 2


def test_parse_operations_detects_deletions(tmp_path):
    """Test that parser detects deleted tasks (Sprint 8.5 Item 2)."""
    from scripts.reconcile_taskwarrior import parse_operations

    # Setup: Create test database
    db_path = create_test_operations_db(tmp_path)

    # Insert operations: Create task, then delete it
    task_uuid = "xyz-789-abc-123"
    insert_operation(db_path, {"Create": {"uuid": task_uuid}})
    insert_operation(db_path, {
        "Update": {
            "uuid": task_uuid,
            "property": "status",
            "value": "deleted",
            "old_value": "pending",
            "timestamp": "2025-10-08T12:00:00Z"
        }
    })

    # Test: Parse operations since ID 0
    deleted_uuids, latest_id = parse_operations(db_path, since_id=0)

    # Assert: UUID detected
    assert task_uuid in deleted_uuids
    assert latest_id == 2


def test_parse_operations_ignores_other_updates(tmp_path):
    """Test that parser ignores non-status updates."""
    from scripts.reconcile_taskwarrior import parse_operations

    # Setup: Create test database
    db_path = create_test_operations_db(tmp_path)

    # Insert operations: Create task, update description (not status)
    task_uuid = "test-uuid-123"
    insert_operation(db_path, {"Create": {"uuid": task_uuid}})
    insert_operation(db_path, {
        "Update": {
            "uuid": task_uuid,
            "property": "description",
            "value": "New description",
            "old_value": "Old description",
            "timestamp": "2025-10-08T12:00:00Z"
        }
    })

    # Test: Parse operations
    changed_uuids, latest_id = parse_operations(db_path, since_id=0)

    # Assert: No UUIDs detected (only description changed, not status)
    assert len(changed_uuids) == 0
    assert latest_id == 2


def test_parse_operations_respects_since_id(tmp_path):
    """Test that parser only processes operations after since_id."""
    from scripts.reconcile_taskwarrior import parse_operations

    # Setup: Create test database
    db_path = create_test_operations_db(tmp_path)

    # Insert old operations (before checkpoint)
    old_uuid = "old-task-uuid"
    insert_operation(db_path, {"Create": {"uuid": old_uuid}})
    insert_operation(db_path, {
        "Update": {"uuid": old_uuid, "property": "status", "value": "completed", "timestamp": "2025-10-08T12:00:00Z"}
    })

    # Insert new operations (after checkpoint)
    new_uuid = "new-task-uuid"
    insert_operation(db_path, {"Create": {"uuid": new_uuid}})
    insert_operation(db_path, {
        "Update": {"uuid": new_uuid, "property": "status", "value": "deleted", "timestamp": "2025-10-08T13:00:00Z"}
    })

    # Test: Parse operations since ID 2 (skip old operations)
    changed_uuids, latest_id = parse_operations(db_path, since_id=2)

    # Assert: Only new UUID detected
    assert old_uuid not in changed_uuids
    assert new_uuid in changed_uuids
    assert latest_id == 4


# ============================================================================
# Integration Test: State File Tracking
# ============================================================================


def test_state_file_tracking(tmp_path):
    """Test that state file persists last processed operation ID."""
    from scripts.reconcile_taskwarrior import get_last_processed_id, save_last_processed_id

    state_file = tmp_path / "last_operation_id"

    # Test: Initial read (no file exists)
    assert get_last_processed_id(state_file) == 0

    # Test: Save and read back
    save_last_processed_id(state_file, 42)
    assert get_last_processed_id(state_file) == 42

    # Test: Update and read back
    save_last_processed_id(state_file, 100)
    assert get_last_processed_id(state_file) == 100
