# Installation Troubleshooting Guide

This guide covers common installation and configuration issues for brainplorp.

## Quick Diagnosis

If you're experiencing any issues, run the diagnostic command first:

```bash
brainplorp doctor
```

This will check:
- ✅ TaskWarrior installation and functionality
- ✅ Python dependencies
- ✅ Configuration file validity
- ✅ Obsidian vault accessibility
- ✅ Claude Desktop MCP setup

The `doctor` command will provide specific fix instructions for any detected issues.

---

## TaskWarrior Issues

### Issue: TaskWarrior Hangs Indefinitely

**Symptoms**:
- `brainplorp start` never completes
- `brainplorp doctor` reports timeout errors
- `task --version` hangs on first run
- Terminal shows no output, just hangs

**Cause**: TaskWarrior 3.4.1 has a known bug that causes it to hang indefinitely during first initialization.

**Fix (macOS with Homebrew)**:
```bash
# Check current TaskWarrior version
task --version  # If this hangs, you have the 3.4.1 bug

# Kill any hung TaskWarrior processes
killall task

# Uninstall broken version
brew uninstall task

# Install pinned working version (3.4.0)
brew install dimatosj/brainplorp/taskwarrior-pinned

# Verify installation
task --version  # Should return immediately with "3.4.0"

# Run brainplorp diagnostics
brainplorp doctor
```

**Fix (Linux/other platforms)**:

1. **Remove TaskWarrior 3.4.1**:
   ```bash
   # Debian/Ubuntu
   sudo apt remove taskwarrior

   # Arch Linux
   sudo pacman -R taskwarrior

   # Or if installed from source
   sudo rm /usr/local/bin/task
   ```

2. **Install TaskWarrior 3.4.0 from source**:
   ```bash
   # Install dependencies
   # Debian/Ubuntu:
   sudo apt install cmake g++ rust-all libgnutls28-dev uuid-dev

   # Arch Linux:
   sudo pacman -S cmake gcc rust gnutls util-linux

   # Clone and build v3.4.0
   cd /tmp
   git clone https://github.com/GothenburgBitFactory/taskwarrior.git
   cd taskwarrior
   git checkout v3.4.0  # Pin to working version

   cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
   cmake --build build
   sudo cmake --install build

   # Verify
   task --version  # Should show "3.4.0"
   ```

3. **Run diagnostics**:
   ```bash
   brainplorp doctor
   ```

**Why This Happens**:
TaskWarrior 3.4.1 introduced a regression bug in the first-run initialization code. The bug causes the process to wait for user input that never arrives, resulting in an infinite hang. This is an upstream TaskWarrior issue, not a brainplorp bug.

**Status**: Fixed in brainplorp v1.6.2+ by automatically pinning to TaskWarrior 3.4.0 via Homebrew formula.

---

### Issue: TaskWarrior Not Found

**Symptoms**:
- `brainplorp doctor` reports "TaskWarrior not installed"
- Commands fail with "task: command not found"

**Fix**:

**macOS (Homebrew)**:
```bash
brew install dimatosj/brainplorp/taskwarrior-pinned
```

**Linux (Debian/Ubuntu)**:
```bash
# Option 1: Package manager (may install 3.4.1 - not recommended)
sudo apt update
sudo apt install taskwarrior

# Option 2: Build v3.4.0 from source (recommended)
# See "Install TaskWarrior 3.4.0 from source" instructions above
```

**Verify**:
```bash
task --version
brainplorp doctor
```

---

### Issue: TaskWarrior Database Corrupted

**Symptoms**:
- `brainplorp doctor` reports timeout or errors
- `task export` fails
- Error messages about SQLite database

**Fix**:

```bash
# 1. Backup your tasks (if possible)
task export > ~/taskwarrior-backup.json

# 2. Check database integrity
cd ~/.task
sqlite3 taskchampion.sqlite3 "PRAGMA integrity_check;"

# 3. If corrupted, restore from backup
rm -rf ~/.task/*
task import ~/taskwarrior-backup.json

# 4. Verify
brainplorp doctor
```

**Prevention**:
- Never edit TaskWarrior's SQLite database directly
- Always use `task` CLI commands for modifications
- Set up TaskChampion sync server for automatic backups

---

## Python/Installation Issues

### Issue: Command Not Found: brainplorp

**Symptoms**:
- `brainplorp: command not found` after installation

**Fix**:

1. **Check if installed**:
   ```bash
   pip list | grep brainplorp
   ```

2. **If not installed, install it**:
   ```bash
   pip install -e .
   # or
   brew install dimatosj/brainplorp/brainplorp
   ```

3. **If installed but not in PATH**:
   ```bash
   # Find where pip installed it
   which python3
   python3 -m site --user-base

   # Add to PATH (add to ~/.bashrc or ~/.zshrc)
   export PATH="$PATH:$(python3 -m site --user-base)/bin"

   # Reload shell
   source ~/.bashrc  # or source ~/.zshrc
   ```

---

### Issue: Python Version Too Old

**Symptoms**:
- `brainplorp doctor` fails with syntax errors
- Import errors mentioning type hints

**Fix**:

