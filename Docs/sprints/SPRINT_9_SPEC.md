# Sprint 9 Spec: General Note Management & Vault Interface via MCP

**Version:** 1.0.0
**Status:** 📋 DRAFT - Planning Phase
**Sprint:** 9
**Estimated Effort:** 18-20 hours
**Dependencies:** Sprint 6 (MCP architecture), Sprint 7 (/process workflow), Sprint 8 (project management)
**Architecture:** MCP-First, General Vault Access
**Date:** 2025-10-08

---

## Executive Summary

Sprint 9 transforms plorp from a "TaskWarrior + Daily Notes bridge" into a **general Obsidian vault interface** accessible via MCP. This enables Claude Desktop to read, write, search, and organize notes throughout the vault - not just daily notes, inbox, and projects.

**Key Innovation:** Provide **low-level note I/O primitives** via MCP tools, allowing Claude to apply intelligence to vault management. Users can say "read all SEO notes and summarize" or "update project doc with today's notes" - Claude combines multiple tools to accomplish complex workflows.

**What's New:**
- Read/write any markdown file in vault (not just specific folders)
- Search notes by tags, frontmatter fields, headers, content
- Folder operations (read all notes in folder with filtering)
- Section-level editing (update specific headers without rewriting entire note)
- Pattern detection (find project-like headers, extract bullets, analyze structure)
- Context-aware content management (prevent context exhaustion)

**User Experience:**
```
User: "Read the sprint 9 spec"
Claude: [reads Docs/sprints/SPRINT_9_SPEC.md, full content now in context]

User: "Read all docs in /Docs but ignore /Docs/archive"
Claude: [scans folder, reads 12 docs, excludes archive/]

User: "Append this bug report to the sprint 9 doc"
Claude: [appends content to ## Bugs section]

User: "Find all SEO notes and report back ready to work on a new idea"
Claude: [searches tag:SEO, reads 5 notes, synthesizes summary]
```

---

## Vision: Recreating Claude Code Experience in MCP

### What Users Want to Say

**Things users currently say to Claude Code:**
- "Read all docs in folder"
- "Read only the docs in /docs, ignore subdirectory /docs/archive"
- "Add this bug report to the sprint 9 doc"
- "Update readme"
- "Update handoff.md with everything we did in this session"

**Things users want to say to Claude via plorp MCP:**
- "Read this doc"
- "Read the docs in this folder"
- "Append this to this doc"
- "Update the project document with the notes from today's note"
- "Read all notes labeled SEO and report back ready to work on a new idea"
- "Find ### headers that are projects, create project notes if they don't exist"

### Two Categories of Operations

#### 1. Deterministic Operations (Direct Tool Calls)
- **Read specific note** → `plorp_read_note(path)`
- **Read folder with filters** → `plorp_read_folder(path, recursive, exclude)`
- **Append content** → `plorp_append_to_note(path, content)`
- **Update section** → `plorp_update_note_section(path, header, content)`
- **Search by tag** → `plorp_search_notes_by_tag(tag)`
- **Create note anywhere** → `plorp_create_note_in_folder(folder, title, content)`

**Characteristic:** Clear input → clear action. No interpretation needed.

#### 2. Stochastic/Intelligent Operations (Claude Decides)
- **"Read all SEO notes and summarize"** → Search + read multiple + Claude synthesizes
- **"Update project doc with today's notes"** → Read daily note + extract relevant content + append to project (Claude decides "relevant")
- **"Find project from header or create it"** → Pattern match headers + search existing + ask user for domain if not found
- **"Organize these notes by topic"** → Claude reads content, reasons about categories, calls tools to move/tag files

**Characteristic:** Claude combines multiple tools and applies intelligence to accomplish goal.

**Key Insight:** MCP tools provide **capabilities**, Claude provides **intelligence**.

---

## How MCP Tools Work with Context

### The Core Question

**Does content returned by MCP tools enter Claude's context?**

**Answer: YES.** It works exactly like Claude Code's Read tool.

### The Flow

```
1. User: "Read the sprint 9 spec"
   ↓
2. Claude calls: plorp_read_note("Docs/sprints/SPRINT_9_SPEC.md")
   ↓
3. Tool executes: plorp reads markdown file
   ↓
4. Tool returns: {
     "path": "Docs/sprints/SPRINT_9_SPEC.md",
     "content": "# Sprint 9 Spec\n\n## Goals\n...[full 5000 words]...",
     "word_count": 5000,
     "headers": ["Goals", "Architecture", "Implementation"]
   }
   ↓
5. Claude receives: Full content in tool result block
   ↓
6. Content enters context: Claude can now reference, quote, analyze
   ↓
7. User asks: "What are the main goals?"
   ↓
8. Claude answers: [references content from step 4, no re-read needed]
```

