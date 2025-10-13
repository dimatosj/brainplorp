# Vault Sync Architecture

**Sprint 10.3: Technical Design and Trade-offs**

## Executive Summary

Vault sync uses **CouchDB** as a central server with **Obsidian LiveSync plugin** as the client-side sync agent. This architecture provides:
- ✅ Real-time automatic sync (2-5 seconds)
- ✅ Mobile support (iOS/Android via LiveSync)
- ✅ Server HTTP API for automation
- ✅ Built-in conflict resolution (MVCC)
- ✅ Self-hostable on Fly.io (free tier)

## System Overview

```
┌─────────────────────────────────────────────────────┐
│          CouchDB Server (Fly.io)                     │
│                                                      │
│  Database: user-jsd-vault                            │
│  ├─ daily/2025-10-12.md (document)                  │
│  ├─ inbox/2025-10.md (document)                     │
│  └─ ... (all vault files as CouchDB documents)      │
│                                                      │
│  Features:                                           │
│  • HTTP/WebSocket API                                │
│  • MVCC conflict detection                          │
│  • Automatic replication                            │
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
    │  Local files │   │Local files│   │  VaultClient│
    │  ↕ CouchDB   │   │ ↕ CouchDB │   │   (no local)│
    └──────────────┘   └───────────┘   └─────────────┘
```

**Single Source of Truth:** CouchDB database contains all vault files as documents.

**Three Access Patterns:**
1. **User devices** (Mac, iPhone) - LiveSync plugin syncs continuously
2. **brainplorp server** (Fly.io) - HTTP API for automation
3. **External scripts** - VaultClient library for custom tools

## Why CouchDB?

### Requirements

1. **Real-time automatic sync** - User never runs manual sync commands
2. **Mobile support** - Must work on iOS/Android (no CLI access)
3. **Server API** - brainplorp server needs to read/write vault
4. **Conflict resolution** - Handle simultaneous edits gracefully
5. **Self-hostable** - User owns their data
6. **Low cost** - Free tier must support typical usage

### CouchDB Advantages

**✅ Real-time sync via LiveSync plugin**
- Obsidian community plugin with 10,000+ users
- Battle-tested, actively maintained
- Works on all platforms (macOS, iOS, Android, Windows, Linux)

**✅ HTTP REST API**
- Simple HTTP requests for read/write
- No complex protocol, just `GET`/`PUT` with JSON
- Easy to integrate from server scripts

**✅ Built-in MVCC conflict detection**
- Each document has a revision number (`_rev`)
- Update requires current revision
- If stale: HTTP 409 Conflict → Retry
- No custom conflict resolution needed

**✅ Mature and stable**
- Apache project since 2008
- Used by millions (npm, Ubuntu, etc.)
- Excellent documentation

**✅ Free hosting on Fly.io**
- Free tier: 3GB storage, 256MB RAM
- Typical vault: 10-100MB
- Paid tier: $1.50/month for 10GB

### Alternatives Considered

#### 1. Git + Git Automation

**Pros:**
- Version history (full audit trail)
- Familiar to developers
- Selective sync (.gitignore)

**Cons:**
- ❌ No mobile support (Git CLI not available on iOS)
- ❌ Manual sync commands required
- ❌ Complex merge conflicts (3-way merges)
- ❌ Poor for non-technical users

**Why rejected:** Real-time sync and mobile support are critical.

#### 2. Syncthing (P2P)

**Pros:**
- True peer-to-peer (no server)
- Privacy-focused

