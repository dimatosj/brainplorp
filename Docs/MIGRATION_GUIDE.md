# Migration Guide: v1.0 → v1.1

This guide helps you migrate from plorp v1.0 to v1.1, which introduces MCP support while maintaining backward compatibility.

## What's New in v1.1

### New Features

1. **MCP Server** - Expose plorp tools to Claude Desktop via Model Context Protocol
2. **Slash Commands** - Quick commands for Claude Desktop (`/start`, `/review`, `/inbox`, `/task`, `/note`)
3. **Python 3.10+** - Upgraded from Python 3.8 for MCP SDK compatibility
4. **Refactored Architecture** - Core layer, MCP layer, CLI layer separation
5. **TypedDict Returns** - All core functions return structured TypedDict for JSON serialization

### Breaking Changes

⚠️ **Python Version**: Requires Python 3.10+ (previously 3.8+)

⚠️ **Import Paths**: If you were importing internal modules, paths have changed:
- `plorp.workflows.daily` → `plorp.core.daily`
- `plorp.workflows.inbox` → `plorp.core.inbox`
- `plorp.workflows.notes` → `plorp.core.notes`

### Backward Compatible

✅ **CLI Commands**: All v1.0 commands work exactly the same
✅ **Configuration**: Same `~/.config/plorp/config.yaml` format
✅ **File Formats**: Daily notes, inbox files, and note frontmatter unchanged
✅ **TaskWarrior Integration**: Same integration strategy

## Migration Steps

### 1. Upgrade Python

Check your Python version:

```bash
python3 --version
```

If < 3.10, install Python 3.10+:

**macOS (Homebrew)**:
```bash
brew install python@3.10
```

**Ubuntu/Debian**:
```bash
sudo apt-get install python3.10 python3.10-venv
```

### 2. Update plorp

If installed from source:

```bash
cd /path/to/plorp
git pull
rm -rf .venv
python3.10 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

If installed via pip (future):

```bash
pip install --upgrade plorp
```

### 3. Verify CLI Still Works

Test existing commands:

```bash
plorp start
plorp review
plorp inbox process
plorp note "Test Note"
```

Everything should work exactly as before.

### 4. (Optional) Set Up MCP

If you want to use Claude Desktop integration:

```bash
plorp init-claude
```

Then configure Claude Desktop (see [MCP_SETUP.md](MCP_SETUP.md)).

## Code Migration

### If You Were Using Internal APIs

#### Old Code (v1.0)

```python
from plorp.workflows.daily import start

# This will break in v1.1
start(vault_path=Path("/path/to/vault"))
```

#### New Code (v1.1)

```python
from plorp.core import start_day
from datetime import date

# New signature with explicit parameters
result = start_day(date.today(), Path("/path/to/vault"))

# Returns TypedDict with structured data
print(result["note_path"])
print(result["summary"]["total_count"])
```

### Return Type Changes

#### v1.0

```python
# Returned Path object
note_path = start(vault_path)
print(note_path)  # PosixPath('/vault/daily/2025-10-06.md')
```

#### v1.1

```python
# Returns TypedDict
result = start_day(date.today(), vault_path)
print(result)
# {
#   "date": "2025-10-06",
#   "note_path": "/vault/daily/2025-10-06.md",
#   "summary": {
#     "overdue_count": 0,
#     "due_today_count": 3,
#     "recurring_count": 1,
#     "total_count": 4
#   }
# }

note_path = result["note_path"]
```

### Exception Changes

#### v1.0

```python
try:
    start(vault_path)
except FileExistsError:
    print("Note already exists")
```

#### v1.1

```python
from plorp.core.exceptions import DailyNoteExistsError

try:
    result = start_day(date.today(), vault_path)
except DailyNoteExistsError as e:
    print(f"Note already exists: {e.note_path}")
    print(f"Date: {e.date}")
```

### Import Map

| v1.0 Import | v1.1 Import |
|-------------|-------------|
| `plorp.workflows.daily.start` | `plorp.core.start_day` |
| `plorp.workflows.daily.review` | `plorp.core.get_review_tasks` + `plorp.core.add_review_notes` |
| `plorp.workflows.inbox.process` | `plorp.core.get_inbox_items` + processing functions |
| `plorp.workflows.notes.create_note_with_task_link` | `plorp.core.create_note_linked_to_task` |
| `plorp.workflows.notes.link_note_to_task` | `plorp.core.link_note_to_task` |

## Configuration Changes

### No Changes Required

Your existing `~/.config/plorp/config.yaml` works without modifications:

```yaml
vault_path: /Users/you/Documents/vault
taskwarrior_data: ~/.task
inbox_email: null
default_editor: vim
```

### Optional: MCP-Specific Config

If using MCP, you can optionally set environment variables in Claude Desktop config:

```json
{
  "mcpServers": {
    "plorp": {
      "command": "plorp-mcp",
      "env": {
        "PLORP_CONFIG": "/custom/path/to/config.yaml",
        "PLORP_DEBUG": "1"
      }
    }
  }
}
```

## File Format Changes

### No Changes

All file formats remain compatible:

- **Daily notes**: Same YAML frontmatter + markdown checkboxes
- **Inbox files**: Same `## Unprocessed` / `## Processed` sections
- **Note frontmatter**: Same `tasks: [uuid1, uuid2]` format
- **TaskWarrior**: Same UUID-based task references

