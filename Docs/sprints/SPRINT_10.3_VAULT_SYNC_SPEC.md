# Sprint 10.3: Vault Sync via CouchDB + Obsidian LiveSync

**Created:** 2025-10-12
**Status:** 📋 READY FOR IMPLEMENTATION
**Sprint Type:** Major Feature (MINOR version increment)
**Target Version:** v1.7.0
**Estimated Effort:** 9 hours
**Dependencies:** Sprint 10.2 (Cloud Sync) must be complete

---

## Executive Summary

Implement automatic, real-time vault synchronization across multiple devices (Mac, iPhone, iPad, Android) using CouchDB as the sync server and Obsidian's LiveSync plugin as the client.

**Key Philosophy:** Users get automatic, real-time sync without managing anything. Edit on Mac, see changes on iPhone instantly.

**Architecture:** Pure CouchDB - single source of truth for vault data, accessed by both users (via LiveSync plugin) and brainplorp server (via HTTP API).

**Why CouchDB?**
- ✅ Real-time automatic sync (2-5 seconds)
- ✅ Mobile support (iOS/Android via LiveSync)
- ✅ No manual sync commands needed
- ✅ Server HTTP API for automation
- ✅ Built-in conflict resolution (MVCC)
- ✅ Battle-tested replication protocol
- ✅ Self-hostable on Fly.io (free tier)

---

## User Experience

### Computer 1 Setup (First Time)

```
$ brainplorp setup

Step 1: Vault Path
  Where is your Obsidian vault? /Users/jsd/vault
  ✓ Vault found

Step 2: TaskWarrior Sync
  Do you have sync credentials from another computer? [y/N]: n

  Configuring brainplorp Cloud Sync...
  ✓ Sync configured and tested!
  ✓ Uploaded 0 tasks to server.

  📋 IMPORTANT: Save these credentials for your other computers:
     Client ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
     Secret: abc123def456...

Step 3: Vault Sync
  Setting up automatic vault sync...

  ✓ CouchDB credentials generated
  ✓ Obsidian LiveSync plugin configured

  📋 To complete setup:
     1. Open Obsidian
     2. Go to Settings → Community Plugins
     3. Enable "Self-hosted LiveSync" (already installed)
     4. Plugin will start syncing automatically

  🎉 Setup complete! Your vault will sync across all devices.

$ brainplorp start
🔄 Vault synced 2 seconds ago
📅 Generating today's daily note...
✓ Created vault/daily/2025-10-12.md
```

### iPhone/iPad (Later That Day)

```
User opens Obsidian on iPhone
→ LiveSync syncs automatically in background
→ Today's daily note appears
→ User adds task: "Buy milk"
→ Syncs to CouchDB automatically (3 seconds)
```

### Computer 1 (Continues Working)

```
User switches back to Mac
→ Opens Obsidian
→ Sees "Buy milk" task appear automatically
→ No sync command needed, LiveSync handled it
```

### Computer 2 Setup (New Mac)

```
$ brainplorp setup

Step 1: Vault Path
  Where is your Obsidian vault? /Users/jsd/vault
  ✓ Vault found

Step 2: TaskWarrior Sync
  Do you have sync credentials from another computer? [y/N]: y

  Enter credentials from Computer 1:
  Client ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
  Secret: abc123def456...

  ✓ Sync successful! Downloaded 15 tasks from server.

Step 3: Vault Sync
  Do you have CouchDB credentials from another computer? [y/N]: y

  Enter CouchDB credentials:
  Server: https://couch-brainplorp-sync.fly.dev
  Database: user-jsd-vault
  Username: user-jsd
  Password: [paste password from Computer 1]

  ✓ Vault sync configured

  📋 To complete setup:
     1. Open Obsidian
     2. Go to Settings → Community Plugins → Self-hosted LiveSync
     3. Click "Start sync"
     4. All your notes will download automatically

  🎉 Setup complete! Vault is syncing.

$ brainplorp start
🔄 Vault synced 1 second ago
📅 Today's daily note already exists
✓ vault/daily/2025-10-12.md
```

### Daily Workflow (Any Device)

**User never thinks about syncing - it just works:**
- Edit note in Obsidian → Syncs in 2-5 seconds automatically
- Create task via `brainplorp start` → Syncs to all devices
- Add inbox item on phone → Appears on Mac automatically
- Run `brainplorp review` → Updates sync to all devices

**If user wants to check sync status:**
```
$ brainplorp vault status

Vault Sync Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Status: ✓ Syncing
  Last sync: 2 seconds ago
  Server: https://couch-brainplorp-sync.fly.dev
  Documents: 127 synced
  Pending: 0
```

---

## Problem Statement

### Current Pain Points

**No Multi-Device Support:**
- brainplorp only works on one Mac
- Can't capture tasks on iPhone
- Can't access vault from multiple computers
- Manual file syncing via iCloud/Dropbox is error-prone

**Manual Sync is Fragile:**
- User must remember to sync before switching devices
- iCloud/Dropbox conflicts corrupt files
- No conflict resolution built-in
- Lost work when conflicts happen

**No Mobile Capture:**
- User has great idea on iPhone
- Can't add to inbox until back at Mac
- Ideas forgotten, tasks missed

### Success Criteria

