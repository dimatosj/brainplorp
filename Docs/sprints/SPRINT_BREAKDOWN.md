# plorp Sprint Breakdown

**Date:** October 6, 2025
**Purpose:** Define implementation sprints for distributed development across Claude Code instances

---

## Overview

Each sprint is designed to be implemented by a separate Claude Code engineering instance following TDD principles. The PM/Architect instance (this one) will:
1. Write detailed sprint specs
2. Hand off to engineering instances
3. Field clarifying questions
4. Update specs with Q&A
5. Evaluate implementation
6. Iterate as needed

---

## Sprint Dependencies

```
Sprint 0: Foundation
    ↓
Sprint 1: TaskWarrior Integration ──┐
    ↓                                │
Sprint 2: Daily Note Generation     │
    ↓                                │
Sprint 3: Review Workflow            │
    ↓                                │
Sprint 4: Inbox Processing          ←┘
    ↓
Sprint 5: Note Linking
```

**Key principle:** Each sprint must be completable in isolation once its dependencies are met.

---

## Sprint 0: Project Setup & Test Infrastructure

**Duration:** 2-4 hours
**Dependencies:** None
**Engineering Instance:** Fresh instance with no prior context

### Scope

- Create complete Python project structure
- Set up pyproject.toml with dependencies
- Configure pytest with coverage
- Create test fixtures and utilities
- Set up black formatter and mypy type checking
- Create basic CLI entry point (no functionality yet)
- Write "Hello World" smoke test

### Success Criteria

```bash
# Can install
pip install -e .

# Can run tests
pytest tests/ -v
# → All tests pass (even if just smoke tests)

# Can invoke CLI
plorp --help
# → Shows help text

# Coverage configured
pytest tests/ --cov=src/plorp --cov-report=html
# → Generates coverage report
```

### Deliverables

- Complete project structure
- Working test infrastructure
- CI/CD configuration (GitHub Actions)
- Installation script skeleton
- Sprint 0 completion report in spec

### Handoff to Next Sprint

Sprint 1 needs:
- Working test infrastructure
- Ability to add new modules in `src/plorp/integrations/`
- Ability to write and run tests in `tests/test_integrations/`

---

## Sprint 1: TaskWarrior Integration Layer

**Duration:** 1-2 days
**Dependencies:** Sprint 0 complete
**Engineering Instance:** Fresh instance + Sprint 0 handoff

### Scope

**TDD approach:** Write tests first for each function, then implement.

**Module:** `src/plorp/integrations/taskwarrior.py`

Functions to implement:
```python
def run_task_command(args: List[str], capture: bool = True) -> subprocess.CompletedProcess
def get_tasks(filter_args: List[str]) -> List[Dict]
def get_overdue_tasks() -> List[Dict]
def get_due_today() -> List[Dict]
def get_recurring_today() -> List[Dict]
def get_task_info(uuid: str) -> Optional[Dict]
def create_task(description: str, **kwargs) -> Optional[str]
def mark_done(uuid: str) -> bool
def defer_task(uuid: str, new_due: str) -> bool
def set_priority(uuid: str, priority: str) -> bool
def delete_task(uuid: str) -> bool
def add_annotation(uuid: str, text: str) -> bool
```

### Testing Strategy

**Unit tests with mocked subprocess:**
- Mock all `subprocess.run()` calls
- Test JSON parsing from TaskWarrior export
- Test error handling (task not found, invalid filter, etc.)

**Integration tests (optional, requires TaskWarrior installed):**
- Mark these with `@pytest.mark.integration`
- Can be skipped in CI if TaskWarrior not available

### Success Criteria

```bash
# All tests pass
pytest tests/test_integrations/test_taskwarrior.py -v
# → 20+ tests pass

# Coverage > 90%
pytest tests/test_integrations/test_taskwarrior.py --cov=src/plorp/integrations/taskwarrior
# → Coverage report shows >90%

# Manual verification (if TaskWarrior installed)
python3 -c "from plorp.integrations.taskwarrior import get_due_today; print(get_due_today())"
# → Returns list of tasks or []
```

### Deliverables

- `src/plorp/integrations/taskwarrior.py` fully implemented
- `tests/test_integrations/test_taskwarrior.py` with comprehensive tests
- Documentation in docstrings
- Sprint 1 completion report with:
  - What was implemented
  - Test coverage achieved
  - Any deviations from spec
  - Known limitations or edge cases

### Handoff to Next Sprint