**Cons:**
- ❌ No iOS support (only Android)
- ❌ Complex setup (install on all devices)
- ❌ No server API (brainplorp server can't access vault)
- ❌ Creates `.conflict` files (manual resolution)

**Why rejected:** iOS support and server API are requirements.

#### 3. iCloud Drive / Dropbox

**Pros:**
- Built into OS
- Simple setup

**Cons:**
- ❌ Eventual consistency (not real-time)
- ❌ Poor conflict resolution (creates duplicate files)
- ❌ No server API (brainplorp server can't access files)
- ❌ Privacy concerns (third-party controls data)

**Why rejected:** Conflict resolution is poor, no server API.

#### 4. Obsidian Sync (Official)

**Pros:**
- Official support
- End-to-end encryption
- Excellent UX

**Cons:**
- ❌ $8/month cost
- ❌ No server API (brainplorp server can't access vault)
- ❌ Not self-hostable

**Why rejected:** Cost and no server API access.

### Decision Matrix

| Feature | CouchDB | Git | Syncthing | iCloud | Obsidian Sync |
|---------|---------|-----|-----------|--------|---------------|
| Real-time sync | ✅ Yes | ❌ Manual | ✅ Yes | ⚠️ Eventual | ✅ Yes |
| Mobile (iOS) | ✅ Yes | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| Server API | ✅ Yes | ✅ Yes | ❌ No | ❌ No | ❌ No |
| Conflict resolution | ✅ Auto | ⚠️ Manual | ⚠️ Manual | ❌ Duplicates | ✅ Auto |
| Self-hosted | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| Cost | ✅ Free | ✅ Free | ✅ Free | ✅ Free | ❌ $8/mo |

**Winner:** CouchDB meets all requirements.

## Architecture Details

### Document Structure

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
- `_id` - Document ID (file path)
- `_rev` - CouchDB revision (for MVCC)
- `content` - Actual markdown text
- `path` - Redundant with `_id`, for clarity
- `mtime` - Last modified timestamp
- `deleted` - Tombstone flag for deleted files

### MVCC Conflict Resolution

**Multi-Version Concurrency Control** - CouchDB's optimistic locking.

**Scenario: User edits on Mac, server appends email to same file**

```
Initial State:
  inbox/2025-10.md (_rev: "1-xyz")
  Content: "- [ ] Old task"

Step 1: Mac edits
  Mac reads: _rev "1-xyz", content "- [ ] Old task"
  Mac adds: "- [ ] Buy groceries"
  Mac saves with _rev "1-xyz"
  → CouchDB accepts, creates _rev "2-abc"

Step 2: Server tries to edit (simultaneous)
  Server reads: _rev "1-xyz" (stale!)
  Server adds: "- [ ] Email: Meeting"
  Server saves with _rev "1-xyz"
  → CouchDB rejects: HTTP 409 Conflict

Step 3: Server retries
  Server reads: _rev "2-abc" (latest)
  Server sees Mac's changes: "- [ ] Buy groceries"
  Server adds: "- [ ] Email: Meeting"
  Server saves with _rev "2-abc"
  → CouchDB accepts, creates _rev "3-def"

Final State:
  inbox/2025-10.md (_rev: "3-def")
  Content:
    - [ ] Old task
    - [ ] Buy groceries
    - [ ] Email: Meeting
```

**Result:** No data loss, automatic merge.

**VaultClient retry strategy:**
- Attempt 1: Immediate
- Attempt 2: +100ms delay
- Attempt 3: +200ms delay
- Attempt 4: +400ms delay
- Attempt 5: +800ms delay
- Total: 1.5 seconds max

**If all retries fail:**
- Raise `VaultUpdateConflictError`
- Log conflict details
- Alert user

### True Conflicts

**When same line is edited:**
- CouchDB keeps both versions
- LiveSync creates `.conflicted.md` file
- User resolves manually in Obsidian
- Delete `.conflicted.md` after merging

**brainplorp detects conflicts:**
```bash
brainplorp vault status
# Shows: "⚠️  Conflicts detected: inbox/2025-10.md"
```

### Security Model

**Authentication:**
- Each user gets unique CouchDB username/password
- HTTP Basic Auth on all requests
- HTTPS encrypts credentials in transit

**Database Isolation:**
- One database per user (`user-{username}-vault`)
- CouchDB enforces permissions per database
- User A cannot read User B's database

**Encryption:**
- **In transit:** TLS 1.3 (HTTPS)
- **At rest:** Fly.io volume encryption (OS-level)
- **Not encrypted:** Vault content in CouchDB (plain text)

**Future:** End-to-end encryption (encrypt on client, decrypt on client, server stores ciphertext).

### Deployment Architecture

**CouchDB Server:**
- Fly.io app: `couch-brainplorp-sync.fly.dev`
- Region: San Jose (SJC)
- VM: 256MB RAM, 1 shared CPU
- Storage: 10GB persistent volume
- Docker image: `couchdb:3.3.3`

**Configuration:**
```ini
[httpd]
enable_cors = true

[cors]
origins = *
credentials = true
```

**Admin Credentials:**
- Stored in Fly.io secrets (encrypted)
- Used only during user setup (create database, create user)

### State Synchronization Pattern

**Critical principle:** Local operations write to local files, server operations write to CouchDB.

**Context 1: Local CLI (user at Mac)**
```
User runs: brainplorp start
1. Query TaskWarrior for tasks
2. Write to LOCAL vault files (existing behavior)
3. LiveSync detects change, syncs to CouchDB (2-5s)
4. Other devices sync from CouchDB

State Sync: TaskWarrior → Local files → LiveSync → CouchDB → Other devices
```

**Context 2: Server automation**
```
Server runs: email fetch
1. Fetch emails from Gmail
2. Write to COUCHDB via HTTP API (no local files)
3. All devices sync from CouchDB via LiveSync

State Sync: Email → CouchDB → LiveSync → All clients
```

**Why context matters:**
- Local: Fast file I/O, LiveSync handles propagation
- Server: No local files, must use CouchDB HTTP API

## Performance Characteristics

### Sync Speed

**Incremental sync (daily use):**
- Small file (5KB): 2-5 seconds
- Medium file (50KB): 5-10 seconds
- Large file (1MB): 10-30 seconds

**Initial sync (new device):**
- Small vault (50 files, 500KB): <5 seconds
- Medium vault (500 files, 5MB): <30 seconds
- Large vault (5000 files, 50MB): <3 minutes

**Factors:**
- Network latency (user → Fly.io)
- CouchDB server load
- Number of concurrent users

### Server API Performance

**Single document read:**
- HTTP GET: <100ms (including network)
- CouchDB lookup: ~10ms

**Batch read (7 documents):**
- HTTP POST to `_all_docs`: <200ms
- Without batch: 7 × 100ms = 700ms
- **Recommendation:** Use batch for >3 documents

**Write operations:**
- HTTP PUT: <150ms (including MVCC validation)
- MVCC conflict retry: +100-800ms (rare)

### Scalability

**Fly.io free tier:**
- 256MB RAM
- Supports ~1000 documents (typical vault)
- Bandwidth: 160GB/month (sufficient for 100+ users)

**Paid tier ($1.50/month for 10GB storage):**
- 1GB RAM
- Supports ~10,000 documents (large vault)
- Bandwidth: Same (160GB/month)

**CouchDB limits:**
- Max database size: 4TB (theoretical)
- Max document size: 4GB (impractical for markdown)
- Max documents: Unlimited (millions)

**Typical brainplorp vault:**
- Files: 100-500
- Size: 1-10MB
- CouchDB overhead: 5x (metadata + revisions)
- Actual size: 5-50MB in CouchDB

## Limitations and Trade-offs

### What Works Well

✅ **Real-time sync** - Changes appear on all devices in 2-5 seconds
✅ **Mobile support** - Works on iPhone/iPad/Android via LiveSync
✅ **Conflict resolution** - MVCC handles most conflicts automatically
✅ **Server API** - HTTP requests are simple and reliable
✅ **Self-hosted** - User owns data, no vendor lock-in
✅ **Cost** - Free tier sufficient for most users

### Known Limitations

❌ **Entire vault syncs** - Can't selectively sync only `daily/` folder
- **Impact:** Mobile devices get full vault (may include private notes)
- **Mitigation:** Use separate vaults for work/personal
- **Future:** Extend LiveSync to support folder filters

❌ **Plugin dependency** - Requires Obsidian LiveSync plugin
- **Impact:** If plugin breaks, sync stops
- **Mitigation:** LiveSync is widely used (10,000+ users), actively maintained
- **Fallback:** Revert to local-only vault, export to new sync method

❌ **No encryption at rest** - CouchDB stores plain text on server
- **Impact:** Server admin can read vault contents
- **Mitigation:** Fly.io volume encryption (OS-level)
- **Future:** End-to-end encryption (client-side encrypt/decrypt)

❌ **Limited version history** - CouchDB keeps only recent revisions
- **Impact:** Can't view document history from 6 months ago
- **Mitigation:** Git backup for audit trail (manual)
- **Alternative:** Use Obsidian Sync for 1-year history ($8/month)

### Edge Cases

**Scenario: Server down during sync**
- User edits locally
- LiveSync can't reach server
- Changes queue locally
- When server returns, changes upload automatically
- **Result:** No data loss

**Scenario: Conflict during offline edit**
- User A edits file offline
- User B edits same file online
- User A comes back online
- LiveSync detects conflict, creates `.conflicted.md`
- **Result:** User resolves manually

**Scenario: Database corruption**
- CouchDB detects corruption on startup
- Fly.io restores from snapshot (daily backups)
- Recent changes (last 24 hours) may be lost
- **Result:** User re-syncs from local vault (LiveSync uploads)

## Future Enhancements

### Sprint 11+: Advanced Features

**End-to-end encryption:**
- Encrypt content on client before upload
- Server stores ciphertext (can't read)
- Encryption key derived from user password
- **Effort:** 4-6 hours
- **Trade-off:** Breaks server API (can't parse encrypted content)

**Selective sync:**
- User chooses which folders to sync
- Example: Sync `daily/` and `inbox/`, skip `journal/`
- Requires LiveSync modification or custom client
- **Effort:** 8-12 hours

**Conflict resolution UI:**
- Visual diff in terminal
- `brainplorp vault resolve <file>` command
- Side-by-side comparison
- **Effort:** 3-4 hours

**CouchDB Views (deferred from Sprint 10.3):**
- Index documents for fast queries
- Analytics queries (tasks by status, notes by date)
- **Effort:** 1-2 hours

**Vault analytics dashboard:**
- Web UI showing sync activity
- Storage usage, device list
- Conflict history
- **Effort:** 12-16 hours

## Testing Strategy

**Unit tests (required):**
- `test_vault_client.py` - 14 tests with `responses` library
- Mock HTTP requests, test MVCC retry logic
- **Coverage:** 100% of VaultClient methods

**Integration tests (optional, manual):**
- Real CouchDB in Docker container
- Test actual HTTP interactions
- Validate MVCC behavior against real server

**Manual testing:**
- Mac 1 → Mac 2 sync (Lead Engineer tests)
- iPhone sync (PM tests, reports results)
- Conflict scenarios (simultaneous edits)
- Offline/online transitions

## Monitoring and Debugging

### Health Checks

**CouchDB server:**
```bash
curl https://couch-brainplorp-sync.fly.dev/
# Should return: {"couchdb":"Welcome","version":"3.3.3",...}
```

**User vault status:**
```bash
brainplorp vault status
# Shows: sync config, conflicts, credentials
```

### Logs

**Fly.io logs:**
```bash
~/.fly/bin/flyctl logs -a couch-brainplorp-sync
```

**CouchDB logs:**
- Stored in `/var/log/couchdb/` inside container
- Access via `flyctl ssh console`

### Common Issues

**Authentication failed:**
- Credentials incorrect
- Re-run `brainplorp setup` with correct credentials

**Connection timeout:**
- Fly.io server down (check https://status.fly.io)
- Network firewall blocking HTTPS
- Check `curl https://couch-brainplorp-sync.fly.dev/`

**Sync stopped:**
- LiveSync plugin disabled
- Obsidian needs restart
- Check Settings → Self-hosted LiveSync

## Conclusion

CouchDB + LiveSync provides the best balance of:
- **User experience** - Real-time automatic sync, no manual commands
- **Mobile support** - Works on iPhone/iPad/Android via LiveSync
- **Developer experience** - Simple HTTP API for server automation
- **Cost** - Free tier sufficient for most users
- **Reliability** - Battle-tested technology, 10+ years mature

**Trade-offs accepted:**
- Entire vault syncs (no selective sync yet)
- Plugin dependency (LiveSync required)
- No encryption at rest (plain text on server)

**Future work addresses these limitations while maintaining core benefits.**

## References

- CouchDB docs: https://docs.couchdb.org/
- LiveSync plugin: https://github.com/vrtmrz/obsidian-livesync
- Fly.io docs: https://fly.io/docs/
- Sprint 10.3 spec: `Docs/sprints/SPRINT_10.3_VAULT_SYNC_SPEC.md`
- VaultClient API: `Docs/VAULT_SYNC_DEVELOPER_GUIDE.md`
