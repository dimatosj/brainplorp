# Vault Sync Architecture Decision - Reference Document

**Date:** 2025-10-12
**Sprint:** 10.3
**Decision:** Pure CouchDB + Obsidian LiveSync plugin
**Status:** Finalized - Ready for implementation

---

## Executive Summary

brainplorp will use **CouchDB + Obsidian LiveSync plugin** for vault synchronization across multiple devices (Mac, iPhone, iPad, Android). This decision provides real-time automatic sync, mobile support, and a clear evolution path to production-grade security.

**Key Decision Points:**
- ✅ Real-time sync (2-5 seconds) without manual commands
- ✅ Mobile support (iOS/Android via Obsidian LiveSync)
- ✅ Server HTTP API for brainplorp automation
- ✅ Built-in conflict resolution (MVCC)
- ✅ Evolution path to E2E encryption (no rearchitecture)
- ✅ 9 hours implementation vs 280 hours for custom solution

---

## Decision Context

### Original Proposal: Git Automation
Initial Sprint 10.3 spec proposed Git-based sync with selective sync capability. User challenged this approach, asking for comparison with CouchDB.

**Git Advantages:**
- Selective sync via .gitignore
- Full version history
- Developer familiarity

**Git Disadvantages:**
- Manual sync commands required
- No mobile support (no Obsidian Git plugin for iOS/Android)
- Complex conflict resolution (manual merge)
- Subprocess overhead for server operations

### Alternative Considered: Hybrid Git + CouchDB
Briefly considered using both:
- CouchDB for real-time sync (frontend)
- Git for server operations (analytics, backups)

**User's Critical Insight:** "wouldn't there be sync risk if we used both?"

**Analysis:** YES - Two sources of truth can diverge:
```
Timeline:
1. User edits daily note in Obsidian
2. LiveSync syncs to CouchDB (rev: 2-abc)
3. Server reads from Git mirror (stale, rev: 1-xyz)
4. Server modifies Git mirror, commits, pushes
5. CouchDB has rev 2-abc, Git has rev 1-xyz+changes
6. DIVERGENCE: Which is correct?
```

**Conclusion:** Hybrid approach rejected - unnecessary complexity and sync risk.

---

## Final Architecture: Pure CouchDB + LiveSync

### High-Level Design

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
    │  Obsidian    │   │ Obsidian  │   │ brainplorp  │
    │  + LiveSync  │   │ + LiveSync│   │  automation │
    └──────────────┘   └───────────┘   └─────────────┘
