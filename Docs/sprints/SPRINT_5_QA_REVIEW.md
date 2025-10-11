# Sprint 5 Q&A Review - PM/Architect Analysis

**Date:** October 6, 2025
**Sprint:** Sprint 5 (Note Linking)
**Engineering Questions:** 13 total
**Status:** Awaiting PM decisions

---

## Overview

The Sprint 5 lead engineering instance submitted 13 detailed technical questions. These questions show excellent engineering judgment - they're asking about edge cases, cross-platform compatibility, data integrity, and integration concerns that could cause real problems if not addressed.

This document groups the questions by theme and explains each one in plain English for PM review.

---

## Category 1: YAML & Front Matter Format (Q1, Q2, Q12)

### Q1: YAML Serialization Options

**What they're asking:**
When we update front matter in notes, how should the YAML be formatted?

**The issues:**

1. **List formatting - Block vs Flow style**
   ```yaml
   # Block style (more readable)
   tasks:
     - abc-123
     - def-456

   # Flow style (more compact)
   tasks: [abc-123, def-456]
   ```
   **Question:** Which format should brainplorp use?

2. **Field ordering**
   - `sort_keys=False` preserves the order fields were added
   - `sort_keys=True` alphabetizes everything

   **Question:** Preserve user's field order, or alphabetize?

3. **YAML Loader consistency**
   - Sprint 3 switched from `yaml.safe_load()` to `yaml.BaseLoader` to avoid converting date strings to date objects
   - But now we're using `yaml.dump()` which handles dates properly

   **Question:** Should we switch back to `safe_load()` for consistency with `dump()`?

4. **String quoting**
   ```yaml
   # Unquoted
   date: 2025-10-06

   # Quoted
   date: '2025-10-06'
   ```
   **Question:** Should dates be quoted or not?

**Why it matters:**
- Inconsistent YAML formatting looks messy in Obsidian
- If we switch loaders, tests might break
- Users might have existing notes with specific formatting

---

### Q2: Creating Front Matter from Scratch

**What they're asking:**
When we add front matter to a note that doesn't have any, what should we create?

**The issues:**

1. **Default fields**
   ```yaml
   # Minimal (spec approach)
   ---
   tasks:
     - abc-123
   ---

   # With defaults (alternative)
   ---
   created: 2025-10-06
   type: note
   tasks:
     - abc-123
   ---
   ```
   **Question:** Should we add automatic fields like `created` date and `type`?

2. **Spacing after front matter**
   ```markdown
   # Option A - no blank line
   ---
   field: value
   ---
   # Content starts immediately

   # Option B - blank line
   ---
   field: value
   ---

   # Content has space
   ```
   **Question:** Which looks better in Obsidian?

3. **Preserving original formatting**
   If the original content had leading newlines, should we keep them?

   **Question:** Match original spacing or normalize it?

**Why it matters:**
- Affects how notes look in Obsidian
- Could break user expectations about note formatting
- Default fields might conflict with user's own conventions

---

### Q12: Front Matter Field Naming

**What they're asking:**
We're using `tasks:` to store task UUIDs. Is this the right name?

**The issues:**

1. **Name clarity**
   ```yaml
   # Current spec
   tasks:
     - abc-123

   # More descriptive
   task_uuids:
     - abc-123

   # Namespaced
   plorp_tasks:
     - abc-123
   ```
   **Question:** Which name is clearest?

2. **Conflict risk**
   - Other Obsidian plugins might use `tasks:` field
   - User might already have their own `tasks:` convention
   - Could brainplorp accidentally overwrite their data?

   **Question:** Should we namespace with `plorp_` prefix?

3. **Future metadata**
   What about other fields we might add later?
   - `plorp_created`
   - `plorp_last_review`
   - `plorp_linked_projects`

   **Question:** Establish naming convention now or wait?

