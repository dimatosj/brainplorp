# Sprint 10.1.1: Installation Hardening & TaskWarrior Fix

**Version:** 1.0.0
**Status:** ✅ Ready for Implementation
**Sprint:** 10.1.1 (Patch sprint - Critical bug fix + diagnostics)
**Estimated Effort:** 7-8 hours (2 + 2 + 2 + 1.5)
**Dependencies:** Blocks Sprint 10.2 (cloud sync requires working TaskWarrior)
**Architecture:** TaskWarrior version pinning + diagnostic tooling + setup validation
**Target Version:** brainplorp v1.6.2 (PATCH)
**Date:** 2025-10-12

---

## Executive Summary

Sprint 10.1.1 fixes the critical TaskWarrior 3.4.1 hang bug and adds comprehensive diagnostic tooling to prevent similar issues in the future. This sprint unblocks Sprint 10.2 (cloud sync) and makes brainplorp production-ready.

**Problem:**
- TaskWarrior 3.4.1 hangs indefinitely on first initialization (see SPRINT_10.1_BUGS.md)
- Setup wizard doesn't validate TaskWarrior functionality
- No diagnostic tools for troubleshooting issues
- All subprocess calls lack timeouts (hang forever)

**Solution:**
- Test and pin to working TaskWarrior 3.x version
- Implement `brainplorp doctor` diagnostic command
- Add TaskWarrior validation to setup wizard
- Add timeouts to all subprocess calls
- Document known issues and troubleshooting

**Impact:**
- ✅ brainplorp becomes production-ready
- ✅ Users get clear error messages instead of hangs
- ✅ Future issues easier to diagnose
- ✅ Unblocks Sprint 10.2 (cloud sync)

---

## Problem Statement

### Current State (Sprint 10.1)

**What Works:**
- ✅ Wheel-based Homebrew installation (12 seconds)
- ✅ All Python dependencies installed automatically
- ✅ MCP server configuration
- ✅ Setup wizard completes successfully

**Critical Blocker:**
- ❌ TaskWarrior 3.4.1 hangs on first run
- ❌ `task --version` hangs indefinitely
- ❌ `brainplorp start` hangs waiting for TaskWarrior
- ❌ Users can't use brainplorp at all

**Root Cause:**
TaskWarrior 3.4.1 has an upstream bug causing first-run initialization to hang. This is NOT a brainplorp bug, but it blocks all brainplorp functionality.

### User Impact

**Installation Success Rate:**
- ✅ Wheel install: 100%
- ✅ Dependencies: 100%
- ❌ TaskWarrior functionality: 0%
- **Overall:** ⛔ NOT PRODUCTION READY

**User Experience:**
```bash
$ brew install brainplorp
==> Installing brainplorp...
✓ brainplorp 1.6.1 installed (12 seconds)

$ brainplorp setup
✓ Setup complete!

$ brainplorp start
# Hangs forever... no error, no timeout, no help
```

**User Frustration:**
- No indication of what's wrong
- No diagnostic tools
- No clear error messages
- Setup says "success" but brainplorp doesn't work

---

## Proposed Solution (High-Level)

### Four-Phase Approach

**Phase 1: TaskWarrior Version Fix (2 hours)**
- Test TaskWarrior 3.3.x, 3.2.x, 3.1.x versions systematically
- Find the most recent working 3.x version
- Pin Homebrew formula to working version
- Test on multiple Macs (with/without conda)

**Phase 2: Diagnostic Tooling (2 hours)**
- Implement `brainplorp doctor` command
- Check TaskWarrior functionality (with timeout)
- Check Python dependencies
- Check vault accessibility
- Check config validity
- Check MCP configuration
- Provide actionable fix instructions for each failure

**Phase 3: Setup Wizard Hardening (2 hours)**
- Add TaskWarrior validation step to setup wizard
- Abort setup if TaskWarrior is broken
- Add timeouts to all subprocess calls
- Show clear error messages with fix instructions

**Phase 4: Documentation (1.5 hours)**
- Document TaskWarrior 3.4.1 issue in README
- Add troubleshooting section to installation guide
- Document `brainplorp doctor` usage
- Create clear help-seeking instructions

---

## Implementation Phases

### Phase 1: TaskWarrior Version Fix (2 hours) - CRITICAL

**Objective:** Find and pin a working TaskWarrior 3.x version

#### Step 1: Systematic Version Testing (1 hour)

**Test Script:**
```bash
#!/bin/bash
# test_taskwarrior_version.sh

VERSION=$1

echo "Testing TaskWarrior ${VERSION}..."
echo "=================================="

# Uninstall current version
brew uninstall --ignore-dependencies task 2>/dev/null

# Install test version
if ! brew install task@${VERSION}; then
    echo "❌ Version ${VERSION} not available in Homebrew"
    exit 1
fi

# Clean TaskWarrior data
rm -rf ~/.task ~/.taskrc

# Test 1: Version check (with timeout)
echo -n "Test 1: task --version... "
if timeout 5s task --version > /dev/null 2>&1; then
    echo "✅ PASS"
else
    echo "❌ FAIL (hung or errored)"
    exit 1
fi

# Test 2: Basic task creation (with timeout)
echo -n "Test 2: task add... "
if timeout 5s task add "test task" > /dev/null 2>&1; then
    echo "✅ PASS"
else
    echo "❌ FAIL (hung or errored)"
    exit 1
fi

# Test 3: Task count (with timeout)
echo -n "Test 3: task count... "
if timeout 5s task count > /dev/null 2>&1; then
    echo "✅ PASS"
else
    echo "❌ FAIL (hung or errored)"
    exit 1
fi

# Test 4: Sync init (with timeout)
echo -n "Test 4: task sync init... "
if timeout 10s task sync init https://brainplorp-sync.fly.dev > /dev/null 2>&1; then
    echo "✅ PASS"
else
    echo "⚠️  WARN (may require credentials)"
fi

echo ""
echo "✅ TaskWarrior ${VERSION} WORKING"
echo "=================================="
exit 0
```

**Test Matrix:**

| Version | Test 1 (--version) | Test 2 (add) | Test 3 (count) | Test 4 (sync) | Result |
|---------|-------------------|--------------|----------------|---------------|---------|
| 3.4.1   | ❌ Hang           | -            | -              | -             | FAIL    |
| 3.3.0   | ?                 | ?            | ?              | ?             | TBD     |
| 3.2.0   | ?                 | ?            | ?              | ?             | TBD     |
| 3.1.0   | ?                 | ?            | ?              | ?             | TBD     |
| 2.6.2   | ?                 | ?            | ?              | ?             | FALLBACK|

**Testing Procedure:**
```bash
# Run test script for each version
./test_taskwarrior_version.sh 3.3
./test_taskwarrior_version.sh 3.2
./test_taskwarrior_version.sh 3.1
./test_taskwarrior_version.sh 2.6  # Fallback if no 3.x works

# Document results in spreadsheet or markdown table
```

#### Step 2: Update Homebrew Formula (30 minutes)

**File:** `Formula/brainplorp.rb` (homebrew-brainplorp repo)

**Before:**
```ruby
depends_on "task"  # Gets latest (3.4.1 - broken!)
```

**After (example with 3.3):**
```ruby
depends_on "task@3.3"  # Pinned to working version
```

**Alternative (if specific version not available):**
```ruby
# Option A: Use specific Homebrew commit/revision
depends_on "task" => "3.3.0"

# Option B: Document manual installation
# Users must install TaskWarrior separately:
# brew install task@3.3
```

**Update post_install message:**
```ruby
def post_install
  ohai "brainplorp installed successfully!"
  ohai "Next steps:"
  ohai "  1. Verify TaskWarrior: task --version"
  ohai "     (Should show 3.3.x - 3.4.1 has known issues)"
  ohai "  2. Run 'brainplorp doctor' to check system"
  ohai "  3. Run 'brainplorp setup' to configure"
  ohai "  4. Run 'brainplorp mcp' to configure Claude Desktop"
  ohai "  5. Restart Claude Desktop to load brainplorp tools"
end
```

#### Step 3: Multi-Mac Testing (30 minutes)

**Test Environments:**

**Mac 1: With conda (arm64)**
- macOS 15.4 (Sequoia)
- Conda/miniconda3 installed
- Python 3.12 (Homebrew)

**Mac 2: Clean system (arm64 or Intel)**
- macOS 14.x or 15.x
- No conda
- Fresh Homebrew installation

