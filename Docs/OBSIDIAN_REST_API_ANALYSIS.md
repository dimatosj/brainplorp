# Obsidian REST API Analysis: Enhanced Capabilities for Future Sprints

**Date:** 2025-10-08
**Status:** 📋 Reference Document
**Related Sprint:** Sprint 9 (filesystem approach), Sprint 10+ (REST API enhancement candidate)

---

## Executive Summary

The [Obsidian Local REST API plugin](https://github.com/coddingtonbear/obsidian-local-rest-api) provides advanced vault operations not easily achievable via filesystem access. This document analyzes capabilities that could enhance plorp in future sprints.

**Key Finding:** REST API offers **intelligent Obsidian-native operations** (search, tag parsing, section editing) that would otherwise require complex parsing logic. However, it requires Obsidian to be running.

**Recommendation:** Keep filesystem as primary (Sprint 9), add optional REST API mode in Sprint 10+ for users who want enhanced features when Obsidian is open.

---

## REST API vs Filesystem: Capability Comparison

### What Filesystem CAN Do (Sprint 9 approach)

✅ **Core read/write operations**
- Read any markdown file in vault
- Write/create files anywhere
- Append content to files
- Parse frontmatter (with PyYAML)
- List folder contents
- Works without Obsidian running
- Works on headless/mobile environments

✅ **What we control**
- File format conventions
- Parsing logic
- Error handling
- No external dependencies (beyond Python)

### What REST API ADDS (unique capabilities)

#### 1. 🔍 **Advanced Search Capabilities**

**REST API provides three search modes:**

**a) Simple Text Search** (`/search/simple/`)
```python
# Returns matches with context
{
  "filename": "notes/idea.md",
  "matches": [
    {
      "context": "...some context around the match...",
      "match": {"start": 45, "end": 53}
    }
  ],
  "score": 0.95
}
```

**b) JsonLogic Search** (powerful filtering)
```json
// Find all notes tagged "SEO" in "work" folder
{
  "and": [
    {"glob": ["*.md", {"var": "path"}]},
    {"regexp": [".*work.*", {"var": "path"}]},
    {"in": ["SEO", {"var": "tags"}]}
  ]
}
```

**c) DataView DQL Queries** (most powerful)
```sql
TABLE file.mtime, tags
FROM #project
WHERE file.mtime >= date(today) - dur(7 days)
SORT file.mtime DESC
LIMIT 10
```

**Filesystem equivalent:** We'd need to:
- Implement custom search indexing
- Parse all markdown files
- Extract tags manually (regex)
- Filter by complex criteria
- Rank results

**Complexity saved:** ~500-800 lines of search code

---

#### 2. ✂️ **Intelligent Section Editing (PATCH operations)**

**REST API `/vault/{file}` PATCH:**

```http
PATCH /vault/notes/idea.md
Headers:
  Operation: append
  Target-Type: heading
  Target: Project Ideas::Q4 Goals
Body: "- New goal for Q4"
```

This will:
- Find the "Project Ideas" section
- Find the "Q4 Goals" subsection
- Append content under that specific heading
- Handle nested heading hierarchy (:: delimiter)
- Preserve formatting

**Operations supported:**
- `append` - Add after target
- `prepend` - Add before target
- `replace` - Replace target content

**Target types:**
- `heading` - By markdown header (nested: `Parent::Child::Grandchild`)
- `block` - By block reference ID (`^block-id`)
- `frontmatter` - By YAML field name

**Filesystem equivalent:** We'd need to:
- Parse markdown AST
- Find heading hierarchy
- Calculate insertion points
- Preserve indentation/formatting
- Handle edge cases (no heading found, etc.)

**What we have in Sprint 9:**
```python
def update_note_section(path, header, content):
    # Find header
    # Replace everything until next same-level header
    # Write back
```

**What REST API adds:**
- Nested heading paths (`Parent::Child`)
- Block reference targeting (`^abc123`)
- Frontmatter field updates
- Three operations (append/prepend/replace) not just replace

**Complexity saved:** ~200-300 lines of parsing code

---

#### 3. 🏷️ **Automatic Tag & Metadata Extraction**

**REST API returns parsed structure:**

```http
GET /vault/notes/idea.md
Accept: application/vnd.olrapi.note+json
```

