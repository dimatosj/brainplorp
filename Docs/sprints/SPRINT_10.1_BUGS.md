# Sprint 10.1: Installation Issues & Bug Tracking

**Created:** 2025-10-12
**Status:** 🔴 ACTIVE - Critical issues blocking production use
**Related Sprint:** Sprint 10.1 (Wheel-based Homebrew distribution)

---

## Executive Summary

Sprint 10.1 wheel-based distribution **succeeded** in fixing the conda Mac installation hanging issue. However, **new critical issues** were discovered during first-time user testing that prevent brainplorp from being production-ready.

**Wheel installer status:** ✅ Working perfectly (12-second install, all dependencies included)

**Blocking issues:**
1. 🔴 **CRITICAL**: TaskWarrior 3.4.1 hangs on first initialization
2. 🟡 **MEDIUM**: Homebrew formula had cached_download filename issue (FIXED)

---

## Issue #1: TaskWarrior 3.4.1 Hangs on First Initialization

### Severity: 🔴 CRITICAL - Blocks all brainplorp functionality

### Status: OPEN - Root cause identified, solution needed

### Description

TaskWarrior 3.4.1 (installed via Homebrew) hangs indefinitely on first run. This prevents brainplorp from functioning because brainplorp calls `task` commands via subprocess.

**Affected commands:**
- `task --version` - Hangs indefinitely
- `task add "test"` - Hangs indefinitely
- `brainplorp start` - Hangs waiting for TaskWarrior response

### Reproduction Steps

1. Clean Mac with no TaskWarrior previously installed
2. Install brainplorp via Homebrew: `brew install dimatosj/brainplorp/brainplorp`
   - This installs TaskWarrior 3.4.1 as a dependency
3. Run `task --version`
   - **Expected**: Shows version number
   - **Actual**: Hangs indefinitely with no output
4. Run `brainplorp start`
   - **Actual**: Hangs waiting for TaskWarrior to respond

### Environment

**System:**
- macOS 15.4 (Sequoia)
- Homebrew (latest)
- Python 3.12.12 (via Homebrew)
- **Conda/miniconda3 present** (but not active)

**TaskWarrior:**
- Version: 3.4.1 (Homebrew bottle)
- Source: `brew install task`
- Location: `/opt/homebrew/bin/task`

**brainplorp:**
- Version: 1.6.1
- Installed via: Homebrew (wheel-based formula)
- Location: `/opt/homebrew/bin/brainplorp`

### Investigation Results

**Attempt 1: Check for TaskWarrior data directory**
```bash
$ ls -la ~/.task
ls: /Users/jsd/.task: No such file or directory
```
- No `.task` directory exists (expected on first run)

**Attempt 2: Check for running processes**
```bash
$ ps aux | grep task
jsd  74974  task status:pending export  # Hung process
jsd  74933  task diagnostics             # Hung process
```
- TaskWarrior processes are stuck running
- No output, no errors, just hanging

**Attempt 3: Kill and retry**
```bash
$ killall -9 task
$ task --version
# Still hangs
```
- Killing processes doesn't fix the issue
- Problem persists across retries

**Attempt 4: Manually create TaskWarrior database**
```bash
$ mkdir -p ~/.task
$ touch ~/.task/taskchampion.sqlite3
$ task --version
# Still hangs
```
- Pre-creating the database doesn't help
- Issue is in TaskWarrior's initialization code

**Attempt 5: Reinstall TaskWarrior**
```bash
$ rm -rf ~/.task ~/.taskrc
$ brew uninstall --ignore-dependencies task
$ brew install task
$ task --version
# Still hangs
```
- Fresh install doesn't fix the issue
- Problem is with TaskWarrior 3.4.1 itself

**Attempt 6: Check for lock files or permissions**
```bash
$ ls -la ~ | grep task
# No lock files found
$ ls -la ~/.task
# No files exist yet
```
- No lock files blocking initialization
- No permission issues detected

### Root Cause Analysis

**Confirmed:** This is a **TaskWarrior 3.4.1 bug**, not a brainplorp issue.

**Evidence:**
1. TaskWarrior hangs even without brainplorp running
2. Simple `task --version` command hangs
3. Fresh reinstall doesn't fix the issue
4. No error messages, logs, or diagnostics available
5. Process is stuck in running state but produces no output

**Hypothesis:** TaskWarrior 3.4.1 has a first-run initialization bug, possibly related to:
- SQLite database creation
- Configuration file generation
- Lock file handling
- Network checks (sync server detection?)
- Environment detection (conda presence?)

