# brainplorp v1.1 MCP - Manual Test User Journey

**Purpose:** Walk through all brainplorp MCP functionality in Claude Desktop to verify end-to-end AI-assisted workflows.

**Prerequisites:**
- brainplorp v1.1 installed (`pip install -e ".[dev]"` from project root)
- TaskWarrior 3.x installed and configured
- Obsidian vault configured in `~/.config/plorp/config.yaml`
- Claude Desktop installed and configured with brainplorp MCP server
- MCP server configuration verified in `~/Library/Application Support/Claude/claude_desktop_config.json`

**Estimated Time:** 20-25 minutes

---

## Journey Overview

You're a software engineer who wants to manage tasks and notes through natural conversation with Claude. You'll use brainplorp MCP tools to:
1. Start your day with AI-generated daily notes
2. Get intelligent task summaries and suggestions
3. Review your day with guided reflections
4. Process inbox items with AI assistance
5. Create and link notes naturally

---

## Setup Verification

### Step 0.1: Verify MCP Server is Running

**In Claude Desktop**, look for:
- 🔨 Hammer icon in the interface (indicates MCP tools available)
- Settings → Developer → MCP servers should list "plorp"

**Check logs:**
```bash
tail -20 ~/Library/Logs/Claude/mcp-server-plorp.log
```

**Expected:**
```
[plorp] [info] Server started and connected successfully
[plorp] [info] Message from server: ...16 tools...
```

### Step 0.2: Verify Slash Commands Installed

**In Claude Desktop**, type `/` and look for:
- `/start` - Start my day
- `/review` - Review my day
- `/inbox` - Process inbox
- `/task` - Create a task
- `/note` - Create a note

**If missing**, run:
```bash
brainplorp init-claude
```
Then restart Claude Desktop.

---

## Part 1: Morning - Start Your Day with AI

### Step 1.1: Use Slash Command to Generate Daily Note

**In Claude Desktop:**
```
/start
```

**Expected AI Response:**
```
I'll generate your daily note for today.

[Tool call: plorp_start_day]

✅ Created your daily note for 2025-10-06!

Here's what's on your plate:
• 0 overdue tasks (great job!)
• 3 tasks due today
• 2 recurring tasks

Your daily note is at: /Users/jsd/vault/daily/2025-10-06.md

Would you like me to:
1. Show you the overdue tasks so we can prioritize them?
2. Break down today's tasks by project?
3. Open the daily note in Obsidian?
```

**Verify:**
1. Daily note exists at the specified path
2. Contains YAML frontmatter with date
3. Tasks are categorized (Overdue, Due Today, Recurring)
4. Each task shows full metadata including UUID

**Try follow-up:**
```
Show me the tasks by project
```

**Expected:**
Claude should parse the daily note and group tasks intelligently.

### Step 1.2: Try Starting Day Again (Error Handling)

**In Claude Desktop:**
```
/start
```

**Expected AI Response:**
```
I tried to generate your daily note, but it already exists for today!

[Tool call resulted in error: Daily note already exists...]

Your daily note is at: /Users/jsd/vault/daily/2025-10-06.md

Would you like me to:
1. Open the existing note?
2. Show you a summary of today's tasks?
3. Generate tomorrow's note instead?
```

**Verify:**
- AI gracefully handles the error
- Provides helpful alternatives
- Doesn't crash or show cryptic errors

---

## Part 2: Working - Create Notes and Tasks with AI

### Step 2.1: Create a Task Naturally

**In Claude Desktop:**
```
I need to prepare for the Q4 planning meeting on Friday. It's high priority and part of the planning project.
```

**Expected AI Response:**
```
I'll create a task for you!

[Tool call: plorp_create_task_from_inbox or similar]

✅ Created task: "Prepare for Q4 planning meeting"
   • Due: 2025-10-10 (Friday)
   • Priority: High
   • Project: planning
   • UUID: abc-def-123

Would you like me to also create a note for planning meeting prep?
This would be great for collecting agenda items and discussion points.
```

**Follow-up:**
```
Yes, create a meeting note for this
```

**Expected:**
```
[Tool call: plorp_create_note_with_task]

✅ Created meeting note at: /Users/jsd/vault/meetings/prepare-for-q4-planning-meeting.md

The note is linked to your task. I've set it up with:
• Task UUID in frontmatter
• TaskWarrior annotation linking back
• Bidirectional link established

Would you like me to help you draft an agenda?
```

**Verify:**
1. Task created in TaskWarrior: `task <UUID> info`
2. Note created in `vault/meetings/` (not `notes/` - correct type)
3. Note frontmatter has `tasks: [abc-def-123]`
4. Task annotation shows note path
5. Bidirectional link works