**Response:**
```json
{
  "path": "notes/idea.md",
  "content": "# My Note\n\nContent with #tag1 and #tag2",
  "frontmatter": {
    "status": "active",
    "project": "website-redesign"
  },
  "tags": ["tag1", "tag2"],  // Automatically extracted
  "stat": {
    "ctime": 1728000000,
    "mtime": 1728100000,
    "size": 1024
  }
}
```

**What this gives us:**
- ✅ Tags parsed from content (inline `#tags`)
- ✅ Tags from frontmatter (merged)
- ✅ File modification times
- ✅ Frontmatter pre-parsed
- ✅ All in one API call

**Filesystem equivalent:**
```python
# Read file
content = read_file(path)

# Parse frontmatter
frontmatter = parse_frontmatter(content)

# Extract inline tags (regex)
tags = re.findall(r'#(\w+)', content)

# Get file stats
stat = os.stat(path)

# Merge tags from frontmatter and content
all_tags = merge_tags(frontmatter.get('tags', []), tags)
```

**Complexity saved:** ~100-150 lines of parsing + tag logic

---

#### 4. 📅 **Periodic Notes Integration**

**REST API has built-in periodic notes support:**

```http
GET /periodic/daily/
```

Returns today's daily note (auto-detected path from Obsidian settings).

**Supported periods:**
- `daily` - Today's daily note
- `weekly` - This week's note
- `monthly` - This month's note
- `quarterly` - This quarter's note
- `yearly` - This year's note

**Also:**
```http
GET /periodic/daily/recent?limit=5&includeContent=true
```

Returns last 5 daily notes with content.

**Filesystem equivalent:**
- Hardcode daily note path format (inflexible)
- Calculate dates for weekly/monthly/quarterly
- Don't support user's custom paths
- Manually implement "recent notes" logic