**Not caused by:**
- ✅ brainplorp code (TaskWarrior hangs independently)
- ✅ Wheel-based installation (same issue with source-based)
- ✅ Python dependencies (TaskWarrior is standalone binary)
- ✅ Homebrew installation method (binary issue, not packaging)

### Impact Assessment

**User Impact:**
- ⛔ **Cannot use brainplorp at all** - All core functions depend on TaskWarrior
- ⛔ `brainplorp start` hangs indefinitely
- ⛔ `brainplorp review` hangs indefinitely
- ⛔ `brainplorp tasks` hangs indefinitely
- ⛔ Setup wizard completes but brainplorp is unusable

**Installation Success Rate:**
- ✅ Wheel install: 100% (12 seconds, no issues)
- ✅ Dependencies: 100% (all Python packages installed)
- ✅ MCP configuration: 100% (Claude Desktop configured)
- ❌ TaskWarrior initialization: 0% (hangs on all test systems)

**Overall Production Readiness:** ⛔ **NOT READY** - Critical blocker

### Potential Solutions

**Solution 1: Wait for TaskWarrior upstream fix**
- **Pros:** Proper fix, no workarounds needed
- **Cons:** Timeline unknown, blocks brainplorp release
- **Effort:** 0 hours (wait for upstream)
- **Risk:** Could take weeks/months

**Solution 2: Downgrade to TaskWarrior 2.6.x**
- **Pros:** TaskWarrior 2.x is stable and widely tested
- **Cons:** brainplorp designed for 3.x (SQLite backend), may need code changes
- **Effort:** 2-4 hours (test and potentially refactor integrations)
- **Risk:** Medium (2.x uses different data format)

**Solution 3: Pin to specific TaskWarrior 3.x version that works**
- **Pros:** Stay on 3.x architecture
- **Cons:** Need to find a working version, may not exist
- **Effort:** 1-2 hours (testing different versions)
- **Risk:** Medium (may not find working version)

**Solution 4: Bundle TaskWarrior or use Python taskw library**
- **Pros:** Full control over TaskWarrior integration
- **Cons:** Significant architectural change, maintenance burden
- **Effort:** 8-12 hours (major refactor)
- **Risk:** High (large scope change)

**Solution 5: Initialize TaskWarrior manually in setup wizard**
- **Pros:** Workaround for first-run issue
- **Cons:** Doesn't fix underlying bug, may fail on some systems
- **Effort:** 2-3 hours (add init step to setup wizard)
- **Risk:** Medium (workaround may not work for all users)

**Solution 6: Add TaskWarrior diagnostic to setup wizard**
- **Pros:** Detect issue early and provide clear error
- **Cons:** Doesn't fix the issue, just detects it
- **Effort:** 1 hour (add diagnostic check)
- **Risk:** Low (detection only)

### Recommended Approach

**Short-term (Sprint 10.1.1 - 2 hours):**
1. Add TaskWarrior diagnostic check to setup wizard
2. Detect hanging TaskWarrior and provide clear error message
3. Document workaround in installation guide
4. Add "Known Issues" section to README

**Medium-term (Sprint 10.2 - 4 hours):**
1. Test TaskWarrior 3.3.x and 3.2.x versions
2. If older 3.x version works, pin Homebrew formula to that version
3. Update formula with working version
4. Test on multiple Mac configurations

**Long-term (Sprint 11):**
1. Report bug to TaskWarrior upstream
2. Monitor TaskWarrior releases for fix
3. Consider alternative TaskWarrior integration approaches
4. Evaluate Python taskw library as alternative

### Workarounds for Users (Temporary)

**Workaround A: Manual TaskWarrior initialization (untested)**
```bash
# Try initializing with a basic config
echo "data.location=~/.task" > ~/.taskrc
task rc.confirmation=off add "init task"
task 1 done
```

**Workaround B: Use older TaskWarrior version (untested)**
```bash
brew uninstall --ignore-dependencies task
# Install TaskWarrior 2.6.x or find working 3.x version
# (specific formula needed)
```

**Workaround C: Skip TaskWarrior-dependent features (partial functionality)**
```bash
# Use only MCP note operations (no task management)
# MCP tools that work without TaskWarrior:
# - list_vault_folders
# - create_note
# - read_note
# - append_to_note
# (not tested yet)
```

---

## Issue #2: Homebrew Formula cached_download Filename Issue

