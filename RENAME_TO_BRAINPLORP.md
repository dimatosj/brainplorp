# Renaming plorp → brainplorp Migration Guide

**Date**: 2025-10-11
**Status**: COMPLETED on Computer 1 (brainplorp directory)

This document provides step-by-step instructions for migrating the `plorp` package to `brainplorp` across multiple computers without breaking your MCP integration or existing installations.

---

## Overview

The project has been renamed from **plorp** to **brainplorp** to better reflect the current nomenclature. This involves:

- Renaming the Python package from `plorp` to `brainplorp`
- Updating all import statements in code
- Updating package configuration
- Re-installing the package locally
- Updating MCP configuration in Claude Desktop

---

## Changes Made on Computer 1

### 1. Codebase Changes
- **Directory renamed**: `src/plorp/` → `src/brainplorp/`
- **Package name updated** in `pyproject.toml`
- **CLI commands renamed**: `plorp` → `brainplorp`, `plorp-mcp` → `brainplorp-mcp`
- **All Python imports updated**: `from plorp.*` → `from brainplorp.*`
- **Documentation updated**: README.md and other docs
- **~3,863 references** to "plorp" updated throughout the codebase

### 2. Files Modified (Detailed List)
- **`pyproject.toml`**
  - Package name: `plorp` → `brainplorp`
  - CLI entry points: `plorp` → `brainplorp`, `plorp-mcp` → `brainplorp-mcp`
  - Package data reference updated
- **`src/brainplorp/__init__.py`**
  - Package docstring and comments updated
- **`src/brainplorp/cli.py`**
  - Import statement fixed: `from plorp import __version__` → `from brainplorp import __version__`
- **All 77 Python files in `src/` and `tests/`**
  - Import statements: `from plorp.` → `from brainplorp.`
  - Patch decorators: `@patch("plorp.` → `@patch("brainplorp.`
  - Context managers: `with patch("plorp.` → `with patch("brainplorp.`
- **`README.md`**
  - Title, headers, and all documentation references updated
  - CLI examples updated with new command names
  - Config path references updated
- **Markdown files in `Docs/`**
  - All references to "plorp " updated to "brainplorp " where appropriate

### 3. Configuration Impact
- **Old config location**: `~/.config/plorp/config.yaml`
- **New config location**: `~/.config/brainplorp/config.yaml`
- **Old CLI commands**: `plorp`, `plorp-mcp`
- **New CLI commands**: `brainplorp`, `brainplorp-mcp`

---

## Migration Instructions for Computer 2 (and subsequent computers)

Follow these steps **IN ORDER** to migrate your other computer(s) to the renamed package.

### Step 1: Pull the Latest Changes

```bash
cd /path/to/your/plorp  # or wherever you have it
git pull
```

This will download all the rename changes from GitHub.

### Step 2: Uninstall the Old Package

```bash
# Activate your virtual environment first (if using one)
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate  # On Windows

# Uninstall the old package
pip uninstall plorp -y
```

### Step 3: Reinstall with New Name

```bash
# Still in your activated virtual environment
pip install -e ".[dev]"
```

This installs the package with its new name `brainplorp`.

### Step 4: Verify Installation

```bash
# Test the new CLI commands
brainplorp --version
brainplorp-mcp --version

# The old commands should no longer work
plorp --version  # Should fail
```

### Step 5: Migrate Configuration Files

```bash
# If you have existing configuration, move it to the new location
mv ~/.config/plorp ~/.config/brainplorp

# Or if you prefer to copy (keeps backup)
cp -r ~/.config/plorp ~/.config/brainplorp
```

**Note**: If you don't have a config file yet, no action needed.

### Step 6: Update MCP Configuration (Claude Desktop)

**IMPORTANT**: This is the critical step to avoid breaking your MCP integration.

1. **Find your Claude Desktop config file**:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. **Edit the config file** and update the MCP server configuration:

