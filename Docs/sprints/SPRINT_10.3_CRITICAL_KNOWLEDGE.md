# Sprint 10.3 Critical Knowledge - Vault Sync via CouchDB

**Purpose:** Compressed essential knowledge for implementing Sprint 10.3
**Created:** 2025-10-12
**For:** Lead Engineer implementing vault sync
**Context:** This document replaces 90k tokens of reference material with critical facts

---

## 1. ARCHITECTURAL LAWS (Non-Negotiable)

### State Synchronization Pattern - THE LAW

**Core Principle:** Every TaskWarrior modification MUST update all related Obsidian surfaces.

**The Pattern:**
```
✅ CORRECT:
1. Update TaskWarrior (mark task done, create task, modify task)
2. Update ALL related Obsidian surfaces (remove UUID from projects, update daily note checkboxes)

❌ WRONG:
1. Update TaskWarrior only
2. Obsidian surfaces show stale data
3. USER SEES INCONSISTENT STATE
```

**Required Sync Operations:**
- `/review` marks task done → `mark_done(uuid)` + `remove_task_from_projects(uuid)` + `update_daily_note_checkbox(uuid)`
- `/review` deletes task → `delete_task(uuid)` + `remove_task_from_all_projects(uuid)`
- `create_task_in_project()` → `create_task()` + `add_uuid_to_project_frontmatter()`
- Change task project → Remove from old project + Add to new project

**Anti-Patterns YOU MUST AVOID:**
1. **Orphaned UUIDs** - Task deleted in TaskWarrior, UUID remains in project frontmatter
2. **Stale Checkbox State** - User checks box, TaskWarrior not updated
3. **Missing Task References** - Task created in project, project doesn't track it

**Testing Requirements:**
- Test BOTH sides of every state change
- `assert get_task_status(uuid) == "completed"` (TaskWarrior)
- `assert uuid not in get_project_task_uuids()` (Obsidian)

**IF YOU VIOLATE THIS PATTERN, YOU HAVE FAILED.**

### Q21: State Sync with CouchDB (BLOCKING DECISION)

**Critical Context-Dependent Behavior:**

**Context 1: Local brainplorp CLI (user at Mac)**
```python
# User runs: brainplorp start
1. Query TaskWarrior for tasks
2. Write to LOCAL vault files (existing behavior)
3. LiveSync detects change, syncs to CouchDB automatically (2-5s)
4. Other devices see changes via LiveSync

State Sync: TaskWarrior → Local files → LiveSync propagates
✅ Maintains existing State Sync pattern
```

**Context 2: Server automation (brainplorp server on Fly.io)**
```python
# Server runs: email fetch automation
1. Fetch emails from Gmail
2. Write to CouchDB via HTTP API (NO local files)
3. All devices sync from CouchDB via LiveSync

State Sync: Email fetch → CouchDB write → LiveSync to clients
✅ Server has no local vault, must use CouchDB
```

**Context 3: Multi-device TaskWarrior sync**
```python
# User marks task done on Mac 1:
1. brainplorp marks task done in TaskWarrior
2. brainplorp updates local daily note (State Sync)
3. brainplorp updates local project frontmatter (State Sync)
4. LiveSync syncs files to CouchDB
5. Other devices receive updates via LiveSync

✅ State Sync preserved on local device
✅ LiveSync propagates to other devices
```

**Implementation Rules:**
- If `vault_path` is local → Write to local files, LiveSync syncs
- If running on server (no vault_path) → Write to CouchDB via HTTP
- State Sync enforcement happens at point of write (local or CouchDB)
- LiveSync is transparent propagation layer

**Code Implications:**
- `core/daily.py`, `core/tasks.py` → Continue writing to local files when local
- `integrations/vault_client.py` (NEW) → Server-only, writes to CouchDB via HTTP
- `core/process.py` → Update local files (State Sync), LiveSync handles propagation

---

## 2. LEAD ENGINEER ROLE & RULES

### Foundational Rules

**Rule #1: If you want exception to ANY rule, STOP and get explicit permission from John first.**

