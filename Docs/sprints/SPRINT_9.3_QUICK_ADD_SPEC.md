# Sprint 9.3 Spec: Quick Add to Inbox (macOS Desktop Capture)

**Version:** 1.0.1
**Status:** 📋 APPROVED - Ready for Implementation
**Sprint:** 9.3 (Minor sprint - Feature addition)
**Estimated Effort:** 1.5-2 hours
**Dependencies:** Sprint 1-2 (Inbox file format)
**Architecture:** CLI command + Raycast frontend + multi-frontend docs
**Date:** 2025-10-10

---

## Executive Summary

Sprint 9.3 implements a "quick add" feature for macOS desktop capture to plorp inbox. Users can instantly add items to their inbox from anywhere on their Mac using a keyboard shortcut, without switching to Obsidian or terminal.

**Philosophy: Pure Capture**
- Quick-add is for CAPTURE ONLY - no metadata, no decisions
- All processing (projects, tags, due dates) happens during `/process` workflow
- Focus on speed: capture thought in <5 seconds, process later

**Problem:**
- User has a thought: "Buy milk for the office party"
- Current workflow: Open terminal → type command OR switch to Obsidian → open inbox → type
- Result: 30-60 seconds of context switching, broken flow state

**Solution:**
```
User anywhere on Mac → Press ⌘⌥I → Type "Buy milk" → Enter
→ Instant append to inbox, no context switch
```

**What's New:**
- `plorp inbox add <text>` - CLI command to append to inbox
- Optional `--urgent` flag for visual priority (🔴)
- Raycast script command (keyboard shortcut enabled)
- Documentation for alternative frontends (Shortcuts, Alfred, Automator)

**Quick Add Demonstration:**

*Raycast (Primary):*
```
⌘⌥I → Raycast window appears
Type: "Buy milk for office party"
Enter → Added to inbox instantly
```

*CLI (Alternative):*
```bash
$ plorp inbox add "Review PR #42"
✓ Added to inbox: vault/inbox/2025-10.md

$ plorp inbox add "Call client ASAP" --urgent
✓ Added to inbox: vault/inbox/2025-10.md
```

**User Experience:**
- **Before:** 30-60 seconds (context switch + navigation)
- **After:** 2-3 seconds (keyboard shortcut + type + enter)
- **10-20x faster** for quick inbox capture

---

## Problem Statement

### Current User Pain

**Scenario: Quick Thought Capture**

1. User is coding in VSCode
2. Thought occurs: "Need to review Sarah's PR before EOD"
3. User must:
   - Switch to terminal (⌘Tab)
   - Type `plorp inbox add "Review Sarah's PR"`
   - Switch back to VSCode (⌘Tab)
   - **OR:** Open Obsidian → navigate to inbox file → type → save → switch back
4. Total time: 30-60 seconds
5. Context switch disrupts flow state

**Frequency:**
- Power users capture 10-30 inbox items per day
- Current friction: 5-30 minutes wasted daily on context switching

### GTD Principle: Ubiquitous Capture

**From GTD methodology:**
> "Your mind is for having ideas, not holding them."

**Requirements for capture system:**
- ✅ **Fast:** <5 seconds from thought to captured
- ✅ **Accessible:** Available from any application
- ✅ **Low friction:** No navigation, no file opening, no decisions
- ❌ **plorp current state:** Requires terminal or Obsidian switch

### Comparison to Competitors

| System | Capture Speed | Keyboard Shortcut | Always Available |
|--------|--------------|-------------------|------------------|
| **Things 3** | 2-3 seconds | ✅ ⌘⌥N | ✅ System-wide |
| **OmniFocus** | 2-3 seconds | ✅ ⌘⌥Space | ✅ System-wide |
| **Todoist** | 3-5 seconds | ✅ ⌘⌥T | ✅ System-wide |
| **plorp (current)** | 30-60 seconds | ❌ No shortcut | ❌ Terminal/Obsidian only |
| **plorp (Sprint 9.3)** | 2-3 seconds | ✅ ⌘⌥I (Raycast) | ✅ System-wide |

---

