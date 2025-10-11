## Success Criteria (Overall Sprint)

### Functional Requirements

1. **Installation**
   - ✅ User can install via `brew install brainplorp`
   - ✅ Installation completes in < 2 minutes
   - ✅ TaskWarrior installed as dependency

2. **Setup**
   - ✅ `brainplorp setup` wizard runs successfully
   - ✅ Wizard detects Obsidian vault in iCloud
   - ✅ Config file created and validated
   - ✅ MCP configuration automated (if Claude Desktop present)
   - ✅ Setup takes < 5 minutes for non-technical user

3. **Multi-Computer Sync**
   - ✅ Task created on Computer 1 → synced to Computer 2 (via TaskChampion)
   - ✅ Note created on Computer 1 → synced to Computer 2 (via iCloud)
   - ✅ Both computers can run `brainplorp start` with consistent results

4. **Documentation**
   - ✅ MULTI_COMPUTER_SETUP.md covers all setup scenarios
   - ✅ TESTER_GUIDE.md is beginner-friendly
   - ✅ Troubleshooting guide addresses common issues

5. **Backend Abstraction**
   - ✅ Backend protocols defined
   - ✅ Local backends fully implemented
   - ✅ Core modules refactored to use backends
   - ✅ Zero behavior change for users

### Testing Requirements

1. **Fresh Install Test** (on clean Mac)
   - ✅ `brew install brainplorp` succeeds
   - ✅ `brainplorp setup` completes without errors
   - ✅ `brainplorp start` creates daily note
   - ✅ `brainplorp tasks` lists tasks

2. **Multi-Computer Test** (2 Macs)
   - ✅ Install on both computers
   - ✅ Create task on Computer 1 → appears on Computer 2
   - ✅ Create note on Computer 1 → appears on Computer 2
   - ✅ Run `brainplorp start` on both → same daily note

3. **Tester Validation** (1-2 non-technical users)
   - ✅ Follow TESTER_GUIDE.md exactly
   - ✅ Report installation friction points
   - ✅ Confirm all commands work

4. **Regression Tests**
   - ✅ All 526 existing tests pass
   - ✅ No breaking changes to MCP tools
   - ✅ CLI commands work as before

### Version Management

- ✅ Version bumped to 1.6.0 in `__init__.py` and `pyproject.toml`
- ✅ CHANGELOG.md updated with Sprint 10 changes
- ✅ Git tag `v1.6.0` created
- ✅ GitHub release published
- ✅ Homebrew formula updated with v1.6.0

---

## Non-Goals (Out of Scope)

- ❌ Windows or Linux support (Mac-only for Sprint 10)
- ❌ GUI installer (Homebrew-only, defer to Sprint 11)
- ❌ Cloud-hosted backend (client-only, defer to Sprint 11+)
- ❌ Obsidian REST API integration (deprioritized)
- ❌ Automated TaskChampion server deployment (user chooses server)
- ❌ Mobile app (iOS/Android defer to future sprints)

---

## Dependencies

**External Tools:**
- Homebrew (Mac package manager) - Users must install
- TaskWarrior 3.4.1+ - Installed via Homebrew formula
- Obsidian - Users must install separately
- Claude Desktop - Optional (for MCP features)
- iCloud account - For vault sync (or user chooses alternative)

**Python Libraries:**
- No new dependencies for Sprint 10
- Existing: PyYAML, click, rich, requests

**Services:**
- TaskChampion sync server - User must set up (self-hosted or cloud)
- iCloud Drive - Apple service (or user chooses alternative sync)

---

## Technical Decisions & Q&A

### Q1: Why Homebrew instead of GUI installer?

**Decision:** Start with Homebrew (Sprint 10), defer GUI to Sprint 11.

**Rationale:**
- Homebrew handles dependencies (TaskWarrior) automatically
- Much faster to implement (4-6 hours vs 20-24 hours)
- Mac developers already familiar with Homebrew
- Easier to maintain (Homebrew handles updates)
- GUI can be added later for broader audience

**Trade-off:** Some non-technical users may struggle with terminal. However, Homebrew is the standard for Mac development tools.

---

### Q2: How does TaskWarrior sync work?

**TaskChampion Sync Architecture:**

```
┌──────────────┐         ┌──────────────┐
│ Computer 1   │         │ Computer 2   │
│              │         │              │
│ TaskWarrior  │         │ TaskWarrior  │
│ (local DB)   │         │ (local DB)   │
└──────┬───────┘         └──────┬───────┘
       │                        │
       │    task sync           │
       └────────┬───────────────┘
                │
         ┌──────▼──────┐
         │TaskChampion │
         │   Server    │
         │             │
         │ (operation  │
         │   log)      │
         └─────────────┘
```

**How it works:**
1. Each computer has local TaskWarrior SQLite database
2. `task sync` sends operations to server (not full database)
3. Server maintains operation log (append-only)
4. Other computers pull operations and apply locally
5. Conflicts resolved via operational transforms

**User Setup Required:**
- TaskChampion server running somewhere (self-hosted or cloud)
- Each computer runs `task config sync.server.url <url>`
- Each computer runs `task sync init` once
- Periodic `task sync` to push/pull changes

**Setup Wizard Support:**
- Wizard prompts for sync server URL
- Wizard configures TaskWarrior automatically
- User still must run `task sync` manually (or via cron)

---

### Q3: What if user doesn't use iCloud?

**Alternative Sync Methods Supported:**

| Method | Pros | Cons | brainplorp Support |
|--------|------|------|-------------------|
| iCloud Drive | Native, automatic | Mac-only | ✅ Auto-detected in setup |
| Obsidian Sync | Reliable, cross-platform | $8/month | ✅ Works (just a folder) |
| Syncthing | Free, self-hosted | Setup complexity | ✅ Works (just a folder) |
| Git | Version control | Manual commits | ✅ Works (just a folder) |
| Dropbox | Reliable | Privacy concerns | ✅ Works (just a folder) |

**brainplorp is agnostic** - it just reads/writes to `vault_path`. Sync method is user's choice.

