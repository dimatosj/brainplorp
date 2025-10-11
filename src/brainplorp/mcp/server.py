"""
plorp MCP Server.

Model Context Protocol server exposing plorp workflows to Claude Desktop.
All tools are async wrappers around synchronous core functions.

Q19: Config loaded once on startup, cached for all tool calls.
Q25: Errors logged to ~/.config/plorp/mcp.log for debugging.
"""

import logging
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from brainplorp.config import load_config
from brainplorp.core import (
    # Workflows
    start_day,
    get_review_tasks,
    add_review_notes,
    mark_completed,
    defer_task,
    drop_task,
    set_priority,
    get_inbox_items,
    create_task_from_inbox,
    create_note_from_inbox,
    create_both_from_inbox,
    discard_inbox_item,
    create_note_standalone,
    create_note_linked_to_task,
    link_note_to_task,
    # Exceptions
    PlorpError,
)
from brainplorp.core.process import process_daily_note_step1, process_daily_note_step2
from brainplorp.core.projects import (
    # Project management (Sprint 8)
    create_project,
    list_projects,
    get_project_info,
    update_project_state,
    delete_project,
    create_task_in_project,
    list_project_tasks,
    get_focused_domain_mcp,
    set_focused_domain_mcp,
    # Sprint 8.6
    sync_all_projects,
)
from brainplorp.core.note_operations import (
    # Note management (Sprint 9)
    read_note,
    read_folder,
    append_to_note,
    update_note_section,
    search_notes_by_metadata,
    create_note_in_folder,
    list_vault_folders,
)
from brainplorp.parsers.note_structure import (
    # Pattern matching (Sprint 9 Phase 2)
    extract_headers,
    find_header_content,
    detect_project_headers,
    extract_bullet_points,
)
from brainplorp.integrations.taskwarrior import get_task_info as tw_get_task_info


logger = logging.getLogger("plorp.mcp")
logger.addHandler(logging.NullHandler())

# Initialize MCP server
app = Server("plorp")

# Q19: Load config once on startup, cache vault_path
_config = load_config()
_vault_path = Path(_config["vault_path"]).expanduser().resolve()


def _get_vault_path() -> Path:
    """Get cached vault path."""
    return _vault_path


