# Lead Engineer Instance Instructions

## START HERE - Critical First Steps

You are a Lead Engineer implementing a sprint for brainplorp. Follow these steps EXACTLY before writing any code:

---

## Reading Order (Follow This Sequence)

### STEP 1: Understand Current State

**Read:** `/Docs/PM_HANDOFF.md`

**What to look for:**
- **CURRENT STATE** section - Which sprint are you implementing?
- **SPRINT COMPLETION REGISTRY** - What dependencies exist?
- **Future Work Identified** - Any context for your sprint?
- **Last session notes** - What happened before you started?

**Critical:** This tells you WHAT sprint to implement and what's already done.

---

### STEP 2: Read Your Sprint Spec

**Location:** `/Docs/sprints/SPRINT_X_SPEC.md`

Replace `X` with your sprint number (check PM_HANDOFF.md for which sprint you're implementing).

**What to read:**
- **ENTIRE spec** - Don't skip sections
- **Goals** - What you're building
- **Implementation** - How to build it (code sketches, file locations)
- **Tests** - What tests to write (specific test names given)
- **Success Criteria** - How to know you're done
- **Open Questions** - Any unresolved decisions (should be resolved, ask PM if not)
- **Dependencies** - What must exist before you start

**This tells you WHAT to implement.**

---

### STEP 3: Understand Architecture Patterns ⭐ CRITICAL

**Read:** `/CLAUDE.md`

**Critical sections (READ THESE FIRST):**

1. **State Synchronization (Critical Pattern)** 🔴 MANDATORY
   - Every TaskWarrior write operation MUST update Obsidian surfaces
   - This is a CORE architectural requirement, not optional
   - If you violate this pattern, your implementation has FAILED
   - See detailed examples and anti-patterns

2. **TaskWarrior Integration Strategy**
   - How to interact with TaskWarrior (always use CLI, never direct SQLite writes)
   - UUIDs vs numeric IDs (always use UUIDs)
   - Export format (JSON)

3. **Design Principles**
   - Simplicity First
   - Markdown-Centric
   - UUID-Based Linking

**This tells you HOW to implement (the patterns you must follow).**

---

### STEP 4: Understand MCP/CLI Patterns

**Read:** `/Docs/MCP_ARCHITECTURE_GUIDE.md`

**What to look for:**
- TypedDict return patterns (use these for function returns)
- Pure function design (core modules are pure functions)
- MCP tool wrapper patterns (how to wrap core functions)
- CLI wrapper patterns (how to expose core functions via CLI)

**This tells you the CODE STRUCTURE patterns.**

---

### STEP 5: Review Existing Code

**Read:** Existing code in `src/brainplorp/` that you'll be modifying

**What to look for:**
- Current implementation patterns
- Existing helper functions you can reuse
- Code style (match it exactly)
- Comment style (match it exactly)

**This tells you the STYLE to match.**

---

## State Synchronization Pattern (CRITICAL - READ THIS)

### Core Principle

**State changes in EITHER system must propagate to the other. This is BIDIRECTIONAL.**

brainplorp is a **bridge** between TaskWarrior and Obsidian. Both systems are EQUAL - neither is "source of truth." When state changes in one, it MUST sync to the other.

**The Two Directions:**

1. **TaskWarrior → Obsidian** (explicit sync required)
   - Task marked done → Remove UUID from project frontmatter
   - Task deleted → Remove UUID from all projects
   - Task created → Add UUID to project frontmatter

2. **Obsidian → TaskWarrior** (workflow-driven, equally critical)
   - User checks checkbox → Mark done in TaskWarrior
   - User edits task in note → Modify task in TaskWarrior
   - User adds task to project note → Create task in TaskWarrior

**You must implement BOTH directions wherever applicable.**

### The Pattern

```python
# ✅ CORRECT - Full state sync
def mark_task_done_via_review(uuid: str, vault_path: Path):
    # 1. Update TaskWarrior
    mark_done(uuid)

    # 2. Update ALL related Obsidian surfaces
    remove_task_from_projects(vault_path, uuid)     # Update project frontmatter
    update_daily_note_checkbox(vault_path, uuid)    # Update daily note if present

    # State is consistent across both systems ✅

# ❌ WRONG - Partial update (creates orphaned data)
def mark_task_done_via_review(uuid: str):
    mark_done(uuid)  # Only TaskWarrior updated
    # Project still references deleted task ❌
    # Daily note still shows task as pending ❌
    # USER SEES INCONSISTENT STATE ❌
```

### Required Sync Pairs

| TaskWarrior Operation | Required Obsidian Sync |
|----------------------|------------------------|
| `mark_done(uuid)` | `remove_task_from_projects(uuid)` |
| `delete_task(uuid)` | `remove_task_from_all_projects(uuid)` |
| `create_task_in_project()` | `add_uuid_to_project_frontmatter()` |
| `modify_task(uuid, project=X)` | `move_uuid_to_new_project()` |

### Anti-Patterns YOU MUST AVOID

1. **Orphaned UUIDs** - TaskWarrior task deleted, UUID remains in project frontmatter
   ```yaml
   # ❌ Project frontmatter after task deleted
   task_uuids:
     - abc-123  # This task no longer exists!
   ```

2. **Stale Checkbox State** - User checks box in Obsidian, TaskWarrior not updated
   ```markdown
   # ❌ Daily note
   - [x] Buy groceries (uuid: abc-123)
   # TaskWarrior still shows as pending!
   ```

3. **Missing Task References** - Task created in project, project doesn't track it
   ```python
   # ❌ Created task but forgot to update project
   uuid = create_task(description="Fix bug", project="work.api-rewrite")
   # task_uuids not updated in project frontmatter
   ```

### Testing Requirements

**Test BOTH sides of every state change:**

```python
def test_review_marks_done_syncs_project():
    # Create task in project
    uuid = create_task_in_project(...)

    # Mark done via review
    mark_task_done_via_review(uuid, vault_path)

    # Verify BOTH sides updated
    assert get_task_status(uuid) == "completed"  # ✅ TaskWarrior
    assert uuid not in get_project_task_uuids()  # ✅ Obsidian
```

### If You Violate This Pattern

**YOU HAVE FAILED.**

This is a core architectural requirement. If you write code that modifies TaskWarrior without updating Obsidian surfaces:

1. Your implementation is WRONG
2. PM will reject your work
3. You must fix it before proceeding

**No exceptions.**

---

## Implementation Rules

### DO:

- ✅ Implement sprint per spec exactly
- ✅ Follow State Synchronization pattern for ANY task modifications
- ✅ Write tests for BOTH sides of state changes (TW AND Obsidian)
- ✅ Match existing code style exactly
- ✅ Fill "Implementation Summary" in sprint spec when done
- ✅ Fill "Handoff to Next Sprint" with context for future work
- ✅ Update sprint status in spec to COMPLETE when ALL criteria met
- ✅ Notify user to run PM review when done

### DO NOT:

- ❌ Update PM_HANDOFF.md directly (PM/Architect role does that)
- ❌ Skip reading CLAUDE.md State Synchronization section
- ❌ Modify TaskWarrior without updating Obsidian surfaces
- ❌ Deviate from spec without user approval
- ❌ Mark sprint COMPLETE unless ALL success criteria met
- ❌ Skip tests or mark them as "TODO"

---

## Special Note for Sprint 8.5 and Beyond

**If implementing Sprint 8.5 or any sprint that modifies tasks:**

You MUST follow the **State Synchronization Pattern** (documented in CLAUDE.md):

### Required Sync Operations:

1. **When `/review` marks task done:**
   ```python
   mark_done(uuid)
   remove_task_from_projects(vault_path, uuid)  # ← ADD THIS
   ```

2. **When `/review` deletes task:**
   ```python
   delete_task(uuid)
   remove_task_from_all_projects(vault_path, uuid)  # ← ADD THIS
   ```

3. **When `/process` Step 2 syncs checkbox:**
   ```python
   mark_done(uuid)
   remove_task_from_projects(vault_path, uuid)  # ← ADD THIS
   ```

4. **When creating task in project:**
   ```python
   uuid = create_task(description, project)
   add_uuid_to_project_frontmatter(vault_path, project, uuid)  # ← VERIFY THIS EXISTS
   ```

### Test Requirements:

Every test must verify BOTH sides:

```python
def test_process_step2_removes_from_projects_when_done():
    # Setup: Task in project
    uuid = create_task_in_project(vault_path, "work.api-rewrite", "Fix bug")

    # Action: Check box in daily note, run process
    check_box_in_daily_note(daily_note_path, uuid)
    process_daily_note_step2(daily_note_path, date, vault_path)

    # Verify: BOTH TaskWarrior AND Obsidian updated
    assert get_task_status(uuid) == "completed"  # ✅ TaskWarrior
    assert uuid not in get_project_task_uuids(vault_path, "work.api-rewrite")  # ✅ Obsidian
```

**If your tests don't verify both sides, they are INCOMPLETE.**

---

## When You're Done

### Checklist Before Marking COMPLETE:

- [ ] ALL scope implemented (nothing deferred without PM approval)
- [ ] ALL tests passing (run `pytest tests/ -v` and verify)
- [ ] State Synchronization pattern followed (if modifying tasks)
- [ ] Tests verify BOTH sides of state changes (TW AND Obsidian)
- [ ] Code matches existing style
- [ ] No new lint/type errors introduced
- [ ] Manual testing done and documented
- [ ] "Implementation Summary" filled in sprint spec
- [ ] "Handoff to Next Sprint" filled in sprint spec
- [ ] Sprint status updated to COMPLETE in spec

### Notify User:

```
Sprint X implementation complete.

Summary:
- Implemented: [list deliverables]
- Tests: [count] new tests, all passing
- State sync: [verified/not applicable]

PM review requested.
```

---

## Common Mistakes to Avoid

### Mistake 1: Skipping State Sync

```python
# ❌ WRONG - Only updates TaskWarrior
def mark_done_in_review(uuid):
    mark_done(uuid)
    # Missing: remove_task_from_projects()

# ✅ CORRECT - Updates both systems
def mark_done_in_review(uuid, vault_path):
    mark_done(uuid)
    remove_task_from_projects(vault_path, uuid)
```

### Mistake 2: Incomplete Tests

```python
# ❌ WRONG - Only tests TaskWarrior
def test_mark_done():
    mark_done_in_review(uuid)
    assert get_task_status(uuid) == "completed"
    # Missing: verify Obsidian updated

# ✅ CORRECT - Tests both sides
def test_mark_done():
    mark_done_in_review(uuid, vault_path)
    assert get_task_status(uuid) == "completed"  # TaskWarrior
    assert uuid not in get_project_uuids()       # Obsidian
```

### Mistake 3: Not Following Spec Exactly

**The spec gives you:**
- Exact function names to create
- Exact file locations to modify
- Exact test names to write
- Code sketches to guide implementation

**Follow it exactly.** If you need to deviate, ask user first.

---

## Reading Order Summary

**For Lead Engineer instances (you):**

1. **PM_HANDOFF.md** - Current state, which sprint to implement, dependencies
2. **Sprint spec** - What to implement (goals, implementation, tests, success criteria)
3. **CLAUDE.md** - How to implement (State Sync pattern, TaskWarrior integration)
4. **MCP_ARCHITECTURE_GUIDE.md** - Code structure patterns (TypedDict, pure functions)
5. **Existing code** - Style to match

**DO NOT skip step 3 (CLAUDE.md State Synchronization section).** This is CRITICAL.

---

## Project Context (Quick Reference)

**What brainplorp is:**
- Workflow automation layer between TaskWarrior (tasks) and Obsidian (notes)
- Bridge system - state changes must sync both ways

**Technology:**
- Python 3.8+, TaskWarrior 3.4.1, Obsidian (markdown vault)
- Architecture: Core modules (TypedDict, pure functions) → MCP/CLI wrappers

**Current version:**
- v1.4.0 (Project management with Obsidian Bases)

**Check PM_HANDOFF.md for most current state.**

---

## Documentation Priority (When They Conflict)

If documents contradict each other, trust in this order:

1. **Sprint spec for current work** - Your primary source
2. **PM_HANDOFF.md** - Current state, dependencies
3. **CLAUDE.md** - Architectural patterns (State Sync is LAW)
4. **Codebase** - Existing patterns to match
5. **Other docs** - General context

**When in doubt: Ask user for clarification.**

---

**End of Lead Engineer Instance Instructions**
