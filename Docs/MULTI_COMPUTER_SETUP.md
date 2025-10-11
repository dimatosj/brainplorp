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

```bash
brew tap dimatosj/brainplorp
brew install brainplorp
```

#### Step 2: Run Setup Wizard

```bash
brainplorp setup
```

Follow prompts to configure:
- Obsidian vault location (should be in iCloud)
- TaskWarrior sync server
- Optional: Email inbox

#### Step 3: Move Vault to iCloud (if needed)

If your Obsidian vault is not in iCloud:

1. Open Obsidian
2. Settings → Files & Links → "Open another vault"
3. Create new vault in iCloud location:
   `~/Library/Mobile Documents/iCloud~md~obsidian/YourVaultName`
4. Copy notes from old vault to new vault
5. Update config: `brainplorp setup` (re-run to update vault path)

#### Step 4: Configure TaskChampion Sync

**Option A: Self-Hosted Server**

```bash
# On a server or always-on computer
cargo install taskchampion-sync-server
taskchampion-sync-server --port 8080
```

**Option B: Cloud-Hosted Server**

Use a service like Railway, Render, or Fly.io to host the server.

**Configure TaskWarrior:**

```bash
task config sync.server.url https://your-server.com
task config sync.server.client_id $(uuidgen)
task sync init
```

#### Step 5: Test Everything

```bash
# Create test task
brainplorp tasks

# Verify vault is in iCloud
ls ~/Library/Mobile\ Documents/iCloud~md~obsidian/

# Validate config
brainplorp config validate
```

---

### Computer 2 (Secondary Setup)

#### Step 1: Wait for iCloud Sync

Ensure iCloud has synced your Obsidian vault:

```bash
ls ~/Library/Mobile\ Documents/iCloud~md~obsidian/
# Should see your vault folder
```

#### Step 2: Install brainplorp

```bash
brew tap dimatosj/brainplorp
brew install brainplorp
```

#### Step 3: Run Setup Wizard

```bash
brainplorp setup
```

**Important:** Use the SAME TaskChampion sync server URL as Computer 1.

#### Step 4: Sync TaskWarrior

```bash
task sync init
task sync
```

All tasks from Computer 1 should now appear.

#### Step 5: Verify Sync

```bash
# List tasks (should match Computer 1)
brainplorp tasks

# Create a test task
task add "Test from Computer 2"

# Sync
task sync

# On Computer 1, run: task sync
# Task should appear on Computer 1
```

---

## Sync Workflows

### Daily Sync Routine

**On any computer:**

```bash
# Before starting work
task sync            # Pull tasks from server

# Do your work
brainplorp start
# ... work in Obsidian, complete tasks ...

# After finishing work
task sync            # Push tasks to server
```

**iCloud vault syncs automatically** - no manual action needed.

### Conflict Resolution

**TaskWarrior Conflicts:**

TaskChampion handles conflicts automatically using operational transforms. If both computers modify the same task offline, sync will merge changes intelligently.

**Obsidian Conflicts:**

iCloud creates conflict files if both computers edit the same note offline:
- Original: `note.md`
- Conflict: `note (conflicted copy 2025-10-11).md`

Manually merge or delete conflict files.

### Troubleshooting

**Tasks not syncing:**

```bash
# Check sync status
task sync

# Verify server URL
task config sync.server.url

# Re-initialize if needed
task sync init
```

**Vault not syncing:**

1. Check iCloud sync status: System Settings → Apple ID → iCloud → iCloud Drive
2. Verify Obsidian vault is in iCloud path
3. Wait a few minutes - iCloud can be slow

**Config out of sync:**

Option 1: Manual copy
```bash
# Computer 1
cat ~/.config/brainplorp/config.yaml

# Computer 2 (paste config)
vim ~/.config/brainplorp/config.yaml
```

Option 2: Git sync (advanced)
```bash
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
```

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

**Q: What happens if I modify the same task on two computers while offline?**
A: TaskChampion's operational transform algorithm merges changes automatically. Both edits are preserved.

**Q: Do I need to sync before every command?**
A: No. Sync before starting your work session and after finishing. TaskWarrior works fine with local-only changes between syncs.