**OLD configuration**:
```json
{
  "mcpServers": {
    "plorp": {
      "command": "plorp-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

**NEW configuration**:
```json
{
  "mcpServers": {
    "brainplorp": {
      "command": "brainplorp-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

**Key changes**:
- Server name: `"plorp"` → `"brainplorp"`
- Command: `"plorp-mcp"` → `"brainplorp-mcp"`

3. **Save the file** and **restart Claude Desktop** completely (quit and reopen).

### Step 7: Verify MCP Integration

1. Open Claude Desktop
2. Start a new conversation
3. Try a slash command: `/start` or `/help`
4. Claude should be able to access your brainplorp tools

If tools are not available, check:
- Claude Desktop was fully restarted
- The `brainplorp-mcp` command works in terminal
- The config file syntax is valid JSON
- Your virtual environment is activated when Claude Desktop tries to run the command

### Step 8: Optional - Rename Local Directory

You can optionally rename your local directory from `plorp` to `brainplorp`:

```bash
cd /path/to/parent/directory
mv plorp brainplorp
cd brainplorp
```

This is purely cosmetic and doesn't affect Git or the package functionality.

---

## Troubleshooting

### "Command not found: brainplorp"

**Problem**: The new package isn't installed or not in PATH.

**Solution**:
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall
pip install -e ".[dev]"
```

### "ModuleNotFoundError: No module named 'plorp'"

**Problem**: Some code still references the old package name.

**Solution**: You didn't pull the latest changes. Run:
```bash
git pull
pip install -e ".[dev]"
```

### MCP Tools Not Available in Claude Desktop

**Problem**: Claude Desktop config still references old command name.

**Solution**:
1. Check `claude_desktop_config.json` uses `brainplorp-mcp`
2. Restart Claude Desktop completely
3. Test `brainplorp-mcp` command works in terminal:
   ```bash
   which brainplorp-mcp
   brainplorp-mcp --version
   ```

### Old Config Not Found

**Problem**: Can't find `~/.config/plorp/config.yaml`.

**Solution**: You may not have created a config file yet. Create a new one:
```bash
mkdir -p ~/.config/brainplorp
cat > ~/.config/brainplorp/config.yaml << 'EOF'
vault_path: /path/to/your/obsidian/vault
taskwarrior_data: ~/.task
inbox_email: null
default_editor: vim
EOF
```

---

## What Did NOT Change

- **Git repository URL**: Still points to `github.com/dimatosj/plorp`
- **GitHub repo name**: Still called "plorp" (unless you rename it on GitHub)
- **Your data**: TaskWarrior tasks and Obsidian notes unchanged
- **Vault structure**: Obsidian vault layout unchanged
- **Functionality**: All features work exactly the same

---

## Optional: Rename GitHub Repository

If you want to rename the GitHub repository itself:

1. Go to https://github.com/dimatosj/plorp
2. Click "Settings"
3. In "Repository name", change to `brainplorp`
4. Click "Rename"

Then update your local Git remote:
```bash
git remote set-url origin https://github.com/dimatosj/brainplorp.git
```

---

## Summary of Changes

| What Changed | Old Value | New Value |
|--------------|-----------|-----------|
| Package name | `plorp` | `brainplorp` |
| CLI command | `plorp` | `brainplorp` |
| MCP command | `plorp-mcp` | `brainplorp-mcp` |
| Source directory | `src/plorp/` | `src/brainplorp/` |
| Config directory | `~/.config/plorp/` | `~/.config/brainplorp/` |
| Python imports | `from plorp.*` | `from brainplorp.*` |
| MCP server name | `"plorp"` | `"brainplorp"` |

---

## Quick Reference: Computer 2 Migration Checklist

```bash
# 1. Pull changes
git pull

# 2. Uninstall old package
pip uninstall plorp -y

# 3. Install new package
pip install -e ".[dev]"

# 4. Move config (if exists)
mv ~/.config/plorp ~/.config/brainplorp

# 5. Update Claude Desktop config
# Edit: ~/Library/Application Support/Claude/claude_desktop_config.json
# Change: "plorp" → "brainplorp" and "plorp-mcp" → "brainplorp-mcp"

# 6. Restart Claude Desktop

# 7. Verify
brainplorp --version
brainplorp-mcp --version
```

---

## Questions?

If you encounter issues not covered here, check:
1. Virtual environment is activated
2. All changes were pulled from Git
3. Package was reinstalled with new name
4. Claude Desktop config was updated AND app was restarted
5. Config file moved to new location

The rename is purely cosmetic - all functionality remains the same. The main gotcha is updating the MCP configuration in Claude Desktop.
