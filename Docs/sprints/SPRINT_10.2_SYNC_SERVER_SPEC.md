# Sprint 10.2: Cloud Sync Server for Multi-User Testing

**Version:** 0.1.0 (DRAFT)
**Status:** 🚧 DRAFT - In Discussion
**Sprint:** 10.2 (Minor sprint - Infrastructure for testing)
**Estimated Effort:** TBD
**Dependencies:** Sprint 10 (Multi-computer sync documented)
**Architecture:** TaskChampion sync server + Setup wizard enhancement
**Target Version:** brainplorp v1.6.2 or v1.7.0 (TBD)
**Date:** 2025-10-12

---

## Executive Summary

Sprint 10.2 deploys a shared TaskChampion sync server in the cloud and enhances the setup wizard to offer it as the default option for testers. This enables multiple testers to easily test brainplorp's multi-computer sync without setting up their own servers.

**Problem:**
- Sprint 10 documented multi-computer sync, but requires users to set up their own TaskChampion server
- Testers need to either self-host (complex) or skip sync testing (incomplete testing)
- No easy way to onboard multiple testers with minimal setup

**Solution:**
- Deploy single public TaskChampion sync server (e.g., `https://sync.brainplorp.com`)
- Update `brainplorp setup` wizard to offer cloud sync as default option
- Auto-generate client credentials (client ID + encryption secret)
- Multiple testers share same server, data isolated by client ID

**User Experience:**
```bash
# Tester runs setup wizard
$ brainplorp setup

Step 2: TaskWarrior Sync
  TaskChampion Server Options:
    1. brainplorp Cloud Sync (recommended for testing)  ← NEW
    2. Self-hosted (you run the server)
    3. Skip for now

  Choose option [1]: 1

  ✓ Sync configured!

  📋 IMPORTANT: Save these credentials for other computers:
     Client ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
     Secret: abc123def456...

  On your other Mac, run 'brainplorp setup' and enter these values.
```

**Benefits:**
- ✅ Testers get sync working in <2 minutes
- ✅ No server deployment knowledge required
- ✅ Multiple testers supported (10, 100, 1000+)
- ✅ Each tester has isolated, encrypted data
- ✅ Each tester can sync across N computers

---

## Problem Statement

### Current State (Sprint 10)

**Setup Wizard TaskWarrior Sync Options:**
```
Step 2: TaskWarrior Sync
  TaskChampion Server Options:
    1. Self-hosted (you run the server)
    2. Cloud-hosted (recommended for testing)  ← Not implemented
    3. Skip for now
```

**What happens if user chooses option 2:**
```python
elif choice == 2:
    # TODO: Provide default cloud server once we have one
    click.echo("  ℹ Cloud server setup will be available in next release")
    config['taskwarrior_sync'] = {'enabled': False}
```

**Result:** Testers skip sync or give up trying to self-host.

### Tester Pain Points

**Scenario: Tester wants to test multi-computer sync**

1. Reads `MULTI_COMPUTER_SETUP.md`
2. Sees "Deploy TaskChampion server" instructions
3. Options:
   - Self-host on VPS (requires server knowledge, costs money)
   - Use Docker locally (complex, only one computer)
   - Skip sync testing (incomplete test coverage)
4. Many testers choose option 3 (skip)

**Impact:**
- Multi-computer sync untested by most testers
- Can't identify sync-related bugs
- Reduces confidence in v1.6.0 release

### Multi-Tester Requirements

**Question from User:**
> "If I'm running a sync server in the cloud, can it serve multiple testers (each with their own data) and multiple computers for each of them?"

**Answer:** YES! TaskChampion sync server architecture:

```
TaskChampion Server (Cloud)
├── Client 1 (Alice's Laptop)
│   └── Data: Alice's tasks (isolated)
├── Client 2 (Alice's Desktop)
│   └── Data: Alice's tasks (same as Client 1)
├── Client 3 (Bob's Laptop)
│   └── Data: Bob's tasks (isolated from Alice)
└── Client 4 (Bob's Desktop)
    └── Data: Bob's tasks (same as Client 3)
```

**Key Concepts:**
- **Client ID** - Unique UUID per user (e.g., `a1b2c3d4-...`)
- **Encryption Secret** - Shared secret for end-to-end encryption
- **Data Isolation** - Server stores encrypted data per client ID
- **No User Accounts** - Authentication via client ID + secret

**Example:**

Alice (Tester 1):
```bash
# Laptop
task config sync.server.client_id "alice-uuid-123"
task config sync.encryption_secret "alice-secret-abc"

# Desktop (SAME credentials)
task config sync.server.client_id "alice-uuid-123"
task config sync.encryption_secret "alice-secret-abc"

# Result: Both computers sync Alice's tasks
```