### Step 2.2: Create Standalone Note

**In Claude Desktop:**
```
/note
```

**Expected AI Response:**
```
I'll help you create a note! What's the title?
```

**You:**
```
Python Testing Best Practices
```

**Claude:**
```
[Tool call: plorp_create_note with title="Python Testing Best Practices"]

✅ Created note: /Users/jsd/vault/notes/python-testing-best-practices.md

The note is ready for you to fill in! Would you like me to:
1. Help you structure the content with headings?
2. Link this note to a task?
3. Add some starter content based on testing best practices?
```

**Verify:**
1. Note exists at correct path
2. Title set in frontmatter
3. No task links (standalone note)

### Step 2.3: Link Existing Note to Task (Natural Language)

**In Claude Desktop:**
```
Link my Python testing note to the task about writing unit tests
```

**Expected AI Response:**
```
I'll link those for you! First, let me find the task about writing unit tests.

[May call plorp_get_task_info or search]

Found it: "Write unit tests for auth module" (UUID: xyz-789)

[Tool call: plorp_link_note_to_task]

✅ Linked note to task:
   📝 Note: /Users/jsd/vault/notes/python-testing-best-practices.md
   📋 Task: Write unit tests for auth module (xyz-789)

Now when you work on unit tests, you have your best practices notes right there!
```

**Verify:**
1. Note frontmatter updated with task UUID
2. Task annotation added
3. Bidirectional link established

---

## Part 3: Inbox Processing with AI Guidance

### Step 3.1: Set Up Inbox

**Manually create** `vault/inbox/2025-10.md`:
```markdown
# Inbox - October 2025

## Unprocessed

- [ ] Email from Sarah: Code review for PR #456
- [ ] Idea: Automate the deployment pipeline with GitHub Actions
- [ ] Reminder: Renew SSL certificates before end of month
- [ ] Link: https://example.com/article-on-microservices

## Processed

- [x] Old processed item
```

### Step 3.2: Process Inbox with AI

**In Claude Desktop:**
```
/inbox
```

**Expected AI Response:**
```
Let me check your inbox for unprocessed items.

[Tool call: plorp_get_inbox_items]

You have 4 unprocessed inbox items:

1. **Email from Sarah: Code review for PR #456**
2. **Idea: Automate the deployment pipeline with GitHub Actions**
3. **Reminder: Renew SSL certificates before end of month**
4. **Link: https://example.com/article-on-microservices**

Let's process them one by one. Starting with the first one:

**Email from Sarah: Code review for PR #456**

This looks like it needs action. Would you like me to:
• Create a task for it
• Create a note to document the review
• Create both a task and a note (recommended for code reviews)
• Discard it
```

**You:**
```
Create both a task and note for the code review
```

**Expected:**
```
[Tool call: plorp_create_both_from_inbox]

✅ Created task: "Code review for PR #456"
   • UUID: task-001
   • Project: (I'll ask) What project should this be under?

✅ Created note: /Users/jsd/vault/notes/code-review-for-pr-456.md
🔗 Linked note and task together

The note is ready for your review comments!

Next item: **Idea: Automate the deployment pipeline with GitHub Actions**

This seems like a project idea. What would you like to do with it?
```

**Continue processing each item:**

**For the automation idea:**
```
Create a project note for this
```

**Expected:**
```
[Tool call: plorp_create_note_from_inbox with note_type="project"]

✅ Created project note: /Users/jsd/vault/projects/automate-deployment-pipeline.md
✅ Marked inbox item as processed

This is a great idea! Would you like me to help you break this down into tasks?
```

**For the SSL reminder:**
```
Make it a task due in 3 weeks
```

**Expected:**
```
[Tool call: plorp_create_task_from_inbox with due date calculation]

✅ Created task: "Renew SSL certificates"
   • Due: 2025-10-27
   • Priority: (suggesting) Should this be High priority since it's security-related?
```

**For the article link:**
```
Just discard it, I already read it
```

**Expected:**
```
[Tool call: plorp_discard_inbox_item]

✅ Discarded item

That's all 4 items processed!

Summary:
• 1 task + note created (code review)
• 1 project note created (automation idea)
• 1 task created (SSL renewal)
• 1 item discarded (article)

Your inbox is now clear! 🎉
```

**Verify:**
1. Open `vault/inbox/2025-10.md`
2. All items moved to "Processed" section
3. Each marked with action taken
4. Check TaskWarrior: `task next` - new tasks appear
5. Check vault - new notes created in correct locations
6. Bidirectional links work for task+note items

