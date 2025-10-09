# ABOUTME: Tests for core process workflow - scanning informal tasks and creating proposals
# ABOUTME: Covers Sprint 7 two-step processing workflow with comprehensive scenarios
"""
Tests for process.py core module.

Comprehensive integration and end-to-end tests for task processing workflow.
"""
from datetime import date
from pathlib import Path
import pytest
from plorp.core.process import (
    scan_for_informal_tasks,
    generate_proposal,
    process_daily_note_step1,
    process_daily_note_step2,
)
from plorp.core.types import InformalTask, TaskProposal


# ============================================================================
# Helper Functions for Test Data
# ============================================================================


def create_test_daily_note(tmp_path: Path, content: str) -> Path:
    """Create a temporary daily note for testing."""
    daily_dir = tmp_path / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    note_path = daily_dir / "2025-10-07.md"
    note_path.write_text(content)
    return note_path


# ============================================================================
# Unit Tests: scan_for_informal_tasks
# ============================================================================


def test_scan_for_informal_tasks_basic(tmp_path):
    """Test scanning identifies informal tasks without UUIDs."""
    content = """# 2025-10-07 Monday

## Tasks
- [ ] existing task (uuid: abc-123)

## Notes
- [ ] call mom today
- [ ] buy groceries
"""
    result = scan_for_informal_tasks(content)

    assert len(result) == 2
    assert result[0]["text"] == "call mom today"
    assert result[1]["text"] == "buy groceries"


def test_scan_ignores_formal_tasks_with_uuid(tmp_path):
    """Test that tasks with UUIDs are ignored (Q4)."""
    content = """# Daily Note

## Tasks
- [ ] task with uuid (uuid: abc-123)
- [ ] task with metadata (due: 2025-10-07, uuid: def-456)
- [ ] informal task without uuid
"""
    result = scan_for_informal_tasks(content)

    assert len(result) == 1
    assert result[0]["text"] == "informal task without uuid"


def test_scan_captures_checkbox_state(tmp_path):
    """Test capturing checked vs unchecked state (Q19)."""
    content = """
- [ ] unchecked task
- [x] checked task
- [X] checked task uppercase
"""
    result = scan_for_informal_tasks(content)

    assert len(result) == 3
    assert result[0]["checkbox_state"] == "[ ]"
    assert result[1]["checkbox_state"] == "[x]"
    assert result[2]["checkbox_state"] == "[X]"


def test_scan_captures_section_names(tmp_path):
    """Test section name detection (Q10)."""
    content = """# 2025-10-07 Monday

- [ ] task before any section

## Notes
- [ ] task in notes

### Subsection
- [ ] task in subsection
"""
    result = scan_for_informal_tasks(content)

    assert len(result) == 3
    assert result[0]["section"] == "(top of file)"
    assert result[1]["section"] == "Notes"
    assert result[2]["section"] == "Subsection"


def test_scan_captures_line_numbers(tmp_path):
    """Test line number capture (0-indexed internally, Q22)."""
    content = """Line 0
Line 1
- [ ] task on line 2
Line 3
- [ ] task on line 4"""

    result = scan_for_informal_tasks(content)

    assert len(result) == 2
    assert result[0]["line_number"] == 2  # 0-indexed
    assert result[1]["line_number"] == 4


def test_scan_captures_original_line(tmp_path):
    """Test capturing original line for removal (Q21)."""
    content = """
- [ ] call mom today
  - [ ] indented task with spaces
	- [ ] indented task with tab
"""
    result = scan_for_informal_tasks(content)

    assert len(result) == 3
    assert result[0]["original_line"].strip() == "- [ ] call mom today"
    # Indented tasks should also have their original line captured
    assert "indented task with spaces" in result[1]["original_line"]


def test_scan_flexible_checkbox_formats(tmp_path):
    """Test liberal checkbox detection (Q9)."""
    content = """
- [ ] standard format
-[ ] no space after dash
- [] no space in checkbox
* [ ] asterisk bullet
  - [ ] indented with spaces
	- [ ] indented with tab
"""
    result = scan_for_informal_tasks(content)

    # Should detect all variations
    assert len(result) == 6