**Setup Wizard:**
- Detects iCloud vault first (common case)
- Falls back to prompting for vault path
- No validation of sync method (user's responsibility)

---

### Q4: Should brainplorp auto-sync TaskWarrior?

**Decision:** No, don't auto-sync in Sprint 10.

**Rationale:**
- `task sync` can be slow (network latency)
- User may want control over when sync happens
- Sync failures could break brainplorp commands
- TaskWarrior UX expects manual sync or cron job

**Recommendation for Users:**
Add cron job:
```bash
# Sync every 15 minutes
*/15 * * * * task sync
```

Or add to shell profile:
```bash
# Sync on terminal open
task sync > /dev/null 2>&1 &
```

**Future:** Sprint 11+ could add `--sync` flag to brainplorp commands.

---

### Q5: Backend abstraction - why now vs Sprint 11?

**Decision:** Implement in Sprint 10 (now).

**Rationale:**
- User expressed interest in cloud backend ("we're inching towards something")
- Refactoring now = less code to migrate later
- Small implementation cost (5 hours)
- Keeps door open for Sprint 11 cloud backend
- No user-facing changes (just internal refactoring)

**What we're NOT doing:**
- Not building cloud backend in Sprint 10
- Not changing any user-facing behavior
- Not adding configuration options for backends (yet)

**What we ARE doing:**
- Creating Protocol interfaces (TaskBackend, VaultBackend)
- Wrapping existing code in LocalTaskWarriorBackend, LocalObsidianBackend
- Updating core modules to use backends
- Making it easy to add CloudTaskBackend in Sprint 11

---

### Q6: What happens if TaskWarrior not installed?

**Behavior:**

1. **Homebrew installation:** TaskWarrior installed as dependency (automatic)

2. **If user uninstalls TaskWarrior:**
   - brainplorp commands fail with clear error:
     ```
     ❌ TaskWarrior not installed

     Install via Homebrew:
       brew install task

     Or reinstall brainplorp:
       brew reinstall brainplorp
     ```

3. **Setup wizard:**
   - Validates TaskWarrior installed
   - Shows installation instructions if missing

4. **Config validation:**
   - `brainplorp config validate` checks for TaskWarrior
   - Reports error if missing

---

### Q7: How do we handle config sync across computers?

**Decision:** Git-based config sync is optional, not automated.

**Three Options for Users:**

**Option A: Manual Copy (Simplest)**
```bash
# Computer 1
cat ~/.config/brainplorp/config.yaml

# Computer 2 - paste and edit as needed
vim ~/.config/brainplorp/config.yaml
```

**Option B: Git Repo (Advanced)**
```bash
# Computer 1
cd ~/.config/brainplorp
git init
git add config.yaml
git commit -m "Initial config"
git remote add origin https://github.com/user/brainplorp-config.git (private repo!)
git push

# Computer 2
cd ~/.config/brainplorp
git clone https://github.com/user/brainplorp-config.git .
```

**Option C: Shared Config in Vault (Hacky)**
```bash
# Store config in Obsidian vault (syncs via iCloud)
ln -s ~/vault/.brainplorp-config.yaml ~/.config/brainplorp/config.yaml
```

**brainplorp doesn't automate this** - it's user's choice.

**Recommendation in Docs:** Option A for most users, Option B for advanced users with many computers.

---

### Q8: What about Windows/Linux support?

**Decision:** Mac-only for Sprint 10.

**Rationale:**
- User specifically said: "we're only doing this for Macs right now"
- Homebrew is Mac-only (Linux has Linuxbrew, but different)
- TaskWarrior install varies by platform (Homebrew vs apt vs pacman)
- iCloud Drive is Mac-only (Linux alternatives are different)
- Focus on one platform for Sprint 10, expand later

**Future Sprint:**
- Sprint 11 or 12 could add Linux support (apt-based installer)
- Windows support would need separate sprint (winget or MSI installer)

---

### Q9: How does setup wizard detect Obsidian vault?

**Detection Strategy:**

1. **Check iCloud Drive** (most common for Mac users)
   ```
   ~/Library/Mobile Documents/iCloud~md~obsidian/
   ```
   List folders, return first non-hidden folder

2. **Check standard locations**
   ```
   ~/Documents/Obsidian Vaults/
   ~/vault/
   ~/Obsidian/
   ~/Documents/vault/
   ```

3. **Look for `.obsidian` marker**
   Valid Obsidian vault contains `.obsidian/` folder

4. **If none found:**
   - Prompt user for path
   - Validate path has `.obsidian/` folder
   - Warn if not a valid vault

**Edge Cases:**
- Multiple vaults in iCloud → Wizard picks first, user can re-run `brainplorp setup` to change
- Vault outside standard locations → User must enter path manually
- No Obsidian installed → Wizard creates config anyway, warns user to install Obsidian

---

### Q10: What about testing with real testers?

**Testing Strategy:**

**Phase 1: Internal Testing (PM + Lead Engineer)**
- Test on own Macs
- Verify installation, setup, sync
- Fix obvious bugs

**Phase 2: Alpha Testing (1-2 technical users)**
- Give them TESTER_GUIDE.md
- Watch them install (screen share)
- Note friction points
- Fix critical issues

**Phase 3: Beta Testing (3-5 non-technical users)**
- Send them GitHub link + instructions
- Let them self-install (no support)
- Collect bug reports
- Fix before marking Sprint 10 complete

**Success Metric:**
- 80% of testers install successfully without assistance
- Average setup time < 10 minutes
- No critical bugs blocking core workflows

---

## Implementation Checklist

### Phase 1: Homebrew Formula
- [ ] Create `dimatosj/homebrew-brainplorp` GitHub repo
- [ ] Write `Formula/brainplorp.rb`
- [ ] Test formula on clean Mac
- [ ] Document release process in `RELEASE_PROCESS.md`
- [ ] Create v1.6.0 GitHub release
- [ ] Update Homebrew formula with v1.6.0 tarball
- [ ] Verify `brew install brainplorp` works

### Phase 2: Setup Wizard
- [ ] Create `src/brainplorp/commands/setup.py`
- [ ] Implement vault detection logic
- [ ] Implement TaskWarrior sync configuration
- [ ] Implement MCP auto-configuration
- [ ] Add `brainplorp config validate` command
- [ ] Test wizard on clean Mac
- [ ] Test wizard with iCloud vault
- [ ] Test wizard without Obsidian installed

### Phase 3: Documentation
- [ ] Write `MULTI_COMPUTER_SETUP.md`
- [ ] Write `TESTER_GUIDE.md`
- [ ] Update `README.md` with multi-computer section
- [ ] Test docs by following them exactly on 2 Macs
- [ ] Add troubleshooting section
- [ ] Add FAQ section

### Phase 4: Backend Abstraction
- [ ] Create `src/brainplorp/core/backends/task_backend.py` (Protocol)
- [ ] Create `src/brainplorp/core/backends/vault_backend.py` (Protocol)
- [ ] Create `src/brainplorp/core/backends/local_taskwarrior.py`
- [ ] Create `src/brainplorp/core/backends/local_obsidian.py`
- [ ] Update `config.py` to initialize backends
- [ ] Refactor `daily.py` to use `config.task_backend`
- [ ] Refactor `tasks.py` to use `config.task_backend`
- [ ] Refactor `note_operations.py` to use `config.vault_backend`
- [ ] Write backend tests
- [ ] Run full test suite (all 526+ tests should pass)

### Testing & Validation
- [ ] Fresh install test on clean Mac
- [ ] Multi-computer sync test (2 Macs)
- [ ] Alpha tester validation (1-2 users)
- [ ] Beta tester validation (3-5 users)
- [ ] All regression tests passing
- [ ] MCP tools still work in Claude Desktop

### Version Management
- [ ] Bump version to 1.6.0 in `__init__.py`
- [ ] Bump version to 1.6.0 in `pyproject.toml`
- [ ] Update `CHANGELOG.md`
- [ ] Create git tag `v1.6.0`
- [ ] Push tag to GitHub
- [ ] Create GitHub release
- [ ] Update Homebrew formula

### Documentation
- [ ] Update PM_HANDOFF.md with Sprint 10 completion
- [ ] Add Sprint 10 to SPRINT COMPLETION REGISTRY
- [ ] Document lessons learned
- [ ] Create handoff notes for Lead Engineer

---

## Risks & Mitigations

### Risk 1: TaskChampion Server Setup Complexity

**Risk:** Users struggle to set up TaskChampion sync server.

**Likelihood:** Medium
**Impact:** High (blocks multi-computer sync)

**Mitigation:**
- Provide clear documentation with multiple options (self-hosted, cloud)
- Consider hosting a shared test server for testers
- Make sync optional (single computer works fine without it)
- Add troubleshooting guide for common sync issues

---

### Risk 2: iCloud Sync Conflicts

**Risk:** Both computers edit same note offline → iCloud conflict files.

**Likelihood:** Low (uncommon for most users)
**Impact:** Medium (annoying but not breaking)

**Mitigation:**
- Document conflict resolution in MULTI_COMPUTER_SETUP.md
- Recommend "work on one computer at a time" workflow
- Future sprint could add conflict detection tool
- Not blocking for Sprint 10

---

### Risk 3: Homebrew Formula Rejection

**Risk:** Homebrew maintainers reject formula or require changes.

**Likelihood:** Low (tap is user-controlled)
**Impact:** Low (tap works regardless)

**Mitigation:**
- Use tap (user-controlled) not core Homebrew (maintainer-controlled)
- Tap: `brew tap dimatosj/brainplorp` always works
- Core: `brew install brainplorp` (without tap) requires approval
- Sprint 10 uses tap only

---

### Risk 4: Setup Wizard Vault Detection Fails

**Risk:** Wizard can't find Obsidian vault automatically.

**Likelihood:** Medium (non-standard locations)
**Impact:** Low (user can enter manually)

**Mitigation:**
- Wizard falls back to manual path entry
- Clear error messages
- Validate path has `.obsidian/` folder
- Not blocking - wizard completes successfully

---

### Risk 5: Backend Abstraction Breaks Existing Code

**Risk:** Refactoring introduces bugs in core workflows.

**Likelihood:** Low (good test coverage)
**Impact:** High (breaks existing features)

**Mitigation:**
- Run full test suite (526 tests) after refactoring
- No behavior change for users (just internal refactoring)
- Test all CLI commands manually
- Test all MCP tools manually
- Rollback if tests fail

---

## Effort Estimate

**Total:** ~18 hours (major sprint, MINOR version bump)

**Breakdown:**
- Phase 1 (Homebrew): 4 hours
- Phase 2 (Setup Wizard): 6 hours
- Phase 3 (Documentation): 3 hours
- Phase 4 (Backend Abstraction): 5 hours

**Timeline:**
- Implementation: 2-3 days (6-8 hours/day)
- Testing: 1 day (with testers)
- Documentation: 0.5 day (concurrent with implementation)

**Total Calendar Time:** 3-4 days

---

## Sprint 10 Definition of Done

### Code Complete
- ✅ All 4 phases implemented
- ✅ All checklist items complete
- ✅ Version bumped to 1.6.0
- ✅ CHANGELOG.md updated

### Testing Complete
- ✅ Fresh install test passed
- ✅ Multi-computer test passed
- ✅ All 526+ regression tests passing
- ✅ Alpha/beta tester validation passed

### Documentation Complete
- ✅ MULTI_COMPUTER_SETUP.md published
- ✅ TESTER_GUIDE.md published
- ✅ README.md updated
- ✅ PM_HANDOFF.md updated

### Release Complete
- ✅ GitHub release v1.6.0 published
- ✅ Homebrew formula updated
- ✅ `brew install brainplorp` verified working

### Sign-Off
- ✅ PM reviews implementation
- ✅ PM verifies success criteria met
- ✅ PM signs off on Sprint 10 completion

---

## Next Steps After Sprint 10

### Immediate (Sprint 10.1)
- Gather feedback from testers
- Fix bugs discovered during testing
- Polish documentation based on tester questions

### Sprint 11 Decision Point

**Path A: Cloud Backend** (if installation still too complex)
- Design cloud API
- Build TaskWarrior API server
- Build vault API server
- Deploy to cloud
- Thin client migration

**Path B: GUI Installer** (if Homebrew works well)
- Build .pkg installer for Mac
- Native setup wizard GUI
- Auto-updater
- Broader user adoption

**Path C: Platform Expansion** (if Sprint 10 success)
- Linux support (apt-based installer)
- Windows support (winget/MSI installer)
- Cross-platform testing

---

## Appendix A: Homebrew Formula Example

Full formula for reference:

```ruby
class Brainplorp < Formula
  include Language::Python::Virtualenv

  desc "Workflow automation for TaskWarrior + Obsidian with MCP integration"
  homepage "https://github.com/dimatosj/plorp"
  url "https://github.com/dimatosj/plorp/archive/refs/tags/v1.6.0.tar.gz"
  sha256 "REPLACE_WITH_ACTUAL_SHA256"
  license "MIT"

  depends_on "python@3.11"
  depends_on "task" # TaskWarrior 3.x

  # Python dependencies
  resource "click" do
    url "https://files.pythonhosted.org/packages/..."
    sha256 "..."
  end

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/..."
    sha256 "..."
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/..."
    sha256 "..."
  end

  def install
    virtualenv_install_with_resources

    # Install brainplorp package
    system bin/"python3", "-m", "pip", "install", "--no-deps", buildpath

    # Create config directory
    (var/"brainplorp").mkpath
  end

  def post_install
    ohai "brainplorp installed successfully!"
    ohai "Run 'brainplorp setup' to configure"
  end

  test do
    assert_match "brainplorp v1.6.0", shell_output("#{bin}/brainplorp --version")
    assert_match "brainplorp-mcp", shell_output("#{bin}/brainplorp-mcp --version")
  end
end
```

---

## Appendix B: Config File Schema (v1.6.0)

```yaml
# brainplorp configuration v1.6.0

# Obsidian vault location
vault_path: /Users/username/Library/Mobile Documents/iCloud~md~obsidian/MyVault

# TaskWarrior configuration
taskwarrior_data: ~/.task
taskwarrior_sync:
  enabled: true
  server_url: https://taskchampion.example.com

# Backend selection (for future cloud support)
task_backend: local  # Options: local, cloud (cloud in Sprint 11+)
vault_backend: local # Options: local, cloud (cloud in Sprint 11+)

# Email inbox (optional)
email:
  enabled: false
  imap_server: imap.gmail.com
  imap_port: 993
  username: user@gmail.com
  password: app_password
  inbox_label: INBOX
  fetch_limit: 20

# Note access permissions (from Sprint 9)
note_access:
  allowed_folders:
    - daily
    - inbox
    - projects
    - notes
    - Docs
  excluded_folders:
    - .obsidian
    - .trash
  limits:
    max_folder_scan: 500
    max_note_size_mb: 10
  warnings:
    large_note_words: 10000

# Default editor
default_editor: vim
```

---

## Appendix C: TaskChampion Server Setup Guide

**Option 1: Self-Hosted (Raspberry Pi, VPS)**

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install TaskChampion server
cargo install taskchampion-sync-server

# Run server
taskchampion-sync-server --port 8080 --data-dir ~/taskchampion-data

# Configure TaskWarrior on clients
task config sync.server.url http://your-server-ip:8080
task config sync.server.client_id $(uuidgen)
task sync init
```

**Option 2: Cloud-Hosted (Railway.app)**

1. Create Railway account
2. New Project → Deploy from GitHub
3. Connect to taskchampion-sync-server repo (or fork it)
4. Set PORT environment variable: 8080
5. Deploy
6. Copy public URL: `https://taskchampion-xxx.up.railway.app`
7. Configure TaskWarrior:
   ```bash
   task config sync.server.url https://taskchampion-xxx.up.railway.app
   task sync init
   ```

**Option 3: Docker (Local or Cloud)**

```bash
# Run server in Docker
docker run -d \
  --name taskchampion \
  -p 8080:8080 \
  -v ~/taskchampion-data:/data \
  taskchampion/sync-server:latest

# Configure TaskWarrior
task config sync.server.url http://localhost:8080
task sync init
```

---

## Pending Decisions

### PD-1: Git Branching Strategy for Phase 4 ✅ DECIDED

**Issue:** Phase 4 (Backend Abstraction) involves refactoring existing core modules, which carries different risk than Phases 1-3 (new code).

**Phase 4 Risk Profile:**
- **Low Risk:** Creating new Protocol interfaces and backend wrapper classes (~2 hours)
- **Medium Risk:** Refactoring core modules to use backends (~2-3 hours)
  - Scope: 6 core modules require changes (per Q15 answer)
  - Risk: Breaking State Synchronization pattern during refactor
  - Mitigation: 526 existing tests, TDD approach, incremental commits

**Refactoring Scope (from Phase 4):**
- Change call sites from `integrations.taskwarrior.create_task()` to `config.task_backend.create_task()`
- Mechanical transformation, but touches existing code
- Each module touched requires test verification

**Branching Options Evaluated:**

**Option A: Single Branch** ❌ REJECTED
- Implement all 4 phases on `sprint-10-homebrew-setup`
- Merge to master when complete → v1.6.0
- Phases 1-3 cannot be shipped independently
- **Risk:** All-or-nothing delivery - Phase 4 problems block entire Sprint 10

**Option B: Two Branches** ✅ SELECTED (Modified)
- Branch 1: Phases 1-3 (Homebrew + Setup + Docs) → v1.6.0
- Branch 2: Phase 4 (Backend Abstraction) → v1.6.1 (or v1.6.0 if merges quickly)
- Phases 1-3 can be shipped independently
- **Benefit:** Maximizes user value, minimizes risk, preserves flexibility

**Option C: Defer Phase 4** ❌ REJECTED
- Ship Phases 1-3 as Sprint 10 (v1.6.0)
- Move Phase 4 to Sprint 10.1 (v1.6.1)
- Removes refactoring risk from Sprint 10 delivery
- **Risk:** Loss of momentum, context switching, Q14 guidance might be forgotten

---

## PM Decision: Modified Option B (Two Branches)

**Decided by:** PM/Architect
**Date:** 2025-10-11
**Rationale:** Maximizes user value (ship Phases 1-3 early), minimizes risk (Phase 4 refactoring isolated), preserves flexibility (can defer Phase 4 without blocking Sprint 10)

### Implementation Strategy

**Branch 1: `sprint-10-installation` (Phases 1-3)**

**Scope:**
- Phase 1: Homebrew Formula (~4 hours)
- Phase 2: Interactive Setup Wizard (~6 hours)
- Phase 3: Multi-Computer Setup Guide (~3 hours)

**Target:** v1.6.0

**Risk:** Low (new code only, no refactoring)

**Timeline:** 10-13 hours

**Merge Criteria:**
- ✅ Homebrew formula works (`brew install brainplorp` succeeds)
- ✅ Setup wizard completes successfully (`brainplorp setup`)
- ✅ Documentation tested on 2 Macs (multi-computer guide)
- ✅ All 526 existing tests passing (zero regressions)
- ✅ Fresh install test passes (new user account)
- ✅ PM sign-off

**Git Workflow:**
```bash
# Week 1: Implement Phases 1-3
git checkout -b sprint-10-installation master

# Phase 1: Homebrew
# - Create homebrew-brainplorp repo
# - Write Formula/brainplorp.rb
# - Test installation

# Phase 2: Setup Wizard
# - Create commands/setup.py
# - Implement vault detection
# - Implement TaskWarrior sync config
# - Implement MCP auto-config

# Phase 3: Documentation
# - Write MULTI_COMPUTER_SETUP.md
# - Write TESTER_GUIDE.md
# - Update README.md

# Test and merge
git checkout master
git merge sprint-10-installation
git tag v1.6.0
git push origin master v1.6.0

# v1.6.0 SHIPPED! ✅
```

---

**Branch 2: `sprint-10-backend-abstraction` (Phase 4)**

**Scope:**
- Phase 4: Backend Abstraction Layer (~5 hours)
  - Create backend Protocol interfaces
  - Create local backend implementations
  - Refactor 6 core modules to use backends
  - Write backend tests (~16 new tests)

**Target:** v1.6.1 (or v1.6.0 if merges before Branch 1)

**Risk:** Medium (refactors existing code, touches State Sync pattern)

**Timeline:** 5 hours

**Merge Criteria:**
- ✅ All 540+ tests passing (526 existing + 16 backend tests)
- ✅ Manual verification of State Sync pattern:
  - Create task → appears in project note ✅
  - Mark task done → removed from project note ✅
  - Process inbox → tasks synced correctly ✅
- ✅ Zero behavior changes observed (regression testing)
- ✅ Lead Engineer confident: "State Sync pattern intact"
- ✅ Code review by PM (verify State Sync preservation)
- ✅ PM sign-off

**Git Workflow:**
```bash
# Week 1-2: Implement Phase 4 (parallel to Branch 1, or after)
git checkout -b sprint-10-backend-abstraction master

# Phase 4a: Create backends
# - src/brainplorp/core/backends/task_backend.py (Protocol)
# - src/brainplorp/core/backends/vault_backend.py (Protocol)
# - src/brainplorp/core/backends/local_taskwarrior.py (Implementation)
# - src/brainplorp/core/backends/local_obsidian.py (Implementation)
# - Write backend tests (~16 tests)

# Phase 4b: Refactor core modules (ONE AT A TIME)
# - Refactor core/daily.py → run tests ✅
# - Refactor core/tasks.py → run tests ✅
# - Refactor core/process.py → run tests ✅
# - Refactor core/projects.py → run tests ✅
# - Refactor core/note_operations.py → run tests ✅

# Phase 4c: Manual State Sync verification
# - Create task, verify appears in project note
# - Mark task done, verify removed from project note
# - Test all workflows that touch State Sync

# If ready: merge to master
git checkout master
git merge sprint-10-backend-abstraction
git tag v1.6.1
git push origin master v1.6.1

# If not ready: keep in branch, defer to Sprint 10.1
# v1.6.0 already shipped, no blocking issues
```

---

### Decision Point After Branch 1

**Scenario A: Branch 1 ships successfully (v1.6.0)**
1. ✅ **Option 1:** Branch 2 merges cleanly → Ship as v1.6.1 in Sprint 10
2. ✅ **Option 2:** Branch 2 has issues → Defer to Sprint 10.1, still have working v1.6.0

**Scenario B: Branch 1 has problems**
- Still ship v1.6.0 with installation improvements
- Phase 4 remains in parallel branch, no blocking issues

**Scenario C: Branch 2 ready before Branch 1 merged**
- Merge Branch 2 first if tests pass
- Merge Branch 1 afterward
- Ship as single v1.6.0 (all 4 phases)

---

### Risk Mitigation for Phase 4

**TDD Approach:**
1. Write backend tests FIRST (before refactoring)
2. Verify backends delegate correctly to integrations
3. Then refactor core modules

**Incremental Commits:**
1. Refactor ONE core module at a time
2. Run full test suite after EACH commit
3. Catch regressions immediately
4. Example commit sequence:
   ```
   commit 1: Create backend Protocol interfaces
   commit 2: Create LocalTaskWarriorBackend (tests pass)
   commit 3: Create LocalObsidianBackend (tests pass)
   commit 4: Refactor core/daily.py (tests pass)
   commit 5: Refactor core/tasks.py (tests pass)
   commit 6: Refactor core/process.py (tests pass)
   commit 7: Refactor core/projects.py (tests pass)
   commit 8: Refactor core/note_operations.py (tests pass)
   commit 9: Manual State Sync verification
   ```

**Manual State Sync Verification:**
After all refactoring complete, manually test:
- Create task in project → verify appears in project note
- Mark task done → verify removed from project note
- Process inbox → verify tasks synced correctly
- Review project → verify State Sync works

**Rollback Plan:**
- If Phase 4 has issues, v1.6.0 already shipped
- Lead Engineer can take time to fix Phase 4 properly
- Sprint 10 not blocked, user has working installation

---

### Why Modified Option B?

**Risk Analysis:**

**Phases 1-3 (High Value, Low Risk):**
- ✅ New code only (no refactoring)
- ✅ User-facing value (easy installation, multi-computer docs)
- ✅ Tester enablement (TESTER_GUIDE.md + Homebrew)
- ✅ Sprint 10 goal achieved: "Enable Mac users to install brainplorp easily"
- ✅ Can ship independently

**Phase 4 (No Immediate Value, Medium Risk):**
- ⚠️ Refactors existing code (touches 6 core modules)
- ⚠️ State Synchronization pattern must be preserved (CRITICAL)
- ⚠️ 526 tests provide safety net, but subtle bugs possible
- ❌ Zero user-facing value in Sprint 10
- ✅ Future enabler for Sprint 11 cloud backend

**Example Failure Scenario (Single Branch):**
```
Week 1: Phases 1-3 complete, working great
Week 2: Phase 4 refactoring breaks projects.py State Sync
Week 3: Debugging State Sync regression
Week 4: Sprint 10 still not shippable
Result: 3 weeks of completed work (Phases 1-3) sitting in branch
```

**Modified Option B Prevents This:**
- Week 1: Ship v1.6.0 with Phases 1-3 ✅
- Week 2-3: Fix Phase 4 State Sync issue (no pressure)
- Week 4: Ship v1.6.1 with Phase 4 ✅
- Result: Users have working v1.6.0 immediately, Phase 4 ships when ready

---

### Sprint 10 Deliverables

**Guaranteed:**
- ✅ v1.6.0 with Phases 1-3 (Homebrew + Setup + Docs)
- ✅ User value: Easy installation, multi-computer setup guide
- ✅ Tester enablement: Lower barrier to entry

**If Phase 4 Ready:**
- ✅ v1.6.1 with backend abstraction (or v1.6.0 if merges early)
- ✅ Architecture prepared for Sprint 11 cloud backend

**If Phase 4 Needs More Time:**
- ✅ Defer to Sprint 10.1, still have working v1.6.0
- ✅ Sprint 10 goal achieved regardless

---

### Lead Engineer Guidance

**Implementation Order:**

**Option 1: Sequential (Recommended)**
```
Week 1: Branch 1 (Phases 1-3)
  - Focus on user-facing features
  - Ship v1.6.0 early

Week 2: Branch 2 (Phase 4)
  - Focus on refactoring
  - Ship v1.6.1 when ready
```

**Option 2: Parallel (Advanced)**
```
Week 1: Both branches simultaneously
  - Switch between branches as needed
  - Merge whichever is ready first
  - Ship v1.6.0 with 1-4 phases depending on readiness
```

**Recommendation:** Start with Branch 1 (Phases 1-3), ship v1.6.0, then work on Branch 2 (Phase 4). Simpler workflow, lower cognitive load, guaranteed user value early.

---

**Decision Status:** ✅ APPROVED - Modified Option B (Two Branches)

**Next Action:** Lead Engineer implements per branching strategy above.

---

## Lead Engineer Clarifying Questions

**Status:** ✅ ALL ANSWERED (25/25)
**Added:** 2025-10-11 (Lead Engineer initial review)
**Answered:** 2025-10-11 (PM/Architect review)

---

## PM Answers to Lead Engineer Questions

**Answered by:** PM/Architect
**Date:** 2025-10-11
**Review time:** ~2 hours

### Blocking Questions (Must Read First)

---

#### Q2: Separate MCP entry point ✅ CONFIRMED

**Question:** Do we currently have separate entry points (brainplorp vs brainplorp-mcp)?

**Answer:** YES - Both entry points already exist in pyproject.toml:

```toml
[project.scripts]
brainplorp = "brainplorp.cli:cli"
brainplorp-mcp = "brainplorp.mcp.server:main"
```

**Action:** No changes needed. Both entry points work correctly and are installed by Homebrew automatically.

**Test verification:**
```bash
# After brew install brainplorp
which brainplorp      # → /opt/homebrew/bin/brainplorp
which brainplorp-mcp  # → /opt/homebrew/bin/brainplorp-mcp
brainplorp --version  # → brainplorp v1.6.0
brainplorp-mcp --version  # → (should work, verify in testing)
```

---

#### Q3: GitHub repo creation timing ✅ USER ACTION REQUIRED

**Question:** Should I create `dimatosj/homebrew-brainplorp` repo, or should John create it?

**Answer:** **John (user) must create it** - I don't have permissions to create repos under `dimatosj` username.

**Process:**
1. User creates repo: `github.com/dimatosj/homebrew-brainplorp`
2. User adds you as collaborator (if needed)
3. You clone and add `Formula/brainplorp.rb`
4. You commit and push

**Blocking:** Yes - cannot proceed with Phase 1 until repo exists.

**Recommendation:** Ask John to create repo now, give you write access.

---

#### Q8: MCP executable installation ✅ ANSWERED

**Question:** How is brainplorp-mcp installed?

**Answer:** Same package, different entry point (see Q2 answer).

**Installation:**
- `brew install brainplorp` installs both entry points
- Both `brainplorp` and `brainplorp-mcp` commands available after install
- No separate package needed

**Setup wizard behavior:**
```python
# Line 374
brainplorp_mcp_path = which_command('brainplorp-mcp')
# This will find: /opt/homebrew/bin/brainplorp-mcp
```

**No additional work needed** - existing code correct.

---

#### Q10: TaskWarrior sync auto-configuration ✅ AUTOMATIC

**Question:** Does wizard run `task config` automatically, or just save to brainplorp config?

**Answer:** **Wizard runs `task config` automatically** for better UX.

**Implementation guidance:**
```python
# In setup.py, Step 2: TaskWarrior Sync
if choice == 1:  # Self-hosted server
    server_url = click.prompt("  Enter server URL")

    # Auto-configure TaskWarrior
    import subprocess
    subprocess.run(['task', 'config', 'sync.server.url', server_url])

    # Generate client ID
    import uuid
    client_id = str(uuid.uuid4())
    subprocess.run(['task', 'config', 'sync.server.client_id', client_id])

    click.echo("  ✓ TaskWarrior sync configured")
    click.echo("    Run 'task sync init' when ready")

    # Save to brainplorp config too
    config['taskwarrior_sync'] = {
        'enabled': True,
        'server_url': server_url
    }
```

**Rationale:** Users want "it just works" - manually running `task config` is friction.

**Safety:** Wizard only writes if TaskWarrior installed and sync not already configured.

---

#### Q14: Refactoring existing integrations ✅ KEEP BOTH FILES

**Question:** After moving logic to backends, should I delete integrations files?

**Answer:** **Option B - Keep both files (with backends importing from integrations initially)**

**Migration strategy:**

**Phase 4a: Backend Creation (safer, incremental)**
```python
# src/brainplorp/core/backends/local_taskwarrior.py
from brainplorp.integrations.taskwarrior import (
    add_task,
    get_tasks,
    mark_done,
    # ... other functions
)

class LocalTaskWarriorBackend:
    """Wrapper around existing integrations."""

    def create_task(self, description: str, **kwargs) -> str:
        # Delegate to existing integration
        return add_task(description, **kwargs)

    def get_tasks(self, filters: List[str]) -> List[Task]:
        # Delegate to existing integration
        return get_tasks(filters)
```

**Phase 4b: Core Module Updates**
```python
# src/brainplorp/core/daily.py
# OLD: from brainplorp.integrations.taskwarrior import get_tasks
# NEW: Use config.task_backend

def create_daily_note(config: Config):
    # OLD: tasks = get_tasks(['status:pending'])
    # NEW: Use backend
    tasks = config.task_backend.get_tasks(['status:pending'])
```

**Rationale:**
- **Less risky** - Backends delegate to tested code
- **Incremental** - Core modules migrate one at a time
- **Rollback-friendly** - Can revert core modules if issues found
- **Sprint 11 cleanup** - Move logic from integrations → backends after Sprint 10 stable

**Don't delete integrations/ in Sprint 10** - They're still the implementation.

---

#### Q15: Core module refactoring scope ✅ SPECIFIC LIST

**Question:** Which core modules exactly need refactoring?

**Answer:** **6 core modules need backend updates:**

**TaskWarrior Backend Updates (4 modules):**
1. **core/daily.py** - Creates daily notes with task queries
   - Changes: `get_tasks()` → `config.task_backend.get_tasks()`
   - Lines affected: ~5-10

2. **core/tasks.py** - Task management operations
   - Changes: All TaskWarrior calls → backend
   - Lines affected: ~15-20

3. **core/process.py** - Inbox processing with task creation
   - Changes: `add_task()`, `mark_done()` → backend
   - Lines affected: ~10-15

4. **core/projects.py** - Project-based task management
   - Changes: All TaskWarrior calls → backend
   - Lines affected: ~20-25

**Obsidian Backend Updates (2 modules):**
5. **core/note_operations.py** - General note management
   - Changes: All obsidian_notes calls → backend
   - Lines affected: ~30-40

6. **core/daily.py** (again) - Daily note creation
   - Changes: File I/O → `config.vault_backend`
   - Lines affected: ~10-15

**Other core modules DON'T need changes:**
- **core/inbox.py** - Uses note_operations (indirect)
- **core/review.py** - Uses other core modules (indirect)
- **core/notes.py** - Already abstracted
- **core/types.py** - Just TypedDicts
- **core/exceptions.py** - Just exceptions

**Total refactoring scope:** ~100-125 lines across 6 modules

**Effort estimate:** 3-4 hours (careful refactoring + testing)

---

#### Q20: Beta tester blocking vs non-blocking ✅ NON-BLOCKING

**Question:** Is beta tester validation blocking Sprint 10 completion?

**Answer:** **Non-blocking - Beta testing happens in Sprint 10.1**

**Sprint 10 Definition of Done:**
- ✅ All 4 phases implemented
- ✅ Homebrew formula works on your Mac
- ✅ Multi-computer test (you + John, or 2 accounts)
- ✅ All regression tests passing
- ✅ Documentation complete
- ✅ PM sign-off

**Sprint 10.1 Definition of Done (separate sprint):**
- ✅ Alpha testing (1-2 technical users)
- ✅ Beta testing (3-5 non-technical users)
- ✅ Bug fixes from feedback
- ✅ Documentation polish

**Rationale:**
- Beta testing requires external coordination (slow)
- Sprint 10 delivers functional Homebrew installer
- Sprint 10.1 validates with real users and polishes

**Your action:** Mark Sprint 10 complete after internal testing passes. User will coordinate beta testing separately.

---

#### Q24: State Synchronization applicability ✅ CORE MODULES RESPONSIBLE

**Question:** Does State Sync pattern still apply at backend level?

**Answer:** **Core modules still handle sync, backends are just data access.**

**Architecture clarity:**

```
┌─────────────────────────────────────────┐
│         Core Modules                    │
│  (State Synchronization happens here)   │
│                                         │
│  • mark_done(uuid)                      │
│    → task_backend.mark_done(uuid)       │
│    → vault_backend.update_section(...)  │  ← Sync enforcement
│                                         │
│  • add_task(...)                        │
│    → task_backend.create_task(...)      │
│    → vault_backend.append_to_note(...)  │  ← Sync enforcement
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│      Backend Layer (Data Access Only)   │
│                                         │
│  TaskBackend Protocol:                  │
│  • get_tasks() → read from TW           │
│  • mark_done() → write to TW            │
│                                         │
│  VaultBackend Protocol:                 │
│  • read_note() → read from vault        │
│  • update_section() → write to vault    │
│                                         │
│  NO SYNC LOGIC IN BACKENDS              │
└─────────────────────────────────────────┘
```

**State Sync remains in core modules:**
- `core/projects.py` lines 664-665: `mark_done() → remove_task_from_all_projects()`
- `core/process.py` lines 676-678: `mark_done() → remove_task_from_all_projects()`

**Backends are dumb pipes:**
- TaskBackend just calls TaskWarrior CLI
- VaultBackend just reads/writes files
- No business logic, no sync enforcement

**Critical:** Don't move sync logic to backends. Sync is a core concern, not a data access concern.

---

### High-Priority Questions

---

#### Q4: Python dependencies in formula ✅ MANUAL LISTING REQUIRED

**Question:** Do I need to manually specify all transitive dependencies?

**Answer:** **No - virtualenv_install_with_resources handles dependencies automatically**

**Homebrew approach for Sprint 10:**

```ruby
class Brainplorp < Formula
  include Language::Python::Virtualenv

  desc "Workflow automation for TaskWarrior + Obsidian"
  homepage "https://github.com/dimatosj/plorp"
  url "https://github.com/dimatosj/plorp/archive/refs/tags/v1.6.0.tar.gz"
  sha256 "..."
  license "MIT"

  depends_on "python@3.11"
  depends_on "task"

  def install
    virtualenv_install_with_resources
  end

  test do
    system bin/"brainplorp", "--version"
    system bin/"brainplorp-mcp", "--version"
  end
end
```

**What `virtualenv_install_with_resources` does:**
1. Creates Python virtualenv
2. Runs `pip install .` from project root
3. Reads `pyproject.toml` dependencies
4. Installs all dependencies from PyPI
5. No manual `resource` blocks needed

**When you WOULD need resource blocks:**
- If dependency not on PyPI (rare)
- If you want pinned versions different from pyproject.toml
- If building from source without PyPI access

**For Sprint 10:** Simple formula works fine. Don't overcomplicate.

**Formula simplification:**
- Remove resource blocks from Appendix A (lines 1765-1778)
- Trust Homebrew + PyPI for dependency resolution

---

#### Q23: GitHub release creation permissions ✅ USER CREATES RELEASE

**Question:** Do I have permissions to create releases on dimatosj/plorp repo?

**Answer:** **John (user) creates release, you prepare release notes**

**Release process (collaborative):**

**Your work (Lead Engineer):**
1. Complete Sprint 10 implementation
2. Bump version to 1.6.0 in `__init__.py` and `pyproject.toml`
3. Update CHANGELOG.md with Sprint 10 changes
4. Create git commit: `git commit -m "Sprint 10 implementation complete"`
5. Push to branch or master: `git push`
6. Prepare release notes in `RELEASE_NOTES_1.6.0.md`:
   ```markdown
   # brainplorp v1.6.0 - Mac Installation & Multi-Computer Sync

   ## New Features
   - Homebrew formula for easy installation (`brew install brainplorp`)
   - Interactive setup wizard (`brainplorp setup`)
   - Multi-computer sync support (TaskChampion + iCloud)
   - Backend abstraction layer (future cloud backend prep)

   ## Installation
   \`\`\`bash
   brew tap dimatosj/brainplorp
   brew install brainplorp
   brainplorp setup
   \`\`\`

   See [MULTI_COMPUTER_SETUP.md](Docs/MULTI_COMPUTER_SETUP.md) for sync setup.
   ```

**John's work (User):**
1. Create git tag: `git tag -a v1.6.0 -m "Sprint 10: Mac Installation & Multi-Computer Sync"`
2. Push tag: `git push origin v1.6.0`
3. Create GitHub release via web UI or `gh` CLI:
   ```bash
   gh release create v1.6.0 \
     --title "v1.6.0 - Mac Installation & Multi-Computer Sync" \
     --notes-file RELEASE_NOTES_1.6.0.md
   ```
4. Calculate SHA256 for formula:
   ```bash
   curl -L https://github.com/dimatosj/plorp/archive/refs/tags/v1.6.0.tar.gz | shasum -a 256
   ```
5. Update Homebrew formula with SHA256

**You don't need release permissions** - Just prepare the artifacts, user handles publishing.

---

### Medium-Priority Questions

---

#### Q5: Directory structure for setup command ✅ CREATE commands/ DIRECTORY

**Question:** Should I create new `commands/` directory?

**Answer:** **Yes - Create `src/brainplorp/commands/` directory**

**Rationale:**
- Separates commands from main CLI logic
- Allows for future commands (install, upgrade, doctor, etc.)
- Cleaner project structure
- Follows Click best practices for large CLIs

**Directory structure:**
```
src/brainplorp/
├── cli.py              # Main CLI group, command registration
├── commands/           # NEW directory
│   ├── __init__.py
│   ├── setup.py        # Setup wizard
│   └── config.py       # Config validation (future)
├── core/
├── integrations/
├── mcp/
└── ...
```

**cli.py updates:**
```python
# src/brainplorp/cli.py
from brainplorp.commands.setup import setup
from brainplorp.commands.config import config  # Future

cli.add_command(setup)
cli.add_command(config)  # Config group for validate, show, etc.
```

**Alternative NOT recommended:** Putting in `cli.py` would make that file too large (already 500+ lines).

---

#### Q9: Config validation command location ✅ SUBCOMMAND GROUP

**Question:** Is `brainplorp config validate` a subcommand group or single command?

**Answer:** **Subcommand group `config` with multiple subcommands**

**CLI structure:**
```
brainplorp config validate     # Check configuration
brainplorp config show         # Display current config
brainplorp config edit         # Open config in editor (future)
brainplorp config reset        # Reset to defaults (future)
```

**Implementation:**
```python
# src/brainplorp/commands/config.py
import click

@click.group()
def config():
    """Manage brainplorp configuration."""
    pass

@config.command()
def validate():
    """Validate brainplorp configuration."""
    # Implementation from spec...
    pass

@config.command()
def show():
    """Display current configuration."""
    from brainplorp.config import load_config
    config = load_config()
    click.echo(f"Vault path: {config.vault_path}")
    # ... etc
```

**Why subcommand group:**
- Extensible for future config operations
- Follows git/docker pattern (`git config`, `docker config`)
- Better organization than flat namespace

**Sprint 10 scope:** Just implement `validate` subcommand. Others can be added in Sprint 10.1 or 11.

---

#### Q11: Testing environment for multi-computer ✅ MULTIPLE OPTIONS

**Question:** Do I have access to 2 Macs for testing?

**Answer:** **Use what you have available - Multiple acceptable options:**

**Option A: You + John (Recommended)**
- You test on your Mac
- John tests on his Mac
- Real multi-computer scenario
- Real iCloud/TaskChampion sync testing

**Option B: Two user accounts on same Mac**
```bash
# Create test user account
sudo sysadmin -addUser testuser
# Log in as testuser, install brainplorp, test sync
# iCloud sync won't work (same iCloud account)
# But TaskWarrior sync will work
```

**Option C: VM (Parallels/VMware) + Host Mac**
- macOS VM + host Mac
- Requires macOS VM license
- Full multi-computer simulation

**Option D: Single Mac with two vault locations**
- Not recommended (doesn't test real sync)
- But validates basic functionality

**My recommendation:** **Option A (You + John)** for authentic testing. Ask John to help test multi-computer setup once Phase 3 docs complete.

**Fallback:** Option B if John unavailable - still tests most functionality.

---

#### Q12: TaskChampion test server ✅ SHARED TEST SERVER

**Question:** Should we provide shared test server URL for testers?

**Answer:** **Yes - Provide shared test server for Sprint 10 testing**

**Recommendation:**
1. **John deploys test server** (Railway, Fly.io, or Render)
   - Deployment guide in Appendix C (lines 1876-1887)
   - Takes ~15 minutes
   - Free tier sufficient for testing

2. **Add to TESTER_GUIDE.md:**
   ```markdown
   ## TaskWarrior Sync Setup

   For testing, use our shared sync server:

   \`\`\`bash
   task config sync.server.url https://brainplorp-test.railway.app
   task config sync.server.client_id $(uuidgen)
   task sync init
   \`\`\`

   **Note:** This is a test server - your tasks are not private!
   Use your own server for production.
   ```

3. **Setup wizard update:**
   ```python
   # Step 2: TaskWarrior Sync
   click.echo("    1. Self-hosted (you run the server)")
   click.echo("    2. Shared test server (for testing only)")
   click.echo("    3. Skip for now")

   choice = click.prompt("  Choose option", type=click.IntRange(1, 3), default=2)

   if choice == 2:
       test_server_url = "https://brainplorp-test.railway.app"
       # Auto-configure...
   ```

**Rationale:**
- **Lower barrier** - Testers don't need to deploy server
- **Faster onboarding** - Just run wizard, works immediately
- **Test server is temporary** - Production users deploy their own

**Action Required:** Ask John to deploy test server before alpha/beta testing.

---

#### Q17: Backend switching in config ✅ HIDDEN IN SPRINT 10

**Question:** Should `task_backend: local` be exposed to users?

**Answer:** **Hidden/hardcoded in Sprint 10 - Not in user-facing config**

**Config schema for Sprint 10:**
```yaml
# User-facing config (what users see and edit)
vault_path: /path/to/vault
taskwarrior_sync:
  enabled: true
  server_url: https://example.com
email:
  enabled: false
# ... etc

# Backend config NOT EXPOSED in Sprint 10
# Hardcoded in Config class:
# self.task_backend = LocalTaskWarriorBackend()
# self.vault_backend = LocalObsidianBackend()
```

**Config class implementation:**
```python
# src/brainplorp/config.py
class Config:
    def __init__(self):
        # Load user config
        self.config_data = self._load_yaml()

        # Hardcode backends (Sprint 10)
        self.task_backend = LocalTaskWarriorBackend()
        self.vault_backend = LocalObsidianBackend(self.vault_path)

        # Sprint 11: Check config for backend type
        # backend_type = self.config_data.get('task_backend', 'local')
```

**Rationale:**
- **Avoid confusion** - Users might try to set `task_backend: cloud` and get errors
- **Internal refactoring only** - Sprint 10 has no cloud backend to switch to
- **Sprint 11 exposure** - When cloud backend exists, add to config schema

**Appendix B config example (lines 1819-1820):** Remove those lines or mark as "Sprint 11+".

---

#### Q19: Fresh install test environment ✅ NEW USER ACCOUNT

**Question:** How should I test "fresh install"?

**Answer:** **Option A (Recommended) - New macOS user account**

**Process:**
```bash
# 1. Create test user
sudo sysadmin -addUser testuser -fullName "Test User" -password "testpass"

# 2. Log in as test user (via Fast User Switching)
# System Settings → Users & Groups → Switch User

# 3. As test user, install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 4. Install brainplorp
brew tap dimatosj/brainplorp
brew install brainplorp

# 5. Run setup wizard
brainplorp setup

# 6. Test commands
brainplorp --version
brainplorp tasks
```

**Why this is best:**
- ✅ Truly fresh environment (no ~/.config pollution)
- ✅ Tests Homebrew dependency installation
- ✅ Tests auto-detection of new vault
- ✅ Fast (no VM overhead)
- ✅ Easy to reset (delete user, recreate)

**Alternative options:**
- **Option B:** VM - Slower, requires VM license
- **Option C:** Reset Homebrew cellar - Doesn't test config isolation
- **Option D:** Docker - Limited macOS support, not worth it

**After testing:** Delete test user account to clean up.

---

#### Q25: Config backend initialization order ✅ LAZY INITIALIZATION

**Question:** What happens if vault_path doesn't exist when Config loads?

**Answer:** **Backends allow lazy/graceful initialization - Don't crash on load**

**Implementation pattern:**
```python
# src/brainplorp/core/backends/local_obsidian.py
class LocalObsidianBackend:
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        # DON'T validate path in __init__ - allow lazy init

    def read_note(self, path: str, mode: str = "full") -> NoteContent:
        # Validate when accessed
        full_path = self.vault_path / path

        if not self.vault_path.exists():
            raise FileNotFoundError(
                f"Vault path does not exist: {self.vault_path}\n"
                f"Run 'brainplorp setup' to configure vault location."
            )

        if not full_path.exists():
            raise FileNotFoundError(f"Note not found: {path}")

        # ... continue reading
```

**Rationale:**
- **Config loads during `brainplorp setup`** - Vault might not exist yet
- **Graceful error messages** - Tell user to run setup, not cryptic errors
- **Lazy initialization** - Only validate when accessing vault

**Error message example:**
```
$ brainplorp start
❌ Error: Vault path does not exist: /Users/test/vault

Run 'brainplorp setup' to configure your Obsidian vault location.
```

**Setup wizard creates config even if vault missing** - User can create vault later.

---

### Low-Priority Questions

---

#### Q1: Post-install directory purpose ✅ FUTURE-PROOFING

**Question:** What is `(var/"brainplorp").mkpath` for?

**Answer:** **Future-proofing - Not used in Sprint 10**

**Homebrew convention:**
- `var` directory for runtime data (logs, caches, databases)
- Common pattern even if not immediately used

**Potential future uses:**
- Task sync cache
- MCP server logs
- Installation analytics
- Update check cache

**Sprint 10 action:** Keep the line (harmless), but not referenced in code.

**Alternative:** Remove line if you prefer - Won't break anything.

---

#### Q6: Cloud server TODO comment ✅ KEEP TODO

**Question:** Is "TODO: Cloud server" intentional?

**Answer:** **Yes - Ship with TODO message**

**Wizard output:**
```
Step 2: TaskWarrior Sync
  TaskChampion Server Options:
    1. Self-hosted (you run the server)
    2. Cloud-hosted (recommended for testing)
    3. Skip for now

  Choose option [2]: 2

  ℹ Cloud server setup will be available in next release
```

**Rationale:**
- **Transparency** - User knows feature is planned
- **Expectations** - Don't make them search for non-existent cloud option
- **Sprint 11 hook** - Easy to replace with actual cloud server URL

**Alternative wording (slightly better):**
```python
elif choice == 2:
    click.echo("  ℹ Shared test server: https://brainplorp-test.railway.app")
    click.echo("    (Test server only - use self-hosted for production)")
    config['taskwarrior_sync'] = {
        'enabled': True,
        'server_url': 'https://brainplorp-test.railway.app'
    }
```

**Action:** If John deploys test server (Q12), use alternative wording. If not, keep TODO.

---

#### Q7: Utility function duplication ✅ SEPARATE MODULE

**Question:** Should `which_command()` be in utility module?

**Answer:** **Yes - Create `src/brainplorp/utils/system.py`**

**Better structure:**
```python
# src/brainplorp/utils/system.py
from pathlib import Path
import shutil

def which_command(cmd: str) -> Path | None:
    """Find command in PATH."""
    result = shutil.which(cmd)
    return Path(result) if result else None

def is_command_available(cmd: str) -> bool:
    """Check if command exists in PATH."""
    return which_command(cmd) is not None
```

**Usage in setup.py:**
```python
from brainplorp.utils.system import which_command, is_command_available

# Line 374
brainplorp_mcp_path = which_command('brainplorp-mcp')

# Line 442
if not is_command_available('task'):
    errors.append("TaskWarrior not installed")
```

**Also useful for:**
- Config validation checking for TaskWarrior
- MCP server checking for Claude Desktop
- Future tools (Obsidian CLI, gh CLI, etc.)

**Action:** Create utils/ directory and module.

---

#### Q13: Backend directory creation ✅ CREATE IT

**Question:** Should I create `src/brainplorp/core/backends/` directory?

**Answer:** **Yes - Create the directory structure:**

```bash
mkdir -p src/brainplorp/core/backends
touch src/brainplorp/core/backends/__init__.py
```

**Files to create in Phase 4:**
```
src/brainplorp/core/backends/
├── __init__.py
├── task_backend.py         # Protocol definition
├── vault_backend.py        # Protocol definition
├── local_taskwarrior.py    # Implementation
└── local_obsidian.py       # Implementation
```

**__init__.py contents:**
```python
"""Backend abstractions for TaskWarrior and Obsidian."""

from .task_backend import TaskBackend
from .vault_backend import VaultBackend
from .local_taskwarrior import LocalTaskWarriorBackend
from .local_obsidian import LocalObsidianBackend

__all__ = [
    'TaskBackend',
    'VaultBackend',
    'LocalTaskWarriorBackend',
    'LocalObsidianBackend',
]
```

**Action:** Straightforward - just create directory.

---

#### Q16: Protocol vs ABC for backends ✅ USE PROTOCOL

**Question:** Should I use `Protocol` or `ABC`?

**Answer:** **Use `Protocol` (as shown in spec)**

**Rationale:**

| Factor | Protocol | ABC |
|--------|----------|-----|
| Type checking | ✅ Static (mypy) | ✅ Static + runtime |
| Duck typing | ✅ Structural | ❌ Nominal (must inherit) |
| Flexibility | ✅ No inheritance needed | ❌ Must inherit |
| Python version | ✅ 3.8+ (typing_extensions) | ✅ 3.8+ (abc) |
| Error messages | ✅ Clear type errors | ✅ Clear runtime errors |

**Why Protocol is better here:**
- **Structural typing** - Cloud backend can be implemented anywhere
- **No inheritance required** - LocalTaskWarriorBackend doesn't need `(TaskBackend)` inheritance
- **Modern Python pattern** - Protocol is newer, more flexible approach

**Implementation:**
```python
from typing import Protocol, List, Optional

class TaskBackend(Protocol):
    """Abstract interface for task storage."""

    def create_task(self, description: str, **kwargs) -> str: ...
    def get_tasks(self, filters: List[str]) -> List[dict]: ...
    # ... etc
```

**mypy will enforce:** Any class passed as `TaskBackend` must have these methods.

**Action:** Use Protocol as shown in spec lines 890-926.

---

#### Q18: Backend singleton pattern ✅ SINGLETON (CREATED ONCE)

**Question:** Should backends be singletons or per-operation?

**Answer:** **Singleton - Created once in Config.__init__()**

**Implementation:**
```python
# src/brainplorp/config.py
class Config:
    _instance = None  # Singleton Config

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        # Create backends once
        self.task_backend = LocalTaskWarriorBackend()
        self.vault_backend = LocalObsidianBackend(self.vault_path)
```

**Rationale:**
- **Performance** - Don't recreate backends for every operation
- **State** - Backends can cache (e.g., TaskWarrior export cache)
- **Config pattern** - Config is singleton, backends should be too
- **Current pattern** - We already use Config singleton throughout codebase

**Testing:**
- Tests create new Config per test (test isolation)
- Each test gets fresh backends
- No cross-test pollution

**Action:** Follow singleton pattern as shown in spec lines 1080-1107.

---

#### Q21: Test count expectation ✅ UPDATE TO 540+

**Question:** Should I expect test count to increase?

**Answer:** **Yes - Update success criteria to 540+ tests**

**Expected new tests (Phase 4):**

**Backend protocol tests:**
- Test LocalTaskWarriorBackend implements all methods (~5 tests)
- Test LocalObsidianBackend implements all methods (~5 tests)

**Backend integration tests:**
- Test backend creation (~2 tests)
- Test backend calls delegate correctly (~4 tests)

**Total new tests:** ~16 tests
**Updated total:** 526 + 16 = **542 tests**

**Update spec line 1199:**
```markdown
- ✅ All 540+ regression tests passing (526 existing + ~16 backend tests)
```

**Update spec line 2095:**
```markdown
**Q21:** Should I expect test count to increase?

**Answer:** Yes - Expect ~16 new backend tests, total 540+ tests passing.
```

**Action:** Update success criteria to reflect new test count.

---

#### Q22: SHA256 calculation process ✅ STANDARD PROCESS

**Question:** What's the process for calculating SHA256?

**Answer:** **Standard process (you already know it, but documented here)**

**Process:**
```bash
# 1. Create GitHub release (John does this)
# 2. Calculate SHA256
curl -L https://github.com/dimatosj/plorp/archive/refs/tags/v1.6.0.tar.gz | shasum -a 256

# Output: <sha256_hash>  -

# 3. Update Homebrew formula
cd ~/homebrew-brainplorp
vim Formula/brainplorp.rb

# Update line 120:
# sha256 "<paste_hash_here>"

# 4. Commit and push
git commit -am "brainplorp 1.6.0"
git push
```

**Timing:**
- ✅ After GitHub release created
- ✅ Before users can `brew install`

**Verification:**
```bash
# User runs
brew install dimatosj/brainplorp/brainplorp

# Homebrew verifies:
# 1. Downloads tarball
# 2. Calculates SHA256
# 3. Compares to formula
# 4. Installs if match
```

**Action:** Document in `RELEASE_PROCESS.md` (Phase 1 checklist item).

---

## Implementation Guidance Summary

**Proceed with confidence - All questions answered.**

**Critical blockers resolved:**
- ✅ Q3: Ask John to create homebrew-brainplorp repo NOW
- ✅ Q14: Keep integrations/, backends delegate to them (safer)
- ✅ Q15: Refactor 6 core modules (~100 lines)
- ✅ Q20: Beta testing is Sprint 10.1 (non-blocking)
- ✅ Q24: State Sync stays in core modules

**Architecture clarity:**
- Backends are data access only (no business logic)
- Core modules handle State Synchronization
- Lazy initialization for graceful errors
- Protocol over ABC for flexibility

**Testing strategy:**
- Fresh install: New user account on Mac
- Multi-computer: You + John testing
- Test count: Expect 540+ tests (526 + 16 backend)
- Beta testing: Sprint 10.1 (after internal validation)

**Next steps:**
1. Ask John to create `dimatosj/homebrew-brainplorp` repo
2. Ask John to deploy TaskChampion test server (optional but recommended)
3. Start Phase 1 implementation

---

### Phase 1: Homebrew Formula

**Q1: Post-install directory purpose**
- **Line 132:** The formula creates `(var/"brainplorp").mkpath` in post_install
- **Question:** What is this directory for? Do we store runtime data there, or is it just future-proofing?
- **Impact:** Need to know if we should use this path in code or ignore it
- **Priority:** Low

**Q2: Separate MCP entry point**
- **Line 196:** Tests verify `brainplorp-mcp --version` works separately from `brainplorp --version`
- **Question:** Do we currently have separate entry points (brainplorp vs brainplorp-mcp) or is this new?
- **Current state:** Looking at pyproject.toml, need to verify if we have:
  ```toml
  [project.scripts]
  brainplorp = "brainplorp.cli:main"
  brainplorp-mcp = "brainplorp.mcp.server:main"  # Does this exist?
  ```
- **Impact:** May need to create new entry point for MCP server
- **Priority:** High (blocking Phase 1)

**Q3: GitHub repo creation timing**
- **Line 112:** Spec says "Create new GitHub repo: `dimatosj/homebrew-brainplorp`"
- **Question:** Should I create this repo as part of Phase 1, or should John create it beforehand?
- **Impact:** Need GitHub permissions to create repo under `dimatosj` organization/user
- **Priority:** High (blocking Phase 1)

**Q4: Python dependencies in formula**
- **Lines 1765-1778:** Formula includes resource blocks for click, pyyaml, rich
- **Question:** Do I need to manually specify all transitive dependencies, or does `virtualenv_install_with_resources` handle this?
- **Homebrew docs say:** Need to list all dependencies explicitly
- **Impact:** May need to audit full dependency tree
- **Priority:** Medium

---

### Phase 2: Setup Wizard

**Q5: Directory structure for setup command**
- **Line 210:** Code goes in `src/brainplorp/commands/setup.py`
- **Current structure:** We have `src/brainplorp/cli.py`, `workflows/`, `core/`, `integrations/`
- **Question:** Should I create new `commands/` directory, or put `setup.py` in root (`src/brainplorp/setup.py`)?
- **Alternative:** Could be a subcommand in existing `cli.py` structure
- **Impact:** Affects import paths and project organization
- **Priority:** Medium

**Q6: Cloud server TODO comment**
- **Line 266:** Setup wizard has TODO: "Cloud server setup will be available in next release"
- **Question:** Is this TODO intentional (ship with this message), or should I remove it for Sprint 10?
- **Impact:** User-facing message in wizard
- **Priority:** Low

**Q7: Utility function duplication**
- **Lines 405-409:** `which_command()` helper function defined
- **Question:** Should this be in a utility module (e.g., `src/brainplorp/utils/system.py`) rather than defined in setup.py?
- **Impact:** May want to reuse in other commands (config validation, etc.)
- **Priority:** Low

**Q8: MCP entry point detection**
- **Line 374:** `which_command('brainplorp-mcp')` to find MCP server path
- **Question:** How is brainplorp-mcp installed? Separate script, or same package with different entry point?
- **Related to Q2:** Need to understand entry point structure
- **Impact:** Setup wizard must find correct MCP executable
- **Priority:** High (blocking Phase 2)

**Q9: Config validation command location**
- **Line 427:** `brainplorp config validate` command
- **Question:** Is this a new subcommand group `config` with `validate` subcommand, or single command `validate`?
- **Preference:** `brainplorp config validate` (subcommand group) for extensibility
- **Impact:** CLI structure design
- **Priority:** Medium

**Q10: TaskWarrior sync auto-configuration**
- **Lines 261-270:** Setup wizard configures TaskWarrior sync
- **Question:** Does the wizard run `task config sync.server.url <url>` automatically, or just save to brainplorp config?
- **If automatic:** Need to shell out to `task config` command
- **If manual:** User must run `task config` separately
- **Impact:** Affects wizard implementation and user experience
- **Priority:** High

---

### Phase 3: Multi-Computer Setup Guide

**Q11: Testing environment for multi-computer**
- **Line 1189:** Success criteria: "Test docs by following them exactly on 2 Macs"
- **Question:** Do I have access to 2 Macs for testing, or should I use VM/separate user accounts?
- **Alternative:** Can test with 1 Mac + 1 Linux for sync logic (though Linux not in scope)
- **Impact:** Testing methodology
- **Priority:** Medium

**Q12: TaskChampion test server**
- **Lines 1597-1603 (Appendix C):** Multiple options for TaskChampion server setup
- **Question:** Should we provide a shared test server URL for testers, or require each tester to set up their own?
- **If shared:** Need to deploy and maintain test server
- **If individual:** Higher barrier to entry for testers
- **Impact:** Tester onboarding experience
- **Priority:** Medium

---

### Phase 4: Backend Abstraction Layer

**Q13: Backend directory creation**
- **Lines 887, 930:** New files in `src/brainplorp/core/backends/`
- **Question:** Should I create this directory structure, or does it already exist?
- **Current:** Need to verify if `backends/` exists in core/
- **Impact:** Project structure
- **Priority:** Low (straightforward to create)

**Q14: Refactoring existing integrations**
- **Line 972:** Comment says "existing logic from integrations/taskwarrior.py"
- **Question:** After moving logic to `backends/local_taskwarrior.py`, should I:
  - A) Delete `integrations/taskwarrior.py` entirely
  - B) Keep both files (old one imports from new one)
  - C) Keep old file with deprecation warning