Sprint 2 needs:
- Working TaskWarrior integration
- Ability to call `get_overdue_tasks()`, `get_due_today()`, `get_recurring_today()`
- Returns tasks as list of dicts with standard TaskWarrior fields

---

## Sprint 2: Daily Note Generation

**Duration:** 1-2 days
**Dependencies:** Sprint 0, Sprint 1 complete
**Engineering Instance:** Fresh instance + Sprint 0 & 1 handoff

### Scope

**Modules:**
- `src/plorp/workflows/daily.py` (start functionality only)
- `src/plorp/utils/files.py`
- `src/plorp/config.py`
- Update `src/plorp/cli.py` to add `start` command

**TDD approach:** Write tests for each component before implementation.

### Functions to Implement

**files.py:**
```python
def read_file(path: Path) -> str
def write_file(path: Path, content: str) -> None
def ensure_directory(path: Path) -> None
```

**config.py:**
```python
def get_config_path() -> Path
def load_config() -> Dict
def save_config(config: Dict) -> None
DEFAULT_CONFIG: Dict
```

**daily.py:**
```python
def start(config: Dict) -> Path
def generate_daily_note_content(today: date, overdue: List, due_today: List, recurring: List) -> str
def format_task_checkbox(task: Dict) -> str
```

**cli.py:**
```python
@cli.command()
def start(config): ...
```

### Testing Strategy

**Unit tests:**
- Test markdown generation with various task lists
- Test task checkbox formatting
- Test file operations with tmp_path fixtures
- Test config loading/saving with tmp_path

**Integration test:**
- Mock TaskWarrior integration
- Generate daily note
- Verify file created and content correct

### Success Criteria

```bash
# Unit tests pass
pytest tests/test_workflows/test_daily.py -v
pytest tests/test_utils/test_files.py -v
pytest tests/test_config.py -v

# CLI works
plorp start
# → Creates vault/daily/YYYY-MM-DD.md
# → Prints summary

# Generated file has correct format
cat ~/vault/daily/$(date +%Y-%m-%d).md
# → Contains YAML front matter
# → Contains task checkboxes with UUIDs
# → Formatted correctly
```

### Deliverables

- All modules implemented with tests
- `plorp start` command functional
- Config system working
- Sprint 2 completion report

### Handoff to Next Sprint

Sprint 3 needs:
- Working daily note generation
- Ability to read daily notes
- Working file utilities
- Working config system

---

## Sprint 3: Review Workflow

**Duration:** 2-3 days
**Dependencies:** Sprint 0, 1, 2 complete
**Engineering Instance:** Fresh instance + Sprints 0, 1, 2 handoff

### Scope

**Modules:**
- `src/plorp/parsers/markdown.py`
- `src/plorp/utils/prompts.py`
- `src/plorp/workflows/daily.py` (add review functionality)
- Update `src/plorp/cli.py` to add `review` command

### Functions to Implement

**markdown.py:**
```python
def parse_daily_note_tasks(note_path: Path) -> List[Tuple[str, str]]
def parse_frontmatter(content: str) -> Dict
```

**prompts.py:**
```python
def prompt(message: str) -> str
def prompt_choice(options: List[str]) -> int
def confirm(message: str) -> bool
```

**daily.py (additions):**
```python
def review(config: Dict) -> None
def append_review_section(daily_path: Path, decisions: List[str]) -> None
```

### Testing Strategy

**Unit tests:**
- Test markdown parsing with fixture files
- Test prompt utilities with mocked input
- Test review section appending

**Integration test:**
- Create sample daily note
- Mock user inputs
- Run review
- Verify TaskWarrior called correctly
- Verify daily note updated

### Success Criteria

```bash
# Tests pass
pytest tests/test_parsers/test_markdown.py -v
pytest tests/test_utils/test_prompts.py -v
pytest tests/test_workflows/test_review.py -v

# CLI works (with mocked input)
echo -e "1\n1\nq\n" | plorp review
# → Processes uncompleted tasks
# → Updates daily note with review section
```

### Deliverables

- Markdown parser implemented
- Interactive prompts working
- Review workflow complete
- Sprint 3 completion report

### Handoff to Next Sprint

Sprint 4 needs:
- Working markdown parser
- Working file utilities (from Sprint 2)
- Working TaskWarrior integration (from Sprint 1)

---

## Sprint 4: Inbox Processing