```bash
# Check Python version
python3 --version  # Must be 3.10 or higher

# If too old, upgrade Python
# macOS:
brew install python@3.12

# Linux (Debian/Ubuntu):
sudo apt update
sudo apt install python3.12

# Verify
python3.12 --version

# Reinstall brainplorp with correct Python
python3.12 -m pip install -e .
```

---

### Issue: Missing Python Dependencies

**Symptoms**:
- `brainplorp doctor` reports missing packages
- ImportError when running commands

**Fix**:

```bash
# Install all dependencies
pip install -e ".[dev]"

# Or install specific missing packages
pip install click pyyaml rich mcp

# Verify
brainplorp doctor
```

---

## Configuration Issues

### Issue: Config File Not Found

**Symptoms**:
- `brainplorp doctor` reports "Configuration file not found"
- Commands fail with config errors

**Fix**:

```bash
# Run setup wizard to create config
brainplorp setup

# Or create manually
mkdir -p ~/.config/brainplorp
cat > ~/.config/brainplorp/config.yaml <<EOF
vault_path: /path/to/your/obsidian/vault
taskwarrior_data: ~/.task
inbox_email: null
default_editor: vim
EOF

# Verify
brainplorp doctor
```

---

### Issue: Invalid Vault Path

**Symptoms**:
- `brainplorp doctor` warns "Vault not found"
- `brainplorp start` fails with vault errors

**Fix**:

1. **Find your Obsidian vault path**:
   - Open Obsidian
   - Settings → Files and Links → Look at "Vault folder location"

2. **Update config**:
   ```bash
   # Edit config file
   vim ~/.config/brainplorp/config.yaml

   # Update vault_path to match Obsidian location
   vault_path: /Users/yourname/Documents/ObsidianVault
   ```

3. **Verify**:
   ```bash
   brainplorp doctor
   ```

---

## Claude Desktop MCP Issues

### Issue: MCP Tools Not Showing in Claude Desktop

**Symptoms**:
- Claude Desktop doesn't show brainplorp tools
- No slash commands available

**Fix**:

1. **Check if MCP is configured**:
   ```bash
   brainplorp doctor
   # Look for "MCP Server" check result
   ```

2. **Run MCP configuration**:
   ```bash
   brainplorp mcp
   # or
   brainplorp setup  # Includes MCP setup
   ```

3. **Verify config file**:
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

   Should contain:
   ```json
   {
     "mcpServers": {
       "brainplorp": {
         "command": "/path/to/brainplorp-mcp",
         "args": [],
         "env": {}
       }
     }
   }
   ```

4. **Restart Claude Desktop completely**:
   - Quit Claude Desktop (Cmd+Q on macOS)
   - Reopen Claude Desktop
   - Try typing `/` to see slash commands

---

### Issue: MCP Tools Error Out

**Symptoms**:
- Claude Desktop shows brainplorp tools but they fail
- Error messages in Claude Desktop

**Fix**:

1. **Check brainplorp installation**:
   ```bash
   brainplorp doctor
   ```

2. **Check MCP logs**:
   ```bash
   # macOS
   cat ~/Library/Logs/Claude/mcp*.log
   ```

3. **Common causes**:
   - TaskWarrior not working → Fix TaskWarrior first
   - Config file invalid → Run `brainplorp doctor`
   - Vault path wrong → Update config vault_path

---

## Multi-Computer Sync Issues

### Issue: Tasks Not Syncing Between Computers

**Symptoms**:
- Computer 1 creates tasks, Computer 2 doesn't see them
- TaskWarrior sync fails

**Fix**:

See [MULTI_COMPUTER_SETUP.md](MULTI_COMPUTER_SETUP.md) for complete setup instructions.

**Quick checklist**:
1. **Both computers have same TaskChampion server configured**:
   ```bash
   task config sync.server.url
   # Should show same URL on both computers
   ```

2. **Run sync manually**:
   ```bash
   task sync
   ```

3. **Check for errors**:
   ```bash
   task sync 2>&1 | grep -i error
   ```

---

## Getting Help

If you're still experiencing issues after following this guide:

1. **Run diagnostics and capture output**:
   ```bash
   brainplorp doctor --verbose > doctor-output.txt 2>&1
   ```

2. **Check brainplorp version**:
   ```bash
   brainplorp --version
   ```

3. **Check TaskWarrior version**:
   ```bash
   task --version
   ```

4. **Open an issue**:
   - Go to: https://github.com/dimatosj/brainplorp/issues
   - Include:
     - Output from `brainplorp doctor --verbose`
     - brainplorp version
     - TaskWarrior version
     - Operating system and version
     - Description of the issue

---

## Known Issues

See [README.md Known Issues section](../README.md#known-issues) for current known issues and their status.

## Additional Resources

- [MCP Setup Guide](MCP_SETUP.md) - Claude Desktop integration
- [Multi-Computer Setup](MULTI_COMPUTER_SETUP.md) - Sync setup guide
- [Architecture](ARCHITECTURE.md) - System design documentation
- [GitHub Issues](https://github.com/dimatosj/brainplorp/issues) - Report bugs