# ============================================================================
# Unit Tests: generate_proposal
# ============================================================================


def test_generate_proposal_with_today():
    """Test proposal generation for task with 'today'."""
    informal_task: InformalTask = {
        "text": "call mom today",
        "line_number": 5,
        "section": "Notes",
        "checkbox_state": "[ ]",
        "original_line": "- [ ] call mom today",
    }
    reference = date(2025, 10, 7)

    proposal = generate_proposal(informal_task, reference)

    assert proposal["proposed_description"] == "call mom"
    assert proposal["proposed_due"] == "2025-10-07"
    assert proposal["proposed_priority"] == "L"
    assert proposal["needs_review"] is False


def test_generate_proposal_with_urgent():
    """Test proposal with urgent keyword → H priority."""
    informal_task: InformalTask = {
        "text": "urgent task to finish",
        "line_number": 5,
        "section": "Notes",
        "checkbox_state": "[ ]",
        "original_line": "- [ ] urgent task to finish",
    }
    reference = date(2025, 10, 7)

    proposal = generate_proposal(informal_task, reference)

    assert proposal["proposed_priority"] == "H"
    assert proposal["priority_reason"] == "detected 'urgent'"
    assert "urgent" not in proposal["proposed_description"].lower()


def test_generate_proposal_with_important():
    """Test proposal with important keyword → M priority."""
    informal_task: InformalTask = {
        "text": "important meeting tomorrow",
        "line_number": 5,
        "section": "Notes",
        "checkbox_state": "[ ]",
        "original_line": "- [ ] important meeting tomorrow",
    }
    reference = date(2025, 10, 7)

    proposal = generate_proposal(informal_task, reference)

    assert proposal["proposed_priority"] == "M"
    assert proposal["priority_reason"] == "detected 'important'"
    assert proposal["proposed_due"] == "2025-10-08"


def test_generate_proposal_no_date():
    """Test proposal without date → no due field."""
    informal_task: InformalTask = {
        "text": "buy groceries",
        "line_number": 5,
        "section": "Random",
        "checkbox_state": "[ ]",
        "original_line": "- [ ] buy groceries",
    }
    reference = date(2025, 10, 7)

    proposal = generate_proposal(informal_task, reference)

    assert proposal["proposed_due"] is None
    assert proposal["proposed_priority"] == "L"
    assert proposal["needs_review"] is False


# ============================================================================
# Integration Tests: Step 1 (Proposal Generation)
# ============================================================================


def test_process_step1_creates_tbd_section(tmp_path):
    """Test that step 1 creates TBD Processing section."""
    content = """# 2025-10-07 Monday

## Notes
- [ ] call mom today
- [ ] buy groceries
"""
    note_path = create_test_daily_note(tmp_path, content)

    result = process_daily_note_step1(note_path, date(2025, 10, 7))

    assert result["proposals_count"] == 2
    assert "## TBD Processing" in result["tbd_section_content"]


def test_process_step1_identifies_informal_tasks(tmp_path):
    """Test identification of informal tasks (no UUIDs)."""
    content = """# Daily Note

- [ ] informal task 1
- [ ] formal task (uuid: abc-123)
- [ ] informal task 2
"""
    note_path = create_test_daily_note(tmp_path, content)

    result = process_daily_note_step1(note_path, date(2025, 10, 7))

    assert result["proposals_count"] == 2  # Only informal tasks


def test_process_step1_ignores_formal_tasks(tmp_path):
    """Test that tasks with UUIDs are ignored."""
    content = """# Daily Note

## Tasks
- [ ] task 1 (uuid: abc-123)
- [ ] task 2 (due: 2025-10-07, priority: H, uuid: def-456)

## Notes
- [ ] informal task
"""
    note_path = create_test_daily_note(tmp_path, content)

    result = process_daily_note_step1(note_path, date(2025, 10, 7))

    assert result["proposals_count"] == 1  # Only the informal task


