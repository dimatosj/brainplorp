# plorp 1.0 - Manual Test User Journey

**Purpose:** Walk through all plorp functionality as a user to verify end-to-end workflows.

**Prerequisites:**
- plorp installed (`pip install -e .` from project root)
- TaskWarrior 3.x installed and configured
- Obsidian vault configured in `~/.config/plorp/config.yaml`
- Terminal ready

**Estimated Time:** 15-20 minutes

---

## Journey Overview

You're a software engineer starting your workday. You'll use plorp to:
1. Start your day with a daily note
2. Work through tasks
3. Review your day
4. Process inbox items
5. Create and link notes to tasks

---

## Part 1: Morning - Start Your Day (Sprint 2)

### Step 1.1: Generate Today's Daily Note

```bash
plorp start
```

**Expected Output:**
```
✅ Daily note created: /path/to/vault/daily/2025-10-06.md
📋 Added 3 pending tasks from TaskWarrior
```

**Verify:**
1. Open the generated file in Obsidian
2. Check front matter has today's date
3. Confirm "Tasks" section exists
4. See unchecked checkboxes with your pending tasks
5. Each task should show: `- [ ] Task description (uuid: abc-123)`

**Try:**
Run `plorp start` again - should see error: "❌ Daily note already exists"

---

## Part 2: Working - Create Notes Linked to Tasks (Sprint 5)

### Step 2.1: Create a Standalone Note

```bash
plorp note "Research Python Testing Frameworks"
```

**Expected Output:**
```
✅ Created note: /path/to/vault/notes/research-python-testing-frameworks.md
```

**Verify:**
1. Note exists in `vault/notes/` directory
2. Title is set in front matter
3. Heading matches title

### Step 2.2: Create a Note Linked to a Task

First, get a task UUID:
```bash
task next
```

Pick one UUID, then:
```bash
plorp note "Sprint Planning Notes" --task <UUID> --type meeting
```

**Expected Output:**
```
✅ Created note: /path/to/vault/meetings/sprint-planning-notes.md
🔗 Linked to task: <UUID>
```

**Verify:**
1. Note is in `vault/meetings/` (not `notes/`)
2. Front matter contains `tasks: [<UUID>]`
3. Check TaskWarrior: `task <UUID> info`
4. Annotation should show: `plorp:note:meetings/sprint-planning-notes.md`

### Step 2.3: Link an Existing Note to a Task

Create a note in Obsidian manually (or use existing note), then:

```bash
plorp link <TASK_UUID> /path/to/vault/notes/existing-note.md
```

**Expected Output:**
```
✅ Linked note to task
📝 Note: /path/to/vault/notes/existing-note.md
📋 Task: <TASK_UUID>
```

**Verify:**
1. Open the note - front matter now has task UUID
2. Check `task <UUID> info` - annotation added
3. Bidirectional link established

**Error Cases to Try:**
```bash
# Non-existent task
plorp link fake-uuid-999 /path/to/note.md
# Expected: ❌ Error: Task not found

# Non-existent note
plorp link <VALID_UUID> /path/to/nonexistent.md
# Expected: ❌ Error: Note not found

# Note outside vault
plorp link <VALID_UUID> /tmp/outside.md
# Expected: ❌ Error: Note must be inside vault
```

---

## Part 3: Working - Check Tasks Throughout Day

### Step 3.1: Complete Tasks as You Work

In Obsidian, check off tasks in your daily note:
- Change `- [ ]` to `- [x]` for completed tasks
- Leave some unchecked

### Step 3.2: Add Tasks in TaskWarrior

```bash
task add "Buy groceries" project:personal
task add "Review PR #123" project:work +urgent
```

These will appear in tomorrow's daily note (they're new today).

---

## Part 4: Evening - Review Your Day (Sprint 3)

### Step 4.1: Run Review

```bash
plorp review
```

**Expected Flow:**

