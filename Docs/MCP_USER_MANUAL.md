# plorp MCP Server - User Manual

**Version:** 1.5.1
**Last Updated:** 2025-10-09

---

## Table of Contents

1. [Overview](#overview)
2. [Installation & Setup](#installation--setup)
3. [Available Tools](#available-tools)
4. [Daily Workflow](#daily-workflow)
5. [Inbox Processing](#inbox-processing)
6. [Project Management](#project-management)
7. [Note Management](#note-management)
8. [Vault Access & Note Reading](#vault-access--note-reading)
9. [Task Processing (/process)](#task-processing-process)
10. [Fast Task Queries](#fast-task-queries)
11. [Common Workflows](#common-workflows)
12. [Natural Language Examples](#natural-language-examples)
13. [Troubleshooting](#troubleshooting)
14. [Advanced Usage](#advanced-usage)

---

## Overview

The plorp MCP (Model Context Protocol) server enables Claude Desktop to interact with your TaskWarrior tasks and Obsidian vault through natural language.

**What You Can Do:**
- Generate daily notes with your tasks
- Process inbox items into tasks or notes
- Manage projects across work/home/personal domains
- Create and link notes to tasks
- Review and update task status
- Process informal tasks with natural language date parsing
- Read and analyze notes from your vault
- Search notes by tags and metadata
- Extract document structure and content
- Discover projects and bullet points in notes

**Architecture:**
```
Claude Desktop (MCP Client)
    ↕ (MCP Protocol)
plorp-mcp server
    ↕
TaskWarrior (tasks) + Obsidian (notes)
```

---

## Installation & Setup

### Prerequisites

1. **TaskWarrior 3.x** installed and configured
   ```bash
   task --version  # Should be 3.x
   ```

2. **Obsidian vault** set up
   ```bash
   # Default location
   ~/vault/

   # Or custom location in config
   ~/.config/plorp/config.yaml
   ```

3. **plorp installed**
   ```bash
   pip install -e /path/to/plorp
   # or
   uv sync
   ```

### MCP Server Configuration

**File:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "plorp": {
      "command": "/path/to/.venv/bin/plorp-mcp",
      "args": []
    }
  }
}
```

**Find your plorp-mcp path:**
```bash
which plorp-mcp
# or
/path/to/plorp/.venv/bin/plorp-mcp --version
```

### Verify Installation

1. Restart Claude Desktop
2. In Claude, say: "List the plorp MCP tools available"
3. You should see 38 tools listed

---

## Available Tools

### Daily Workflow (3 tools)

| Tool | Purpose | Required Args |
|------|---------|---------------|
| `plorp_start_day` | Generate daily note with tasks | `date` (optional) |
| `plorp_get_review_tasks` | Get uncompleted tasks for review | `date` (optional) |
| `plorp_add_review_notes` | Add reflection notes to daily note | `date`, reflections |

### Task Management (4 tools)

| Tool | Purpose | Required Args |
|------|---------|---------------|
| `plorp_mark_task_completed` | Mark task as done | `uuid` |
| `plorp_defer_task` | Change task due date | `uuid`, `new_due` |
| `plorp_set_task_priority` | Set priority (H/M/L) | `uuid`, `priority` |
| `plorp_drop_task` | Delete task | `uuid` |
| `plorp_get_task_info` | Get detailed task info | `uuid` |

### Inbox Processing (5 tools)

| Tool | Purpose | Required Args |
|------|---------|---------------|
| `plorp_get_inbox_items` | Get unprocessed inbox items | None |
| `plorp_create_task_from_inbox` | Create task from inbox item | `item_text`, `description` |
| `plorp_create_note_from_inbox` | Create note from inbox item | `item_text`, `title` |
| `plorp_create_both_from_inbox` | Create linked task + note | `item_text`, `task_description`, `note_title` |
| `plorp_discard_inbox_item` | Discard inbox item | `item_text` |

### Note Management (3 tools)

| Tool | Purpose | Required Args |
|------|---------|---------------|
| `plorp_create_note` | Create standalone note | `title` |
| `plorp_create_note_with_task` | Create note linked to task | `title`, `task_uuid` |
| `plorp_link_note_to_task` | Link existing note to task | `note_path`, `task_uuid` |

### Project Management (9 tools)

| Tool | Purpose | Required Args |
|------|---------|---------------|
| `plorp_create_project` | Create new project | `name`, `domain` |
| `plorp_list_projects` | List all projects | None (filters optional) |
| `plorp_get_project_info` | Get project details | `full_path` |
| `plorp_update_project_state` | Update project state | `full_path`, `state` |
| `plorp_delete_project` | Delete project note | `full_path` |
| `plorp_create_task_in_project` | Create task in project | `description`, `project_full_path` |
| `plorp_list_project_tasks` | List tasks for project | `project_full_path` |
| `plorp_set_focused_domain` | Set domain focus | `domain` |
| `plorp_get_focused_domain` | Get current domain focus | None |

### Vault Access (8 tools)

| Tool | Purpose | Required Args |
|------|---------|---------------|
| `plorp_read_note` | Read note content | `note_path`, `mode` (optional) |
| `plorp_read_folder` | List notes in folder | `folder_path` |
| `plorp_append_to_note` | Add content to end of note | `note_path`, `content` |
| `plorp_update_note_section` | Replace section content | `note_path`, `header`, `new_content` |
| `plorp_search_notes_by_tag` | Search by tag | `tag` |
| `plorp_search_notes_by_field` | Search by metadata field | `field`, `value` |
| `plorp_create_note_in_folder` | Create note with metadata | `folder_path`, `filename` |
| `plorp_list_vault_folders` | Get vault structure | None |

### Pattern Matching (4 tools)

| Tool | Purpose | Required Args |
|------|---------|---------------|
| `plorp_extract_headers` | Get document structure | `note_path` |
| `plorp_get_section_content` | Extract section content | `note_path`, `header` |
| `plorp_detect_projects_in_note` | Find project headers | `note_path` |
| `plorp_extract_bullets` | Extract bullet points | `note_path` |

### Advanced Workflow (1 tool)

| Tool | Purpose | Required Args |
|------|---------|---------------|
| `plorp_process_daily_note` | Process informal tasks with NLP | `date` (optional) |

---

## Daily Workflow

### Morning: Start Your Day

**Say to Claude:**
> "Start my day - create today's daily note with my tasks"

**What Happens:**
1. Claude calls `plorp_start_day`
2. Queries TaskWarrior for:
   - Overdue tasks
   - Tasks due today
   - Recurring tasks due today
3. Generates `vault/daily/YYYY-MM-DD.md` with:
   - YAML frontmatter (date, type, version)
   - Markdown checkboxes for each task
   - Task metadata (project, due, priority, uuid)

**Example Output:**
```
✅ Created daily note: /Users/jsd/vault/daily/2025-10-07.md

📊 Task Summary:
  Overdue: 2
  Due today: 5
  Recurring: 1
  Total: 8
```

**Your daily note looks like:**
```markdown
---
date: 2025-10-07
type: daily
plorp_version: 1.4.0
---

# Daily Note - October 7, 2025

## Tasks

### Overdue
- [ ] Fix critical bug (project: work.engineering.plorp, due: 2025-10-05, priority: H, uuid: abc-123)

### Due Today
- [ ] Team standup (due: 2025-10-07, uuid: def-456)
- [ ] Code review PR #42 (project: work.engineering.api, priority: M, uuid: ghi-789)

### Recurring
- [ ] Daily journal entry (recur: daily, uuid: jkl-012)
```

### Evening: Review Your Day

**Say to Claude:**
> "Review my day - what tasks are incomplete?"

**What Happens:**
1. Claude calls `plorp_get_review_tasks`
2. Parses your daily note for unchecked tasks
3. Shows you each incomplete task

**Then:**
> "For each incomplete task, ask me if I want to: complete it, defer it, change priority, or skip"

Claude will interactively walk through each task and call the appropriate tools:
- `plorp_mark_task_completed` - If you say "done"
- `plorp_defer_task` - If you want to reschedule
- `plorp_set_task_priority` - If you want to change priority

**End with reflection:**
> "Add these review notes to my daily note:
> - Went well: Shipped the new feature
> - Could improve: Too many meetings
> - Tomorrow: Focus on testing"

Calls `plorp_add_review_notes` to append reflection section.

---

## Inbox Processing

### What is the Inbox?

The inbox is a monthly markdown file where you capture quick thoughts, ideas, and tasks throughout the month. It's at `vault/inbox/YYYY-MM.md`.

**Structure:**
```markdown
# Inbox - October 2025

## Unprocessed
- [ ] Email John about Q4 planning
- [ ] Research new database options
- [ ] Blog post idea: TaskWarrior + Obsidian

## Processed
- [x] Call dentist (Action: Task created)
- [x] Meeting notes from standup (Action: Note created)
```

### Process Inbox Items

**Say to Claude:**
> "Process my inbox"

**What Happens:**
1. Claude calls `plorp_get_inbox_items`
2. Shows you each unprocessed item
3. Asks what you want to do with each:
   - **Create task** - Becomes a TaskWarrior task
   - **Create note** - Becomes an Obsidian note
   - **Create both** - Task + linked note
   - **Discard** - Mark as processed but don't create anything

### Examples

**Create Task:**
> "Turn 'Email John about Q4 planning' into a task due Friday with high priority"

Calls `plorp_create_task_from_inbox`:
```json
{
  "item_text": "Email John about Q4 planning",
  "description": "Email John about Q4 planning",
  "due": "friday",
  "priority": "H",
  "project": "work.management"
}
```

**Create Note:**
> "Turn 'Blog post idea: TaskWarrior + Obsidian' into a note"

Calls `plorp_create_note_from_inbox`:
```json
{
  "item_text": "Blog post idea: TaskWarrior + Obsidian",
  "title": "Blog Post - TaskWarrior and Obsidian Integration"
}
```

**Create Both (Task + Note):**
> "Turn 'Research new database options' into a task and a research note, due next week"

Calls `plorp_create_both_from_inbox`:
```json
{
  "item_text": "Research new database options",
  "task_description": "Research database options for new project",
  "note_title": "Database Research - Options and Comparison",
  "due": "next week"
}
```

---

## Project Management

### Understanding Projects

Projects organize your work into a 3-tier hierarchy:
- **Domain** - work, home, or personal
- **Workstream** - Area of work (marketing, engineering, house, etc.)
- **Project** - Specific initiative

**Examples:**
- `work.marketing.website-redesign`
- `work.engineering.api-v2`
- `home.house.kitchen-remodel`
- `personal.learning.spanish`

### Setting Domain Focus

**Say to Claude:**
> "Set my focus to work"

Calls `plorp_set_focused_domain("work")`. This makes work your default domain for the conversation.

**Check current focus:**
> "What domain am I focused on?"

Returns: `"work"`

### Creating Projects

**Say to Claude:**
> "Create a project called 'website-redesign' in the work domain under marketing workstream. Description: Redesign company website with modern UI"

Calls `plorp_create_project`:
```json
{
  "name": "website-redesign",
  "domain": "work",
  "workstream": "marketing",
  "state": "active",
  "description": "Redesign company website with modern UI"
}
```

**Creates file:** `vault/projects/work.marketing.website-redesign.md`

**Frontmatter:**
```yaml
---
domain: work
workstream: marketing
project_name: website-redesign
full_path: work.marketing.website-redesign
state: active
created_at: 2025-10-07T10:30:00
description: Redesign company website with modern UI
task_uuids: []
needs_review: false
tags: [project, work, marketing]
---
```

### Adding Tasks to Projects

**Say to Claude:**
> "Add these tasks to the website-redesign project:
> 1. Design homepage mockup - high priority, due Friday
> 2. Write copy for landing page - medium priority
> 3. Setup staging environment - due tomorrow"

Claude calls `plorp_create_task_in_project` three times.

**What Happens:**
1. Creates task in TaskWarrior with `project:work.marketing.website-redesign`
2. Adds annotation: `plorp-project:work.marketing.website-redesign`
3. Adds UUID to project note frontmatter

**Bidirectional linking:**
- Task → Project (via annotation)
- Project → Tasks (via frontmatter `task_uuids` array)

### Viewing Project Tasks

**Say to Claude:**
> "Show me all tasks in the website-redesign project"

Calls `plorp_list_project_tasks("work.marketing.website-redesign")`

**Returns:**
```json
{
  "tasks": [
    {
      "uuid": "abc-123",
      "description": "Design homepage mockup",
      "priority": "H",
      "due": "2025-10-10",
      "status": "pending",
      "project": "work.marketing.website-redesign"
    },
    ...
  ],
  "count": 3
}
```

### Managing Project State

**Say to Claude:**
> "Mark the website-redesign project as completed"

Calls `plorp_update_project_state`:
```json
{
  "full_path": "work.marketing.website-redesign",
  "state": "completed"
}
```

**Valid states:**
- `active` - Currently working on
- `planning` - In planning phase
- `completed` - Finished
- `blocked` - Waiting on something
- `archived` - No longer active

### Listing Projects

**Say to Claude:**
> "List all my work projects"

Calls `plorp_list_projects(domain="work")`

**Or:**
> "Show me all completed projects"

Calls `plorp_list_projects(state="completed")`

**Or:**
> "What projects do I have in the marketing workstream?"

Filters result to show only marketing projects.

---

## Note Management

### Create Standalone Note

**Say to Claude:**
> "Create a meeting note titled 'Q4 Planning Meeting'"

Calls `plorp_create_note`:
```json
{
  "title": "Q4 Planning Meeting",
  "note_type": "meeting"
}
```

**Creates:** `vault/meetings/q4-planning-meeting.md`

### Create Note Linked to Task

**Say to Claude:**
> "I have task uuid abc-123. Create a note called 'API Design Decisions' linked to this task"

Calls `plorp_create_note_with_task`:
```json
{
  "title": "API Design Decisions",
  "task_uuid": "abc-123",
  "note_type": "general"
}
```

**What Happens:**
1. Creates note in `vault/notes/api-design-decisions.md`
2. Adds task UUID to note's frontmatter: `tasks: [abc-123]`
3. Adds annotation to task: `Note: vault/notes/api-design-decisions.md`

**Bidirectional linking:**
- Note → Task (frontmatter)
- Task → Note (annotation)

### Link Existing Note to Task

**Say to Claude:**
> "Link the note 'vault/notes/research.md' to task xyz-789"

Calls `plorp_link_note_to_task`:
```json
{
  "note_path": "vault/notes/research.md",
  "task_uuid": "xyz-789"
}
```

---

## Vault Access & Note Reading

Sprint 9 introduced comprehensive vault access tools that enable Claude to read, analyze, and manipulate notes beyond just task and project management.

### Reading Notes

**Say to Claude:**
> "Read the note at vault/projects/work.marketing.website-redesign.md"

**What Happens:**
1. Claude calls `plorp_read_note` with `mode: "full"`
2. Returns complete note with frontmatter, content, headers, and metadata

**Example Response:**
```json
{
  "path": "projects/work.marketing.website-redesign.md",
  "title": "Website Redesign",
  "content": "...",
  "metadata": {"domain": "work", "state": "active"},
  "word_count": 342,
  "headers": ["Goals", "Timeline", "Tasks"],
  "warnings": []
}
```

**Read Modes:**
- `mode: "full"` - Complete note with content
- `mode: "info"` - Metadata only (faster)

**Large File Warning:**
Files over 10,000 words trigger a context warning to help manage token usage.

### Listing Folders

**Say to Claude:**
> "What notes are in my projects folder?"

Calls `plorp_read_folder` to list all notes with metadata:
```json
{
  "folder_path": "projects",
  "notes": [
    {
      "path": "projects/work.marketing.website-redesign.md",
      "title": "Website Redesign",
      "metadata": {"state": "active"},
      "word_count": 342,
      "created": "2025-10-01T10:00:00",
      "modified": "2025-10-07T15:30:00"
    }
  ],
  "total_count": 12,
  "returned_count": 12,
  "has_more": false
}
```

**Recursive reading:**
> "List all notes under vault/notes/ including subfolders"

Uses `recursive: true` to walk entire directory tree.

### Searching by Metadata

**Search by tag:**
> "Find all notes tagged with #urgent"

Calls `plorp_search_notes_by_tag("urgent")` to search frontmatter across vault.

**Search by field:**
> "Find all projects in the work domain that are active"

Calls `plorp_search_notes_by_field("domain", "work")` and filters by `state`.

**Smart matching:**
- Matches scalar values: `domain: work`
- Matches list values: `domains: [work, personal]`
- Case-insensitive

### Updating Notes

**Append content:**
> "Add this to my daily note: ## Evening Reflection..."

Calls `plorp_append_to_note` to add content to end of file.

**Update section:**
> "In my website-redesign project, update the Timeline section with..."

Calls `plorp_update_note_section` to replace content between headers.

### Extracting Structure

**Get headers:**
> "What's the structure of my database-comparison note?"

Calls `plorp_extract_headers` to return all headers with levels:
```json
{
  "headers": [
    {"text": "Database Comparison", "level": 1, "line_number": 0},
    {"text": "PostgreSQL", "level": 2, "line_number": 5},
    {"text": "Conclusion", "level": 2, "line_number": 58}
  ]
}
```

**Get section content:**
> "Show me the Conclusion section"

Calls `plorp_get_section_content` to extract only that section.

**Extract bullets:**
> "List all bullet points in the Tasks section"

Calls `plorp_extract_bullets` with optional `section` parameter.

### Project Detection

**Find potential projects:**
> "What project-like items are mentioned in my daily note?"

Calls `plorp_detect_projects_in_note` to find:
- Title Case headers (e.g., `### Website Redesign`)
- kebab-case headers (e.g., `### api-rewrite`)
- Excludes common sections (Tasks, Notes, etc.)

### Vault Structure

**Discover folders:**
> "What folders exist in my vault?"

Calls `plorp_list_vault_folders` to show complete directory tree and permission boundaries.

**Permission boundaries:**
All tools respect `allowed_folders` configuration. Default allowed:
- `daily`, `inbox`, `projects`, `notes`, `Docs`

Excluded by default:
- `.obsidian`, `.trash`, `templates`

### Advanced Workflows

See [MCP_WORKFLOWS.md](MCP_WORKFLOWS.md) for 23 detailed workflow examples including:
- Reading and analyzing notes
- Folder navigation
- Metadata-based searches
- Document structure analysis
- Content extraction patterns
- Multi-tool workflows

---

## Task Processing (/process)

The `/process` workflow uses natural language processing to convert informal tasks into proper TaskWarrior tasks.

### How It Works

**Step 1: Scan for Informal Tasks**

Say to Claude:
> "Process my daily note to find informal tasks"

Claude looks for checkboxes **without UUIDs** in your daily note:
```markdown
- [ ] call dentist tomorrow
- [ ] review pr #42 high priority
- [ ] team meeting friday at 2pm
```

**Step 2: Generate Proposals**

Claude parses natural language dates and priority, then adds a "TBD" section:
```markdown
## TBD (To Be Decided)

Approve or reject these task proposals. Edit [Y] to approve, [N] to reject.

- [Y] call dentist (due: 2025-10-08, priority: none) {TBD-1}
- [Y] review pr #42 (due: none, priority: H) {TBD-2}
- [Y] team meeting (due: 2025-10-10, priority: none) {TBD-3}
```

**Step 3: Process Approvals**

You edit the file to approve/reject:
```markdown
- [Y] call dentist (due: 2025-10-08, priority: none) {TBD-1}
- [N] review pr #42 (due: none, priority: H) {TBD-2}  ← Rejected
- [Y] team meeting (due: 2025-10-10, priority: none) {TBD-3}
```

Say to Claude:
> "Process the approvals in my daily note"

**Step 4: Create Tasks**

Claude:
1. Creates TaskWarrior tasks for approved items (TBD-1, TBD-3)
2. Skips rejected items (TBD-2)
3. Removes TBD section
4. Updates daily note with new tasks including UUIDs:
```markdown
## Tasks
- [ ] call dentist (due: 2025-10-08, uuid: abc-123)
- [ ] team meeting (due: 2025-10-10, uuid: def-456)
```

### Natural Language Parsing

The `/process` workflow understands:

**Dates:**
- "tomorrow", "friday", "next week"
- "oct 15", "10/15", "2025-10-15"
- "in 3 days"

**Priority:**
- "high priority", "important" → H
- "medium priority" → M
- "low priority" → L

**Projects:**
- "for work.engineering" → `project:work.engineering`

---

## Fast Task Queries

Sprint 9.1 introduced instant task queries to solve the "MCP slowness problem" - simple task queries that previously took 5-8 seconds now complete in under 2 seconds via slash commands.

### The Three-Tier Query Architecture

plorp offers three ways to query your tasks, each with different speed/flexibility tradeoffs:

| Tier | Interface | Speed | Use Case |
|------|-----------|-------|----------|
| **1. CLI** | `plorp tasks` | <100ms | Terminal workflows, scripts, instant queries |
| **2. Slash Commands** | `/urgent`, `/today` | 1-2s | Quick Claude Desktop queries |
| **3. Natural Language** | "show urgent tasks" | 5-8s | Complex queries with analysis |

### Available Slash Commands

Five slash commands provide instant access to common queries:

**`/tasks`** - List all pending tasks
```
User: /tasks

Claude runs: plorp tasks
Shows: All pending tasks in a rich table (default limit: 50)
```

**`/urgent`** - Show only urgent (priority:H) tasks
```
User: /urgent

Claude runs: plorp tasks --urgent
Shows: High-priority tasks only
```

**`/today`** - Tasks due today
```
User: /today

Claude runs: plorp tasks --due today
Shows: Tasks with due date = today
```

**`/overdue`** - Tasks past their due date
```
User: /overdue

Claude runs: plorp tasks --due overdue
Shows: Tasks where due < today
```

**`/work-tasks`** - Tasks in work project
```
User: /work-tasks

Claude runs: plorp tasks --project work
Shows: All tasks with project:work
```

### CLI Command Reference

All slash commands use the `plorp tasks` CLI command. You can also use it directly in the terminal:

**Basic usage:**
```bash
plorp tasks                          # All pending tasks
plorp tasks --limit 10               # Limit to 10 tasks
```

**Filters:**
```bash
plorp tasks --urgent                 # Priority:H tasks
plorp tasks --important              # Priority:M tasks
plorp tasks --project work           # Filter by project
plorp tasks --due today              # Due today
plorp tasks --due overdue            # Overdue tasks
plorp tasks --due tomorrow           # Due tomorrow
plorp tasks --due week               # Due this week
```

**Output formats:**
```bash
plorp tasks --format table           # Rich table with emojis (default)
plorp tasks --format simple          # Plain text for scripts
plorp tasks --format json            # JSON for programmatic use
```

**Combine filters:**
```bash
plorp tasks --urgent --project work                    # Urgent work tasks
plorp tasks --due today --project home                # Today's home tasks
plorp tasks --important --due week --limit 5          # Top 5 important tasks this week
```

### When to Use Each Tier

**Tier 1 (CLI):** Use when working in the terminal
```bash
# Quick check before starting work
$ plorp tasks --urgent

# Export for scripting
$ plorp tasks --format json | jq '.[] | select(.project == "work")'
```

**Tier 2 (Slash Commands):** Use for instant queries in Claude Desktop
```
You: /urgent                    ← 1-2 seconds
Claude: Shows 3 urgent tasks

You: /today                     ← 1-2 seconds
Claude: Shows 5 tasks due today
```

**Tier 3 (Natural Language):** Use for complex queries requiring reasoning
```
You: "Show me urgent tasks in the API project that are due this week and analyze which ones are blocking"

Claude: (5-8 seconds)
  1. Reasons about the query
  2. Combines multiple filters
  3. Calls: plorp tasks --urgent --project api --due week
  4. Analyzes dependencies
  5. Provides detailed breakdown
```

### Performance Benefits

**Before Sprint 9.1:**
```
You: "Show me urgent tasks"
Agent reasoning: 3 seconds
Tool calls: 2-3 seconds
Total: 5-8 seconds
```

**After Sprint 9.1:**
```
You: /urgent
Command execution: <100ms
Claude overhead: 1-2 seconds
Total: 1-2 seconds ← 3-4x faster
```

### Creating Custom Slash Commands

You can create your own slash commands for common queries:

**Example:** Create `/api-tasks` for your API project
```bash
# Create file: .claude/commands/api-tasks.md
Run the command: `plorp tasks --project work.engineering.api`

Display tasks for the API rewrite project.
```

**Usage:**
```
You: /api-tasks
Claude: Runs plorp tasks --project work.engineering.api
```

### Natural Language Still Works

Slash commands are a shortcut, not a replacement. Natural language queries still work for complex needs:

```
You: "Show me urgent tasks in the API project that have dependencies"

Claude will:
  1. Use plorp tasks --urgent --project work.engineering.api
  2. Fetch each task's details
  3. Analyze dependencies from annotations
  4. Present organized breakdown
```

---

## Common Workflows

### Workflow 1: Morning Routine

```
You: "Good morning! Start my day"

Claude:
- Calls plorp_start_day
- Creates daily note with 8 tasks
- Shows you the summary

You: "Thanks. Set my focus to work for today"

Claude:
- Calls plorp_set_focused_domain("work")
- Confirms focus set
```

### Workflow 2: Quick Task Capture

```
You: "Add to my inbox:
- Email Sarah about project timeline
- Research CI/CD tools
- Schedule dentist appointment"

(You manually add these to vault/inbox/2025-10.md)

Later...

You: "Process my inbox"

Claude:
- Shows 3 items
- Asks what to do with each
- Creates tasks/notes based on your answers
```

### Workflow 3: Project-Based Work

```
You: "Create a new work project for the API rewrite in the engineering workstream"

Claude:
- Creates work.engineering.api-rewrite project

You: "Add these tasks to the api-rewrite project:
1. Design new endpoints - high priority
2. Write migration plan - due next Friday
3. Setup test environment"

Claude:
- Creates 3 tasks
- Links them to project
- Shows confirmation

You: "Show me all tasks in the api-rewrite project"

Claude:
- Lists 3 tasks with details
```

### Workflow 4: End-of-Day Review

```
You: "Review my day"

Claude:
- Gets uncompleted tasks
- Shows 3 incomplete tasks

You: "Mark the first one done, defer the second to tomorrow, and skip the third"

Claude:
- Calls plorp_mark_task_completed
- Calls plorp_defer_task
- Skips third task

You: "Add review notes: Shipped feature X, need to focus more tomorrow"

Claude:
- Calls plorp_add_review_notes
- Appends reflection to daily note
```

---

## Natural Language Examples

### Creating Projects

**Informal:**
> "Make me a project for planning my vacation to Japan, personal domain"

**Specific:**
> "Create project: name='japan-trip', domain='personal', workstream='travel', description='Plan 2-week trip to Japan in spring'"

### Adding Tasks

**Simple:**
> "Add a task to call the plumber tomorrow"

**Detailed:**
> "Create task in the kitchen-remodel project: 'Get contractor quotes', high priority, due Friday"

### Querying

**Domain queries:**
> "What work projects do I have?"
> "Show me all my personal projects"

**State queries:**
> "Which projects are blocked?"
> "List my completed projects"

**Task queries:**
> "What tasks are in the website-redesign project?"
> "Show me all high-priority work tasks"

### Managing State

**Simple:**
> "Mark the website project as completed"

**With detail:**
> "The api-rewrite project is blocked waiting for design approval"

---

## Troubleshooting

### MCP Server Not Appearing

**Issue:** Claude doesn't show plorp tools

**Check:**
1. `claude_desktop_config.json` is correct
2. Path to `plorp-mcp` is absolute and correct
3. Restart Claude Desktop completely (Cmd+Q, reopen)
4. Check logs: `~/Library/Logs/Claude/mcp-server-plorp.log`

**Test:**
```bash
# Verify plorp-mcp runs
/path/to/.venv/bin/plorp-mcp --version
```

### Vault Not Found

**Issue:** "Vault not found" error

**Check:**
```bash
cat ~/.config/plorp/config.yaml
```

**Ensure:**
```yaml
vault_path: /Users/jsd/vault  # Correct absolute path
```

**Test:**
```bash
ls /Users/jsd/vault/daily
ls /Users/jsd/vault/projects
```

### Tasks Not Created

**Issue:** `plorp_create_task_in_project` returns error

**Possible causes:**
1. TaskWarrior not installed: `which task`
2. Project doesn't exist: Check `vault/projects/`
3. Race condition (should be fixed in v1.4.0 with retry logic)

**Check TaskWarrior:**
```bash
task export | python3 -m json.tool
```

### Focus Not Persisting

**Issue:** Domain focus resets

**Check:**
```bash
cat ~/.config/plorp/mcp_focus.txt
```

**Should contain:** `work`, `home`, or `personal`

**Fix:**
```bash
echo "work" > ~/.config/plorp/mcp_focus.txt
```

### Tool Call Errors

**Issue:** Tool returns error or unexpected result

**Check logs:**
```bash
tail -50 ~/Library/Logs/Claude/mcp-server-plorp.log
```

**Common issues:**
- Missing required arguments
- Invalid UUIDs
- Project not found
- Permission errors on vault files

---

## Advanced Usage

### Using Multiple Domains

You can switch focus between domains throughout the day:

**Morning (work focus):**
```
You: "Set focus to work"
Claude: ✓ Focused on work

You: "Create project website-redesign in marketing"
Claude: Creates work.marketing.website-redesign
```

**Evening (home focus):**
```
You: "Set focus to home"
Claude: ✓ Focused on home

You: "Create project garden-planning in outdoor"
Claude: Creates home.outdoor.garden-planning
```

### Obsidian Bases Integration

Projects are designed to work with the [Obsidian Bases](https://github.com/RafaelGB/obsidian-db-folder) plugin.

**Create a base file:** `vault/projects.base`

```yaml
query: |
  FROM "projects"
  WHERE state = "active"
  SELECT domain, workstream, project_name, state
```

**View in Obsidian:**
- Open `projects.base`
- See all active projects in a table view
- Sort, filter, and edit interactively

### Task Annotations

Every task linked to a project has a special annotation:
```
plorp-project:work.marketing.website-redesign
```

**View annotations:**
```bash
task <uuid> info | grep plorp-project
```

**Filter tasks by annotation:**
```bash
task plorp-project.any: export
```

### Project Frontmatter Fields

All fields available in project notes:

| Field | Type | Description |
|-------|------|-------------|
| `domain` | string | work/home/personal |
| `workstream` | string | Area (optional) |
| `project_name` | string | Project identifier |
| `full_path` | string | Complete path (domain.workstream.name) |
| `state` | string | active/planning/completed/blocked/archived |
| `created_at` | ISO datetime | Creation timestamp |
| `description` | string | Short description |
| `task_uuids` | array | Linked task UUIDs |
| `needs_review` | boolean | Flag for 2-segment projects |
| `tags` | array | Tags for organization |

### Configuration Files

**plorp config:** `~/.config/plorp/config.yaml`
```yaml
vault_path: /Users/jsd/vault
taskwarrior_data: ~/.task
inbox_email: null
default_editor: vim
```

**MCP focus (CLI):** `~/.config/plorp/cli_focus.txt`
```
work
```

**MCP focus (MCP):** `~/.config/plorp/mcp_focus.txt`
```
work
```

Note: CLI and MCP focus are separate and independent.

---

## Tips & Best Practices

### 1. Use Domain Focus

Always set your focus at the start of a session:
```
Morning: "Set focus to work"
Evening: "Set focus to home"
```

This makes all subsequent commands default to that domain.

### 2. Consistent Naming

Use consistent, lowercase, hyphen-separated names:
- ✅ `website-redesign`
- ❌ `Website Redesign`
- ❌ `website_redesign`

### 3. Project Descriptions

Always add descriptions to projects - they help you remember context:
```
"Create project api-v2 in engineering with description:
'Complete rewrite of REST API using new architecture'"
```

### 4. Regular Reviews

Use the daily review workflow every evening:
```
"Review my day"
"Add review notes: [what went well] [what to improve] [tomorrow's plan]"
```

### 5. Inbox as Capture

Don't process inbox items immediately. Just capture throughout the day, then:
```
End of day: "Process my inbox"
```

### 6. Workstream Organization

Group related projects under workstreams:
- `work.marketing.*` - All marketing projects
- `work.engineering.*` - All engineering projects
- `home.house.*` - All house projects

### 7. Use Project States

Update project state as work progresses:
```
Planning → Active → Completed
                ↓
            Blocked (temporarily)
                ↓
            Archived (long-term)
```

---

## Version History

**v1.5.0** (2025-10-09) - Current
- Sprint 9: General Note Management & Vault Interface
- 12 new tools (8 I/O + 4 pattern matching)
- Read notes with metadata and content
- Search by tags and metadata fields
- Extract document structure (headers, sections, bullets)
- Project detection heuristics
- Large file context warnings
- Permission model for vault access

**v1.4.0** (2025-10-07)
- Sprint 8: Project management with Obsidian Bases
- 9 project management tools
- Domain focus mechanism
- Bidirectional task-project linking
- Bug fix: Race condition in task creation

**v1.3.0** (2025-10-07)
- Sprint 7: /process workflow
- Natural language date parsing
- Two-step approval workflow

**v1.2.0** (2025-10-06)
- Sprint 6: MCP integration
- 16 MCP tools
- TaskWarrior + Obsidian integration

**v1.1.0** (2025-10-05)
- Sprint 3-5: Inbox processing
- Note management
- Task linking

**v1.0.0** (2025-10-04)
- Sprint 0-2: Initial workflows
- Daily note generation
- Review workflow

---

## Getting Help

**Logs:**
- MCP server: `~/Library/Logs/Claude/mcp-server-plorp.log`
- Claude main: `~/Library/Logs/Claude/main.log`

**Common Commands:**
```bash
# Check TaskWarrior status
task diagnostics

# Check plorp config
cat ~/.config/plorp/config.yaml

# Test MCP server
/path/to/.venv/bin/plorp-mcp --version

# Check vault structure
ls -la /Users/jsd/vault/{daily,projects,notes,inbox}
```

**Report Issues:**
- GitHub: `https://github.com/yourusername/plorp/issues`
- Include: logs, commands tried, expected vs actual behavior

---

## Appendix: All Tools Quick Reference

### Daily (3)
- `plorp_start_day` - Generate daily note
- `plorp_get_review_tasks` - Get uncompleted tasks
- `plorp_add_review_notes` - Add reflections

### Tasks (5)
- `plorp_get_task_info` - Get task details
- `plorp_mark_task_completed` - Mark done
- `plorp_defer_task` - Reschedule
- `plorp_set_task_priority` - Change priority
- `plorp_drop_task` - Delete task

### Inbox (5)
- `plorp_get_inbox_items` - List unprocessed
- `plorp_create_task_from_inbox` - Inbox → task
- `plorp_create_note_from_inbox` - Inbox → note
- `plorp_create_both_from_inbox` - Inbox → task+note
- `plorp_discard_inbox_item` - Mark processed

### Notes (3)
- `plorp_create_note` - Create standalone note
- `plorp_create_note_with_task` - Create linked note
- `plorp_link_note_to_task` - Link existing note

### Projects (9)
- `plorp_create_project` - New project
- `plorp_list_projects` - List projects
- `plorp_get_project_info` - Project details
- `plorp_update_project_state` - Change state
- `plorp_delete_project` - Delete project
- `plorp_create_task_in_project` - Add task to project
- `plorp_list_project_tasks` - List project's tasks
- `plorp_set_focused_domain` - Set focus
- `plorp_get_focused_domain` - Get focus

### Vault Access (8)
- `plorp_read_note` - Read note content
- `plorp_read_folder` - List notes in folder
- `plorp_append_to_note` - Append content
- `plorp_update_note_section` - Replace section
- `plorp_search_notes_by_tag` - Search by tag
- `plorp_search_notes_by_field` - Search by field
- `plorp_create_note_in_folder` - Create with metadata
- `plorp_list_vault_folders` - List vault structure

### Pattern Matching (4)
- `plorp_extract_headers` - Get document structure
- `plorp_get_section_content` - Extract section
- `plorp_detect_projects_in_note` - Find projects
- `plorp_extract_bullets` - Extract bullets

### Advanced (1)
- `plorp_process_daily_note` - Process informal tasks

---

**Total:** 38 MCP tools

**End of Manual**