### Comparison: Claude Code vs MCP Tools

| Aspect | Claude Code | plorp MCP Tools |
|--------|-------------|-----------------|
| **Content in context** | ✅ Yes | ✅ Yes |
| **Can reference later** | ✅ Yes | ✅ Yes |
| **Counts toward context** | ✅ Yes (200k tokens) | ✅ Yes (200k tokens) |
| **Context warnings** | ✅ Built-in alerts at 60% | ❌ No automatic warnings |
| **Large file handling** | ✅ offset/limit params | ⚠️ Need to implement |
| **Pagination** | ✅ Can read in chunks | ⚠️ Need to implement |
| **Folder recursion** | ✅ Glob patterns | ⚠️ Need to implement |

### Implications for Design

**This means the workflows WILL work:**

✅ **"Read all SEO notes"**
- plorp returns all note contents (up to reasonable limit)
- Claude sees all content in context
- Claude can synthesize across notes
- **Limitation**: If 10 notes × 2000 words = 20k tokens used

✅ **"Read sprint 9 spec then add bug report"**
- First call: Read spec → full content in context
- Claude sees current structure
- Second call: Append to correct section
- Claude references context to know where to append

✅ **"Update project with today's notes"**
- Read daily note → content in context
- Read project doc → content in context
- Claude sees both, decides what's relevant
- Claude calls append with synthesized content

**But we need to be careful:**
- Reading 50 notes could exhaust context window
- Large files (20k+ words) could consume too much context
- Need smart defaults (limits, previews, metadata-first)

---

## Goals

### Primary Goals (Must Have)

1. **Enable general note read/write operations**
   - Read any markdown file in vault (not just daily/inbox/projects)
   - Write/append to any note
   - Update specific sections without rewriting entire file
   - Create notes in arbitrary folders

2. **Provide folder operations**
   - Read all notes in folder (with filtering)
   - List vault structure
   - Search notes by metadata (tags, frontmatter fields)

3. **Context-aware content management**
   - Return previews for large files
   - Limit folder scans to reasonable defaults
   - Provide metadata-first search (defer full reads)
   - Warn when operations might consume excessive context

4. **Maintain backward compatibility**
   - Existing daily/inbox/project workflows unchanged
   - New tools are additive, not replacements
   - High-level workflows coexist with low-level primitives

### Secondary Goals (Nice to Have)