**Why it matters:**
- Hard to change field names after users have notes with them
- Namespacing prevents conflicts but looks ugly
- Need to balance clarity with brevity

---

## Category 2: Validation & Error Handling (Q3, Q6)

### Q3: Task UUID Validation

**What they're asking:**
When adding a task UUID to a note's front matter, should we verify it exists in TaskWarrior first?

**The tradeoffs:**

**Option A: Validate (safer)**
```python
def add_task_to_note_frontmatter(note_path, task_uuid):
    task = get_task_info(task_uuid)  # Check TaskWarrior
    if not task:
        raise ValueError(f"Task {task_uuid} not found")
    # ... add to front matter
```
- ✅ Prevents broken links
- ✅ Fails fast with clear error
- ❌ Slower (TaskWarrior call every time)
- ❌ Requires TaskWarrior to be available
- ❌ Can't work offline

**Option B: Trust caller (faster)**
```python
def add_task_to_note_frontmatter(note_path, task_uuid):
    # Just add it, assume it's valid
    # ... add to front matter
```
- ✅ Fast
- ✅ Works offline
- ✅ Allows manual UUID entry
- ❌ Could create broken links
- ❌ Errors show up later, not immediately

**Context:**
`create_note_with_task_link()` already validates the task exists, but `add_task_to_note_frontmatter()` is a public function that could be called directly or from other code.

**Why it matters:**
- Affects performance (every link creation calls TaskWarrior)
- Affects user experience (offline use, manual linking)
- Broken links are hard to debug later

---

### Q6: Error Handling for File Operations

**What they're asking:**
Functions like `add_task_to_note_frontmatter()` do file I/O. What could go wrong?

**The issues:**

1. **Possible exceptions**
   ```python
   read_file(note_path)  # Could raise:
   # - FileNotFoundError (we document this)
   # - PermissionError (we don't document this)
   # - UnicodeDecodeError (we don't document this)
   # - IOError (disk full, we don't document this)
   ```
   **Question:** Document all exceptions or just the common ones?

2. **Enhanced error messages**
   ```python
   # Let it propagate (current)
   content = read_file(note_path)

   # Catch and enhance (alternative)
   try:
       content = read_file(note_path)
   except PermissionError:
       raise PermissionError(f"Cannot read note {note_path}: Permission denied. Check file permissions.")
   ```
   **Question:** Add helpful error messages or keep it simple?

3. **Atomicity for writes**
   What if we crash mid-write and corrupt the note?
   ```python
   # Simple (current)
   write_file(note_path, updated_content)

   # Atomic (safer)
   temp_path = note_path.with_suffix('.tmp')
   write_file(temp_path, updated_content)
   temp_path.rename(note_path)  # Atomic on POSIX
   ```
   **Question:** Trust Sprint 2's file utilities or add extra safety?

**Why it matters:**
- User data (notes) could be corrupted
- Cryptic error messages are frustrating
- Too much error handling adds complexity

---

## Category 3: Paths & Linking Logic (Q4, Q5, Q8)

### Q4: Annotation Format and Parsing

**What they're asking:**
TaskWarrior annotations use format: `"Note: relative/path/to/note.md"`

**The issues:**

1. **Colons in filenames**
   ```
   # What if user names their note:
   "Meeting: Client A - Discussion.md"

   # Annotation becomes:
   "Note: notes/Meeting: Client A - Discussion.md"

   # Parsing with startswith('Note: ') and removing 6 chars:
   path = "notes/Meeting: Client A - Discussion.md"  ✅ Works
   ```
   Actually this works fine! But engineer is right to check.

2. **Prefix conflicts**
   ```
   # User manually adds annotation:
   "Note to self: call Bob tomorrow"

   # get_linked_notes() will parse this as:
   path = "to self: call Bob tomorrow"  ❌ Broken
   ```
   **Question:** Use more specific prefix like `"LinkedNote:"` or `"plorp:note:"`?