**Test Protocol:**
```bash
# On each Mac:

# 1. Clean slate
brew uninstall brainplorp task
rm -rf ~/.task ~/.taskrc ~/.config/brainplorp

# 2. Install updated formula
brew install dimatosj/brainplorp/brainplorp

# 3. Verify TaskWarrior
task --version  # Should show 3.3.x
task add "test install"
task list
task 1 done

# 4. Run brainplorp setup
brainplorp setup

# 5. Test brainplorp commands
brainplorp tasks
brainplorp start

# 6. Document results
```

**Success Criteria:**
- ✅ TaskWarrior 3.3 (or working version) identified
- ✅ Homebrew formula updated and pushed
- ✅ Installation tested on 2+ Macs
- ✅ All TaskWarrior commands complete in <5 seconds
- ✅ `brainplorp start` works without hanging

**Deliverables:**
- Test results document (markdown table with version/test matrix)
- Updated Homebrew formula with pinned version
- Testing notes from multiple Mac configurations

---

### Phase 2: Diagnostic Tooling (2 hours) - HIGH PRIORITY

**Objective:** Implement `brainplorp doctor` command for comprehensive system diagnostics

#### Implementation

**File:** `src/brainplorp/commands/doctor.py`

```python
"""
brainplorp doctor command - System diagnostics and health checks.

Usage:
    brainplorp doctor

Checks:
- TaskWarrior installation and functionality
- Python dependencies
- Obsidian vault accessibility
- Config file validity
- MCP server configuration
"""

import subprocess
import sys
import json
from pathlib import Path
from typing import Dict, Any

import click
import yaml


@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed diagnostic information')
def doctor(verbose: bool):
    """
    Diagnose brainplorp installation and configuration issues.

    Runs comprehensive health checks and provides actionable fix instructions.
    """
    click.echo()
    click.secho("brainplorp System Diagnostics", fg='cyan', bold=True)
    click.echo("=" * 60)
    click.echo()

    checks = [
        ('TaskWarrior', check_taskwarrior, True),   # Critical
        ('Python Dependencies', check_python_dependencies, True),
        ('Configuration File', check_config_validity, True),
        ('Obsidian Vault', check_vault_access, False),  # Not critical
        ('MCP Server', check_mcp_configuration, False)
    ]

    results = {}
    critical_failures = []

    for name, check_func, is_critical in checks:
        click.echo(f"Checking {name}...", nl=False)
        result = check_func(verbose)
        results[name] = result

        if result['passed']:
            click.secho(f" ✓", fg='green', nl=False)
            click.echo(f" {result['message']}")
        else:
            click.secho(f" ✗", fg='red', nl=False)
            click.echo(f" {result['message']}")
            if is_critical:
                critical_failures.append((name, result))

    # Summary
    click.echo()
    click.echo("=" * 60)

    if all(r['passed'] for r in results.values()):
        click.secho("✓ All checks passed!", fg='green', bold=True)
        click.echo("brainplorp is ready to use.")
        return 0

    elif not critical_failures:
        click.secho("⚠ Some non-critical checks failed", fg='yellow', bold=True)
        click.echo("brainplorp should still work, but some features may be limited.")

        click.echo()
        click.echo("Recommendations:")
        for name, result in results.items():
            if not result['passed'] and result.get('fix'):
                click.echo(f"  • {name}: {result['fix']}")
        return 0

    else:
        click.secho("✗ Critical checks failed", fg='red', bold=True)
        click.echo("brainplorp cannot function until these issues are resolved.")

        click.echo()
        click.echo("Required fixes:")
        for name, result in critical_failures:
            click.echo()
            click.secho(f"  {name}:", fg='yellow', bold=True)
            click.echo(f"    Issue: {result['message']}")
            if result.get('fix'):
                click.echo(f"    Fix: {result['fix']}")

        click.echo()
        click.echo("After fixing, run 'brainplorp doctor' again to verify.")
        return 1


def check_taskwarrior(verbose: bool = False) -> Dict[str, Any]:
    """
    Check if TaskWarrior is installed and functional.

    Tests:
    1. TaskWarrior binary exists in PATH
    2. Version check completes (doesn't hang)
    3. Basic operations work (task count)
    """
    try:
        # Test 1: Check if 'task' command exists
        which_result = subprocess.run(
            ['which', 'task'],
            capture_output=True,
            text=True,
            timeout=2
        )

        if which_result.returncode != 0:
            return {
                'passed': False,
                'message': 'TaskWarrior not found in PATH',
                'fix': 'Install TaskWarrior: brew install task@3.3'
            }

        task_path = which_result.stdout.strip()

        # Test 2: Check version (with timeout to catch hangs)
        try:
            version_result = subprocess.run(
                ['task', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
        except subprocess.TimeoutExpired:
            return {
                'passed': False,
                'message': 'TaskWarrior hangs on --version (known issue with 3.4.1)',
                'fix': 'Downgrade TaskWarrior: brew uninstall task && brew install task@3.3',
                'details': {
                    'path': task_path,
                    'issue': 'TaskWarrior 3.4.1 has a first-run initialization bug'
                }
            }

        if version_result.returncode != 0:
            return {
                'passed': False,
                'message': f'TaskWarrior failed to run: {version_result.stderr[:100]}',
                'fix': 'Reinstall TaskWarrior: brew reinstall task@3.3'
            }

        version = version_result.stdout.strip()

        # Check for problematic version
        if '3.4.1' in version:
            return {
                'passed': False,
                'message': f'TaskWarrior {version} has known hang issues',
                'fix': 'Downgrade: brew uninstall task && brew install task@3.3',
                'details': {
                    'path': task_path,
                    'version': version,
                    'issue': 'Version 3.4.1 hangs on first initialization'
                }
            }

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

        if count_result.returncode != 0:
            return {
                'passed': False,
                'message': f'TaskWarrior {version} installed but not functional',
                'fix': 'Initialize: rm -rf ~/.task ~/.taskrc && task add "init task" && task 1 done',
                'details': {
                    'error': count_result.stderr[:200]
                }
            }

        task_count = count_result.stdout.strip()

        return {
            'passed': True,
            'message': f'{version} working ({task_count} tasks)',
            'details': {
                'path': task_path,
                'version': version,
                'task_count': task_count
            }
        }

    except Exception as e:
        return {
            'passed': False,
            'message': f'TaskWarrior check failed: {str(e)}',
            'fix': 'Check TaskWarrior installation: brew list task'
        }


def check_python_dependencies(verbose: bool = False) -> Dict[str, Any]:
    """Check if required Python packages are installed."""
    required = {
        'click': 'Click',
        'yaml': 'PyYAML',
        'rich': 'Rich'
    }

    missing = []
    installed = []

    for module, package in required.items():
        try:
            __import__(module)
            installed.append(package)
        except ImportError:
            missing.append(package)

    if missing:
        return {
            'passed': False,
            'message': f'Missing dependencies: {", ".join(missing)}',
            'fix': 'Reinstall brainplorp: brew reinstall brainplorp',
            'details': {
                'missing': missing,
                'installed': installed
            }
        }

    return {
        'passed': True,
        'message': f'All dependencies installed ({len(installed)} packages)',
        'details': {'installed': installed}
    }


def check_config_validity(verbose: bool = False) -> Dict[str, Any]:
    """Check if config file exists and is valid YAML."""
    config_path = Path.home() / '.config' / 'brainplorp' / 'config.yaml'

    if not config_path.exists():
        return {
            'passed': False,
            'message': 'Config file not found',
            'fix': 'Run: brainplorp setup',
            'details': {'expected_path': str(config_path)}
        }

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Check required fields
        required_fields = ['vault_path']
        missing_fields = [f for f in required_fields if f not in config]

        if missing_fields:
            return {
                'passed': False,
                'message': f'Config missing fields: {", ".join(missing_fields)}',
                'fix': 'Re-run: brainplorp setup',
                'details': {
                    'path': str(config_path),
                    'missing_fields': missing_fields
                }
            }

        return {
            'passed': True,
            'message': f'Config valid at {config_path.name}',
            'details': {
                'path': str(config_path),
                'vault_path': config.get('vault_path')
            }
        }

    except yaml.YAMLError as e:
        return {
            'passed': False,
            'message': f'Config file invalid YAML: {str(e)[:50]}',
            'fix': 'Fix config or re-run: brainplorp setup',
            'details': {
                'path': str(config_path),
                'error': str(e)
            }
        }
    except Exception as e:
        return {
            'passed': False,
            'message': f'Config check failed: {str(e)}',
            'fix': 'Re-run: brainplorp setup'
        }


def check_vault_access(verbose: bool = False) -> Dict[str, Any]:
    """Check if Obsidian vault is accessible."""
    config_path = Path.home() / '.config' / 'brainplorp' / 'config.yaml'

    if not config_path.exists():
        return {
            'passed': False,
            'message': 'Config file not found (run brainplorp setup first)',
            'fix': 'Run: brainplorp setup'
        }

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except Exception:
        return {
            'passed': False,
            'message': 'Cannot read config file',
            'fix': 'Re-run: brainplorp setup'
        }

    vault_path = Path(config.get('vault_path', ''))

    if not vault_path:
        return {
            'passed': False,
            'message': 'Vault path not configured',
            'fix': 'Run: brainplorp setup'
        }

    if not vault_path.exists():
        return {
            'passed': False,
            'message': f'Vault not found: {vault_path}',
            'fix': 'Update vault path: brainplorp setup',
            'details': {'vault_path': str(vault_path)}
        }

    if not vault_path.is_dir():
        return {
            'passed': False,
            'message': f'Vault path is not a directory: {vault_path}',
            'fix': 'Update vault path: brainplorp setup'
        }

    # Check for typical Obsidian vault structure
    has_obsidian_dir = (vault_path / '.obsidian').exists()

    return {
        'passed': True,
        'message': f'Vault accessible at {vault_path.name}/',
        'details': {
            'vault_path': str(vault_path),
            'has_obsidian_config': has_obsidian_dir
        }
    }


def check_mcp_configuration(verbose: bool = False) -> Dict[str, Any]:
    """Check if MCP server is configured for Claude Desktop."""
    claude_config_path = (
        Path.home() / 'Library' / 'Application Support' / 'Claude' / 'claude_desktop_config.json'
    )

    if not claude_config_path.exists():
        return {
            'passed': False,
            'message': 'Claude Desktop config not found',
            'fix': 'Run: brainplorp mcp (requires Claude Desktop installed)',
            'details': {'expected_path': str(claude_config_path)}
        }

    try:
        with open(claude_config_path) as f:
            config = json.load(f)

        if 'mcpServers' not in config:
            return {
                'passed': False,
                'message': 'MCP servers section missing',
                'fix': 'Run: brainplorp mcp'
            }

        if 'brainplorp' not in config['mcpServers']:
            return {
                'passed': False,
                'message': 'brainplorp MCP server not configured',
                'fix': 'Run: brainplorp mcp',
                'details': {
                    'configured_servers': list(config['mcpServers'].keys())
                }
            }

        brainplorp_config = config['mcpServers']['brainplorp']

        return {
            'passed': True,
            'message': 'MCP server configured for Claude Desktop',
            'details': {
                'command': brainplorp_config.get('command'),
                'config_path': str(claude_config_path)
            }
        }

    except json.JSONDecodeError as e:
        return {
            'passed': False,
            'message': f'Claude Desktop config invalid JSON: {str(e)[:50]}',
            'fix': 'Fix Claude config or run: brainplorp mcp'
        }
    except Exception as e:
        return {
            'passed': False,
            'message': f'MCP config check failed: {str(e)}',
            'fix': 'Run: brainplorp mcp'
        }
```