5. **Pattern detection and extraction**
   - Detect project-like headers (### Project Name)
   - Extract bullet points from specific sections
   - Parse document structure (headers, links, tags)

6. **CLI wrappers for note operations**
   - `plorp note read <path>` for power users
   - `plorp note search <query>` for testing
   - Optional - MCP is primary interface

### Non-Goals (Explicitly Out of Scope)

- ❌ Full-text search across vault (defer to Obsidian's search or external tools)
- ❌ Semantic search / embeddings (Sprint 10+)
- ❌ Automatic note organization / AI classification (Sprint 10+)
- ❌ Real-time file watching / sync (not needed for MCP workflow)
- ❌ Obsidian plugin integration / REST API calls (file system only)

---

## Architecture

### Three-Phase Implementation

#### Phase 1: Core Note I/O (Deterministic - Week 1)

**New integration module:** `integrations/obsidian_notes.py`

**Functions:**
```python
def read_note(vault_path: Path, note_path: str, mode: str = "full") -> NoteContent:
    """
    Read any markdown note in vault.

    Args:
        vault_path: Vault root path
        note_path: Relative path to note (e.g., "notes/ideas.md" or "Docs/sprint-9.md")
        mode: "full" (entire content), "preview" (first 1000 chars),
              "metadata" (frontmatter only), "structure" (headers only)

    Returns:
        NoteContent TypedDict with path, content, metadata, word_count

    Raises:
        NoteNotFoundError: If note doesn't exist
    """

def read_folder(vault_path: Path, folder_path: str,
                recursive: bool = False,
                exclude: List[str] = None,
                limit: int = 10,
                mode: str = "metadata") -> FolderReadResult:
    """
    Read all notes in folder with filtering.

    Args:
        vault_path: Vault root path
        folder_path: Relative folder path (e.g., "notes" or "Docs")
        recursive: Include subdirectories
        exclude: Folder names to skip (e.g., ["archive", "templates"])
        limit: Max notes to return (default 10, max 50)
        mode: Content mode (default "metadata" to avoid context exhaustion)

    Returns:
        FolderReadResult with notes list, total_count, has_more flag
    """

def append_to_note(vault_path: Path, note_path: str, content: str) -> None:
    """
    Append content to end of note.

    Args:
        vault_path: Vault root path
        note_path: Relative path to note
        content: Content to append (will add newlines for spacing)

    Raises:
        NoteNotFoundError: If note doesn't exist
    """

def update_note_section(vault_path: Path, note_path: str,
                       header: str, content: str) -> None:
    """
    Replace content under specific header (## Header).

    Args:
        vault_path: Vault root path
        note_path: Relative path to note
        header: Header text (without ## prefix)
        content: New content for section (replaces everything until next header)

    Raises:
        NoteNotFoundError: If note doesn't exist
        HeaderNotFoundError: If header doesn't exist in note
    """

def search_notes_by_metadata(vault_path: Path,
                             field: str, value: Any,
                             limit: int = 20) -> List[NoteInfo]:
    """
    Find notes where frontmatter[field] == value.

    Args:
        vault_path: Vault root path
        field: Frontmatter field name (e.g., "tags", "project", "status")
        value: Value to match (e.g., "SEO", "active", "work")
        limit: Max results (default 20)

    Returns:
        List of NoteInfo with path, title, metadata preview
    """

def create_note_in_folder(vault_path: Path, folder_path: str,
                         title: str, content: str = "",
                         metadata: Dict[str, Any] = None) -> Path:
    """
    Create note in arbitrary vault folder (not just notes/).

    Args:
        vault_path: Vault root path
        folder_path: Target folder (e.g., "Docs", "projects/work")
        title: Note title
        content: Note body (optional)
        metadata: Frontmatter fields (optional)

    Returns:
        Path to created note
    """
```

**MCP Tools (8 new):**
- `plorp_read_note` - Read single note
- `plorp_read_folder` - Read all notes in folder
- `plorp_append_to_note` - Append content to note
- `plorp_update_note_section` - Replace section under header
- `plorp_search_notes_by_tag` - Find notes with specific tag
- `plorp_search_notes_by_field` - Find notes by frontmatter field
- `plorp_create_note_in_folder` - Create note anywhere
- `plorp_list_vault_folders` - Get vault directory structure

**TypedDict Definitions:**
```python
# In core/types.py

class NoteContent(TypedDict):
    """Content returned by read_note."""
    path: str                    # Relative path in vault
    title: str                   # From frontmatter or first # header
    content: str                 # Full markdown content
    metadata: Dict[str, Any]     # YAML frontmatter
    word_count: int
    headers: List[str]           # List of ## headers
    mode: str                    # "full", "preview", etc.

class NoteInfo(TypedDict):
    """Metadata about a note (without full content)."""
    path: str
    title: str
    metadata: Dict[str, Any]
    word_count: int
    created: str                 # ISO timestamp
    modified: str                # ISO timestamp

class FolderReadResult(TypedDict):
    """Result from read_folder operation."""
    folder_path: str
    notes: List[NoteInfo]
    total_count: int
    returned_count: int
    has_more: bool
    excluded_folders: List[str]
```

---

#### Phase 2: Pattern Matching (Semi-Deterministic - Week 2)

**New parser module:** `parsers/note_structure.py`

**Functions:**
```python
def extract_headers(content: str, level: int = None) -> List[Header]:
    """
    Extract all headers from markdown content.

    Args:
        content: Markdown text
        level: Filter by header level (1-6), None = all levels

    Returns:
        List of Header TypedDicts with text, level, line_number
    """

def find_header_content(content: str, header: str) -> str:
    """
    Get content under specific header (until next same-level header).

    Args:
        content: Markdown text
        header: Header text to find (without # prefix)

    Returns:
        Content under header (empty string if header not found)
    """

def detect_project_headers(content: str) -> List[str]:
    """
    Find ### headers that look like project names.

    Pattern matching heuristics:
    - Level 3 headers (###)
    - Not in "Notes" or "Tasks" sections
    - Title-case or kebab-case format
    - Not common section names (Overview, Summary, etc.)

    Args:
        content: Markdown text (typically from daily note)

    Returns:
        List of potential project names
    """

def extract_bullet_points(content: str, section: str = None) -> List[str]:
    """
    Get all bullet points (- or *), optionally under specific section.

    Args:
        content: Markdown text
        section: Header name to extract bullets from (None = all bullets)

    Returns:
        List of bullet text (without - prefix)
    """

def extract_tags(content: str) -> List[str]:
    """
    Extract all #tags from content (Obsidian-style inline tags).

    Args:
        content: Markdown text

    Returns:
        List of unique tags (without # prefix)
    """
```

**MCP Tools (4 new):**
- `plorp_extract_headers` - Get document structure
- `plorp_get_section_content` - Read specific section by header
- `plorp_detect_projects_in_note` - Find project-like headers
- `plorp_extract_bullets` - Get all bullets from section

**TypedDict Definitions:**
```python
class Header(TypedDict):
    """Represents a markdown header."""
    text: str           # Header text (without # prefix)
    level: int          # 1-6 (number of # symbols)
    line_number: int    # 0-indexed line in content
```

---

#### Phase 3: Intelligent Workflows (Stochastic - Week 3)

**No new functions - documentation for Claude on combining tools.**

**Workflow Documentation:** `Docs/MCP_WORKFLOWS.md`

```markdown
## Workflow Patterns for Claude

### Pattern 1: "Read all notes with tag X"

**User says:** "Read all SEO notes and summarize"

**Claude's approach:**
1. plorp_search_notes_by_tag(tag="SEO")
   → Returns list of 5 notes with metadata
2. Check total word count across notes
   - If < 10k words: Read all notes fully
   - If > 10k words: Ask user which notes to read, or read previews
3. For each selected note:
   plorp_read_note(path, mode="full")
4. Synthesize summary across all content in context

**Context management:**
- Metadata search first (cheap)
- Selective full reads (expensive)
- Claude decides based on word_count fields

---

### Pattern 2: "Update project doc with today's notes"

**User says:** "Update the website redesign project with today's notes"

**Claude's approach:**
1. plorp_read_note("daily/2025-10-08.md")
   → Gets today's full note in context
2. plorp_extract_headers(content, level=3)
   → Finds ### headers (potential project sections)
3. plorp_extract_bullets(content, section="website redesign")
   → Gets bullets under that header
4. plorp_search_notes_by_field(field="project_name", value="website-redesign")
   → Finds project note at projects/work.marketing.website-redesign.md
5. plorp_read_note("projects/work.marketing.website-redesign.md")
   → Gets current project doc in context
6. **Claude decides** what's relevant from bullets
7. plorp_append_to_note("projects/work.marketing.website-redesign.md", relevant_content)
   → Adds notes under ## Notes section

**Intelligence applied:**
- Claude determines "relevant" (not all bullets belong in project)
- Claude formats content appropriately
- Claude may ask user for confirmation before appending

---

### Pattern 3: "Find or create project from header"

**User says:** "Check if there are projects in today's note and create them if missing"

**Claude's approach:**
1. plorp_read_note("daily/2025-10-08.md")
   → Full content in context
2. plorp_detect_projects_in_note(content)
   → Finds ["website redesign", "api rewrite"]
3. For each potential project:
   a. plorp_search_notes_by_field(field="project_name", value="website-redesign")
   b. If found: Report "Project exists at [path]"
   c. If not found: Ask user for domain/workstream
   d. plorp_create_project(name, domain, workstream)
4. Report results

**Decision points:**
- Claude interprets which headers are projects (not "Tasks", "Notes", etc.)
- Claude asks user for missing metadata (domain)
- Claude can batch questions ("I found 2 new projects, both look like work domain - confirm?")

---

### Pattern 4: "Read docs folder excluding archive"

**User says:** "Read all docs in /Docs but ignore /Docs/archive"

**Claude's approach:**
1. plorp_read_folder(
     folder_path="Docs",
     recursive=true,
     exclude=["archive"],
     limit=50,
     mode="metadata"
   )
   → Gets list of ~30 docs with metadata
2. Check total_count vs returned_count
   - If has_more=true: Ask user if they want to see all or filter
3. Ask user: "Found 30 docs. Read all, or specify which ones?"
4. Based on user response:
   - Option A: Read all (if <20 docs and <50k total words)
   - Option B: Show list, user picks specific ones
   - Option C: Read structure only (headers) for all
5. For selected docs:
   plorp_read_note(path, mode="full")

**Context management:**
- Metadata first (cheap operation)
- Ask before bulk read (avoid context exhaustion)
- Adaptive based on size
```

---

## Context Management Strategy

### The Problem

Reading many large files can exhaust Claude's 200k token context window:
- 10 notes × 5,000 words = ~50k words = ~65k tokens (~33% of context)
- 50 notes × 2,000 words = ~100k words = ~130k tokens (~65% of context)
- Sprint 8 spec alone = ~15k words = ~20k tokens (~10% of context)

**Without limits, users could accidentally consume entire context in 2-3 tool calls.**

### Design Principles

1. **Metadata-first**: Search returns metadata (path, title, word_count) before content
2. **Lazy loading**: Claude decides which notes to read fully
3. **Smart defaults**: Conservative limits that can be overridden
4. **Preview modes**: Offer truncated content for large files
5. **Warn, don't block**: Tell user if operation is expensive, let them decide

### Implementation Details

#### 1. Mode Parameter (All Read Operations)

```python
mode = "full" | "preview" | "metadata" | "structure"

# full - Entire content (default for single notes)
# preview - First 1000 characters + "..." + metadata
# metadata - Frontmatter only
# structure - Headers only (no body content)
```

**Example:**
```python
# Large file warning
result = read_note("Docs/ARCHITECTURE.md", mode="full")
if result["word_count"] > 10000:
    return {
        ...result,
        "warning": "This note is 15,000 words. Consider mode='preview' or 'structure' to save context."
    }
```

#### 2. Folder Scan Limits

```python
read_folder(path, limit=10, mode="metadata")

# Default: 10 notes, metadata only
# Max: 50 notes
# Returns: has_more flag if total_count > limit
```

**Example:**
```python
result = read_folder("notes", recursive=True)
# {
#   "notes": [...10 notes with metadata...],
#   "total_count": 47,
#   "returned_count": 10,
#   "has_more": true,
#   "suggestion": "Use limit=50 to see all, or filter with exclude=[...]"
# }
```

#### 3. Search Result Batching

```python
search_notes_by_tag("SEO", limit=20)

# Returns metadata for first 20 matches
# Claude can then selectively read_note() for specific ones
```

**Example workflow:**
```
1. User: "Read all SEO notes"
2. Claude: search_notes_by_tag("SEO") → 15 notes found
3. Claude checks: Sum of word_counts = 35,000 words (~45k tokens)
4. Claude decides: "Too large, ask user"
5. Claude: "Found 15 SEO notes (35k words total). Should I:
   - Read all (will use ~45k tokens = 22% of context)
   - Show you the list so you can pick specific ones
   - Read structure only (headers from each note)"
6. User chooses
```

#### 4. Adaptive Response Formatting

When returning large content, include usage hints:

```python
{
  "path": "Docs/SPRINT_8_SPEC.md",
  "content": "[... 15,000 words ...]",
  "word_count": 15000,
  "estimated_tokens": 19500,
  "context_usage": "~10% of 200k token budget",
  "suggestion": "If you only need specific sections, use plorp_get_section_content() instead"
}
```

#### 5. Scope Control via Config

**Config file: `~/.config/plorp/config.yaml`**

```yaml
vault_path: /Users/jsd/vault

# Note access control (Sprint 9)
note_access:
  # Folders plorp can read/write
  allowed_folders:
    - notes
    - projects
    - daily
    - inbox
    - Docs
    - _bases

  # Folders to always exclude from scans
  excluded_folders:
    - .obsidian
    - .trash
    - templates

  # Max file sizes
  max_file_size_kb: 500  # Warn if note > 500KB

  # Context protection
  max_folder_read: 50    # Max notes per folder scan
  warn_large_file_words: 10000  # Warn if note > 10k words
```

**Security model:**
- **Default:** Read/write only in allowed_folders
- **Override:** User can add folders to allowed list
- **Protection:** Never read .obsidian config or .trash
- **Transparency:** Tool returns error if path outside allowed folders

---

## Existing Sprint 9 Candidates (from Sprint 8)

### Sprint 9 Candidates (Validation & Cleanup)

**Note:** These were originally planned for Sprint 9 but may be **deferred to Sprint 10** given the scope of general note management.

1. **Hybrid workstream validation** (from Sprint 8 Q7)
   - CLI: Prompt for confirmation if workstream not in suggested list
   - MCP: Claude warns about unusual workstreams

2. **Project sync command** (from Sprint 8 Q3)
   - `plorp project sync <full-path>` to clean up orphaned task UUIDs
   - Validates all task_uuids, removes deleted tasks from frontmatter

3. **Orphaned project review workflow**
   - Interactive workflow to assign workstream to 2-segment projects
   - Batch process projects with `needs_review: true`

4. **Orphaned task review workflow**
   - Help user assign domain/project to tasks with `project.none:`
   - Low-friction capture → organize later pattern

5. **Clarify `/process` vs `/review` workflow boundaries** (from Sprint 8 discussion)
   - **Current confusion**: `/process` only converts informal tasks (no UUID) → formal tasks (with UUID)
   - **Gap identified**: No automatic sync when user checks off formal tasks in daily note
   - **User expectation**: Checking a box in Obsidian should mark task done in TaskWarrior
   - **Options to evaluate**:
     - A: Keep workflows separate (current design - `/process` = conversion, `/review` = sync)
     - B: Extend `/process` Step 2 to also sync checkbox state for formal tasks
     - C: Create new `plorp sync` command specifically for checkbox → TaskWarrior sync
     - D: Make checkbox sync automatic on daily note read (background process)
   - **Decision needed**: Clarify workflow responsibilities and determine if duplication is acceptable

**PM Decision Point:** Evaluate Sprint 9 scope and potentially defer items 1-4 to Sprint 10 if general note management takes full sprint.

---

## Implementation Plan

### Phase 1: Core Note I/O (Week 1, ~8 hours)

**Deliverables:**
- `integrations/obsidian_notes.py` - 6 functions
- `core/note_operations.py` - High-level API wrapping integrations
- TypedDict definitions in `core/types.py`
- 8 new MCP tools in `mcp/server.py`
- Configuration schema updates for `note_access`

**Files to create/modify:**
- New: `src/plorp/integrations/obsidian_notes.py`
- New: `src/plorp/core/note_operations.py`
- Modify: `src/plorp/core/types.py` (add NoteContent, NoteInfo, FolderReadResult)
- Modify: `src/plorp/mcp/server.py` (add 8 tools)
- Modify: `src/plorp/config.py` (add note_access schema)
- New: `Docs/NOTE_ACCESS.md` (security and config documentation)

**Tests:**
- Unit tests: `tests/test_integrations/test_obsidian_notes.py` (~15 tests)
- Integration tests: `tests/test_core/test_note_operations.py` (~10 tests)
- MCP tests: `tests/test_mcp/test_note_tools.py` (~8 tests)

**Success criteria:**
- Can read any note in vault (in allowed folders)
- Can read folder with filtering
- Can append to note
- Can update section under header
- Can search by tag/field
- All operations respect config permissions
- Large file warnings work

---

### Phase 2: Pattern Matching (Week 2, ~6 hours)

**Deliverables:**
- `parsers/note_structure.py` - 5 functions for structure analysis
- 4 new MCP tools for pattern detection
- Update MCP documentation with pattern examples

**Files to create/modify:**
- New: `src/plorp/parsers/note_structure.py`
- Modify: `src/plorp/mcp/server.py` (add 4 tools)
- Modify: `src/plorp/core/types.py` (add Header TypedDict)

**Tests:**
- Unit tests: `tests/test_parsers/test_note_structure.py` (~12 tests)
- Integration tests with real daily notes

**Success criteria:**
- Can extract headers at any level
- Can get content under specific header
- Can detect project-like headers (with test cases from real daily notes)
- Can extract bullets from specific sections
- Can extract inline #tags

---

### Phase 3: Workflows & Documentation (Week 2-3, ~4 hours)

**Deliverables:**
- Workflow documentation for Claude
- User manual updates
- Example interactions
- MCP tool catalog updates

**Files to create/modify:**
- New: `Docs/MCP_WORKFLOWS.md` (patterns for Claude)
- Update: `Docs/MCP_USER_MANUAL.md` (add note management section)
- Update: `Docs/MCP_TOOL_CATALOG.md` (add 12 new tools)
- New: `examples/note_management_workflows.md` (user examples)

**Success criteria:**
- Claude Desktop can execute all example workflows
- Documentation explains intelligent vs deterministic operations
- Context management strategy is clear
- Users understand allowed_folders config

---

### Phase 4: Polish & Testing (Week 3, ~2 hours)

**Deliverables:**
- Address any issues found during Phase 1-3 testing
- Performance optimization if needed
- Final integration testing

**Files to modify:**
- Any files needing refinement based on testing

**Success criteria:**
- All Sprint 9 tests passing (80+ new tests)
- No regressions in existing functionality
- Performance meets requirements (<2s folder reads)

---

## Testing Strategy

### Unit Tests (35 tests)

**`tests/test_integrations/test_obsidian_notes.py`** (~15 tests)
- `test_read_note_full_mode()`
- `test_read_note_preview_mode()`
- `test_read_note_metadata_mode()`
- `test_read_note_structure_mode()`
- `test_read_note_not_found()`
- `test_read_folder_with_limit()`
- `test_read_folder_recursive()`
- `test_read_folder_with_exclude()`
- `test_append_to_note()`
- `test_update_note_section()`
- `test_update_note_section_header_not_found()`
- `test_search_notes_by_tag()`
- `test_search_notes_by_field()`
- `test_create_note_in_folder()`
- `test_large_file_warning()`

**`tests/test_parsers/test_note_structure.py`** (~12 tests)
- `test_extract_headers_all_levels()`
- `test_extract_headers_specific_level()`
- `test_find_header_content()`
- `test_find_header_content_not_found()`
- `test_detect_project_headers()`
- `test_detect_project_headers_excludes_common_sections()`
- `test_extract_bullet_points_all()`
- `test_extract_bullet_points_from_section()`
- `test_extract_tags()`
- etc.

**`tests/test_core/test_note_operations.py`** (~10 tests)
- High-level API tests
- Permission checking tests
- Config validation tests

### Integration Tests (10 tests)

**`tests/test_mcp/test_note_tools.py`** (~8 tests)
- End-to-end MCP tool tests
- Context size verification
- Error handling

**Real Vault Tests** (~2 tests)
- Test with user's actual vault structure
- Verify allowed_folders enforcement

### Manual Testing Checklist

- [ ] Read note via MCP in Claude Desktop
- [ ] Read folder with recursive flag
- [ ] Append content to existing note
- [ ] Update section under ## header
- [ ] Search notes by tag
- [ ] Create note in Docs/ folder
- [ ] Verify large file warning appears
- [ ] Test with note outside allowed_folders (should error)
- [ ] Execute "read all SEO notes" workflow
- [ ] Execute "update project from daily note" workflow

---

## Success Criteria

### Functional Requirements

- [ ] Can read any note in allowed folders (config enforced)
- [ ] Can read folder with recursive and exclude filters
- [ ] Can append content to notes
- [ ] Can update specific sections by header
- [ ] Can search notes by tags and frontmatter fields
- [ ] Can create notes in arbitrary folders (within allowed list)
- [ ] Can extract document structure (headers, bullets, tags)
- [ ] Can detect project-like headers in daily notes
- [ ] Large file warnings work (>10k words)
- [ ] Folder scan limits work (default 10, max 50)
- [ ] Config validation prevents access outside allowed folders

### MCP Integration

- [ ] 12 new MCP tools registered and working
- [ ] Tools return proper TypedDict structures
- [ ] Error messages are clear and actionable
- [ ] Content returned enters Claude's context correctly
- [ ] Context usage hints included in large responses

### Testing

- [ ] 80+ tests passing (35 unit + 10 integration + existing)
- [ ] No regressions in Sprint 1-8 functionality
- [ ] Manual testing checklist complete

### Documentation

- [ ] MCP_WORKFLOWS.md created with 4+ workflow patterns
- [ ] MCP_USER_MANUAL.md updated with note management section
- [ ] MCP_TOOL_CATALOG.md updated with 12 new tools
- [ ] NOTE_ACCESS.md explains security model and config
- [ ] Example interactions documented

### Performance

- [ ] Read folder with 100 notes completes in <2 seconds
- [ ] Large file (50k words) warning displays immediately
- [ ] Metadata search across 1000 notes completes in <5 seconds

---

## Dependencies

### Required from Previous Sprints

**Sprint 6 (MCP Architecture):**
- ✅ MCP server infrastructure
- ✅ Tool registration system
- ✅ TypedDict-based returns

**Sprint 7 (/process workflow):**
- ✅ Markdown parsing utilities
- ✅ Section extraction patterns
- ✅ Daily note structure knowledge

**Sprint 8 (Project Management):**
- ✅ Obsidian Bases integration patterns
- ✅ Frontmatter parsing
- ✅ Folder scanning utilities

### External Dependencies

- Python 3.8+
- PyYAML (existing dependency)
- pathlib (standard library)
- re (standard library)
- Obsidian vault at configured path

### Configuration

**Requires:** `~/.config/plorp/config.yaml` with `note_access` section:
```yaml
note_access:
  allowed_folders:
    - notes
    - projects
    - daily
    - inbox
    - Docs
```

---

## Risks & Mitigation

### Risk 1: Context Exhaustion

**Risk:** Users accidentally consume entire 200k context with bulk reads.

**Mitigation:**
- Smart defaults (limit=10, mode="metadata")
- Warnings for large files/folders
- Metadata-first approach
- Documentation emphasizes selective reading

**Monitoring:** Include context usage hints in tool responses.

---

### Risk 2: Permission/Security Issues

**Risk:** User accidentally gives plorp access to sensitive folders or files.

**Mitigation:**
- Whitelist approach (allowed_folders in config)
- Never read .obsidian or .trash by default
- Clear error messages when accessing forbidden paths
- Documentation explains security model

**Testing:** Unit tests verify permission enforcement.

---

### Risk 3: Breaking Existing Workflows

**Risk:** New note operations conflict with daily/inbox/project workflows.

**Mitigation:**
- New tools are **additive**, not replacements
- Existing high-level workflows unchanged
- Low-level primitives coexist with high-level workflows
- Regression tests for all Sprint 1-8 functionality

**Testing:** Full test suite must pass before Sprint 9 sign-off.

---

### Risk 4: Performance Degradation

**Risk:** Scanning large vaults is slow.

**Mitigation:**
- Implement limits and pagination
- Use generators for large folder scans
- Cache folder structure (future optimization)
- Profile operations during testing

**Acceptable:** <2s for folder with 100 notes, <5s for metadata search across 1000 notes.

---

## Open Questions

### Q1: Should note access be unrestricted or whitelist-based?

**Context:** Users might want to read notes in custom folders not in default list.

**Options:**
- A: Unrestricted - Read/write anywhere in vault (max flexibility)
- B: Whitelist with easy config override (recommended)
- C: Prompt for confirmation outside known folders (interactive)

**Recommendation:** Option B. Config file allows power users to expand, default is safe.

**Implementation:**
```yaml
# Default allowed_folders
allowed_folders: [notes, projects, daily, inbox, Docs]

# User can add custom folders
allowed_folders: [notes, projects, daily, inbox, Docs, journal, ideas]
```

**Status:** ⏳ PENDING - Need user input

---

### Q2: Should plorp cache folder structure or scan on every call?

**Context:** Scanning vault/notes with 500+ files might be slow.

**Options:**
- A: No caching - Scan filesystem every time (simple, always fresh)
- B: Cache folder structure, invalidate on write (complex, faster)
- C: Cache with TTL (5 minute expiry) (balanced)

**Recommendation:** Option A for Sprint 9, Option C for Sprint 10 if needed.

**Rationale:**
- Sprint 9 focus is getting functionality working
- Optimize only if performance issues arise
- Obsidian users don't create hundreds of notes per hour
- Caching adds complexity (invalidation, stale data)

**Status:** ✅ RESOLVED - No caching in Sprint 9

---

### Q3: How should plorp handle notes edited outside plorp?

**Context:** User might edit note in Obsidian while Claude has old content in context.

**Options:**
- A: Ignore - Not plorp's responsibility (recommended for Sprint 9)
- B: Add "last modified" timestamp check (warn if stale)
- C: Re-read note before every write (slow, safe)

**Recommendation:** Option A. Claude Desktop sessions are short (<1 hour typically).

**Future:** Option B in Sprint 10 if users report issues.

**Status:** ✅ RESOLVED - No staleness detection in Sprint 9

---

### Q4: Should CLI commands be created for note operations?

**Context:** All operations accessible via MCP. CLI wrappers are optional.

**Options:**
- A: MCP-only (recommended for Sprint 9)
- B: Add CLI wrappers: `plorp note read <path>`, `plorp note search <query>`
- C: Add only most useful CLI commands (read, search)

**Recommendation:** Option A. MCP is primary interface. Add CLI in Sprint 10 if users request.

**Rationale:**
- Sprint 9 scope is already large
- CLI adds development time with minimal user benefit
- Power users can use Obsidian's built-in search
- MCP tools provide full functionality via Claude Desktop

**Status:** ✅ RESOLVED - No CLI wrappers in Sprint 9

---

### Q5: How to handle malformed frontmatter or invalid markdown?

**Context:** User notes might have syntax errors, broken YAML, etc.

**Options:**
- A: Strict - Return error if frontmatter invalid (fails early)
- B: Lenient - Parse what's possible, skip broken frontmatter (forgiving)
- C: Hybrid - Warn about issues but still return content (recommended)

**Recommendation:** Option C.

**Implementation:**
```python
result = read_note("notes/broken.md")
# {
#   "content": "[full content even if frontmatter broken]",
#   "metadata": {},  # Empty if parse failed
#   "warnings": ["Could not parse YAML frontmatter: expected key:value on line 3"]
# }
```

**Rationale:**
- Obsidian is forgiving with markdown
- Users may have notes from other systems
- Better to return partial data than fail completely
- Warnings inform without blocking

**Status:** ⏳ PENDING - Implementation decision

---

## Version History

- **v1.0.0** (2025-10-08) - Initial Sprint 9 spec
  - General note management vision
  - MCP context behavior documented
  - Three-phase architecture
  - Context management strategy
  - Integration with Sprint 8 candidates

---

## PM Sign-Off Checklist

**Pre-Implementation:**
- [ ] Vision aligns with user goals
- [ ] Architecture is sound (3 phases)
- [ ] Open questions resolved
- [ ] Scope is reasonable for sprint (18-20 hours)
- [ ] Dependencies identified
- [ ] Risks mitigated

**Post-Implementation:**
- [ ] All 80+ tests passing
- [ ] 12 MCP tools working in Claude Desktop
- [ ] Documentation complete
- [ ] Manual testing checklist complete
- [ ] No regressions in Sprint 1-8 functionality
- [ ] Performance acceptable (<2s folder reads)
- [ ] Security model enforced (allowed_folders)

**Sign-Off:** _______________  Date: ___________

---

## Document Status

**Version:** 1.0.0
**Status:** 📋 DRAFT - Awaiting PM Review
**Last Updated:** 2025-10-08
**Next Review:** After user feedback on scope and open questions

**Outstanding Items:**
- Q1: Whitelist vs unrestricted access (pending user input)
- Q4: CLI wrappers decision (resolved - no CLI in Sprint 9)
- Q5: Malformed frontmatter handling (pending implementation decision)