**1. Task Review Prompt:**
```
📋 Task: Buy groceries (UUID: abc-123)

Status: completed
What happened?
1. completed
2. carried
3. dropped
Choice [1-3]:
```

For each unchecked task, you'll be prompted. Try all options:
- **Choice 1 (completed):** Marks task done in TaskWarrior
- **Choice 2 (carried):** Keeps task active
- **Choice 3 (dropped):** Deletes task from TaskWarrior

**2. Priority Review:**
```
⚠️  Carried Task: Buy groceries

Set priority for tomorrow:
1. H (High)
2. M (Medium)
3. L (Low)
4. (none)
Choice [1-4]:
```

**3. Reflection Prompts:**
```
💭 What went well today?
> [Type your response]

💭 What could be improved?
> [Type your response]

💭 Notes for tomorrow:
> [Type your response]
```

**Expected Output:**
```
✅ Review complete
📝 Updated: /path/to/vault/daily/2025-10-06.md
✅ Processed 5 tasks
```

**Verify:**
1. Open daily note in Obsidian
2. See new "## Review" section at bottom
3. Timestamp should show current date/time
4. Your reflection responses are recorded
5. Check TaskWarrior: `task completed` - see completed tasks
6. Carried tasks still in `task next`

### Step 4.2: Run Review Again (Append Test)

```bash
plorp review
```

**Expected:**
- No tasks to review (all already processed)
- Still get reflection prompts
- New "## Review" section APPENDED with new timestamp
- Previous review section preserved

**Try Ctrl+C during review:**
```
⚠️  Review interrupted by user
```
Should exit gracefully without corruption.

---

## Part 5: Inbox Processing (Sprint 4)

### Step 5.1: Set Up Inbox

Create/edit `vault/inbox.md`:

```markdown
# Inbox

## Unprocessed

- [ ] Email from boss: Q4 planning meeting Friday 2pm
- [ ] Idea: Automate deployment pipeline
- [ ] Reminder: Renew gym membership
- [ ] Link: https://example.com/interesting-article

## Processed

- [x] Old item from yesterday
```

### Step 5.2: Process Inbox

```bash
plorp inbox process
```

**Expected Flow:**

For each item, you'll see:
```
📥 Item: Email from boss: Q4 planning meeting Friday 2pm

What should we do?
1. Create task
2. Create note
3. Create both (task + note)
4. Discard
Choice [1-4]:
```

**Try Each Option:**

**Option 1 - Create Task:**
```
Choice: 1

📋 Task description: [Email from boss: Q4 planning meeting Friday 2pm]
> Q4 planning meeting

📅 Due date (YYYY-MM-DD, or blank):
> 2025-10-10

🏷️  Project (or blank):
> work

✅ Created task (UUID: xyz-789)
```

**Option 2 - Create Note:**
```
Choice: 2

📝 Note title: [Idea: Automate deployment pipeline]
> Deployment Pipeline Ideas

📝 Note content (Ctrl+D when done):
> Need to research GitHub Actions
> Consider Docker optimization
> ^D

✅ Created note: vault/notes/deployment-pipeline-ideas.md
```

**Option 3 - Create Both:**
```
Choice: 3

📋 Task description: [Link: https://example.com/interesting-article]
> Read article on testing

📅 Due date (YYYY-MM-DD, or blank):
>

🏷️  Project (or blank):
> learning

✅ Created task (UUID: qrs-456)

📝 Note title: [Read article on testing]
> Testing Article Notes

📝 Note content (Ctrl+D when done):
> https://example.com/interesting-article
> ^D

✅ Created note: vault/notes/testing-article-notes.md
🔗 Linked note to task
```

**Option 4 - Discard:**
```
Choice: 4

🗑️  Discarded
```

**Expected Output:**
```
✅ Processed 4 inbox items
```