## Solution: Hybrid CLI + Raycast

### Architecture Decision

**Approach: Core CLI + Multiple Frontend Options**

**Why this wins:**
- ✅ Core logic in plorp (testable, maintainable)
- ✅ Users choose their preferred capture method
- ✅ No forced third-party dependencies
- ✅ Each frontend is thin wrapper calling CLI

**Primary Frontend: Raycast**
- Free tier available (no paid upgrade required)
- Modern, fast, beautiful UI
- Growing user base (especially among developers)
- Easy script command creation
- Native keyboard shortcut support

**Alternative Frontends (Documented):**
- macOS Shortcuts (native, macOS 12+)
- Alfred (popular, but requires Powerpack for hotkeys)
- Automator Service (native, all macOS versions)

---

## Implementation Details

### Phase 1: Core CLI Command (45 minutes)

**File:** `src/plorp/core/inbox.py` (add function)

```python
def quick_add_to_inbox(
    text: str,
    vault_path: Path,
    urgent: bool = False
) -> Dict[str, Any]:
    """
    Quick-add text to inbox file.

    Pure capture - no metadata besides optional urgent flag.
    Project assignment, tags, and due dates happen during '/process' workflow.

    Args:
        text: Item text to add
        vault_path: Path to Obsidian vault
        urgent: Mark as urgent (adds 🔴 indicator for visual priority)

    Returns:
        TypedDict with:
            - added: Boolean success
            - inbox_path: Path to inbox file
            - item: Formatted item that was added

    Example:
        {
            "added": True,
            "inbox_path": "/vault/inbox/2025-10.md",
            "item": "- Buy milk"
        }
    """
    from datetime import date

    # Get current month's inbox file
    today = date.today()
    inbox_dir = vault_path / "inbox"
    inbox_file = inbox_dir / f"{today.year}-{today.month:02d}.md"

    # Ensure inbox directory exists
    inbox_dir.mkdir(parents=True, exist_ok=True)

    # Read existing inbox (create if doesn't exist)
    if inbox_file.exists():
        content = inbox_file.read_text(encoding="utf-8")
    else:
        content = f"# Inbox {today.year}-{today.month:02d}\n\n## Unprocessed\n\n## Processed\n"

    # Find "## Unprocessed" section
    unprocessed_section_start = content.find("## Unprocessed")
    processed_section_start = content.find("## Processed")

    if unprocessed_section_start == -1:
        # Create sections if missing
        content += "\n## Unprocessed\n\n## Processed\n"
        unprocessed_section_start = content.find("## Unprocessed")
        processed_section_start = content.find("## Processed")

    # Format item (simple bullet, with optional urgent indicator)
    if urgent:
        item = f"- 🔴 {text}"
    else:
        item = f"- {text}"

    # Insert item at end of Unprocessed section (before ## Processed)
    insertion_point = processed_section_start
    new_content = (
        content[:insertion_point].rstrip() +
        "\n" +
        item +
        "\n\n" +
        content[insertion_point:]
    )

    # Write back
    inbox_file.write_text(new_content, encoding="utf-8")

    return {
        "added": True,
        "inbox_path": str(inbox_file),
        "item": item
    }
```

**File:** `src/plorp/cli.py` (add command)

```python
@inbox.command("add")
@click.argument("text", nargs=-1, required=True)
@click.option("--urgent", "-u", is_flag=True, help="Mark as urgent (🔴)")
@click.pass_context
def inbox_add(ctx, text, urgent):
    """
    Quick-add item to inbox.

    Pure capture - no metadata. Use '/process' to assign projects and tags.
    Perfect for keyboard-driven workflows and fast thought capture.

    Examples:

        # Simple add
        plorp inbox add "Buy milk"

        # Multi-word items (no quotes needed)
        plorp inbox add Review PR #42 before EOD

        # Mark as urgent
        plorp inbox add "Call client ASAP" --urgent

    All project assignment, tagging, and due dates happen during 'plorp inbox process'.
    """
    from plorp.core.inbox import quick_add_to_inbox

    try:
        config = load_config()
        vault_path = Path(config["vault_path"]).expanduser().resolve()

        # Join text arguments
        text_str = " ".join(text)

        # Quick add
        result = quick_add_to_inbox(
            text=text_str,
            vault_path=vault_path,
            urgent=urgent
        )

        # Report success
        console.print(f"[green]✓ Added to inbox:[/green] {result['item']}")
        console.print(f"[dim]  {result['inbox_path']}[/dim]")

    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}", err=True)
        ctx.exit(1)
```

