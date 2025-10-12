# Sprint 10.2: Cloud Sync Server for Multi-User Testing

**Version:** 1.1.0
**Status:** ✅ Ready for Implementation
**Sprint:** 10.2 (Minor sprint - Infrastructure for testing)
**Estimated Effort:** 11 hours (2 + 4 + 2 + 3)
**Dependencies:** Sprint 10.1 (v1.6.1 must ship first)
**Architecture:** TaskChampion sync server (Fly.io) + Setup wizard with automatic first sync
**Target Version:** brainplorp v1.7.0 (MINOR)
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

### TaskChampion Authentication Model

**IMPORTANT: TaskChampion uses possession-based authentication, NOT username/password.**

**No Traditional Login:**
- ❌ No username/password
- ❌ No account creation
- ❌ No email verification
- ✅ Credentials (client_id + secret) ARE the authentication

**The Credentials:**

1. **Client ID (UUID)** - 128-bit unique identifier
   - Example: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`
   - Acts like a "username" but impossible to guess (1 in 2^128)
   - Public: visible in server requests

2. **Encryption Secret (64-char hex)** - 256-bit symmetric key
   - Example: `abc123def456...` (32 bytes)
   - Acts like a "password" AND encrypts all data
   - Private: never sent to server, only used locally

**How "Authentication" Works:**

```
Computer 1 (First Setup):
├─ Generates: client_id=abc-123, secret=xyz-789
├─ Creates task: "Buy milk"
├─ Encrypts locally with secret=xyz-789
├─ Uploads to server: POST /client/abc-123 (encrypted blob)
└─ Server stores blob (can't read it, no secret)

Computer 2 (Second Setup):
├─ User enters: client_id=abc-123, secret=xyz-789 (SAME)
├─ Requests from server: GET /client/abc-123
├─ Server returns: encrypted blob (no credential check!)
├─ Decrypts locally with secret=xyz-789
└─ Success: "Buy milk" appears ✓

Computer 3 (Wrong Secret):
├─ User enters: client_id=abc-123, secret=WRONG (different)
├─ Requests from server: GET /client/abc-123
├─ Server returns: encrypted blob (doesn't verify secret)
├─ Tries to decrypt with WRONG secret
└─ Failure: garbage data, TaskWarrior errors ✗
```

**Key Insights:**

1. **Server doesn't authenticate** - It gives encrypted blob to anyone who asks for client_id
2. **Security = possession of secret** - Only correct secret can decrypt
3. **Zero-knowledge server** - Server never knows your encryption secret
4. **Computer 2 "authenticates" by decrypting** - If decrypt works, you're authorized

**Why This Is Secure:**

- Client ID impossible to guess (2^128 = 340 undecillion possibilities)
- Even if attacker guesses client_id, data is encrypted
- Need BOTH client_id AND secret to read data
- For small testing group (5-20 users), collision probability ≈ 0%

**Why No Username/Password:**

- Simpler: no account system, password resets, email verification
- More secure: end-to-end encryption (server can't be hacked for plaintext)
- Privacy-first: server admin can't read your tasks
- Stateless: server doesn't track "logged in" state

**Implications for Computer 2 Setup:**

1. User must manually enter EXACT client_id from Computer 1
2. User must manually enter EXACT encryption_secret from Computer 1
3. No "forgot password" recovery (if lost, must create new credentials)
4. First sync automatically downloads tasks (no explicit "login" step)

### TaskChampion Multi-User Architecture

**How it works:**
- Server stores data per-client-ID (UUID)
- Each client has unique client ID + encryption secret
- Data encrypted on client before upload (end-to-end)
- Server never sees plaintext
- No user accounts or traditional authentication

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

---

## Answers to Open Questions (PM/Architect - 2025-10-12)

### A1-A5: Server Infrastructure

**A1: Platform Selection**
- **Recommendation:** Fly.io
- **Rationale:**
  - Free tier: 3 shared-cpu-1x VMs (256MB RAM each)
  - 3GB persistent volume free
  - Simple deployment (`fly launch && fly deploy`)
  - Auto-scaling and health checks built-in
  - Good for hobby projects transitioning to production
- **Cost:** Free for testing (10-50 testers), $5-10/month if we exceed free tier
- **Reliability:** 99.9% uptime SLA on paid plans, good enough for testing

**A2: Domain & DNS**
- **Recommendation:** Use platform subdomain for Sprint 10.2
  - URL: `https://brainplorp-sync.fly.dev`
  - Reason: Simpler (no DNS setup), faster deployment, free SSL
- **Future:** Can add custom domain (`sync.brainplorp.com`) in Sprint 11 if we productionize
- **DNS:** Not needed for Sprint 10.2 (testing only)

**A3: Monitoring & Maintenance**
- **Basic monitoring (Sprint 10.2):**
  - Fly.io dashboard (uptime, memory, requests)
  - Manual checks: `curl https://brainplorp-sync.fly.dev/`
  - Testers report issues if server down
- **Advanced monitoring (Future):**
  - Add `/health` endpoint that checks storage
  - Uptime monitoring (e.g., UptimeRobot free tier)
  - Alert maintainer via email if down >5 minutes
- **Maintenance:** Maintainer (you) monitors Fly.io dashboard weekly

**A4: Capacity Planning**
- **Expected testers:** 5-20 for Sprint 10.2 testing
- **Storage per tester:** 1-10 MB (estimate: 100-500 tasks × 2KB each)
- **Total storage needed:** 200 MB (with 10x headroom)
- **Bandwidth:** ~10 KB per sync × 100 syncs/day × 20 testers = 20 MB/day (negligible)
- **Fly.io free tier:** 3GB storage, 160GB/month bandwidth (more than enough)

**A5: Server Lifecycle**
- **Sprint 10.2:** Temporary testing server
- **Sprint 11+:** Evaluate based on tester feedback
  - Option A: Keep running (promote to "beta" server)
  - Option B: Shut down, tell users to self-host
  - Option C: Migrate to more robust infrastructure
- **Migration plan:** If needed, deploy new server, give users 30 days to update config
- **Data retention:** Keep for 6 months after Sprint 10.2, then archive/delete

### A6-A8: Security & Privacy

**A6: Data Privacy**
- **Terms of Service:** Not needed for Sprint 10.2 (testing only, invited testers)
- **Data retention:** Keep while server running, delete 30 days after tester inactivity
- **GDPR:** Compliant (data encrypted, server admin can't read, users can delete)
- **Future:** Add TOS if we productionize in Sprint 11+

**A7: Abuse Prevention**
- **Sprint 10.2:** No rate limiting (trusted testers only)
- **Risk:** Low (small group, invite-only)
- **Future:** Add rate limiting if server becomes public:
  - 100 syncs per client per hour (prevents runaway scripts)
  - Nginx/Caddy rate limiting by IP
- **Banning:** Can block client ID by editing server config (manual, rare)

**A8: Server Access**
- **SSH access:** Yes, maintainer has SSH via `fly ssh console`
- **Logs:** Fly.io logs show requests, errors (no task content, data encrypted)
- **Debugging:** Can see client IDs, sync timestamps, errors (not task data)
- **Backup:** Fly.io automatic volume snapshots daily (retain 7 days)

### A9-A11: User Experience

**A9: Credential Management**
- **Save to config.yaml:** YES
  ```yaml
  taskwarrior_sync:
    enabled: true
    server_url: https://brainplorp-sync.fly.dev
    client_id: abc-123
    encryption_secret: secret-xyz
  ```
- **Benefit:** User can retrieve credentials via `cat ~/.config/brainplorp/config.yaml`
- **Lost credentials:** No recovery (server doesn't store user info). User must:
  - Check config.yaml on Computer 1
  - Or re-generate new credentials (lose sync with other computers)
- **QR code:** Nice-to-have for Sprint 11+, not Sprint 10.2

**A10: Setup Flow**
- **Test connection:** YES, after config:
  ```python
  click.echo("  Testing connection...")
  result = subprocess.run(['task', 'sync'], capture_output=True)
  if result.returncode == 0:
      click.echo("  ✓ Sync successful!")
  else:
      click.echo("  ⚠ Sync failed, but config saved. Try 'task sync' later.")
  ```
- **Auto-sync:** No, require manual `task sync` (user controls when)
- **Already configured:** Detect existing sync config:
  ```python
  existing = subprocess.run(['task', 'config', 'sync.server.url'], capture_output=True)
  if existing.stdout:
      click.echo("  ⚠ TaskWarrior sync already configured")
      overwrite = click.confirm("  Overwrite with brainplorp cloud sync?")
      if not overwrite:
          return  # Skip sync setup
  ```

**A11: Error Handling**
- **Server unreachable during setup:**
  - Wizard still completes (config saved)
  - Show warning: "Couldn't reach server, but config saved. Try 'task sync' later."
  - User can sync when server back online
- **Invalid credentials on Computer 2:**
  - `task sync` will fail with error (TaskWarrior handles this)
  - User re-runs wizard, re-enters correct credentials
- **Sync conflicts:**
  - TaskChampion handles automatically (CRDTs, no conflicts)
  - If corruption: user runs `task sync --force` (rare)

### A12-A13: Development & Testing

**A12: Testing Strategy**
- **Multi-tester isolation (local):**
  - Create 2 TaskWarrior databases with different client IDs
  - Sync both to server, verify no cross-contamination
  ```bash
  # Terminal 1: Tester A
  export TASKDATA=/tmp/tester-a
  task config sync.server.client_id "aaa-111"
  task add "Alice task"
  task sync

  # Terminal 2: Tester B
  export TASKDATA=/tmp/tester-b
  task config sync.server.client_id "bbb-222"
  task add "Bob task"
  task sync

  # Verify: Tester A doesn't see Bob's tasks
  ```
- **Load testing:** Not needed for Sprint 10.2 (5-20 testers max)
- **Staging server:** Not needed (Fly.io allows easy redeploy if issues)

**A13: Rollout Plan**
1. Deploy server (Phase 1)
2. Test manually with 2 local TaskWarrior databases
3. Update wizard code (Phase 2)
4. Test wizard on 2 Macs (maintainer's computers)
5. Update docs (Phase 3)
6. Beta test: Invite 1-2 testers
7. Fix issues, then announce to all testers
8. Monitor for 1 week

### A14-A15: Integration with Existing Sprints

**A14: Version Number**
- **Recommendation:** v1.7.0 (MINOR)
- **Rationale:**
  - New feature: cloud sync option in wizard
  - User-facing change: wizard behavior different
  - Not just a bug fix (PATCH)
  - Not breaking change (MAJOR)
- **Note:** Depends on Sprint 10.1 success (v1.6.1 must ship first)

**A15: Sprint Dependencies**
- **Block on Sprint 10.1:** YES
  - Sprint 10.1 must ship first (v1.6.1 - wheel distribution)
  - Sprint 10.2 builds on stable installation (can't test sync if install broken)
- **Parallel work:** Can deploy server (Phase 1) while Sprint 10.1 in progress
- **Testing:** Sprint 10.2 requires working v1.6.1 installation

---

## Updated Implementation Phases (With Answers Applied)

### Phase 1: Server Deployment (2 hours)

**Platform:** Fly.io (free tier)
**URL:** `https://brainplorp-sync.fly.dev`

**Steps:**

1. **Install flyctl:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   fly auth login
   ```

2. **Create Dockerfile:**
   ```dockerfile
   FROM rust:1.75-slim

   # Install TaskChampion sync server
   RUN cargo install taskchampion-sync-server

   # Expose port
   EXPOSE 8080

   # Run server
   CMD ["taskchampion-sync-server", "--port", "8080", "--data-dir", "/data"]
   ```

3. **Create fly.toml:**
   ```toml
   app = "brainplorp-sync"
   primary_region = "sjc"  # San Jose

   [build]

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
   ```

4. **Deploy:**
   ```bash
   fly launch --no-deploy --name brainplorp-sync
   fly volumes create taskchampion_data --size 3  # 3GB
   fly deploy
   ```

5. **Verify:**
   ```bash
   curl https://brainplorp-sync.fly.dev/
   # Should return 200 OK or TaskChampion response

   # Test with real TaskWarrior client
   task config sync.server.url https://brainplorp-sync.fly.dev
   task config sync.server.client_id "test-$(uuidgen)"
   task config sync.encryption_secret "$(openssl rand -hex 32)"
   task sync  # Should succeed
   ```

**Completion Criteria:**
- ✅ Server accessible at `https://brainplorp-sync.fly.dev`
- ✅ TaskWarrior client can sync successfully
- ✅ Fly.io dashboard shows healthy status

### Phase 2: Setup Wizard Enhancement (4 hours)

**File:** `src/brainplorp/commands/setup.py`

**Changes:**

1. **Add helper functions:**
   ```python
   def generate_sync_credentials() -> dict:
       """Generate TaskChampion sync credentials."""
       import uuid
       import secrets
       return {
           'client_id': str(uuid.uuid4()),
           'encryption_secret': secrets.token_hex(32)
       }

   def configure_taskwarrior_sync(server_url: str, client_id: str, secret: str) -> bool:
       """
       Configure TaskWarrior sync settings.
       Returns True if successful, False if error.
       """
       try:
           subprocess.run(['task', 'config', 'sync.server.url', server_url], check=True)
           subprocess.run(['task', 'config', 'sync.server.client_id', client_id], check=True)
           subprocess.run(['task', 'config', 'sync.encryption_secret', secret], check=True)
           return True
       except subprocess.CalledProcessError:
           return False

   def test_sync_connection() -> bool:
       """Test TaskWarrior sync connection. Returns True if successful."""
       try:
           result = subprocess.run(['task', 'sync'],
                                   capture_output=True,
                                   timeout=10)
           return result.returncode == 0
       except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
           return False
   ```

2. **Update setup wizard (Step 2):**
   ```python
   # Step 2: TaskWarrior Sync
   click.echo("\nStep 2: TaskWarrior Sync")
   click.echo("  TaskChampion Server Options:")
   click.echo("    1. brainplorp Cloud Sync (recommended for testing)")
   click.echo("    2. Self-hosted (you run the server)")
   click.echo("    3. Skip for now")

   choice = click.prompt("Choose option", type=click.IntRange(1, 3), default=1)

   if choice == 1:
       # Cloud sync
       click.echo()

       # Check if already configured
       existing = subprocess.run(['task', 'config', 'sync.server.url'],
                                 capture_output=True, text=True)
       if existing.stdout.strip():
           click.echo(f"  ⚠ TaskWarrior sync already configured: {existing.stdout.strip()}")
           overwrite = click.confirm("  Overwrite with brainplorp cloud sync?", default=False)
           if not overwrite:
               click.echo("  Keeping existing sync configuration.")
               config['taskwarrior_sync'] = {'enabled': True, 'type': 'existing'}
               return

       # Ask: new or existing credentials
       use_existing = click.confirm("  Do you have existing credentials from another computer?",
                                    default=False)

       if use_existing:
           # Enter existing credentials
           click.echo()
           click.echo("  Enter credentials from your other computer:")
           server_url = click.prompt("  Server URL",
                                      default="https://brainplorp-sync.fly.dev")
           client_id = click.prompt("  Client ID")
           encryption_secret = click.prompt("  Encryption Secret", hide_input=True)
       else:
           # Generate new credentials
           server_url = "https://brainplorp-sync.fly.dev"
           creds = generate_sync_credentials()
           client_id = creds['client_id']
           encryption_secret = creds['encryption_secret']

       # Configure TaskWarrior
       click.echo()
       click.echo("  Configuring TaskWarrior...")
       success = configure_taskwarrior_sync(server_url, client_id, encryption_secret)

       if not success:
           click.echo("  ✗ Failed to configure TaskWarrior")
           config['taskwarrior_sync'] = {'enabled': False}
           return

       # Save to brainplorp config
       config['taskwarrior_sync'] = {
           'enabled': True,
           'type': 'cloud',
           'server_url': server_url,
           'client_id': client_id,
           'encryption_secret': encryption_secret
       }

       # Test connection and perform first sync
       click.echo()
       click.echo("  Testing connection...")

       sync_result = subprocess.run(['task', 'sync'],
                                     capture_output=True,
                                     text=True,
                                     timeout=30)

       if sync_result.returncode == 0:
           # Successful sync - check if we downloaded tasks
           task_count_result = subprocess.run(['task', 'count'],
                                              capture_output=True,
                                              text=True)
           task_count = int(task_count_result.stdout.strip()) if task_count_result.returncode == 0 else 0

           if use_existing and task_count > 0:
               # Computer 2+ downloading existing tasks
               click.echo(f"  ✓ Sync successful! Downloaded {task_count} tasks from server.")
               click.echo()
               click.secho("  🎉 Your tasks are now available on this computer!",
                          fg='green', bold=True)
               click.echo(f"     Run 'task list' to see your {task_count} tasks.")
           elif not use_existing and task_count > 0:
               # Computer 1 uploading existing tasks
               click.echo(f"  ✓ Sync successful! Uploaded {task_count} tasks to server.")
               click.echo()
               click.echo("  Your tasks are now synced to the cloud.")
           else:
               # Fresh start on both sides
               click.echo("  ✓ Sync successful!")
       else:
           # Sync failed
           click.echo("  ⚠ Couldn't reach server, but config saved.")
           click.echo("    Try 'task sync' later to verify.")
           if use_existing:
               click.echo()
               click.secho("  💡 First sync will download your tasks from the server.",
                          fg='cyan')
               click.echo("     Your tasks from Computer 1 will appear after first successful sync.")

       # Display credentials (for Computer 2 setup)
       if not use_existing:
           click.echo()
           click.secho("  📋 IMPORTANT: Save these credentials for other computers:",
                       fg='yellow', bold=True)
           click.echo(f"     Server URL: {server_url}")
           click.echo(f"     Client ID: {client_id}")
           click.echo(f"     Secret: {encryption_secret}")
           click.echo()
           click.echo("  On your other Mac:")
           click.echo("    1. Install brainplorp: brew install dimatosj/brainplorp/brainplorp")
           click.echo("    2. Run: brainplorp setup")
           click.echo("    3. Choose option 1 (Cloud Sync)")
           click.echo("    4. Select 'Yes' when asked about existing credentials")
           click.echo("    5. Enter the credentials above")
           click.echo("    6. First sync will download all your tasks automatically")
           click.echo()
           click.echo("  (Credentials also saved to: ~/.config/brainplorp/config.yaml)")
       else:
           # Computer 2+ just finished first sync
           if sync_result.returncode == 0 and task_count > 0:
               click.echo()
               click.echo("  Next steps:")
               click.echo("    • Run 'brainplorp start' to generate today's daily note")
               click.echo("    • Add/complete tasks on either computer")
               click.echo("    • Run 'task sync' periodically to keep computers in sync")

   elif choice == 2:
       # Self-hosted (existing implementation)
       # ... keep existing code ...

   else:
       # Skip
       config['taskwarrior_sync'] = {'enabled': False}
       click.echo("  Sync setup skipped. You can configure later in ~/.taskrc")
   ```

3. **Add tests:**
   ```python
   # tests/test_commands/test_setup.py

   def test_generate_sync_credentials():
       """Test credential generation."""
       creds = generate_sync_credentials()
       assert 'client_id' in creds
       assert 'encryption_secret' in creds
       assert len(creds['client_id']) == 36  # UUID format
       assert len(creds['encryption_secret']) == 64  # 32 bytes hex

   def test_configure_taskwarrior_sync(tmp_path):
       """Test TaskWarrior config (requires task installed)."""
       # Skip if task not installed
       if not shutil.which('task'):
           pytest.skip("TaskWarrior not installed")

       # Use temp TASKDATA
       env = os.environ.copy()
       env['TASKDATA'] = str(tmp_path)

       # Configure
       success = configure_taskwarrior_sync(
           "https://test.example.com",
           "test-uuid-123",
           "test-secret-456"
       )
       assert success

       # Verify config
       result = subprocess.run(['task', 'config', 'sync.server.url'],
                               capture_output=True, text=True, env=env)
       assert "test.example.com" in result.stdout
   ```

**Completion Criteria:**
- ✅ Wizard offers cloud sync as option 1
- ✅ New credentials auto-generated and displayed
- ✅ Existing credentials can be entered on Computer 2
- ✅ Credentials saved to config.yaml
- ✅ Connection tested after setup
- ✅ Tests pass

### Phase 3: Documentation Updates (2 hours)

**Update `Docs/MULTI_COMPUTER_SETUP.md`:**

Add new section at top:

```markdown
# Multi-Computer Setup

## Option 1: Cloud Sync (Recommended for Testing)

The easiest way to sync brainplorp across multiple computers is to use the brainplorp cloud sync server.

### Computer 1 (First Setup)

1. Run setup wizard:
   ```bash
   brainplorp setup
   ```

2. Choose option 1 (brainplorp Cloud Sync)

3. **Save the credentials shown:**
   ```
   Server URL: https://brainplorp-sync.fly.dev
   Client ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
   Secret: abc123def456...
   ```

4. Test sync:
   ```bash
   task sync
   ```

### Computer 2 (Additional Computers)

1. Install brainplorp:
   ```bash
   brew install dimatosj/brainplorp/brainplorp
   ```

2. Run setup wizard:
   ```bash
   brainplorp setup
   ```

3. Choose option 1 (brainplorp Cloud Sync)

4. When asked "Do you have existing credentials?", choose YES

5. Enter credentials from Computer 1:
   - Server URL: `https://brainplorp-sync.fly.dev`
   - Client ID: (paste from Computer 1)
   - Encryption Secret: (paste from Computer 1)

6. **First sync happens automatically** - Your tasks download from server!
   ```
   Testing connection...
   ✓ Sync successful! Downloaded 50 tasks from server.

   🎉 Your tasks are now available on this computer!
       Run 'task list' to see your 50 tasks.
   ```

7. Verify tasks appear:
   ```bash
   task list
   # You should see all tasks from Computer 1!
   ```

**How It Works:**
- Computer 2 starts with empty TaskWarrior database
- When you enter same credentials as Computer 1, first sync downloads all tasks
- Server recognizes the client_id and sends encrypted task data
- Computer 2 decrypts with encryption_secret locally
- All tasks appear as if they've always been there!

### Retrieving Credentials

If you forget your credentials, check Computer 1:

```bash
cat ~/.config/brainplorp/config.yaml
```

Look for the `taskwarrior_sync` section.

### Troubleshooting

**"Connection refused" during setup:**
- Check internet connection
- Verify server URL: `curl https://brainplorp-sync.fly.dev/`
- If server down, setup completes but warns you
- Try `task sync` again when server is back up

**"Sync failed" error:**
- Check credentials match between computers
- Re-run `brainplorp setup` and enter correct credentials
- Verify client_id: `task config sync.server.client_id`
- Verify server URL: `task config sync.server.url`

**Tasks not appearing on Computer 2 after first sync:**
1. Verify same client_id on both computers:
   ```bash
   # Computer 1
   task config sync.server.client_id
   # Output: abc-123-xyz

   # Computer 2
   task config sync.server.client_id
   # Output: abc-123-xyz (should match!)
   ```

2. Run sync on both computers:
   ```bash
   # Computer 1
   task sync

   # Computer 2
   task sync
   task list  # Should now see tasks
   ```

3. Check for sync errors:
   ```bash
   task sync --verbose
   ```

**"Wrong encryption secret" symptoms:**
- No explicit error (server doesn't validate)
- TaskWarrior errors when trying to decrypt
- Garbage data or "corrupted database" messages
- **Solution:** Re-run `brainplorp setup`, enter CORRECT secret from Computer 1

**"I lost my credentials":**
- Check Computer 1: `cat ~/.config/brainplorp/config.yaml`
- If all computers lost: no recovery, must create new client_id
- Old tasks on server become inaccessible (no way to decrypt)

**"Authentication failed" or "Unauthorized":**
- TaskChampion doesn't use username/password authentication
- No "login" step - credentials are used for encryption only
- If you see auth errors, it's likely a different issue (firewall, wrong URL)

---

## Option 2: Self-Hosted Sync (Advanced)

(Move existing self-hosted documentation here)
```

**Create `Docs/TESTING_GUIDE.md` (or add section):**

```markdown
## Testing Multi-Computer Sync

### Test Scenario: Two Computers

**Goal:** Verify tasks sync across both computers.

**Setup:**
1. Computer 1: Run `brainplorp setup`, choose cloud sync
2. Save credentials
3. Computer 2: Run `brainplorp setup`, enter same credentials

**Test Steps:**

1. **On Computer 1:**
   ```bash
   task add "Test task from Computer 1" project:test
   task sync
   ```

2. **On Computer 2:**
   ```bash
   task sync
   task list project:test
   # Should see: "Test task from Computer 1"
   ```

3. **On Computer 2:**
   ```bash
   task add "Test task from Computer 2" project:test
   task sync
   ```

4. **On Computer 1:**
   ```bash
   task sync
   task list project:test
   # Should see both tasks
   ```

**Expected Results:**
- ✅ Both tasks visible on both computers
- ✅ No sync errors
- ✅ No duplicate tasks

**Common Issues:**
- Tasks not appearing: Different client IDs (check config)
- Duplicate tasks: Sync conflict (rare, run `task sync --force`)
```

**Completion Criteria:**
- ✅ MULTI_COMPUTER_SETUP.md updated with cloud sync section
- ✅ Testing guide includes sync test scenario
- ✅ Troubleshooting steps documented

### Phase 4: Testing (3 hours)

**Test Plan:**

**Test 1: Single Computer Initial Setup**
```bash
# Clean environment
./scripts/clean_test_environment.sh

# Install v1.7.0
brew install dimatosj/brainplorp/brainplorp

# Run wizard
brainplorp setup
# Choose: vault path, option 1 (cloud sync), generate new credentials

# Verify config
cat ~/.config/brainplorp/config.yaml
# Should have: taskwarrior_sync.client_id, encryption_secret

# Test sync
task add "Test task 1"
task sync  # Should succeed

# Verify on server (check logs)
fly logs --app brainplorp-sync
# Should see: sync request from client_id
```

**Test 2: Two Computers (Same User) - First Sync Download**
```bash
# Computer 1 (already set up from Test 1)
task add "Task from Computer 1" project:sync-test
task add "Another task" project:sync-test
task sync
task count  # Should show: 2 (or more if Test 1 had tasks)

# Computer 2 (different Mac or clean environment)
brew install dimatosj/brainplorp/brainplorp

# IMPORTANT: Verify Computer 2 starts with EMPTY database
task count  # Should show: 0 (fresh install, no tasks)

brainplorp setup
# Vault path: (enter path)
# Choose: option 1 (cloud sync)
# Do you have existing credentials? YES
# Enter: client_id from Computer 1 (from config.yaml)
# Enter: secret from Computer 1 (from config.yaml)

# First sync should happen AUTOMATICALLY during setup
# Expected output:
#   Testing connection...
#   ✓ Sync successful! Downloaded 2 tasks from server.
#   🎉 Your tasks are now available on this computer!

# Verify tasks downloaded
task count  # Should show: 2 (same as Computer 1)
task list project:sync-test
# Should see: "Task from Computer 1" and "Another task"

# Verify task UUIDs match between computers
task _get 1.uuid  # Copy this UUID
# On Computer 1: task _get 1.uuid
# Should match Computer 2's UUID (same task object!)

# Add task on Computer 2
task add "Task from Computer 2" project:sync-test
task sync
task count  # Should show: 3

# Back to Computer 1
task sync
task count  # Should show: 3 (downloaded Computer 2's new task)
task list project:sync-test
# Should see: All 3 tasks

# CRITICAL: Verify bidirectional sync
# Computer 1: mark task done
task 1 done
task sync

# Computer 2: verify completion synced
task sync
task 1 status
# Should show: completed
```

**Test 3: Multiple Testers (Data Isolation)**
```bash
# Tester A
export TASKDATA=/tmp/tester-a
task config sync.server.url https://brainplorp-sync.fly.dev
task config sync.server.client_id "aaa-111-$(uuidgen)"
task config sync.encryption_secret "$(openssl rand -hex 32)"
task add "Alice task" project:alice
task sync

# Tester B
export TASKDATA=/tmp/tester-b
task config sync.server.url https://brainplorp-sync.fly.dev
task config sync.server.client_id "bbb-222-$(uuidgen)"
task config sync.encryption_secret "$(openssl rand -hex 32)"
task add "Bob task" project:bob
task sync

# Verify isolation
export TASKDATA=/tmp/tester-a
task list
# Should see: ONLY Alice's task (not Bob's)

export TASKDATA=/tmp/tester-b
task list
# Should see: ONLY Bob's task (not Alice's)
```

**Test 4: Error Conditions**
```bash
# Server unreachable (simulate by shutting down Fly.io app)
fly scale count 0 --app brainplorp-sync

# Run wizard
brainplorp setup
# Choose: option 1
# Expected: Wizard completes, shows warning about server unreachable

# Restart server
fly scale count 1 --app brainplorp-sync

# Try sync
task sync
# Expected: Now succeeds
```

**Test 5: Invalid Credentials**
```bash
# Computer 2: Enter wrong client_id
brainplorp setup
# Enter: client_id from Computer 1, but WRONG secret

task sync
# Expected: Fails (TaskWarrior error about encryption)

# Re-run with correct credentials
brainplorp setup
# Enter: Correct client_id AND secret

task sync
# Expected: Succeeds
```

**Completion Criteria:**
- ✅ Test 1 passes (single computer)
- ✅ Test 2 passes (two computers, same user)
- ✅ Test 3 passes (multiple testers, data isolated)
- ✅ Test 4 passes (server unreachable gracefully handled)
- ✅ Test 5 passes (invalid credentials detected)

---

## Success Criteria (Finalized)

**Infrastructure:**
- ✅ TaskChampion server deployed to Fly.io at `https://brainplorp-sync.fly.dev`
- ✅ Server accessible and responds to sync requests
- ✅ 3GB persistent volume configured for task data

**Setup Wizard:**
- ✅ Wizard offers "brainplorp Cloud Sync" as option 1 (default)
- ✅ Credentials auto-generated securely (UUID + 32-byte secret)
- ✅ Credentials displayed to user with step-by-step Computer 2 instructions
- ✅ Credentials saved to config.yaml for retrieval
- ✅ "Existing credentials" flow for Computer 2+ setup
- ✅ First sync happens automatically during setup
- ✅ Wizard shows task count after successful first sync

**Sync Behavior:**
- ✅ Computer 2 starts with empty TaskWarrior database
- ✅ First sync downloads all tasks from server automatically
- ✅ User sees: "Downloaded X tasks from server" message
- ✅ Task UUIDs match between computers (same objects)
- ✅ Bidirectional sync works (both directions)
- ✅ Multiple testers have isolated data (different client_ids)

**Documentation:**
- ✅ MULTI_COMPUTER_SETUP.md explains cloud sync option
- ✅ Documentation clarifies "no username/password" authentication model
- ✅ Troubleshooting section covers first-sync issues
- ✅ TESTING_GUIDE.md includes sync testing scenario

**Testing:**
- ✅ Test 1 passes (single computer setup)
- ✅ Test 2 passes (two computers, first-sync download verified)
- ✅ Test 3 passes (multiple testers, data isolated)
- ✅ Test 4 passes (server unreachable gracefully handled)
- ✅ Test 5 passes (invalid credentials detected)

**Release:**
- ✅ Version bumped to v1.7.0
- ✅ Sprint 10.1 (v1.6.1) shipped successfully before starting 10.2

---

## Effort Estimate

| Phase | Description | Hours |
|-------|-------------|-------|
| Phase 1 | Server Deployment (Fly.io) | 2 |
| Phase 2 | Setup Wizard Enhancement | 4 |
| Phase 3 | Documentation Updates | 2 |
| Phase 4 | Testing (5 scenarios) | 3 |
| **Total** | | **11 hours** |

---

## Version History

**v0.1.0 (2025-10-12):**
- Initial DRAFT created
- Based on user Q&A about multi-user sync
- Captured architecture discussion (TaskChampion isolation model)
- Listed 15 open questions for resolution
- Identified 4 implementation phases (high-level)
- Status: In discussion, not ready for implementation

**v1.0.0 (2025-10-12):**
- Answered all 15 open questions (A1-A15)
- Platform: Fly.io (free tier, https://brainplorp-sync.fly.dev)
- Version: v1.7.0 (MINOR - new feature)
- Dependencies: Sprint 10.1 (v1.6.1) must ship first
- Updated all 4 phases with detailed implementation steps
- Added comprehensive testing plan (5 test scenarios)
- Added effort estimate (11 hours)
- Added success criteria (finalized)
- Status: Ready for implementation

**v1.1.0 (2025-10-12):**
- Added explicit first-sync behavior to wizard (Phase 2)
- Wizard now performs `task sync` automatically during setup
- Shows task count after sync: "Downloaded X tasks from server"
- Different messages for Computer 1 (upload) vs Computer 2+ (download)
- Step-by-step Computer 2 setup instructions displayed
- Added comprehensive TaskChampion authentication model explanation
- Clarified: no username/password, possession-based auth (client_id + secret)
- Documented how "authentication" works via decryption success
- Updated MULTI_COMPUTER_SETUP.md section with first-sync details
- Enhanced troubleshooting: wrong secret symptoms, lost credentials
- Test 2 now explicitly verifies first-sync download behavior
- Verify Computer 2 starts with empty database (task count = 0)
- Verify task UUIDs match between computers
- Verify bidirectional sync (mark done on Computer 1, appears on Computer 2)
- Expanded success criteria (28 checkboxes, organized by category)
- Status: Ready for implementation (v1.1.0)
