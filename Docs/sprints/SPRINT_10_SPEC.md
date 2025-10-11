# Sprint 10: Mac Installation & Multi-Computer Sync

**Version:** 1.0.0
**Status:** DRAFT - Ready for PM Review
**Created:** 2025-10-11
**Target Version:** brainplorp v1.6.0 (MINOR bump - major sprint)

---

## Overview

**Goal:** Enable Mac users to install brainplorp easily via Homebrew and use it seamlessly across multiple computers with proper TaskWarrior and Obsidian vault synchronization.

**User Needs Addressed:**
1. **Multi-Computer Sync** - Use brainplorp on 2+ Macs with full suite (MCP, tasks, notes, inbox) staying in sync
2. **Easy Installation** - Enable non-technical Mac users to install and configure brainplorp with minimal terminal knowledge
3. **Tester Onboarding** - Reduce installation from 11 manual steps to 2-3 simple commands

**What This Sprint Does NOT Include:**
- ❌ Windows or Linux support (Mac-only for Sprint 10)
- ❌ Cloud-hosted backend (client-only architecture, defer to Sprint 11+)
- ❌ GUI installer .pkg (Homebrew formula only, GUI deferred to Sprint 11)
- ❌ Obsidian REST API integration (deprioritized based on user needs)

---

## User Stories

### Story 1: Easy Installation
**As a** non-technical Mac user
**I want** to install brainplorp with 2 simple commands
**So that** I can start using it without complex setup

**Acceptance Criteria:**
- Install via `brew install brainplorp`
- Run `brainplorp setup` interactive wizard
- Working system in < 10 minutes

### Story 2: Multi-Computer Sync
**As a** brainplorp user with multiple Macs
**I want** my tasks and notes to sync automatically
**So that** I can work on any computer and see the same data

**Acceptance Criteria:**
- Task created on Computer 1 → appears on Computer 2 (via TaskChampion sync)
- Note created on Computer 1 → appears on Computer 2 (via iCloud sync)
- Config changes can be synced (via Git or manual copy)

### Story 3: Tester Onboarding
**As a** project maintainer
**I want** to give testers a simple setup guide
**So that** they can start testing without needing technical support

**Acceptance Criteria:**
- Tester receives: "Install Homebrew, run 2 commands, test features"
- Setup wizard auto-detects vault location
- MCP configuration automated
- Clear error messages if something fails

---

## Architecture Overview

### Current State (v1.5.3)
```
┌──────────────────────────────────────┐
│          brainplorp v1.5.3           │
│                                      │
│  Installation: Manual (11 steps)    │
│  ├─ Clone repo                       │
│  ├─ Install Python                   │
│  ├─ Install TaskWarrior              │
│  ├─ pip install -e .                 │
│  ├─ Manual config editing            │
│  └─ Manual MCP setup                 │
│                                      │
│  Multi-Computer: Not supported       │
│  └─ No sync documentation            │
└──────────────────────────────────────┘
```

### Target State (v1.6.0)
```
┌──────────────────────────────────────┐
│          brainplorp v1.6.0           │
│                                      │
│  Installation: Homebrew              │
│  ├─ brew install brainplorp          │
│  └─ brainplorp setup (wizard)        │
│                                      │
│  Multi-Computer: Sync Enabled        │
│  ├─ TaskWarrior → TaskChampion sync  │
│  ├─ Obsidian → iCloud Drive sync     │
│  └─ Config → Git repo sync           │
│                                      │
│  Backend: Abstracted for future      │
│  └─ Ready for cloud migration        │
└──────────────────────────────────────┘
```

---

## Phase 1: Homebrew Formula (~4 hours)

### Goal
Create a Homebrew tap that allows users to install brainplorp with `brew install brainplorp`.

### Implementation

**1.1 Create Homebrew Tap Repository**

Create new GitHub repo: `dimatosj/homebrew-brainplorp`

```ruby
# Formula/brainplorp.rb
class Brainplorp < Formula
  desc "Workflow automation for TaskWarrior + Obsidian"
  homepage "https://github.com/dimatosj/plorp"
  url "https://github.com/dimatosj/plorp/archive/refs/tags/v1.6.0.tar.gz"
  sha256 "WILL_BE_CALCULATED_ON_RELEASE"
  license "MIT"

  depends_on "python@3.11"
  depends_on "task"  # TaskWarrior 3.x

  def install
    virtualenv_install_with_resources
  end

  def post_install
    # Create config directory
    (var/"brainplorp").mkpath

    # Print setup instructions
    ohai "Installation complete! Run 'brainplorp setup' to configure."
  end

  test do
    system bin/"brainplorp", "--version"
  end
end
```