---

### Phase 2: Raycast Script Command (30 minutes)

**Why Raycast:**
- Free tier includes script commands
- No Keyboard Maestro needed (separate app)
- Beautiful native UI
- Fast (written in Rust)
- Easy installation and setup

**File:** `raycast/quick-add-inbox.sh`

```bash
#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Quick Add to Inbox
# @raycast.mode silent
# @raycast.packageName plorp
# @raycast.icon 📥

# Optional parameters:
# @raycast.argument1 { "type": "text", "placeholder": "Item to add" }

# Documentation:
# @raycast.description Quickly add an item to your plorp inbox
# @raycast.author plorp
# @raycast.authorURL https://github.com/yourusername/plorp

# Configuration
PLORP_PATH="/Users/jsd/Documents/plorp/.venv/bin/plorp"

# Get the item text from argument
ITEM="$1"

# Add to inbox
OUTPUT=$("$PLORP_PATH" inbox add "$ITEM" 2>&1)
EXIT_CODE=$?

# Check result
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Added: $ITEM"
else
    echo "❌ Error: $OUTPUT"
    exit 1
fi
```

**Installation Instructions (for user):**

1. **Install Raycast:** Download from https://raycast.com (free)

2. **Add Script Command:**
   ```bash
   # Create Raycast scripts directory
   mkdir -p ~/Documents/Raycast/Scripts

   # Copy plorp quick-add script
   cp raycast/quick-add-inbox.sh ~/Documents/Raycast/Scripts/
   chmod +x ~/Documents/Raycast/Scripts/quick-add-inbox.sh
   ```

3. **Configure in Raycast:**
   - Open Raycast (⌘Space)
   - Type "Script Commands"
   - Enable "quick-add-inbox"
   - Assign keyboard shortcut: ⌘⌥I

4. **Edit script for your setup:**
   - Update `PLORP_PATH` to your plorp installation
   - Customize icon emoji if desired

**Usage:**
```
⌘⌥I anywhere on Mac
→ Raycast window appears with "Item to add" prompt
→ Type "Buy milk for office party"
→ Press Enter
→ See "✓ Added: Buy milk for office party" notification
→ Item instantly added to inbox file
```

---

### Phase 3: Alternative Frontend Documentation (15 minutes)

**File:** `Docs/QUICK_ADD_FRONTENDS.md`

Document setup instructions for:

**1. macOS Shortcuts (Native, Free)**
```
Create Shortcut:
1. "Ask for input" → "What to add to inbox?"
2. "Run Shell Script" → plorp inbox add "{{input}}"
3. Assign keyboard shortcut in System Settings

Pros: Native, no third-party apps
Cons: Basic UI, slower than Raycast
```

**2. Alfred Workflow (Popular, Requires Powerpack)**
```
Create Workflow:
1. Hotkey Trigger: ⌘⌥I
2. Keyword Input: "inbox {query}"
3. Run Script: plorp inbox add "{query}"
4. Post Notification: "Added to inbox"

Pros: Beautiful UI, very fast
Cons: Requires paid Powerpack ($34)
```

**3. Automator Service (Native, Free)**
```
Create Service:
1. New Quick Action (Service)
2. AppleScript:
   set userInput to text returned of (display dialog "Quick add to inbox:" default answer "")
   do shell script "/usr/local/bin/plorp inbox add " & quoted form of userInput
3. Assign keyboard shortcut in System Settings

Pros: Native, all macOS versions
Cons: Ugly dialog, slower
```

---

### Phase 4: Tests & Documentation (30 minutes)

**File:** `tests/test_core/test_inbox.py` (add tests)