1. **Automatic Sync:** User never runs sync commands, happens in background
2. **Real-Time:** Changes sync within 5 seconds across all devices
3. **Mobile Support:** Works on iPhone, iPad, Android (via Obsidian mobile)
4. **Conflict Resolution:** Automatic handling of simultaneous edits
5. **Transparent Setup:** `brainplorp setup` configures everything, user just enables plugin
6. **Server Integration:** brainplorp server can read/write vault via HTTP API
7. **Offline Support:** User can work offline, changes sync when reconnected
8. **Status Visibility:** User can check sync health with `brainplorp vault status`

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────┐
│          CouchDB Server (Fly.io)                     │
│                                                      │
│  Database: user-jsd-vault                            │
│  ├─ daily/2025-10-12.md (doc)                       │
│  ├─ inbox/2025-10.md (doc)                          │
│  ├─ notes/project-alpha.md (doc)                    │
│  └─ ... (all vault files as documents)              │
│                                                      │
│  Features:                                           │
│  • HTTP/WebSocket API                                │
│  • Multi-version concurrency control (MVCC)         │
│  • Automatic conflict detection                     │
│  • Incremental replication protocol                 │
└─────────────────────────────────────────────────────┘
              ▲                ▲                ▲
              │                │                │
         WebSocket        WebSocket          HTTP API
              │                │                │
    ┌─────────┴────┐   ┌──────┴────┐   ┌──────┴──────┐
    │   Mac 1      │   │  iPhone   │   │   Server    │
    │              │   │           │   │             │
    │  Obsidian    │   │ Obsidian  │   │ brainplorp  │
    │  + LiveSync  │   │ + LiveSync│   │  automation │
    │              │   │           │   │             │
    │  Reads/writes│   │Reads/writes   │ HTTP client │
    │  via plugin  │   │via plugin │   │ for email,  │
    │              │   │           │   │ tasks, etc  │
    └──────────────┘   └───────────┘   └─────────────┘
```

**Single Source of Truth:** CouchDB database contains all vault files as documents.

**Three Clients:**
1. **Obsidian + LiveSync** (Mac, iPhone, iPad, Android) - Real-time sync for users
2. **brainplorp server** (Fly.io) - HTTP API for automation (email fetch, scheduled tasks)
3. **Other Obsidian clients** (future) - Any device running Obsidian mobile

### Document Structure in CouchDB

Each vault file becomes a CouchDB document:

```json
{
  "_id": "daily/2025-10-12.md",
  "_rev": "3-abc123def",
  "type": "markdown",
  "path": "daily/2025-10-12.md",
  "content": "# Daily Note - 2025-10-12\n\n## Tasks\n- [ ] Review inbox",
  "mtime": "2025-10-12T14:30:00Z",
  "ctime": "2025-10-12T08:00:00Z",
  "size": 256,
  "deleted": false
}
```

**Key fields:**
- `_id`: File path (unique identifier)
- `_rev`: CouchDB revision (for MVCC conflict detection)
- `content`: Actual markdown content
- `mtime`: Last modified timestamp
- `deleted`: Tombstone for deleted files

**LiveSync manages this structure automatically** - users and brainplorp server just see files.

### Conflict Resolution via MVCC

**Multi-Version Concurrency Control (MVCC)** means each document update requires the current revision number.

**Scenario: User edits on Mac while server adds email to inbox**

```
Step 1: Initial State
  inbox/2025-10.md (_rev: "1-xyz")
  Content: "- [ ] Old task"

Step 2: Simultaneous Edits
  Mac LiveSync:
    Reads: _rev "1-xyz"
    Adds: "- [ ] Buy groceries"
    Attempts update with _rev "1-xyz"
    → Success! New _rev: "2-abc"

  Server HTTP API:
    Reads: _rev "1-xyz" (stale)
    Adds: "- [ ] Email: Client meeting"
    Attempts update with _rev "1-xyz"
    → Rejected! CouchDB says: "Conflict - rev mismatch"

Step 3: Server Retries
  Server reads latest: _rev "2-abc"
  Sees Mac's changes: "- [ ] Buy groceries"
  Merges: "- [ ] Buy groceries\n- [ ] Email: Client meeting"
  Updates with _rev "2-abc"
  → Success! New _rev: "3-def"

Step 4: Mac Syncs
  LiveSync polls CouchDB
  Sees _rev "3-def" (newer than local "2-abc")
  Downloads merged content
  User sees both items in Obsidian
```

**Result:** No data loss, automatic conflict resolution.

**If true conflict (same line edited):**
- CouchDB keeps both versions
- LiveSync creates conflict file: `inbox/2025-10.conflicted.md`
- User reviews and merges manually

### Server HTTP API Access

brainplorp server can read/write vault directly via CouchDB HTTP API:

**Example 1: Fetch emails to inbox (Sprint 10.2 feature)**

```
1. Server fetches emails from Gmail
2. Server reads current inbox document via HTTP GET:
   GET https://couch.brainplorp.com/user-jsd-vault/inbox%2F2025-10.md

3. Server appends emails to content:
   - [ ] Email: Project deadline moved
   - [ ] Email: Team standup at 2pm

4. Server updates document via HTTP PUT:
   PUT https://couch.brainplorp.com/user-jsd-vault/inbox%2F2025-10.md
   Body: {content: "...", _rev: "5-abc"}

5. Mac LiveSync polls, sees new _rev, downloads changes
6. User opens Obsidian, sees new emails in inbox automatically
```

**Example 2: Read today's tasks for analytics**

```
1. Server queries CouchDB:
   GET https://couch.brainplorp.com/user-jsd-vault/daily%2F2025-10-12.md

