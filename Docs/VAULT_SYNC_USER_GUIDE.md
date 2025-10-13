# Vault Sync User Guide

**Sprint 10.3: Vault Sync via CouchDB + Obsidian LiveSync**

## Overview

Vault sync allows you to automatically synchronize your Obsidian vault across multiple devices:
- **Mac computers** (multiple Macs)
- **iPhone and iPad** (iOS devices)
- **Android devices**

Changes sync in **real-time** (2-5 seconds) without any manual commands.

## Prerequisites

1. **brainplorp installed** on your computer
2. **Obsidian installed** on all devices
3. **Self-hosted LiveSync plugin** installed in Obsidian

## Setup: First Computer

### Step 1: Install LiveSync Plugin

1. Open Obsidian
2. Go to **Settings** → **Community Plugins** → **Browse**
3. Search for **"Self-hosted LiveSync"**
4. Click **Install**, then **Enable**

### Step 2: Run brainplorp Setup

```bash
brainplorp setup
```

When prompted:
- **Step 5: Vault Sync** → Choose **Yes**
- Setup will detect LiveSync plugin and configure it automatically
- You'll see your credentials displayed - **SAVE THESE!**

Example output:
```
Step 5: Vault Sync (Optional)
  Sync your vault across devices (Mac, iPhone, iPad, etc.)
  Configure vault sync? [y/N]: y
  ✓ Self-hosted LiveSync plugin installed

  Generating CouchDB credentials...
  Connecting to CouchDB server...
  Creating database: user-jsd-vault
  ✓ CouchDB configured
  ✓ LiveSync plugin configured
  ✓ Credentials stored in OS keychain

  ============================================================
  📋 SAVE THESE CREDENTIALS FOR YOUR OTHER COMPUTERS:
  ============================================================
  Server:   https://couch-brainplorp-sync.fly.dev
  Database: user-jsd-vault
  Username: user-jsd
  Password: CZzAQ7wnpPHY-tL0dYu20VY9-vcQHWdvENs0rLkye_0
  ============================================================
```

### Step 3: Enable LiveSync in Obsidian

1. Open Obsidian (if not already open)
2. Go to **Settings** → **Community Plugins**
3. Find **Self-hosted LiveSync**
4. It should show **"Connected"** or **"Syncing"**

Your vault is now syncing!

## Setup: Additional Mac

### Step 1: Install brainplorp and LiveSync Plugin

Same as First Computer:
1. Install brainplorp: `brew install dimatosj/brainplorp/brainplorp`
2. Install LiveSync plugin in Obsidian

### Step 2: Run Setup with Existing Credentials

```bash
brainplorp setup
```

When prompted:
- **Step 5: Vault Sync** → Choose **Yes**
- **Do you have CouchDB credentials from another computer?** → Choose **Yes**
- Enter the credentials you saved from Computer 1

```
  Do you have CouchDB credentials from another computer? [y/N]: y

  Enter credentials from your other computer:
  Username: user-jsd
  Database: user-jsd-vault
  Password: [paste password]

  ✓ LiveSync plugin configured
  ✓ Credentials stored in OS keychain
```

### Step 3: Enable LiveSync and Download Vault

1. Open Obsidian
2. Enable LiveSync plugin
3. Your vault will download automatically from the server
4. Wait for initial sync to complete (may take 30 seconds to 2 minutes for large vaults)

## Setup: iPhone or iPad

### Step 1: Install Obsidian and Create Empty Vault

1. Install **Obsidian** from App Store
2. Open Obsidian
3. Create a new empty vault (any name)

### Step 2: Install LiveSync Plugin

1. In Obsidian: **Settings** (gear icon) → **Community Plugins** → **Browse**
2. Search for **"Self-hosted LiveSync"**
3. Install and Enable

### Step 3: Configure Sync

1. Go to **Settings** → **Self-hosted LiveSync**
2. Enter your credentials from Computer 1:
   - **Server URL**: `https://couch-brainplorp-sync.fly.dev`
   - **Database**: `user-jsd-vault`
   - **Username**: `user-jsd`
   - **Password**: [your password]
3. Toggle **Live Sync** to **ON**
4. Tap **Start Sync**

Your vault will download automatically. Wait for initial sync to complete.

## Daily Usage

Once configured, sync happens **automatically**:

- **Edit on Mac** → Syncs to iPhone in 2-5 seconds
- **Add task on iPhone** → Appears on Mac immediately
- **Create note on iPad** → Available everywhere

You never need to run sync commands - it just works.

## Checking Sync Status

### From Command Line

```bash
brainplorp vault status
```

Output shows:
- Sync configuration
- Server and database info
- Any conflicts detected
- Instructions for other computers