**1.2 Package brainplorp for Distribution**

Update `pyproject.toml` to support pip installation from GitHub:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "brainplorp"
version = "1.6.0"
# ... existing fields
```

**1.3 Create Release Process**

Document release workflow in `Docs/RELEASE_PROCESS.md`:

```bash
# 1. Version bump (already covered in Sprint 9)
# 2. Git tag
git tag -a v1.6.0 -m "Sprint 10: Mac Installation & Multi-Computer Sync"
git push origin v1.6.0

# 3. Create GitHub release
gh release create v1.6.0 --title "v1.6.0" --notes "See CHANGELOG.md"

# 4. Update Homebrew formula (automated via GitHub Actions or manual)
cd ../homebrew-brainplorp
# Update URL and SHA256 in Formula/brainplorp.rb
git commit -am "brainplorp 1.6.0"
git push
```

**1.4 Test Installation**

```bash
# On a clean Mac (or fresh user account)
brew tap dimatosj/brainplorp
brew install brainplorp

# Verify
brainplorp --version  # Should print: brainplorp v1.6.0
which brainplorp      # Should be in Homebrew path
task --version        # Should be installed as dependency
```

### Success Criteria (Phase 1)
- ✅ `brew tap dimatosj/brainplorp` succeeds
- ✅ `brew install brainplorp` installs brainplorp + TaskWarrior
- ✅ `brainplorp --version` prints correct version
- ✅ `brainplorp-mcp --version` prints correct version
- ✅ Installation takes < 2 minutes

---

## Phase 2: Interactive Setup Wizard (~6 hours)

### Goal
Create `brainplorp setup` command that guides users through configuration with intelligent defaults.

### Implementation

**2.1 Setup Wizard Command**

Create `src/brainplorp/commands/setup.py`:

```python
import click
import os
from pathlib import Path
import json
import yaml

@click.command()
def setup():
    """Interactive setup wizard for brainplorp."""

    click.echo("🧠 brainplorp Setup Wizard")
    click.echo("=" * 50)
    click.echo()

    config = {}

    # Step 1: Detect Obsidian vault
    click.echo("Step 1: Obsidian Vault Location")
    vault_path = detect_obsidian_vault()

    if vault_path:
        click.echo(f"  ✓ Found Obsidian vault: {vault_path}")
        use_detected = click.confirm("  Use this vault?", default=True)
        if use_detected:
            config['vault_path'] = str(vault_path)
        else:
            config['vault_path'] = click.prompt("  Enter vault path")
    else:
        click.echo("  ℹ No Obsidian vault detected")
        config['vault_path'] = click.prompt("  Enter vault path (or press Enter to skip)", default="", show_default=False)

    click.echo()

    # Step 2: TaskWarrior sync configuration
    click.echo("Step 2: TaskWarrior Sync")
    click.echo("  For multi-computer sync, TaskWarrior needs a TaskChampion server.")
    setup_sync = click.confirm("  Configure TaskWarrior sync now?", default=True)

    if setup_sync:
        click.echo()
        click.echo("  TaskChampion Server Options:")
        click.echo("    1. Self-hosted (you run the server)")
        click.echo("    2. Cloud-hosted (recommended for testing)")
        click.echo("    3. Skip for now")

        choice = click.prompt("  Choose option", type=click.IntRange(1, 3), default=2)

        if choice == 1:
            config['taskwarrior_sync'] = {
                'enabled': True,
                'server_url': click.prompt("  Enter server URL")
            }
        elif choice == 2:
            # TODO: Provide default cloud server once we have one
            click.echo("  ℹ Cloud server setup will be available in next release")
            config['taskwarrior_sync'] = {'enabled': False}
        else:
            config['taskwarrior_sync'] = {'enabled': False}

    click.echo()

    # Step 3: Default editor
    click.echo("Step 3: Default Text Editor")
    config['default_editor'] = click.prompt("  Editor for notes", default="vim")

    click.echo()

    # Step 4: Email inbox (optional)
    click.echo("Step 4: Email Inbox (Optional)")
    setup_email = click.confirm("  Configure email inbox capture?", default=False)

    if setup_email:
        config['email'] = {
            'enabled': True,
            'imap_server': 'imap.gmail.com',
            'imap_port': 993,
            'username': click.prompt("  Gmail address"),
            'password': click.prompt("  Gmail App Password", hide_input=True),
            'inbox_label': click.prompt("  Gmail label (or INBOX)", default="INBOX"),
            'fetch_limit': 20
        }
    else:
        config['email'] = {'enabled': False}

    click.echo()

    # Step 5: Save configuration
    click.echo("Step 5: Save Configuration")
    config_path = Path.home() / '.config' / 'brainplorp' / 'config.yaml'
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    click.echo(f"  ✓ Config saved to {config_path}")
    click.echo()

    # Step 6: Configure Claude Desktop MCP
    click.echo("Step 6: Claude Desktop MCP Configuration")
    setup_mcp = click.confirm("  Configure MCP for Claude Desktop?", default=True)

    if setup_mcp:
        configure_mcp()

    click.echo()
    click.echo("=" * 50)
    click.echo("✅ Setup complete!")
    click.echo()
    click.echo("Next steps:")
    click.echo("  1. Run 'brainplorp start' to create your first daily note")
    click.echo("  2. Open Claude Desktop to use MCP tools")
    click.echo("  3. See 'brainplorp --help' for all commands")
    click.echo()