- **Impact:** Affects backward compatibility and migration path
- **Priority:** High (affects architecture)

**Q15: Core module refactoring scope**
- **Line 1109:** "Update core modules (`daily.py`, `tasks.py`, etc.)"
- **Question:** Which core modules exactly need refactoring? Can you list them?
- **Current modules:** Need to audit which modules call TaskWarrior/Obsidian directly
- **Estimate:** Need to understand scope for time estimate accuracy
- **Impact:** Phase 4 effort and risk
- **Priority:** High

**Q16: Protocol vs ABC for backends**
- **Lines 893-926:** Using `Protocol` from typing module
- **Question:** Should I use `Protocol` (structural typing) or `ABC` (abstract base class)?
- **Protocol pros:** More flexible, duck typing
- **ABC pros:** Runtime checking, enforced inheritance
- **Python 3.8 support:** Both are available in 3.8+
- **Impact:** Type checking and error messages
- **Priority:** Low (either works, but need decision)

**Q17: Backend switching in config**
- **Lines 1819-1820:** Config has `task_backend: local` and `vault_backend: local`
- **Question:** Should these config options be exposed to users in Sprint 10, or hidden/hardcoded?
- **Sprint 10 behavior:** Always uses `local` backend
- **If hidden:** Users can't set these values (futureproofing only)
- **If exposed:** Users might try to set to "cloud" and get errors
- **Impact:** User-facing config schema
- **Priority:** Medium