**Verify:**
1. Open `vault/inbox.md`
2. All items moved from "Unprocessed" to "Processed"
3. Each marked `[x]` with action taken:
   - `- [x] Email from boss... - Created task (uuid: xyz-789)`
   - `- [x] Idea: Automate... - Created note`
   - `- [x] Link: https://... - Created task and note (uuid: qrs-456)`
   - `- [x] Reminder: Renew... - Discarded`

4. Check TaskWarrior: `task next` - new tasks appear
5. Check `vault/notes/` - new notes created
6. For "both" option - verify bidirectional link:
   - Note has task UUID in front matter
   - Task has note annotation

**Try Ctrl+C during processing:**
```
⚠️  Inbox processing interrupted by user
```
Should save progress - processed items marked, unprocessed items remain.

---

## Part 6: Next Day - Verify Continuity

### Step 6.1: Next Morning

Wait until next day (or mock date in tests), then:

```bash
plorp start
```

**Expected:**
- New daily note for new date
- Shows tasks carried from yesterday (priority set)
- Shows new tasks added yesterday
- Does NOT duplicate tasks from previous note

---

## Verification Checklist

After completing all steps, verify:

### Daily Workflow
- ✅ Daily notes created in `vault/daily/YYYY-MM-DD.md`
- ✅ Tasks pulled from TaskWarrior with UUIDs
- ✅ Review appends multiple times without corruption
- ✅ Task completion syncs to TaskWarrior
- ✅ Carried tasks persist with priority
- ✅ Dropped tasks removed from TaskWarrior

### Inbox Workflow
- ✅ Inbox items processed to tasks/notes
- ✅ Items move from Unprocessed → Processed
- ✅ Action taken recorded in checkbox
- ✅ Multi-line content input works (Ctrl+D)
- ✅ Interruption (Ctrl+C) handled gracefully

### Note Linking
- ✅ Notes created in correct directories (meetings/ vs notes/)
- ✅ Task UUIDs in note front matter
- ✅ Note paths in TaskWarrior annotations
- ✅ Bidirectional links work
- ✅ Linking existing notes works
- ✅ Duplicate links prevented
- ✅ Error handling for invalid UUIDs/paths

### TaskWarrior Integration
- ✅ Reading tasks via SQLite
- ✅ Writing tasks/annotations via CLI
- ✅ UUID-based operations reliable
- ✅ Task metadata preserved (project, priority, due)

### Error Handling
- ✅ Duplicate daily note rejected
- ✅ Invalid task UUIDs caught
- ✅ Missing files reported clearly
- ✅ Notes outside vault rejected
- ✅ Keyboard interrupts handled gracefully

---

## Common Issues & Troubleshooting

**Issue:** `plorp: command not found`
- **Fix:** Run `pip install -e .` from project root

**Issue:** `❌ Error: vault_path not configured`
- **Fix:** Check `~/.config/plorp/config.yaml` exists with valid vault path

**Issue:** TaskWarrior shows no tasks
- **Fix:** Add test tasks: `task add "Test task" project:test`

**Issue:** Daily note empty (no tasks)
- **Fix:** Expected if no pending tasks in TaskWarrior

**Issue:** Annotations not appearing in TaskWarrior
- **Fix:** Run `task <uuid> info` (not just `task list`)

**Issue:** Note linking fails "outside vault"
- **Fix:** Ensure note path is inside configured vault_path (use absolute paths)

---

## Success Criteria

✅ All commands run without crashes
✅ Data flows correctly between TaskWarrior ↔ Obsidian
✅ Files created in expected locations with correct content
✅ Bidirectional links maintain integrity
✅ User prompts are clear and functional
✅ Error messages are helpful
✅ Interruptions don't corrupt data

---

## Next Steps After Manual Testing

1. Document any bugs found
2. Add edge cases to automated tests
3. Consider usability improvements
4. Plan future enhancements (from Sprint 5 spec)

---

**Test Date:** _____________
**Tester:** _____________
**Result:** ✅ PASS / ❌ FAIL
**Notes:**