def test_process_step1_scans_entire_document(tmp_path):
    """Test that tasks are found in any section."""
    content = """# Daily Note

- [ ] task at top

## Notes
- [ ] task in notes

## Random Section
- [ ] task in random section

### Deep Subsection
- [ ] task in deep section
"""
    note_path = create_test_daily_note(tmp_path, content)

    result = process_daily_note_step1(note_path, date(2025, 10, 7))

    assert result["proposals_count"] == 4


def test_process_step1_generates_correct_format(tmp_path):
    """Test TBD section format (Q16)."""
    content = """# Daily Note

## Notes
- [ ] call mom today
"""
    note_path = create_test_daily_note(tmp_path, content)

    result = process_daily_note_step1(note_path, date(2025, 10, 7))

    tbd = result["tbd_section_content"]

    # Check format elements
    assert "- [ ] **[Y/N]**" in tbd
    assert '- Proposed: `description: "' in tbd
    assert "- Original location:" in tbd
    assert "(line " in tbd


# ============================================================================
# Integration Tests: Step 2 (Task Creation)
# ============================================================================


def test_process_step2_creates_tasks_from_approvals(tmp_path):
    """Test task creation for [Y] markers."""
    # Setup: Create note with TBD section containing [Y] approvals
    content = """# 2025-10-07 Monday

## Notes
- [ ] call mom today
- [ ] buy groceries

## TBD Processing

- [Y] **[Y/N]** call mom
	- Proposed: `description: "call mom", due: 2025-10-07, priority: M`
	- Original location: Notes (line 4)

- [N] **[Y/N]** buy groceries
	- Proposed: `description: "buy groceries", priority: L`
	- Original location: Notes (line 5)
"""
    note_path = create_test_daily_note(tmp_path, content)

    # Mock TaskWarrior integration
    from unittest.mock import patch, MagicMock

    with patch('plorp.integrations.taskwarrior.create_task') as mock_create_task:
        # Mock successful task creation
        mock_create_task.return_value = "abc-123-uuid"

        # Mock get_task_info to return task details
        with patch('plorp.integrations.taskwarrior.get_task_info') as mock_get_task_info:
            mock_get_task_info.return_value = {
                "uuid": "abc-123-uuid",
                "description": "call mom",
                "status": "pending",
                "due": "20251007T000000Z",
                "priority": "M",
                "project": None,
                "tags": []
            }

            result = process_daily_note_step2(note_path, date(2025, 10, 7))

            # Should create 1 task (the [Y] approval)
            assert result["approved_count"] == 1
            assert result["rejected_count"] == 1
            assert len(result["created_tasks"]) == 1
            assert result["created_tasks"][0]["uuid"] == "abc-123-uuid"


def test_process_step2_preserves_rejected_tasks(tmp_path):
    """Test that [N] tasks stay in original location."""
    content = """# Daily Note

## Notes
- [ ] task 1
- [ ] task 2

## TBD Processing

- [Y] **[Y/N]** task 1
	- Proposed: `description: "task 1", priority: L`
	- Original location: Notes (line 4)

- [N] **[Y/N]** task 2
	- Proposed: `description: "task 2", priority: L`
	- Original location: Notes (line 5)
"""
    note_path = create_test_daily_note(tmp_path, content)

    from unittest.mock import patch

    with patch('plorp.integrations.taskwarrior.create_task') as mock_create:
        mock_create.return_value = "uuid-1"
        with patch('plorp.integrations.taskwarrior.get_task_info') as mock_get:
            mock_get.return_value = {
                "uuid": "uuid-1",
                "description": "task 1",
                "status": "pending",
                "due": None,
                "priority": "L",
                "project": None,
                "tags": []
            }

            process_daily_note_step2(note_path, date(2025, 10, 7))

            # Read note and verify rejected task is still there
            updated_content = note_path.read_text()
            print("\n=== UPDATED CONTENT ===")
            print(updated_content)
            print("=== END ===\n")

            # Extract Notes section to verify approved task removed from original location
            import re
            notes_section_match = re.search(r'## Notes\n(.*?)(?=\n##|\Z)', updated_content, re.DOTALL)
            assert notes_section_match is not None
            notes_content = notes_section_match.group(1)

            assert "- [ ] task 2" in notes_content  # Rejected task stays
            assert "- [ ] task 1" not in notes_content  # Approved task removed from original location