Bob (Tester 2):
```bash
# Laptop
task config sync.server.client_id "bob-uuid-456"  # DIFFERENT
task config sync.encryption_secret "bob-secret-def"  # DIFFERENT

# Desktop (SAME as Bob's laptop)
task config sync.server.client_id "bob-uuid-456"
task config sync.encryption_secret "bob-secret-def"

# Result: Both of Bob's computers sync Bob's tasks (separate from Alice)
```

**Security:**
- Data encrypted on client before upload (end-to-end)
- Server never sees plaintext (only encrypted blobs)
- Alice can't decrypt Bob's data (different secrets)
- Collision probability: ~0% (128-bit UUIDs)

---

## Proposed Solution (High-Level)

### Architecture

**Single Public Server:**
```
https://sync.brainplorp.com
├── Port: 8080 (TaskChampion protocol)
├── Deployment: Fly.io / Railway / Docker on VPS
├── Storage: Persistent volume for encrypted task data
└── Access: Public (no authentication, security via encryption)
```

**Multiple Testers:**
```
Tester 1 (Alice)
├── Laptop: client_id=alice-123, secret=alice-abc
└── Desktop: client_id=alice-123, secret=alice-abc
    → Syncs Alice's tasks

Tester 2 (Bob)
├── Laptop: client_id=bob-456, secret=bob-def
└── Desktop: client_id=bob-456, secret=bob-def
    → Syncs Bob's tasks (isolated from Alice)
```

### Setup Wizard Enhancement

**Update `src/brainplorp/commands/setup.py`:**

```python
# Step 2: TaskWarrior Sync
click.echo("Step 2: TaskWarrior Sync")
click.echo("  TaskChampion Server Options:")
click.echo("    1. brainplorp Cloud Sync (recommended for testing)")
click.echo("    2. Self-hosted (you run the server)")
click.echo("    3. Skip for now")

choice = click.prompt("Choose option", type=click.IntRange(1, 3), default=1)

if choice == 1:
    # NEW: Use shared brainplorp sync server
    import uuid
    import secrets

    server_url = "https://sync.brainplorp.com"
    client_id = str(uuid.uuid4())
    encryption_secret = secrets.token_hex(32)

    # Configure TaskWarrior
    subprocess.run(['task', 'config', 'sync.server.url', server_url])
    subprocess.run(['task', 'config', 'sync.server.client_id', client_id])
    subprocess.run(['task', 'config', 'sync.encryption_secret', encryption_secret])

    # Save to brainplorp config for reference
    config['taskwarrior_sync'] = {
        'enabled': True,
        'server_url': server_url,
        'client_id': client_id,
        'encryption_secret': encryption_secret
    }

    click.echo()
    click.echo("  ✓ Sync configured!")
    click.echo()
    click.secho("  📋 IMPORTANT: Save these credentials for other computers:", fg='yellow', bold=True)
    click.echo(f"     Server: {server_url}")
    click.echo(f"     Client ID: {client_id}")
    click.echo(f"     Secret: {encryption_secret}")
    click.echo()
    click.echo("  On your other Mac, run 'brainplorp setup' and choose option 2 to enter these values.")
    click.echo()

elif choice == 2:
    # Self-hosted (existing functionality)
    config['taskwarrior_sync'] = {
        'enabled': True,
        'server_url': click.prompt("  Enter server URL")
    }
    # ... existing self-hosted setup ...
```

**Second Computer Setup:**

Need to add option to "use existing credentials":

```python
if choice == 1:
    # Cloud sync
    use_existing = click.confirm("  Do you have existing credentials from another computer?", default=False)

    if use_existing:
        server_url = click.prompt("  Server URL", default="https://sync.brainplorp.com")
        client_id = click.prompt("  Client ID")
        encryption_secret = click.prompt("  Encryption Secret", hide_input=True)
    else:
        # Generate new credentials (as above)
        server_url = "https://sync.brainplorp.com"
        client_id = str(uuid.uuid4())
        encryption_secret = secrets.token_hex(32)

    # Configure TaskWarrior (same for both cases)
    # ...
```

---

## Implementation Phases (DRAFT)

### Phase 1: Server Deployment (TBD hours)

**Options to evaluate:**

**Option A: Fly.io (Recommended)**
- Free tier: 3 shared-cpu-1x VMs
- Persistent volumes supported
- Easy deployment (`fly launch && fly deploy`)
- URL: `https://brainplorp-sync.fly.dev`

**Option B: Railway**
- Free tier available
- Persistent storage
- Simple deployment (`railway init && railway up`)
- URL: `https://brainplorp-sync.up.railway.app`

**Option C: Docker on VPS**
- Full control
- Requires VPS management
- More complex but most flexible