---

## Part 4: Evening - AI-Guided Review

### Step 4.1: Mark Some Tasks Complete in Obsidian

Before review, manually edit your daily note:
- Change some `- [ ]` to `- [x]` (completed)
- Leave some unchecked (not completed)

### Step 4.2: Start Review with AI

**In Claude Desktop:**
```
/review
```

**Expected AI Response:**
```
Let me check what tasks you didn't complete today.

[Tool call: plorp_get_review_tasks]

I found 3 uncompleted tasks from your daily note:

1. **Code review for PR #456** (Priority: Medium)
   - This has a linked note for tracking your review comments
   - Status: Pending

2. **Renew SSL certificates** (Priority: High, Due: Oct 27)
   - Security task, important!
   - Status: Pending

3. **Research new testing framework** (Priority: Low)
   - Status: Pending

Let's go through each one. Starting with the code review:

**Code review for PR #456** - What happened with this?
• Did you complete it? (I can mark it done)
• Need more time? (I can defer it to tomorrow or another day)
• No longer relevant? (I can drop it)
• Change priority?
```

**You:**
```
I finished the review, mark it complete
```

**Expected:**
```
[Tool call: plorp_mark_task_completed]

✅ Marked "Code review for PR #456" as complete!

Next task: **Renew SSL certificates**

This is high priority and due in 3 weeks. Did you make progress on this?
```

**You:**
```
Defer it to next Monday, I need to coordinate with DevOps first
```

**Expected:**
```
[Tool call: plorp_defer_task with new_due="2025-10-13"]

✅ Deferred "Renew SSL certificates" to 2025-10-13 (Monday)

I'll make sure it shows up in Monday's daily note!

Last task: **Research new testing framework** (Priority: Low)

What should we do with this one?
```

**You:**
```
Drop it, we decided to stick with pytest
```

**Expected:**
```
[Tool call: plorp_drop_task]

✅ Dropped task "Research new testing framework"

All tasks reviewed! Now let's add some reflections to your daily note.

What went well today?
```

**You:**
```
Completed the code review efficiently and unblocked Sarah's PR
```

**Claude:**
```
Great! What could be improved?
```

**You:**
```
Better time estimation for complex tasks
```

**Claude:**
```
And any notes for tomorrow?
```

**You:**
```
Focus on SSL certificates coordination first thing
```

**Expected:**
```
[Tool call: plorp_add_review_notes]

✅ Review complete! I've added your reflections to today's daily note.

Summary:
• ✅ 1 task completed (code review)
• ⏭️ 1 task deferred (SSL certificates → Monday)
• 🗑️ 1 task dropped (testing framework research)

Tomorrow's priority: SSL certificates coordination 🔐

Have a great evening!
```

**Verify:**
1. Open daily note - "## Review" section appended
2. Contains timestamp and reflections
3. TaskWarrior updated: `task completed` shows code review
4. Deferred task shows new due date: `task <UUID> info`
5. Dropped task deleted: `task <UUID> info` returns nothing

---

## Part 5: Advanced Workflows

### Step 5.1: Get Task Information

**In Claude Desktop:**
```
Tell me about task abc-123
```

**Expected AI Response:**
```
[Tool call: plorp_get_task_info with uuid="abc-123"]

Here's the full info on that task:

**Code review for PR #456**
• Status: Completed ✅
• Description: Code review for PR #456
• Project: work
• Priority: Medium
• Due date: 2025-10-06
• Completed: 2025-10-06 22:30
• UUID: abc-123
• Tags: code-review
• Notes: Linked to /Users/jsd/vault/notes/code-review-for-pr-456.md

Would you like me to:
1. Open the linked note?
2. See all tasks in this project?
3. See other completed tasks from today?
```

### Step 5.2: Change Task Priority

**In Claude Desktop:**
```
The SSL certificate task should be high priority, not medium
```

**Expected AI Response:**
```
I'll update that for you!

[Tool call: plorp_set_task_priority with priority="H"]

✅ Changed "Renew SSL certificates" to High priority

Now it's properly marked as urgent. It'll stand out in your daily notes!
```

**Verify:**
```bash
task <UUID> info
```
Shows `Priority: H`

### Step 5.3: Complex Multi-Step Workflow

**In Claude Desktop:**
```
I'm starting a new project to migrate our database to PostgreSQL.
I need to:
1. Research migration tools
2. Set up test environment
3. Write migration scripts
4. Test with staging data

Create tasks and a project note for this
```