**Register command in CLI:**

**File:** `src/brainplorp/cli.py`

```python
from brainplorp.commands.doctor import doctor

# In cli() function, add:
cli.add_command(doctor)
```

**Success Criteria:**
- ✅ `brainplorp doctor` command exists
- ✅ Detects TaskWarrior hanging (5-second timeout)
- ✅ Detects TaskWarrior 3.4.1 specifically
- ✅ Checks all critical dependencies
- ✅ Provides actionable fix instructions
- ✅ Exit code 0 if all pass, 1 if critical failures
- ✅ Verbose mode shows detailed diagnostic info

---

### Phase 3: Setup Wizard Hardening (2 hours)

**Objective:** Make setup wizard validate TaskWarrior before declaring success

#### Changes to Setup Wizard

**File:** `src/brainplorp/commands/setup.py`

**Add imports:**
```python
from brainplorp.commands.doctor import check_taskwarrior
```

**Add TaskWarrior validation step (after vault setup, before sync setup):**

```python
def run_setup():
    """Run interactive setup wizard."""
    click.echo()
    click.secho("brainplorp Setup Wizard", fg='cyan', bold=True)
    click.echo("=" * 60)
    click.echo()

    # Step 1: Vault Path
    click.echo("Step 1: Obsidian Vault")
    # ... existing vault setup code ...

    # Step 1.5: TaskWarrior Validation (NEW)
    click.echo()
    click.echo("Step 1.5: Checking TaskWarrior...")

    tw_check = check_taskwarrior(verbose=False)

    if not tw_check['passed']:
        click.echo()
        click.secho(f"  ✗ TaskWarrior issue detected:", fg='red', bold=True)
        click.echo(f"     {tw_check['message']}")
        click.echo()
        click.secho(f"  Fix:", fg='yellow', bold=True)
        click.echo(f"     {tw_check['fix']}")
        click.echo()

        # Check if it's the known 3.4.1 issue
        if '3.4.1' in tw_check.get('message', ''):
            click.secho("  ⚠ Known Issue: TaskWarrior 3.4.1 hang bug", fg='yellow', bold=True)
            click.echo("     This is an upstream TaskWarrior bug, not a brainplorp issue.")
            click.echo("     See: https://github.com/dimatosj/brainplorp#known-issues")

        click.echo()

        if click.confirm("  Continue setup anyway? (brainplorp will NOT work until TaskWarrior is fixed)", default=False):
            click.echo()
            click.secho("  ⚠ Setup continuing with known issues", fg='yellow')
            click.echo("     brainplorp commands will hang or fail until TaskWarrior is fixed.")
            click.echo()
        else:
            click.echo()
            click.secho("  Setup aborted.", fg='red')
            click.echo("  Fix TaskWarrior and run 'brainplorp setup' again.")
            click.echo()
            sys.exit(1)
    else:
        click.echo(f"  ✓ {tw_check['message']}")

    # Step 2: TaskWarrior Sync
    # ... existing sync setup code ...
```

#### Add Timeouts to TaskWarrior Integration

**File:** `src/brainplorp/integrations/taskwarrior.py`

**Add timeout wrapper:**

```python
import subprocess
from typing import List, Dict, Any

class TaskWarriorError(Exception):
    """Raised when TaskWarrior operations fail."""
    pass

class TaskWarriorTimeoutError(TaskWarriorError):
    """Raised when TaskWarrior operations timeout."""
    pass

def run_task_command(args: List[str], timeout: int = 10) -> subprocess.CompletedProcess:
    """
    Run a TaskWarrior command with timeout.

    Args:
        args: Command arguments (e.g., ['export', 'status:pending'])
        timeout: Timeout in seconds (default: 10)

    Returns:
        CompletedProcess with stdout/stderr

    Raises:
        TaskWarriorTimeoutError: If command times out
        TaskWarriorError: If command fails
    """
    try:
        result = subprocess.run(
            ['task'] + args,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            raise TaskWarriorError(
                f"TaskWarrior command failed: {' '.join(args)}\n"
                f"Error: {result.stderr}"
            )

        return result

    except subprocess.TimeoutExpired:
        raise TaskWarriorTimeoutError(
            f"TaskWarrior command timed out after {timeout}s: {' '.join(args)}\n"
            f"This may indicate TaskWarrior is hanging.\n"
            f"Try: brainplorp doctor"
        )
```

**Update all TaskWarrior calls to use wrapper:**

```python
# Before:
def get_pending_tasks():
    result = subprocess.run(['task', 'export', 'status:pending'], capture_output=True)
    return json.loads(result.stdout)

# After:
def get_pending_tasks():
    try:
        result = run_task_command(['export', 'status:pending'], timeout=10)
        return json.loads(result.stdout)
    except TaskWarriorTimeoutError as e:
        click.secho(f"✗ TaskWarrior timed out: {e}", fg='red')
        click.echo("Run 'brainplorp doctor' to diagnose the issue.")
        sys.exit(1)
    except TaskWarriorError as e:
        click.secho(f"✗ TaskWarrior error: {e}", fg='red')
        sys.exit(1)
```

**Update all commands that call TaskWarrior:**

```python
# src/brainplorp/commands/start.py
# src/brainplorp/commands/review.py
# src/brainplorp/commands/tasks.py
# src/brainplorp/workflows/daily.py
# src/brainplorp/workflows/inbox.py

# Add timeout handling to every TaskWarrior subprocess call
```