3. **Windows backslashes**
   ```
   # On Windows:
   "Note: notes\meeting.md"

   # On Mac/Linux vault:
   Path("notes\meeting.md")  ❌ Won't find file
   ```
   **Question:** Normalize all paths to forward slashes?

**Why it matters:**
- Cross-platform compatibility (Windows users)
- User confusion if manual annotations get parsed as note links
- Silent failures are hard to debug

---

### Q5: Duplicate Link Detection

**What they're asking:**
We check if note is already linked by comparing annotation strings. But are two strings really the same path?

**The issues:**

**Path variations that mean the same thing:**
```python
"Note: notes/meeting.md"
"Note: ./notes/meeting.md"
"Note: notes//meeting.md"
"Note: notes/Meeting.md"  # On macOS (case-insensitive)
"Note: notes/Meeting.md"  # On Linux (case-sensitive) - DIFFERENT!
```

**Current code:**
```python
if annotation_text not in existing_annotations:
    add_annotation(...)
```

This uses exact string matching, so:
- `"Note: notes/meeting.md"` ≠ `"Note: ./notes/meeting.md"` → Would add duplicate!

**Question:** Should we normalize paths before comparison?
```python
# Normalize
normalized = str(Path(relative_path).resolve())
# Compare normalized versions
```

**Why it matters:**
- Duplicate annotations clutter task display
- User might link same note multiple times unknowingly
- Different behavior on different operating systems

---

### Q8: Notes Outside the Vault

**What they're asking:**
What if someone tries to link a note that's not inside the Obsidian vault?

**The scenario:**
```python
vault_path = Path("/Users/john/vault")
note_path = Path("/Users/john/Documents/external-note.md")

# This will fail:
relative_path = note_path.relative_to(vault_path)
# ValueError: '/Users/john/Documents/external-note.md' is not in the subpath of '/Users/john/vault'
```

**Options:**

**A. Let it crash (current spec)**
- ✅ Simple
- ❌ Confusing error message
- ❌ Could happen via symlinks

**B. Use absolute path instead**
```python
try:
    relative_path = note_path.relative_to(vault_path)
except ValueError:
    relative_path = note_path.absolute()
```
- ✅ Handles edge case
- ❌ Absolute paths in annotations look ugly
- ❌ Breaks if vault moves

**C. Refuse to link**
```python
if not note_path.is_relative_to(vault_path):
    raise ValueError("Note must be inside vault")
```
- ✅ Clear policy
- ✅ Good error message
- ❌ Prevents valid use cases (symlinked notes?)

**Symlink complication:**
What if note is symlinked into vault?
```bash
vault/notes/meeting.md → /external/real-note.md
```
Should we resolve symlinks first?

**Why it matters:**
- User might accidentally try to link non-vault notes
- Symlinks are common in advanced setups
- Cryptic errors frustrate users

---

## Category 4: Unlinking & CLI UX (Q9, Q11)

### Q9: Unlinking Behavior

**What they're asking:**
`unlink_note_from_task()` removes UUID from note, but can't remove annotation from TaskWarrior (CLI limitation).

**The issue:**

After unlinking:
- ✅ Note front matter updated: `tasks: []`
- ❌ TaskWarrior annotation still shows: `"Note: notes/meeting.md"`

**This is asymmetric and confusing!**

**Options:**

**A. Silent unlinking (current spec)**
- Remove from note silently
- Documented in "Known Issues"
- User discovers annotation still there later

**B. Print warning**
```bash
$ brainplorp unlink abc-123 meeting.md
✅ Removed from note
⚠️  Note: TaskWarrior annotation cannot be removed automatically
💡 To remove manually: task abc-123 edit
```

**C. Research `task modify`**
Maybe there's a way to remove annotations programmatically?
```bash
# Is this possible?
task abc-123 modify -annotation:"Note: meeting.md"
```
Engineer wants to research this.

