# MCP Setup Guide

This guide explains how to configure Claude Desktop to use the plorp MCP server.

## Overview

plorp v1.1 provides an MCP (Model Context Protocol) server that exposes 16 tools to Claude Desktop. These tools allow you to interact with your TaskWarrior tasks and Obsidian notes through natural language.

## Prerequisites

- plorp v1.1 installed (`pip install -e .`)
- Claude Desktop application
- TaskWarrior 3.4.1+
- Obsidian vault configured in `~/.config/plorp/config.yaml`

## Installation Steps

### 1. Install Slash Commands

Run the `init-claude` command to install slash commands:

```bash
plorp init-claude
```

This copies the slash command files to `~/.claude/commands/`:
- `/start` - Generate daily note
- `/review` - End-of-day review
- `/inbox` - Process inbox items
- `/task` - Create a new task
- `/note` - Create a new note

### 2. Configure Claude Desktop

Edit your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Linux**: `~/.config/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the plorp MCP server configuration:

```json
{
  "mcpServers": {
    "plorp": {
      "command": "plorp-mcp",
      "env": {
        "PLORP_CONFIG": "/Users/yourusername/.config/plorp/config.yaml"
      }
    }
  }
}
```

**Important**: Replace `/Users/yourusername` with your actual home directory path.

### 3. Configure plorp

Ensure your plorp configuration exists at `~/.config/plorp/config.yaml`:

```yaml
vault_path: /path/to/your/obsidian/vault
taskwarrior_data: ~/.task
inbox_email: null
default_editor: vim
```

### 4. Restart Claude Desktop

Quit and restart Claude Desktop for the MCP server configuration to take effect.

## Verification

To verify the MCP server is running:

1. Open Claude Desktop
2. Type `/start` - you should see the slash command appear
3. Try creating a daily note: `/start`

You should see Claude call the `plorp_start_day` tool and generate your daily note.

## Available Tools

The plorp MCP server provides these tools:

### Daily Workflow
- `plorp_start_day` - Generate daily note with tasks from TaskWarrior

### Review Workflow
- `plorp_get_review_tasks` - Get uncompleted tasks from daily note
- `plorp_add_review_notes` - Add end-of-day reflections

### Task Operations
- `plorp_mark_task_completed` - Mark a task as done
- `plorp_defer_task` - Defer a task to a new date
- `plorp_drop_task` - Delete a task
- `plorp_set_task_priority` - Change task priority
- `plorp_get_task_info` - Get detailed task information

### Inbox Workflow
- `plorp_get_inbox_items` - List unprocessed inbox items
- `plorp_create_task_from_inbox` - Convert inbox item to task
- `plorp_create_note_from_inbox` - Convert inbox item to note
- `plorp_create_both_from_inbox` - Create both task and linked note
- `plorp_discard_inbox_item` - Mark inbox item as processed

### Notes Workflow
- `plorp_create_note` - Create a standalone note
- `plorp_create_note_with_task` - Create note linked to a task
- `plorp_link_note_to_task` - Link existing note to task

## Slash Commands

After running `plorp init-claude`, you can use these commands in Claude Desktop:

- `/start` - "Start my day" - Generates daily note with tasks
- `/review` - "Review my day" - Interactive end-of-day review
- `/inbox` - "Process my inbox" - Convert inbox items to tasks/notes
- `/task` - "Create a task" - Create TaskWarrior task with optional note
- `/note` - "Create a note" - Create Obsidian note with optional task link

## Troubleshooting

### MCP Server Not Starting

Check the MCP server logs:
```bash
tail -f ~/.config/plorp/mcp.log
```

### Tools Not Appearing in Claude Desktop

1. Verify `plorp-mcp` is in your PATH:
   ```bash
   which plorp-mcp
   ```

2. Check Claude Desktop configuration JSON is valid
3. Restart Claude Desktop

### Permission Errors

Ensure the plorp configuration directory is readable:
```bash
ls -la ~/.config/plorp/
chmod 755 ~/.config/plorp
```

### TaskWarrior Integration Issues

Test TaskWarrior directly:
```bash
task export
```

If this fails, the MCP server won't be able to access tasks.

## Advanced Configuration

### Custom Config Path

Override the default config path by setting the `PLORP_CONFIG` environment variable in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "plorp": {
      "command": "plorp-mcp",
      "env": {
        "PLORP_CONFIG": "/custom/path/to/config.yaml"
      }
    }
  }
}
```

### Debug Mode

Enable debug logging by setting `PLORP_DEBUG`:

```json
{
  "mcpServers": {
    "plorp": {
      "command": "plorp-mcp",
      "env": {
        "PLORP_DEBUG": "1"
      }
    }
  }
}
```

This will log detailed information to `~/.config/plorp/mcp.log`.

## Next Steps

- Read [EXAMPLE_WORKFLOWS.md](EXAMPLE_WORKFLOWS.md) for usage examples
- See [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system design
- Check [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) if upgrading from v1.0