# ============================================================================
# Daily Workflow Tools
# ============================================================================


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available plorp tools."""
    return [
        Tool(
            name="plorp_start_day",
            description="Generate daily note with tasks from TaskWarrior. Creates markdown file with overdue, due today, and recurring tasks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date for daily note in YYYY-MM-DD format (defaults to today)",
                    }
                },
            },
        ),
        Tool(
            name="plorp_get_review_tasks",
            description="Get uncompleted tasks from daily note for end-of-day review. Returns tasks that were not completed during the day.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date to review in YYYY-MM-DD format (defaults to today)",
                    }
                },
                "required": [],
            },
        ),
        Tool(
            name="plorp_add_review_notes",
            description="Add reflection notes to daily note after review. Appends review section with reflections on what went well, what could improve, and notes for tomorrow.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date to add review for in YYYY-MM-DD format (defaults to today)",
                    },
                    "went_well": {
                        "type": "string",
                        "description": "What went well today",
                    },
                    "could_improve": {
                        "type": "string",
                        "description": "What could be improved",
                    },
                    "tomorrow": {
                        "type": "string",
                        "description": "Notes for tomorrow",
                    },
                },
            },
        ),
        Tool(
            name="plorp_mark_task_completed",
            description="Mark a task as completed in TaskWarrior. Updates task status to done.",
            inputSchema={
                "type": "object",
                "properties": {
                    "uuid": {
                        "type": "string",
                        "description": "Task UUID",
                    }
                },
                "required": ["uuid"],
            },
        ),
        Tool(
            name="plorp_defer_task",
            description="Defer a task to a new due date. Updates the task's due date in TaskWarrior.",
            inputSchema={
                "type": "object",
                "properties": {
                    "uuid": {
                        "type": "string",
                        "description": "Task UUID",
                    },
                    "new_due": {
                        "type": "string",
                        "description": "New due date in YYYY-MM-DD format",
                    },
                },
                "required": ["uuid", "new_due"],
            },
        ),
        Tool(
            name="plorp_drop_task",
            description="Drop/delete a task from TaskWarrior. Permanently removes the task.",
            inputSchema={
                "type": "object",
                "properties": {
                    "uuid": {
                        "type": "string",
                        "description": "Task UUID",
                    }
                },
                "required": ["uuid"],
            },
        ),
        Tool(
            name="plorp_set_task_priority",
            description="Set task priority. Updates priority level (H=High, M=Medium, L=Low, empty string=None).",
            inputSchema={
                "type": "object",
                "properties": {
                    "uuid": {
                        "type": "string",
                        "description": "Task UUID",
                    },
                    "priority": {
                        "type": "string",
                        "description": "Priority: H, M, L, or empty string for none",
                    },
                },
                "required": ["uuid", "priority"],
            },
        ),
        Tool(
            name="plorp_get_inbox_items",
            description="Get unprocessed items from inbox file. Returns list of items waiting to be processed from monthly inbox file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date for inbox file in YYYY-MM-DD format (defaults to current month)",
                    }
                },
            },
        ),
        Tool(
            name="plorp_create_task_from_inbox",
            description="Create TaskWarrior task from inbox item. Creates task and marks inbox item as processed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_text": {
                        "type": "string",
                        "description": "Original inbox item text to mark as processed",
                    },
                    "description": {
                        "type": "string",
                        "description": "Task description",
                    },
                    "due": {
                        "type": "string",
                        "description": "Due date (YYYY-MM-DD format, optional)",
                    },
                    "priority": {
                        "type": "string",
                        "description": "Priority (H/M/L, optional)",
                    },
                    "project": {
                        "type": "string",
                        "description": "Project name (optional)",
                    },
                },
                "required": ["item_text", "description"],
            },
        ),
        Tool(
            name="plorp_create_note_from_inbox",
            description="Create Obsidian note from inbox item. Creates note and marks inbox item as processed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_text": {
                        "type": "string",
                        "description": "Original inbox item text to mark as processed",
                    },
                    "title": {
                        "type": "string",
                        "description": "Note title",
                    },
                    "content": {
                        "type": "string",
                        "description": "Note content (optional)",
                    },
                    "note_type": {
                        "type": "string",
                        "description": "Note type: general, meeting, etc. (optional, defaults to general)",
                    },
                },
                "required": ["item_text", "title"],
            },
        ),
        Tool(
            name="plorp_create_both_from_inbox",
            description="Create both task and note from inbox item, linked together. Creates task, creates note, links them bidirectionally, and marks inbox item as processed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_text": {
                        "type": "string",
                        "description": "Original inbox item text",
                    },
                    "task_description": {
                        "type": "string",
                        "description": "Task description",
                    },
                    "note_title": {
                        "type": "string",
                        "description": "Note title",
                    },
                    "note_content": {
                        "type": "string",
                        "description": "Note content (optional)",
                    },
                    "due": {
                        "type": "string",
                        "description": "Task due date (YYYY-MM-DD, optional)",
                    },
                    "priority": {
                        "type": "string",
                        "description": "Task priority (H/M/L, optional)",
                    },
                    "project": {
                        "type": "string",
                        "description": "Task project (optional)",
                    },
                },
                "required": ["item_text", "task_description", "note_title"],
            },
        ),
        Tool(
            name="plorp_discard_inbox_item",
            description="Discard inbox item without creating anything. Marks item as processed with 'Discarded' annotation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_text": {
                        "type": "string",
                        "description": "Inbox item text to discard",
                    }
                },
                "required": ["item_text"],
            },
        ),
        Tool(
            name="plorp_create_note",
            description="Create standalone note in Obsidian vault. Creates note without linking to any task.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Note title",
                    },
                    "content": {
                        "type": "string",
                        "description": "Note content (optional)",
                    },
                    "note_type": {
                        "type": "string",
                        "description": "Note type: general, meeting, etc. (optional, defaults to general)",
                    },
                },
                "required": ["title"],
            },
        ),
        Tool(
            name="plorp_create_note_with_task",
            description="Create note linked to existing task. Creates note and establishes bidirectional link with task.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Note title",
                    },
                    "task_uuid": {
                        "type": "string",
                        "description": "Task UUID to link to",
                    },
                    "content": {
                        "type": "string",
                        "description": "Note content (optional)",
                    },
                    "note_type": {
                        "type": "string",
                        "description": "Note type (optional, defaults to general)",
                    },
                },
                "required": ["title", "task_uuid"],
            },
        ),
        Tool(
            name="plorp_link_note_to_task",
            description="Link existing note to existing task. Creates bidirectional link between note and task.",
            inputSchema={
                "type": "object",
                "properties": {
                    "note_path": {
                        "type": "string",
                        "description": "Path to note file (absolute or relative to vault)",
                    },
                    "task_uuid": {
                        "type": "string",
                        "description": "Task UUID",
                    },
                },
                "required": ["note_path", "task_uuid"],
            },
        ),
        Tool(
            name="plorp_get_task_info",
            description="Get detailed information about a task from TaskWarrior. Returns full task data including description, status, due date, priority, project, and tags.",
            inputSchema={
                "type": "object",
                "properties": {
                    "uuid": {
                        "type": "string",
                        "description": "Task UUID",
                    }
                },
                "required": ["uuid"],
            },
        ),
        Tool(
            name="plorp_process_daily_note",
            description="Process informal tasks in daily note. Two-step workflow: (1) If no TBD section exists, scan for informal tasks (checkboxes without UUIDs), parse natural language dates/priority, generate proposals in TBD section. (2) If TBD section exists, parse [Y]/[N] approvals, create TaskWarrior tasks from approved proposals, reorganize note.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date for daily note in YYYY-MM-DD format (defaults to today)",
                    }
                },
            },
        ),
        # ====================================================================
        # Project Management Tools (Sprint 8)
        # ====================================================================
        Tool(
            name="plorp_create_project",
            description="Create new project in vault/projects/ with YAML frontmatter. Projects organize tasks into domain.workstream.project hierarchy (e.g., work.marketing.website).",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Project name (e.g., 'website-redesign')",
                    },
                    "domain": {
                        "type": "string",
                        "description": "Domain (work/home/personal)",
                        "enum": ["work", "home", "personal"],
                    },
                    "workstream": {
                        "type": "string",
                        "description": "Workstream/area (e.g., 'marketing', 'engineering') - optional",
                    },
                    "state": {
                        "type": "string",
                        "description": "Project state (default: active)",
                        "enum": ["active", "planning", "completed", "blocked", "archived"],
                    },
                    "description": {
                        "type": "string",
                        "description": "Short project description - optional",
                    },
                },
                "required": ["name", "domain"],
            },
        ),
        Tool(
            name="plorp_list_projects",
            description="List all projects with optional filtering by domain or state. Returns projects with metadata and task counts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Filter by domain (optional)",
                        "enum": ["work", "home", "personal"],
                    },
                    "state": {
                        "type": "string",
                        "description": "Filter by state (optional)",
                        "enum": ["active", "planning", "completed", "blocked", "archived"],
                    },
                },
            },
        ),
        Tool(
            name="plorp_get_project_info",
            description="Get detailed information about a specific project including tasks, state, and metadata.",
            inputSchema={
                "type": "object",
                "properties": {
                    "full_path": {
                        "type": "string",
                        "description": "Full project path (e.g., 'work.marketing.website')",
                    },
                },
                "required": ["full_path"],
            },
        ),
        Tool(
            name="plorp_update_project_state",
            description="Update project state (e.g., mark as completed or blocked).",
            inputSchema={
                "type": "object",
                "properties": {
                    "full_path": {
                        "type": "string",
                        "description": "Full project path",
                    },
                    "state": {
                        "type": "string",
                        "description": "New state",
                        "enum": ["active", "planning", "completed", "blocked", "archived"],
                    },
                },
                "required": ["full_path", "state"],
            },
        ),
        Tool(
            name="plorp_delete_project",
            description="Delete a project note. Note: This does NOT delete associated tasks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "full_path": {
                        "type": "string",
                        "description": "Full project path to delete",
                    },
                },
                "required": ["full_path"],
            },
        ),
        Tool(
            name="plorp_create_task_in_project",
            description="Create a new task in TaskWarrior and link it to a project bidirectionally.",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Task description",
                    },
                    "project_full_path": {
                        "type": "string",
                        "description": "Full project path (e.g., 'work.marketing.website')",
                    },
                    "due": {
                        "type": "string",
                        "description": "Due date (optional, TaskWarrior format like 'friday', '2025-10-10')",
                    },
                    "priority": {
                        "type": "string",
                        "description": "Priority (optional)",
                        "enum": ["H", "M", "L"],
                    },
                },
                "required": ["description", "project_full_path"],
            },
        ),
        Tool(
            name="plorp_list_project_tasks",
            description="List all tasks for a specific project. Warns if project has orphaned task references.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_full_path": {
                        "type": "string",
                        "description": "Full project path",
                    },
                },
                "required": ["project_full_path"],
            },
        ),
        Tool(
            name="plorp_set_focused_domain",
            description="Set focused domain for this MCP conversation. Commands will default to this domain. Note: This is conversation-scoped and persists across MCP server restarts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Domain to focus on",
                        "enum": ["work", "home", "personal"],
                    },
                },
                "required": ["domain"],
            },
        ),
        Tool(
            name="plorp_get_focused_domain",
            description="Get current focused domain for this conversation.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # ====================================================================
        # Sprint 8.6: State Synchronization Tools
        # ====================================================================
        Tool(
            name="plorp_sync_all_projects",
            description="Sync all project note bodies with frontmatter (Sprint 8.6). Bulk reconciliation command that updates Tasks sections across all project notes to match their task_uuids. Useful after external TaskWarrior modifications.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # ====================================================================
        # Sprint 9: General Note Management Tools
        # ====================================================================
        Tool(
            name="plorp_read_note",
            description="Read any markdown note in vault. Returns content with metadata, headers, word count. Supports different modes: full (entire content), preview (first 1000 chars), metadata (frontmatter only), structure (headers only).",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to note (e.g., 'notes/ideas.md', 'Docs/spec.md')",
                    },
                    "mode": {
                        "type": "string",
                        "description": "Content mode: full, preview, metadata, or structure (default: full)",
                        "enum": ["full", "preview", "metadata", "structure"],
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="plorp_read_folder",
            description="Read all notes in folder with filtering. Returns list of notes with metadata. Useful for exploring vault structure or finding notes in specific locations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative folder path (e.g., 'notes', 'Docs')",
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Include subdirectories (default: false)",
                    },
                    "exclude": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Folder names to skip (e.g., ['archive', 'templates'])",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Max notes to return (default: 10, max: 50)",
                    },
                    "mode": {
                        "type": "string",
                        "description": "Content mode for each note (default: metadata)",
                        "enum": ["full", "preview", "metadata", "structure"],
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="plorp_append_to_note",
            description="Append content to end of note. Adds content with proper spacing (blank line separator). Useful for adding notes, observations, or updates to existing documents.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to note",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to append",
                    },
                },
                "required": ["path", "content"],
            },
        ),
        Tool(
            name="plorp_update_note_section",
            description="Replace content under specific header. Updates section between header and next same-level header. Useful for updating specific parts of structured documents.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to note",
                    },
                    "header": {
                        "type": "string",
                        "description": "Header text (without ## prefix)",
                    },
                    "content": {
                        "type": "string",
                        "description": "New content for section",
                    },
                },
                "required": ["path", "header", "content"],
            },
        ),
        Tool(
            name="plorp_search_notes_by_tag",
            description="Find notes with specific tag in frontmatter. Returns list of matching notes with metadata. Useful for finding all notes on a topic.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "Tag to search for (e.g., 'SEO', 'project', 'meeting')",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Max results (default: 20)",
                    },
                },
                "required": ["tag"],
            },
        ),
        Tool(
            name="plorp_search_notes_by_field",
            description="Find notes by frontmatter field value. Returns list of matching notes. Useful for finding notes with specific metadata (status, category, etc).",
            inputSchema={
                "type": "object",
                "properties": {
                    "field": {
                        "type": "string",
                        "description": "Frontmatter field name (e.g., 'status', 'category', 'author')",
                    },
                    "value": {
                        "type": "string",
                        "description": "Value to match",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Max results (default: 20)",
                    },
                },
                "required": ["field", "value"],
            },
        ),
        Tool(
            name="plorp_create_note_in_folder",
            description="Create note in any vault folder. Creates note with optional frontmatter metadata. Folder will be created if it doesn't exist.",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder": {
                        "type": "string",
                        "description": "Target folder path (e.g., 'notes', 'Docs', 'projects/work')",
                    },
                    "title": {
                        "type": "string",
                        "description": "Note title (filename will be title.md)",
                    },
                    "content": {
                        "type": "string",
                        "description": "Note body content (optional)",
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Frontmatter fields as key-value pairs (optional)",
                    },
                },
                "required": ["folder", "title"],
            },
        ),
        Tool(
            name="plorp_list_vault_folders",
            description="Get vault directory structure. Returns allowed folders, excluded folders, and list of all folders in vault. Useful for understanding vault organization.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # ====================================================================
        # Sprint 9 Phase 2: Pattern Matching Tools
        # ====================================================================
        Tool(
            name="plorp_extract_headers",
            description="Extract all headers from note content. Returns list of headers with text, level (1-6), and line numbers. Useful for understanding document structure.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Markdown content to parse",
                    },
                    "level": {
                        "type": "number",
                        "description": "Filter by header level (1-6), omit for all levels",
                    },
                },
                "required": ["content"],
            },
        ),
        Tool(
            name="plorp_get_section_content",
            description="Get content under specific header (until next same-level header). Returns section content as string. Useful for extracting specific parts of notes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Markdown content to parse",
                    },
                    "header": {
                        "type": "string",
                        "description": "Header text to find (without # prefix)",
                    },
                },
                "required": ["content", "header"],
            },
        ),
        Tool(
            name="plorp_detect_projects_in_note",
            description="Find ### headers that look like project names using heuristics. Returns list of potential project names. Useful for discovering projects mentioned in daily notes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Markdown content to analyze (typically from daily note)",
                    },
                },
                "required": ["content"],
            },
        ),
        Tool(
            name="plorp_extract_bullets",
            description="Extract bullet points from content, optionally from specific section. Returns list of bullet text. Useful for collecting tasks, notes, or ideas.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Markdown content to parse",
                    },
                    "section": {
                        "type": "string",
                        "description": "Header name to extract bullets from (optional, omit for all bullets)",
                    },
                },
                "required": ["content"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    """
    Handle MCP tool calls.

    All tools return JSON-serialized results wrapped in TextContent.
    Exceptions are caught and converted to ValueError per Q3 decision.
    """
    try:
        if name == "plorp_start_day":
            return await _plorp_start_day(arguments)
        elif name == "plorp_get_review_tasks":
            return await _plorp_get_review_tasks(arguments)
        elif name == "plorp_add_review_notes":
            return await _plorp_add_review_notes(arguments)
        elif name == "plorp_mark_task_completed":
            return await _plorp_mark_task_completed(arguments)
        elif name == "plorp_defer_task":
            return await _plorp_defer_task(arguments)
        elif name == "plorp_drop_task":
            return await _plorp_drop_task(arguments)
        elif name == "plorp_set_task_priority":
            return await _plorp_set_task_priority(arguments)
        elif name == "plorp_get_inbox_items":
            return await _plorp_get_inbox_items(arguments)
        elif name == "plorp_create_task_from_inbox":
            return await _plorp_create_task_from_inbox(arguments)
        elif name == "plorp_create_note_from_inbox":
            return await _plorp_create_note_from_inbox(arguments)
        elif name == "plorp_create_both_from_inbox":
            return await _plorp_create_both_from_inbox(arguments)
        elif name == "plorp_discard_inbox_item":
            return await _plorp_discard_inbox_item(arguments)
        elif name == "plorp_create_note":
            return await _plorp_create_note(arguments)
        elif name == "plorp_create_note_with_task":
            return await _plorp_create_note_with_task(arguments)
        elif name == "plorp_link_note_to_task":
            return await _plorp_link_note_to_task(arguments)
        elif name == "plorp_get_task_info":
            return await _plorp_get_task_info(arguments)
        elif name == "plorp_process_daily_note":
            return await _plorp_process_daily_note(arguments)
        # Project management tools (Sprint 8)
        elif name == "plorp_create_project":
            return await _plorp_create_project(arguments)
        elif name == "plorp_list_projects":
            return await _plorp_list_projects(arguments)
        elif name == "plorp_get_project_info":
            return await _plorp_get_project_info(arguments)
        elif name == "plorp_update_project_state":
            return await _plorp_update_project_state(arguments)
        elif name == "plorp_delete_project":
            return await _plorp_delete_project(arguments)
        elif name == "plorp_create_task_in_project":
            return await _plorp_create_task_in_project(arguments)
        elif name == "plorp_list_project_tasks":
            return await _plorp_list_project_tasks(arguments)
        elif name == "plorp_set_focused_domain":
            return await _plorp_set_focused_domain(arguments)
        elif name == "plorp_get_focused_domain":
            return await _plorp_get_focused_domain(arguments)
        # Sprint 8.6: State sync tools
        elif name == "plorp_sync_all_projects":
            return await _plorp_sync_all_projects(arguments)
        # Sprint 9: Note management tools
        elif name == "plorp_read_note":
            return await _plorp_read_note(arguments)
        elif name == "plorp_read_folder":
            return await _plorp_read_folder(arguments)
        elif name == "plorp_append_to_note":
            return await _plorp_append_to_note(arguments)
        elif name == "plorp_update_note_section":
            return await _plorp_update_note_section(arguments)
        elif name == "plorp_search_notes_by_tag":
            return await _plorp_search_notes_by_tag(arguments)
        elif name == "plorp_search_notes_by_field":
            return await _plorp_search_notes_by_field(arguments)
        elif name == "plorp_create_note_in_folder":
            return await _plorp_create_note_in_folder(arguments)
        elif name == "plorp_list_vault_folders":
            return await _plorp_list_vault_folders(arguments)
        # Sprint 9 Phase 2: Pattern matching tools
        elif name == "plorp_extract_headers":
            return await _plorp_extract_headers(arguments)
        elif name == "plorp_get_section_content":
            return await _plorp_get_section_content(arguments)
        elif name == "plorp_detect_projects_in_note":
            return await _plorp_detect_projects_in_note(arguments)
        elif name == "plorp_extract_bullets":
            return await _plorp_extract_bullets(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    except PlorpError as e:
        # Q3: Convert exceptions to ValueError for MCP
        # Q13: Technical error messages (factual, actionable)
        logger.error(f"Tool {name} failed: {e}", exc_info=True)
        raise ValueError(str(e))
    except Exception as e:
        logger.error(f"Tool {name} unexpected error: {e}", exc_info=True)
        raise ValueError(f"Unexpected error: {e}")


# ============================================================================
# Tool Implementations
# ============================================================================


async def _plorp_start_day(args: Dict[str, Any]) -> list[TextContent]:
    """Generate daily note."""
    target_date = date.fromisoformat(args["date"]) if "date" in args else date.today()
    vault = _get_vault_path()

    result = start_day(target_date, vault)

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_get_review_tasks(args: Dict[str, Any]) -> list[TextContent]:
    """Get review tasks."""
    target_date = date.fromisoformat(args["date"]) if "date" in args else date.today()
    vault = _get_vault_path()

    result = get_review_tasks(target_date, vault)

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_add_review_notes(args: Dict[str, Any]) -> list[TextContent]:
    """Add review notes."""
    target_date = date.fromisoformat(args["date"]) if "date" in args else date.today()
    vault = _get_vault_path()

    reflections = {
        "went_well": args.get("went_well", ""),
        "could_improve": args.get("could_improve", ""),
        "tomorrow": args.get("tomorrow", ""),
    }

    result = add_review_notes(target_date, vault, reflections)

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_mark_task_completed(args: Dict[str, Any]) -> list[TextContent]:
    """Mark task completed."""
    # Sprint 8.5: Pass vault_path for State Sync
    vault = _get_vault_path()
    result = mark_completed(args["uuid"], vault_path=vault)

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_defer_task(args: Dict[str, Any]) -> list[TextContent]:
    """Defer task."""
    new_due = date.fromisoformat(args["new_due"])
    result = defer_task(args["uuid"], new_due)

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_drop_task(args: Dict[str, Any]) -> list[TextContent]:
    """Drop task."""
    # Sprint 8.5: Pass vault_path for State Sync
    vault = _get_vault_path()
    result = drop_task(args["uuid"], vault_path=vault)

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_set_task_priority(args: Dict[str, Any]) -> list[TextContent]:
    """Set task priority."""
    result = set_priority(args["uuid"], args["priority"])

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_get_inbox_items(args: Dict[str, Any]) -> list[TextContent]:
    """Get inbox items."""
    target_date = date.fromisoformat(args["date"]) if "date" in args else None
    vault = _get_vault_path()

    result = get_inbox_items(vault, target_date)

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_create_task_from_inbox(args: Dict[str, Any]) -> list[TextContent]:
    """Create task from inbox."""
    vault = _get_vault_path()

    result = create_task_from_inbox(
        vault,
        args["item_text"],
        args["description"],
        due=args.get("due"),
        priority=args.get("priority"),
        project=args.get("project"),
    )

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_create_note_from_inbox(args: Dict[str, Any]) -> list[TextContent]:
    """Create note from inbox."""
    vault = _get_vault_path()

    result = create_note_from_inbox(
        vault,
        args["item_text"],
        args["title"],
        content=args.get("content", ""),
        note_type=args.get("note_type", "general"),
    )

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_create_both_from_inbox(args: Dict[str, Any]) -> list[TextContent]:
    """Create both task and note from inbox."""
    vault = _get_vault_path()

    result = create_both_from_inbox(
        vault,
        args["item_text"],
        args["task_description"],
        args["note_title"],
        note_content=args.get("note_content", ""),
        due=args.get("due"),
        priority=args.get("priority"),
        project=args.get("project"),
    )

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_discard_inbox_item(args: Dict[str, Any]) -> list[TextContent]:
    """Discard inbox item."""
    vault = _get_vault_path()

    result = discard_inbox_item(vault, args["item_text"])

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_create_note(args: Dict[str, Any]) -> list[TextContent]:
    """Create standalone note."""
    vault = _get_vault_path()

    result = create_note_standalone(
        vault,
        args["title"],
        note_type=args.get("note_type", "general"),
        content=args.get("content", ""),
    )

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_create_note_with_task(args: Dict[str, Any]) -> list[TextContent]:
    """Create note linked to task."""
    vault = _get_vault_path()

    result = create_note_linked_to_task(
        vault,
        args["title"],
        args["task_uuid"],
        note_type=args.get("note_type", "general"),
        content=args.get("content", ""),
    )

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_link_note_to_task(args: Dict[str, Any]) -> list[TextContent]:
    """Link note to task."""
    vault = _get_vault_path()
    note_path = Path(args["note_path"])

    # Handle relative paths
    if not note_path.is_absolute():
        note_path = vault / note_path

    result = link_note_to_task(vault, note_path, args["task_uuid"])

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_get_task_info(args: Dict[str, Any]) -> list[TextContent]:
    """Get task info."""
    task = tw_get_task_info(args["uuid"])

    if not task:
        raise ValueError(f"Task not found: {args['uuid']}")

    import json
    return [TextContent(type="text", text=json.dumps(task, indent=2))]


async def _plorp_process_daily_note(args: Dict[str, Any]) -> list[TextContent]:
    """
    Process informal tasks in daily note.

    Auto-detects which step to run:
    - No TBD section → Step 1 (generate proposals)
    - TBD section exists → Step 2 (create tasks)
    """
    target_date = date.fromisoformat(args["date"]) if "date" in args else date.today()
    vault = _get_vault_path()

    # Construct daily note path
    daily_dir = vault / "daily"
    note_path = daily_dir / f"{target_date}.md"

    # Check if note exists
    if not note_path.exists():
        raise ValueError(f"Daily note not found: {note_path}. Run plorp_start_day first.")

    # Read note to check for TBD section
    content = note_path.read_text()
    has_tbd_section = "## TBD Processing" in content

    if has_tbd_section:
        # Step 2: Create tasks from approvals
        # Sprint 8.5: Pass vault for State Sync
        result = process_daily_note_step2(note_path, target_date, vault)

        # Build response message
        response = {
            "step": "2",
            "action": "created_tasks_from_approvals",
            "created_tasks": result["created_tasks"],
            "approved_count": result["approved_count"],
            "rejected_count": result["rejected_count"],
            "errors": result["errors"],
            "needs_review_remaining": result["needs_review_remaining"],
            "note_path": str(note_path),
        }
    else:
        # Step 1: Generate proposals
        result = process_daily_note_step1(note_path, target_date)

        # Build response message
        response = {
            "step": "1",
            "action": "generated_proposals",
            "proposals_count": result["proposals_count"],
            "needs_review_count": result["needs_review_count"],
            "note_path": str(note_path),
            "next_steps": "Review proposals in ## TBD Processing section, mark [Y] to approve or [N] to reject, then run plorp_process_daily_note again.",
        }

    import json
    return [TextContent(type="text", text=json.dumps(response, indent=2))]


# ============================================================================
# Server Entry Point
# ============================================================================


# ============================================================================
# Project Management Tool Implementations (Sprint 8)
# ============================================================================


async def _plorp_create_project(args: Dict[str, Any]) -> list[TextContent]:
    """Create project."""
    project = create_project(
        name=args["name"],
        domain=args["domain"],
        workstream=args.get("workstream"),
        state=args.get("state", "active"),
        description=args.get("description")
    )

    import json
    return [TextContent(type="text", text=json.dumps(project, indent=2))]


async def _plorp_list_projects(args: Dict[str, Any]) -> list[TextContent]:
    """List projects with optional filters."""
    result = list_projects(
        domain=args.get("domain"),
        state=args.get("state")
    )

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_get_project_info(args: Dict[str, Any]) -> list[TextContent]:
    """Get project info."""
    project = get_project_info(args["full_path"])

    if not project:
        raise ValueError(f"Project not found: {args['full_path']}")

    import json
    return [TextContent(type="text", text=json.dumps(project, indent=2))]


async def _plorp_update_project_state(args: Dict[str, Any]) -> list[TextContent]:
    """Update project state."""
    project = update_project_state(
        full_path=args["full_path"],
        state=args["state"]
    )

    import json
    return [TextContent(type="text", text=json.dumps(project, indent=2))]


async def _plorp_delete_project(args: Dict[str, Any]) -> list[TextContent]:
    """Delete project."""
    deleted = delete_project(args["full_path"])

    result = {
        "deleted": deleted,
        "full_path": args["full_path"]
    }

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_create_task_in_project(args: Dict[str, Any]) -> list[TextContent]:
    """Create task in project with bidirectional linking."""
    task_uuid = create_task_in_project(
        description=args["description"],
        project_full_path=args["project_full_path"],
        due=args.get("due"),
        priority=args.get("priority")
    )

    result = {
        "task_uuid": task_uuid,
        "project": args["project_full_path"]
    }

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_list_project_tasks(args: Dict[str, Any]) -> list[TextContent]:
    """List tasks for a project."""
    tasks = list_project_tasks(args["project_full_path"])

    result = {
        "tasks": tasks,
        "count": len(tasks),
        "project": args["project_full_path"]
    }

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_set_focused_domain(args: Dict[str, Any]) -> list[TextContent]:
    """Set focused domain for MCP conversation."""
    domain = args["domain"]
    set_focused_domain_mcp(domain)

    result = {
        "focused_domain": domain,
        "message": f"Focused on domain: {domain}. All commands will default to this domain."
    }

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_get_focused_domain(args: Dict[str, Any]) -> list[TextContent]:
    """Get current focused domain."""
    domain = get_focused_domain_mcp()

    result = {
        "focused_domain": domain,
        "is_default": domain == "home"
    }

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


# ============================================================================
# Sprint 8.6: State Synchronization Tool Implementations
# ============================================================================


async def _plorp_sync_all_projects(args: Dict[str, Any]) -> list[TextContent]:
    """
    Sync all project note bodies with frontmatter.

    Sprint 8.6: Bulk reconciliation after external TaskWarrior changes.
    Updates Tasks section in all project notes to match task_uuids.
    """
    vault = _get_vault_path()
    stats = sync_all_projects(vault)

    result = {
        "synced_count": stats["synced"],
        "errors_count": len(stats["errors"]),
        "errors": [
            {"project": project, "error": error}
            for project, error in stats["errors"]
        ]
    }

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


# ============================================================================
# Sprint 9: Note Management Tool Implementations
# ============================================================================


async def _plorp_read_note(args: Dict[str, Any]) -> list[TextContent]:
    """Read note."""
    vault = _get_vault_path()
    mode = args.get("mode", "full")

    result = read_note(vault, args["path"], mode)

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_read_folder(args: Dict[str, Any]) -> list[TextContent]:
    """Read folder."""
    vault = _get_vault_path()

    result = read_folder(
        vault,
        args["path"],
        recursive=args.get("recursive", False),
        exclude=args.get("exclude"),
        limit=args.get("limit", 10),
        mode=args.get("mode", "metadata"),
    )

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_append_to_note(args: Dict[str, Any]) -> list[TextContent]:
    """Append to note."""
    vault = _get_vault_path()

    append_to_note(vault, args["path"], args["content"])

    result = {
        "path": args["path"],
        "action": "appended",
        "message": f"Content appended to {args['path']}"
    }

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_update_note_section(args: Dict[str, Any]) -> list[TextContent]:
    """Update note section."""
    vault = _get_vault_path()

    update_note_section(vault, args["path"], args["header"], args["content"])

    result = {
        "path": args["path"],
        "header": args["header"],
        "action": "updated",
        "message": f"Section '{args['header']}' updated in {args['path']}"
    }

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_search_notes_by_tag(args: Dict[str, Any]) -> list[TextContent]:
    """Search notes by tag."""
    vault = _get_vault_path()
    limit = args.get("limit", 20)

    results = search_notes_by_metadata(vault, "tags", args["tag"], limit)

    result = {
        "tag": args["tag"],
        "count": len(results),
        "notes": results
    }

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_search_notes_by_field(args: Dict[str, Any]) -> list[TextContent]:
    """Search notes by field."""
    vault = _get_vault_path()
    limit = args.get("limit", 20)

    results = search_notes_by_metadata(vault, args["field"], args["value"], limit)

    result = {
        "field": args["field"],
        "value": args["value"],
        "count": len(results),
        "notes": results
    }

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_create_note_in_folder(args: Dict[str, Any]) -> list[TextContent]:
    """Create note in folder."""
    vault = _get_vault_path()

    note_path = create_note_in_folder(
        vault,
        args["folder"],
        args["title"],
        content=args.get("content", ""),
        metadata=args.get("metadata"),
    )

    result = {
        "path": str(note_path),
        "folder": args["folder"],
        "title": args["title"],
        "action": "created",
        "message": f"Note created at {note_path}"
    }

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_list_vault_folders(args: Dict[str, Any]) -> list[TextContent]:
    """List vault folders."""
    vault = _get_vault_path()

    result = list_vault_folders(vault)

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


# ============================================================================
# Sprint 9 Phase 2: Pattern Matching Tool Implementations
# ============================================================================


async def _plorp_extract_headers(args: Dict[str, Any]) -> list[TextContent]:
    """Extract headers from content."""
    headers = extract_headers(
        content=args["content"],
        level=args.get("level")
    )

    result = {
        "headers": headers,
        "count": len(headers)
    }

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_get_section_content(args: Dict[str, Any]) -> list[TextContent]:
    """Get section content by header."""
    section_content = find_header_content(
        content=args["content"],
        header=args["header"]
    )

    result = {
        "header": args["header"],
        "content": section_content,
        "found": bool(section_content)
    }

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_detect_projects_in_note(args: Dict[str, Any]) -> list[TextContent]:
    """Detect project headers in note."""
    projects = detect_project_headers(args["content"])

    result = {
        "projects": projects,
        "count": len(projects)
    }

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _plorp_extract_bullets(args: Dict[str, Any]) -> list[TextContent]:
    """Extract bullet points from content."""
    bullets = extract_bullet_points(
        content=args["content"],
        section=args.get("section")
    )

    result = {
        "bullets": bullets,
        "count": len(bullets),
        "section": args.get("section")
    }

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


# ============================================================================
# Server Entry Point
# ============================================================================


async def run_server():
    """Run MCP server via stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main():
    """Main entry point."""
    import asyncio

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