### Example Daily Note (Same Format)

```markdown
---
date: 2025-10-06
type: daily
plorp_version: 1.1.0
---

# 2025-10-06 Sunday

## Overdue

- [ ] Fix the bug (project: work, due: 2025-10-05, uuid: abc-123)

## Due Today

- [ ] Team meeting (due: 2025-10-06, uuid: def-456)

## Recurring

- [ ] Daily standup (due: 2025-10-06, uuid: ghi-789)
```

## Testing Your Migration

### 1. Test CLI Commands

```bash
# Generate daily note
plorp start

# Review tasks
plorp review

# Process inbox
plorp inbox process

# Create note
plorp note "Migration Test"

# Link note to task
plorp link abc-123 notes/migration-test.md
```

### 2. Test MCP (if configured)

In Claude Desktop:

1. Type `/start` - Should generate daily note
2. Type `/review` - Should list uncompleted tasks
3. Type `/inbox` - Should show inbox items

### 3. Verify Data Integrity

Check that your existing data is untouched:

```bash
# Daily notes still exist
ls ~/Documents/vault/daily/

# Inbox files still exist
ls ~/Documents/vault/inbox/

# TaskWarrior tasks unchanged
task export | jq '.[0]'
```

## Rollback Plan

If you need to roll back to v1.0:

### 1. Downgrade Python (if necessary)

```bash
# Recreate venv with Python 3.8
rm -rf .venv
python3.8 -m venv .venv
source .venv/bin/activate
```

### 2. Checkout v1.0 Tag

```bash
cd /path/to/plorp
git checkout v1.0.0
pip install -e ".[dev]"
```

### 3. Remove MCP Config

Edit `~/.config/Claude/claude_desktop_config.json` and remove the `plorp` MCP server entry.

### 4. Remove Slash Commands (optional)

```bash
rm -rf ~/.claude/commands/
```

## Common Migration Issues

### Issue: `ModuleNotFoundError: No module named 'mcp'`

**Solution**: Ensure you're using Python 3.10+ and reinstalled dependencies:

```bash
python3 --version  # Should be 3.10+
pip install -e ".[dev]"
```

### Issue: `ImportError: cannot import name 'start'`

**Solution**: Update import paths:

```python
# Old
from plorp.workflows.daily import start

# New
from plorp.core import start_day
```

### Issue: `TypeError: start() missing 1 required positional argument`

**Solution**: Update function signature:

```python
# Old
start(vault_path=path)

# New
start_day(date.today(), vault_path=path)
```

### Issue: MCP server not appearing in Claude Desktop

**Solution**:

1. Verify `plorp-mcp` is installed:
   ```bash
   which plorp-mcp
   ```

2. Check Claude Desktop config is valid JSON

3. Restart Claude Desktop completely (quit and reopen)

4. Check MCP logs:
   ```bash
   tail -f ~/.config/plorp/mcp.log
   ```

## Getting Help

- **Documentation**: See [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- **Examples**: See [EXAMPLE_WORKFLOWS.md](EXAMPLE_WORKFLOWS.md) for usage
- **MCP Setup**: See [MCP_SETUP.md](MCP_SETUP.md) for Claude Desktop config
- **Issues**: https://github.com/yourusername/plorp/issues

## Frequently Asked Questions

### Q: Do I need to use MCP?

No! The CLI works exactly as before. MCP is optional for Claude Desktop integration.

### Q: Will my existing daily notes/tasks still work?

Yes. All file formats are backward compatible. v1.1 can read v1.0 data.

### Q: Can I use both CLI and MCP?

Yes. They share the same core logic and operate on the same data.

### Q: What if I don't have Python 3.10?

You can continue using v1.0, which supports Python 3.8+. However, MCP requires 3.10+.

### Q: Do I need Claude Desktop to use v1.1?

No. The CLI improvements work without Claude Desktop.

### Q: Will v1.2 support Python 3.8?

No. v1.1+ requires Python 3.10 due to MCP SDK dependencies.

## Summary

- ✅ Upgrade Python to 3.10+
- ✅ Reinstall plorp with new dependencies
- ✅ Test CLI commands (should work unchanged)
- ✅ (Optional) Set up MCP for Claude Desktop
- ✅ Update import paths if using internal APIs
- ✅ Enjoy MCP features!