def test_process_step2_removes_tbd_section_on_success(tmp_path):
    """Test TBD section removed when all tasks processed successfully."""
    content = """# Daily Note

## Notes
- [ ] task 1

## TBD Processing

- [Y] **[Y/N]** task 1
	- Proposed: `description: "task 1", priority: L`
	- Original location: Notes (line 4)
"""
    note_path = create_test_daily_note(tmp_path, content)

    from unittest.mock import patch

    with patch('plorp.integrations.taskwarrior.create_task') as mock_create:
        mock_create.return_value = "uuid-1"
        with patch('plorp.integrations.taskwarrior.get_task_info') as mock_get:
            mock_get.return_value = {
                "uuid": "uuid-1",
                "description": "task 1",
                "status": "pending",
                "due": None,
                "priority": "L",
                "project": None,
                "tags": []
            }

            result = process_daily_note_step2(note_path, date(2025, 10, 7))

            # Should have no errors
            assert result["needs_review_remaining"] is False

            # TBD section should be removed
            updated_content = note_path.read_text()
            assert "## TBD Processing" not in updated_content


def test_process_step2_keeps_tbd_on_errors(tmp_path):
    """Test TBD section kept when errors occur."""
    content = """# Daily Note

## Notes
- [ ] task 1

## TBD Processing

- [Y] **[Y/N]** task 1
	- Proposed: `description: "task 1", priority: L`
	- Original location: Notes (line 4)
	- *NEEDS_REVIEW: Test error condition*
"""
    note_path = create_test_daily_note(tmp_path, content)

    # Don't mock - let it fail naturally or mark as needing review
    result = process_daily_note_step2(note_path, date(2025, 10, 7))

    # Should keep TBD section due to NEEDS_REVIEW
    updated_content = note_path.read_text()
    assert "## TBD Processing" in updated_content or result["needs_review_remaining"] is True


# ============================================================================
# End-to-End Tests
# ============================================================================


def test_full_workflow_success(tmp_path):
    """Test complete workflow: scan → approve → create."""
    # Step 1: Create note with informal tasks
    content = """# Daily Note

## Notes
- [ ] call mom today
- [ ] buy groceries
"""
    note_path = create_test_daily_note(tmp_path, content)

    # Step 1: Generate proposals
    result1 = process_daily_note_step1(note_path, date(2025, 10, 7))
    assert result1["proposals_count"] == 2

    # Simulate user approval: mark both as [Y]
    updated_content = note_path.read_text()
    updated_content = updated_content.replace("- [ ] **[Y/N]**", "- [Y] **[Y/N]**")
    note_path.write_text(updated_content)

    # Step 2: Create tasks from approvals
    from unittest.mock import patch

    with patch('plorp.integrations.taskwarrior.create_task') as mock_create:
        # Return different UUIDs for each task
        mock_create.side_effect = ["uuid-1", "uuid-2"]

        with patch('plorp.integrations.taskwarrior.get_task_info') as mock_get:
            def get_task_side_effect(uuid):
                if uuid == "uuid-1":
                    return {
                        "uuid": "uuid-1",
                        "description": "call mom",
                        "status": "pending",
                        "due": "20251007T000000Z",
                        "priority": "L",
                        "project": None,
                        "tags": []
                    }
                elif uuid == "uuid-2":
                    return {
                        "uuid": "uuid-2",
                        "description": "buy groceries",
                        "status": "pending",
                        "due": None,
                        "priority": "L",
                        "project": None,
                        "tags": []
                    }
            mock_get.side_effect = get_task_side_effect

            result2 = process_daily_note_step2(note_path, date(2025, 10, 7))

            assert result2["approved_count"] == 2
            assert result2["rejected_count"] == 0
            assert len(result2["created_tasks"]) == 2
            assert result2["needs_review_remaining"] is False