2. Server parses markdown content
3. Server analyzes tasks (completed, pending, overdue)
4. Server generates metrics (no write needed)
```

**Example 3: Batch read for weekly summary**

```
1. Server queries multiple documents:
   POST https://couch.brainplorp.com/user-jsd-vault/_all_docs?include_docs=true
   Body: {
     "keys": [
       "daily/2025-10-06.md",
       "daily/2025-10-07.md",
       "daily/2025-10-08.md",
       "daily/2025-10-09.md",
       "daily/2025-10-10.md",
       "daily/2025-10-11.md",
       "daily/2025-10-12.md"
     ]
   }

2. Receives all 7 documents in one HTTP response
3. Analyzes week's task completion rate
4. Sends summary email to user
```

**No Git needed, no working directories, just HTTP requests.**

---

## Implementation Plan

### Phase 1: CouchDB Server Deployment (2 hours)

**Goal:** Deploy self-hosted CouchDB instance on Fly.io

**Deliverables:**
- CouchDB Docker container running on Fly.io
- HTTPS endpoint with SSL certificate
- Admin credentials configured
- Volume mounted for persistent data
- Fly.io app configured for auto-restart

**Files to create/modify:**
- `deploy/couchdb.Dockerfile` - CouchDB container image
- `deploy/couchdb-fly.toml` - Fly.io configuration
- `deploy/couchdb-config.ini` - CouchDB settings (CORS, auth)

**Deployment steps:**
1. Build CouchDB Docker image with custom config
2. Deploy to Fly.io (alongside TaskChampion sync server)
3. Create persistent volume for database storage
4. Configure HTTPS with Fly.io's automatic SSL
5. Test: HTTP GET to verify CouchDB responds

**Success criteria:**
- `curl https://couch-brainplorp-sync.fly.dev/` returns CouchDB welcome JSON
- Admin panel accessible: `https://couch-brainplorp-sync.fly.dev/_utils/`
- Database persists across container restarts

---

### Phase 2: User Setup Wizard Integration (2 hours)

**Goal:** Extend `brainplorp setup` to configure CouchDB + LiveSync

**User flows:**

**Flow 1: First Computer**
1. User runs `brainplorp setup`
2. brainplorp creates CouchDB database for user via HTTP API
3. brainplorp generates unique username/password
4. brainplorp creates `vault/.obsidian/plugins/obsidian-livesync/data.json` with credentials
5. brainplorp installs LiveSync plugin if not present
6. brainplorp displays credentials for user to save
7. User opens Obsidian, enables LiveSync plugin
8. LiveSync syncs vault to CouchDB automatically

**Flow 2: Additional Computer**
1. User runs `brainplorp setup` on new Mac
2. brainplorp prompts: "Do you have CouchDB credentials?"
3. User pastes credentials from Computer 1
4. brainplorp configures LiveSync with same database
5. User opens Obsidian, enables LiveSync
6. Vault downloads from CouchDB automatically

**Flow 3: Mobile Device**
1. User installs Obsidian on iPhone
2. User creates empty vault
3. User goes to Settings → Community Plugins → Browse
4. User installs "Self-hosted LiveSync"
5. User enters CouchDB credentials (from Computer 1)
6. Vault syncs automatically

**Files to create/modify:**
- `src/brainplorp/commands/setup.py` - Add vault sync step
- `src/brainplorp/integrations/couchdb.py` - HTTP client for CouchDB API
- `src/brainplorp/utils/livesync_config.py` - Generate LiveSync config JSON

**Key functions:**
- `create_couchdb_database(username)` - Create user's vault database
- `generate_couchdb_credentials()` - Create username/password pair
- `configure_livesync_plugin(vault_path, credentials)` - Write plugin config
- `verify_livesync_sync(vault_path)` - Check if LiveSync is syncing

**Success criteria:**
- `brainplorp setup` on Computer 1 completes without errors
- User can paste credentials into Computer 2's setup
- LiveSync plugin config JSON is valid and loads in Obsidian
- User opens Obsidian and sees sync happening (status indicator)

---

### Phase 3: Server HTTP API Client (2 hours)

**Goal:** Python library for brainplorp server to access vault via CouchDB

**Use cases:**
1. **Email to inbox** (Sprint 10.2): Append email bullets to `inbox/YYYY-MM.md`
2. **Read daily note** (analytics): Parse today's tasks for completion tracking
3. **Batch reads** (reporting): Read week's daily notes for summary
4. **Create notes** (automation): Generate project notes from templates

**Library interface:**

```
VaultClient(server_url, database, username, password)
  .read_document(path) → document content
  .write_document(path, content) → success/failure
  .update_document(path, update_fn) → handles MVCC retries
  .list_documents(prefix) → list of document IDs
  .batch_read(paths) → dict of path → content
```

**Features:**
- Automatic MVCC retry on conflict (exponential backoff)
- Connection pooling for performance
- Error handling with clear messages
- Logging for debugging
- Unit tests with mock CouchDB

**Files to create:**
- `src/brainplorp/integrations/vault_client.py` - HTTP client library
- `tests/test_vault_client.py` - Unit tests

**Example usage (email to inbox):**

```
High-level pseudocode:

vault = VaultClient(couch_url, "user-jsd-vault", username, password)

def append_email(email_text):
    current_month = "2025-10"
    inbox_path = f"inbox/{current_month}.md"

    def add_bullet(content):
        return content + f"\n- [ ] Email: {email_text}"

    vault.update_document(inbox_path, add_bullet)
    # update_document handles MVCC retries automatically
```

**Success criteria:**
- Can read document from CouchDB via HTTP GET
- Can write document via HTTP PUT with MVCC
- MVCC conflicts retry automatically (tested with concurrent writes)
- Error messages are clear ("Document not found", "Auth failed", etc.)
- Unit tests pass with 100% coverage