```python
def test_quick_add_to_inbox_simple(tmp_path):
    """Test simple quick add."""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    from plorp.core.inbox import quick_add_to_inbox
    result = quick_add_to_inbox("Buy milk", vault_path)

    assert result["added"] is True
    assert "2025-10" in result["inbox_path"]
    assert result["item"] == "- Buy milk"

    # Verify file content
    inbox_file = Path(result["inbox_path"])
    content = inbox_file.read_text()
    assert "- Buy milk" in content
    assert "## Unprocessed" in content


def test_quick_add_to_inbox_urgent(tmp_path):
    """Test urgent quick add."""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    from plorp.core.inbox import quick_add_to_inbox
    result = quick_add_to_inbox("Fix production bug", vault_path, urgent=True)

    assert result["item"] == "- 🔴 Fix production bug"

    inbox_file = Path(result["inbox_path"])
    content = inbox_file.read_text()
    assert "🔴 Fix production bug" in content


def test_quick_add_to_inbox_existing_file(tmp_path):
    """Test quick add to existing inbox file."""
    vault_path = tmp_path / "vault"
    inbox_dir = vault_path / "inbox"
    inbox_dir.mkdir(parents=True)

    from datetime import date
    today = date.today()
    inbox_file = inbox_dir / f"{today.year}-{today.month:02d}.md"
    inbox_file.write_text(
        f"# Inbox {today.year}-{today.month:02d}\n\n"
        "## Unprocessed\n\n"
        "- Existing item\n\n"
        "## Processed\n"
    )

    from plorp.core.inbox import quick_add_to_inbox
    result = quick_add_to_inbox("New item", vault_path)

    content = inbox_file.read_text()
    assert "- Existing item" in content
    assert "- New item" in content


def test_quick_add_to_inbox_multi_word(tmp_path):
    """Test quick add with multi-word text."""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    from plorp.core.inbox import quick_add_to_inbox
    result = quick_add_to_inbox("This is a long item with many words", vault_path)

    assert result["item"] == "- This is a long item with many words"
```

**Documentation Updates:**

1. **CLAUDE.md** - Add Quick Add section:
```markdown
## Quick Add to Inbox

**Keyboard-Driven Capture (Recommended):**

Raycast (⌘⌥I anywhere):
- Setup: Install Raycast + copy script command
- Usage: ⌘⌥I → Type → Enter
- Speed: <3 seconds per capture

CLI (Terminal):
- plorp inbox add "Buy milk"
- plorp inbox add "Call client" --urgent
- plorp inbox add Multi word items work without quotes

**Philosophy:**
Quick-add is pure capture only. All processing (projects, tags, due dates)
happens during 'plorp inbox process' workflow.

**Alternative Frontends:**
See `Docs/QUICK_ADD_FRONTENDS.md` for Shortcuts, Alfred, Automator setup.
```

2. **Update existing inbox workflow docs** to clarify two-step process:
   - Step 1: Quick-add (capture)
   - Step 2: `/process` (organize)

---

## Success Criteria

### Functional Requirements

- [ ] `plorp inbox add <text>` command works
- [ ] Appends to current month's inbox file
- [ ] Creates inbox file if missing
- [ ] Handles existing inbox file (appends to Unprocessed)
- [ ] `--urgent` flag adds 🔴 indicator
- [ ] Multiple word text handled correctly (no quotes needed)
- [ ] Silent success (just success message)
- [ ] No metadata besides urgent flag (pure capture)

### Raycast Integration

- [ ] Raycast script command created
- [ ] Script has correct metadata (title, icon, description)
- [ ] Script accepts text argument
- [ ] Script calls plorp CLI correctly
- [ ] Script shows success/error notification
- [ ] Installation instructions documented
- [ ] Keyboard shortcut configuration documented

### Alternative Frontends

- [ ] macOS Shortcuts example documented
- [ ] Alfred workflow example documented
- [ ] Automator service example documented
- [ ] Each frontend shows pros/cons
- [ ] Each frontend has step-by-step setup

### Testing Requirements