def test_full_workflow_with_rejections(tmp_path):
    """Test workflow with both Y and N approvals."""
    content = """# Daily Note

## Notes
- [ ] task 1
- [ ] task 2
- [ ] task 3
"""
    note_path = create_test_daily_note(tmp_path, content)

    # Step 1
    result1 = process_daily_note_step1(note_path, date(2025, 10, 7))
    assert result1["proposals_count"] == 3

    # Simulate user: Approve 1, reject 2, skip 3 (leave as [ ])
    updated_content = note_path.read_text()
    lines = updated_content.split('\n')
    new_lines = []
    proposal_count = 0
    for line in lines:
        if "**[Y/N]**" in line:
            proposal_count += 1
            if proposal_count == 1:
                new_lines.append(line.replace("- [ ] **[Y/N]**", "- [Y] **[Y/N]**"))
            elif proposal_count == 2:
                new_lines.append(line.replace("- [ ] **[Y/N]**", "- [N] **[Y/N]**"))
            else:
                new_lines.append(line)  # Leave as [ ]
        else:
            new_lines.append(line)
    note_path.write_text('\n'.join(new_lines))

    # Step 2
    from unittest.mock import patch

    with patch('plorp.integrations.taskwarrior.create_task') as mock_create:
        mock_create.return_value = "uuid-1"
        with patch('plorp.integrations.taskwarrior.get_task_info') as mock_get:
            mock_get.return_value = {
                "uuid": "uuid-1",
                "description": "task 1",
                "status": "pending",
                "due": None,
                "priority": "L",
                "project": None,
                "tags": []
            }

            result2 = process_daily_note_step2(note_path, date(2025, 10, 7))

            # 1 approved, 1 rejected, 1 skipped
            assert result2["approved_count"] == 1
            assert result2["rejected_count"] >= 1  # At least the explicit [N]

            # Verify rejected task still in original location
            final_content = note_path.read_text()
            assert "- [ ] task 2" in final_content


def test_full_workflow_with_errors(tmp_path):
    """Test workflow with NEEDS_REVIEW items."""
    content = """# Daily Note

## Notes
- [ ] call mom on Invalid-Date
- [ ] buy groceries today
"""
    note_path = create_test_daily_note(tmp_path, content)

    # Step 1: Generate proposals
    result1 = process_daily_note_step1(note_path, date(2025, 10, 7))
    assert result1["proposals_count"] == 2
    assert result1["needs_review_count"] == 1  # Invalid-Date task

    # Verify TBD section has NEEDS_REVIEW marker (Q20: italics format)
    step1_content = note_path.read_text()
    assert "*NEEDS_REVIEW:" in step1_content

    # Simulate user approval: mark both as [Y]
    updated_content = step1_content.replace("- [ ] **[Y/N]**", "- [Y] **[Y/N]**")
    note_path.write_text(updated_content)

    # Step 2: Create tasks from approvals
    from unittest.mock import patch

    with patch('plorp.integrations.taskwarrior.create_task') as mock_create:
        mock_create.return_value = "uuid-1"
        with patch('plorp.integrations.taskwarrior.get_task_info') as mock_get:
            mock_get.return_value = {
                "uuid": "uuid-1",
                "description": "buy groceries",
                "status": "pending",
                "due": "20251007T000000Z",
                "priority": "L",
                "project": None,
                "tags": []
            }

            result2 = process_daily_note_step2(note_path, date(2025, 10, 7))

            # Only 1 task should be created (the valid one)
            assert result2["approved_count"] == 2  # Both were approved by user
            assert len(result2["created_tasks"]) == 1  # But only 1 succeeded
            assert len(result2["errors"]) == 1  # 1 NEEDS_REVIEW error
            assert result2["needs_review_remaining"] is True

            # Verify TBD section is kept because of NEEDS_REVIEW
            final_content = note_path.read_text()
            assert "## TBD Processing" in final_content
            assert "*NEEDS_REVIEW:" in final_content

            # Verify the successful task was created
            assert "## Created Tasks" in final_content
            assert "buy groceries" in final_content


