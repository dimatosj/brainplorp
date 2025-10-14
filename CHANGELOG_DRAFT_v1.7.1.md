# Changelog Draft: v1.7.1

**Release Date:** TBD
**Focus:** Bug fixes and UX improvements

## Bug Fixes

### `brainplorp doctor` - Misleading Error on Fresh Install

**Issue:** On fresh installations, `brainplorp doctor` incorrectly reports "TaskWarrior 3.4.0 hangs on operations" when TaskWarrior is simply not initialized.

**Root Cause:** The diagnostic check runs `task count` without first checking if `.taskrc` exists. Since the command requires interactive input to create the config file, it times out waiting for stdin.

**Fix:**
- Added initialization check before running TaskWarrior commands
- Improved error messages to distinguish between:
  - Not initialized (no `.taskrc`)
  - Actually hanging (legitimate timeout)
  - Database corruption
- Updated fix instructions to be step-by-step and accurate

**Changes:**
- `src/brainplorp/utils/diagnostics.py`: Added Test 2.5 initialization check
- Error message now says: "TaskWarrior 3.4.0 not initialized (no config file)"
- Fix instructions provide clear manual initialization steps

**User Impact:** ✅ Better
- Clear error messages that explain the actual problem
- Working fix instructions that users can follow successfully
- No more confusion about TaskWarrior "hanging"

## Improvements

### Setup Wizard - TaskChampion Cloud Sync Implementation

**Issue:** Setup wizard shows "Cloud server setup will be available in next release" placeholder message, but the server was already deployed in Sprint 10.2.

**Server Details:**
- URL: `https://brainplorp-sync.fly.dev`
- Status: ✅ Live and operational (deployed 2025-10-12)
- Type: TaskChampion sync server v0.7.2-pre on Fly.io

**Fix:**
Implement cloud sync option in setup wizard (lines 94-100 in `setup.py`):
- Replace placeholder with actual TaskChampion sync configuration
- Auto-generate client_id (UUID) and encryption_secret
- Configure TaskWarrior via `task config` commands
- Save credentials to config.yaml
- Display credentials for user to save for other computers
- Add prompt for "existing credentials" flow (Computer 2+)

**Changes:**
- `src/brainplorp/commands/setup.py`: Implement choice==2 cloud sync option
- Add helper functions: `generate_sync_credentials()`, `configure_taskwarrior_sync()`
- Test sync connection automatically during setup
- Display task count after first sync (upload vs download)

**User Impact:** ✅ Better
- Users can now actually use cloud sync (not just a placeholder)
- Multi-computer setup works as documented
- Automatic credential generation and TaskWarrior configuration
- Clear instructions for syncing additional computers

**Status:** ✅ IMPLEMENTED (2025-10-14)

### Better TaskWarrior Initialization in Setup Wizard (Stretch Goal)

If time permits, add automatic TaskWarrior initialization to `brainplorp setup`:

- Setup wizard detects uninitialized TaskWarrior
- Offers to initialize automatically
- Creates `.taskrc` non-interactively
- Runs init task and marks complete
- No user interaction required

**Status:** Optional for v1.7.1, may defer to v1.8.0

## Documentation

- Added `Docs/DOCTOR_COMMAND_IMPROVEMENTS.md` - Technical analysis and implementation guide
- Added `Docs/KNOWN_ISSUES.md` - Centralized known issues tracking
- Updated `README.md` - Link to troubleshooting docs

## Testing Checklist

Before release:

- [ ] Test on Mac with no `.taskrc` - Should detect "not initialized"
- [ ] Follow initialization steps - Should succeed
- [ ] Re-run doctor - Should pass
- [ ] Test with actual hanging TaskWarrior - Should detect correctly
- [ ] Test with corrupted `.task/` - Should provide troubleshooting
- [ ] Verify all error messages are clear and actionable

## Upgrade Notes

No breaking changes. Users on v1.7.0 can upgrade directly:

```bash
brew upgrade brainplorp
```

## Credits

- Issue discovered during fresh install testing on 2025-10-14
- Part of ongoing Sprint 10.1.1 installation hardening improvements