- [ ] 4+ tests for quick_add_to_inbox()
- [ ] Test simple add
- [ ] Test urgent flag
- [ ] Test existing file append
- [ ] Test multi-word text
- [ ] No regressions in existing tests

### Documentation Requirements

- [ ] CLI command help text clear
- [ ] Raycast installation guide complete
- [ ] QUICK_ADD_FRONTENDS.md created
- [ ] CLAUDE.md updated with quick-add section
- [ ] Examples for common use cases

---

## User Stories

### Story 1: Quick Thought Capture

**As a** plorp user
**I want** to instantly add thoughts to my inbox from anywhere
**So that** I can capture ideas without breaking flow state

**Acceptance Criteria:**
- Press ⌘⌥I anywhere on Mac
- Type thought
- Press Enter
- Thought appears in inbox file
- Total time: <5 seconds

### Story 2: Urgent Item Flagging

**As a** plorp user
**I want** to mark inbox items as urgent during capture
**So that** I can visually distinguish critical items

**Acceptance Criteria:**
- Run `plorp inbox add "Fix bug" --urgent`
- Item appears with 🔴 indicator
- Visual distinction in inbox file
- All other metadata assigned during `/process`

---

## Implementation Phases

### Phase 1: Core CLI Command (45 minutes)

**Tasks:**
1. Add `quick_add_to_inbox()` to `core/inbox.py`
2. Add `inbox add` command to `cli.py`
3. Implement --urgent flag (🔴 indicator)
4. Format items as plain bullets
5. Manual testing

**Deliverables:**
- `plorp inbox add` works end-to-end
- --urgent flag functional

### Phase 2: Raycast Script Command (30 minutes)

**Tasks:**
1. Create `raycast/quick-add-inbox.sh`
2. Add Raycast metadata
3. Test script execution
4. Write installation guide
5. Test keyboard shortcut

**Deliverables:**
- Working Raycast script
- Installation documentation

### Phase 3: Alternative Frontend Docs (15 minutes)

**Tasks:**
1. Create `Docs/QUICK_ADD_FRONTENDS.md`
2. Document Shortcuts setup
3. Document Alfred setup
4. Document Automator setup
5. Add pros/cons for each

**Deliverables:**
- Comprehensive frontend guide
- Setup instructions for 3 methods

### Phase 4: Tests & Documentation (30 minutes)

**Tasks:**
1. Write 4+ tests for `quick_add_to_inbox()`
2. Update CLAUDE.md
3. Run full test suite
4. Version bump

**Deliverables:**
- All tests passing (526+ total)
- Documentation complete

---

## Technical Decisions

### Q1: Text Argument Handling

**Decision:** Use `nargs=-1` to accept all arguments and join them. More user-friendly (no quotes needed).

### Q2: Urgent Indicator

**Decision:** Emoji (🔴) - Visual, works in Obsidian, doesn't require special parsing.

### Q3: Metadata in Quick-Add

**Decision:** Pure capture only - assign metadata during `/process`. Keeps quick-add focused on speed.

### Q4: Raycast vs Alfred Priority

**Decision:** Raycast primary (free tier). Alfred documented as alternative (requires Powerpack).

---

## Version Management

**Current Version:** 1.5.2 (Sprint 9.2)
**Next Version:** 1.5.3 (Sprint 9.3 - minor sprint, PATCH bump)

**Files to Update:**
- `src/plorp/__init__.py` - `__version__ = "1.5.3"`
- `pyproject.toml` - `version = "1.5.3"`
- `tests/test_cli.py` - Update version assertion
- `tests/test_smoke.py` - Update version assertion

---

## Risk Assessment

### Low Risk

**Raycast Dependency:**
- Risk: Users may not want to install Raycast
- Mitigation: Provide multiple frontend options (Shortcuts, Alfred, Automator)

**Keyboard Shortcut Conflicts:**
- Risk: ⌘⌥I might conflict with existing shortcuts
- Mitigation: Document shortcut as suggestion, users can customize

**Path Configuration:**
- Risk: Hardcoded path in Raycast script won't work for all users
- Mitigation: Document path update in installation guide

---

## Future Enhancements (Out of Scope)