---

### Phase 4: CouchDB Views for Analytics (1 hour)

**Goal:** Optimize batch queries using CouchDB map/reduce views

**Problem:** Reading 30 daily notes individually = 30 HTTP requests (slow)

**Solution:** CouchDB views index documents, allow fast queries

**Views to create:**

**View 1: Daily notes by date**
```
Purpose: Get all daily notes in date range for weekly/monthly summaries
Query: /vault/_design/brainplorp/_view/daily_by_date?startkey="2025-10-01"&endkey="2025-10-31"
Returns: List of daily note documents for October
```

**View 2: Tasks by status**
```
Purpose: Count completed vs pending tasks across all daily notes
Query: /vault/_design/brainplorp/_view/tasks_by_status?group=true
Returns: {pending: 42, completed: 158}
```

**View 3: Inbox items by month**
```
Purpose: Track inbox processing rate (unprocessed vs processed items per month)
Query: /vault/_design/brainplorp/_view/inbox_items?group=true
Returns: {"2025-10": {unprocessed: 12, processed: 45}}
```

**Implementation:**
- Create design document with map/reduce functions
- Upload to CouchDB via HTTP PUT
- Query views in analytics code
- Compare performance (view vs. multiple doc reads)

**Files to create:**
- `deploy/couchdb-design-docs.json` - View definitions
- `src/brainplorp/analytics/views.py` - Query view helper functions

**Success criteria:**
- Views return correct results (validated against manual parsing)
- Query performance: <1 second for 30 days of data
- Views update automatically as documents change

---

### Phase 5: Testing & Documentation (2 hours)

**Testing scenarios:**

**Multi-device sync:**
1. Edit file on Mac 1
2. Verify appears on iPhone within 5 seconds
3. Edit same file on iPhone
4. Verify Mac 1 sees changes
5. Edit simultaneously on Mac 1 and iPhone
6. Verify conflict handled (no data loss)

**Offline/online:**
1. Disconnect Mac 1 from internet
2. Create new daily note
3. Reconnect
4. Verify syncs to CouchDB
5. Verify Mac 2 receives new note

**Server operations:**
1. Server appends email to inbox via API
2. Verify Mac sees email in Obsidian
3. Server reads daily note via API
4. Verify content matches Obsidian view

**MVCC conflict resolution:**
1. Server reads inbox (rev: 1-abc)
2. Mac edits inbox (creates rev: 2-def)
3. Server tries to write with stale rev 1-abc
4. Verify server detects conflict
5. Verify server retries with rev 2-def
6. Verify no data lost

**Performance:**
1. Sync 100 small files (daily notes)
2. Measure time to sync
3. Goal: <10 seconds
4. Sync 10MB file (PDF attachment)
5. Goal: <30 seconds

**Documentation to write:**

1. **User Guide: Setting up vault sync**
   - First computer setup
   - Additional computer setup
   - Mobile device setup
   - Troubleshooting common issues

2. **Developer Guide: Server HTTP API**
   - Reading documents
   - Writing documents
   - Handling MVCC conflicts
   - Batch operations
   - View queries

3. **Architecture Doc: Why CouchDB**
   - Comparison with other solutions
   - Trade-offs and limitations
   - Performance characteristics
   - Scaling considerations

**Files to create:**
- `Docs/VAULT_SYNC_USER_GUIDE.md`
- `Docs/VAULT_SYNC_DEVELOPER_GUIDE.md`
- `Docs/VAULT_SYNC_ARCHITECTURE.md`

**Success criteria:**
- All test scenarios pass
- Documentation is clear and complete
- User can follow guide and set up vault sync successfully
- Developer can write server automation using API guide

---

## Configuration

### User Config (~/.config/brainplorp/config.yaml)

```yaml
vault_path: /Users/jsd/vault

taskwarrior_sync:
  enabled: true
  server: https://brainplorp-sync.fly.dev
  client_id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
  encryption_secret: abc123def456...

vault_sync:
  enabled: true
  method: couchdb
  server: https://couch-brainplorp-sync.fly.dev
  database: user-jsd-vault
  username: user-jsd
  password: [encrypted password]
```

### LiveSync Plugin Config (vault/.obsidian/plugins/obsidian-livesync/data.json)

```json
{
  "couchDB_URI": "https://couch-brainplorp-sync.fly.dev",
  "couchDB_USER": "user-jsd",
  "couchDB_PASSWORD": "...",
  "couchDB_DBNAME": "user-jsd-vault",
  "liveSync": true,
  "syncOnSave": true,
  "syncOnStart": true,
  "conflictResolutionStrategy": "automatic"
}
```

**brainplorp setup writes this file automatically.**

---

## User Workflows

### Workflow 1: Capture Task on iPhone

```
Context: User at grocery store, remembers task

1. User opens Obsidian on iPhone
2. Opens inbox/2025-10.md
3. Adds: "- [ ] Buy milk"
4. Closes Obsidian
5. LiveSync syncs automatically (3 seconds)

Later that day:
6. User opens Obsidian on Mac
7. Runs: brainplorp inbox process
8. Sees "Buy milk" in inbox
9. Creates TaskWarrior task from inbox item
10. TaskWarrior syncs to server
11. Task appears in today's daily note on all devices
```

**Key insight:** User never thought about syncing - it just worked.

### Workflow 2: Server Fetches Emails to Inbox