**Success Criteria:**
- ✅ Setup wizard validates TaskWarrior before completion
- ✅ User gets clear error message if TaskWarrior is broken
- ✅ All TaskWarrior subprocess calls have timeouts (10s default)
- ✅ Timeout errors provide helpful guidance ("run brainplorp doctor")
- ✅ Setup doesn't complete successfully if TaskWarrior fails

---

### Phase 4: Documentation & Communication (1.5 hours)

**Objective:** Document known issues and provide clear troubleshooting guidance

#### Update README.md

**Add Known Issues section:**

```markdown
## Known Issues

### TaskWarrior 3.4.1 Initialization Hang

**Issue:** TaskWarrior 3.4.1 (latest Homebrew version as of Oct 2025) hangs indefinitely on first initialization on some Macs.

**Symptoms:**
- `task --version` hangs indefinitely (no output, no error)
- `brainplorp start` hangs waiting for TaskWarrior
- `brainplorp doctor` shows "TaskWarrior hangs on --version"

**Cause:** This is an upstream TaskWarrior bug, not a brainplorp issue. The bug affects TaskWarrior's first-run initialization code.

**Fix:**

```bash
# Option 1: Install TaskWarrior 3.3 (recommended)
brew uninstall task
brew install task@3.3
brainplorp doctor  # Verify fix

# Option 2: Manual initialization workaround (if downgrade unavailable)
rm -rf ~/.task ~/.taskrc
echo "data.location=~/.task" > ~/.taskrc
mkdir -p ~/.task
task add "initialization task"
task 1 done
task count  # Should return 0 after deleting init task
```

**Verification:**
```bash
# Should complete in <1 second:
task --version

# Should run without hanging:
brainplorp start
```

**Status:** brainplorp Homebrew formula now pins to TaskWarrior 3.3 to avoid this issue. If you already installed with 3.4.1, follow the fix above.

**More info:** See [SPRINT_10.1_BUGS.md](Docs/sprints/SPRINT_10.1_BUGS.md) for detailed analysis.
```

#### Create Installation Troubleshooting Guide

**File:** `Docs/INSTALLATION_TROUBLESHOOTING.md`

```markdown
# Installation Troubleshooting

## Quick Diagnostics

**First step for any issue:**

```bash
brainplorp doctor
```

This runs comprehensive health checks and provides specific fix instructions for any problems detected.

---

## Common Issues

### brainplorp Commands Hang

**Symptom:** `brainplorp start` or other commands hang indefinitely with no output.

**Cause:** TaskWarrior is hanging (likely version 3.4.1 bug).

**Diagnosis:**
```bash
brainplorp doctor
# Look for: "TaskWarrior hangs on --version"
```

**Fix:**
```bash
# Downgrade TaskWarrior
brew uninstall task
brew install task@3.3

# Verify
brainplorp doctor
```

---

### Setup Says "Complete" But Nothing Works

**Symptom:** `brainplorp setup` completes successfully but `brainplorp start` fails.

**Cause:** Setup wizard didn't validate TaskWarrior functionality (fixed in v1.6.2+).

**Diagnosis:**
```bash
brainplorp doctor
```

**Fix:** Follow the specific fix instructions from `brainplorp doctor` output.

---

### "TaskWarrior not found" Error

**Symptom:** `brainplorp doctor` shows "TaskWarrior not found in PATH".

**Cause:** TaskWarrior not installed or not in PATH.

**Fix:**
```bash
# Install TaskWarrior
brew install task@3.3

# Verify
which task
task --version

# Re-run diagnostics
brainplorp doctor
```

---

### MCP Server Not Working in Claude Desktop

**Symptom:** brainplorp tools don't appear in Claude Desktop.

**Diagnosis:**
```bash
brainplorp doctor
# Look for: "MCP server" check
```

**Fix:**
```bash
# Reconfigure MCP
brainplorp mcp

# Restart Claude Desktop (important!)
# Quit Claude Desktop completely
# Reopen Claude Desktop

# In Claude Desktop, start a new conversation
# Type: list my vault folders
# Should show brainplorp tools working
```

---

## Getting Help

If `brainplorp doctor` doesn't solve your issue:

1. **Run diagnostics and save output:**
   ```bash
   brainplorp doctor > doctor_output.txt
   ```

2. **Check GitHub Issues:**
   https://github.com/dimatosj/brainplorp/issues

3. **Open a new issue with:**
   - Output from `brainplorp doctor`
   - Your macOS version
   - Installation method (Homebrew)
   - Steps to reproduce the problem

4. **Include system info:**
   ```bash
   sw_vers  # macOS version
   brew --version  # Homebrew version
   task --version  # TaskWarrior version
   brainplorp --version  # brainplorp version
   ```
```

#### Update Post-Install Message

**File:** `Formula/brainplorp.rb` (homebrew-brainplorp repo)

```ruby
def post_install
  ohai "brainplorp #{version} installed successfully!"
  ohai ""
  ohai "Next steps:"
  ohai "  1. Check system health: brainplorp doctor"
  ohai "  2. Configure brainplorp: brainplorp setup"
  ohai "  3. Configure Claude Desktop: brainplorp mcp"
  ohai "  4. Restart Claude Desktop"
  ohai ""
  ohai "Troubleshooting:"
  ohai "  • If commands hang: brainplorp doctor"
  ohai "  • TaskWarrior 3.4.1 has known issues (we use 3.3)"
  ohai "  • See: github.com/dimatosj/brainplorp#known-issues"
end
```

**Success Criteria:**
- ✅ README documents TaskWarrior 3.4.1 issue
- ✅ Installation guide has troubleshooting section
- ✅ `brainplorp doctor` command documented
- ✅ Clear instructions for getting help
- ✅ Post-install message mentions diagnostics

---

## Testing Plan

### Test Scenario 1: Fresh Install (Critical)

**Environment:** Clean Mac with no previous brainplorp or TaskWarrior installation

**Steps:**
```bash
# 1. Install brainplorp
brew tap dimatosj/brainplorp
brew install brainplorp

# 2. Verify TaskWarrior version
task --version
# Expected: 3.3.x (not 3.4.1)

# 3. Run diagnostics
brainplorp doctor
# Expected: All checks pass

# 4. Run setup
brainplorp setup
# Expected: Completes successfully with TaskWarrior validation

# 5. Test basic functionality
brainplorp tasks
brainplorp start
# Expected: Both complete in <2 seconds without hanging
```

**Success Criteria:**
- ✅ TaskWarrior 3.3 installed (not 3.4.1)
- ✅ `brainplorp doctor` passes all checks
- ✅ Setup completes successfully
- ✅ Commands work without hanging

---

### Test Scenario 2: Broken TaskWarrior Detection (Critical)

**Environment:** Mac with broken TaskWarrior 3.4.1

**Steps:**
```bash
# 1. Simulate broken TaskWarrior
brew uninstall task
brew install task@3.4  # If available

# 2. Run diagnostics
brainplorp doctor
# Expected: Detects TaskWarrior hang, provides fix instructions

# 3. Try setup
brainplorp setup
# Expected: Detects TaskWarrior issue, offers to abort

# 4. Apply fix
brew uninstall task
brew install task@3.3

# 5. Verify fix
brainplorp doctor
# Expected: All checks pass

# 6. Complete setup
brainplorp setup
# Expected: Completes successfully
```

**Success Criteria:**
- ✅ `brainplorp doctor` detects TaskWarrior 3.4.1 hang
- ✅ Clear error message with fix instructions
- ✅ Setup wizard validates TaskWarrior
- ✅ After fix, setup completes successfully

---

### Test Scenario 3: Multiple Mac Configurations

**Test Matrix:**

| Mac Type | Conda | macOS | Architecture | Expected Result |
|----------|-------|-------|--------------|-----------------|
| Mac 1    | Yes   | 15.4  | arm64        | ✅ Works        |
| Mac 2    | No    | 15.4  | arm64        | ✅ Works        |
| Mac 3    | No    | 14.x  | arm64        | ✅ Works        |
| Mac 4    | No    | 14.x  | Intel        | ✅ Works        |

**Steps (on each Mac):**
```bash
# 1. Clean install
brew uninstall brainplorp task
rm -rf ~/.task ~/.taskrc ~/.config/brainplorp

# 2. Install
brew install dimatosj/brainplorp/brainplorp

# 3. Diagnostics
brainplorp doctor

# 4. Setup
brainplorp setup

# 5. Test commands
brainplorp tasks
brainplorp start

# 6. Document results
```

**Success Criteria:**
- ✅ Works on all Mac configurations
- ✅ No hangs on conda Macs (Sprint 10 original goal)
- ✅ TaskWarrior 3.3 works consistently

