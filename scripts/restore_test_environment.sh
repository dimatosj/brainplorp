#!/bin/bash
# ABOUTME: Restore test environment script - restores TaskWarrior and Obsidian configs from backup
# ABOUTME: Used after testing to restore your previous working environment

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔄 brainplorp Test Environment Restore"
echo "======================================"
echo ""

# Check if backup directory provided
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_directory>"
    echo ""
    echo "Available backups:"
    if [ -d "$HOME/.brainplorp-test-backups" ]; then
        ls -1t "$HOME/.brainplorp-test-backups" | head -5
    else
        echo "  No backups found"
    fi
    exit 1
fi

BACKUP_DIR="$1"

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Error: Backup directory not found: $BACKUP_DIR"
    exit 1
fi

echo "Restoring from: $BACKUP_DIR"
echo ""
echo "This will:"
echo "  1. Restore TaskWarrior data and config"
echo "  2. Restore brainplorp config"
echo "  3. Restore Obsidian config (if backed up)"
echo ""
echo "⚠️  This will OVERWRITE any current configs!"
echo ""

# Confirm with user
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Step 1: Restoring TaskWarrior..."
if [ -d "$BACKUP_DIR/task" ]; then
    mkdir -p "$HOME/.task"
    cp -R "$BACKUP_DIR/task/"* "$HOME/.task/"
    echo "  ✓ Restored $HOME/.task"
else
    echo "  ℹ️  No TaskWarrior data in backup"
fi

if [ -f "$BACKUP_DIR/taskrc" ]; then
    cp "$BACKUP_DIR/taskrc" "$HOME/.taskrc"
    echo "  ✓ Restored $HOME/.taskrc"
else
    echo "  ℹ️  No .taskrc in backup"
fi

echo ""
echo "Step 2: Restoring brainplorp config..."
if [ -d "$BACKUP_DIR/brainplorp-config" ]; then
    mkdir -p "$HOME/.config/brainplorp"
    cp -R "$BACKUP_DIR/brainplorp-config/"* "$HOME/.config/brainplorp/"
    echo "  ✓ Restored $HOME/.config/brainplorp"
else
    echo "  ℹ️  No brainplorp config in backup"
fi

echo ""
echo "Step 3: Restoring Obsidian config..."
if [ -d "$BACKUP_DIR/obsidian-config" ]; then
    mkdir -p "$HOME/Library/Application Support/obsidian"
    cp -R "$BACKUP_DIR/obsidian-config/"* "$HOME/Library/Application Support/obsidian/"
    echo "  ✓ Restored Obsidian config"
else
    echo "  ℹ️  No Obsidian config in backup"
fi

if [ -f "$BACKUP_DIR/vault_path.txt" ]; then
    VAULT_PATH=$(cat "$BACKUP_DIR/vault_path.txt")
    echo ""
    echo "  ℹ️  Original vault path: $VAULT_PATH"
fi

echo ""
echo "✅ Restore complete!"
echo ""
echo "Your TaskWarrior and brainplorp configs have been restored."
echo ""
