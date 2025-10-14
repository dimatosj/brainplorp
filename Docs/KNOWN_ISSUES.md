# Known Issues

This document tracks known issues in brainplorp and their status.

## Active Issues

### 1. Doctor Command: Misleading "Hangs" Error on Fresh Install

**Affects:** v1.7.0
**Severity:** Medium (Confusing UX, not functional breakage)
**Status:** Documented, fix planned for v1.7.1

**Description:**
On a fresh installation, `brainplorp doctor` reports "TaskWarrior 3.4.0 hangs on operations" when TaskWarrior is simply not initialized (no `.taskrc` file). The command is waiting for interactive input, not actually hanging.

**Workaround:**
Manually initialize TaskWarrior:
```bash
task add "init task"    # Answer "yes" when prompted
task 1 done
brainplorp doctor       # Should now pass
```

**Fix Status:** Documented in `Docs/DOCTOR_COMMAND_IMPROVEMENTS.md`

**Related Files:**
- `src/brainplorp/utils/diagnostics.py` (lines 94-107)
- `Docs/DOCTOR_COMMAND_IMPROVEMENTS.md`

---

## Resolved Issues

### TaskWarrior 3.4.1 Hang Bug

**Affects:** Users who installed TaskWarrior 3.4.1 directly
**Severity:** High (Complete hang, system unusable)
**Status:** ✅ Resolved in v1.6.2+ by pinning to TaskWarrior 3.4.0

**Description:**
TaskWarrior 3.4.1 has an upstream bug that causes it to hang indefinitely on first initialization. The `task --version` command never returns.

**Resolution:**
brainplorp Homebrew formula now pins to TaskWarrior 3.4.0 (a known working version). Users who manually installed 3.4.1 should downgrade:

```bash
brew uninstall task
brew install dimatosj/brainplorp/taskwarrior-pinned
```

**Documented in:** `README.md` (Known Issues section)

---

## Issue Reporting

If you encounter an issue:

1. **Check this list first** to see if it's already known
2. **Run diagnostics:** `brainplorp doctor` to gather info
3. **Check troubleshooting:** `Docs/INSTALLATION_TROUBLESHOOTING.md`
4. **Report on GitHub:** https://github.com/dimatosj/brainplorp/issues

Include:
- brainplorp version (`brainplorp --version`)
- TaskWarrior version (`task --version`)
- macOS version
- Output from `brainplorp doctor`
- Steps to reproduce