---

### Test Scenario 4: Diagnostic Command Accuracy

**Steps:**
```bash
# Test 1: All checks pass
brainplorp doctor
# Expected: Exit 0, green checkmarks

# Test 2: Missing TaskWarrior
mv /opt/homebrew/bin/task /opt/homebrew/bin/task.bak
brainplorp doctor
# Expected: Exit 1, detects missing TaskWarrior, provides fix

# Test 3: Broken config
echo "invalid yaml: [" > ~/.config/brainplorp/config.yaml
brainplorp doctor
# Expected: Detects invalid YAML, provides fix

# Test 4: Missing vault
# In config.yaml, set vault_path to non-existent directory
brainplorp doctor
# Expected: Detects missing vault (non-critical warning)

# Test 5: Verbose mode
brainplorp doctor --verbose
# Expected: Shows detailed diagnostic information
```

**Success Criteria:**
- ✅ Detects all error conditions accurately
- ✅ Provides specific fix instructions for each error
- ✅ Exit codes correct (0 = pass, 1 = fail)
- ✅ Verbose mode shows useful details

---

## Success Criteria (Overall)

**Installation:**
- ✅ brainplorp installs with TaskWarrior 3.3 (not 3.4.1)
- ✅ Installation completes in <15 seconds
- ✅ Works on multiple Mac configurations

**Diagnostics:**
- ✅ `brainplorp doctor` command exists and works
- ✅ Detects TaskWarrior hangs (5-second timeout)
- ✅ Detects TaskWarrior 3.4.1 specifically
- ✅ Provides actionable fix instructions
- ✅ Checks all critical dependencies

**Setup Wizard:**
- ✅ Validates TaskWarrior before declaring success
- ✅ Aborts setup if TaskWarrior is broken
- ✅ Shows clear error messages with fixes
- ✅ All subprocess calls have timeouts

**Documentation:**
- ✅ README documents TaskWarrior 3.4.1 issue
- ✅ Troubleshooting guide complete
- ✅ Post-install message mentions diagnostics
- ✅ Clear help-seeking instructions

**Production Readiness:**
- ✅ No hangs on any Mac configuration
- ✅ Clear error messages for all failure modes
- ✅ Users can self-diagnose issues
- ✅ Unblocks Sprint 10.2 (cloud sync)

---

## Deliverables

**Code:**
- `src/brainplorp/commands/doctor.py` - Diagnostic command
- `src/brainplorp/commands/setup.py` - Updated with TaskWarrior validation
- `src/brainplorp/integrations/taskwarrior.py` - Added timeout wrapper
- All commands updated with timeout handling

**Documentation:**
- `README.md` - Known Issues section
- `Docs/INSTALLATION_TROUBLESHOOTING.md` - Comprehensive troubleshooting guide
- `Formula/brainplorp.rb` - Updated post-install message

**Testing:**
- Test results document (version matrix, multi-Mac testing)
- TaskWarrior version compatibility notes

**Homebrew:**
- Updated formula with pinned TaskWarrior 3.3
- Tested on 2+ Mac configurations

---

## Version Bump

**Current:** v1.6.1 (Sprint 10.1 - wheel distribution)
**Target:** v1.6.2 (Sprint 10.1.1 - bug fixes + diagnostics)

**Update locations:**
- `src/brainplorp/__init__.py` - `__version__ = "1.6.2"`
- `pyproject.toml` - `version = "1.6.2"`

**Rationale:** PATCH version bump (bug fixes and diagnostics, no new features)

---

## Sprint Dependencies

**Blocks:**
- Sprint 10.2 (Cloud Sync) - Cannot implement sync if TaskWarrior is broken

**Blocked By:**
- None - Can start immediately

**Recommended Order:**
1. Sprint 10.1.1 (this sprint) - Fix TaskWarrior + diagnostics
2. Sprint 10.2 (cloud sync) - Implement cloud sync wizard

---

## Effort Estimate

| Phase | Description | Hours |
|-------|-------------|-------|
| Phase 1 | TaskWarrior Version Fix | 2 |
| Phase 2 | Diagnostic Tooling (`brainplorp doctor`) | 2 |
| Phase 3 | Setup Wizard Hardening | 2 |
| Phase 4 | Documentation | 1.5 |
| **Total** | | **7.5 hours** |

---

## Risk Assessment

**Low Risk:**
- Diagnostic tooling is purely additive (no breaking changes)
- TaskWarrior version pinning is well-tested approach
- Timeout additions are safe (prevent hangs)

**Medium Risk:**
- May not find working TaskWarrior 3.x version
- Fallback: Use TaskWarrior 2.6.x (requires testing for compatibility)

**High Risk:**
- None identified

---

## Lessons Learned (Pre-emptive)

**What to avoid:**
- Don't use `depends_on "package"` without version pin
- Test external dependencies thoroughly before release
- Add diagnostics early in development

**What to replicate:**
- Timeout all subprocess calls by default
- Provide actionable error messages
- Create diagnostic tools for troubleshooting

---

## Version History

**v1.0.0 (2025-10-12):**
- Initial specification created
- Based on Sprint 10.1 bug analysis
- Comprehensive four-phase approach
- Diagnostic tooling design
- Testing plan defined
- Status: Ready for implementation

---

## Lead Engineer Questions

**Date:** 2025-10-12
**Status:** Awaiting PM/Architect Answers

### Phase 1: TaskWarrior Version Fix

**Q1 (BLOCKING):** TaskWarrior Version Availability in Homebrew
- The spec assumes we can install specific TaskWarrior versions like `task@3.3`
- **Question:** Are versioned TaskWarrior formulas actually available in Homebrew?
- **Context:** When I check `brew search task`, I only see `task` (latest) and `tasksh`
- **Impact:** If versioned formulas don't exist, we may need:
  - Option A: Create our own versioned formula in homebrew-brainplorp
  - Option B: Build TaskWarrior from source
  - Option C: Document manual downgrade process
- **Need clarification on:** What's the actual available version matrix in Homebrew?

**Q2 (HIGH):** Testing Procedure for conda Environment
- Sprint 10 original issue was hang on "conda Mac" (arm64, macOS 15.4, with conda)
- **Question:** Do I need to test inside the conda environment, or with conda just installed but not activated?
- **Context:** The test script uses system `brew` commands which would be outside conda
- **Need clarification on:** Exact test procedure for conda Mac scenario

**Q3 (MEDIUM):** Test Script File Location
- Spec provides `test_taskwarrior_version.sh` script
- **Question:** Where should this test script live in the repo?
- **Options:**
  - `scripts/test_taskwarrior_version.sh` (alongside other scripts)
  - `tests/integration/test_taskwarrior_version.sh` (with integration tests)
  - Standalone in repo root (temporary testing tool)
- **Recommendation:** `scripts/` directory for utility scripts

**Q4 (MEDIUM):** TaskWarrior Data Cleanup Safety
- Test script includes `rm -rf ~/.task ~/.taskrc`
- **Question:** Should we warn the user before running this destructive operation?
- **Context:** If someone runs this script on a production Mac with real tasks, they'll lose data
- **Recommendation:** Add confirmation prompt or document as "destructive test only"

**Q5 (LOW):** Fallback to TaskWarrior 2.6.x
- Spec mentions 2.6.2 as fallback if no 3.x works
- **Question:** Is TaskWarrior 2.6.x compatible with brainplorp?
- **Context:** We assume TaskChampion (3.x) for sync functionality
- **Need clarification on:** Do we support 2.x at all, or is 3.x required?

### Phase 2: Diagnostic Tooling

**Q6 (HIGH):** Doctor Command Import Structure
- Spec shows `from brainplorp.commands.doctor import doctor`
- **Question:** Should this be in `commands/` or at the top level like other commands?
- **Context:** Looking at existing code structure:
  - `src/brainplorp/cli.py` imports from various locations
  - Some commands are in main modules (e.g., `workflows/daily.py`)
  - Others might be in `commands/` (need to verify)
- **Recommendation:** Check existing pattern and match it

**Q7 (MEDIUM):** Doctor Command Timeout Values
- Spec uses 5-second timeout for TaskWarrior checks
- **Question:** Is 5 seconds appropriate for all TaskWarrior operations?
- **Context:**
  - `task count` on large databases might take longer
  - Sync operations definitely take longer (spec shows 10s for sync)
- **Recommendation:** Use different timeouts per operation type?
  - Version check: 5s
  - Count/export: 10s
  - Sync: 30s

