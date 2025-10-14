# Doctor Command Improvements for v1.7.1

## Issue Summary

The `brainplorp doctor` command produces misleading error messages when TaskWarrior is not initialized on a fresh installation.

**Current Behavior:**
```
Checking TaskWarrior... ✗ TaskWarrior 3.4.0 hangs on operations

Required fixes:
  TaskWarrior:
    Issue: TaskWarrior 3.4.0 hangs on operations
    Fix: Try: rm -rf ~/.task ~/.taskrc && task add "init"
```

**Actual Problem:** TaskWarrior is waiting for interactive user input to create `.taskrc`, not hanging.

**User Impact:**
- Confusing error message suggests TaskWarrior is broken
- Suggested fix command won't work (also requires interactive input)
- Users may think they have a serious bug when it's just uninitialized

## Root Cause

**File:** `src/brainplorp/utils/diagnostics.py`
**Function:** `check_taskwarrior()`, lines 94-107

```python
# Test 3: Try basic operation (with timeout)
try:
    count_result = subprocess.run(
        ['task', 'count'],
        capture_output=True,
        text=True,
        timeout=5
    )
except subprocess.TimeoutExpired:
    return {
        'passed': False,
        'message': f'TaskWarrior {version} hangs on operations',
        'fix': 'Try: rm -rf ~/.task ~/.taskrc && task add "init"'
    }
```

**Why This Fails:**

1. Fresh TaskWarrior install has no `~/.taskrc` file
2. `task count` command prompts: "Would you like a sample /Users/jsd/.taskrc created?"
3. `subprocess.run()` with `capture_output=True` doesn't provide stdin
4. Command waits forever for input → timeout after 5 seconds
5. Error message says "hangs" when really it's just waiting for user input

## Recommended Solution

### Add Initialization Check Before Running Commands

Add a new test between version check and command execution to detect uninitialized TaskWarrior:

```python
# Test 2.5: Check if TaskWarrior is initialized (NEW)
taskrc_path = Path.home() / '.taskrc'
task_data_path = Path.home() / '.task'

if not taskrc_path.exists() or not task_data_path.exists():
    return {
        'passed': False,
        'message': f'TaskWarrior {version} not initialized (no config file)',
        'fix': 'Initialize TaskWarrior interactively:\n' +
               '    1. Run: task add "init task"\n' +
               '    2. Answer "yes" when prompted to create config\n' +
               '    3. Run: task 1 done\n' +
               '    4. Run: brainplorp doctor',
        'details': {
            'taskrc_exists': taskrc_path.exists(),
            'task_data_exists': task_data_path.exists()
        }
    }
```

### Improve Error Messages for Actual Hangs

If TaskWarrior is initialized but still times out, provide more detailed troubleshooting:

```python
except subprocess.TimeoutExpired:
    return {
        'passed': False,
        'message': f'TaskWarrior {version} hangs on operations (unexpected)',
        'fix': 'This is unusual. Try:\n' +
               '    1. Kill any stuck task processes: pkill task\n' +
               '    2. Check database: ls -la ~/.task/\n' +
               '    3. If corrupted, reset: rm -rf ~/.task ~/.taskrc\n' +
               '    4. Re-initialize: task add "init" (answer yes)',
        'details': {
            'note': 'TaskWarrior initialized but hanging - may be database corruption'
        }
    }
```

## Alternative: Auto-Initialize in Setup Wizard

**Better long-term solution:** Have `brainplorp setup` automatically initialize TaskWarrior.

### Add to `src/brainplorp/commands/setup.py`

```python
def initialize_taskwarrior_non_interactive():
    """Initialize TaskWarrior non-interactively by creating .taskrc first."""
    taskrc_path = Path.home() / '.taskrc'

    if taskrc_path.exists():
        return True  # Already initialized

    # Create minimal .taskrc
    taskrc_content = """# Taskwarrior configuration
data.location=~/.task

# Color theme
include /opt/homebrew/Cellar/taskwarrior-pinned/3.4.0/share/doc/task/rc/light-256.theme
"""

    taskrc_path.write_text(taskrc_content)

    # Now run initialization command (won't prompt because .taskrc exists)
    try:
        subprocess.run(
            ['task', 'add', 'init task'],
            capture_output=True,
            timeout=10,
            check=True
        )

        # Complete the init task
        subprocess.run(
            ['task', '1', 'done'],
            capture_output=True,
            timeout=10,
            check=True
        )

        return True
    except Exception as e:
        return False
```

Then in the setup wizard (after Step 1.5 TaskWarrior validation):

```python
# Step 1.5: TaskWarrior Validation (existing code)
tw_check = check_taskwarrior(verbose=False)

if not tw_check['passed']:
    # If it's just not initialized, offer to do it automatically
    if 'not initialized' in tw_check.get('message', ''):
        click.echo()
        if click.confirm("  Initialize TaskWarrior now?", default=True):
            click.echo("  Initializing TaskWarrior...")
            if initialize_taskwarrior_non_interactive():
                click.echo("  ✓ TaskWarrior initialized")
                # Re-check to confirm
                tw_check = check_taskwarrior(verbose=False)
                if tw_check['passed']:
                    click.echo(f"  ✓ {tw_check['message']}")
                else:
                    # Still failed, show error and exit
                    click.echo(f"  ✗ Initialization failed: {tw_check['message']}")
                    sys.exit(1)
            else:
                click.echo("  ✗ Failed to initialize TaskWarrior")
                sys.exit(1)
        else:
            click.echo("  Setup cannot continue without TaskWarrior.")
            sys.exit(1)
    else:
        # Other error (not just uninitialized)
        click.secho(f"  ✗ TaskWarrior issue detected:", fg='red', bold=True)
        click.echo(f"     {tw_check['message']}")
        # ... rest of existing error handling
```

## Implementation Plan

### Phase 1: Quick Fix (v1.7.1)
- Add Test 2.5 initialization check in `diagnostics.py`
- Improve error messages
- Update fix instructions to be multi-step and clear
- **Estimated effort:** 30 minutes
- **Testing:** Run on fresh Mac without `.taskrc`

### Phase 2: Better UX (v1.8.0)
- Add auto-initialization to `brainplorp setup`
- Add optional `brainplorp init` command for manual initialization
- Update documentation
- **Estimated effort:** 2 hours
- **Testing:** Full setup wizard flow on fresh Mac

## Testing Checklist

Before releasing v1.7.1:

- [ ] Test `brainplorp doctor` on Mac without `.taskrc` → Should say "not initialized"
- [ ] Follow initialization instructions → Should work
- [ ] Run `brainplorp doctor` again → Should pass
- [ ] Test with actual hanging TaskWarrior (simulate with sleep) → Should detect correctly
- [ ] Test with corrupted `.task/` database → Should provide useful troubleshooting

## Related Files

- `src/brainplorp/utils/diagnostics.py` - Contains the buggy check
- `src/brainplorp/commands/doctor.py` - Calls the diagnostic functions
- `src/brainplorp/commands/setup.py` - Setup wizard (for auto-init)
- `Docs/INSTALLATION_TROUBLESHOOTING.md` - User-facing troubleshooting guide

## See Also

- Issue experienced during fresh install testing on 2025-10-14
- Related to TaskWarrior 3.4.0 vs 3.4.1 version pinning in Homebrew formula
- Part of Sprint 10.1.1 installation hardening improvements