**Q18: Backend initialization in Config**
- **Lines 1088-1107:** Config class initializes backends
- **Question:** Should backends be singletons (created once), or created per-operation?
- **Singleton pros:** Better performance, less initialization overhead
- **Per-operation pros:** Easier to test, no state issues
- **Current Config pattern:** Appears to be singleton-style
- **Impact:** Performance and testing
- **Priority:** Low

---

### Testing & Validation

**Q19: Fresh install test environment**
- **Line 1183:** "Fresh install test on clean Mac"
- **Question:** How should I test "fresh install"?
  - A) Create new macOS user account
  - B) Use VM (Parallels, VMware)
  - C) Docker container (limited Mac support)
  - D) Reset Homebrew cellar
- **Impact:** Testing reliability
- **Priority:** Medium

**Q20: Beta tester blocking vs non-blocking**
- **Line 1510:** "Phase 3: Beta Testing (3-5 non-technical users)"
- **Question:** Is beta tester validation blocking Sprint 10 completion, or can it happen in Sprint 10.1?
- **If blocking:** Need to coordinate with John to find testers
- **If non-blocking:** Can mark Sprint 10 complete before beta feedback
- **Impact:** Sprint completion timeline
- **Priority:** High (affects Definition of Done)

**Q21: Regression test scope**
- **Line 1199:** "All 526+ regression tests passing"
- **Question:** Should I expect test count to increase (backend tests), or stay at 526?
- **New tests:** Backend protocol compliance, backend implementations
- **Estimate:** +10-15 tests for backends
- **Impact:** Success criteria (should update to "536+ tests")
- **Priority:** Low