### Severity: 🟡 MEDIUM - Blocked initial installation

### Status: ✅ FIXED (2025-10-12)

### Description

Homebrew's `cached_download` returns a path with a hash prefix (e.g., `abc123--wheel.whl`), which pip doesn't recognize as a valid wheel filename.

### Error Message

```
ERROR: Invalid wheel filename (wrong number of parts): '1bc16bbba71c7edd80df6d63d91921015fa00e6cdcfa2703482180cd45b70269--brainplorp-1.6.1-py3-none-any'
```

### Root Cause

Homebrew caches downloads with format: `<hash>--<filename>`
Pip requires exact wheel naming: `<package>-<version>-<python>-<abi>-<platform>.whl`

### Solution Implemented

```ruby
def install
  # Copy wheel to proper filename (Homebrew caches with hash prefix)
  wheel_file = "brainplorp-#{version}-py3-none-any.whl"
  cp cached_download, wheel_file

  # Install wheel with dependencies
  system Formula["python@3.12"].opt_bin/"pip3.12", "install",
         "--target=#{libexec}",
         "--ignore-installed",
         wheel_file
  # ...
end
```

### Testing

**Test 1: Fresh install**
```bash
brew uninstall brainplorp
brew install dimatosj/brainplorp/brainplorp
# ✅ Success: Completed in 12 seconds
```

**Test 2: Reinstall**
```bash
brew reinstall brainplorp
# ✅ Success: Completed in 12 seconds
```

**Test 3: Verify installation**
```bash
brainplorp --version
# ✅ Output: brainplorp, version 1.6.1

which brainplorp
# ✅ Output: /opt/homebrew/bin/brainplorp

ls /opt/homebrew/Cellar/brainplorp/1.6.1/libexec/
# ✅ Shows all dependencies installed
```

### Resolution

- **Fixed in:** Commit `3a0d3e4` (homebrew-brainplorp repo)
- **Status:** ✅ Merged and tested
- **No further action needed**

---

## Issue #3: Setup Wizard - Potential Improvements (Not Critical)

### Severity: 🟢 LOW - Enhancement opportunity

### Status: DEFERRED - Document for future improvement

### Observations from First-Time User Testing

**Issue 3.1: Setup wizard doesn't validate TaskWarrior works**
- Setup completes successfully even though TaskWarrior is broken
- User discovers TaskWarrior issue only when running `brainplorp start`
- **Recommendation:** Add TaskWarrior health check to setup wizard

**Issue 3.2: No clear indication of what's hanging**
- When `brainplorp start` hangs, user doesn't know why
- No timeout, no error message, just hangs
- **Recommendation:** Add timeout and helpful error messages

**Issue 3.3: Setup wizard success message misleading**
- Shows "✓ Setup complete!" even though system is unusable
- **Recommendation:** Add post-setup validation step

**Issue 3.4: No diagnostic command**
- Users can't easily check system health
- **Recommendation:** Add `brainplorp doctor` command

---

## Testing Summary

### What Was Tested

**Wheel Installation (Sprint 10.1 core deliverable):**
- ✅ GitHub Actions workflow (builds wheel on tag)
- ✅ Wheel structure (dependencies, entry points)
- ✅ Homebrew formula (downloads and installs wheel)
- ✅ Installation speed (12 seconds vs 2-5 minutes)
- ✅ Dependencies (all Python packages installed automatically)
- ✅ Entry points (brainplorp and brainplorp-mcp commands work)
- ✅ MCP configuration (Claude Desktop config created)

**First-Time User Experience:**
- ✅ Clean system installation (from scratch)
- ✅ Setup wizard (vault detection, config creation)
- ✅ MCP configuration (automated via setup wizard)
- ❌ TaskWarrior functionality (hangs on first run) 🔴 **BLOCKER**
- ⏸️ brainplorp core commands (blocked by TaskWarrior issue)

### Test Environment

**System Configuration:**
- macOS 15.4 (Sequoia)
- Architecture: arm64 (Apple Silicon)
- Homebrew: Latest
- Python: 3.12.12 (Homebrew)
- Conda: miniconda3 present (but not active)

**Installation Method:**
```bash
brew tap dimatosj/brainplorp
brew install brainplorp
brainplorp setup
```

**What Succeeded:**
- Wheel downloads in <1 second
- Installation completes in 12 seconds
- All Python dependencies installed (30MB, 2,405 files)
- MCP server configured for Claude Desktop
- Setup wizard detects Obsidian vault
- Config file created at `~/.config/brainplorp/config.yaml`