**Q8 (MEDIUM):** Doctor Verbose Mode Output
- Spec includes `--verbose` flag but doesn't show what additional info is displayed
- **Question:** What should verbose mode show?
- **Options:**
  - Full command outputs (stdout/stderr)
  - Timing information per check
  - System environment details (PATH, Python version, etc.)
  - All of the above
- **Recommendation:** Show command outputs and timing at minimum

**Q9 (LOW):** Doctor Command and State Synchronization
- **Question:** Does the doctor command need to verify State Synchronization is working?
- **Context:** State Sync is a critical architectural pattern
- **Possible check:** Create test task in TaskWarrior, verify it appears in project frontmatter
- **Recommendation:** Defer to Sprint 10.1.2 (more comprehensive validation sprint)

**Q10 (LOW):** MCP Configuration Check Depth
- Spec checks if 'brainplorp' key exists in MCP config
- **Question:** Should we validate the MCP config more deeply?
- **Checks that could be added:**
  - Command path exists and is executable
  - Args array is valid
  - brainplorp-mcp entry point exists
- **Recommendation:** Basic check is sufficient for Sprint 10.1.1

### Phase 3: Setup Wizard Hardening

**Q11 (BLOCKING):** Import Statement for check_taskwarrior
- Spec shows: `from brainplorp.commands.doctor import check_taskwarrior`
- **Question:** Is this circular dependency safe?
- **Context:**
  - `setup.py` imports from `doctor.py`
  - Both are in `commands/` directory
  - If they both import from `cli.py`, could create issues
- **Recommendation:** Extract check functions to separate utility module?
  - `src/brainplorp/utils/diagnostics.py`
  - Both `doctor.py` and `setup.py` import from there

**Q12 (HIGH):** Setup Wizard Behavior on TaskWarrior Failure
- Spec shows confirmation prompt: "Continue setup anyway?"
- **Question:** Should we allow setup to continue if TaskWarrior is broken?
- **Consideration:** If user continues, they'll have:
  - Valid config file pointing to vault
  - MCP server configured
  - But brainplorp commands won't work
- **Alternative:** Always abort setup if TaskWarrior fails (stronger stance)
- **Need clarification on:** Product decision - allow continuation or enforce requirements?

**Q13 (MEDIUM):** Timeout Error Handling in Commands
- Spec shows timeout wrapper in `taskwarrior.py`
- **Question:** How should individual commands handle TaskWarriorTimeoutError?
- **Context:** Spec shows example for one command, but we have:
  - `start.py`, `review.py`, `tasks.py`, `inbox.py`, etc.
  - Daily workflows, review workflows, etc.
- **Pattern needed:** Should all commands follow the same error handling pattern?
- **Recommendation:** Create common error handler function in CLI utils

**Q14 (MEDIUM):** Refactoring Scope for Timeout Addition
- Spec says "Update all commands that call TaskWarrior"
- **Question:** How many files/functions are affected?
- **Need to audit:**
  - All direct `subprocess.run(['task', ...])` calls
  - All functions in `integrations/taskwarrior.py`
  - All workflow files that call TaskWarrior
- **Recommendation:** Do comprehensive grep to find all call sites first

**Q15 (LOW):** Timeout for Non-Critical Operations
- **Question:** Should non-critical TaskWarrior operations have longer timeouts?
- **Examples:**
  - Task export for reporting (could be 30s)
  - Sync operations (could be 60s)
  - Interactive review (could be infinite?)
- **Recommendation:** Context-specific timeouts, not global 10s default

### Phase 4: Documentation

**Q16 (MEDIUM):** Known Issues Section Location
- Spec adds Known Issues to README.md
- **Question:** Should this also be in installation docs?
- **Context:** Users might read installation guide without reading full README
- **Recommendation:** Add to both with cross-references

**Q17 (LOW):** Troubleshooting Guide Maintenance
- **Question:** Who maintains INSTALLATION_TROUBLESHOOTING.md as new issues arise?
- **Process needed:**
  - GitHub issues → documented in troubleshooting guide
  - Regular review and updates
- **Recommendation:** Add maintenance note in PM handoff docs

### Cross-Phase Questions

**Q18 (HIGH):** Test Coverage for This Sprint
- **Question:** How many new tests should be added?
- **Estimated:**
  - `test_doctor.py`: ~15 tests (one per check, plus error cases)
  - `test_setup_validation.py`: ~5 tests (TaskWarrior validation scenarios)
  - `test_taskwarrior_timeout.py`: ~8 tests (timeout scenarios)
  - **Total: ~28 new tests**
- **Need clarification on:** Are these estimates reasonable?

**Q19 (HIGH):** Manual Testing Requirements
- Spec describes 4 test scenarios requiring manual testing
- **Question:** Who performs these tests?
- **Options:**
  - Lead Engineer (me) during implementation
  - John (user) after implementation
  - Both (lead engineer smoke test, John comprehensive test)
- **Need clarification on:** Testing responsibility and timing

**Q20 (MEDIUM):** Version Bump Timing
- Target version: v1.6.2
- **Question:** When should I bump the version?
- **Options:**
  - At start of sprint (commit 1)
  - At end of sprint (final commit)
  - Before releasing to Homebrew
- **Recommendation:** End of sprint, just before release

**Q21 (MEDIUM):** Homebrew Formula Update Process
- **Question:** Do I update the Homebrew formula or does John?
- **Context:** Homebrew formula is in separate repo (homebrew-brainplorp)
- **Need clarification on:** Who has write access and who publishes the update?

**Q22 (LOW):** Sprint Dependencies on Sprint 10.2
- Spec says this sprint blocks Sprint 10.2 (Cloud Sync)
- **Question:** What specifically does Sprint 10.2 need from this sprint?
- **Assumption:** Working TaskWarrior is prerequisite for sync testing
- **Confirmation needed:** Is this the only dependency?

### Architecture Questions

**Q23 (MEDIUM):** State Synchronization Validation
- This sprint adds diagnostics but doesn't validate State Sync pattern
- **Question:** Should State Sync validation be in this sprint or deferred?
- **Consideration:**
  - This is a CRITICAL pattern (per role docs)
  - `brainplorp doctor` would be perfect place to validate it
- **Recommendation:** Add basic State Sync check to doctor command

**Q24 (LOW):** Backend Abstraction Impact
- Sprint 10 added backend abstraction layer
- **Question:** Do timeout wrappers need to be added to backend layer too?
- **Context:** If backends delegate to integrations, timeouts should propagate
- **Recommendation:** Audit backend code for timeout handling

---

## Summary of Blocking Questions

**Must be answered before implementation:**
1. **Q1:** TaskWarrior version availability in Homebrew (affects entire Phase 1)
2. **Q11:** Circular dependency concern with setup.py importing from doctor.py
3. **Q12:** Product decision on setup continuation with broken TaskWarrior

**High priority (affect implementation approach):**
4. **Q2:** conda Mac testing procedure
5. **Q6:** Doctor command module location
6. **Q13:** Error handling pattern for all commands
7. **Q19:** Manual testing responsibility
8. **Q18:** Test coverage expectations

**Can proceed without (implementation details):**
- All MEDIUM and LOW priority questions
- Can make reasonable assumptions and document decisions

---

## Proposed Next Steps After Q&A

1. **Phase 1 Start:** Only after Q1 answered (Homebrew version availability)
2. **Phase 2 Start:** After Q6 and Q11 answered (module structure)
3. **Phase 3 Start:** After Q12 and Q13 answered (error handling pattern)
4. **Phase 4 Start:** Can proceed in parallel with other phases

**Estimated time for Q&A:** 30-45 minutes for PM/Architect to review and answer

---

## PM/Architect Answers

**Date:** 2025-10-12
**Answered By:** PM/Architect
**Status:** ✅ All questions answered - Ready to proceed

### Phase 1 Answers

**A1 (BLOCKING): TaskWarrior Version Availability**

**Answer:** You're correct - Homebrew doesn't have versioned TaskWarrior formulas like `task@3.3`.

**Approach:** Create our own pinned TaskWarrior formula in the `homebrew-brainplorp` repo.

**Implementation:**
1. Copy the Homebrew core TaskWarrior formula as a baseline
2. Pin to a specific git commit/tag that works (test to find it)
3. Name it `taskwarrior-pinned.rb` in our tap
4. Update brainplorp formula to `depends_on "dimatosj/brainplorp/taskwarrior-pinned"`

**Testing approach:**
```bash
# Test TaskWarrior from different git commits
git clone https://github.com/GothenburgBitFactory/taskwarrior.git
cd taskwarrior
git checkout v3.3.0  # Try tags/commits until one works
mkdir build && cd build
cmake ..
make
./src/task --version
# Test if it hangs
```