**Why it matters:**
- Asymmetric behavior is surprising
- Users might not read "Known Issues" section
- Half-unlinked state is confusing

---

### Q11: CLI Title Parsing and Validation

**What they're asking:**
The `brainplorp note` command accepts multi-word titles. How should this work exactly?

**The issues:**

1. **Both forms work:**
   ```bash
   # Without quotes (using nargs=-1)
   $ brainplorp note Meeting Notes
   # title = ('Meeting', 'Notes')
   # Joined: "Meeting Notes"

   # With quotes
   $ brainplorp note "Meeting Notes"
   # title = ('Meeting Notes',)
   # Joined: "Meeting Notes"
   ```
   Both produce the same result! Should we document this?

2. **Edge cases:**
   ```bash
   $ brainplorp note ""
   # Joined: "" (empty string)

   $ brainplorp note "   "
   # Joined: "   " (whitespace)

   $ brainplorp note
   # Error: Missing argument (Click handles this)
   ```
   **Question:** Validate title is not empty/whitespace after joining?

3. **Filesystem-unsafe characters:**
   ```bash
   $ brainplorp note "Meeting: Q4 Planning"
   # On Windows: Colon (:) not allowed in filename

   $ brainplorp note "Project/Feature"
   # Creates subdirectory (probably not intended)

   $ brainplorp note "Report?.md"
   # Windows doesn't allow ? in filenames
   ```

   Problematic characters: `/ \ : * ? " < > |`

   **Question:** Should we sanitize these?
   ```python
   # Replace unsafe chars
   safe_title = title.replace(':', '-').replace('/', '-')
   # Or error
   if any(c in title for c in '/:*?"<>|'):
       raise ValueError("Title contains invalid characters")
   ```

**Why it matters:**
- Cross-platform compatibility (Windows vs Mac/Linux)
- User confusion if `brainplorp note ""` silently succeeds
- Filesystem errors are cryptic

---

## Category 5: Dependencies & Integration (Q7, Q10, Q13)

### Q7: Note Type Validation

**What they're asking:**
The function accepts `note_type` parameter but doesn't document what's valid.

**The confusion:**

```python
# In Sprint 5 spec:
create_note_with_task_link(config, "Title", note_type='general')

# But what's valid?
note_type='general'   # ✅ ?
note_type='meeting'   # ✅ ?
note_type='project'   # ✅ ?
note_type='banana'    # ✅ ? ❌ ?
```

**Questions:**

1. **What types are valid?**
   This comes from Sprint 4's `create_note()` function.
   Need to check Sprint 4 spec for valid types.

2. **Does type affect directory?**
   From Sprint 4 Q&A resolution:
   - `meeting` → `vault/meetings/`
   - Everything else → `vault/notes/`

   Should we document this in Sprint 5?

3. **Should CLI validate?**
   ```bash
   $ brainplorp note "Test" --type banana
   # Should this:
   # A) Accept it and pass to create_note()
   # B) Show error: "Invalid type. Valid types: general, meeting, project"
   ```

**Why it matters:**
- Users will try random type values
- Documentation prevents confusion
- Validation provides better error messages

---

### Q10: Testing Sprint 4 Integration

**What they're asking:**
Sprint 5 needs Sprint 4's `create_note()` and `get_vault_path()` functions. How do we test?

**The approaches:**

**A. Mock everything (current spec)**
```python
@patch('plorp.workflows.notes.create_note')
@patch('plorp.workflows.notes.get_vault_path')
def test_create_note_with_task_link(mock_vault, mock_create):
    mock_create.return_value = Path('/fake/note.md')
    # Test without real Sprint 4 code
```
- ✅ Tests work even if Sprint 4 incomplete
- ✅ Fast unit tests
- ❌ Don't catch integration bugs

**B. Wait for Sprint 4**
- ✅ Can test real integration
- ❌ Sprint 5 blocked until Sprint 4 done
- ❌ Against parallel sprint execution