# ============================================================================
# Bug #2 Regression Tests: Optional TaskWarrior Fields
# ============================================================================


def test_process_step2_task_without_due_date(tmp_path):
    """Ensure Step 2 handles tasks without due dates (Bug #2 regression test).

    TaskWarrior omits the 'due' key entirely when a task has no due date,
    rather than setting it to None. This test ensures we use .get() instead
    of bracket notation to avoid KeyError.
    """
    # Create daily note with approved proposal (no due date)
    content = """# 2025-10-07 Monday

## Notes
- [ ] buy groceries

## TBD Processing

- [Y] **[Y/N]** buy groceries
\t- Proposed: `description: "buy groceries", priority: L`
\t- Original location: Notes (line 4)
"""
    note_path = create_test_daily_note(tmp_path, content)

    # Mock TaskWarrior integration
    from unittest.mock import patch

    with patch('plorp.integrations.taskwarrior.create_task') as mock_create, \
         patch('plorp.integrations.taskwarrior.get_task_info') as mock_get:

        mock_create.return_value = "uuid-123"

        # Real TaskWarrior omits 'due' key when not set (not None, ABSENT)
        mock_get.return_value = {
            "uuid": "uuid-123",
            "description": "buy groceries",
            "status": "pending",
            "priority": "L",
            # NO 'due' key - this is what triggers the bug
        }

        # Should not raise KeyError
        result = process_daily_note_step2(note_path, date(2025, 10, 7))

    # Verify success
    assert result["approved_count"] == 1
    assert len(result["errors"]) == 0
    assert len(result["created_tasks"]) == 1
    assert result["created_tasks"][0]["description"] == "buy groceries"

    # Verify note content (task should be in Created Tasks section)
    final_content = note_path.read_text()
    assert "## Created Tasks" in final_content
    assert "buy groceries" in final_content


def test_process_step2_task_without_priority(tmp_path):
    """Ensure Step 2 handles tasks without priority (Bug #2 regression test).

    TaskWarrior omits the 'priority' key entirely when a task has no priority,
    rather than setting it to None. This test ensures we use .get() instead
    of bracket notation to avoid KeyError.
    """
    # Create daily note with approved proposal (no priority)
    content = """# 2025-10-07 Monday

## Notes
- [ ] call dentist

## TBD Processing

- [Y] **[Y/N]** call dentist
\t- Proposed: `description: "call dentist", due: 2025-10-10`
\t- Original location: Notes (line 4)
"""
    note_path = create_test_daily_note(tmp_path, content)

    from unittest.mock import patch

    with patch('plorp.integrations.taskwarrior.create_task') as mock_create, \
         patch('plorp.integrations.taskwarrior.get_task_info') as mock_get:

        mock_create.return_value = "uuid-456"

        # Real TaskWarrior omits 'priority' key when not set
        mock_get.return_value = {
            "uuid": "uuid-456",
            "description": "call dentist",
            "status": "pending",
            "due": "20251010T000000Z",
            # NO 'priority' key
        }

        result = process_daily_note_step2(note_path, date(2025, 10, 7))

    # Verify success
    assert result["approved_count"] == 1
    assert len(result["errors"]) == 0
    assert len(result["created_tasks"]) == 1

    # Verify note content
    final_content = note_path.read_text()
    assert "## Created Tasks" in final_content
    assert "call dentist" in final_content