**Fallback:** If no 3.x version works cleanly, we'll test 2.6.2 (answer in A5).

---

**A2 (HIGH): conda Mac Testing Procedure**

**Answer:** Test with conda **installed but not activated** (normal user state).

**Rationale:**
- Sprint 10's original issue was conda interfering with Python path resolution
- Wheel distribution fixed this by bundling everything
- We just need to verify TaskWarrior itself doesn't hang (independent of Python)

**Test procedure:**
```bash
# On conda Mac:
which python    # Should show Homebrew Python, not conda
which task      # Should show Homebrew TaskWarrior
echo $PATH      # Should show Homebrew before conda

# Run tests normally with system brew/task
task --version
brainplorp setup
```

**No need** to test inside activated conda environment - that's not our target use case.

---

**A3 (MEDIUM): Test Script Location**

**Answer:** `scripts/test_taskwarrior_version.sh` ✅

**Rationale:**
- It's a utility script for development/testing, not a pytest test
- Aligns with existing `scripts/` directory pattern
- Can be run manually during development

---

**A4 (MEDIUM): TaskWarrior Data Cleanup Safety**

**Answer:** Add a BIG warning comment at top of script + confirmation prompt.

**Implementation:**
```bash
#!/bin/bash
# ⚠️  WARNING: This script deletes ~/.task and ~/.taskrc
# ⚠️  Only run on a test Mac with no important tasks!

echo "⚠️  This script will DELETE ~/.task and ~/.taskrc"
echo "⚠️  All TaskWarrior data will be lost!"
read -p "Continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# ... rest of script
```

---

**A5 (LOW): TaskWarrior 2.6.x Compatibility**

**Answer:** TaskWarrior 2.x is **NOT compatible** with brainplorp. Require 3.x.

**Rationale:**
- brainplorp assumes TaskChampion (3.x) architecture
- 2.x uses flat files, 3.x uses SQLite
- Sync functionality requires TaskChampion protocol (3.x only)
- Sprint 10.2 (cloud sync) requires 3.x

**Fallback strategy if no 3.x works:**
- Find the oldest 3.x commit that works (even pre-release)
- Build from source if necessary
- Document as "experimental TaskWarrior build"

---

### Phase 2 Answers

**A6 (HIGH): Doctor Command Module Location**

**Answer:** Create new `src/brainplorp/commands/` directory pattern.

**Structure:**
```
src/brainplorp/
├── commands/
│   ├── __init__.py
│   ├── doctor.py       # NEW
│   ├── setup.py        # Existing (if not already here)
│   └── ...
├── cli.py              # Imports from commands/
```

**Import pattern:**
```python
# In cli.py
from brainplorp.commands.doctor import doctor
from brainplorp.commands.setup import setup
```

**Note:** If commands don't currently live in `commands/`, create the directory and move them there as part of this sprint (code organization improvement).

---

**A7 (MEDIUM): Doctor Command Timeout Values**

**Answer:** Use context-specific timeouts. Your recommendation is correct.

**Timeout matrix:**
- `task --version`: 5 seconds (should be instant)
- `task count`: 10 seconds (database query)
- `task export`: 15 seconds (larger output)
- `task sync init`: 30 seconds (network operation)

**Implementation:**
```python
def check_taskwarrior(verbose: bool = False) -> Dict[str, Any]:
    # Version check (5s)
    version_result = subprocess.run(['task', '--version'], timeout=5, ...)

    # Count check (10s)
    count_result = subprocess.run(['task', 'count'], timeout=10, ...)
```

---

**A8 (MEDIUM): Doctor Verbose Mode Output**

**Answer:** Show **all of the above** - command outputs, timing, and environment.

**Verbose output example:**
```
Checking TaskWarrior... ✓ 3.3.0 working (0 tasks)
  [VERBOSE] Path: /opt/homebrew/bin/task
  [VERBOSE] Version check: 0.234s
  [VERBOSE] Count check: 0.456s
  [VERBOSE] Command output:
    $ task --version
    TaskWarrior 3.3.0
```

**Keep it simple for v1.6.2** - just show command outputs and timing.

---

**A9 (LOW): State Synchronization Validation**

**Answer:** **Defer to future sprint** (10.1.2 or later). Don't add to this sprint.

**Rationale:**
- Sprint 10.1.1 is already substantial (7.5 hours)
- State Sync validation requires test task creation (side effects)
- Focus on critical diagnostics first
- Can add comprehensive validation in dedicated sprint

---

**A10 (LOW): MCP Configuration Check Depth**

**Answer:** Basic check is sufficient. ✅ Your recommendation accepted.

**What to check:**
- ✅ `claude_desktop_config.json` exists
- ✅ `mcpServers.brainplorp` key exists
- ✅ Command field is populated

**Don't validate:**
- ❌ Binary existence (PATH could change)
- ❌ Args validity (too complex, low value)

---

### Phase 3 Answers

**A11 (BLOCKING): Import Statement Circular Dependency**

**Answer:** Extract checks to `src/brainplorp/utils/diagnostics.py`. ✅ Your recommendation accepted.

**Structure:**
```python
# src/brainplorp/utils/diagnostics.py (NEW)
def check_taskwarrior(verbose: bool = False) -> Dict[str, Any]:
    """Check TaskWarrior functionality."""
    # ... implementation

def check_python_dependencies(verbose: bool = False) -> Dict[str, Any]:
    """Check Python packages."""
    # ... implementation

# And so on for all checks
```

**Usage:**
```python
# src/brainplorp/commands/doctor.py
from brainplorp.utils.diagnostics import (
    check_taskwarrior,
    check_python_dependencies,
    # ...
)

# src/brainplorp/commands/setup.py
from brainplorp.utils.diagnostics import check_taskwarrior
```

**No circular dependency** - both import from `utils/`, neither imports from each other.

---

**A12 (HIGH): Setup Wizard Behavior on Broken TaskWarrior**

**Answer:** **Always abort** if TaskWarrior is broken (stronger stance).

**Rationale:**
- brainplorp is useless without TaskWarrior
- No point in continuing setup
- User will just be frustrated when commands don't work
- Better to fail fast with clear fix instructions

**Implementation:**
```python
if not tw_check['passed']:
    click.secho(f"✗ TaskWarrior issue: {tw_check['message']}", fg='red')
    click.echo(f"Fix: {tw_check['fix']}")
    click.echo()
    click.echo("Setup cannot continue until TaskWarrior is working.")
    click.echo("Run 'brainplorp setup' again after fixing TaskWarrior.")
    sys.exit(1)  # Always abort, no confirmation prompt
```

---

**A13 (MEDIUM): Timeout Error Handling Pattern**

**Answer:** Create common error handler in `utils/`. ✅ Your recommendation accepted.

**Implementation:**
```python
# src/brainplorp/utils/taskwarrior_errors.py (NEW)
import click
import sys

def handle_taskwarrior_error(error: Exception, context: str = "TaskWarrior operation"):
    """
    Common error handler for TaskWarrior exceptions.

    Args:
        error: The exception raised
        context: Description of what was being attempted
    """
    from brainplorp.integrations.taskwarrior import TaskWarriorTimeoutError, TaskWarriorError

    if isinstance(error, TaskWarriorTimeoutError):
        click.secho(f"✗ {context} timed out", fg='red')
        click.echo(str(error))
        click.echo()
        click.echo("This usually indicates TaskWarrior is hanging.")
        click.echo("Run 'brainplorp doctor' to diagnose the issue.")
        sys.exit(1)
    elif isinstance(error, TaskWarriorError):
        click.secho(f"✗ {context} failed", fg='red')
        click.echo(str(error))
        sys.exit(1)
    else:
        raise  # Re-raise unexpected errors
```

**Usage in commands:**
```python
# In start.py, review.py, etc.
from brainplorp.utils.taskwarrior_errors import handle_taskwarrior_error
from brainplorp.integrations.taskwarrior import run_task_command, TaskWarriorTimeoutError

try:
    result = run_task_command(['export', 'status:pending'])
except (TaskWarriorTimeoutError, TaskWarriorError) as e:
    handle_taskwarrior_error(e, "Fetching tasks")
```

---

**A14 (MEDIUM): Refactoring Scope**

**Answer:** Do the audit first, document all call sites, then refactor systematically.

**Audit command:**
```bash
# Find all direct TaskWarrior subprocess calls
grep -r "subprocess.run.*task" src/

# Find all functions in taskwarrior.py
grep "^def " src/brainplorp/integrations/taskwarrior.py
```