**What this solves:**
- User's custom daily note format (e.g., `YYYY/MM/YYYY-MM-DD.md`)
- Obsidian settings integration (reads user's template paths)
- Weekly/monthly notes without date math

**Complexity saved:** ~150-200 lines of date logic + path conventions

---

#### 5. 🎯 **Active File Operations**

**REST API knows which file is currently open:**

```http
GET /active/
```

Returns currently active file in Obsidian.

**Use cases:**
- "Append this to the current note I'm looking at"
- "What tags are in the active note?"
- "Update the current note's frontmatter"

**Filesystem equivalent:** Impossible. We have no idea which file user has open.

**What this enables:**
- Context-aware MCP commands
- "Add this to the note I'm working on" (no need to specify path)
- Real-time collaboration with Obsidian UI

---

#### 6. 🔧 **Obsidian Command Execution**

**REST API can execute ANY Obsidian command:**

```http
GET /commands/
```

Returns list of all available commands:
```json
{
  "commands": [
    {"id": "global-search:open", "name": "Search: Search in all files"},
    {"id": "graph:open", "name": "Graph view: Open graph view"},
    {"id": "daily-notes:open-today", "name": "Daily notes: Open today's note"}
  ]
}
```

**Execute command:**
```http
POST /commands/graph:open/
```

**What this enables:**
- Open graph view after creating project note
- Trigger Obsidian search from plorp
- Open daily note in Obsidian from CLI
- Any plugin command (if installed)

**Filesystem equivalent:** Impossible. No way to control Obsidian UI.

---

## Architecture Implications

### Current Approach (Sprint 9): Filesystem Primary ✅

**Philosophy:** plorp works anywhere, anytime
- ✅ No Obsidian required to be running
- ✅ Works on headless servers, cron jobs
- ✅ Mobile/tablet compatible
- ✅ No plugin dependencies
- ✅ Direct file access (fast)

**Trade-offs:**
- ⚠️ Manual parsing (tags, sections, metadata)
- ⚠️ No access to Obsidian-specific features (graph, search, active file)
- ⚠️ Can't execute Obsidian commands

---

### Future Enhancement (Sprint 10+): Optional REST API Mode 📋

**Philosophy:** Enhanced capabilities when Obsidian is open

**Config-based switching:**
```yaml
# ~/.config/plorp/config.yaml
obsidian_integration:
  mode: "filesystem"  # or "rest_api" or "hybrid"

  rest_api:
    host: "127.0.0.1"
    port: 27124
    api_key: "your-api-key-here"

  # If hybrid: use REST API when available, fallback to filesystem
  prefer_rest_api: true  # Try REST API first
```

**Hybrid mode implementation:**
```python
def read_note_with_metadata(path: str) -> NoteContent:
    """Read note with full metadata."""

    if config.obsidian_mode == "rest_api" or config.prefer_rest_api:
        # Try REST API first
        if rest_client.is_available():
            return rest_client.get_note(path)  # Gets tags, frontmatter parsed

    # Fallback to filesystem
    return filesystem.read_note(path)  # Parse ourselves
```

**When to use REST API mode:**

✅ **User at desktop with Obsidian open:**
- MCP commands from Claude Desktop
- Interactive plorp sessions
- Advanced search requirements

✅ **Automation that can "wake up" Obsidian:**
- `plorp start --open-obsidian` (opens Obsidian, uses REST API)
- Scripts that assume desktop environment

❌ **When NOT to use REST API:**
- Cron jobs (Obsidian not running)
- Headless servers
- Mobile environments
- User prefers Obsidian closed

---

## Specific Sprint 10+ Enhancements

### Enhancement 1: Advanced Search Tools

**New MCP tools (REST API mode only):**

```python
@mcp.tool()
def plorp_search_advanced(query: dict) -> List[NoteInfo]:
    """
    Advanced search using JsonLogic.

    Example:
        query = {
            "and": [
                {"glob": ["*.md", {"var": "path"}]},
                {"in": ["SEO", {"var": "tags"}]},
                {">=": [{"var": "stat.mtime"}, timestamp_7_days_ago]}
            ]
        }

    Returns notes matching complex criteria.
    Requires: Obsidian running with REST API plugin
    """
    if not rest_client.is_available():
        raise RuntimeError("Obsidian REST API not available. Open Obsidian or use plorp_search_notes_by_tag for basic search.")

    return rest_client.search_json(query)

@mcp.tool()
def plorp_search_dql(dql_query: str) -> List[dict]:
    """
    Search using DataView DQL query.

    Example:
        dql_query = '''
        TABLE file.mtime AS "Modified", tags
        FROM #project
        WHERE file.mtime >= date(today) - dur(7 days)
        SORT file.mtime DESC
        '''

    Requires: Obsidian running with Dataview plugin
    """
    return rest_client.search_dql(dql_query)
```

**Estimated effort:** 4-6 hours (wrapper + tests)

---

### Enhancement 2: Intelligent Section Editing

**New MCP tools:**

```python
@mcp.tool()
def plorp_patch_section(
    filepath: str,
    operation: str,  # "append" | "prepend" | "replace"
    target_type: str,  # "heading" | "block" | "frontmatter"
    target: str,
    content: str
) -> str:
    """
    Insert content relative to heading, block, or frontmatter field.

    Examples:
        # Append under nested heading
        plorp_patch_section(
            "notes/ideas.md",
            "append",
            "heading",
            "2025::Q4 Goals",
            "- New goal item"
        )

        # Update frontmatter field
        plorp_patch_section(
            "notes/ideas.md",
            "replace",
            "frontmatter",
            "status",
            "completed"
        )

    Requires: Obsidian running with REST API plugin
    Fallback: Use filesystem update_note_section (heading only)
    """
    if rest_client.is_available():
        return rest_client.patch_content(filepath, operation, target_type, target, content)
    elif target_type == "heading":
        # Fallback for simple heading updates
        return filesystem.update_note_section(filepath, target, content)
    else:
        raise RuntimeError("Block/frontmatter patching requires Obsidian REST API")
```

**Estimated effort:** 3-4 hours (wrapper + fallback logic + tests)

---

### Enhancement 3: Active Note Operations

**New MCP tools:**

```python
@mcp.tool()
def plorp_get_active_note() -> NoteContent:
    """
    Get the note currently open in Obsidian.

    Use case: "Append this to the note I'm currently looking at"

    Requires: Obsidian running with REST API plugin
    """
    if not rest_client.is_available():
        raise RuntimeError("Obsidian must be running. Open Obsidian to use active note features.")

    return rest_client.get_active_note()

@mcp.tool()
def plorp_append_to_active_note(content: str) -> str:
    """
    Append content to currently active note in Obsidian.

    Requires: Obsidian running with REST API plugin
    """
    return rest_client.append_to_active(content)
```

**User experience:**
```
User: "Add this bug report to the note I'm working on"
Claude: [calls plorp_get_active_note() → "projects/work.api-rewrite.md"]
Claude: [calls plorp_append_to_active_note(bug_report)]
Claude: "Added to projects/work.api-rewrite.md"
```

**Estimated effort:** 2-3 hours (simple wrappers + tests)

---

### Enhancement 4: Obsidian Command Integration

**New MCP tools:**

```python
@mcp.tool()
def plorp_open_in_obsidian(filepath: str) -> str:
    """
    Open specified note in Obsidian.

    Requires: Obsidian running with REST API plugin
    """
    if not rest_client.is_available():
        return f"Obsidian not running. To open {filepath}, launch Obsidian and run this command again."

    rest_client.open_file(filepath)
    return f"Opened {filepath} in Obsidian"

@mcp.tool()
def plorp_execute_obsidian_command(command_id: str) -> str:
    """
    Execute any Obsidian command.

    Examples:
        plorp_execute_obsidian_command("graph:open")  # Open graph view
        plorp_execute_obsidian_command("daily-notes:open-today")  # Open daily note

    Use plorp_list_obsidian_commands() to see available commands.

    Requires: Obsidian running with REST API plugin
    """
    return rest_client.execute_command(command_id)

@mcp.tool()
def plorp_list_obsidian_commands() -> List[dict]:
    """Get list of all available Obsidian commands."""
    return rest_client.list_commands()
```

**User experience:**
```
User: "Create a project note for the API rewrite, then show it in the graph view"
Claude: [calls plorp_create_project(...)]
Claude: [calls plorp_open_in_obsidian("projects/work.engineering.api-rewrite.md")]
Claude: [calls plorp_execute_obsidian_command("graph:open")]
Claude: "Created project and opened in graph view"
```

**Estimated effort:** 3-4 hours (wrappers + command discovery + tests)

---

## Implementation Strategy for Sprint 10+

### Phase 1: REST API Client Infrastructure (~4 hours)

**Create:** `src/plorp/integrations/obsidian_rest_client.py`

```python
class ObsidianRESTClient:
    """Client for Obsidian Local REST API plugin."""

    def __init__(self, host: str, port: int, api_key: str):
        self.base_url = f"https://{host}:{port}"
        self.api_key = api_key
        self.verify_ssl = False  # Self-signed cert

    def is_available(self) -> bool:
        """Check if REST API is running."""
        try:
            response = requests.get(f"{self.base_url}/", timeout=2)
            return response.status_code == 200
        except:
            return False

    def get_note(self, path: str) -> NoteContent:
        """Read note with automatic tag/metadata parsing."""
        response = requests.get(
            f"{self.base_url}/vault/{path}",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/vnd.olrapi.note+json"
            }
        )
        data = response.json()
        return {
            "path": data["path"],
            "content": data["content"],
            "metadata": data["frontmatter"],
            "tags": data["tags"],  # Parsed automatically
            "modified": data["stat"]["mtime"]
        }

    # ... other methods
```

**Config integration:**
```python
# src/plorp/config.py
class Config:
    def __init__(self):
        # ... existing fields
        self.obsidian_mode = config_data.get("obsidian_integration", {}).get("mode", "filesystem")
        self.rest_api_config = config_data.get("obsidian_integration", {}).get("rest_api", {})

        if self.obsidian_mode in ["rest_api", "hybrid"]:
            self.rest_client = ObsidianRESTClient(
                host=self.rest_api_config.get("host", "127.0.0.1"),
                port=self.rest_api_config.get("port", 27124),
                api_key=self.rest_api_config["api_key"]
            )
```

---

### Phase 2: Enhanced MCP Tools (~8 hours)

**Add to:** `src/plorp/mcp/server.py`

- 4 search tools (simple, jsonlogic, dql, active file search)
- 3 section editing tools (patch heading, patch block, patch frontmatter)
- 3 active note tools (get active, append to active, open in obsidian)
- 2 command tools (execute command, list commands)

**Total:** 12 new REST API-enhanced tools

---

### Phase 3: Fallback Logic & Hybrid Mode (~4 hours)

**Wrapper pattern:**
```python
def read_note_enhanced(path: str) -> NoteContent:
    """Read note with best available method."""

    # Try REST API if configured
    if config.prefer_rest_api and config.rest_client.is_available():
        return config.rest_client.get_note(path)

    # Fallback to filesystem
    return obsidian_notes.read_note(path)
```

**User feedback when REST API unavailable:**
```python
# In MCP tool response
if not rest_client.is_available():
    return {
        "error": "Enhanced search requires Obsidian REST API",
        "suggestion": "Open Obsidian to enable advanced search, or use plorp_search_notes_by_tag for basic search",
        "fallback_available": True
    }
```

---

### Phase 4: Documentation & Testing (~4 hours)

**Documents to create:**
- `Docs/OBSIDIAN_REST_API_SETUP.md` - Plugin install, API key setup
- `Docs/MCP_ENHANCED_FEATURES.md` - What REST API mode enables
- Update `Docs/MCP_TOOL_CATALOG.md` - Mark which tools need REST API

**Tests:**
- Mock REST API responses
- Fallback behavior tests
- Integration tests with actual plugin (manual)

---

## User Experience Scenarios

### Scenario 1: Desktop Power User

**Setup:**
```yaml
obsidian_integration:
  mode: "hybrid"
  rest_api:
    api_key: "abc123"
  prefer_rest_api: true
```

**Experience:**
- Obsidian open → Advanced search, intelligent patching, active note features
- Obsidian closed → Basic filesystem operations still work
- Best of both worlds

---

### Scenario 2: Headless Automation

**Setup:**
```yaml
obsidian_integration:
  mode: "filesystem"
```

**Experience:**
- Cron job runs `plorp start` → Works fine (no Obsidian needed)
- Server environment → No REST API dependency
- Reliable automation

---

### Scenario 3: Mobile/Tablet

**Setup:**
```yaml
obsidian_integration:
  mode: "filesystem"
```

**Experience:**
- Mobile Obsidian doesn't support REST API plugin
- Filesystem mode works everywhere
- No functionality loss on mobile

---

## Migration Path

### Sprint 9 (Current): Filesystem Foundation ✅
- Core note I/O primitives
- Basic search (tag, field)
- Section editing (replace only)
- **No REST API dependency**

### Sprint 10: Optional REST API Enhancement 📋
- Add REST API client
- Enhanced search tools
- Intelligent section patching
- Active note operations
- **Backward compatible - filesystem still works**

### Sprint 11+: Advanced Integration 🔮
- Obsidian command automation
- Graph API integration
- Plugin-specific features (Dataview, Templater)
- **Progressive enhancement**

---

## Cost-Benefit Analysis

### Filesystem Approach (Sprint 9)

**Costs:**
- ~500 lines: Search implementation
- ~200 lines: Section parsing
- ~150 lines: Tag extraction
- ~150 lines: Periodic note path logic
- **Total:** ~1000 lines of parsing/search code

**Benefits:**
- ✅ Works anywhere
- ✅ No external dependencies
- ✅ Full control over logic
- ✅ Reliable (no network/plugin issues)

### REST API Approach (Sprint 10+)

**Costs:**
- Plugin dependency (users must install)
- Obsidian must be running
- Network overhead (localhost, but still HTTP)
- Plugin compatibility (versions, updates)

**Benefits:**
- ✅ ~1000 lines of code we DON'T write
- ✅ Obsidian-native search (DQL, JsonLogic)
- ✅ Intelligent section editing (nested headings, blocks)
- ✅ Active file awareness
- ✅ Command execution
- ✅ Automatic tag/metadata parsing

**Break-even point:** If >30% of users use REST API features, code savings justify maintenance burden.

---

## Recommendation Summary

### For Sprint 9 (Now) ✅

**Build on filesystem as spec'd.** This gives us:
- Core functionality working everywhere
- No external dependencies
- Foundation for all future work

**Reference this document** in Sprint 9 spec as "Future Enhancement" section.

### For Sprint 10 (Later) 📋

**Add optional REST API mode.** This gives power users:
- Advanced search when Obsidian is open
- Intelligent editing features
- Active note operations
- Obsidian command integration

**Key principle:** REST API is an **enhancement**, not a **replacement**.

### Decision Rules for Users

**Use filesystem mode if:**
- Running plorp in automation/cron
- Using headless/server environments
- Prefer Obsidian closed while working
- Want maximum reliability

**Use REST API mode if:**
- Always work with Obsidian open (desktop)
- Want advanced search (DQL queries)
- Need active file awareness
- Want Obsidian command integration

**Use hybrid mode if:**
- Want best of both worlds
- Tolerate "feature degrades gracefully" UX

---

## AI-Enhanced Features (Sprint 11+)

**Note:** These were deferred from Sprint 9 but are planned for future sprints. They represent intelligence layers on top of the foundation built in Sprints 9-10.

### Feature 1: Semantic Search / Embeddings 🔮

**Vision:** Find notes by meaning, not just keywords.

**Example use cases:**
- "Find notes about productivity even if they don't use the word 'productivity'"
- "Show me all notes similar to this one"
- "What notes discuss the same concepts as the API rewrite project?"

**Technical approach:**

```python
from sentence_transformers import SentenceTransformer

class SemanticNoteSearch:
    """Semantic search using embeddings."""

    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None  # FAISS or similar

    def index_vault(self, vault_path: Path):
        """Generate embeddings for all notes."""
        notes = read_all_notes(vault_path)
        embeddings = self.model.encode([n.content for n in notes])
        # Store in vector database

    def search_semantic(self, query: str, top_k: int = 10):
        """Find notes semantically similar to query."""
        query_embedding = self.model.encode([query])
        # Search vector index
        return similar_notes
```

**MCP tool:**
```python
@mcp.tool()
def plorp_search_semantic(query: str, limit: int = 10) -> List[NoteInfo]:
    """
    Find notes by semantic similarity.

    Example:
        plorp_search_semantic("productivity tips", limit=5)
        # Returns notes about GTD, time management, focus techniques
        # Even if they don't contain exact phrase "productivity tips"

    Requires: Embeddings index (run `plorp index build` first)
    """
    return semantic_search.search(query, limit)
```

**Infrastructure needs:**
- Vector database (FAISS, ChromaDB, Qdrant)
- Embedding model (sentence-transformers)
- Index build/update process
- ~1-2GB disk space for embeddings

**Estimated effort:** 12-16 hours (Sprint 11)

---

### Feature 2: Automatic Note Organization / AI Classification 🔮

**Vision:** Automatically categorize, tag, and organize notes based on content.

**Example use cases:**
- "Auto-tag this note based on its content"
- "Suggest which project this note belongs to"
- "Classify all untagged notes in my vault"
- "Find orphaned notes that should be linked to projects"

**Technical approach:**

```python
class NoteClassifier:
    """LLM-based note classification."""

    def suggest_tags(self, note_content: str) -> List[str]:
        """Suggest tags for note based on content."""
        prompt = f"""
        Analyze this note and suggest 3-5 relevant tags:

        {note_content}

        Return only tags as comma-separated list.
        """
        response = llm.complete(prompt)
        return response.strip().split(',')

    def suggest_project(self, note_content: str, projects: List[str]) -> str:
        """Suggest which project note belongs to."""
        prompt = f"""
        Given these projects: {', '.join(projects)}

        Which project does this note belong to?

        {note_content}

        Return only the project name or "none".
        """
        return llm.complete(prompt).strip()

    def detect_note_type(self, note_content: str) -> str:
        """Classify note type (meeting, idea, task list, etc.)"""
        # Use few-shot classification
        pass
```

**MCP tools:**
```python
@mcp.tool()
def plorp_suggest_tags(filepath: str) -> List[str]:
    """
    Suggest tags for a note based on its content.

    Uses LLM to analyze note and recommend relevant tags.
    """
    note = read_note(filepath)
    tags = classifier.suggest_tags(note.content)
    return tags

@mcp.tool()
def plorp_auto_classify_note(filepath: str) -> dict:
    """
    Automatically classify note (type, project, tags).

    Returns:
        {
            "type": "meeting-notes",
            "suggested_project": "work.engineering.api-rewrite",
            "suggested_tags": ["api", "architecture", "planning"],
            "confidence": 0.87
        }
    """
    note = read_note(filepath)
    return classifier.classify_comprehensive(note)

@mcp.tool()
def plorp_organize_vault() -> dict:
    """
    Scan vault for unorganized notes and suggest organization.

    Returns list of suggestions like:
    - "notes/idea-2024-10.md should be tagged: #product, #feature"
    - "daily/2024-10-01.md has project content, extract to project note?"
    """
    return organizer.analyze_vault()
```

**User workflows:**

**Workflow 1: Auto-tag on save**
```
User writes note → MCP detects new note → Auto-suggests tags → User approves
```

**Workflow 2: Bulk organization**
```
User: "Organize all notes from last month"
Claude: [scans notes, classifies, suggests tags/projects]
Claude: "Found 23 untagged notes. Suggested tags for each. Apply all?"
```

**Infrastructure needs:**
- LLM API (Claude API, OpenAI, or local LLM)
- Classification prompt library
- Confidence scoring
- User approval workflow (don't auto-apply)

**Estimated effort:** 16-20 hours (Sprint 11-12)

---

### Feature 3: Real-Time File Watching / Sync 🔮

**Vision:** Automatically sync changes when files are edited outside plorp.

**Example use cases:**
- User checks off task in Obsidian → TaskWarrior auto-updates
- User modifies project frontmatter → plorp detects and syncs
- External script creates task → plorp picks it up immediately
- Obsidian plugin creates note → plorp indexes it instantly

**Technical approach:**

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class VaultWatcher(FileSystemEventHandler):
    """Watch vault for file changes and trigger sync."""

    def on_modified(self, event):
        if event.is_directory:
            return

        if event.src_path.endswith('.md'):
            self.handle_note_modified(event.src_path)

    def handle_note_modified(self, filepath: str):
        """Sync changes when note modified externally."""

        # Detect what changed
        if is_daily_note(filepath):
            # Check for checkbox state changes
            sync_daily_note_checkboxes(filepath)

        elif is_project_note(filepath):
            # Check for frontmatter task_uuids changes
            sync_project_frontmatter(filepath)

        # Trigger MCP notification (if connected)
        notify_mcp_clients({
            "event": "note_modified",
            "path": filepath,
            "timestamp": time.time()
        })

class PlorpDaemon:
    """Long-running plorp process for real-time sync."""

    def start(self):
        observer = Observer()
        observer.schedule(
            VaultWatcher(),
            path=config.vault_path,
            recursive=True
        )
        observer.start()

        # Also watch TaskWarrior database
        self.watch_taskwarrior()

        # Run MCP server in same process
        self.run_mcp_server()
```

**User workflows:**

**Workflow 1: Checkbox sync (finally!)**
```
User in Obsidian: Checks off "- [x] Buy groceries (uuid: abc-123)"
↓ (file watcher detects change)
plorp daemon: Detects checkbox checked
↓
plorp daemon: Runs `task abc-123 done`
↓
TaskWarrior: Task marked complete
```

**Workflow 2: External task sync**
```
Mobile app: Creates task in TaskWarrior
↓ (TaskWarrior database changes)
plorp daemon: Detects new task
↓
plorp daemon: Adds task to today's daily note
↓
Obsidian: Auto-refreshes, shows new task
```

**MCP tools:**
```python
@mcp.tool()
def plorp_start_sync_daemon() -> str:
    """
    Start plorp sync daemon for real-time sync.

    This keeps plorp running in background, watching for:
    - Obsidian note changes → sync to TaskWarrior
    - TaskWarrior changes → sync to Obsidian
    - New files → auto-index for search

    Run this once at system startup.
    """
    daemon.start()
    return "plorp sync daemon started (PID: {daemon.pid})"

@mcp.tool()
def plorp_sync_status() -> dict:
    """Check sync daemon status."""
    return {
        "running": daemon.is_running(),
        "last_sync": daemon.last_sync_time,
        "pending_changes": daemon.pending_changes_count
    }
```

**CLI commands:**
```bash
# Start daemon
plorp daemon start

# Check status
plorp daemon status

# Stop daemon
plorp daemon stop

# Sync once (no daemon)
plorp sync now
```

**Infrastructure needs:**
- File system watcher (watchdog library)
- Daemon/background process management
- Change detection logic (diff files)
- Conflict resolution (if both sides changed)
- PID file, logging, graceful shutdown

**Challenges:**
- **Infinite loops:** Change in Obsidian → triggers plorp → writes file → triggers watch again
  - Solution: Track changes plorp made, ignore those
- **Performance:** Large vaults (1000+ notes) create many watch events
  - Solution: Debounce, batch changes
- **Conflicts:** User edits same task in Obsidian AND mobile app
  - Solution: Last-write-wins + manual conflict resolution

**Estimated effort:** 20-24 hours (Sprint 12-13)

---

### Feature 4: Advanced Note Linking & Graph Analysis 🔮

**Vision:** Analyze note relationships and suggest connections.

**Example use cases:**
- "What notes should I link to this one?"
- "Find notes that discuss similar topics but aren't linked"
- "Build a concept map from my project notes"
- "Show me the knowledge graph around this topic"

**Technical approach:**

```python
class NoteLinkAnalyzer:
    """Analyze and suggest note relationships."""

    def suggest_links(self, note_path: str) -> List[dict]:
        """Suggest notes to link to based on content similarity."""
        note = read_note(note_path)

        # Semantic similarity
        similar = semantic_search.find_similar(note.content, limit=10)

        # Shared tags
        tag_matches = search_by_tags(note.metadata.get('tags', []))

        # Shared entities (people, projects, concepts)
        entities = extract_entities(note.content)
        entity_matches = search_by_entities(entities)

        # Combine and rank
        return rank_link_suggestions(similar, tag_matches, entity_matches)

    def build_concept_graph(self, seed_note: str, depth: int = 2):
        """Build graph of related notes."""
        graph = NetworkX.Graph()
        # BFS from seed note, add edges based on links/similarity
        return graph
```

**Estimated effort:** 12-16 hours (Sprint 13)

---

## Sprint 10+ Roadmap Summary

### Sprint 10: REST API Enhancement ✅
- Optional REST API mode
- Advanced search (DQL, JsonLogic)
- Intelligent section patching
- Active note operations
- **Effort:** 20 hours

### Sprint 11: Semantic Search 🔮
- Embedding generation
- Vector database integration
- Semantic search MCP tools
- **Effort:** 16 hours

### Sprint 12: AI Classification 🔮
- Note auto-tagging
- Project suggestion
- Bulk organization tools
- **Effort:** 20 hours

### Sprint 13: Real-Time Sync 🔮
- File watching daemon
- Bidirectional sync (Obsidian ↔ TaskWarrior)
- Conflict resolution
- **Effort:** 24 hours

### Sprint 14: Graph Analysis 🔮
- Link suggestions
- Concept mapping
- Knowledge graph visualization
- **Effort:** 16 hours

**Total Sprint 10-14:** ~96 hours (12 days of work)

---

## Open Questions for Sprint 10
**Question:** Should we bundle REST API plugin with plorp, or require separate install?

**Options:**
- A: Require separate install (recommended - licensing, updates)
- B: Bundle plugin binary (complex - Obsidian plugin store)
- C: Auto-install via script (requires Obsidian CLI access)

**Recommendation:** Option A. Document installation, link to plugin.

---

### Q2: API Key Management
**Question:** How should users manage REST API keys securely?

**Options:**
- A: Store in config.yaml (simple, less secure)
- B: Environment variable (secure, automation-friendly)
- C: System keychain (most secure, platform-specific)

**Recommendation:** Support A and B. Document security implications.

---

### Q3: Version Compatibility
**Question:** What happens when REST API plugin updates break compatibility?

**Options:**
- A: Pin to specific plugin version (inflexible)
- B: Version detection + adaptation (complex)
- C: Best-effort + clear errors (pragmatic)

**Recommendation:** Option C. Test against current version, fail gracefully on incompatibility.

---

## References

- **Obsidian Local REST API Plugin:** https://github.com/coddingtonbear/obsidian-local-rest-api
- **mcp-obsidian Implementation:** https://github.com/MarkusPfundstein/mcp-obsidian
- **OpenAPI Spec:** `/tmp/mcp-obsidian/openapi.yaml`
- **Sprint 9 Spec:** `Docs/sprints/SPRINT_9_SPEC.md`

---

## Version History

- **v1.0.0** (2025-10-08) - Initial analysis
  - Researched mcp-obsidian implementation
  - Documented REST API unique capabilities
  - Compared filesystem vs REST API approaches
  - Recommended hybrid strategy for Sprint 10+