**C. Create minimal stub**
```python
# Temporary stub in Sprint 5
def create_note_stub(vault_path, title, note_type, content):
    # Minimal implementation for testing
    note_path = vault_path / 'notes' / f"{title}.md"
    note_path.write_text(f"---\ntitle: {title}\n---\n\n{content}")
    return note_path
```
- ✅ Tests work immediately
- ✅ Can verify behavior
- ❌ Might not match real Sprint 4 behavior

**Question:** Which approach?

**Secondary question:** Should we also have integration tests?
```python
def test_create_and_link_integration():
    # Uses real create_note() from Sprint 4
    # Tests end-to-end flow
    pass
```

**Why it matters:**
- Unit tests don't catch integration bugs
- Sprint 4 might have different behavior than mocks
- Sprint parallelization vs. test quality tradeoff

---

### Q13: Sprint 4 Completion Verification

**What they're asking:**
How do we verify Sprint 4 is actually complete before starting Sprint 5?

**The options:**

**A. Try importing**
```python
# At start of Sprint 5 implementation
try:
    from plorp.integrations.obsidian import create_note, get_vault_path
except ImportError:
    raise RuntimeError("Sprint 4 incomplete - obsidian.py not implemented")
```

**B. Check for completion marker**
```python
# Sprint 4 should add to completion report
if not sprint_4_complete:
    raise RuntimeError("Please complete Sprint 4 first")
```

**C. Assume it's done**
- Sprint 5 engineer assumes Sprint 4 is complete
- If it's not, import errors will happen naturally
- Fix at integration testing time

**Question:** Which approach?

**Related question:** Should Sprint 5 fail fast or proceed?
- Fail fast: Clear error message immediately
- Proceed: Let Python handle import errors naturally

**Why it matters:**
- Confusing errors if Sprint 4 incomplete
- Sprint parallelization coordination
- Engineer time wasted debugging missing dependencies

---

## Summary by Decision Type

### **Decisions I Need from You (PM):**

1. **Q1** - YAML formatting preferences (block style, sort keys, loader choice)
2. **Q2** - Front matter defaults and spacing
3. **Q12** - Field naming: `tasks` vs `plorp_tasks` vs `task_uuids`
4. **Q3** - Validate task UUIDs (slow/safe) vs trust caller (fast/risky)
5. **Q4** - Annotation prefix: `"Note:"` vs `"plorp:note:"` for uniqueness
6. **Q9** - Unlinking UX: silent vs warning message
7. **Q11** - Title validation: accept anything vs sanitize vs error on unsafe chars
8. **Q7** - Note type: document valid types vs accept anything
9. **Q13** - Sprint 4 dependency: verify completion vs assume it's done

### **Engineering Decisions I Can Make:**

1. **Q5** - Path normalization for duplicate detection (normalize paths - clear engineering best practice)
2. **Q6** - Error handling: document common exceptions, let others propagate
3. **Q8** - Notes outside vault: refuse to link with clear error message
4. **Q10** - Testing: mock for unit tests, verify imports at runtime

---

## Recommendations

Based on my experience as PM/Architect, here are my initial recommendations:

### High Priority (affects user experience):
- **Q3**: Validate UUIDs - safer, clearer errors
- **Q4**: Use `"plorp:note:"` prefix - prevents user annotation conflicts
- **Q11**: Sanitize titles - replace unsafe chars with `-`
- **Q12**: Keep `tasks` - simple, clear, low conflict risk

### Medium Priority (affects code quality):
- **Q1**: Use block style, preserve order, keep BaseLoader
- **Q5**: Normalize paths before comparison
- **Q8**: Refuse to link notes outside vault

### Low Priority (nice to have):
- **Q2**: No blank line after front matter (cleaner)
- **Q9**: Print warning message (better UX)
- **Q7**: Document valid types from Sprint 4

**Ready to review these with you and get your decisions?**