def detect_obsidian_vault() -> Path | None:
    """Detect Obsidian vault in standard locations."""

    # Check iCloud Drive
    icloud_path = Path.home() / 'Library' / 'Mobile Documents' / 'iCloud~md~obsidian'
    if icloud_path.exists():
        # Find first vault folder
        for item in icloud_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                return item

    # Check local Documents
    docs_vaults = Path.home() / 'Documents' / 'Obsidian Vaults'
    if docs_vaults.exists():
        for item in docs_vaults.iterdir():
            if item.is_dir() and (item / '.obsidian').exists():
                return item

    # Check common locations
    for location in [
        Path.home() / 'vault',
        Path.home() / 'Obsidian',
        Path.home() / 'Documents' / 'vault'
    ]:
        if location.exists() and (location / '.obsidian').exists():
            return location

    return None


def configure_mcp():
    """Configure Claude Desktop MCP integration."""

    claude_config_path = Path.home() / 'Library' / 'Application Support' / 'Claude' / 'claude_desktop_config.json'

    if not claude_config_path.exists():
        click.echo("  ℹ Claude Desktop config not found")
        click.echo(f"    Expected location: {claude_config_path}")
        click.echo("    Install Claude Desktop first, then run 'brainplorp setup' again")
        return

    # Read existing config
    with open(claude_config_path, 'r') as f:
        claude_config = json.load(f)

    # Get brainplorp-mcp path
    brainplorp_mcp_path = which_command('brainplorp-mcp')

    if not brainplorp_mcp_path:
        click.echo("  ⚠ brainplorp-mcp command not found")
        return

    # Add or update brainplorp server
    if 'mcpServers' not in claude_config:
        claude_config['mcpServers'] = {}

    claude_config['mcpServers']['brainplorp'] = {
        'command': str(brainplorp_mcp_path),
        'args': [],
        'env': {}
    }

    # Backup existing config
    backup_path = claude_config_path.parent / 'claude_desktop_config.json.backup'
    if claude_config_path.exists():
        import shutil
        shutil.copy2(claude_config_path, backup_path)
        click.echo(f"  ℹ Backed up existing config to {backup_path}")

    # Write updated config
    with open(claude_config_path, 'w') as f:
        json.dump(claude_config, f, indent=2)

    click.echo("  ✓ Claude Desktop MCP configured")
    click.echo("    Restart Claude Desktop to load brainplorp tools")


def which_command(cmd: str) -> Path | None:
    """Find command in PATH."""
    import shutil
    result = shutil.which(cmd)
    return Path(result) if result else None
```

**2.2 Add to CLI**

Update `src/brainplorp/cli.py`:

```python
from brainplorp.commands.setup import setup