```
Context: Cron job runs on brainplorp server every 15 minutes

1. Server fetches emails from Gmail via IMAP
2. For each unread email:
   - Parse subject/body to markdown bullet
   - Read current month's inbox via CouchDB HTTP GET
   - Append email bullet to inbox content
   - Update inbox via CouchDB HTTP PUT (with MVCC)
3. If MVCC conflict (user edited inbox simultaneously):
   - Server retries with latest revision
   - Merges server's emails with user's edits
4. User opens Obsidian on Mac
5. LiveSync synced new emails automatically
6. User sees emails in inbox, processes with `brainplorp inbox process`
```

**Key insight:** Server and user can both write to vault without conflicts.

### Workflow 3: Weekly Summary Report

```
Context: User wants weekly task completion summary

1. User runs: brainplorp report weekly
2. brainplorp server queries CouchDB view:
   - Get all daily notes from last 7 days
   - View returns indexed data (fast)
3. brainplorp parses task lists from each daily note
4. brainplorp calculates:
   - Total tasks: 87
   - Completed: 64 (74%)
   - Pending: 23 (26%)
   - Overdue: 5
5. brainplorp displays rich table in terminal
6. Optional: Email summary to user
```

**Key insight:** CouchDB views make analytics fast, no need to read 7 documents individually.

---

## Trade-offs and Limitations

### What CouchDB + LiveSync Does Well

✅ **Real-time automatic sync** - Best-in-class UX, no manual commands
✅ **Mobile support** - Works on iPhone/iPad/Android via Obsidian mobile
✅ **Conflict resolution** - MVCC handles simultaneous edits gracefully
✅ **Server HTTP API** - Easy for brainplorp server to read/write vault
✅ **Battle-tested** - CouchDB is mature, used by millions
✅ **Self-hostable** - Runs on Fly.io free tier, user owns data
✅ **Offline support** - Edit offline, syncs when reconnected
✅ **Scalable** - CouchDB handles large vaults (GBs) efficiently

### Limitations and Workarounds

❌ **Requires Obsidian plugin** - Users must install and enable LiveSync
**Mitigation:** brainplorp setup installs plugin automatically, user just enables it

❌ **Entire vault syncs** - Can't selectively sync only brainplorp directories
**Mitigation:** CouchDB is efficient with incremental sync, bandwidth not a problem for text files
**Future:** Could extend LiveSync to support selective sync (advanced feature)

❌ **CouchDB is another service** - More complexity than Git
**Mitigation:** Docker makes deployment trivial, Fly.io handles restarts/SSL automatically

❌ **No built-in encryption at rest** - CouchDB stores data unencrypted on disk
**Mitigation:** Fly.io volumes are encrypted, network traffic is HTTPS
**Future:** Could implement application-level encryption (encrypt content before storing in CouchDB)

❌ **Plugin maintenance** - If LiveSync breaks, users can't sync
**Mitigation:** LiveSync is widely used (10,000+ users), actively maintained
**Fallback:** Users can still use brainplorp on single device, export vault to file

### Compared to Git Automation

**CouchDB wins on:**
- Real-time automatic sync (Git requires manual `brainplorp vault sync`)
- Mobile support (Git requires CLI, not available on iOS/Android)
- Server API simplicity (HTTP requests vs. Git subprocess calls)
- Conflict resolution (MVCC built-in vs. custom merge logic)

**Git would win on:**
- Selective sync (only brainplorp directories)
- Familiarity (developers know Git)
- Version history (full audit trail)

**Decision:** Real-time sync + mobile support are critical for user experience. CouchDB is the right choice.

---

## Security Considerations

### Authentication

**Per-user credentials:**
- Each user gets unique CouchDB username/password
- Generated by brainplorp during setup (strong random password)
- Stored in user's config file (encrypted at rest by OS)
- Never shared across users

**HTTP authentication:**
- All requests require username/password (HTTP Basic Auth)
- HTTPS enforces encrypted transport (Fly.io automatic SSL)
- CouchDB validates credentials on every request

### Data Privacy

**User data isolation:**
- Each user gets separate CouchDB database (e.g., `user-jsd-vault`)
- CouchDB enforces database-level permissions
- User A cannot read User B's database

**Network security:**
- All communication over HTTPS (TLS 1.3)
- Fly.io provides automatic SSL certificates
- No plaintext passwords on wire

**At-rest encryption:**
- Fly.io volumes encrypted by default
- CouchDB data files encrypted at OS level
- Future: Application-level encryption (encrypt content field before storing)

### Threat Model

**Protected against:**
- ✅ Network eavesdropping (HTTPS)
- ✅ Unauthorized database access (per-user auth)
- ✅ Cross-user data leakage (separate databases)
- ✅ Server disk theft (Fly.io volume encryption)

**Not protected against:**
- ⚠️ brainplorp server compromise (server has access to all user vaults via HTTP API)
- ⚠️ User credential theft (if attacker gets username/password, can access vault)
- ⚠️ Obsidian plugin vulnerability (malicious plugin could read vault)

**Future improvements:**
- End-to-end encryption (encrypt on client, decrypt on client, server stores ciphertext)
- Token-based auth (refresh tokens, scope-limited access)
- Audit logs (track all vault modifications)

---

## Performance Characteristics

### Sync Speed

**Initial sync (new device):**
- Small vault (50 notes, 500KB): <5 seconds
- Medium vault (500 notes, 5MB): <30 seconds
- Large vault (5000 notes, 50MB): <3 minutes

**Incremental sync (daily use):**
- Single file edit (5KB): 2-5 seconds
- 10 files edited (50KB): 5-10 seconds
- Large file (1MB): 10-15 seconds