**Deployment Steps (Fly.io example):**
```bash
# 1. Install flyctl
curl -L https://fly.io/install.sh | sh

# 2. Create fly.toml
cat > fly.toml <<EOF
app = "brainplorp-sync"
primary_region = "sjc"  # San Jose (close to maintainer)

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = false
  auto_start_machines = false

[[vm]]
  size = "shared-cpu-1x"
  memory = "256mb"

[mounts]
  source = "taskchampion_data"
  destination = "/data"
EOF

# 3. Deploy
fly launch --no-deploy
fly volumes create taskchampion_data --size 1
fly deploy

# 4. Test
curl https://brainplorp-sync.fly.dev/health
```

**Questions to resolve:**
- Q1: Which platform has best free tier for our needs?
- Q2: What volume size needed for 100 testers? (estimate: 10MB per tester = 1GB)
- Q3: Should we use custom domain (sync.brainplorp.com) or platform subdomain?
- Q4: How to monitor server health?
- Q5: Rate limiting needed?

### Phase 2: Setup Wizard Enhancement (TBD hours)

**Update `src/brainplorp/commands/setup.py`:**
- Add cloud sync option (1)
- Auto-generate credentials
- Display credentials with copy instructions
- Add "existing credentials" flow for Computer 2

**New functions needed:**
```python
def generate_sync_credentials() -> dict:
    """Generate TaskChampion sync credentials."""
    import uuid
    import secrets
    return {
        'client_id': str(uuid.uuid4()),
        'encryption_secret': secrets.token_hex(32)
    }

def configure_taskwarrior_sync(server_url: str, client_id: str, secret: str):
    """Configure TaskWarrior sync settings."""
    subprocess.run(['task', 'config', 'sync.server.url', server_url])
    subprocess.run(['task', 'config', 'sync.server.client_id', client_id])
    subprocess.run(['task', 'config', 'sync.encryption_secret', secret])
```

**Questions to resolve:**
- Q6: Should we store credentials in brainplorp config.yaml for reference?
- Q7: How to handle case where TaskWarrior already configured with different sync?
- Q8: Should wizard offer to test sync connection immediately?
- Q9: What if server is down during setup?

### Phase 3: Documentation Updates (TBD hours)

**Update `Docs/MULTI_COMPUTER_SETUP.md`:**
- Add "Cloud Sync (Recommended)" section at top
- Move self-hosted to "Advanced" section
- Document credential sharing workflow

**Create `Docs/TESTER_GUIDE.md` section:**
- "Testing Multi-Computer Sync" with cloud server
- Step-by-step: Computer 1 setup → Computer 2 setup → verify sync
- Troubleshooting: server unreachable, credential typos, etc.

**Questions to resolve:**
- Q10: Should we document manual TaskWarrior config (without wizard)?
- Q11: What troubleshooting steps for common sync issues?

### Phase 4: Testing (TBD hours)

**Test scenarios:**
1. Single tester, 2 computers (basic sync)
2. Multiple testers, each with 2 computers (isolation)
3. Credential copy-paste (human error testing)
4. Server unreachable during setup
5. Sync after server downtime

**Questions to resolve:**
- Q12: How to test multi-tester isolation without actual testers?
- Q13: Should we test with 10+ dummy clients to verify server capacity?

---

## Open Questions

### Server Infrastructure

**Q1: Platform Selection**
- Which cloud platform? (Fly.io vs Railway vs VPS)
- Cost for 100+ testers?
- Reliability requirements?

**Q2: Domain & DNS**
- Use custom domain (`sync.brainplorp.com`) or platform subdomain?
- Need SSL certificate?
- DNS propagation considerations?

**Q3: Monitoring & Maintenance**
- How to monitor server health?
- Alerting if server goes down?
- Who maintains the server?

**Q4: Capacity Planning**
- How many testers expected?
- Storage requirements per tester? (estimate: 1-10 MB)
- Bandwidth requirements? (sync operations are small, ~KB per sync)

**Q5: Server Lifecycle**
- Is this temporary (testing only) or permanent?
- What happens after Sprint 10/11 testing complete?
- Migration plan if we need to change servers?

### Security & Privacy