**Expected AI Response:**
```
Great project! Let me set this up for you.

[Tool call: plorp_create_note with note_type="project"]

✅ Created project note: /Users/jsd/vault/projects/migrate-database-to-postgresql.md

Now I'll create the 4 tasks and link them to this note:

[Multiple tool calls: plorp_create_task_from_inbox + plorp_link_note_to_task]

✅ Created and linked 4 tasks:

1. **Research PostgreSQL migration tools**
   • UUID: task-pg-001
   • Priority: High (starting point)
   • Linked to project note

2. **Set up PostgreSQL test environment**
   • UUID: task-pg-002
   • Priority: High
   • Linked to project note

3. **Write database migration scripts**
   • UUID: task-pg-003
   • Priority: Medium (depends on research)
   • Linked to project note

4. **Test migration with staging data**
   • UUID: task-pg-004
   • Priority: Medium (final step)
   • Linked to project note

Your project note has all 4 tasks in the frontmatter. I've suggested priorities based on typical workflow, but let me know if you want to adjust them!

Would you like me to:
1. Add dependencies between these tasks?
2. Set due dates based on a project timeline?
3. Help you structure the project note with sections?
```

**Verify:**
1. Project note exists with all task UUIDs in frontmatter
2. All 4 tasks created in TaskWarrior
3. Each task has annotation linking to project note
4. Bidirectional links work

---

## Part 6: Error Handling & Edge Cases

### Step 6.1: Invalid Task UUID

**In Claude Desktop:**
```
Mark task fake-uuid-999 as complete
```

**Expected AI Response:**
```
[Tool call: plorp_mark_task_completed]

❌ I couldn't find that task (UUID: fake-uuid-999)

It might have been deleted, or the UUID might be incorrect. Would you like me to:
1. Search for tasks by description?
2. Show you all pending tasks?
3. Check recently deleted tasks?
```

### Step 6.2: Note Outside Vault

**In Claude Desktop:**
```
Link /tmp/outside-note.md to task abc-123
```

**Expected AI Response:**
```
[Tool call: plorp_link_note_to_task]

❌ That note is outside your Obsidian vault!

Notes must be inside: /Users/jsd/vault

Did you mean to:
1. Create a new note inside the vault instead?
2. Move the existing note into the vault first?
```

### Step 6.3: Duplicate Daily Note

Already tested in Step 1.2 ✅

### Step 6.4: Task Not Found in Review

If a task UUID in daily note was deleted in TaskWarrior:

**Expected AI Response:**
```
I found an issue with one of your tasks:

⚠️ Task "Some deleted task" (UUID: deleted-123) was deleted from TaskWarrior

This task appears in your daily note but no longer exists in TaskWarrior.
I've marked it as "missing" in the review.

Should I skip it or remove the reference from your daily note?
```

---

## Verification Checklist

After completing all steps, verify:

### MCP Server
- ✅ Server starts successfully (check logs)
- ✅ All 16 tools available
- ✅ Tools callable from Claude Desktop
- ✅ JSON responses parse correctly
- ✅ Error messages converted properly (PlorpError → ValueError)

### AI Integration
- ✅ Slash commands autocomplete
- ✅ Natural language task creation works
- ✅ AI provides helpful suggestions
- ✅ Multi-step workflows handled smoothly
- ✅ Error handling is graceful with alternatives
- ✅ Follow-up questions work

### Daily Workflow
- ✅ `/start` generates daily note with AI summary
- ✅ AI breaks down tasks by project/priority
- ✅ Duplicate detection with helpful response
- ✅ Task metadata displayed correctly

### Review Workflow
- ✅ `/review` guides through uncompleted tasks
- ✅ AI suggests actions based on task context
- ✅ Reflections collected naturally
- ✅ Review section appended to daily note
- ✅ TaskWarrior updates confirmed

### Inbox Workflow
- ✅ `/inbox` processes items with AI guidance
- ✅ AI suggests appropriate action per item
- ✅ Tasks created with intelligent defaults
- ✅ Notes categorized by type (project vs general)
- ✅ Bidirectional links maintained
- ✅ Summary provided after processing

### Notes Workflow
- ✅ `/note` creates notes with AI assistance
- ✅ `/task` creates tasks with AI guidance
- ✅ Note types respected (meetings → vault/meetings/)
- ✅ Natural language linking works
- ✅ AI helps structure note content
- ✅ Frontmatter managed correctly

### Task Operations
- ✅ Complete, defer, drop via conversation
- ✅ Priority changes via natural language
- ✅ Task info retrieval with formatting
- ✅ Intelligent due date suggestions