**Factors:**
- Network latency (Fly.io to user)
- CouchDB server load
- Number of concurrent users
- File size

### Server API Performance

**Single document read:**
- HTTP GET: <100ms (including network round-trip)
- Document size: No impact for typical notes (<100KB)

**Batch read (7 daily notes):**
- Using `_all_docs?include_docs=true`: <200ms
- Without view: 7 HTTP requests = ~700ms
- Recommendation: Use batch endpoint for >3 documents

**CouchDB view query:**
- Indexed query (e.g., daily notes by date): <100ms
- First query builds index: <1 second for 100 documents
- Subsequent queries: Fast (index cached)

**Write operations:**
- HTTP PUT: <150ms (including MVCC validation)
- MVCC conflict retry: +100ms per retry (rare)

### Scalability

**Fly.io free tier limits:**
- 3 shared VMs
- 256MB RAM per VM
- 3GB storage
- 160GB bandwidth/month

**CouchDB on 256MB RAM:**
- Can handle ~1000 documents (typical vault size)
- Performance degrades with >10,000 documents (rare)
- Upgrade to paid tier if needed ($7/month for 1GB RAM)

**Concurrent users:**
- Free tier: 1-5 users comfortable
- Paid tier: 50+ users per instance
- CouchDB replication allows multi-datacenter scaling (future)

---

## Migration Path

### From No Sync → CouchDB

**User currently has local-only vault:**

1. User runs `brainplorp setup` → configures CouchDB
2. User enables LiveSync in Obsidian
3. LiveSync uploads entire vault to CouchDB (one-time, <1 minute)
4. User sets up additional devices with same credentials
5. All devices sync automatically

**No data loss risk:** Original vault stays local, CouchDB is additive.

### From iCloud/Dropbox → CouchDB

**User currently syncs via iCloud:**

1. User runs `brainplorp setup` → configures CouchDB
2. User enables LiveSync in Obsidian
3. LiveSync uploads vault to CouchDB
4. User can keep iCloud as backup (no conflict)
5. LiveSync takes over as primary sync method

**Recommendation:** Disable iCloud sync for vault folder to avoid conflicts.

### From Git (if Sprint 10.3 had used Git) → CouchDB

**Future migration if we change approaches:**

1. Export Git repository to filesystem
2. Run `brainplorp vault migrate-to-couchdb`
3. brainplorp reads all files, uploads to CouchDB as documents
4. Git history preserved in CouchDB revision history (partial)
5. User enables LiveSync, continues with CouchDB

**Estimated migration time:** 10 files/second = 100 files in 10 seconds.

---

## Comparison with Other Solutions

### vs. Obsidian Sync (Official, $8/month)

| Feature | Obsidian Sync | brainplorp CouchDB |
|---------|---------------|-------------------|
| Real-time sync | ✅ Yes | ✅ Yes |
| Mobile support | ✅ Yes | ✅ Yes (via LiveSync) |
| Self-hosted | ❌ No | ✅ Yes |
| Cost | $8/month | Free (Fly.io free tier) |
| Server API access | ❌ No | ✅ Yes (HTTP API) |
| End-to-end encryption | ✅ Yes | ⚠️ Future |
| Version history | ✅ 1 year | ⚠️ Limited (CouchDB revisions) |

**Verdict:** brainplorp CouchDB is free and self-hosted, with server API access. Obsidian Sync has better E2E encryption and version history.

### vs. iCloud Drive

| Feature | iCloud Drive | brainplorp CouchDB |
|---------|-------------|-------------------|
| Real-time sync | ⚠️ Eventual | ✅ Real-time (2-5s) |
| Mobile support | ✅ Yes | ✅ Yes |
| Conflict resolution | ❌ Creates .conflict files | ✅ Automatic (MVCC) |
| Server API access | ❌ No | ✅ Yes |
| Cost | Free (5GB) | Free (Fly.io) |

**Verdict:** brainplorp CouchDB has better conflict resolution and server API. iCloud is simpler (no setup).

### vs. Syncthing (P2P)

| Feature | Syncthing | brainplorp CouchDB |
|---------|----------|-------------------|
| Real-time sync | ✅ Yes | ✅ Yes |
| Mobile support | ⚠️ Android only | ✅ iOS + Android |
| Server API access | ❌ No | ✅ Yes |
| Setup complexity | ⚠️ High (install on all devices) | ✅ Low (brainplorp setup) |
| Conflict resolution | ⚠️ Creates .conflict files | ✅ Automatic (MVCC) |

**Verdict:** brainplorp CouchDB has better conflict resolution, iOS support, and server API. Syncthing is more private (P2P).

### vs. Git + Obsidian Git Plugin

| Feature | Git Plugin | brainplorp CouchDB |
|---------|-----------|-------------------|
| Real-time sync | ❌ Manual/scheduled | ✅ Automatic (2-5s) |
| Mobile support | ❌ No (Git not on mobile) | ✅ Yes |
| Server API access | ✅ Yes (git clone) | ✅ Yes (HTTP) |
| Version history | ✅ Full Git history | ⚠️ Limited |
| Selective sync | ✅ Yes (.gitignore) | ❌ No (entire vault) |
| Conflict resolution | ⚠️ Manual merge | ✅ Automatic (MVCC) |
| Setup complexity | ⚠️ High (Git knowledge) | ✅ Low (brainplorp setup) |

**Verdict:** brainplorp CouchDB has better UX (real-time, mobile, auto-conflicts). Git has better version history and selective sync.

