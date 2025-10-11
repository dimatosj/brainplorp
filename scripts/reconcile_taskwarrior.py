#!/usr/bin/env python3
"""
Reconcile Obsidian vault with external TaskWarrior changes.

Sprint 8.5 Item 2: External Change Reconciliation

Reads TaskWarrior 3.x's operations table (SQLite) to detect tasks deleted
or completed outside plorp, then updates project frontmatter accordingly.

TaskWarrior 3.x uses TaskChampion with SQLite instead of undo.data.
Operations are stored in taskchampion.sqlite3 with JSON format.

Run via cron: */15 * * * * /path/to/reconcile_taskwarrior.py

Author: plorp team
Date: 2025-10-08
"""

import json
import sqlite3
from pathlib import Path
from typing import Set, Tuple


# ============================================================================
# Configuration
# ============================================================================


def get_state_file() -> Path:
    """Get state file path for tracking last processed operation ID."""
    return Path.home() / ".config/plorp/last_operation_id"


def get_taskwarrior_db() -> Path:
    """Get TaskWarrior SQLite database path."""
    return Path.home() / ".task/taskchampion.sqlite3"


def get_vault_path() -> Path:
    """Get vault path from plorp config."""
    from brainplorp.config import load_config
    config = load_config()
    return Path(config["vault_path"]).expanduser().resolve()


# ============================================================================
# State Tracking
# ============================================================================


def get_last_processed_id(state_file: Path) -> int:
    """
    Read last processed operation ID from state file.

    Returns:
        Last processed operation ID, or 0 if no state file exists
    """
    if not state_file.exists():
        return 0
    return int(state_file.read_text().strip())


def save_last_processed_id(state_file: Path, operation_id: int):
    """
    Save last processed operation ID to state file.

    Args:
        state_file: Path to state file
        operation_id: Operation ID to save
    """
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(str(operation_id))


# ============================================================================
# TaskWarrior Operations Parsing
# ============================================================================


def parse_operations(db_path: Path, since_id: int = 0) -> Tuple[Set[str], int]:
    """
    Parse TaskWarrior operations table for deleted/completed task UUIDs.

    TaskWarrior 3.x stores operations in SQLite with JSON data.
    Each operation is one of:
    - Create: {"Create": {"uuid": "..."}}
    - Update: {"Update": {"uuid": "...", "property": "...", "value": "..."}}
    - Delete: {"Delete": {"uuid": "..."}}

    We detect tasks that changed status to "completed" or "deleted".

    Args:
        db_path: Path to taskchampion.sqlite3
        since_id: Only process operations with ID > since_id

    Returns:
        Tuple of (set of UUIDs that were completed/deleted, latest operation ID)
    """
    changed_uuids: Set[str] = set()
    latest_id = since_id

    if not db_path.exists():
        return changed_uuids, latest_id

    # Connect to TaskWarrior SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        """
        SELECT id, data
        FROM operations
        WHERE id > ?
        ORDER BY id ASC
        """,
        (since_id,)
    )

    for op_id, data_json in cursor:
        latest_id = op_id

        try:
            data = json.loads(data_json)

            # Check for status update to completed or deleted
            if "Update" in data:
                update = data["Update"]
                if update.get("property") == "status":
                    value = update.get("value")
                    if value in ["completed", "deleted"]:
                        uuid = update.get("uuid")
                        if uuid:
                            changed_uuids.add(uuid)

        except (json.JSONDecodeError, KeyError):
            # Skip malformed operations
            continue

    conn.close()
    return changed_uuids, latest_id


# ============================================================================
# Obsidian Project Updates
# ============================================================================


def remove_uuids_from_projects(vault_path: Path, uuids: Set[str]):
    """
    Remove UUIDs from all project frontmatter.

    Uses the same remove_task_from_all_projects helper from Sprint 8.5 Item 1.

    Args:
        vault_path: Path to Obsidian vault
        uuids: Set of UUIDs to remove
    """
    # Import the State Sync function from Item 1
    from brainplorp.core.projects import remove_task_from_all_projects

    for uuid in uuids:
        remove_task_from_all_projects(vault_path, uuid)


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """
    Main reconciliation workflow.

    1. Read last processed operation ID
    2. Parse new operations from TaskWarrior SQLite
    3. Remove orphaned UUIDs from project frontmatter
    4. Update state file
    """
    # Get paths
    state_file = get_state_file()
    db_path = get_taskwarrior_db()
    vault_path = get_vault_path()

    # Read last checkpoint
    last_id = get_last_processed_id(state_file)

    # Parse new operations
    changed_uuids, latest_id = parse_operations(db_path, since_id=last_id)

    # Update Obsidian if changes detected
    if changed_uuids:
        print(f"Found {len(changed_uuids)} completed/deleted tasks:")
        for uuid in changed_uuids:
            print(f"  - {uuid}")

        remove_uuids_from_projects(vault_path, changed_uuids)
        print(f"✓ Updated project frontmatter")

    # Save checkpoint
    save_last_processed_id(state_file, latest_id)

    if changed_uuids:
        print(f"✓ Processed operations up to ID {latest_id}")
    else:
        print(f"No changes detected (operations {last_id} → {latest_id})")


if __name__ == "__main__":
    main()