Example:
```
Vault Sync Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Status: ✓ Configured
  Server: https://couch-brainplorp-sync.fly.dev
  Database: user-jsd-vault
  Username: user-jsd

  ✓ No conflicts detected
```

### In Obsidian

Look for the LiveSync status icon:
- **Green checkmark** = Syncing normally
- **Yellow warning** = Conflict detected
- **Red X** = Not connected

## Troubleshooting

### Sync Not Working

**Check LiveSync Status:**
1. Open Obsidian → **Settings** → **Self-hosted LiveSync**
2. Look for connection status

**Common issues:**
- **Not connected** → Check credentials are correct
- **Authentication failed** → Re-enter password
- **Can't reach server** → Check internet connection

**Re-run setup if needed:**
```bash
brainplorp setup
# Choose "No" for vault sync
# Then run again and choose "Yes" with correct credentials
```

### Conflicts

**What are conflicts?**
- Happen when same file edited on two devices simultaneously
- LiveSync creates `.conflicted.md` files

**How to resolve:**
1. Find conflicted files: `brainplorp vault status` will list them
2. Open both files in Obsidian (original + `.conflicted.md`)
3. Manually merge the changes
4. Delete the `.conflicted.md` file
5. LiveSync will sync your merged version

**Example:**
```
daily/2025-10-12.md              ← Your original file
daily/2025-10-12.conflicted.md   ← Conflict from other device
```

Merge content from conflicted file into original, then delete conflicted file.

### Slow Sync

**Normal speeds:**
- Small files (<10KB): 2-5 seconds
- Large files (1MB+): 10-30 seconds
- Initial sync (100+ files): 1-3 minutes

**If unusually slow:**
- Check internet connection
- Check Fly.io status: https://status.fly.io
- Restart Obsidian
- Toggle LiveSync off and on

### Lost Credentials

**If you lost your password:**

You cannot recover it. You'll need to reconfigure sync:

1. On Computer 1 (where it's working):
   ```bash
   brainplorp vault status
   ```
   This shows your credentials

2. Copy them for other computers

**Best practice:** Store credentials in a password manager (1Password, Bitwarden, etc.)

## Offline Mode

**LiveSync handles offline gracefully:**

1. **Go offline** (airplane mode, no WiFi) - Edit files as normal
2. **Come back online** - Changes sync automatically
3. **No data loss** - All offline edits are preserved

**How it works:**
- Obsidian queues changes while offline
- When reconnected, queued changes upload
- MVCC conflict resolution prevents overwrite

## Security

**Your data is protected:**
- ✅ **HTTPS encryption** in transit (TLS 1.3)
- ✅ **Unique credentials** per user (no sharing)
- ✅ **Database isolation** (your data is separate from others)
- ✅ **Password stored in OS keychain** (not plain text)

**Server location:**
- Hosted on Fly.io (https://fly.io)
- Server URL: `couch-brainplorp-sync.fly.dev`
- Self-hosted by brainplorp project

**What's encrypted:**
- Network traffic (HTTPS)
- Passwords in keychain

**What's NOT encrypted:**
- Vault content on server (CouchDB stores plain text)
- Future versions may add end-to-end encryption

## Uninstalling Vault Sync

If you want to stop syncing:

1. Open Obsidian → **Settings** → **Self-hosted LiveSync**
2. Toggle **Live Sync** to **OFF**
3. Optionally: Disable or uninstall LiveSync plugin

Your local vault remains unchanged. Only sync stops.

To fully remove:
```bash
# Edit config to disable sync
vim ~/.config/brainplorp/config.yaml
# Set vault_sync.enabled: false
```

## FAQ

**Q: Do I need sync for single-device use?**
A: No. Vault sync is optional. brainplorp works fine on a single Mac without sync.

**Q: Can I use Obsidian Sync instead?**
A: Yes, but you'd pay $8/month. brainplorp's sync is free and self-hosted.

**Q: Does this sync TaskWarrior tasks?**
A: No, TaskWarrior has its own sync (Sprint 10). Vault sync is only for Obsidian files.

**Q: How much does Fly.io hosting cost?**
A: Free tier supports small vaults (<1GB). Larger vaults: $1.50/month for 10GB storage.

**Q: Can I host CouchDB myself?**
A: Yes, but you'd need to modify brainplorp setup code to point to your server.

**Q: What happens if Fly.io goes down?**
A: Local vault still works. Sync resumes when server is back. No data loss.

**Q: Can I sync with Obsidian Sync AND CouchDB?**
A: Not recommended. Choose one sync method to avoid conflicts.

## Getting Help

**Issues:**
- GitHub: https://github.com/dimatosj/brainplorp/issues
- Include output of `brainplorp vault status`

**Questions:**
- Check documentation: `Docs/` folder in brainplorp repo
- Create GitHub discussion
