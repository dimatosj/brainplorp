# plorp

Workflow automation layer for TaskWarrior + Obsidian.

## Status

🚧 **Under Development** - Sprint 0 Complete

plorp is currently in active development. The project structure and test infrastructure are in place.

## What is plorp?

plorp bridges TaskWarrior (task management) and Obsidian (note-taking) through three core workflows:

1. **Daily workflow** - Generate daily notes with tasks from TaskWarrior
2. **Review workflow** - End-of-day processing of incomplete tasks
3. **Inbox workflow** - Email → Markdown → TaskWarrior/Obsidian

## Installation

```bash
# Clone the repository
cd /Users/jsd/Documents/plorp

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

## Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Unix/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install plorp in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

## Quick Start

```bash
# Show help
plorp --help

# Commands (coming in future sprints)
plorp start    # Generate daily note
plorp review   # Review incomplete tasks
plorp inbox    # Process inbox
```

## Development

```bash
# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src/plorp --cov-report=html

# Format code
black src/ tests/

# Type check
mypy src/
```

## Project Structure

See `Docs/plorp_ARCHITECTURE.md` for detailed architecture documentation.

## Documentation

- `Docs/plorp_SPEC.md` - Complete specification
- `Docs/plorp_ARCHITECTURE.md` - Technical architecture
- `Docs/plorp_IMPLEMENTATION_PLAN.md` - Implementation plan

## License

[To be determined]
