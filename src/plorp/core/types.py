"""
Type definitions for plorp core module.

All core functions return TypedDict structures for maximum compatibility
with JSON serialization (for MCP) and Python type checking.

Requires Python 3.10+ for native union syntax.
"""

from typing import TypedDict, Literal


# ============================================================================
# Task Types
# ============================================================================


class TaskInfo(TypedDict):
    """Information about a TaskWarrior task."""

    uuid: str
    description: str
    status: Literal["pending", "completed", "deleted", "missing"]
    due: str | None
    priority: Literal["H", "M", "L", ""] | None
    project: str | None
    tags: list[str]
    urgency: float


class TaskSummary(TypedDict):
    """Summary of task counts for a daily note."""

    overdue_count: int
    due_today_count: int
    recurring_count: int
    total_count: int


class TaskCompleteResult(TypedDict):
    """Result of marking a task as completed."""

    uuid: str
    description: str
    completed_at: str


class TaskDeferResult(TypedDict):
    """Result of deferring a task to a new date."""

    uuid: str
    description: str
    old_due: str | None
    new_due: str


class TaskDropResult(TypedDict):
    """Result of dropping/deleting a task."""

    uuid: str
    description: str
    deleted_at: str


class TaskPriorityResult(TypedDict):
    """Result of setting task priority."""

    uuid: str
    description: str
    priority: str | None


# ============================================================================
# Daily Workflow Types
# ============================================================================


class DailyStartResult(TypedDict):
    """Result of starting a daily note."""

    note_path: str
    created_at: str
    date: str
    summary: TaskSummary
    tasks: list[TaskInfo]


# ============================================================================
# Review Workflow Types
# ============================================================================


class ReviewData(TypedDict):
    """Data for reviewing uncompleted tasks."""

    date: str
    daily_note_path: str
    uncompleted_tasks: list[TaskInfo]
    total_tasks: int
    uncompleted_count: int


class ReviewResult(TypedDict):
    """Result of adding review notes to daily note."""

    daily_note_path: str
    review_added_at: str
    reflections: dict[str, str]


# ============================================================================
# Inbox Workflow Types
# ============================================================================


class InboxItem(TypedDict):
    """A single unprocessed inbox item."""

    text: str
    line_number: int


class InboxData(TypedDict):
    """Data about inbox items."""

    inbox_path: str
    unprocessed_items: list[InboxItem]
    item_count: int


class InboxProcessResult(TypedDict):
    """Result of processing an inbox item."""

    item_text: str
    action: Literal["task", "note", "both", "discard"]
    task_uuid: str | None
    note_path: str | None


# ============================================================================
# Note Workflow Types
# ============================================================================


class NoteCreateResult(TypedDict):
    """Result of creating a note."""

    note_path: str
    created_at: str
    title: str
    linked_task_uuid: str | None


class NoteLinkResult(TypedDict):
    """Result of linking a note to a task."""

    note_path: str
    task_uuid: str
    linked_at: str


# ============================================================================
# Process Workflow Types (Sprint 7)
# ============================================================================


class InformalTask(TypedDict):
    """An informal task (checkbox without UUID) found in daily note."""

    text: str  # Raw task text (without checkbox marker)
    line_number: int  # Line in original document (0-indexed)
    section: str  # Section name where found
    checkbox_state: str  # "[ ]" or "[x]"
    original_line: str  # Complete original line for removal (Q21)


class TaskProposal(TypedDict):
    """Proposed TaskWarrior task from informal task with NLP parsing."""

    informal_task: InformalTask
    proposed_description: str
    proposed_due: str | None  # YYYY-MM-DD format
    proposed_priority: Literal["H", "M", "L"]
    proposed_project: str | None  # Future (Sprint 8+)
    proposed_tags: list[str]  # Future (Sprint 8+)
    priority_reason: str | None  # e.g., "detected 'urgent'"
    needs_review: bool  # True if parsing failed
    review_reason: str | None  # e.g., "Invalid date format"


class ProcessError(TypedDict):
    """Error encountered during task processing."""

    proposal: TaskProposal
    error_message: str
    needs_review: bool


class ProcessStepOneResult(TypedDict):
    """Result of Step 1: scanning and proposal generation."""

    proposals_count: int
    needs_review_count: int
    tbd_section_content: str


class ProcessStepTwoResult(TypedDict):
    """Result of Step 2: task creation and note reorganization."""

    created_tasks: list[TaskInfo]
    approved_count: int
    rejected_count: int
    errors: list[ProcessError]
    needs_review_remaining: bool


# ============================================================================
# Project Management Types (Sprint 8)
# ============================================================================


class ProjectInfo(TypedDict):
    """Project metadata from Obsidian note frontmatter."""

    domain: str  # work/home/personal
    workstream: str | None  # Area of responsibility
    project_name: str  # Project identifier
    full_path: str  # Full TaskWarrior project path
    state: Literal["active", "planning", "completed", "blocked", "archived"]
    created_at: str  # ISO timestamp
    description: str | None  # Short description
    task_uuids: list[str]  # Linked TaskWarrior task UUIDs
    needs_review: bool  # True if missing workstream
    tags: list[str]  # Tags for filtering
    note_path: str  # Path to project note


class ProjectListResult(TypedDict):
    """Result from list_projects()."""

    projects: list[ProjectInfo]
    grouped_by_domain: dict[str, list[ProjectInfo]]  # Grouped by domain
