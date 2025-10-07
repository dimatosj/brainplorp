"""
plorp.core - Pure business logic layer.

This module contains pure functions that implement plorp's core workflows.
Functions in this module:
- Return structured data (TypedDict)
- Raise specific exceptions
- Do not perform I/O decisions (no printing, no prompting)
- Are fully typed with type hints

The core layer is used by both MCP server and CLI interfaces.
"""

# Types
from plorp.core.types import (
    TaskInfo,
    TaskSummary,
    DailyStartResult,
    ReviewData,
    ReviewResult,
    InboxItem,
    InboxData,
    InboxProcessResult,
    NoteCreateResult,
    NoteLinkResult,
    TaskCompleteResult,
    TaskDeferResult,
    TaskDropResult,
)

# Exceptions
from plorp.core.exceptions import (
    PlorpError,
    VaultNotFoundError,
    DailyNoteExistsError,
    DailyNoteNotFoundError,
    TaskNotFoundError,
    NoteNotFoundError,
    NoteOutsideVaultError,
    InboxNotFoundError,
)

# Workflow functions
from plorp.core.daily import start_day
from plorp.core.review import get_review_tasks, add_review_notes
from plorp.core.tasks import mark_completed, defer_task, drop_task, set_priority
from plorp.core.inbox import (
    get_inbox_items,
    create_task_from_inbox,
    create_note_from_inbox,
    create_both_from_inbox,
    discard_inbox_item,
)
from plorp.core.notes import (
    create_note_standalone,
    create_note_linked_to_task,
    link_note_to_task,
)

__all__ = [
    # Types
    "TaskInfo",
    "TaskSummary",
    "DailyStartResult",
    "ReviewData",
    "ReviewResult",
    "InboxItem",
    "InboxData",
    "InboxProcessResult",
    "NoteCreateResult",
    "NoteLinkResult",
    "TaskCompleteResult",
    "TaskDeferResult",
    "TaskDropResult",
    # Exceptions
    "PlorpError",
    "VaultNotFoundError",
    "DailyNoteExistsError",
    "DailyNoteNotFoundError",
    "TaskNotFoundError",
    "NoteNotFoundError",
    "NoteOutsideVaultError",
    "InboxNotFoundError",
    # Functions
    "start_day",
    "get_review_tasks",
    "add_review_notes",
    "mark_completed",
    "defer_task",
    "drop_task",
    "set_priority",
    "get_inbox_items",
    "create_task_from_inbox",
    "create_note_from_inbox",
    "create_both_from_inbox",
    "discard_inbox_item",
    "create_note_standalone",
    "create_note_linked_to_task",
    "link_note_to_task",
]