**Q6: Data Privacy**
- Should we have terms of service?
- Data retention policy? (delete after N days of inactivity?)
- GDPR considerations? (data encrypted, server admin can't read)

**Q7: Abuse Prevention**
- Rate limiting needed?
- How to handle malicious clients?
- Can we ban client IDs if needed?

**Q8: Server Access**
- Should maintainer have SSH access?
- Logs and debugging - what's visible?
- Backup strategy?

### User Experience

**Q9: Credential Management**
- Should wizard save credentials to brainplorp config.yaml?
- How to help users retrieve lost credentials?
- QR code for credential sharing between computers?

**Q10: Setup Flow**
- Should wizard test sync connection after config?
- Auto-sync on first setup or require manual `task sync`?
- What if user already has TaskWarrior sync configured?

**Q11: Error Handling**
- Server unreachable during setup - fallback behavior?
- Invalid credentials - how to detect and fix?
- Sync conflicts - how to guide users?

### Development & Testing

**Q12: Testing Strategy**
- How to test multi-tester isolation locally?
- Load testing needed? (simulate 100 testers)
- Can we use staging server before production?

**Q13: Rollout Plan**
- Deploy server before or after wizard update?
- Beta test with 1-2 testers first?
- Announce to all testers when?

### Integration with Existing Sprints

**Q14: Version Number**
- Should this be v1.6.2 (PATCH - minor enhancement)?
- Or v1.7.0 (MINOR - new feature)?
- Depends on Sprint 10.1 success

**Q15: Sprint Dependencies**
- Block on Sprint 10.1 (wheel distribution)?
- Can implement in parallel?
- Testing dependencies?

---

## User Stories (DRAFT)

### Story 1: Easy Cloud Sync
**As a** tester
**I want** to enable multi-computer sync with 1 click
**So that** I can test sync without deploying a server

**Acceptance Criteria:**
- Choose "Cloud Sync" option in wizard
- Credentials auto-generated
- Sync works immediately
- Can copy credentials to second computer

### Story 2: Multi-Computer Setup
**As a** tester with 2 Macs
**I want** to enter sync credentials on second Mac
**So that** both computers sync my tasks

**Acceptance Criteria:**
- Run wizard on Computer 2
- Enter credentials from Computer 1
- Both computers sync successfully
- Task created on Computer 1 appears on Computer 2

### Story 3: Isolated Testing
**As a** project maintainer
**I want** multiple testers to use same server
**So that** I don't deploy N servers

**Acceptance Criteria:**
- 2+ testers use same server URL
- Each tester has different client ID
- Testers can't see each other's tasks
- No authentication/authorization needed

---

## Success Criteria (DRAFT)

- ✅ TaskChampion server deployed and accessible
- ✅ Setup wizard offers cloud sync as option 1
- ✅ Credentials auto-generated securely
- ✅ Tester can sync across 2 computers
- ✅ Multiple testers have isolated data
- ✅ Documentation updated
- ✅ Testing guide includes sync testing

---

## Technical Notes (From Q&A)

### TaskChampion Multi-User Architecture

**How it works:**
- Server stores data per-client-ID (UUID)
- Each client has unique client ID + encryption secret
- Data encrypted on client before upload (end-to-end)
- Server never sees plaintext
- No user accounts or authentication

**Same user, multiple computers:**
```
User A Computer 1: client_id=A, secret=X
User A Computer 2: client_id=A, secret=X  ← SAME
→ Both computers sync User A's data
```

**Different users:**
```
User A: client_id=A, secret=X
User B: client_id=B, secret=Y  ← DIFFERENT
→ Data isolated, no cross-user access
```

**Security model:**
- Encryption secret acts as password
- UUID client ID prevents guessing (~2^128 possibilities)
- Even if someone guesses client ID, need secret to decrypt
- Server admin can't read data (encrypted)

### Alternative Approaches Considered

**Option 1: Single Public Server (PROPOSED)**
- ✅ Simplest for testers
- ✅ One deployment for everyone
- ✅ Natural isolation via client IDs
- ⚠️ Single point of failure
- ⚠️ Can't revoke individual testers

**Option 2: Per-Tester Instances**
- ✅ Full isolation (separate servers)
- ✅ Can monitor per-tester
- ✅ Can shut down individual testers
- ❌ N server deployments
- ❌ More complex

**Option 3: No Cloud Server (Status Quo)**
- ✅ No infrastructure to maintain
- ❌ Testers can't test sync
- ❌ Incomplete test coverage

**Recommendation:** Start with Option 1, can add Option 2 later if needed.

---

## Next Steps (For PM/Lead Engineer Discussion)

1. **Decide on server platform** (Fly.io vs Railway vs VPS)
2. **Resolve open questions** (especially Q1-Q5)
3. **Estimate effort** for each phase
4. **Determine version number** (v1.6.2 vs v1.7.0)
5. **Plan rollout** (deploy server before wizard update?)
6. **Consider beta testing** with 1-2 testers first

---

## Version History

**v0.1.0 (2025-10-12):**
- Initial DRAFT created
- Based on user Q&A about multi-user sync
- Captured architecture discussion (TaskChampion isolation model)
- Listed 15 open questions for resolution
- Identified 4 implementation phases (high-level)
- Status: In discussion, not ready for implementation