```

### Why CouchDB Wins

| Factor | CouchDB | Git |
|--------|---------|-----|
| **Real-time sync** | ✅ Automatic (2-5s) | ❌ Manual commands |
| **Mobile support** | ✅ iOS/Android | ❌ No mobile client |
| **Server API** | ✅ HTTP/REST | ❌ Subprocess calls |
| **Conflict resolution** | ✅ MVCC (automatic) | ❌ Manual merge |
| **Selective sync** | ❌ Syncs entire vault | ✅ .gitignore |
| **Version history** | ⚠️ Limited revisions | ✅ Full history |

**Critical Use Cases:**
1. **Task capture on iPhone** - Requires mobile sync (CouchDB only option)
2. **Real-time sync** - Edit on Mac, see on iPhone instantly (Git requires manual pull)
3. **Email-to-inbox automation** - Server needs vault access (CouchDB HTTP API)

---

## Multi-User Security Model

### Current Architecture (Sprint 10.3)

**Database-Level Isolation:**
- One CouchDB database per user
- Database naming: `user-alice-vault`, `user-bob-vault`
- Each user gets unique credentials (username/password)
- CouchDB enforces permissions on every HTTP request

**Security Properties:**
- ✅ Users cannot access each other's databases (403 Forbidden)
- ✅ HTTPS encrypts data in transit
- ✅ Disk encryption protects data at rest
- ⚠️ Server can read vault contents (for automation)
- ❌ No end-to-end encryption yet

**Threat Model (Sprint 10.3):**
- **Protected against:** Network eavesdropping, unauthorized users, disk theft
- **NOT protected against:** Malicious server admin, server compromise
- **Acceptable for:** 5-10 trusted users with transparency about server access

### Evolution Path to Production Security

#### Sprint 11: End-to-End Encryption (5-10 hours)
- Client-side encryption in LiveSync plugin
- Server stores ciphertext only
- Encryption key never leaves user devices
- Server can no longer read vault contents
- **Result:** Zero-knowledge architecture

#### Sprint 12: Custom Sync Client (15-20 hours)
- Replace LiveSync with custom brainplorp sync client
- Obsidian plugin to hook file events
- Direct CouchDB replication protocol
- Add selective sync capability
- **Result:** Full control over sync behavior

#### Sprint 13: External Authentication (20-30 hours)
- OAuth integration (Google, GitHub)
- JWT tokens for session management
- Remove per-user CouchDB credentials
- Centralized user management
- **Result:** Professional authentication flow

**Total Evolution Effort:** 60-90 hours over 12-18 months
**Key Point:** This is EVOLUTION, not rearchitecture. CouchDB remains the foundation.

---

## Ground-Up Architecture Comparison

### Question from User
"how would we do it from the ground up if couchDB + livesync didn't exist"

### Custom Sync Protocol Design

**Architecture:**
```
┌─────────────────────────────────────────────────────┐
│          Sync Server (Fly.io)                        │
│                                                      │
│  PostgreSQL (operations log):                       │
│  ├─ Event 1: Create daily/2025-10-12.md            │
│  ├─ Event 2: Edit daily/2025-10-12.md (line 5)     │
│  ├─ Event 3: Delete inbox/2025-09.md               │
│  └─ ... (immutable event stream)                    │
│                                                      │
│  S3/Minio (encrypted blobs):                        │
│  ├─ blob-abc123 (encrypted markdown)                │
│  ├─ blob-def456 (encrypted markdown)                │
│  └─ ... (content-addressed storage)                 │
│                                                      │
│  WebSocket API:                                      │
│  • Push events to clients in real-time              │
│  • Operational Transformation (OT)                  │
│  • Conflict-free Replicated Data Type (CRDT)       │
└─────────────────────────────────────────────────────┘
              ▲                ▲                ▲
              │                │                │
          WebSocket        WebSocket        WebSocket
              │                │                │
    ┌─────────┴────┐   ┌──────┴────┐   ┌──────┴──────┐
    │   Mac 1      │   │  iPhone   │   │   Server    │
    │  Custom      │   │  Custom   │   │ brainplorp  │
    │  Sync Client │   │  Sync     │   │  automation │
    └──────────────┘   └───────────┘   └─────────────┘
```

**Key Features:**
1. **Event Sourcing** - Operations log instead of current state
2. **OT/CRDT** - Automatic conflict resolution (merge character edits)
3. **E2E Encryption** - Built-in from day 1
4. **Real-time Push** - WebSocket events
5. **Selective Sync** - Client chooses directories
6. **Offline-First** - Queue operations, sync when online

**Development Estimate:** 200-300 hours

**Component Breakdown:**
- PostgreSQL schema + event log (20 hours)
- S3 blob storage + encryption (20 hours)
- WebSocket server + push protocol (30 hours)
- OT/CRDT conflict resolution (60 hours) ⚠️ HARD
- iOS sync client (40 hours)
- Android sync client (40 hours)
- Testing + edge cases (60 hours)

### Comparison: CouchDB vs Ground-Up

| Factor | CouchDB | Ground-Up |
|--------|---------|-----------|
| **Time to market** | 9 hours | 280 hours |
| **Conflict resolution** | MVCC (basic) | OT/CRDT (advanced) |
| **E2E encryption** | Sprint 11 (10h) | Built-in |
| **Mobile clients** | Existing (LiveSync) | Build from scratch |
| **Selective sync** | Sprint 12 (15h) | Built-in |
| **Battle-tested** | Yes (npm, others) | No |
| **Technical ownership** | Depend on CouchDB | Full control |

**Strategic Recommendation:**
```
Start with CouchDB+LiveSync (Sprint 10.3, 9 hours)
→ Validate workflows with 5-10 users
→ Add E2E encryption (Sprint 11, 10 hours)
→ Build custom sync client if needed (Sprint 12-14, 100 hours)
→ Migrate to PostgreSQL+S3 only if user demand justifies (Sprint 15+, 60 hours)