**Core Values:**
- Doing it right is better than doing it fast
- Honesty is a core value - if you lie, you'll be replaced
- Tedious, systematic work is often correct - don't abandon because it's repetitive

**Communication:**
- Address John (never "you", always "John")
- Speak up immediately when you don't know something
- Call out bad ideas, unreasonable expectations, mistakes
- NEVER write "You're absolutely right!" - not a sycophant
- If uncomfortable pushing back: say "Strange things are afoot at the Circle K"

### Test-Driven Development (TDD) - MANDATORY

**FOR EVERY NEW FEATURE OR BUGFIX:**
1. Write a failing test that validates desired functionality
2. Run the test to confirm it fails as expected
3. Write ONLY enough code to make the test pass
4. Run the test to confirm success
5. Refactor if needed while keeping tests green

**Testing State Sync:**
```python
def test_review_marks_done_syncs_project():
    # Create task in project
    uuid = create_task_in_project(vault_path, "work", "Fix bug")

    # Mark done via review
    mark_task_done_via_review(uuid, vault_path)

    # Verify BOTH sides updated
    assert get_task_status(uuid) == "completed"  # TaskWarrior ✅
    assert uuid not in get_project_task_uuids(vault_path, "work")  # Obsidian ✅
```

### Code Quality Rules

- Make SMALLEST reasonable changes
- Strongly prefer simple, clean, maintainable solutions
- Work hard to reduce code duplication
- NEVER throw away or rewrite implementations without EXPLICIT permission
- MATCH style of surrounding code exactly
- Fix broken things immediately when found

### Version Control

- Track all non-trivial changes in git
- Commit frequently throughout development
- NEVER SKIP, EVADE OR DISABLE A PRE-COMMIT HOOK
- Never use `git add -A` unless you've just done `git status`

### Systematic Debugging Framework

**Phase 1: Root Cause Investigation (BEFORE fixes)**
1. Read error messages carefully
2. Reproduce consistently
3. Check recent changes (git diff)

**Phase 2: Pattern Analysis**
1. Find working examples in codebase
2. Compare against references
3. Identify differences
4. Understand dependencies

**Phase 3: Hypothesis and Testing**
1. Form single hypothesis (state it clearly)
2. Test minimally
3. Verify before continuing
4. When you don't know: say "I don't understand X"

**Phase 4: Implementation Rules**
- ALWAYS have simplest possible failing test case
- NEVER add multiple fixes at once
- ALWAYS test after each change
- IF first fix doesn't work, STOP and re-analyze

### Testing Philosophy

- ALL TEST FAILURES ARE YOUR RESPONSIBILITY
- Never delete a test because it's failing
- Tests MUST comprehensively cover ALL functionality
- NEVER test mocked behavior - test real logic
- Test output MUST BE PRISTINE TO PASS

---

## 3. SPRINT 10.3 CRITICAL DECISIONS

### Architecture

**Deployment:** Separate Fly.io app `couch-brainplorp-sync.fly.dev` (not same as TaskChampion server)

**CouchDB Version:** 3.3.3 (latest stable)

**Docker Image:** `couchdb:3.3.3` (official)

**Persistent Volume:** 10GB ($1.50/month, supports vaults up to 2GB)

**CORS:** Enable for all origins (`origins = *`) - authentication is security layer

### Security Model

**Credentials:** Each user gets unique CouchDB username/password

**Password Storage:**
- Local: OS keychain via `keyring` library
- Server: Fly.io secrets (encrypted env vars)

**Database Isolation:** One database per user (`user-{username}-vault`)

**Server Access:** Server uses SAME credentials as user (not separate admin)

### LiveSync Plugin Integration

**Plugin ID:** `obsidian-livesync` (folder name in `.obsidian/plugins/`)

**User-Facing Name:** "Self-hosted LiveSync"

**Installation:** Manual (guide user, check for installation, write config if installed)

**Auto-Install:** NO - Obsidian API not documented, would be brittle

