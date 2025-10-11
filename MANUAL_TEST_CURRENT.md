# Manual Testing Guide - v1.5.3

**Date:** 2025-10-11
**Version:** 1.5.3
**Test Count:** 526 tests passing

## Installation Status

✅ **Installed and Working**
- Package: `brainplorp` v1.5.3
- Location: `/opt/miniconda3/bin/brainplorp`
- Entry points: `brainplorp` and `brainplorp-mcp`
- Test suite: All 526 tests passing

## Quick Verification

```bash
# Check version
python -m brainplorp.cli --version
# Output: python -m brainplorp.cli, version 1.5.3

# Run test suite
python -m pytest tests/ -q
# Output: 526 passed in 2.23s
```

## Recent Fixes Applied

1. **Package Rename Cleanup** - Fixed remaining `plorp` → `brainplorp` references in tests
   - `tests/test_smoke.py` - Updated imports
   - `tests/test_config.py` - Updated monkeypatch paths
   - `tests/test_core/test_process.py` - Updated patch calls
   - All test files - Updated string references via sed

## Manual Testing Areas

### Sprint 9.3: Quick Add to Inbox
**Command:** `brainplorp inbox add "Your task here"`

**Test Cases:**
1. Add single task to inbox
2. Add multiple tasks
3. Check inbox file created at correct location
4. Process inbox items

### Sprint 9.2: Email Inbox Capture
**Command:** `brainplorp inbox fetch`

**Test Cases:**
1. Fetch emails from configured inbox
2. Verify emails added to inbox
3. Process email inbox items

### Sprint 9: General Note Management
**Commands:**
- `brainplorp note create "Note title" --task UUID`
- `brainplorp note link NOTE_PATH --task UUID`

**Test Cases:**
1. Create note without task link
2. Create note with task link
3. Link existing note to task
4. Verify bidirectional linking

### Sprint 8.6: Interactive Projects & State Sync
**Commands:**
- `brainplorp project create NAME --domain DOMAIN`
- `brainplorp project list`
- `brainplorp project tasks PROJECT_PATH`
- `brainplorp project process PROJECT_PATH`

**Test Cases:**
1. Create new project
2. List all projects
3. Add task to project
4. Mark task done via checkbox in project note
5. Verify task removed from project frontmatter (State Sync)
6. Process project note to sync checkboxes

### Core Workflows
**Commands:**
- `brainplorp start` - Generate daily note
- `brainplorp review` - Interactive review
- `brainplorp process` - Process informal tasks
- `brainplorp tasks` - List tasks

**Test Cases:**
1. Start daily note with pending tasks
2. Review tasks interactively
3. Process informal tasks (2-step workflow)
4. List tasks with filters

## Known Issues

None currently - all 526 tests passing.

## Configuration Files

Check these files for proper configuration:
- `~/.config/brainplorp/config.yaml` - Main configuration
- `~/.config/brainplorp/cli_focus.txt` - CLI domain focus
- `~/.config/brainplorp/mcp_focus.txt` - MCP domain focus

## Manual Test Checklist

- [ ] Verify brainplorp version
- [ ] Run full test suite
- [ ] Test inbox add command
- [ ] Test inbox fetch command (if email configured)
- [ ] Test note creation
- [ ] Test project creation
- [ ] Test project task management
- [ ] Test daily note generation
- [ ] Test task review workflow
- [ ] Test informal task processing
- [ ] Verify State Synchronization (task done → removed from projects)

## Next Steps

After manual testing is complete:
1. Report any issues found
2. Sprint 10 implementation can begin (pending GitHub repo creation)
3. Consider deploying TaskChampion test server for multi-computer testing

## Troubleshooting

If you encounter issues:

```bash
# Reinstall brainplorp
pip install -e . --force-reinstall

# Run specific test file
python -m pytest tests/test_cli.py -v

# Check imports work
python -c "import brainplorp; print(brainplorp.__version__)"
```

## Sprint 10 Readiness

**Status:** ✅ Code is ready for Sprint 10 implementation

**Blockers:**
- GitHub repo creation: `dimatosj/homebrew-brainplorp` (user action required)
- Optional: TaskChampion test server deployment

**Sprint 10 Spec:** `/Users/jsd/Documents/plorps/brainplorp/Docs/sprints/SPRINT_10_SPEC.md`
- All 25 Q&A answered
- Branching strategy decided (two-branch approach)
- Ready for lead engineer implementation
