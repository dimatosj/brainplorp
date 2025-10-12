# Sprint 10.3: Vault Sync via Git Automation

**Created:** 2025-10-12
**Status:** 📋 READY FOR IMPLEMENTATION
**Sprint Type:** Major Feature (MINOR version increment)
**Target Version:** v1.7.0
**Estimated Effort:** 6 hours
**Dependencies:** Sprint 10.2 (Cloud Sync) must be complete

---

## Executive Summary

Implement automatic vault synchronization across multiple computers using Git as the sync protocol. Users get one-command sync (`brainplorp vault sync`) that handles all Git operations automatically - no Git knowledge required.

**Key Philosophy:** brainplorp manages Git, not the user. Users never touch Git directly.

**Sync Scope:** Only brainplorp-managed directories (selective sync):
- `vault/daily/` - Daily notes
- `vault/inbox/` - Monthly inbox files
- `vault/notes/` - brainplorp-created notes

**Why Git?**
- ✅ No Obsidian plugins required
- ✅ Selective sync (don't sync entire vault)
- ✅ Version history built-in
- ✅ Smart conflict resolution
- ✅ Standard protocol (works anywhere)
- ✅ Server integration (programmatic access on Fly.io)
- ✅ Expandable (add more directories as brainplorp grows)

**User Experience:**

```bash
# Computer 1 (first time)
$ brainplorp vault sync
📦 Initializing vault sync...
✓ Vault Git repository created
✓ Connected to sync server
✓ Synced 3 daily notes, 2 inbox files
🎉 Vault sync complete!

# Computer 2 (first time)
$ brainplorp vault sync
📦 Downloading vault from server...
✓ Downloaded 5 files from server
✓ Vault sync complete!

# Daily usage (any computer)
$ brainplorp vault sync
📦 Syncing vault...
✓ Uploaded 1 new file
✓ Downloaded 2 updated files
✓ Vault sync complete! (Last sync: 3 hours ago)
```

---

## Problem Statement

### Current Pain Points

**Manual Sync is Error-Prone:**
- Users must remember to sync vault manually via iCloud/Dropbox/Git
- No conflict resolution built-in
- Risk of data loss if files conflict
- No visibility into what changed

**Obsidian Sync is Paid:**
- $8/month per user
- Not self-hostable
- Syncs entire vault (brainplorp only needs selective sync)

**Obsidian Git Plugin Requires Expertise:**
- Users must know Git
- Manual conflict resolution
- Not suitable for non-technical users
- Plugin maintenance (can break with Obsidian updates)

### Success Criteria

1. **One-Command Sync:** `brainplorp vault sync` handles everything
2. **Automatic Conflict Resolution:** Smart merge strategies for common conflicts
3. **Selective Sync:** Only sync brainplorp-managed directories
4. **No Git Knowledge Required:** Users never see Git commands or errors
5. **Integrated with Setup:** Vault sync configured during `brainplorp setup`
6. **Works Offline:** Queue changes, sync when online
7. **Clear Status:** Show last sync time, pending changes

---

## Architecture

### Git-Based Sync Model

```
┌─────────────────────────────────────────┐
│  brainplorp Sync Server (Fly.io)        │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ Bare Git Repository               │ │
│  │                                   │ │
│  │  vault/                           │ │
│  │  ├── daily/                       │ │
│  │  ├── inbox/                       │ │
│  │  └── notes/                       │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Accessible via SSH: git@server:vault  │
└─────────────────────────────────────────┘
                    ▲
                    │ git push/pull
        ┌───────────┴───────────┐
        │                       │
┌───────▼─────────┐   ┌─────────▼───────┐
│   Computer 1    │   │   Computer 2    │
│                 │   │                 │
│  Obsidian Vault │   │  Obsidian Vault │
│  (full vault)   │   │  (full vault)   │
│                 │   │                 │
│  .git/ (hidden) │   │  .git/ (hidden) │
│  ├── daily/  ✓  │   │  ├── daily/  ✓  │
│  ├── inbox/  ✓  │   │  ├── inbox/  ✓  │
│  ├── notes/  ✓  │   │  ├── notes/  ✓  │
│  └── other/  ✗  │   │  └── other/  ✗  │
│    (not synced) │   │    (not synced) │
└─────────────────┘   └─────────────────┘
```

### Selective Sync via .gitignore

brainplorp creates `.gitignore` in vault root:

```gitignore
# brainplorp vault sync - only sync managed directories
# Generated by brainplorp v1.7.0

# Sync these directories (brainplorp-managed)
!daily/
!inbox/
!notes/

# Ignore everything else
/*
!.gitignore
!README_SYNC.md

# Obsidian metadata (never sync)
.obsidian/
.trash/
```

**Result:** Only `daily/`, `inbox/`, `notes/` are versioned and synced.

### Conflict Resolution Strategy

**Common Conflict Scenarios:**

1. **Same file modified on two computers** (e.g., today's daily note)
   - **Strategy:** Use Git's merge tool with "theirs" preference for metadata, "ours" for content
   - **Fallback:** Create conflict copy: `YYYY-MM-DD.conflicted-TIMESTAMP.md`

2. **Task added in daily note on Computer 1, task deleted via review on Computer 2**
   - **Strategy:** Deletion wins (TaskWarrior is source of truth for tasks)
   - **Implementation:** Before sync, regenerate daily note from TaskWarrior

3. **Inbox file modified simultaneously**
   - **Strategy:** Merge additions (new inbox items never conflict)
   - **Implementation:** Parse both versions, combine unprocessed items

**Conflict Resolution Flow:**

```python
def resolve_conflict(file_path: str) -> str:
    """
    Resolve Git conflict for brainplorp-managed file.

    Strategy:
    1. Daily notes: Regenerate from TaskWarrior (source of truth)
    2. Inbox files: Merge unprocessed items from both versions
    3. Notes: Create conflict copy, let user choose
    """
    if file_path.startswith('daily/'):
        return regenerate_daily_note(file_path)

    elif file_path.startswith('inbox/'):
        return merge_inbox_items(file_path)

    elif file_path.startswith('notes/'):
        return create_conflict_copy(file_path)

    else:
        raise ValueError(f"Unknown file type: {file_path}")
```

---

## Implementation Plan

### Phase 1: Git Repository Setup (2 hours)

**1.1: Git Initialization**

Create `src/brainplorp/integrations/git.py`:

```python
"""
Git integration for vault sync.

This module wraps Git operations to provide user-friendly vault sync.
Users never interact with Git directly - brainplorp handles everything.
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from rich.console import Console

console = Console()


class GitError(Exception):
    """Base exception for Git operations."""
    pass


class GitConflictError(GitError):
    """Raised when Git conflict cannot be automatically resolved."""
    pass


def git_init(vault_path: Path) -> None:
    """
    Initialize Git repository in vault.

    Creates:
    - .git/ directory
    - .gitignore (selective sync rules)
    - README_SYNC.md (explains what's synced)
    - Initial commit
    """
    # Check if already initialized
    if (vault_path / '.git').exists():
        return

    # Initialize repo
    subprocess.run(
        ['git', 'init'],
        cwd=vault_path,
        check=True,
        capture_output=True
    )

    # Create .gitignore for selective sync
    gitignore_content = """# brainplorp vault sync - only sync managed directories
# Generated by brainplorp v1.7.0

# Sync these directories (brainplorp-managed)
!daily/
!inbox/
!notes/

# Ignore everything else
/*
!.gitignore
!README_SYNC.md

# Obsidian metadata (never sync)
.obsidian/
.trash/
"""
    (vault_path / '.gitignore').write_text(gitignore_content)

    # Create README
    readme_content = """# brainplorp Vault Sync

This vault is synced via brainplorp's Git-based sync system.

## What's Synced

- `daily/` - Daily notes generated by brainplorp
- `inbox/` - Monthly inbox files
- `notes/` - Notes created by brainplorp

## What's NOT Synced

- Other directories (your personal notes, attachments, etc.)
- Obsidian settings (`.obsidian/`)
- Trash (`.trash/`)

## How to Sync

Run `brainplorp vault sync` to sync your vault across computers.

## Conflicts

brainplorp automatically resolves most conflicts. If manual resolution
is needed, you'll see a `.conflicted-TIMESTAMP.md` file.
"""
    (vault_path / 'README_SYNC.md').write_text(readme_content)

    # Initial commit
    subprocess.run(
        ['git', 'add', '.gitignore', 'README_SYNC.md'],
        cwd=vault_path,
        check=True,
        capture_output=True
    )

    subprocess.run(
        ['git', 'commit', '-m', 'Initialize brainplorp vault sync'],
        cwd=vault_path,
        check=True,
        capture_output=True
    )


def git_add_remote(vault_path: Path, remote_url: str) -> None:
    """
    Add remote Git server.

    Args:
        vault_path: Path to vault
        remote_url: Git remote URL (e.g., ssh://git@server/vault)
    """
    # Check if remote already exists
    result = subprocess.run(
        ['git', 'remote', 'get-url', 'origin'],
        cwd=vault_path,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        # Remote exists, update URL
        subprocess.run(
            ['git', 'remote', 'set-url', 'origin', remote_url],
            cwd=vault_path,
            check=True,
            capture_output=True
        )
    else:
        # Add new remote
        subprocess.run(
            ['git', 'remote', 'add', 'origin', remote_url],
            cwd=vault_path,
            check=True,
            capture_output=True
        )


def git_status(vault_path: Path) -> Tuple[int, int, bool]:
    """
    Get vault sync status.

    Returns:
        (pending_changes, unsynced_commits, needs_pull)
    """
    # Check for uncommitted changes
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        cwd=vault_path,
        capture_output=True,
        text=True,
        check=True
    )
    pending_changes = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0

    # Check for unpushed commits
    result = subprocess.run(
        ['git', 'rev-list', '--count', 'origin/master..HEAD'],
        cwd=vault_path,
        capture_output=True,
        text=True,
        check=True
    )
    unsynced_commits = int(result.stdout.strip()) if result.stdout.strip() else 0

    # Check if remote has new commits
    subprocess.run(
        ['git', 'fetch', 'origin'],
        cwd=vault_path,
        capture_output=True,
        check=True
    )

    result = subprocess.run(
        ['git', 'rev-list', '--count', 'HEAD..origin/master'],
        cwd=vault_path,
        capture_output=True,
        text=True,
        check=True
    )
    needs_pull = int(result.stdout.strip()) > 0 if result.stdout.strip() else False

    return (pending_changes, unsynced_commits, needs_pull)
```

**1.2: Remote Server Setup**

Extend `deploy/Dockerfile` to include Git server:

```dockerfile
FROM rust:latest as builder

# Install build dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Clone and build TaskChampion sync server
WORKDIR /build
RUN git clone https://github.com/GothenburgBitFactory/taskchampion-sync-server.git
WORKDIR /build/taskchampion-sync-server
RUN rm Cargo.lock && cargo build --release

# Runtime stage
FROM debian:bookworm-slim

# Install Git and SSH server
RUN apt-get update && \
    apt-get install -y git openssh-server && \
    rm -rf /var/lib/apt/lists/*

# Copy binary from builder
COPY --from=builder /build/taskchampion-sync-server/target/release/taskchampion-sync-server /usr/local/bin/

# Create data directories
RUN mkdir -p /data /data/git-repos /data/taskchampion

# Setup SSH for Git
RUN mkdir -p /var/run/sshd && \
    useradd -m -s /usr/bin/git-shell git && \
    mkdir -p /home/git/.ssh

# Expose ports
EXPOSE 8080 22

# Startup script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
```

Create `deploy/entrypoint.sh`:

```bash
#!/bin/bash
set -e

# Start SSH server
service ssh start

# Start TaskChampion sync server
exec taskchampion-sync-server --listen 0.0.0.0:8080 --data-dir /data/taskchampion
```

**1.3: SSH Key Management**

Update `src/brainplorp/commands/setup.py` to generate SSH key for Git:

```python
def setup_vault_sync(config: dict) -> dict:
    """
    Configure vault sync (Phase 4 of setup wizard).

    Creates:
    - SSH key pair for Git authentication
    - Git repository in vault
    - Remote connection to sync server
    """
    console.print("\n[bold cyan]Step 4: Vault Sync[/bold cyan]")
    console.print("  brainplorp can sync your vault across multiple computers.\n")

    # Check if already configured
    ssh_key_path = Path.home() / '.config' / 'brainplorp' / 'vault_sync_key'
    if ssh_key_path.exists():
        console.print("  ✓ Vault sync already configured")
        return config

    # Generate SSH key
    console.print("  Generating SSH key for vault sync...")
    subprocess.run(
        ['ssh-keygen', '-t', 'ed25519', '-f', str(ssh_key_path), '-N', '', '-C', 'brainplorp-vault-sync'],
        check=True,
        capture_output=True
    )

    # Read public key
    public_key = (ssh_key_path.with_suffix('.pub')).read_text().strip()

    # Upload public key to server
    vault_sync_url = config.get('taskwarrior_sync', {}).get('server', '').replace('8080', '22')

    console.print(f"  Registering key with sync server...")
    # TODO: API call to register public key with server

    # Initialize Git repo in vault
    vault_path = Path(config['vault_path'])
    git_init(vault_path)

    # Add remote
    git_remote = f"ssh://git@{vault_sync_url}/vault"
    git_add_remote(vault_path, git_remote)

    # Update config
    config['vault_sync'] = {
        'enabled': True,
        'remote_url': git_remote,
        'ssh_key_path': str(ssh_key_path)
    }

    console.print("  [green]✓ Vault sync configured![/green]")
    return config
```

### Phase 2: Sync Command (2 hours)

**2.1: Core Sync Logic**

Create `src/brainplorp/commands/vault_sync.py`:

```python
"""
Vault sync command - synchronize vault across computers.
"""

import click
from pathlib import Path
from rich.console import Console
from datetime import datetime
import subprocess

from ..config import load_config
from ..integrations.git import (
    git_status,
    git_add_remote,
    GitError,
    GitConflictError
)

console = Console()


@click.group()
def vault():
    """Vault synchronization commands."""
    pass


@vault.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed sync information')
@click.option('--dry-run', is_flag=True, help='Show what would be synced without syncing')
def sync(verbose: bool, dry_run: bool):
    """
    Sync vault with remote server.

    This command:
    1. Commits local changes
    2. Pulls remote changes
    3. Resolves conflicts automatically
    4. Pushes local changes

    Users never need to know Git - brainplorp handles everything.
    """
    try:
        config = load_config()
        vault_path = Path(config['vault_path'])

        # Check if vault sync is enabled
        if not config.get('vault_sync', {}).get('enabled'):
            console.print("[yellow]Vault sync not configured.[/yellow]")
            console.print("Run [bold]brainplorp setup[/bold] to configure vault sync.")
            return

        console.print("\n[bold cyan]📦 Syncing vault...[/bold cyan]\n")

        # Get current status
        pending_changes, unsynced_commits, needs_pull = git_status(vault_path)

        if verbose:
            console.print(f"  Pending changes: {pending_changes}")
            console.print(f"  Unsynced commits: {unsynced_commits}")
            console.print(f"  Needs pull: {needs_pull}\n")

        if dry_run:
            console.print("[yellow]Dry run mode - no changes will be made[/yellow]")
            if pending_changes > 0:
                console.print(f"  Would commit {pending_changes} changed files")
            if needs_pull:
                console.print("  Would download remote changes")
            if unsynced_commits > 0:
                console.print(f"  Would upload {unsynced_commits} commits")
            return

        # Step 1: Commit local changes
        if pending_changes > 0:
            _commit_changes(vault_path, verbose)

        # Step 2: Pull remote changes
        if needs_pull:
            _pull_changes(vault_path, verbose)

        # Step 3: Push local changes
        if unsynced_commits > 0 or pending_changes > 0:
            _push_changes(vault_path, verbose)

        # Show sync summary
        console.print("\n[green]✓ Vault sync complete![/green]")
        console.print(f"  Last sync: {datetime.now().strftime('%I:%M %p')}")

    except GitConflictError as e:
        console.print(f"\n[red]Conflict detected:[/red] {e}")
        console.print("Run [bold]brainplorp vault conflicts[/bold] to resolve.")
        raise click.Abort()

    except GitError as e:
        console.print(f"\n[red]Sync failed:[/red] {e}")
        raise click.Abort()


def _commit_changes(vault_path: Path, verbose: bool) -> None:
    """Commit local changes to Git."""
    if verbose:
        console.print("  Committing local changes...")

    # Stage brainplorp-managed files
    subprocess.run(
        ['git', 'add', 'daily/', 'inbox/', 'notes/', '.gitignore', 'README_SYNC.md'],
        cwd=vault_path,
        check=True,
        capture_output=True
    )

    # Commit with timestamp
    hostname = subprocess.run(
        ['hostname'],
        capture_output=True,
        text=True,
        check=True
    ).stdout.strip()

    commit_message = f"Sync from {hostname} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    subprocess.run(
        ['git', 'commit', '-m', commit_message],
        cwd=vault_path,
        check=True,
        capture_output=True
    )

    if verbose:
        console.print("  [green]✓ Changes committed[/green]")


def _pull_changes(vault_path: Path, verbose: bool) -> None:
    """Pull remote changes with conflict resolution."""
    if verbose:
        console.print("  Downloading remote changes...")

    try:
        # Pull with rebase to avoid merge commits
        subprocess.run(
            ['git', 'pull', '--rebase', 'origin', 'master'],
            cwd=vault_path,
            check=True,
            capture_output=True
        )

        if verbose:
            console.print("  [green]✓ Remote changes downloaded[/green]")

    except subprocess.CalledProcessError as e:
        # Check if it's a conflict
        if b'CONFLICT' in e.stderr or b'conflict' in e.stderr.lower():
            raise GitConflictError("Merge conflict detected during pull")
        else:
            raise GitError(f"Pull failed: {e.stderr.decode()}")


def _push_changes(vault_path: Path, verbose: bool) -> None:
    """Push local changes to remote."""
    if verbose:
        console.print("  Uploading changes to server...")

    subprocess.run(
        ['git', 'push', 'origin', 'master'],
        cwd=vault_path,
        check=True,
        capture_output=True
    )

    if verbose:
        console.print("  [green]✓ Changes uploaded[/green]")


@vault.command()
def status():
    """Show vault sync status."""
    try:
        config = load_config()
        vault_path = Path(config['vault_path'])

        if not config.get('vault_sync', {}).get('enabled'):
            console.print("[yellow]Vault sync not configured.[/yellow]")
            return

        pending_changes, unsynced_commits, needs_pull = git_status(vault_path)

        console.print("\n[bold cyan]Vault Sync Status[/bold cyan]\n")

        if pending_changes > 0:
            console.print(f"  [yellow]●[/yellow] {pending_changes} uncommitted changes")
        else:
            console.print("  [green]✓[/green] No uncommitted changes")

        if unsynced_commits > 0:
            console.print(f"  [yellow]●[/yellow] {unsynced_commits} commits not uploaded")
        else:
            console.print("  [green]✓[/green] All commits uploaded")

        if needs_pull:
            console.print("  [yellow]●[/yellow] Remote changes available")
        else:
            console.print("  [green]✓[/green] Up to date with server")

        # Show last sync time
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%cr'],
            cwd=vault_path,
            capture_output=True,
            text=True,
            check=True
        )
        last_sync = result.stdout.strip()
        console.print(f"\n  Last sync: {last_sync}")

    except GitError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise click.Abort()
```

**2.2: Register Command**

Update `src/brainplorp/cli.py`:

```python
from .commands.vault_sync import vault

@click.group()
def cli():
    """brainplorp - Workflow automation for TaskWarrior + Obsidian"""
    pass

# ... existing commands ...

cli.add_command(vault)
```

### Phase 3: Conflict Resolution (1.5 hours)

**3.1: Automatic Conflict Resolution**

Create `src/brainplorp/utils/conflict_resolution.py`:

```python
"""
Automatic conflict resolution for vault sync.

brainplorp uses domain knowledge to resolve most conflicts automatically:
- Daily notes: Regenerate from TaskWarrior (source of truth)
- Inbox files: Merge unprocessed items
- Notes: Create conflict copy for user review
"""

from pathlib import Path
from typing import Optional
from datetime import datetime

from ..workflows.daily import generate_daily_note
from ..parsers.markdown import parse_inbox_file


def resolve_conflict(vault_path: Path, file_path: str) -> Optional[str]:
    """
    Automatically resolve Git conflict for brainplorp-managed file.

    Returns:
        Resolved content, or None if manual resolution needed
    """
    if file_path.startswith('daily/'):
        return _resolve_daily_note_conflict(vault_path, file_path)

    elif file_path.startswith('inbox/'):
        return _resolve_inbox_conflict(vault_path, file_path)

    elif file_path.startswith('notes/'):
        return _create_conflict_copy(vault_path, file_path)

    else:
        return None  # Unknown file type


def _resolve_daily_note_conflict(vault_path: Path, file_path: str) -> str:
    """
    Resolve daily note conflict by regenerating from TaskWarrior.

    Strategy: TaskWarrior is source of truth for tasks.
    Regenerate daily note from TaskWarrior, discarding both conflict versions.
    """
    # Extract date from filename (daily/YYYY-MM-DD.md)
    date_str = Path(file_path).stem  # "YYYY-MM-DD"

    # Regenerate from TaskWarrior
    content = generate_daily_note(date_str)

    return content


def _resolve_inbox_conflict(vault_path: Path, file_path: str) -> str:
    """
    Resolve inbox conflict by merging unprocessed items.

    Strategy: Combine all unprocessed items from both versions.
    Duplicates are OK (user will skip during processing).
    """
    full_path = vault_path / file_path

    # Read both versions (Git creates conflict markers)
    conflict_content = full_path.read_text()

    # Parse conflict markers
    ours_content = _extract_conflict_section(conflict_content, 'ours')
    theirs_content = _extract_conflict_section(conflict_content, 'theirs')

    # Parse both inbox versions
    ours_items = parse_inbox_file(ours_content).get('unprocessed', [])
    theirs_items = parse_inbox_file(theirs_content).get('unprocessed', [])

    # Merge unprocessed items
    merged_items = list(set(ours_items + theirs_items))  # Remove duplicates

    # Reconstruct inbox file
    merged_content = f"""# Inbox - {Path(file_path).stem}

## Unprocessed

"""
    for item in merged_items:
        merged_content += f"- [ ] {item}\n"

    merged_content += "\n## Processed\n\n"

    return merged_content


def _create_conflict_copy(vault_path: Path, file_path: str) -> None:
    """
    Create conflict copy for manual user resolution.

    Strategy: Can't automatically resolve note conflicts.
    Create `.conflicted-TIMESTAMP.md` copy and let user choose.
    """
    full_path = vault_path / file_path
    conflict_content = full_path.read_text()

    # Create conflict copy
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    conflict_file = full_path.with_name(f"{full_path.stem}.conflicted-{timestamp}.md")
    conflict_file.write_text(conflict_content)

    # Keep "ours" version in original file
    ours_content = _extract_conflict_section(conflict_content, 'ours')
    full_path.write_text(ours_content)

    return None  # Signal manual resolution needed


def _extract_conflict_section(content: str, section: str) -> str:
    """
    Extract content from Git conflict markers.

    Git conflict format:
    <<<<<<< HEAD (ours)
    Our content
    =======
    Their content
    >>>>>>> origin/master (theirs)
    """
    lines = content.split('\n')

    if section == 'ours':
        start_marker = '<<<<<<< HEAD'
        end_marker = '======='
    else:  # theirs
        start_marker = '======='
        end_marker = '>>>>>>> '

    in_section = False
    section_lines = []

    for line in lines:
        if line.startswith(start_marker):
            in_section = True
            continue
        elif line.startswith(end_marker):
            break
        elif in_section:
            section_lines.append(line)

    return '\n'.join(section_lines)
```

### Phase 4: Integration with Existing Commands (0.5 hours)

**4.1: Auto-sync on Start**

Update `src/brainplorp/commands/start.py`:

```python
@click.command()
@click.option('--auto-sync/--no-auto-sync', default=True, help='Automatically sync vault before start')
def start(auto_sync: bool):
    """Generate today's daily note."""

    # Auto-sync vault before generating daily note
    if auto_sync:
        config = load_config()
        if config.get('vault_sync', {}).get('enabled'):
            console.print("🔄 Syncing vault...")
            # Call vault sync internally
            from .vault_sync import sync as vault_sync_cmd
            try:
                vault_sync_cmd(verbose=False, dry_run=False)
            except Exception as e:
                console.print(f"[yellow]Warning: Vault sync failed: {e}[/yellow]")
                console.print("Continuing with start command...\n")

    # ... rest of start command ...
```

**4.2: Auto-sync on Review**

Update `src/brainplorp/commands/review.py`:

```python
@click.command()
@click.option('--auto-sync/--no-auto-sync', default=True, help='Automatically sync vault after review')
def review(auto_sync: bool):
    """Interactive review of incomplete tasks."""

    # ... review workflow ...

    # Auto-sync vault after review (to upload changes)
    if auto_sync:
        config = load_config()
        if config.get('vault_sync', {}).get('enabled'):
            console.print("\n🔄 Syncing vault...")
            from .vault_sync import sync as vault_sync_cmd
            try:
                vault_sync_cmd(verbose=False, dry_run=False)
            except Exception as e:
                console.print(f"[yellow]Warning: Vault sync failed: {e}[/yellow]")
```

---

## Testing Strategy

### Manual Testing Checklist

**Setup (Two Test Computers Required):**

- [ ] Computer 1: Fresh brainplorp install, run setup wizard
- [ ] Computer 1: Verify `.git/` directory created in vault
- [ ] Computer 1: Verify `.gitignore` created with selective sync rules
- [ ] Computer 1: Create test daily note with `brainplorp start`
- [ ] Computer 1: Run `brainplorp vault sync`
- [ ] Computer 1: Verify sync completes successfully

**Computer 2 First Sync:**

- [ ] Computer 2: Fresh brainplorp install, run setup wizard
- [ ] Computer 2: Run `brainplorp vault sync`
- [ ] Computer 2: Verify daily note downloaded from Computer 1
- [ ] Computer 2: Verify `daily/`, `inbox/`, `notes/` directories synced
- [ ] Computer 2: Verify other vault directories NOT synced

**Bidirectional Sync:**

- [ ] Computer 1: Add task to today's daily note
- [ ] Computer 1: Run `brainplorp vault sync`
- [ ] Computer 2: Run `brainplorp vault sync`
- [ ] Computer 2: Verify task appears in daily note

**Conflict Resolution:**

- [ ] Computer 1: Add "Task A" to daily note, DON'T sync yet
- [ ] Computer 2: Add "Task B" to same daily note, sync immediately
- [ ] Computer 1: Run `brainplorp vault sync`
- [ ] Computer 1: Verify conflict resolved automatically (daily note regenerated from TaskWarrior)

**Offline Mode:**

- [ ] Computer 1: Disconnect from internet
- [ ] Computer 1: Run `brainplorp vault sync`
- [ ] Computer 1: Verify graceful error message (queued for next sync)
- [ ] Computer 1: Reconnect to internet
- [ ] Computer 1: Run `brainplorp vault sync`
- [ ] Computer 1: Verify changes uploaded successfully

**Status Command:**

- [ ] Run `brainplorp vault status` with no changes
- [ ] Verify shows "Up to date"
- [ ] Modify daily note without syncing
- [ ] Run `brainplorp vault status`
- [ ] Verify shows "N uncommitted changes"

### Automated Tests

Create `tests/test_vault_sync.py`:

```python
"""Tests for vault sync functionality."""

import pytest
from pathlib import Path
import subprocess
import tempfile

from brainplorp.integrations.git import git_init, git_status, git_add_remote
from brainplorp.utils.conflict_resolution import resolve_conflict


def test_git_init_creates_repo(tmp_path):
    """Test Git initialization creates .git directory."""
    git_init(tmp_path)

    assert (tmp_path / '.git').exists()
    assert (tmp_path / '.gitignore').exists()
    assert (tmp_path / 'README_SYNC.md').exists()


def test_gitignore_selective_sync(tmp_path):
    """Test .gitignore only syncs brainplorp directories."""
    git_init(tmp_path)

    # Create test files
    (tmp_path / 'daily').mkdir()
    (tmp_path / 'daily' / 'test.md').write_text('daily note')
    (tmp_path / 'other').mkdir()
    (tmp_path / 'other' / 'test.md').write_text('other file')

    # Stage all files
    subprocess.run(['git', 'add', '.'], cwd=tmp_path, check=True)

    # Check what's staged
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only'],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True
    )

    staged_files = result.stdout.strip().split('\n')

    assert 'daily/test.md' in staged_files
    assert 'other/test.md' not in staged_files


def test_git_status_reports_changes(tmp_path):
    """Test git_status reports pending changes."""
    git_init(tmp_path)

    # Create uncommitted file
    (tmp_path / 'daily').mkdir()
    (tmp_path / 'daily' / 'test.md').write_text('test')

    pending, unsynced, needs_pull = git_status(tmp_path)

    assert pending > 0  # Uncommitted change detected


def test_conflict_resolution_daily_note(tmp_path):
    """Test daily note conflict resolved by regeneration."""
    # Create conflict scenario
    conflict_content = """<<<<<<< HEAD
- [ ] Task A (uuid: abc-123)
=======
- [ ] Task B (uuid: def-456)
>>>>>>> origin/master
"""

    (tmp_path / 'daily').mkdir()
    conflict_file = tmp_path / 'daily' / '2025-10-12.md'
    conflict_file.write_text(conflict_content)

    # Resolve conflict
    resolved = resolve_conflict(tmp_path, 'daily/2025-10-12.md')

    # Should regenerate from TaskWarrior (not contain conflict markers)
    assert '<<<<<<< HEAD' not in resolved
    assert '>>>>>>>' not in resolved
```

---

## Configuration

### Updated config.yaml Schema

```yaml
vault_path: /Users/jsd/vault

taskwarrior_sync:
  enabled: true
  server: https://brainplorp-sync.fly.dev
  client_id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
  encryption_secret: abc123def456...

vault_sync:
  enabled: true
  remote_url: ssh://git@brainplorp-sync.fly.dev/vault
  ssh_key_path: ~/.config/brainplorp/vault_sync_key
  auto_sync: true  # Auto-sync on start/review commands
```

---

## User Documentation

### Quick Start Guide

**Enable vault sync:**

```bash
# Already enabled during setup wizard
brainplorp vault sync
```

**Check sync status:**

```bash
brainplorp vault status
```

**Sync manually:**

```bash
brainplorp vault sync
```

**Disable auto-sync:**

```bash
# Edit ~/.config/brainplorp/config.yaml
vault_sync:
  auto_sync: false
```

### Troubleshooting

**Q: What if sync fails with "authentication failed"?**

A: Your SSH key may not be registered with the server. Run:

```bash
brainplorp setup  # Re-run setup to re-register key
```

**Q: What if I see a `.conflicted-TIMESTAMP.md` file?**

A: brainplorp couldn't automatically resolve a conflict in a note. Open both files, choose the content you want to keep, and delete the `.conflicted-*` file.

**Q: Can I sync my entire vault?**

A: Not with brainplorp's built-in sync. brainplorp only syncs directories it manages (`daily/`, `inbox/`, `notes/`). Use Obsidian Sync or iCloud for full vault sync.

**Q: What if I'm offline?**

A: Changes are queued locally. Next time you run `brainplorp vault sync` while online, changes will be uploaded.

---

## Success Metrics

**Must Have (Sprint 10.3):**
- [ ] `brainplorp vault sync` command works end-to-end
- [ ] Selective sync (only brainplorp directories)
- [ ] Automatic conflict resolution for daily notes and inbox files
- [ ] SSH key generation and registration during setup
- [ ] `brainplorp vault status` shows sync state
- [ ] Git server deployed to Fly.io

**Should Have (Sprint 10.4):**
- [ ] Auto-sync on `brainplorp start` and `brainplorp review`
- [ ] Offline mode (queue changes, sync when online)
- [ ] Clear error messages for auth failures
- [ ] Performance: <5 seconds for typical sync

**Could Have (Future):**
- [ ] `brainplorp vault history` to view sync history
- [ ] `brainplorp vault conflicts` to list unresolved conflicts
- [ ] Web UI to view vault sync activity
- [ ] Webhook notifications on sync events

---

## Risk Assessment

**High Risk:**
- **Git complexity for users** - Mitigated by abstracting Git entirely
- **SSH key management** - Mitigated by automated key generation and registration
- **Conflict resolution failures** - Mitigated by conservative strategies (regenerate from source of truth)

**Medium Risk:**
- **Server storage limits** - Fly.io free tier has 3GB, adequate for text files
- **Network failures during sync** - Mitigated by atomic Git operations (all-or-nothing)

**Low Risk:**
- **Performance** - Git is fast for small text files (daily notes, inbox files)
- **User adoption** - Optional feature, doesn't affect existing workflows

---

## Future Enhancements (Post-Sprint 10.3)

**Sprint 11: Advanced Conflict Resolution**
- Smart merge for inbox items (deduplicate based on content similarity)
- Interactive conflict resolution UI
- Conflict history and rollback

**Sprint 12: Sync Monitoring**
- Web dashboard for sync activity
- Email notifications on conflicts
- Sync analytics (files synced, bandwidth used)

**Sprint 13: Expanded Sync Scope**
- Sync `projects/` directory as brainplorp manages more of vault
- Sync attachments referenced in brainplorp notes
- Selective sync configuration (user chooses directories)

---

## Document Maintenance

**Created:** 2025-10-12 by PM Claude
**Last Updated:** 2025-10-12
**Related Sprints:**
- Sprint 10.2 (Cloud Sync - TaskWarrior)
- Sprint 10.1.1 (Installation Hardening)

**Dependencies:**
- Sprint 10.2 must be complete (sync server deployed)
- Git must be installed on user's Mac (Homebrew dependency)

**Update Protocol:**
- Update spec if conflict resolution strategies change
- Update if Git server architecture changes
- Update when expanding sync scope (new directories)
