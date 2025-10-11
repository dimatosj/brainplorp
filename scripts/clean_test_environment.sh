#!/bin/bash
# ABOUTME: Clean test environment script - removes TaskWarrior and Obsidian configs for fresh installation testing
# ABOUTME: Creates backups before removing anything, can be run multiple times safely

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$HOME/.brainplorp-test-backups/backup-$(date +%Y%m%d-%H%M%S)"

echo "🧹 brainplorp Test Environment Cleanup"
echo "======================================"
echo ""
echo "This script will:"
echo "  1. Backup existing TaskWarrior and Obsidian configs"
echo "  2. Uninstall brainplorp and TaskWarrior (Homebrew)"
echo "  3. Remove TaskWarrior and brainplorp config files"
echo "  4. Optionally remove Obsidian config"
echo ""
echo "⚠️  This preserves:"
echo "  - This repository ($SCRIPT_DIR)"
echo "  - All backups in ~/.brainplorp-test-backups/"
echo ""
echo "Backup location: $BACKUP_DIR"
echo ""

# Confirm with user
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Step 1: Creating backup directory..."
mkdir -p "$BACKUP_DIR"

# Backup TaskWarrior
if [ -d "$HOME/.task" ]; then
    echo "  📦 Backing up TaskWarrior data..."
    cp -R "$HOME/.task" "$BACKUP_DIR/task"
    echo "     ✓ Backed up to $BACKUP_DIR/task"
else
    echo "  ℹ️  No TaskWarrior data found"
fi

if [ -f "$HOME/.taskrc" ]; then
    echo "  📦 Backing up .taskrc..."
    cp "$HOME/.taskrc" "$BACKUP_DIR/taskrc"
    echo "     ✓ Backed up to $BACKUP_DIR/taskrc"
else
    echo "  ℹ️  No .taskrc found"
fi

# Backup brainplorp config
if [ -d "$HOME/.config/brainplorp" ]; then
    echo "  📦 Backing up brainplorp config..."
    cp -R "$HOME/.config/brainplorp" "$BACKUP_DIR/brainplorp-config"
    echo "     ✓ Backed up to $BACKUP_DIR/brainplorp-config"
else
    echo "  ℹ️  No brainplorp config found"
fi

# Backup Obsidian vault location (just the path, not the vault itself)
if [ -f "$HOME/.config/brainplorp/config.yaml" ]; then
    VAULT_PATH=$(grep "vault_path:" "$HOME/.config/brainplorp/config.yaml" | sed 's/vault_path: *//' | tr -d '"' | tr -d "'")
    if [ -n "$VAULT_PATH" ] && [ -d "$VAULT_PATH" ]; then
        echo "  📦 Backing up Obsidian vault location: $VAULT_PATH"
        echo "$VAULT_PATH" > "$BACKUP_DIR/vault_path.txt"
        echo "     ✓ Vault path saved (not copying vault data for space)"
    fi
fi

# Backup Obsidian config
if [ -d "$HOME/Library/Application Support/obsidian" ]; then
    echo "  📦 Backing up Obsidian config..."
    cp -R "$HOME/Library/Application Support/obsidian" "$BACKUP_DIR/obsidian-config"
    echo "     ✓ Backed up to $BACKUP_DIR/obsidian-config"
else
    echo "  ℹ️  No Obsidian config found"
fi

echo ""
echo "Step 2: Uninstalling Homebrew packages..."

# Uninstall brainplorp first (this will allow task to be uninstalled)
if command -v brew &> /dev/null && brew list brainplorp &> /dev/null 2>&1; then
    echo "  🍺 Uninstalling brainplorp via Homebrew..."
    brew uninstall brainplorp
    echo "     ✓ Uninstalled brainplorp"
else
    echo "  ℹ️  brainplorp not installed via Homebrew"
fi

# Now uninstall TaskWarrior (no longer blocked by brainplorp dependency)
if command -v brew &> /dev/null && brew list task &> /dev/null 2>&1; then
    echo "  🍺 Uninstalling TaskWarrior via Homebrew..."
    brew uninstall task
    echo "     ✓ Uninstalled task"
else
    echo "  ℹ️  TaskWarrior not installed via Homebrew"
fi

echo ""
echo "Step 3: Removing configuration files..."

# Remove TaskWarrior configs
if [ -d "$HOME/.task" ]; then
    rm -rf "$HOME/.task"
    echo "  ✓ Removed $HOME/.task"
else
    echo "  ℹ️  No TaskWarrior data directory"
fi

if [ -f "$HOME/.taskrc" ]; then
    rm "$HOME/.taskrc"
    echo "  ✓ Removed $HOME/.taskrc"
else
    echo "  ℹ️  No .taskrc file"
fi

# Remove brainplorp config
if [ -d "$HOME/.config/brainplorp" ]; then
    rm -rf "$HOME/.config/brainplorp"
    echo "  ✓ Removed $HOME/.config/brainplorp"
else
    echo "  ℹ️  No brainplorp config directory"
fi

echo ""
echo "Step 4: Obsidian cleanup (optional)..."
echo "  ℹ️  Obsidian app itself is NOT removed (you may want to keep it)"
echo "  ℹ️  Vault data is NOT removed (preserved for safety)"
if [ -d "$HOME/Library/Application Support/obsidian" ]; then
    read -p "  Remove Obsidian config? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$HOME/Library/Application Support/obsidian"
        echo "     ✓ Removed Obsidian config"
    else
        echo "     ℹ️  Kept Obsidian config"
    fi
else
    echo "  ℹ️  No Obsidian config found"
fi

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "Summary:"
echo "  📦 Backup location: $BACKUP_DIR"
echo "  🗑️  Removed: TaskWarrior data, brainplorp config"
echo "  ✅ Preserved: This repository, vault data (if any)"
echo ""
echo "To test fresh installation:"
echo "  1. brew tap dimatosj/brainplorp"
echo "  2. brew install brainplorp"
echo "  3. brainplorp setup"
echo ""
echo "To restore from backup:"
echo "  Run: $SCRIPT_DIR/restore_test_environment.sh $BACKUP_DIR"
echo ""