---

### Release & Deployment

**Q22: Homebrew formula SHA256 calculation**
- **Line 120:** SHA256 is "WILL_BE_CALCULATED_ON_RELEASE"
- **Question:** What's the process for calculating and updating SHA256?
- **Process:**
  ```bash
  curl -L https://github.com/dimatosj/plorp/archive/refs/tags/v1.6.0.tar.gz | shasum -a 256
  ```
- **Timing:** After creating GitHub release, before publishing formula
- **Impact:** Release process documentation
- **Priority:** Low (standard practice)

**Q23: GitHub release creation permissions**
- **Line 169:** "gh release create v1.6.0"
- **Question:** Do I have permissions to create releases on dimatosj/plorp repo, or should John do this?
- **Alternative:** I can prepare release notes, John creates release
- **Impact:** Release process ownership
- **Priority:** Medium

---

### Architecture & Design

**Q24: State Synchronization applicability**
- **Phase 4:** Backend abstraction refactors TaskWarrior/Obsidian access
- **Question:** Does State Synchronization pattern still apply at backend level?
- **Current pattern:** Core modules handle TW→Obsidian sync
- **With backends:** Should backends handle sync, or core modules still responsible?
- **My assumption:** Core modules still handle sync (backends are just data access)
- **Impact:** Architecture boundaries
- **Priority:** High (critical pattern)