**Decision:** For brainplorp's target users (non-technical), CouchDB is the clear winner.

---

## Future Enhancements

### Sprint 11+: Advanced Features

**End-to-end encryption:**
- Encrypt document content on client before uploading to CouchDB
- Server stores ciphertext, can't read user's vault
- Encryption key derived from user's password
- Implementation: 4-6 hours

**Selective sync:**
- Allow user to specify which folders sync
- Example: Sync `daily/` and `inbox/`, skip `journal/` (personal)
- Requires LiveSync plugin modification or custom sync client
- Implementation: 8-12 hours

**Conflict resolution UI:**
- When automatic merge fails, show visual diff in terminal
- `brainplorp vault conflicts` command to list conflicts
- `brainplorp vault resolve <file>` to merge manually
- Implementation: 3-4 hours

**Vault analytics dashboard:**
- Web UI showing sync activity, storage usage, device list
- Real-time sync status for all devices
- Conflict history and resolution rate
- Implementation: 12-16 hours (web app)

**Multi-vault support:**
- User has multiple Obsidian vaults (work, personal)
- Each vault gets separate CouchDB database
- `brainplorp setup --vault work` to configure second vault
- Implementation: 2-3 hours

---

## Success Metrics

**Must Have (Sprint 10.3):**
- [ ] CouchDB server running on Fly.io (accessible via HTTPS)
- [ ] `brainplorp setup` configures LiveSync plugin automatically
- [ ] User can enable LiveSync in Obsidian, vault syncs
- [ ] Vault syncs across Mac 1 → CouchDB → Mac 2
- [ ] Mobile device (iPhone) can sync vault via LiveSync
- [ ] brainplorp server can read document via HTTP API
- [ ] brainplorp server can write document via HTTP API (with MVCC)
- [ ] `brainplorp vault status` shows sync health
- [ ] Documentation complete (user guide + developer guide)

**Should Have (Nice to have for Sprint 10.3):**
- [ ] MVCC conflict automatically retries (tested with concurrent writes)
- [ ] CouchDB views for analytics (daily notes by date)
- [ ] Offline edit syncs when reconnected (tested)
- [ ] Sync performance: <10 seconds for 100 files
- [ ] Error messages are clear and actionable

**Could Have (Future sprints):**
- [ ] End-to-end encryption
- [ ] Selective sync (choose folders)
- [ ] Conflict resolution UI
- [ ] Web dashboard for sync monitoring
- [ ] Multi-vault support

---

## Risk Assessment

### High Risk

**Risk:** LiveSync plugin breaks in future Obsidian update
**Impact:** Users can't sync vault
**Mitigation:**
- LiveSync is actively maintained with 10,000+ users
- Community would fix critical issues quickly
- Fallback: Users can still use brainplorp on single device
**Contingency:** Fork LiveSync if abandoned, maintain our own version

**Risk:** CouchDB data corruption (rare but catastrophic)
**Impact:** User loses vault data
**Mitigation:**
- CouchDB is battle-tested, data corruption extremely rare
- Fly.io volumes have automatic snapshots (daily)
- User's local Obsidian vault is always source of truth (can re-upload)
**Contingency:** Implement automatic daily backups to S3 (Sprint 11)

### Medium Risk

**Risk:** MVCC conflicts cause data loss (implementation bug)
**Impact:** User's edits overwritten by server/other device
**Mitigation:**
- Extensive testing of concurrent writes (Phase 5)
- Start with conservative retry logic (abort on ambiguous conflicts)
- Monitor conflict rate in production
**Contingency:** Add conflict logging, alert on high conflict rate

**Risk:** CouchDB performance degrades with large vault (>10,000 files)
**Impact:** Slow sync, poor user experience
**Mitigation:**
- Most vaults have <1,000 files (typical user)
- CouchDB handles 10,000 documents comfortably on 256MB RAM
- Can upgrade Fly.io instance if needed ($7/month for 1GB RAM)
**Contingency:** Implement sharding (split vault across multiple databases)

### Low Risk

**Risk:** Setup wizard fails to install LiveSync plugin
**Impact:** User must install plugin manually
**Mitigation:**
- Document manual installation steps clearly
- Most users already have LiveSync installed
**Contingency:** User installs plugin from Community Plugins (5 seconds)

**Risk:** HTTP API authentication credentials leak
**Impact:** Attacker can read/write user's vault
**Mitigation:**
- Credentials stored encrypted in user's config file
- HTTPS prevents network sniffing
- Each user has unique credentials (blast radius limited)
**Contingency:** Implement token rotation, audit logs

---

## Testing Strategy

### Manual Testing Checklist

**Setup (two Macs, one iPhone):**

- [ ] Mac 1: Fresh brainplorp install, no existing vault sync
- [ ] Mac 1: Run `brainplorp setup`, configure CouchDB
- [ ] Mac 1: Verify LiveSync config file created
- [ ] Mac 1: Open Obsidian, enable LiveSync plugin
- [ ] Mac 1: Verify sync status shows "Connected"
- [ ] Mac 1: Create test file `test-sync.md`
- [ ] Mac 1: Verify file uploads to CouchDB (check CouchDB Fauxton UI)

**Multi-device sync:**

- [ ] Mac 2: Fresh brainplorp install, empty vault
- [ ] Mac 2: Run `brainplorp setup`, paste credentials from Mac 1
- [ ] Mac 2: Open Obsidian, enable LiveSync
- [ ] Mac 2: Verify `test-sync.md` downloads from CouchDB
- [ ] Mac 2: Edit `test-sync.md`, add line "Hello from Mac 2"
- [ ] Mac 1: Verify sees "Hello from Mac 2" within 5 seconds