cli.add_command(setup)
```

**2.3 Validation Command**

Add `brainplorp config validate` to check configuration:

```python
@cli.command()
def validate():
    """Validate brainplorp configuration."""

    config = load_config()
    errors = []
    warnings = []

    # Check vault path
    if not config.vault_path.exists():
        errors.append(f"Vault path does not exist: {config.vault_path}")
    elif not (config.vault_path / '.obsidian').exists():
        warnings.append(f"Not an Obsidian vault (missing .obsidian): {config.vault_path}")

    # Check TaskWarrior
    if not which_command('task'):
        errors.append("TaskWarrior not installed (run: brew install task)")

    # Check MCP configuration
    claude_config_path = Path.home() / 'Library' / 'Application Support' / 'Claude' / 'claude_desktop_config.json'
    if claude_config_path.exists():
        with open(claude_config_path, 'r') as f:
            claude_config = json.load(f)

        if 'brainplorp' not in claude_config.get('mcpServers', {}):
            warnings.append("brainplorp MCP server not configured in Claude Desktop")
    else:
        warnings.append("Claude Desktop not installed or not configured")

    # Print results
    if errors:
        click.secho("❌ Configuration Errors:", fg='red', bold=True)
        for error in errors:
            click.echo(f"  • {error}")

    if warnings:
        click.secho("⚠️  Warnings:", fg='yellow', bold=True)
        for warning in warnings:
            click.echo(f"  • {warning}")

    if not errors and not warnings:
        click.secho("✅ Configuration valid!", fg='green', bold=True)

    return 0 if not errors else 1
```

### Success Criteria (Phase 2)
- ✅ `brainplorp setup` runs without errors
- ✅ Wizard detects Obsidian vault in iCloud Drive
- ✅ Config file created at `~/.config/brainplorp/config.yaml`
- ✅ MCP configuration added to Claude Desktop (if installed)
- ✅ `brainplorp config validate` reports success or specific errors
- ✅ Non-technical user can complete wizard in < 5 minutes

---

## Phase 3: Multi-Computer Setup Guide (~3 hours)

### Goal
Document the complete process for using brainplorp across multiple Macs with proper sync.

### Implementation

**3.1 Create MULTI_COMPUTER_SETUP.md**

```markdown
# Multi-Computer Setup Guide for brainplorp

This guide shows you how to use brainplorp on multiple Macs with full synchronization.

## Prerequisites

- 2+ Mac computers
- Homebrew installed on each Mac
- iCloud account (for vault sync)
- Internet connection

## Architecture

brainplorp syncs via three mechanisms:

1. **TaskWarrior tasks** → TaskChampion sync server
2. **Obsidian vault** → iCloud Drive
3. **brainplorp config** → Git repository (optional)

## Setup Steps

### Computer 1 (Primary Setup)

#### Step 1: Install brainplorp