**Sprint 9.4 or later:**

1. **MCP Tool** - `plorp_quick_add_inbox` for Claude Desktop
2. **Smart Parsing** - Detect project/tags from natural language (opt-in)
3. **Template Support** - Pre-defined inbox item templates
4. **Quick Add History** - Recently added items for repeat capture
5. **Voice Input** - macOS dictation integration
6. **iOS Shortcut** - Quick add from iPhone/iPad

---

## Manual Testing Checklist

### CLI Testing
- [ ] Test `plorp inbox add "Simple item"`
- [ ] Test `plorp inbox add Multi word item without quotes`
- [ ] Test `plorp inbox add "Urgent item" --urgent`
- [ ] Test with existing inbox file
- [ ] Test with missing inbox file (auto-create)
- [ ] Test error handling (invalid vault path)

### Raycast Testing
- [ ] Install Raycast
- [ ] Copy script to Raycast scripts folder
- [ ] Enable script in Raycast settings
- [ ] Assign keyboard shortcut (⌘⌥I)
- [ ] Test: Press ⌘⌥I, type item, verify added
- [ ] Test: Verify success notification appears
- [ ] Test: Verify item in inbox file

### Alternative Frontend Testing (Optional)
- [ ] Test macOS Shortcut setup
- [ ] Test Alfred workflow (if user has Powerpack)
- [ ] Test Automator service

---

## Implementation Checklist

### Before Starting
- [ ] Read Sprint 9.3 spec
- [ ] Confirm Sprint 9.2 is complete and signed off
- [ ] Install Raycast for testing

### Phase 1: Core CLI Command
- [ ] Add `quick_add_to_inbox()` to `core/inbox.py`
- [ ] Implement item formatting (text, urgent indicator only)
- [ ] Add `inbox add` command to `cli.py`
- [ ] Implement `nargs=-1` for multi-word text
- [ ] Implement `--urgent` flag
- [ ] Test CLI command manually

### Phase 2: Raycast Script Command
- [ ] Create `raycast/` directory in repo
- [ ] Create `quick-add-inbox.sh` script
- [ ] Add Raycast metadata headers
- [ ] Make script executable (`chmod +x`)
- [ ] Test script execution from terminal
- [ ] Test script in Raycast
- [ ] Test keyboard shortcut

### Phase 3: Alternative Frontend Docs
- [ ] Create `Docs/QUICK_ADD_FRONTENDS.md`
- [ ] Document macOS Shortcuts setup (step-by-step)
- [ ] Document Alfred workflow setup
- [ ] Document Automator service setup
- [ ] Add pros/cons table

### Phase 4: Tests & Documentation
- [ ] Create tests in `test_core/test_inbox.py`
- [ ] Test simple add
- [ ] Test urgent flag
- [ ] Test existing file append
- [ ] Test multi-word text
- [ ] Run full test suite (should be 526+ passing)
- [ ] Update `CLAUDE.md` with Quick Add section
- [ ] Update version in `__init__.py` and `pyproject.toml`
- [ ] Update test version assertions

### Final
- [ ] Manual testing (all checklist items)
- [ ] All tests passing
- [ ] Raycast script working
- [ ] Documentation complete
- [ ] Ready for PM review

---

## Final Status

**Sprint 9.3: APPROVED - Ready for Implementation**

**Scope Summary:**
- Core: CLI command `plorp inbox add` with optional --urgent flag
- Primary Frontend: Raycast script command (free tier)
- Alternative Frontends: Documented for Shortcuts, Alfred, Automator
- Philosophy: Pure capture - all metadata during `/process`

**Estimated Time:** 1.5-2 hours (minor sprint)

**Target Tests:** 526+ (522 existing + 4+ new)

**Next Steps:**
1. Lead Engineer implements Sprint 9.3
2. Version bump to 1.5.3
3. User tests Raycast integration
4. Ready for production

---

**Spec Version:** 1.0.1 (Simplified - Pure Capture)
**Date:** 2025-10-10
**Author:** PM/Architect Instance
**Status:** 📋 APPROVED - Ready for Implementation