**Mobile sync:**

- [ ] iPhone: Install Obsidian, create empty vault
- [ ] iPhone: Install Self-hosted LiveSync plugin
- [ ] iPhone: Enter CouchDB credentials from Mac 1
- [ ] iPhone: Verify vault downloads (all files)
- [ ] iPhone: Create file `mobile-test.md`
- [ ] Mac 1: Verify sees `mobile-test.md` within 5 seconds

**Conflict resolution:**

- [ ] Mac 1: Edit `test-sync.md`, add "Line from Mac 1"
- [ ] Mac 2: Edit `test-sync.md` (same file), add "Line from Mac 2"
- [ ] Both Macs: Save files simultaneously (within 1 second)
- [ ] Verify: LiveSync creates conflict file (e.g., `test-sync.conflicted.md`)
- [ ] Verify: No data lost (both lines present in one of the files)

**Server API:**

- [ ] Server: Read `test-sync.md` via HTTP GET
- [ ] Verify: Content matches what's in Obsidian
- [ ] Server: Append line "Hello from server" via HTTP PUT
- [ ] Mac 1: Verify sees "Hello from server" within 5 seconds
- [ ] Verify: No conflicts (MVCC worked)

**Offline/online:**

- [ ] Mac 1: Disconnect from internet (airplane mode)
- [ ] Mac 1: Edit `test-sync.md`, add "Offline edit"
- [ ] Mac 1: Verify LiveSync shows "Disconnected" status
- [ ] Mac 1: Reconnect to internet
- [ ] Mac 1: Verify LiveSync syncs automatically
- [ ] Mac 2: Verify sees "Offline edit" within 5 seconds

**Performance:**

- [ ] Create 100 small files (1KB each)
- [ ] Mac 2: Enable LiveSync, measure time to download all files
- [ ] Goal: <10 seconds
- [ ] Create 1 large file (10MB PDF)
- [ ] Measure time to sync
- [ ] Goal: <30 seconds

### Automated Tests

**Unit tests:**
- CouchDB client (read, write, MVCC retry)
- LiveSync config generation
- Credentials encryption/decryption
- Document parsing (markdown to JSON)

**Integration tests:**
- `brainplorp setup` end-to-end (mock CouchDB server)
- Server HTTP API (real CouchDB in Docker)
- MVCC concurrent writes (simulate race conditions)

**Files to create:**
- `tests/test_couchdb_client.py` - Unit tests for HTTP client
- `tests/test_livesync_config.py` - Config generation tests
- `tests/test_vault_sync_integration.py` - End-to-end sync tests

---

## Documentation Deliverables

### 1. User Guide: Vault Sync Setup

**Docs/VAULT_SYNC_USER_GUIDE.md**

Contents:
- Introduction to vault sync (why it's useful)
- Prerequisites (Obsidian installed, brainplorp installed)
- Setup walkthrough (first computer)
- Setup walkthrough (additional computers)
- Setup walkthrough (mobile devices)
- Troubleshooting (common errors and fixes)
- FAQ (selective sync, encryption, conflicts)

### 2. Developer Guide: Server HTTP API

**Docs/VAULT_SYNC_DEVELOPER_GUIDE.md**

Contents:
- CouchDB HTTP API basics
- Reading documents (GET)
- Writing documents (PUT with MVCC)
- Batch operations (_all_docs)
- CouchDB views (queries)
- Error handling
- Example code (Python)

### 3. Architecture Document

**Docs/VAULT_SYNC_ARCHITECTURE.md**

Contents:
- System overview (diagram)
- Why CouchDB (trade-offs)
- MVCC conflict resolution (detailed explanation)
- Security model (auth, encryption)
- Performance characteristics
- Scalability considerations
- Comparison with alternatives (Git, Syncthing, etc.)

---

## Sprint Completion Checklist

- [ ] Phase 1: CouchDB deployed on Fly.io (2h)
- [ ] Phase 2: Setup wizard integration (2h)
- [ ] Phase 3: Server HTTP API client (2h)
- [ ] Phase 4: CouchDB views for analytics (1h)
- [ ] Phase 5: Testing & documentation (2h)
- [ ] All manual tests pass
- [ ] All automated tests pass
- [ ] User guide complete
- [ ] Developer guide complete
- [ ] Architecture doc complete
- [ ] Git commit and push changes
- [ ] Update PM_HANDOFF.md with completion notes
- [ ] Version bump to v1.7.0
- [ ] Tag release: `git tag v1.7.0`

**Total Estimated Effort:** 9 hours

**Sign-off Requirements:**
- [ ] PM reviews implementation
- [ ] PM tests on two Macs + iPhone
- [ ] PM verifies documentation is complete
- [ ] PM approves Sprint 10.3 as complete

---

## Document Maintenance

**Created:** 2025-10-12 by PM Claude
**Last Updated:** 2025-10-12 (rewritten from Git to CouchDB)
**Related Sprints:**
- Sprint 10.2 (Cloud Sync - TaskWarrior)
- Sprint 10.1.1 (Installation Hardening)

**Dependencies:**
- Sprint 10.2 must be complete (Fly.io infrastructure deployed)
- Obsidian installed on user's device
- LiveSync plugin available (Community Plugin)

**Update Protocol:**
- Update spec if CouchDB architecture changes
- Update if LiveSync plugin interface changes
- Update when adding new features (encryption, selective sync)