def test_process_step2_task_minimal_fields(tmp_path):
    """Ensure Step 2 handles tasks with only required fields (Bug #2 regression test).

    TaskWarrior only requires 'description'. When both 'due' and 'priority' are
    omitted, the JSON export omits both keys entirely. This test ensures we
    handle the minimal case gracefully.
    """
    # Create daily note with approved proposal (no due, no priority)
    content = """# 2025-10-07 Monday

## Notes
- [ ] read book

## TBD Processing

- [Y] **[Y/N]** read book
\t- Proposed: `description: "read book"`
\t- Original location: Notes (line 4)
"""
    note_path = create_test_daily_note(tmp_path, content)

    from unittest.mock import patch

    with patch('plorp.integrations.taskwarrior.create_task') as mock_create, \
         patch('plorp.integrations.taskwarrior.get_task_info') as mock_get:

        mock_create.return_value = "uuid-789"

        # Minimal TaskWarrior response (only required fields)
        mock_get.return_value = {
            "uuid": "uuid-789",
            "description": "read book",
            "status": "pending",
            # NO 'due' or 'priority' keys
        }

        result = process_daily_note_step2(note_path, date(2025, 10, 7))

    # Verify success
    assert result["approved_count"] == 1
    assert len(result["errors"]) == 0
    assert len(result["created_tasks"]) == 1
    assert result["created_tasks"][0]["description"] == "read book"

    # Verify note content shows only uuid metadata (no due, no priority)
    final_content = note_path.read_text()
    assert "## Created Tasks" in final_content
    assert "read book" in final_content
    assert "(uuid: uuid-789)" in final_content


# ============================================================================
# Sprint 8.5: Checkbox Sync Tests (Item 1)
# ============================================================================


def test_process_step2_syncs_checked_formal_tasks(tmp_path):
    """Test that checked formal tasks are marked done in TaskWarrior (Sprint 8.5 Item 1).

    When /process Step 2 runs, it should scan for formal tasks (with UUIDs)
    that have been checked in Obsidian and mark them done in TaskWarrior.
    """
    # Create daily note with checked formal task
    content = """# 2025-10-07 Monday

## Tasks
- [x] Buy groceries (uuid: task-abc-123)
- [ ] Call dentist (uuid: task-def-456)

## Notes
Some notes here
"""
    note_path = create_test_daily_note(tmp_path, content)

    # Mock TaskWarrior integration
    from unittest.mock import patch, MagicMock

    with patch('plorp.integrations.taskwarrior.get_task_info') as mock_get_info, \
         patch('plorp.integrations.taskwarrior.mark_done') as mock_mark_done:

        # Mock task exists
        mock_get_info.return_value = {
            "uuid": "task-abc-123",
            "description": "Buy groceries",
            "status": "pending"
        }

        # Mock vault_path for State Sync (no projects to update in this test)
        result = process_daily_note_step2(note_path, date(2025, 10, 7), tmp_path)

        # Assert: mark_done was called for the checked task
        mock_mark_done.assert_called_once_with("task-abc-123")


def test_process_step2_removes_from_projects_when_done(tmp_path, monkeypatch):
    """Test that checked tasks are removed from project frontmatter (Sprint 8.5 Item 1).

    State Synchronization pattern: when a task is marked done via checkbox,
    it must be removed from all project frontmatter.
    """
    # Setup: Create vault structure with project
    monkeypatch.setattr("plorp.integrations.obsidian_bases.get_vault_path", lambda: tmp_path)

    # Create project with task
    from plorp.core.projects import create_project
    from plorp.integrations.obsidian_bases import add_task_to_project

    create_project(name="groceries", domain="home", workstream="chores")
    add_task_to_project("home.chores.groceries", "task-xyz-789")

    # Create daily note with checked formal task
    content = """# 2025-10-07 Monday

## Tasks
- [x] Buy milk (uuid: task-xyz-789)

## Notes
Some notes
"""
    note_path = create_test_daily_note(tmp_path, content)

    # Mock TaskWarrior integration
    from unittest.mock import patch

    with patch('plorp.integrations.taskwarrior.get_task_info') as mock_get_info, \
         patch('plorp.integrations.taskwarrior.mark_done') as mock_mark_done:

        mock_get_info.return_value = {
            "uuid": "task-xyz-789",
            "description": "Buy milk",
            "status": "pending"
        }

        # Run Step 2 with vault_path for State Sync
        result = process_daily_note_step2(note_path, date(2025, 10, 7), tmp_path)

        # Assert: Task was marked done
        mock_mark_done.assert_called_once_with("task-xyz-789")

        # Assert: UUID was removed from project frontmatter
        from plorp.core.projects import get_project_info
        project = get_project_info("home.chores.groceries")
        assert project is not None
        assert "task-xyz-789" not in project["task_uuids"]
