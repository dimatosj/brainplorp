# Testing Environment Scripts

These scripts help you test fresh brainplorp installations by safely removing and restoring your existing configurations.

## Quick Start

### 1. Clean Environment for Testing

```bash
cd /Users/jsd/Documents/plorps/brainplorp
./scripts/clean_test_environment.sh
```

This will:
- ✅ Create timestamped backup in `~/.brainplorp-test-backups/`
- ✅ Remove TaskWarrior data (`~/.task`) and config (`~/.taskrc`)
- ✅ Remove brainplorp config (`~/.config/brainplorp`)
- ✅ Uninstall brainplorp (if installed via Homebrew)
- ✅ Optionally remove Obsidian config
- ✅ **Preserve this repository**
- ✅ **Preserve vault data** (just saves the path)

### 2. Test Fresh Installation

```bash
# Install TaskWarrior
brew install task

# Install brainplorp via Homebrew
brew tap dimatosj/brainplorp
brew install brainplorp

# Run setup wizard
brainplorp setup

# Test the workflows
brainplorp start
brainplorp tasks
brainplorp inbox process
```

### 3. Restore Original Environment

```bash
# Find your backup (script will list recent backups)
./scripts/restore_test_environment.sh ~/.brainplorp-test-backups/backup-YYYYMMDD-HHMMSS
```

This will:
- ✅ Restore TaskWarrior data and config
- ✅ Restore brainplorp config
- ✅ Restore Obsidian config

## What Gets Backed Up

| Item | Location | Backed Up? |
|------|----------|------------|
| TaskWarrior data | `~/.task/` | ✅ Yes |
| TaskWarrior config | `~/.taskrc` | ✅ Yes |
| brainplorp config | `~/.config/brainplorp/` | ✅ Yes |
| Obsidian config | `~/Library/Application Support/obsidian/` | ✅ Yes |
| Obsidian vault | Your vault location | ❌ No (too large) |
| This repository | `~/Documents/plorps/brainplorp/` | ❌ Never touched |

## Safety Features

- **Timestamped backups** - Each cleanup creates a new backup
- **Confirmation prompts** - Script asks before removing anything
- **Preserves repository** - Your development code is never touched
- **Preserves vault data** - Only config removed, not actual notes
- **Multiple backups** - Can run cleanup multiple times, each creates new backup

## Common Workflows

### Test Fresh Install → Restore

```bash
# 1. Clean
./scripts/clean_test_environment.sh

# 2. Test fresh install
brew install task
brew tap dimatosj/brainplorp
brew install brainplorp
brainplorp setup

# 3. Restore
./scripts/restore_test_environment.sh ~/.brainplorp-test-backups/backup-YYYYMMDD-HHMMSS
```

### Test Multiple Times

```bash
# Each cleanup creates a new backup
./scripts/clean_test_environment.sh  # backup-20251011-140000
# ... test ...

./scripts/clean_test_environment.sh  # backup-20251011-150000
# ... test again ...

# Restore from any backup
./scripts/restore_test_environment.sh ~/.brainplorp-test-backups/backup-20251011-140000
```

## Backup Location

All backups stored in: `~/.brainplorp-test-backups/`

Backup directory structure:
```
~/.brainplorp-test-backups/
└── backup-20251011-140530/
    ├── task/                   # TaskWarrior data
    ├── taskrc                  # TaskWarrior config
    ├── brainplorp-config/      # brainplorp config
    ├── obsidian-config/        # Obsidian config
    └── vault_path.txt          # Path to vault (for reference)
```

## Troubleshooting

**"No backups found"**
- You haven't run `clean_test_environment.sh` yet
- Run it once to create your first backup

**"Backup directory not found"**
- Check the path: `ls -la ~/.brainplorp-test-backups/`
- Use tab completion for the backup directory name

**"Permission denied"**
- Make scripts executable: `chmod +x scripts/*.sh`

**Want to clean up old backups?**
```bash
# List all backups (newest first)
ls -lt ~/.brainplorp-test-backups/

# Remove old backups manually
rm -rf ~/.brainplorp-test-backups/backup-YYYYMMDD-HHMMSS
```

## Notes

- **Repository is never touched** - These scripts only affect configs
- **Safe to run multiple times** - Each run creates a new backup
- **Vault data preserved** - Scripts don't touch your actual notes
- **Obsidian app preserved** - Only config removed, not the application
- **Can restore at any time** - All backups kept until manually deleted