**Expected files to update:**
- `src/brainplorp/integrations/taskwarrior.py` (all functions)
- `src/brainplorp/workflows/daily.py`
- `src/brainplorp/workflows/review.py`
- `src/brainplorp/workflows/inbox.py`
- `src/brainplorp/commands/tasks.py`
- Any MCP tool that calls TaskWarrior

**Estimate:** ~10-15 call sites total

---

**A15 (LOW): Context-Specific Timeouts**

**Answer:** Yes, use context-specific timeouts. ✅ Your recommendation accepted.

**Timeout guidelines:**
- **Quick operations** (version, status): 5s
- **Database queries** (count, export small filters): 10s
- **Large exports** (all tasks): 30s
- **Sync operations**: 60s
- **Interactive operations** (review loops): No timeout (user-driven)

**Implementation:**
```python
# Allow timeout to be specified per operation
def run_task_command(args: List[str], timeout: int = 10) -> subprocess.CompletedProcess:
    # Default 10s, but can override:
    # run_task_command(['sync'], timeout=60)
```

---

### Phase 4 Answers

**A16 (MEDIUM): Known Issues Location**

**Answer:** Add to both README and installation docs with cross-references. ✅

**README.md:**
```markdown
## Known Issues

### TaskWarrior 3.4.1 Hang
[Full description and fix]

For more troubleshooting, see [Installation Troubleshooting](Docs/INSTALLATION_TROUBLESHOOTING.md).
```

**Docs/INSTALLATION_TROUBLESHOOTING.md:**
```markdown
## Common Issues

### TaskWarrior Hangs
[Detailed troubleshooting steps]

See also: [Known Issues in README](../README.md#known-issues)
```

---

**A17 (LOW): Troubleshooting Guide Maintenance**

**Answer:** PM (you, John) maintains it during PM handoff updates.

**Process:**
1. GitHub issues → PM reviews
2. Recurring issues → Add to troubleshooting guide
3. Each sprint PM handoff → Review and update guide
4. Lead Engineer can propose additions during implementation

---

### Cross-Phase Answers

**A18 (HIGH): Test Coverage**

**Answer:** Your estimates are reasonable. Aim for ~20-25 tests.

**Priority:**
- `test_doctor.py`: ~12 tests (critical checks + error cases)
- `test_setup_validation.py`: ~5 tests (TaskWarrior validation)
- `test_taskwarrior_timeout.py`: ~5 tests (timeout scenarios)
- **Total: ~22 tests**

**Focus on:**
- Critical path tests (TaskWarrior checks, timeout detection)
- Skip exhaustive edge cases (can add later)

---

**A19 (HIGH): Manual Testing Responsibility**

**Answer:** **Both** - Lead Engineer smoke test, John comprehensive test.

**Lead Engineer during implementation:**
- Test Scenario 1: Fresh install (basic functionality)
- Test Scenario 2: Broken TaskWarrior detection (error handling)

**John (PM) after implementation:**
- Test Scenario 3: Multiple Mac configurations (real-world validation)
- Test Scenario 4: Diagnostic accuracy (comprehensive validation)

**Handoff:** Lead Engineer provides test results document, John validates on 2+ Macs.

---

**A20 (MEDIUM): Version Bump Timing**

**Answer:** **End of sprint, before final commit**. ✅ Your recommendation accepted.

**Timing:**
1. Implement all phases
2. Tests pass
3. Lead Engineer smoke test passes
4. Bump version: `__init__.py` and `pyproject.toml` → v1.6.2
5. Final commit with version bump
6. Tag release: `git tag v1.6.2 && git push --tags`

---

**A21 (MEDIUM): Homebrew Formula Update**

**Answer:** **Lead Engineer updates formula**, John reviews and publishes.

**Process:**
1. Lead Engineer: Update formula in `homebrew-brainplorp` repo
2. Lead Engineer: Open PR with changes
3. John: Review PR, test locally
4. John: Merge PR (publishes to users)

**Note:** Lead Engineer should have write access to homebrew-brainplorp repo.

---

**A22 (LOW): Sprint 10.2 Dependencies**

**Answer:** Yes, working TaskWarrior is the only blocker. ✅

**Sprint 10.2 needs:**
- TaskWarrior functional (doesn't hang)
- `brainplorp setup` works
- `task sync init` works

**Doesn't need:**
- `brainplorp doctor` (nice to have, not required)
- All timeout handling complete (only critical paths)

---

### Architecture Answers

**A23 (MEDIUM): State Synchronization Validation**

**Answer:** Defer to future sprint (same as A9).

**Rationale:**
- Not critical for v1.6.2 production readiness
- State Sync is working (no reported issues)
- Can add comprehensive validation in Sprint 10.3 or 11

---

**A24 (LOW): Backend Abstraction Timeout Handling**

**Answer:** Yes, audit backend layer for timeout propagation.

**Approach:**
1. Check if backend layer calls `integrations/taskwarrior.py`
2. If yes, timeouts should propagate automatically (our wrapper handles it)
3. If backend has direct subprocess calls, add timeouts there too

**Low priority** - likely already covered by taskwarrior.py wrapper.

---

## Revised Implementation Plan

### Unblocked - Ready to Start

**Phase 1:**
- ✅ Create pinned TaskWarrior formula approach (A1)
- ✅ Test with conda installed but not activated (A2)
- ✅ Put test script in `scripts/` (A3)
- ✅ Add safety warnings (A4)
- ✅ Require 3.x, no 2.x fallback (A5)

**Phase 2:**
- ✅ Create `commands/` directory if needed (A6)
- ✅ Extract checks to `utils/diagnostics.py` (A11)
- ✅ Use context-specific timeouts (A7)
- ✅ Verbose mode shows commands + timing (A8)
- ✅ Skip State Sync validation (A9)
- ✅ Basic MCP check only (A10)

**Phase 3:**
- ✅ Always abort setup if TaskWarrior broken (A12)
- ✅ Common error handler in `utils/` (A13)
- ✅ Audit call sites first (A14)
- ✅ Context-specific timeouts (A15)

**Phase 4:**
- ✅ Add to both README and troubleshooting doc (A16)
- ✅ PM maintains guide (A17)

**Testing:**
- ✅ ~20-25 tests (A18)
- ✅ Lead Engineer smoke test, John comprehensive test (A19)

**Process:**
- ✅ Version bump at end (A20)
- ✅ Lead Engineer updates formula, John publishes (A21)

---

## Additional Implementation Notes

### File Structure Changes

**New files to create:**
```
src/brainplorp/
├── commands/
│   └── doctor.py              # NEW
├── utils/
│   ├── diagnostics.py         # NEW (extracted checks)
│   └── taskwarrior_errors.py  # NEW (common error handling)
scripts/
└── test_taskwarrior_version.sh  # NEW (testing utility)
```

**Files to modify:**
```
src/brainplorp/
├── commands/
│   └── setup.py               # Add TaskWarrior validation
├── integrations/
│   └── taskwarrior.py         # Add timeout wrapper
├── workflows/
│   ├── daily.py               # Update TaskWarrior calls
│   ├── review.py              # Update TaskWarrior calls
│   └── inbox.py               # Update TaskWarrior calls
├── cli.py                     # Register doctor command
├── __init__.py                # Version bump to 1.6.2
pyproject.toml                 # Version bump to 1.6.2
```

### Homebrew Changes

**In `homebrew-brainplorp` repo:**
```
Formula/
├── brainplorp.rb              # Update depends_on
└── taskwarrior-pinned.rb      # NEW (pinned TaskWarrior version)
```

---

## Effort Estimate Validation

| Phase | Original | With Q&A | Notes |
|-------|----------|----------|-------|
| Phase 1 | 2h | 3h | Added formula creation |
| Phase 2 | 2h | 2h | Unchanged |
| Phase 3 | 2h | 2.5h | Added common error handler |
| Phase 4 | 1.5h | 1.5h | Unchanged |
| **Total** | **7.5h** | **9h** | More realistic with custom formula |

**Revised total effort:** 9 hours

---

## Final Status

✅ **All 24 questions answered**
✅ **No blocking issues remain**
✅ **Ready for implementation**

**Lead Engineer can now proceed with:**
1. Phase 1: TaskWarrior version fix (3 hours)
2. Phase 2: Diagnostic tooling (2 hours)
3. Phase 3: Setup wizard hardening (2.5 hours)
4. Phase 4: Documentation (1.5 hours)

**Total:** 9 hours → v1.6.2 release