**Duration:** 2-3 days
**Dependencies:** Sprint 0, 1, 2 complete (Sprint 3 optional)
**Engineering Instance:** Fresh instance + Sprints 0, 1, 2 handoff

### Scope

**Modules:**
- `src/plorp/integrations/obsidian.py`
- `src/plorp/workflows/inbox.py`
- `src/plorp/parsers/markdown.py` (add inbox parsing)
- Update `src/plorp/cli.py` to add `inbox` command

### Functions to Implement

**obsidian.py:**
```python
def create_note(vault_path: Path, title: str, note_type: str, metadata: Dict) -> Path
def get_vault_path(config: Dict) -> Path
```

**markdown.py (additions):**
```python
def parse_inbox_items(inbox_path: Path) -> List[str]
def mark_item_processed(inbox_path: Path, item_text: str, action: str) -> None
```

**inbox.py:**
```python
def process(config: Dict) -> None
def get_current_inbox_path(config: Dict) -> Path
def process_item_as_task(item: str, config: Dict) -> Optional[str]
def process_item_as_note(item: str, config: Dict) -> Optional[Path]
```

### Testing Strategy

**Unit tests:**
- Test inbox parsing
- Test note creation
- Test item processing logic

**Integration test:**
- Create sample inbox file
- Mock user inputs
- Run processing
- Verify tasks created
- Verify notes created
- Verify inbox file updated

### Success Criteria

```bash
# Tests pass
pytest tests/test_integrations/test_obsidian.py -v
pytest tests/test_workflows/test_inbox.py -v

# CLI works
plorp inbox process
# → Processes unprocessed items
# → Creates tasks/notes as directed
# → Updates inbox file
```

### Deliverables

- Obsidian integration implemented
- Inbox workflow complete
- Sprint 4 completion report

### Handoff to Next Sprint

Sprint 5 needs:
- Working note creation (from Sprint 4)
- Working TaskWarrior annotations (from Sprint 1)
- Working markdown front matter parsing (from Sprint 3 or this sprint)

---

## Sprint 5: Note Linking

**Duration:** 1-2 days
**Dependencies:** Sprint 0, 1, 2, 4 complete
**Engineering Instance:** Fresh instance + Sprints 0, 1, 2, 4 handoff

### Scope

**Modules:**
- `src/plorp/workflows/notes.py`
- `src/plorp/parsers/markdown.py` (add front matter editing)
- Update `src/plorp/cli.py` to add `note` and `link` commands

### Functions to Implement

**markdown.py (additions):**
```python
def add_frontmatter_field(content: str, field: str, value: Any) -> str
def extract_task_uuids_from_note(note_path: Path) -> List[str]
```

**notes.py:**
```python
def create_note(config: Dict, title: str, task_uuid: Optional[str] = None) -> Path
def link_note_to_task(note_path: Path, task_uuid: str, vault_path: Path) -> None
def get_linked_notes(task_uuid: str) -> List[str]
```

### Testing Strategy

**Unit tests:**
- Test front matter manipulation
- Test bidirectional linking logic
- Test note creation with task links

**Integration test:**
- Create task in TaskWarrior
- Create linked note
- Verify bidirectional links
- Test in review workflow (if Sprint 3 complete)

### Success Criteria

```bash
# Tests pass
pytest tests/test_workflows/test_notes.py -v

# CLI works
plorp note "Meeting Notes" --task abc-123
# → Creates note with task UUID in front matter
# → Adds annotation to task

plorp link abc-123 vault/notes/existing-note.md
# → Links existing note to task
# → Updates both directions
```

### Deliverables

- Note linking implemented
- Bidirectional links working
- Sprint 5 completion report

---

## Sprint Handoff Format

Each sprint handoff document will include:

### Context Section
- What sprints are complete
- What functionality is available
- Where to find existing code

### Sprint Goal
- Clear objective
- Success criteria
- Deliverables expected

### Technical Specifications
- Detailed function signatures
- Expected behavior
- Error handling requirements

### Testing Requirements
- Test coverage expectations
- Specific test scenarios
- Integration test requirements

### Completion Report Template
- What was implemented
- Test coverage achieved
- Deviations from spec
- Known issues or limitations
- Questions for PM/Architect
- Recommendations for future work

---

## Next Steps

1. Create detailed sprint specs (one file per sprint)
2. Create handoff prompt template
3. Start with Sprint 0

---

**Document Version:** 1.0
**Last Updated:** October 6, 2025
**Status:** Ready to create individual sprint specs