\`\`\`bash
brew tap dimatosj/brainplorp
brew install brainplorp
\`\`\`

#### Step 2: Run Setup Wizard

\`\`\`bash
brainplorp setup
\`\`\`

Follow prompts to configure:
- Obsidian vault location (should be in iCloud)
- TaskWarrior sync server
- Optional: Email inbox

#### Step 3: Move Vault to iCloud (if needed)

If your Obsidian vault is not in iCloud:

1. Open Obsidian
2. Settings → Files & Links → "Open another vault"
3. Create new vault in iCloud location:
   \`~/Library/Mobile Documents/iCloud~md~obsidian/YourVaultName\`
4. Copy notes from old vault to new vault
5. Update config: \`brainplorp setup\` (re-run to update vault path)

#### Step 4: Configure TaskChampion Sync

**Option A: Self-Hosted Server**

\`\`\`bash
# On a server or always-on computer
cargo install taskchampion-sync-server
taskchampion-sync-server --port 8080
\`\`\`

**Option B: Cloud-Hosted Server**

Use a service like Railway, Render, or Fly.io to host the server.

**Configure TaskWarrior:**

\`\`\`bash
task config sync.server.url https://your-server.com
task config sync.server.client_id $(uuidgen)
task sync init
\`\`\`

#### Step 5: Test Everything

\`\`\`bash
# Create test task
brainplorp tasks

# Verify vault is in iCloud
ls ~/Library/Mobile\\ Documents/iCloud~md~obsidian/

# Validate config
brainplorp config validate
\`\`\`

---

### Computer 2 (Secondary Setup)

#### Step 1: Wait for iCloud Sync

Ensure iCloud has synced your Obsidian vault:

\`\`\`bash
ls ~/Library/Mobile\\ Documents/iCloud~md~obsidian/
# Should see your vault folder
\`\`\`

#### Step 2: Install brainplorp

\`\`\`bash
brew tap dimatosj/brainplorp
brew install brainplorp
\`\`\`

#### Step 3: Run Setup Wizard

\`\`\`bash
brainplorp setup
\`\`\`

**Important:** Use the SAME TaskChampion sync server URL as Computer 1.

#### Step 4: Sync TaskWarrior

\`\`\`bash
task sync init
task sync
\`\`\`

All tasks from Computer 1 should now appear.

#### Step 5: Verify Sync

\`\`\`bash
# List tasks (should match Computer 1)
brainplorp tasks

# Create a test task
task add "Test from Computer 2"

# Sync
task sync

# On Computer 1, run: task sync
# Task should appear on Computer 1
\`\`\`

---

## Sync Workflows

### Daily Sync Routine

**On any computer:**

\`\`\`bash
# Before starting work
task sync            # Pull tasks from server

# Do your work
brainplorp start
# ... work in Obsidian, complete tasks ...

# After finishing work
task sync            # Push tasks to server
\`\`\`

**iCloud vault syncs automatically** - no manual action needed.

### Conflict Resolution

**TaskWarrior Conflicts:**

TaskChampion handles conflicts automatically using operational transforms. If both computers modify the same task offline, sync will merge changes intelligently.

**Obsidian Conflicts:**

iCloud creates conflict files if both computers edit the same note offline:
- Original: \`note.md\`
- Conflict: \`note (conflicted copy 2025-10-11).md\`

Manually merge or delete conflict files.

### Troubleshooting

**Tasks not syncing:**

\`\`\`bash
# Check sync status
task sync

# Verify server URL
task config sync.server.url

# Re-initialize if needed
task sync init
\`\`\`

**Vault not syncing:**

1. Check iCloud sync status: System Settings → Apple ID → iCloud → iCloud Drive
2. Verify Obsidian vault is in iCloud path
3. Wait a few minutes - iCloud can be slow

**Config out of sync:**

Option 1: Manual copy
\`\`\`bash
# Computer 1
cat ~/.config/brainplorp/config.yaml

# Computer 2 (paste config)
vim ~/.config/brainplorp/config.yaml
\`\`\`

Option 2: Git sync (advanced)
\`\`\`bash
# Put config in Git repo
cd ~/.config/brainplorp
git init
git add config.yaml
git commit -m "Initial config"
git remote add origin https://github.com/yourusername/brainplorp-config.git
git push -u origin main

# On Computer 2
cd ~/.config/brainplorp
git clone https://github.com/yourusername/brainplorp-config.git .
\`\`\`

---

## Advanced: 3+ Computers

Same process - just repeat Computer 2 steps for each additional computer.

All computers share:
- Same TaskChampion sync server
- Same iCloud vault
- Same (or similar) config

---

## Security Considerations

**TaskWarrior Sync:**
- Use HTTPS for sync server URL
- Keep client_id private (don't commit to Git)

**iCloud Vault:**
- Encrypted by Apple
- Subject to Apple's privacy policy

**Config Files:**
- Contains Gmail App Password (if configured)
- Don't commit config to public Git repos
- Use environment variables for sensitive data

---

## FAQ

**Q: Can I use Obsidian Sync instead of iCloud?**
A: Yes! brainplorp works with any vault sync method. Just ensure vault path is synced across computers.

**Q: Can I have different configs on each computer?**
A: Yes, but you'll need to maintain them separately. Vault path can differ if using different sync methods.

**Q: Does brainplorp work offline?**
A: Yes. TaskWarrior and Obsidian work offline. Sync when you regain internet connection.

**Q: Can I use brainplorp on iPad/iPhone?**
A: Not yet. Sprint 10 is Mac-only. Mobile support planned for future sprints.
\`\`\`

**3.2 Update README.md**

Add multi-computer section to main README:

```markdown
## Multi-Computer Usage

brainplorp works seamlessly across multiple Macs. See [MULTI_COMPUTER_SETUP.md](Docs/MULTI_COMPUTER_SETUP.md) for detailed instructions.

**Quick setup:**
1. Computer 1: `brew install brainplorp` → `brainplorp setup`
2. Set up iCloud vault sync and TaskChampion server
3. Computer 2: `brew install brainplorp` → `brainplorp setup` (use same sync server)
4. Both computers stay in sync automatically
```

**3.3 Create Tester Onboarding Doc**

`Docs/TESTER_GUIDE.md`:

```markdown
# brainplorp Tester Guide