Total evolution: ~200 hours over 12-18 months
This is EVOLUTION, not rearchitecture
```

**Rationale:**
- CouchDB gets 80% of value in 3% of time
- Validates product-market fit quickly
- Clear upgrade path if needed
- Avoid premature optimization

---

## Implementation Plan (Sprint 10.3)

### Estimated Effort: 9 hours

### Phase 1: CouchDB Server Deployment (2 hours)
1. Deploy CouchDB 3.x on Fly.io
2. Configure HTTPS, persistent volume
3. Set admin credentials
4. Test HTTP API access
5. Create backup script

### Phase 2: Setup Wizard Integration (2 hours)
1. Extend `brainplorp setup` command
2. Generate unique user credentials
3. Create user's CouchDB database via API
4. Generate LiveSync plugin config
5. Guide user through Obsidian plugin installation

### Phase 3: Server HTTP API Client (2 hours)
1. Python library for vault access from server
2. MVCC retry logic for concurrent writes
3. Integrate with email-to-inbox automation
4. Error handling and logging

### Phase 4: CouchDB Views for Analytics (1 hour)
1. Map/reduce views for batch queries
2. Daily notes by date range
3. Task completion statistics
4. Dashboard data aggregation

### Phase 5: Testing & Documentation (2 hours)
1. Multi-device sync testing (Mac, iPhone)
2. Conflict resolution scenarios
3. User guide (setup, usage, troubleshooting)
4. Developer guide (API, views, debugging)
5. Architecture documentation

---

## Key Architectural Decisions

### Decision 1: Pure CouchDB (No Hybrid)
**Rejected:** Git + CouchDB hybrid approach
**Reason:** Two sources of truth create sync divergence risk
**Impact:** Simplified architecture, single sync mechanism

### Decision 2: Database-Level User Isolation
**Choice:** One CouchDB database per user
**Alternative:** Shared database with document-level permissions
**Reason:** Simpler security model, CouchDB optimized for this
**Impact:** Easier to manage, clear permission boundaries

### Decision 3: Evolution over Custom Build
**Choice:** Start with CouchDB, evolve as needed
**Alternative:** Build custom sync protocol from scratch
**Reason:** 9 hours vs 280 hours, validates product first
**Impact:** Faster time-to-market, clear upgrade path

### Decision 4: Obsidian LiveSync Plugin
**Choice:** Use existing LiveSync plugin
**Alternative:** Build custom Obsidian plugin
**Reason:** Battle-tested, mobile support, 0 development time
**Impact:** Faster deployment, community support

---

## Questions Answered

### Q: "why is this [hybrid approach] superior to just couchDB?"
**A:** It's not. Hybrid approach adds complexity and sync risk. Pure CouchDB is superior.

### Q: "how will the couchDB server work for multiple file vaults from multiple users?"
**A:** One database per user (user-alice-vault, user-bob-vault). CouchDB enforces database-level permissions on every request.

### Q: "will it keep they private and secure to each user?"
**A:** Yes. Users get unique credentials, cannot access each other's databases. Server can access for automation (acceptable for 5-10 trusted users). E2E encryption in Sprint 11 eliminates server access.

### Q: "in the future if I wanted to expand it would I have to do a refactor/rearchitecture?"
**A:** No. Evolution path adds layers (E2E encryption, custom client, OAuth) without replacing CouchDB foundation. 60-90 hours over 12-18 months.

### Q: "how would we do it from the ground up if couchDB + livesync didn't exist?"
**A:** Event-sourced architecture with PostgreSQL + S3 + OT/CRDT. Technically superior but 280 hours vs 9 hours. Start with CouchDB, migrate only if justified.

---

## Success Criteria

### Sprint 10.3 Success Criteria:
- [ ] CouchDB server deployed on Fly.io with HTTPS
- [ ] `brainplorp setup` configures CouchDB + LiveSync
- [ ] User can edit daily note on Mac, see on iPhone within 5 seconds
- [ ] Server can append to inbox via HTTP API
- [ ] Email-to-inbox automation works with CouchDB
- [ ] Documentation complete (user guide, developer guide)

### Production Readiness (Future):
- [ ] E2E encryption enabled (Sprint 11)
- [ ] Custom sync client with selective sync (Sprint 12)
- [ ] OAuth authentication (Sprint 13)
- [ ] Multi-region replication (Sprint 14)
- [ ] 99.9% uptime monitoring (Sprint 15)

---

## Related Documentation

- **Sprint 10.3 Spec:** `Docs/sprints/SPRINT_10.3_VAULT_SYNC_SPEC.md` (1,295 lines)
- **Sprint 10.2 Spec:** TaskChampion sync server deployment (complete)
- **Sprint 10.1.1 Spec:** Installation hardening (75% complete)
- **CouchDB Documentation:** https://docs.couchdb.org/en/stable/
- **Obsidian LiveSync:** https://github.com/vrtmrz/obsidian-livesync

---

## Conversation History

**Date:** 2025-10-12
**Participants:** User (jsd), Claude PM Instance
**Duration:** Multiple hours
**Outcome:** Architectural decision finalized, Sprint 10.3 spec complete

**Key Turning Points:**
1. User challenged Git automation approach → Comprehensive comparison
2. User questioned hybrid approach → Rejected hybrid, simplified to pure CouchDB
3. User asked about production scalability → Evolution path documented
4. User requested ground-up comparison → Full custom protocol designed for reference

**Final User Statement:** "definitely going with your recommendation: Start with CouchDB+LiveSync"

---

## Appendix: Technical Details

### CouchDB MVCC Conflict Resolution

**How it works:**
1. Each document has `_rev` field (revision ID): `2-abc123`
2. Client reads document: `GET /db/daily-2025-10-12` → `_rev: 2-abc`
3. Client modifies, sends back with `_rev`: `PUT /db/daily-2025-10-12 {_rev: 2-abc, ...}`
4. CouchDB checks: Is `2-abc` still current?
   - YES: Accept update, generate `3-def`
   - NO: Reject with 409 Conflict
5. Client retries: Read latest `_rev`, reapply changes, submit again

**Conflict scenario:**
```
Timeline:
1. Mac reads daily note (_rev: 2-abc)
2. iPhone reads daily note (_rev: 2-abc)
3. Mac edits, saves → CouchDB accepts → _rev: 3-def
4. iPhone edits, saves with _rev: 2-abc → CouchDB rejects (409 Conflict)
5. iPhone reads latest (_rev: 3-def), merges changes, saves → _rev: 4-ghi
```

**LiveSync behavior:**
- LiveSync retries automatically on conflict
- User sees brief "Syncing..." indicator
- Conflicts rare (2-5 second sync window)

### Database Naming Convention

**Format:** `user-{username}-vault`

**Examples:**
- `user-jsd-vault` - User jsd's vault
- `user-alice-vault` - User alice's vault
- `user-bob-vault` - User bob's vault

**Permissions:**
```json
{
  "_id": "org.couchdb.user:jsd",
  "name": "jsd",
  "roles": [],
  "type": "user",
  "password": "hashed_password"
}
```

**Database security:**
```json
{
  "_id": "_security",
  "admins": {
    "names": ["admin"],
    "roles": []
  },
  "members": {
    "names": ["jsd"],
    "roles": []
  }
}
```

### Server HTTP API Examples

**Read daily note:**
```python
import requests

response = requests.get(
    'https://couchdb.fly.dev/user-jsd-vault/daily-2025-10-12',
    auth=('jsd', 'password')
)
doc = response.json()
content = doc['content']  # Markdown content
```

**Append to inbox:**
```python
# 1. Read current inbox
response = requests.get(
    'https://couchdb.fly.dev/user-jsd-vault/inbox-2025-10',
    auth=('jsd', 'password')
)
doc = response.json()

# 2. Append new item
doc['content'] += '\n- [ ] New inbox item'

# 3. Save with _rev (MVCC)
response = requests.put(
    'https://couchdb.fly.dev/user-jsd-vault/inbox-2025-10',
    json=doc,
    auth=('jsd', 'password')
)

# 4. Handle conflicts
if response.status_code == 409:
    # Retry: Read latest _rev, reapply changes
    pass
```

---

**END OF REFERENCE DOCUMENT**