**What Failed:**
- TaskWarrior initialization (hangs indefinitely)
- brainplorp core commands (blocked by TaskWarrior)

---

## Next Steps

### Immediate Action Items (Sprint 10.1.1)

**Priority 1: Unblock users**
- [ ] Test TaskWarrior 3.3.x, 3.2.x, 3.1.x versions
- [ ] Find a working TaskWarrior 3.x version
- [ ] Update Homebrew formula to pin working version
- [ ] Test installation on 2+ Macs

**Priority 2: Improve diagnostics**
- [ ] Add TaskWarrior health check to setup wizard
- [ ] Add timeout to `brainplorp start` command
- [ ] Add helpful error message when TaskWarrior hangs
- [ ] Create `brainplorp doctor` diagnostic command

**Priority 3: Documentation**
- [ ] Update README with known TaskWarrior issue
- [ ] Document manual TaskWarrior initialization workaround
- [ ] Add troubleshooting section to installation guide
- [ ] Create "Known Issues" section

### Research Tasks

- [ ] Test TaskWarrior on clean Mac (no conda)
- [ ] Test TaskWarrior on Intel Mac
- [ ] Test TaskWarrior 2.6.x compatibility with brainplorp
- [ ] Research TaskWarrior 3.x initialization process
- [ ] Check TaskWarrior GitHub issues for similar reports
- [ ] Evaluate Python taskw library as alternative

### Sprint Planning

**Sprint 10.1.1: TaskWarrior Fix (CRITICAL - 4 hours)**
- Goal: Get brainplorp working with a stable TaskWarrior version
- Deliverables:
  - Working TaskWarrior integration
  - Updated Homebrew formula with pinned version
  - Installation tested on multiple Macs
  - Documentation updated

**Sprint 10.2: Installation Robustness (8 hours)**
- Goal: Bulletproof the installation experience
- Deliverables:
  - TaskWarrior health checks in setup wizard
  - `brainplorp doctor` diagnostic command
  - Comprehensive error messages
  - Installation troubleshooting guide

---

## Lessons Learned

### What Went Well

1. **Wheel-based distribution works perfectly**
   - 12-second install time achieved
   - No hanging on conda Macs (Sprint 10 goal ✅)
   - Dependencies install automatically
   - Formula is simple and maintainable

2. **GitHub Actions automation works**
   - Wheel built in 16 seconds
   - SHA256 calculated automatically
   - Release created with assets

3. **MCP configuration works**
   - Setup wizard configures Claude Desktop correctly
   - brainplorp-mcp command installed properly

### What Didn't Go Well

1. **Didn't test TaskWarrior functionality during wheel testing**
   - Focused on installation speed and wheel structure
   - Assumed TaskWarrior would work (it's an external dependency)
   - Should have tested full end-to-end workflow

2. **No diagnostic commands for troubleshooting**
   - When TaskWarrior fails, users have no way to diagnose
   - No `brainplorp doctor` or health check commands
   - Error messages don't help identify root cause

3. **External dependency (TaskWarrior) broke**
   - Can't control upstream package quality
   - Need better dependency testing and pinning strategy
   - Should test new versions before updating

### Improvements for Future Sprints

1. **Test external dependencies thoroughly**
   - Don't assume Homebrew packages work
   - Test TaskWarrior functionality, not just installation
   - Add integration tests for external dependencies

2. **Add diagnostic tooling early**
   - `brainplorp doctor` command should be Sprint 1 priority
   - Health checks for all external dependencies
   - Clear error messages with actionable troubleshooting

3. **Pin external dependency versions**
   - Don't use `depends_on "task"` (gets latest)
   - Pin to specific version: `depends_on "task@3.3"`
   - Test new versions before updating

4. **Better testing protocol**
   - Test on multiple Mac configurations
   - Test full user workflow, not just installation
   - Include TaskWarrior functionality in test checklist

---

## Document Maintenance

**Created:** 2025-10-12 by Lead Engineer
**Last Updated:** 2025-10-12
**Related Files:**
- `Docs/sprints/SPRINT_10.1_WHEEL_DISTRIBUTION_SPEC.md`
- `Formula/brainplorp.rb` (homebrew-brainplorp repo)
- `.github/workflows/release.yml`

**Update Protocol:**
- Add new issues as discovered
- Update issue status when resolved
- Document all attempted solutions
- Keep testing summary current