Thank you for testing brainplorp! This guide will get you up and running.

## Quick Start (5 minutes)

### Step 1: Install Homebrew (if needed)

If you don't have Homebrew:

\`\`\`bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
\`\`\`

### Step 2: Install brainplorp

\`\`\`bash
brew tap dimatosj/brainplorp
brew install brainplorp
\`\`\`

### Step 3: Setup

\`\`\`bash
brainplorp setup
\`\`\`

Answer the questions - it's okay to skip optional features.

### Step 4: Test It Works

\`\`\`bash
brainplorp --version
brainplorp tasks
\`\`\`

## What to Test

### Core Workflows

1. **Daily Start**
   \`\`\`bash
   brainplorp start
   \`\`\`
   - Does it create a daily note?
   - Are tasks listed correctly?

2. **Task Management**
   \`\`\`bash
   brainplorp tasks
   brainplorp tasks --urgent
   \`\`\`
   - Do task queries work?
   - Is output readable?

3. **MCP Integration** (if you use Claude Desktop)
   - Open Claude Desktop
   - Try slash commands: \`/tasks\`, \`/urgent\`, \`/start\`
   - Do tools work?

### Bugs to Report

- Installation errors
- Setup wizard confusion
- Commands that don't work
- Unclear error messages
- Missing features you expected

### How to Report

Create GitHub issue with:
- What you tried
- What happened
- What you expected
- Error messages (if any)

## Need Help?

- GitHub Issues: https://github.com/dimatosj/plorp/issues
- Email: [your-email]
\`\`\`

### Success Criteria (Phase 3)
- ✅ MULTI_COMPUTER_SETUP.md covers all scenarios
- ✅ TESTER_GUIDE.md is beginner-friendly
- ✅ README.md links to multi-computer docs
- ✅ Docs tested by following them exactly on 2 Macs

---

## Phase 4: Backend Abstraction Layer (~5 hours)

### Goal
Refactor TaskWarrior and Obsidian integrations to use abstract interfaces, making future cloud backend migration easier.

**Why Now:**
- Sprint 10 keeps client-only architecture
- But user wants cloud option in future (Sprint 11+)
- Refactoring now = easier migration later
- No behavior change for users

### Implementation

**4.1 TaskWarrior Backend Protocol**

Create `src/brainplorp/core/backends/task_backend.py`:

```python
from typing import Protocol, List, Optional
from brainplorp.core.types import Task