**Q25: Config backend initialization order**
- **Lines 1085-1107:** Backends initialized in Config.__init__()
- **Question:** What happens if vault_path doesn't exist when Config loads?
- **Scenario:** User runs `brainplorp setup` but hasn't created vault yet
- **Should:** Backends allow lazy initialization?
- **Impact:** Error handling and user experience
- **Priority:** Medium

---

## Questions Summary

**Blocking Questions (Must answer before starting):**
- Q2: MCP entry point structure (High)
- Q3: GitHub repo creation (High)
- Q8: MCP executable installation (High)
- Q10: TaskWarrior auto-configuration (High)
- Q14: Refactoring migration strategy (High)
- Q15: Core module refactoring scope (High)
- Q20: Beta testing blocking status (High)
- Q24: State Sync at backend level (High)

**High-Priority Questions (Should answer in Phase 1-2):**
- Q4: Homebrew dependency listing
- Q23: GitHub release permissions

**Medium-Priority Questions (Can defer to implementation phase):**
- Q5: Setup command directory structure
- Q9: Config validation command structure
- Q11: Multi-computer testing environment
- Q12: TaskChampion test server
- Q17: Backend config exposure
- Q19: Fresh install testing
- Q25: Config initialization error handling

**Low-Priority Questions (Minor clarifications):**
- Q1: Post-install directory purpose
- Q6: Cloud server TODO message
- Q7: Utility function location
- Q13: Backend directory creation
- Q16: Protocol vs ABC choice
- Q18: Backend singleton pattern
- Q21: Test count expectation
- Q22: SHA256 calculation process

**Total Questions:** 25
**Status:** Awaiting PM answers

---

## Version History

- **v1.0.0** (2025-10-11) - Initial Sprint 10 spec
  - User needs analysis completed
  - Scope defined: Homebrew + setup wizard + multi-computer sync + backend abstraction
  - 4 phases documented with implementation details
  - Success criteria and testing requirements defined
  - Ready for PM review and lead engineer assignment

- **v1.0.1** (2025-10-11) - Lead Engineer Q&A added
  - 25 clarifying questions added by Lead Engineer
  - Questions grouped by phase and priority
  - Blocking questions identified for PM review

---

**End of Sprint 10 Specification**
