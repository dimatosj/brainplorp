# plorp

**Workflow automation for TaskWarrior + Obsidian, with Claude Desktop integration**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-270%20passing-brightgreen.svg)]()

## What is plorp?

plorp bridges TaskWarrior (task management) and Obsidian (note-taking) through an intelligent workflow system. It provides both a traditional CLI and MCP (Model Context Protocol) integration for Claude Desktop.

### Core Workflows

1. **Daily workflow** - Generate daily notes with tasks from TaskWarrior
2. **Review workflow** - End-of-day processing of incomplete tasks
3. **Inbox workflow** - Email → Markdown → TaskWarrior/Obsidian
4. **Notes workflow** - Create and link notes to tasks

### Two Ways to Use plorp

**Traditional CLI**:
```bash
plorp start        # Generate daily note
plorp review       # Review incomplete tasks
plorp inbox process # Process inbox items
plorp note "Title" # Create a note
```

**Claude Desktop Integration** (v1.1):
```
You: /start

Claude: [Generates your daily note with intelligent summaries]
        [Provides task breakdowns and suggestions]
        [Opens files in Obsidian for you]
```

## Quick Start

### Prerequisites

- **Python 3.10+** (check with `python3 --version`)
- **TaskWarrior 3.4.1+** (check with `task --version`)
- **Obsidian** with a vault configured

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/plorp.git
cd plorp

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install plorp
pip install -e ".[dev]"

# Verify installation
plorp --version
```

### Configuration

Create `~/.config/plorp/config.yaml`:

```yaml
vault_path: /path/to/your/obsidian/vault
taskwarrior_data: ~/.task
inbox_email: null
default_editor: vim
```

### First Run

```bash
# Generate your first daily note
plorp start

# Output:
# ✅ Created daily note: /vault/daily/2025-10-06.md
#
# 📊 Task Summary:
#   Overdue: 0
#   Due today: 5
#   Recurring: 3
#   Total: 8
```

## Features

### v1.1 (Current)

✅ **Full CLI Support**
- Daily note generation from TaskWarrior tasks
- Interactive end-of-day review
- Inbox processing (email → tasks/notes)
- Note creation with bidirectional task linking
- Task operations (complete, defer, priority, delete)

✅ **MCP Server for Claude Desktop**
- 16 tools exposed to Claude Desktop
- Natural language task management
- Intelligent workflow guidance
- Slash commands (`/start`, `/review`, `/inbox`, `/task`, `/note`)

✅ **Robust Architecture**
- Core business logic layer (pure functions)
- MCP integration layer (async wrappers)
- CLI layer (traditional interface)
- 270 passing tests (98% coverage)

✅ **Type-Safe Design**
- TypedDict for all return values
- JSON-serializable for MCP
- Full type hints throughout

## Usage Examples

### CLI Examples

```bash
# Morning routine
plorp start
open "$(plorp start --date 2025-10-06 | grep 'Created' | awk '{print $NF}')"

# Evening review
plorp review
# Interactive prompts for each uncompleted task

# Process inbox
plorp inbox process
# Convert emails to tasks or notes

# Create note linked to task
plorp note "Sprint Planning" --task abc-123 --type meeting

# Link existing note to task
plorp link def-456 notes/architecture-decisions.md
```

### Claude Desktop Examples

See [EXAMPLE_WORKFLOWS.md](Docs/EXAMPLE_WORKFLOWS.md) for detailed examples.

```
You: /start

Claude: [Generates daily note, provides intelligent summary]

You: /review

Claude: [Guides you through task review with context-aware suggestions]

You: I need to track research on deployment tools

Claude: [Creates project note and linked tasks automatically]
```

## Architecture

plorp v1.1 uses a layered architecture:

```
┌─────────────────────────────────────────────┐
│  Interfaces: CLI + MCP (Claude Desktop)    │
├─────────────────────────────────────────────┤
│  Core: Pure business logic (TypedDict)     │
├─────────────────────────────────────────────┤
│  Integrations: TaskWarrior + Obsidian      │
└─────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](Docs/ARCHITECTURE.md) for detailed design documentation.

## Documentation