class TaskBackend(Protocol):
    """Abstract interface for task storage."""

    def create_task(
        self,
        description: str,
        project: Optional[str] = None,
        due: Optional[str] = None,
        priority: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """Create a task and return its UUID."""
        ...

    def get_tasks(self, filters: List[str]) -> List[Task]:
        """Query tasks with filters."""
        ...

    def mark_done(self, uuid: str) -> bool:
        """Mark task as complete."""
        ...

    def delete_task(self, uuid: str) -> bool:
        """Delete a task."""
        ...

    def modify_task(self, uuid: str, **changes) -> bool:
        """Modify task attributes."""
        ...

    def get_task_info(self, uuid: str) -> Optional[Task]:
        """Get task details by UUID."""
        ...
```

**4.2 Local TaskWarrior Backend (Current Implementation)**

Create `src/brainplorp/core/backends/local_taskwarrior.py`:

```python
import subprocess
import json
from typing import List, Optional
from .task_backend import TaskBackend
from brainplorp.core.types import Task

class LocalTaskWarriorBackend:
    """TaskWarrior backend using local subprocess calls."""

    def __init__(self):
        self.command_prefix = ['task']

    def create_task(
        self,
        description: str,
        project: Optional[str] = None,
        due: Optional[str] = None,
        priority: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """Create a task using task CLI."""
        cmd = self.command_prefix + ['add', description]

        if project:
            cmd.append(f'project:{project}')
        if due:
            cmd.append(f'due:{due}')
        if priority:
            cmd.append(f'priority:{priority}')
        if tags:
            for tag in tags:
                cmd.append(f'+{tag}')

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Task creation failed: {result.stderr}")

        # Extract UUID from output
        # (existing logic from integrations/taskwarrior.py)
        ...

        return uuid

    def get_tasks(self, filters: List[str]) -> List[Task]:
        """Query tasks using task export."""
        cmd = self.command_prefix + filters + ['export']
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return []

        tasks = json.loads(result.stdout)
        return tasks

    # ... implement other methods similarly
```

**4.3 Obsidian Backend Protocol**

Create `src/brainplorp/core/backends/vault_backend.py`:

```python
from typing import Protocol, List, Optional
from pathlib import Path
from brainplorp.core.types import NoteContent, NoteInfo

class VaultBackend(Protocol):
    """Abstract interface for note storage."""

    def read_note(self, path: str, mode: str = "full") -> NoteContent:
        """Read a note."""
        ...

    def read_folder(
        self,
        folder: str,
        filter_by: Optional[dict] = None
    ) -> List[NoteInfo]:
        """List notes in a folder."""
        ...

    def create_note(
        self,
        folder: str,
        title: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> str:
        """Create a new note."""
        ...

    def append_to_note(self, path: str, content: str) -> bool:
        """Append content to a note."""
        ...

    def update_section(
        self,
        path: str,
        header: str,
        content: str
    ) -> bool:
        """Update a section in a note."""
        ...
```

**4.4 Local Obsidian Backend (Current Implementation)**

Create `src/brainplorp/core/backends/local_obsidian.py`:

```python
from pathlib import Path
from typing import List, Optional
from .vault_backend import VaultBackend
from brainplorp.core.types import NoteContent, NoteInfo

class LocalObsidianBackend:
    """Obsidian backend using filesystem operations."""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path

    def read_note(self, path: str, mode: str = "full") -> NoteContent:
        """Read note from filesystem."""
        full_path = self.vault_path / path

        if not full_path.exists():
            raise FileNotFoundError(f"Note not found: {path}")

        content = full_path.read_text(encoding='utf-8')

        # (existing logic from integrations/obsidian_notes.py)
        ...

        return note_content

    # ... implement other methods similarly
```

**4.5 Update Core Modules to Use Backends**

Modify `src/brainplorp/config.py`:

```python
from brainplorp.core.backends.local_taskwarrior import LocalTaskWarriorBackend
from brainplorp.core.backends.local_obsidian import LocalObsidianBackend

class Config:
    def __init__(self):
        # ... existing config loading

        # Initialize backends
        self.task_backend = self._init_task_backend()
        self.vault_backend = self._init_vault_backend()

    def _init_task_backend(self):
        """Initialize TaskWarrior backend."""
        backend_type = self.config_data.get('task_backend', 'local')

        if backend_type == 'local':
            return LocalTaskWarriorBackend()
        # Future: elif backend_type == 'cloud': return CloudTaskBackend()
        else:
            raise ValueError(f"Unknown task backend: {backend_type}")

    def _init_vault_backend(self):
        """Initialize vault backend."""
        backend_type = self.config_data.get('vault_backend', 'local')

        if backend_type == 'local':
            return LocalObsidianBackend(self.vault_path)
        # Future: elif backend_type == 'cloud': return CloudVaultBackend()
        else:
            raise ValueError(f"Unknown vault backend: {backend_type}")
```

Update core modules (`daily.py`, `tasks.py`, etc.) to use `config.task_backend` and `config.vault_backend` instead of calling integration functions directly.

**4.6 Tests for Backend Abstraction**

```python
# tests/test_backends/test_task_backend.py

def test_local_taskwarrior_backend_create():
    backend = LocalTaskWarriorBackend()
    uuid = backend.create_task("Test task", project="test")
    assert uuid

    # Verify task exists
    tasks = backend.get_tasks(["project:test"])
    assert any(t['uuid'] == uuid for t in tasks)

def test_backend_protocol_compliance():
    """Ensure backend implements all required methods."""
    backend = LocalTaskWarriorBackend()

    # Check protocol compliance
    assert callable(backend.create_task)
    assert callable(backend.get_tasks)
    assert callable(backend.mark_done)
    # ... etc
```

### Success Criteria (Phase 4)
- ✅ Backend protocols defined with clear interfaces
- ✅ Local backends implement all protocol methods
- ✅ Core modules refactored to use backends
- ✅ All existing tests pass (no behavior change)
- ✅ Future cloud backend can be added by implementing protocols
- ✅ Config supports `task_backend: local` (extensible to `cloud`)

---


---

**Note:** For Success Criteria, Technical Q&A, Implementation Checklist, and Appendices, see `SPRINT_10_APPENDIX.md`.

**End of SPRINT_10_SPEC.md**
