# MCP Workflows - Advanced Usage Patterns

**Version:** 1.5.0
**Last Updated:** 2025-10-09

This document provides workflow examples for using plorp's MCP tools to accomplish common tasks.

---

## Table of Contents

1. [Reading and Analyzing Notes](#reading-and-analyzing-notes)
2. [Folder Navigation and Discovery](#folder-navigation-and-discovery)
3. [Metadata-Based Searches](#metadata-based-searches)
4. [Note Creation and Updates](#note-creation-and-updates)
5. [Document Structure Analysis](#document-structure-analysis)
6. [Project Discovery](#project-discovery)
7. [Content Extraction](#content-extraction)
8. [Combining Workflows](#combining-workflows)

---

## Reading and Analyzing Notes

### Workflow 1: Read a Specific Note

**Goal:** Read the contents of a specific note to understand its content.

**Say to Claude:**
> "Read the note at vault/projects/work.marketing.website-redesign.md"

**What Happens:**
1. Claude calls `plorp_read_note` with `mode: "full"`
2. Returns complete note with frontmatter, content, headers, and metadata
3. Analyzes content to answer follow-up questions

**Example Response:**
```json
{
  "path": "projects/work.marketing.website-redesign.md",
  "title": "Website Redesign",
  "content": "...",
  "metadata": {
    "domain": "work",
    "workstream": "marketing",
    "state": "active"
  },
  "word_count": 342,
  "headers": ["Goals", "Timeline", "Tasks"],
  "warnings": []
}
```

**Follow-up Questions:**
> "What's the current state of this project?"
> "What tasks are listed in this note?"
> "Summarize the goals section"

### Workflow 2: Quick Metadata Check

**Goal:** Check a note's metadata without reading the full content.

**Say to Claude:**
> "What's the state of the website-redesign project?"

**What Happens:**
1. Claude calls `plorp_read_note` with `mode: "info"`
2. Returns only metadata, title, word count, dates
3. No full content loaded (faster)

**Use Cases:**
- Checking project state
- Getting file modification times
- Quick metadata lookups
- Checking if a note exists

### Workflow 3: Large File Warning

**Goal:** Read a large note with context awareness.

**Say to Claude:**
> "Read the note at vault/research/database-comparison.md"

**What Happens:**
1. Claude calls `plorp_read_note` with `mode: "full"`
2. Note is 12,000 words (exceeds 10k threshold)
3. Returns note with warning: `"Large file (12000 words) - may consume significant context"`

**Claude's Response:**
> "I've read the database comparison note (12,000 words). Note that this is a large file that may consume significant context. Would you like me to focus on a specific section instead?"

**Better Alternative:**
> "Show me just the Conclusions section from that note"

Claude calls `plorp_get_section_content` to extract only the relevant section.

---

## Folder Navigation and Discovery

### Workflow 4: List All Notes in a Folder

**Goal:** Discover what notes exist in a folder.

**Say to Claude:**
> "What notes do I have in my projects folder?"

**What Happens:**
1. Claude calls `plorp_read_folder` with `folder_path: "projects"`
2. Returns list of all notes with metadata
3. Can filter by criteria

**Example Response:**
```json
{
  "folder_path": "projects",
  "notes": [
    {
      "path": "projects/work.marketing.website-redesign.md",
      "title": "Website Redesign",
      "metadata": {"state": "active", "domain": "work"},
      "word_count": 342,
      "created": "2025-10-01T10:00:00",
      "modified": "2025-10-07T15:30:00"
    },
    ...
  ],
  "total_count": 12,
  "returned_count": 12,
  "has_more": false
}
```

**Follow-up Questions:**
> "Which projects were modified in the last week?"
> "Show me only active projects"
> "Which is the largest note?"

### Workflow 5: Recursive Folder Reading

**Goal:** Read all notes in a folder and its subfolders.

**Say to Claude:**
> "List all notes under vault/notes/ including subfolders"

**What Happens:**
1. Claude calls `plorp_read_folder` with `recursive: true`
2. Walks entire directory tree
3. Returns notes from all subdirectories

**Example Structure:**
```
notes/
  meeting-notes/
    q4-planning.md
    standup-2025-10-07.md
  research/
    database-options.md
  general/
    ideas.md
```

**Result:** Returns all 4 notes from all subdirectories.

### Workflow 6: Vault Structure Discovery

**Goal:** Understand the overall structure of your vault.

**Say to Claude:**
> "What folders exist in my vault?"

**What Happens:**
1. Claude calls `plorp_list_vault_folders`
2. Returns complete directory tree
3. Shows which folders are accessible

**Example Response:**
```json
{
  "folders": [
    "daily",
    "inbox",
    "projects",
    "notes",
    "notes/meetings",
    "notes/research",
    "Docs",
    ".obsidian",
    ".trash"
  ],
  "accessible_folders": [
    "daily",
    "inbox",
    "projects",
    "notes",
    "notes/meetings",
    "notes/research",
    "Docs"
  ],
  "excluded_folders": [".obsidian", ".trash"]
}
```

**Use Cases:**
- Understanding vault layout
- Finding where to create new notes
- Checking permission boundaries

---

## Metadata-Based Searches

### Workflow 7: Search by Tag

**Goal:** Find all notes with a specific tag.

**Say to Claude:**
> "Find all notes tagged with #urgent"

**What Happens:**
1. Claude calls `plorp_search_notes_by_tag` with `tag: "urgent"`
2. Searches frontmatter `tags` fields across all notes
3. Returns matching notes with metadata

**Example Matches:**
```markdown
---
tags: [urgent, work, bug]
---
```

**Result:**
```json
{
  "matches": [
    {
      "path": "notes/critical-bug-fix.md",
      "title": "Critical Bug Fix",
      "metadata": {"tags": ["urgent", "work", "bug"]},
      "match_reason": "Has tag 'urgent'"
    },
    ...
  ],
  "count": 3
}
```

### Workflow 8: Search by Metadata Field

**Goal:** Find notes with specific metadata values.

**Say to Claude:**
> "Find all projects in the work domain that are active"

**What Happens:**
1. Claude calls `plorp_search_notes_by_field` with:
   ```json
   {
     "field": "domain",
     "value": "work",
     "folder_hint": "projects"
   }
   ```
2. Finds notes where `domain: work`
3. Can filter results by `state: active`

**Smart Value Matching:**
- `value: "work"` matches `domain: work`
- `value: "work"` matches `domains: [work, personal]` (list)
- Case-insensitive

### Workflow 9: Complex Metadata Queries

**Goal:** Find notes matching multiple criteria.

**Say to Claude:**
> "Find all completed projects in the engineering workstream"

**What Happens:**
1. Claude calls `plorp_search_notes_by_field` for `workstream: engineering`
2. Filters results where `state: completed`
3. Returns only matching projects

**Example Workflow:**
```
Claude: Searching for workstream=engineering...
Claude: Found 8 projects. Filtering by state=completed...
Claude: 3 completed engineering projects:
  - work.engineering.api-v1
  - work.engineering.database-migration
  - work.engineering.ci-cd-setup
```

---

## Note Creation and Updates

### Workflow 10: Create Note with Metadata

**Goal:** Create a new note with specific frontmatter.

**Say to Claude:**
> "Create a meeting note titled 'Q4 Planning Session' with participants Alice, Bob, and tag it as meeting and planning"

**What Happens:**
1. Claude calls `plorp_create_note_in_folder`:
   ```json
   {
     "folder_path": "notes/meetings",
     "filename": "q4-planning-session.md",
     "title": "Q4 Planning Session",
     "initial_content": "## Agenda\n\n## Notes\n\n## Action Items\n",
     "metadata": {
       "type": "meeting",
       "participants": ["Alice", "Bob"],
       "tags": ["meeting", "planning"]
     }
   }
   ```
2. Creates file at `notes/meetings/q4-planning-session.md`
3. Includes frontmatter with metadata

**Result:**
```markdown
---
type: meeting
participants:
  - Alice
  - Bob
tags:
  - meeting
  - planning
created_at: 2025-10-09T14:30:00
---

# Q4 Planning Session

## Agenda

## Notes

## Action Items
```

### Workflow 11: Append to Daily Note

**Goal:** Add content to the end of today's daily note.

**Say to Claude:**
> "Add this to my daily note:
> ## Evening Reflection
> - Shipped feature X
> - Tomorrow: Focus on testing"

**What Happens:**
1. Claude calls `plorp_append_to_note`:
   ```json
   {
     "note_path": "daily/2025-10-09.md",
     "content": "\n## Evening Reflection\n- Shipped feature X\n- Tomorrow: Focus on testing\n"
   }
   ```
2. Appends content to end of file
3. Preserves existing content

**Use Cases:**
- Adding review notes
- Appending meeting notes
- Adding new sections

### Workflow 12: Update a Specific Section

**Goal:** Replace the content of a specific section in a note.

**Say to Claude:**
> "In my website-redesign project note, update the Timeline section with:
> - Design phase: Oct 10-15
> - Development: Oct 16-30
> - Launch: Nov 1"

**What Happens:**
1. Claude calls `plorp_update_note_section`:
   ```json
   {
     "note_path": "projects/work.marketing.website-redesign.md",
     "header": "Timeline",
     "new_content": "- Design phase: Oct 10-15\n- Development: Oct 16-30\n- Launch: Nov 1"
   }
   ```
2. Finds `## Timeline` section
3. Replaces content between that header and the next header
4. Preserves rest of document

**Before:**
```markdown
## Timeline

TBD

## Tasks
```

**After:**
```markdown
## Timeline

- Design phase: Oct 10-15
- Development: Oct 16-30
- Launch: Nov 1

## Tasks
```

---

## Document Structure Analysis

### Workflow 13: Extract Document Headers

**Goal:** Understand the structure of a document.

**Say to Claude:**
> "What's the structure of my database-comparison note?"

**What Happens:**
1. Claude calls `plorp_extract_headers`:
   ```json
   {
     "note_path": "notes/research/database-comparison.md"
   }
   ```
2. Returns all headers with levels and line numbers

**Example Response:**
```json
{
  "headers": [
    {"text": "Database Comparison", "level": 1, "line_number": 0},
    {"text": "PostgreSQL", "level": 2, "line_number": 5},
    {"text": "Pros", "level": 3, "line_number": 7},
    {"text": "Cons", "level": 3, "line_number": 15},
    {"text": "MySQL", "level": 2, "line_number": 23},
    {"text": "MongoDB", "level": 2, "line_number": 40},
    {"text": "Conclusion", "level": 2, "line_number": 58}
  ],
  "count": 7
}
```

**Follow-up:**
> "Show me just the Conclusion section"

Claude can then use `plorp_get_section_content` to extract that specific section.

### Workflow 14: Extract Section Content

**Goal:** Read only a specific section from a long document.

**Say to Claude:**
> "Show me the Pros section from the PostgreSQL comparison"

**What Happens:**
1. Claude calls `plorp_get_section_content`:
   ```json
   {
     "note_path": "notes/research/database-comparison.md",
     "header": "Pros"
   }
   ```
2. Finds `### Pros` header
3. Returns only content between that header and next same-level header

**Result:**
```markdown
- ACID compliant
- Rich feature set
- Great JSON support
- Excellent documentation
```

**Use Cases:**
- Reading specific sections from long documents
- Avoiding context overload
- Focused analysis

---

## Project Discovery

### Workflow 15: Detect Projects in a Note

**Goal:** Find project references in a note that might not be formal projects yet.

**Say to Claude:**
> "What project-like items are mentioned in my daily note?"

**What Happens:**
1. Claude calls `plorp_detect_projects_in_note`:
   ```json
   {
     "note_path": "daily/2025-10-09.md"
   }
   ```
2. Uses heuristics to detect project names:
   - Title Case headers (e.g., `### Website Redesign`)
   - kebab-case headers (e.g., `### api-rewrite`)
   - Excludes common section names (Tasks, Notes, etc.)

**Example Note:**
```markdown
## Projects

### Website Redesign

- Working on homepage mockup

### api-rewrite

- Completed endpoint design

### Tasks

- General tasks here
```

**Result:**
```json
{
  "potential_projects": [
    "Website Redesign",
    "api-rewrite"
  ],
  "count": 2,
  "detection_method": "header_analysis"
}
```

**Follow-up:**
> "Create formal projects for these if they don't already exist"

Claude can then check existing projects and create new ones as needed.

### Workflow 16: Discover Workstreams

**Goal:** Find what workstreams are active across all projects.

**Say to Claude:**
> "What workstreams do I have in my work projects?"

**What Happens:**
1. Claude calls `plorp_read_folder("projects")`
2. Filters by `domain: work`
3. Extracts unique `workstream` values from metadata
4. Groups projects by workstream

**Example Result:**
```
Work Workstreams:
  marketing (3 projects)
    - website-redesign (active)
    - email-campaign (planning)
    - brand-refresh (completed)

  engineering (5 projects)
    - api-v2 (active)
    - database-migration (active)
    - ci-cd-setup (completed)
    - monitoring (planning)
    - security-audit (blocked)
```

---

## Content Extraction

### Workflow 17: Extract All Bullets from a Section

**Goal:** Get a list of bullet points from a specific section.

**Say to Claude:**
> "What tasks are listed in the Tasks section of my website-redesign project?"

**What Happens:**
1. Claude calls `plorp_extract_bullets`:
   ```json
   {
     "note_path": "projects/work.marketing.website-redesign.md",
     "section": "Tasks"
   }
   ```
2. Finds `## Tasks` section
3. Extracts all bullet points (including nested)

**Example Section:**
```markdown
## Tasks

- [ ] Design homepage mockup
  - Research competitor designs
  - Create wireframes
- [ ] Write landing page copy
- [x] Setup staging environment
```

**Result:**
```json
{
  "bullets": [
    "[ ] Design homepage mockup",
    "Research competitor designs",
    "Create wireframes",
    "[ ] Write landing page copy",
    "[x] Setup staging environment"
  ],
  "count": 5
}
```

**Use Cases:**
- Extracting task lists
- Finding action items
- Collecting notes from meetings

### Workflow 18: Extract All Bullets from Document

**Goal:** Get all bullet points regardless of section.

**Say to Claude:**
> "List all bullet points in my Q4 planning note"

**What Happens:**
1. Claude calls `plorp_extract_bullets` without `section` parameter
2. Extracts ALL bullets from entire document

**Use Cases:**
- Getting overview of all items
- Finding all checkboxes
- Comprehensive task extraction

---

## Combining Workflows

### Workflow 19: Research Project Analysis

**Goal:** Comprehensive analysis of a project note.

**Say to Claude:**
> "Analyze the website-redesign project - give me a full summary"

**What Claude Does:**
1. Calls `plorp_read_note` to get full content
2. Calls `plorp_extract_headers` to understand structure
3. Calls `plorp_list_project_tasks` to get linked tasks
4. Analyzes and synthesizes information

**Example Flow:**
```
Claude: Reading project note...
Claude: Found 5 sections: Goals, Timeline, Tasks, Resources, Notes
Claude: Extracting tasks...
Claude: Found 3 linked TaskWarrior tasks
Claude: Analysis complete.

Summary:
- Project: Website Redesign (work.marketing)
- State: Active
- Tasks: 3 total (2 pending, 1 completed)
- Timeline: Oct 10 - Nov 1
- Key goals: Modern UI, mobile-first, improved UX
```

### Workflow 20: Multi-Folder Search

**Goal:** Find notes matching criteria across multiple folders.

**Say to Claude:**
> "Find all notes tagged 'urgent' in either my projects or notes folders"

**What Claude Does:**
1. Calls `plorp_search_notes_by_tag("urgent")` (searches entire vault)
2. Filters results to show only notes from `projects/` or `notes/`
3. Groups by folder

**Example Result:**
```
Found 5 urgent notes:

Projects (2):
- work.engineering.security-audit.md
- work.marketing.brand-refresh.md

Notes (3):
- notes/critical-bug-analysis.md
- notes/meetings/emergency-planning.md
- notes/incidents/2025-10-08-outage.md
```

### Workflow 21: Project Health Check

**Goal:** Check the status of all active projects.

**Say to Claude:**
> "Check the health of all my active work projects"

**What Claude Does:**
1. Calls `plorp_list_projects(domain="work", state="active")`
2. For each project:
   - Calls `plorp_get_project_info`
   - Calls `plorp_list_project_tasks`
   - Checks last modified date
3. Analyzes and reports

**Example Report:**
```
Active Work Projects Health Check:

✅ website-redesign (marketing)
   - 3 tasks (2 pending, 1 done)
   - Last updated: 2 days ago
   - Status: On track

⚠️  api-v2 (engineering)
   - 12 tasks (10 pending, 2 done)
   - Last updated: 14 days ago
   - Warning: No recent activity

✅ email-campaign (marketing)
   - 1 task (1 pending)
   - Last updated: 1 day ago
   - Status: Active
```

### Workflow 22: Inbox to Project Pipeline

**Goal:** Process inbox item into a project with tasks.

**Say to Claude:**
> "I have an inbox item 'Plan team offsite'. Turn it into a project with initial tasks"

**What Claude Does:**
1. Calls `plorp_create_project`:
   ```json
   {
     "name": "team-offsite",
     "domain": "work",
     "workstream": "management",
     "description": "Plan and organize team offsite event"
   }
   ```
2. Calls `plorp_create_task_in_project` multiple times for initial tasks:
   - "Research venue options"
   - "Create budget proposal"
   - "Survey team for dates"
3. Calls `plorp_discard_inbox_item` to mark original item processed
4. Returns project path and task UUIDs

**Result:**
```
✓ Created project: work.management.team-offsite
✓ Added 3 tasks:
  - Research venue options (uuid: abc-123)
  - Create budget proposal (uuid: def-456)
  - Survey team for dates (uuid: ghi-789)
✓ Inbox item processed
```

### Workflow 23: Weekly Review Automation

**Goal:** Generate a weekly review from daily notes.

**Say to Claude:**
> "Summarize my week - read all daily notes from this week and tell me what I accomplished"

**What Claude Does:**
1. Calculates date range (Monday-Friday)
2. Calls `plorp_read_folder("daily")` to get all daily notes
3. Filters to current week
4. For each day:
   - Calls `plorp_read_note` with `mode: "full"`
   - Extracts completed tasks (checked boxes)
   - Looks for reflection sections
5. Synthesizes weekly summary

**Example Output:**
```
Week of Oct 7-11, 2025

Tasks Completed: 23
- High priority: 8
- Medium priority: 12
- Low priority: 3

By Project:
- website-redesign: 7 tasks
- api-v2: 4 tasks
- team-management: 3 tasks
- general: 9 tasks

Highlights:
- Monday: Shipped new homepage design
- Wednesday: Completed security audit
- Friday: Q4 planning session

Notes from reflections:
- Need better time management
- Too many context switches
- Sprint planning went well
```

---

## Permission Boundaries

All MCP tools respect the `allowed_folders` configuration. Default allowed folders:
- `daily`
- `inbox`
- `projects`
- `notes`
- `Docs`

**Excluded by default:**
- `.obsidian` (Obsidian config)
- `.trash` (Deleted files)
- `templates` (Template files)

**Attempting to access excluded folders:**
```
You: "Read the note at .obsidian/workspace.json"

Claude: ❌ Error: Access denied. Folder '.obsidian' is not in allowed_folders.
```

**To modify permissions:**
Edit `~/.config/plorp/config.yaml`:
```yaml
note_access:
  allowed_folders: ["daily", "inbox", "projects", "notes", "Docs", "my-custom-folder"]
```

---

## Performance Tips

### 1. Use Mode: Info for Metadata Checks

Don't read full content if you only need metadata:
```
❌ Slow: plorp_read_note(mode="full") → 5000 words loaded
✅ Fast:  plorp_read_note(mode="info") → Only metadata
```

### 2. Use folder_hint in Searches

Help narrow search scope:
```
❌ Slower: plorp_search_notes_by_field("domain", "work")  → Searches entire vault
✅ Faster: plorp_search_notes_by_field("domain", "work", folder_hint="projects")
```

### 3. Extract Sections Instead of Full Docs

For large documents:
```
❌ Slow: Read full 15,000-word note
✅ Fast: plorp_get_section_content("Conclusion")
```

### 4. Use Recursive: False When Possible

Avoid deep directory walks:
```
❌ Slower: plorp_read_folder("notes", recursive=True)  → 100+ notes
✅ Faster: plorp_read_folder("notes/meetings", recursive=False)  → 10 notes
```

---

## Error Handling

### Common Errors

**1. HeaderNotFoundError**
```
Error: Header 'Conclusion' not found in note: research/database.md

Fix: Check header spelling, or list headers first:
  plorp_extract_headers("research/database.md")
```

**2. FileNotFoundError**
```
Error: Note not found: projects/missing.md

Fix: Use plorp_list_vault_folders or plorp_read_folder to find correct path
```

**3. PermissionError**
```
Error: Access denied. Folder 'templates' is not in allowed_folders.

Fix: Either:
  - Move note to allowed folder
  - Update config.yaml to allow folder
```

**4. Large File Warning**
```
Warning: Large file (15000 words) - may consume significant context

Not an error, but suggests:
  - Use mode: "info" for metadata only
  - Use plorp_get_section_content for specific sections
  - Consider splitting document
```

---

## Advanced Patterns

### Pattern 1: Lazy Loading

Load metadata first, then content only if needed:
```python
# Step 1: Check metadata
info = plorp_read_note(path, mode="info")

# Step 2: Only load full content if criteria met
if info["word_count"] < 5000 and info["metadata"]["priority"] == "high":
    full = plorp_read_note(path, mode="full")
```

### Pattern 2: Incremental Search

Start narrow, expand as needed:
```python
# Step 1: Search in most likely folder
results = plorp_search_notes_by_tag("urgent", folder_hint="projects")

# Step 2: If not found, expand search
if not results:
    results = plorp_search_notes_by_tag("urgent")  # Vault-wide
```

### Pattern 3: Structure-First Analysis

Understand document structure before reading content:
```python
# Step 1: Get headers
headers = plorp_extract_headers(path)

# Step 2: Read only relevant sections
for header in headers:
    if "conclusion" in header["text"].lower():
        content = plorp_get_section_content(path, header["text"])
```

---

## Troubleshooting Workflows

### Issue: Can't Find a Note

**Workflow:**
1. List vault folders: `plorp_list_vault_folders`
2. Read target folder: `plorp_read_folder("expected-folder")`
3. Search by metadata: `plorp_search_notes_by_field("title", "partial-match")`

### Issue: Note Too Large, Context Limit Hit

**Workflow:**
1. Get headers: `plorp_extract_headers(path)`
2. Identify relevant section
3. Extract only that section: `plorp_get_section_content(path, "Relevant Section")`

### Issue: Don't Know What Tags Exist

**Workflow:**
1. Read folder: `plorp_read_folder("notes")`
2. Inspect metadata of all notes
3. Extract unique tag values
4. Search by discovered tags

---

## Sprint 9 Tool Summary

**I/O Tools (8):**
- `plorp_read_note` - Read note content
- `plorp_read_folder` - List notes in folder
- `plorp_append_to_note` - Add content to end
- `plorp_update_note_section` - Replace section content
- `plorp_search_notes_by_tag` - Search by tag
- `plorp_search_notes_by_field` - Search by metadata field
- `plorp_create_note_in_folder` - Create note with metadata
- `plorp_list_vault_folders` - Get vault structure

**Pattern Matching Tools (4):**
- `plorp_extract_headers` - Get document structure
- `plorp_get_section_content` - Extract section content
- `plorp_detect_projects_in_note` - Find project headers
- `plorp_extract_bullets` - Extract bullet points

**Total:** 12 new tools in Sprint 9

---

**End of Workflows Guide**