### Error Handling
- ✅ Invalid UUIDs caught with helpful messages
- ✅ Missing files reported clearly
- ✅ Notes outside vault rejected
- ✅ Duplicate operations prevented
- ✅ AI provides recovery options

---

## Common Issues & Troubleshooting

**Issue:** MCP server not appearing in Claude Desktop
- **Check:** `~/Library/Logs/Claude/mcp-server-plorp.log`
- **Fix:** Verify config uses full path: `/Users/jsd/Documents/plorp/.venv/bin/plorp-mcp`
- **Fix:** Restart Claude Desktop completely (Cmd+Q)

**Issue:** Tools listed but calls fail
- **Check:** `~/.config/plorp/mcp.log` for errors
- **Fix:** Verify brainplorp config exists: `cat ~/.config/plorp/config.yaml`
- **Fix:** Check vault path is valid

**Issue:** Slash commands don't work
- **Run:** `brainplorp init-claude`
- **Fix:** Restart Claude Desktop
- **Check:** `ls ~/.claude/commands/` for .md files

**Issue:** AI doesn't understand task references
- **Fix:** Use UUIDs explicitly: "task abc-123" not "that task"
- **Fix:** Provide more context in requests

**Issue:** Bidirectional links broken
- **Check:** Task annotations: `task <UUID> info | grep Note`
- **Check:** Note frontmatter: `grep tasks: /path/to/note.md`
- **Fix:** Re-run linking command

---

## Performance Verification

### Step P.1: Response Time

Track response times for common operations:

```
/start - Expected: < 2 seconds
/review (3 tasks) - Expected: < 5 seconds
/inbox (4 items) - Expected: < 3 seconds per item
Note creation - Expected: < 1 second
Task linking - Expected: < 2 seconds
```

### Step P.2: Concurrent Operations

Try rapid-fire commands:
```
Create task A
Create task B
Link note to task A
Mark task B complete
```

All should succeed without conflicts.

### Step P.3: Large Data Sets

Test with:
- 20+ tasks in daily note
- 10+ inbox items
- Complex project with many linked notes

Should remain responsive.

---

## Success Criteria

✅ MCP server starts reliably
✅ All 16 tools callable via Claude Desktop
✅ Slash commands work and provide AI guidance
✅ Natural language commands understood
✅ AI responses are helpful and contextual
✅ Error handling is graceful with recovery options
✅ Data flows correctly between TaskWarrior ↔ Obsidian
✅ Bidirectional links maintain integrity
✅ Multi-step workflows complete successfully
✅ Performance is acceptable for interactive use
✅ No crashes or data corruption
✅ Logs show expected behavior

---

## Next Steps After Manual Testing

1. Document any bugs or UX issues found
2. Identify AI response improvements needed
3. Consider additional error scenarios
4. Test with real-world usage patterns
5. Gather user feedback on AI interactions
6. Plan v1.2 enhancements

---

**Test Date:** _____________
**Tester:** _____________
**Claude Desktop Version:** _____________
**Result:** ✅ PASS / ❌ FAIL

**Notes:**

---

## Appendix: MCP Tool Reference

Quick reference for manual tool testing:

| Tool | Purpose | Key Parameters |
|------|---------|---------------|
| `plorp_start_day` | Generate daily note | `date` (optional) |
| `plorp_get_review_tasks` | Get uncompleted tasks | `date` (optional) |
| `plorp_add_review_notes` | Add reflections | `went_well`, `could_improve`, `tomorrow` |
| `plorp_mark_task_completed` | Complete task | `uuid` (required) |
| `plorp_defer_task` | Defer task | `uuid`, `new_due` (required) |
| `plorp_drop_task` | Delete task | `uuid` (required) |
| `plorp_set_task_priority` | Change priority | `uuid`, `priority` (H/M/L/"") |
| `plorp_get_inbox_items` | List inbox items | `date` (optional) |
| `plorp_create_task_from_inbox` | Inbox → Task | `item_text`, `description` (required) |
| `plorp_create_note_from_inbox` | Inbox → Note | `item_text`, `title` (required) |
| `plorp_create_both_from_inbox` | Inbox → Task+Note | `item_text`, `task_description`, `note_title` (required) |
| `plorp_discard_inbox_item` | Discard inbox item | `item_text` (required) |
| `plorp_create_note` | Create standalone note | `title` (required) |
| `plorp_create_note_with_task` | Create linked note | `title`, `task_uuid` (required) |
| `plorp_link_note_to_task` | Link existing note | `note_path`, `task_uuid` (required) |
| `plorp_get_task_info` | Get task details | `uuid` (required) |

---

**End of Manual Test Journey**