**Existing Config:** If LiveSync already configured, ABORT and warn user (don't overwrite)

### MVCC Conflict Resolution

**Retry Strategy:** Exponential backoff
- Attempt 1: 0ms (initial)
- Attempt 2: 100ms delay
- Attempt 3: 200ms delay
- Attempt 4: 400ms delay
- Attempt 5: 800ms delay
- Max retries: 4 (5 total attempts)

**If All Retries Fail:**
- Raise `VaultUpdateConflictError`
- Log conflict details
- User message: "Vault sync conflict - please try again"

**Connection Pooling:** 10 connections with keep-alive (requests library default)

### Username Sanitization

**Required:** CouchDB requires lowercase, alphanumeric + hyphen/underscore

```python
def sanitize_username(username: str) -> str:
    username = username.lower()
    username = username.replace(' ', '-')
    username = re.sub(r'[^a-z0-9\-_]', '', username)
    if not username[0].isalpha():
        username = 'user-' + username
    return username

# "John Smith" → "john-smith"
# "jsd123" → "jsd123"
# "123user" → "user-123user"
```

**Database Name Format:** `user-{sanitized_username}-vault`

### Backward Compatibility

**Vault Sync is OPTIONAL** - brainplorp works without it

```yaml
# config.yaml when sync disabled
vault_path: /Users/jsd/vault
taskwarrior_data: ~/.task
# No vault_sync section = disabled
```

**Commands work normally:**
- `brainplorp start` - writes to local vault
- `brainplorp review` - reads local vault
- `brainplorp tasks` - queries TaskWarrior

**Only sync-specific commands require it:**
- `brainplorp vault status` - errors if not configured

### Email-to-Inbox Integration

**Sprint 10.3 Scope:** Create `vault_client.py` library ONLY

**NOT in scope:** Refactoring existing `inbox.py` to use CouchDB

**Future Sprint (10.4 or 11):**
- Refactor `core/inbox.py` to use vault_client when server context
- Keep local file operations when CLI context
- Update `brainplorp inbox fetch` to detect context

### Version Management

**Target Version:** v1.7.0 (MINOR bump from 1.6.2)

**Lead Engineer Responsibility:** Bump version in Phase 5 after tests pass

**Files to Update:**
- `src/brainplorp/__init__.py`: `__version__ = "1.7.0"`
- `pyproject.toml`: `version = "1.7.0"`
- `tests/test_cli.py`: version assertion
- `tests/test_smoke.py`: version assertion

**Commit Message:** "Sprint 10.3 complete - bump to v1.7.0"

---

## 4. TESTING REQUIREMENTS

### Test Count Expectations

**Current:** 532 tests passing (5 failures are TaskWarrior env issues, not code bugs)

**Expected New Tests:** 20-25

**Target for Sign-Off:** 552+ tests (all passing)

**Breakdown:**
- vault_client.py: 8 tests (read, write, update, MVCC retry, error handling)
- livesync_config.py: 4 tests (credentials, config, sanitize, validation)
- vault status command: 3 tests (syncing, no config, with conflicts)
- setup.py vault sync: 5 tests (first computer, existing config, credentials, skip, plugin not installed)

### Mock Library

**Use `responses` library** for HTTP mocking (not `unittest.mock`)

```python
import responses

@responses.activate
def test_read_document():
    responses.add(
        responses.GET,
        'https://couch.test.dev/vault/daily%2F2025-10-12.md',
        json={'_id': 'daily/2025-10-12.md', '_rev': '1-abc', 'content': '# Daily'},
        status=200
    )

    client = VaultClient('https://couch.test.dev', 'vault', 'user', 'pass')
    doc = client.read_document('daily/2025-10-12.md')
    assert doc['content'] == '# Daily'
```

**Why `responses`:**
- Intercepts at requests library level (realistic)
- Self-documenting (shows exact HTTP request/response)
- Easier to assert on URL, headers, body

### Integration Tests

**Unit tests (required):** Mock with `responses` library

**Integration tests (optional):** Real CouchDB in Docker (manual testing before release)

```bash
# Manual integration test
docker run -d -p 5984:5984 couchdb:3.3.3
pytest tests/integration/test_vault_client_real.py
docker stop <container-id>
```

### Mobile Testing

**You test:** Mac 1 → Mac 2 sync (two terminal windows, two Obsidian instances)

**John tests:** iPhone sync (he has iPhone, validates mobile)

**PM validates:** iPhone testing complete before final sign-off

---

## 5. BRAINPLORP CORE PRINCIPLES

### TaskWarrior Integration Strategy

**For Writes (ALWAYS):** Use `subprocess` to call `task` CLI

```python
subprocess.run(['task', 'add', description, f'due:{due}', f'priority:{priority}'])
subprocess.run(['task', uuid, 'done'])
subprocess.run(['task', uuid, 'modify', f'project:{project}'])
```

**NEVER write directly to SQLite** - bypasses TaskChampion operation log, corrupts database

**For Reads:** Use `task export` via subprocess (returns JSON)

```python
result = subprocess.run(['task', 'status:pending', 'export'], capture_output=True, text=True)
tasks = json.loads(result.stdout)
```

**UUIDs are stable** across sync - always use UUIDs for references, not numeric IDs

**Filter Syntax:**
- `status:pending`
- `due:today`, `due.before:today`
- `project:home`, `+tag`

### Obsidian Integration

**Vault Structure:**
```
vault/
├── daily/          # Daily notes (YYYY-MM-DD.md)
├── inbox/          # Monthly inbox (YYYY-MM.md)
├── notes/          # General notes
└── projects/       # Project notes
```

**Daily Note Format:**
```markdown
---
date: 2025-10-12
type: daily
plorp_version: 1.7.0
---

# Daily Note - 2025-10-12

## Tasks
- [ ] Description (project: X, due: Y, uuid: abc-123)
- [x] Completed task (project: Z, uuid: def-456)
```

**Inbox Format:**
```markdown
## Unprocessed
- [ ] Item 1
- [ ] Item 2

## Processed
- [x] Item 3 (→ task abc-123)
- [x] Item 4 (→ note notes/file.md)
```

### Design Principles

**Simplicity First:**
- No custom database
- No custom codes (m1, p1, etc.)
- Python scripts call `task` CLI
- brainplorp is stateless

**Markdown-Centric:**
- Daily notes, inbox, review - all markdown
- brainplorp parses markdown ↔ TaskWarrior

**UUID-Based Linking:**
- Tasks → Notes: TaskWarrior annotations
- Notes → Tasks: YAML front matter `tasks:` field
- Bidirectional maintained by brainplorp

---

## 6. PHASE-SPECIFIC GUIDANCE

### Phase 1: CouchDB Deployment (2 hours)

**Files to Create:**
- `deploy/couchdb.Dockerfile`
- `deploy/couchdb-fly.toml`
- `deploy/couchdb-config.ini`

**Dockerfile:**
```dockerfile
FROM couchdb:3.3.3
COPY couchdb-config.ini /opt/couchdb/etc/local.d/
```

**Fly.io Config:**
```toml
app = "couch-brainplorp-sync"

[mounts]
  source = "couchdb_data"
  destination = "/opt/couchdb/data"
```

**Create Volume:**
```bash
fly volumes create couchdb_data --size 10 --region sjc
```

**Test:** `curl https://couch-brainplorp-sync.fly.dev/` returns CouchDB welcome JSON

### Phase 2: Setup Wizard (2 hours)

**Files to Create/Modify:**
- `src/brainplorp/commands/setup.py` - Add vault sync step
- `src/brainplorp/integrations/couchdb.py` - HTTP client
- `src/brainplorp/utils/livesync_config.py` - Config generation

**Key Functions:**
```python
def create_couchdb_database(username)  # Create user's vault DB
def generate_couchdb_credentials()     # Create username/password
def configure_livesync_plugin(vault_path, credentials)  # Write plugin config
def verify_livesync_sync(vault_path)   # Check sync status
```

**Setup Flow:**
1. Check if LiveSync plugin installed (abort if not)
2. Check if LiveSync already configured (abort if yes)
3. Generate credentials
4. Create CouchDB database via HTTP
5. Write LiveSync config JSON
6. Store credentials in OS keychain
7. Update config.yaml with vault_sync section
8. Display credentials for other computers

### Phase 3: Server HTTP API Client (2 hours)

**Files to Create:**
- `src/brainplorp/integrations/vault_client.py`
- `tests/test_vault_client.py`

**Library Interface:**
```python
class VaultClient:
    def __init__(self, server_url, database, username, password)
    def read_document(self, path: str) -> dict
    def write_document(self, path: str, content: str) -> dict
    def update_document(self, path: str, update_fn: Callable) -> dict
    def list_documents(self, prefix: str) -> list[str]
    def batch_read(self, paths: list[str]) -> dict[str, dict]
```

**MVCC Update Pattern:**
```python
def update_document(self, path, update_fn, max_retries=4):
    for attempt in range(max_retries):
        doc = self.read_document(path)
        updated = update_fn(doc['content'])
        try:
            self._put_document(path, updated, doc['_rev'])
            return
        except ConflictError:
            if attempt == max_retries - 1:
                raise
            delay = 0.1 * (2 ** attempt)
            time.sleep(delay)
```

**Connection Setup:**
```python
self.session = requests.Session()
adapter = HTTPAdapter(pool_connections=10, pool_maxsize=10)
self.session.mount('https://', adapter)
self.session.auth = (username, password)
```

### Phase 4: CouchDB Views (1 hour) - OPTIONAL

**Can defer to Sprint 11 if time constrained**

**Files to Create:**
- `deploy/couchdb-design-docs.json`
- `src/brainplorp/analytics/views.py`

**Views:**
- Daily notes by date (for weekly summaries)
- Tasks by status (completed vs pending)
- Inbox items by month

### Phase 5: Testing & Documentation (2 hours)

**Testing:**
- Mac 1 → Mac 2 sync (you test)
- iPhone sync (John tests, reports to you)
- Server HTTP API (read + write + MVCC)
- Offline/online scenarios
- Conflict resolution

**Documentation:**
- `Docs/VAULT_SYNC_USER_GUIDE.md` - User setup walkthrough
- `Docs/VAULT_SYNC_DEVELOPER_GUIDE.md` - Server API examples
- `Docs/VAULT_SYNC_ARCHITECTURE.md` - Why CouchDB, trade-offs

**Version Bump:** Update 4 files after tests pass (see Section 3)

**Conflict Detection:**
```python
def check_vault_status():
    conflicts = list(vault_path.rglob("*.conflicted.md"))
    if conflicts:
        click.echo("⚠️  Conflicts detected:")
        for f in conflicts:
            click.echo(f"   • {f.relative_to(vault_path)}")
```

---

## 7. SUCCESS CRITERIA FOR SIGN-OFF

**Must Have (Required):**
- [ ] CouchDB server deployed on Fly.io with HTTPS
- [ ] `brainplorp setup` configures CouchDB + LiveSync
- [ ] User can enable LiveSync in Obsidian, vault syncs
- [ ] Mac 1 → CouchDB → Mac 2 sync verified
- [ ] iPhone sync verified (John tests)
- [ ] brainplorp server can read document via HTTP API
- [ ] brainplorp server can write document with MVCC
- [ ] `brainplorp vault status` command works
- [ ] 552+ tests passing (20-25 new tests)
- [ ] Version bumped to v1.7.0
- [ ] Documentation complete

**Should Have (Nice to Have):**
- [ ] MVCC conflict retry tested (concurrent writes)
- [ ] CouchDB views for analytics
- [ ] Offline edit syncs when reconnected
- [ ] Sync performance: <10s for 100 files

**Phase 4 Views:** Optional - implement if time in 9-hour budget, defer to Sprint 11 if needed

---

## 8. PROJECT CONTEXT

**Current Version:** v1.6.2 (in code, not released - waiting for v1.7.0)

**Latest Release:** v1.6.1

**Test Status:** 532 tests passing, 5 failures (TaskWarrior env issues, not code bugs)

**Git Branch:** master

**Recent Sprints:**
- Sprint 10: Mac Installation & Multi-Computer Sync (COMPLETE, v1.6.0)
- Sprint 10.1: Wheel Distribution (COMPLETE, v1.6.1)
- Sprint 10.1.1: Installation Hardening (CODE COMPLETE, committed, waiting for v1.7.0)

**Dependencies:**
- Sprint 10 is COMPLETE ✅
- Fly.io account active with `brainplorp-sync.fly.dev` (TaskChampion server)
- CouchDB will be separate app: `couch-brainplorp-sync.fly.dev`

**Homebrew Installation:**
- Repository: https://github.com/dimatosj/homebrew-brainplorp
- Formula working for v1.6.1
- Need to update formula for v1.7.0 after Sprint 10.3 complete

---

## 9. COMMON PITFALLS TO AVOID

### Pitfall 1: Forgetting State Sync

```python
# ❌ WRONG - Only updates TaskWarrior
def mark_done_in_review(uuid):
    mark_done(uuid)
    # Missing: remove_task_from_projects()

# ✅ CORRECT - Updates both systems
def mark_done_in_review(uuid, vault_path):
    mark_done(uuid)
    remove_task_from_projects(vault_path, uuid)
```

### Pitfall 2: Direct SQLite Write

```python
# ❌ WRONG - Bypasses TaskChampion, corrupts database
import sqlite3
conn = sqlite3.connect('~/.task/taskchampion.sqlite3')
conn.execute("UPDATE tasks SET status='completed'")

# ✅ CORRECT - Use CLI
subprocess.run(['task', uuid, 'done'])
```

### Pitfall 3: Incomplete Testing

```python
# ❌ WRONG - Only tests TaskWarrior side
def test_mark_done():
    mark_done(uuid)
    assert get_task_status(uuid) == "completed"
    # Missing: verify Obsidian updated

# ✅ CORRECT - Tests both sides
def test_mark_done():
    mark_done(uuid, vault_path)
    assert get_task_status(uuid) == "completed"  # TaskWarrior
    assert uuid not in get_project_uuids()       # Obsidian
```

### Pitfall 4: Overwriting User's LiveSync Config

```python
# ❌ WRONG - Overwrites existing sync
config_file = plugin_dir / "data.json"
write_livesync_config(config_file, credentials)

# ✅ CORRECT - Check and abort if exists
if config_file.exists():
    existing = json.loads(config_file.read_text())
    if existing.get('couchDB_URI'):
        click.echo("⚠️  LiveSync already configured")
        sys.exit(1)
write_livesync_config(config_file, credentials)
```

### Pitfall 5: Context Confusion (Q21)

```python
# ❌ WRONG - Server tries to write to local files
def email_to_inbox_on_server():
    inbox_path = Path("/Users/jsd/vault/inbox/2025-10.md")  # Doesn't exist on server!
    inbox_path.write_text(content)

# ✅ CORRECT - Server writes to CouchDB
def email_to_inbox_on_server():
    vault_client = VaultClient(...)
    vault_client.update_document("inbox/2025-10.md", lambda c: c + "\n" + email_content)
```

---

## 10. QUICK REFERENCE

**When in doubt:**
- State Sync? → Update BOTH TaskWarrior AND Obsidian
- TaskWarrior write? → Use subprocess CLI, never SQLite
- Testing? → Test both sides of state changes
- Breaking rules? → STOP and ask John for permission
- Don't understand? → Say "I don't understand X", don't pretend

**Key Files to Create:**
- `deploy/couchdb.Dockerfile`
- `deploy/couchdb-fly.toml`
- `deploy/couchdb-config.ini`
- `src/brainplorp/integrations/vault_client.py`
- `src/brainplorp/utils/livesync_config.py`
- `tests/test_vault_client.py`
- `Docs/VAULT_SYNC_USER_GUIDE.md`

**Key Dependencies:**
- `responses` (for HTTP mocking in tests)
- `keyring` (for secure password storage)
- requests library (already used)

**Estimated Effort:** 9 hours (2+2+2+1+2)

**Target:** v1.7.0 with 552+ tests passing

---

**END OF CRITICAL KNOWLEDGE DOCUMENT**

This document should be sufficient to implement Sprint 10.3 with just the spec as additional reference.