- **[MCP Setup Guide](Docs/MCP_SETUP.md)** - Configure Claude Desktop integration
- **[Architecture](Docs/ARCHITECTURE.md)** - System design and layer responsibilities
- **[Migration Guide](Docs/MIGRATION_GUIDE.md)** - Upgrade from v1.0 to v1.1
- **[Example Workflows](Docs/EXAMPLE_WORKFLOWS.md)** - Practical usage examples
- **[Complete Specification](Docs/plorp_SPEC.md)** - Full product specification
- **[TaskWarrior Integration](Docs/plorp_TASKWARRIOR_INTEGRATION.md)** - Integration details

## Development

### Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src/plorp --cov-report=html

# Specific test file
pytest tests/test_core/test_daily.py -v

# Single test
pytest tests/test_core/test_daily.py::test_start_day_creates_note -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Type checking
mypy src/
```

### Project Structure

```
plorp/
├── src/plorp/
│   ├── cli.py              # CLI commands (thin wrapper)
│   ├── config.py           # Configuration management
│   ├── core/               # Core business logic ⭐
│   │   ├── types.py        # TypedDict definitions
│   │   ├── exceptions.py   # Custom exceptions
│   │   ├── daily.py        # Daily workflow
│   │   ├── review.py       # Review workflow
│   │   ├── tasks.py        # Task operations
│   │   ├── inbox.py        # Inbox processing
│   │   └── notes.py        # Note creation/linking
│   ├── mcp/                # MCP server ⭐
│   │   └── server.py       # 16 tools for Claude Desktop
│   ├── integrations/       # External tool adapters
│   │   ├── taskwarrior.py  # TaskWarrior CLI wrapper
│   │   └── obsidian.py     # Markdown file operations
│   ├── parsers/            # Data parsing
│   │   └── markdown.py     # Markdown parsing utilities
│   ├── utils/              # Utilities
│   │   ├── dates.py        # Date formatting
│   │   ├── files.py        # File operations
│   │   └── prompts.py      # Interactive prompts
│   └── slash_commands/     # Claude Desktop slash commands
├── tests/                  # 270 passing tests
└── Docs/                   # Documentation
```

## Requirements

- **Python**: 3.10+ (for MCP support)
- **TaskWarrior**: 3.4.1+ (SQLite backend via TaskChampion)
- **Obsidian**: Any recent version (for vault access)
- **Claude Desktop**: Optional (for MCP integration)

## Roadmap

### v1.1 (Current - Sprint 6) ✅
- MCP server implementation
- Slash commands for Claude Desktop
- Core layer refactoring
- Full test coverage

### v1.2 (Future)
- Web UI for browser-based access
- Mobile companion app
- Advanced task filtering
- Custom workflow templates
- Plugin system for extensions

### v2.0 (Vision)
- Multi-vault support
- Team collaboration features
- Cloud sync integration
- Advanced AI suggestions
- Third-party integrations (Todoist, Notion, etc.)

## Contributing

plorp is currently in active development. Contributions welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest tests/`)
6. Format code (`black src/ tests/`)
7. Commit changes (`git commit -m 'Add amazing feature'`)
8. Push to branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## Philosophy

plorp follows these design principles:

- **Simplicity First**: No custom codes, no complex abstractions
- **Markdown-Centric**: All data in plain markdown files
- **UUID-Based Linking**: Stable task references across sync
- **Layered Architecture**: Separation of concerns (core, MCP, CLI)
- **Type-Safe**: TypedDict for all interfaces
- **Testable**: Pure functions, no hidden dependencies
- **Interoperable**: Works with existing TaskWarrior/Obsidian workflows

## Support

- **Issues**: https://github.com/yourusername/plorp/issues
- **Documentation**: See `Docs/` directory
- **Questions**: Open a GitHub Discussion

## License

[To be determined]

## Acknowledgments

- **TaskWarrior**: Robust task management foundation
- **Obsidian**: Powerful markdown-based note-taking
- **Claude Desktop**: AI-powered workflow assistance via MCP
- **MCP**: Model Context Protocol enabling AI tool integration

---

**plorp v1.1** - Built with ❤️ for productive workflows
