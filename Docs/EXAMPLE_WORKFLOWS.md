# Example Workflows

This document provides practical examples of using brainplorp v1.1 with both the CLI and MCP (Claude Desktop) interfaces.

## Daily Workflows

### Morning Routine

#### Via CLI

```bash
# Generate today's daily note
brainplorp start

# Output:
# ✅ Created daily note: /vault/daily/2025-10-06.md
#
# 📊 Task Summary:
#   Overdue: 2
#   Due today: 5
#   Recurring: 3
#   Total: 10

# Open in Obsidian to review
open "/vault/daily/2025-10-06.md"
```

#### Via Claude Desktop

```
You: /start

Claude: I'll generate your daily note for today.

[Calls plorp_start_day]

✅ Created your daily note for 2025-10-06!

Here's what's on your plate:
• 2 overdue tasks (carry over from yesterday)
• 5 tasks due today
• 3 recurring tasks

Your daily note is at: /vault/daily/2025-10-06.md

Would you like me to:
1. Show you the overdue tasks so we can prioritize them?
2. Open the daily note in Obsidian?
3. Create a focused task list for the morning?
```

### Evening Review

#### Via CLI

```bash
# Review uncompleted tasks
brainplorp review

# Interactive prompts:
# Task: Fix authentication bug
#   Status: pending
#   Due: 2025-10-06
#   Priority: H
#   Project: backend
#
# What would you like to do?
# 1. Mark as done
# 2. Defer to another day
# 3. Change priority
# 4. Delete
# 5. Skip
#
# Choice: 2
#
# Defer to (YYYY-MM-DD): 2025-10-07
# ✅ Deferred task to 2025-10-07

# ... (repeat for each task)

# End of day reflection:
# What went well today? (optional): Completed code review process
# What could improve? (optional): Better time estimation
# Notes for tomorrow? (optional): Focus on authentication module

# ✅ Review complete!
```

#### Via Claude Desktop

```
You: /review

Claude: Let me check your tasks for today.

[Calls plorp_get_review_tasks]

I found 3 uncompleted tasks from your daily note:

1. **Fix authentication bug** (Priority: H, Due: today)
   - Looks like this is important. Did you make progress on this?

2. **Update documentation** (Priority: M, Due: today)
   - Documentation task.

3. **Team retrospective prep** (Priority: L, Due: today)
   - Planning task.

For each task, I can help you:
• Mark it complete
• Defer it to tomorrow or another day
• Change its priority
• Delete it if no longer needed

Let's start with the authentication bug. What happened with that?

You: I made good progress but need another day. Defer to tomorrow.

Claude: [Calls plorp_defer_task with uuid and new date]

✅ Deferred "Fix authentication bug" to 2025-10-07.

What about the documentation update?

You: That's done.

Claude: [Calls plorp_mark_task_completed]

✅ Marked "Update documentation" as complete!

And the retrospective prep?

You: Delete that, we postponed the meeting.

Claude: [Calls plorp_drop_task]

✅ Deleted "Team retrospective prep".

Great! Now let's add some reflections to your daily note.

What went well today?

You: Completed the code review process and unblocked the team.

What could be improved?

You: Better time estimation for complex tasks.

Any notes for tomorrow?

You: Focus on the authentication module first thing.

[Calls plorp_add_review_notes]

✅ Review complete! I've added your reflections to today's daily note.

Tomorrow's priority: Authentication module ⚡
```

## Inbox Processing

### Email to Task Workflow

#### Step 1: Capture Inbox Item (External Script)

```bash
# ~/.local/bin/email-to-inbox.sh
#!/bin/bash
# This script is called by email client (e.g., mutt, Mail.app)

INBOX_DIR="$HOME/Documents/vault/inbox"
CURRENT_MONTH=$(date +%Y-%m)
INBOX_FILE="$INBOX_DIR/${CURRENT_MONTH}.md"

# Extract subject from email
SUBJECT="$1"

# Append to inbox file
echo "- [ ] $SUBJECT" >> "$INBOX_FILE"
```

#### Step 2: Process Inbox via CLI

```bash
brainplorp inbox process

# Output:
# Found 5 inbox item(s)
#
# Item: Review Q4 budget proposal
#
# What would you like to do?
# 1. Create task
# 2. Create note
# 3. Create both (task + linked note)
# 4. Discard
# 5. Skip
#
# Choice: 1
#
# Task description: Review Q4 budget proposal
# Due date (YYYY-MM-DD, optional): 2025-10-10
# Priority (H/M/L, optional): H
# Project (optional): finance
#
# ✅ Created task abc-def-123
# ✅ Marked inbox item as processed
```

#### Step 3: Process Inbox via Claude Desktop

```
You: /inbox

Claude: Let me check your inbox for unprocessed items.

[Calls plorp_get_inbox_items]

You have 5 unprocessed inbox items:

1. **Review Q4 budget proposal**
2. **Schedule team building event**
3. **Research new deployment tools**
4. **Follow up with Sarah about design**
5. **Buy birthday gift for Mom**

Let's process them one by one. Starting with the budget proposal review:

This looks like it needs action. Would you like me to:
• Create a task for it
• Create a note to collect thoughts
• Create both a task and a linked note
• Just discard it

You: Create a task with high priority, due Friday.

Claude: [Calls plorp_create_task_from_inbox]

✅ Created task "Review Q4 budget proposal"
   • Priority: High
   • Due: 2025-10-10 (Friday)
   • UUID: abc-def-123

Next: "Schedule team building event". What should we do with this?

You: Create both a task and a note so I can brainstorm ideas.

Claude: [Calls plorp_create_both_from_inbox]

✅ Created task "Schedule team building event" (uuid: def-ghi-456)
✅ Created linked note at: /vault/notes/schedule-team-building-event.md

The note is ready for you to add ideas!

...
```

## Note-Taking Workflows

### Meeting Notes with Task Tracking

#### Via CLI

```bash
# Create note linked to existing task
brainplorp note "Q4 Planning Meeting" --task abc-123 --type meeting

# Output:
# ✅ Created note: /vault/meetings/q4-planning-meeting.md
# 🔗 Linked to task: abc-123
```

The generated note:

```markdown
---
title: Q4 Planning Meeting
created: 2025-10-06
type: meeting
tasks:
  - abc-123
---

# Q4 Planning Meeting

[Add your meeting notes here]
```

#### Via Claude Desktop

```
You: /task

Claude: I'll help you create a new task. Let me gather the details.

What's the task description?

You: Q4 planning meeting

Should I set a due date? (You can say "Friday", "tomorrow", "Oct 15", etc.)

You: This Friday

Any priority? (High, Medium, Low)

You: High

Which project does this belong to?

You: planning

Great! Should I create a linked note for this task? Meeting tasks often benefit from notes for agendas and minutes.

You: Yes, make it a meeting note.

Claude: [Calls plorp_create_note_with_task with note_type="meeting"]

✅ Created task "Q4 planning meeting"
   • Due: 2025-10-10 (Friday)
   • Priority: High
   • Project: planning
   • UUID: abc-def-789

✅ Created linked meeting note at: /vault/meetings/q4-planning-meeting.md

The note is ready for you to add:
• Meeting agenda
• Attendees
• Discussion notes
• Action items

Would you like me to help you structure the meeting agenda?
```

### Research Note with Multiple Tasks

#### Scenario

You're researching deployment tools and want to track multiple related tasks.

#### Via Claude Desktop

```
You: I'm researching deployment tools and need to track several related tasks. Can you help?

Claude: Absolutely! Let's create a research note and link the tasks to it.

First, let me create the research note.

[Calls plorp_create_note with note_type="project"]

✅ Created note: /vault/projects/deployment-tools-research.md

Now, what tasks should we create?

You:
1. Compare Docker vs Kubernetes pricing
2. Test deployment on staging environment
3. Write migration plan document

Claude: Great! I'll create these three tasks and link them to your research note.

[Calls plorp_create_task_from_inbox three times, then plorp_link_note_to_task for each]

✅ Created and linked 3 tasks:

1. **Compare Docker vs Kubernetes pricing**
   • UUID: task-001
   • Linked to: deployment-tools-research.md

2. **Test deployment on staging environment**
   • UUID: task-002
   • Linked to: deployment-tools-research.md

3. **Write migration plan document**
   • UUID: task-003
   • Linked to: deployment-tools-research.md

Your research note now references all three tasks in the frontmatter. When you work on the research, you'll see which tasks are related. And in TaskWarrior, each task has an annotation linking back to your research note!

Would you like me to set due dates or priorities for these tasks?
```

## Advanced Workflows

### GTD Weekly Review

#### Via CLI + Script

```bash
#!/bin/bash
# weekly-review.sh

echo "=== WEEKLY REVIEW ==="
echo

# Review each day of the past week
for i in {6..0}; do
  DATE=$(date -v-${i}d +%Y-%m-%d 2>/dev/null || date -d "${i} days ago" +%Y-%m-%d)
  NOTE_PATH="$HOME/Documents/vault/daily/${DATE}.md"

  if [ -f "$NOTE_PATH" ]; then
    echo "### $DATE"
    grep "^## Review" -A 20 "$NOTE_PATH" | head -15
    echo
  fi
done

# Check for stale tasks
echo "=== OVERDUE TASKS ==="
task status:pending due.before:today export | jq -r '.[] | "- \(.description) (due: \(.due))"'

echo
echo "=== NEXT ACTIONS ==="
task status:pending due.before:+7d export | jq -r '.[] | "- \(.description) (due: \(.due), priority: \(.priority // \"none\"))"'
```

#### Via Claude Desktop

```
You: Can you help me with my weekly review? I want to see what I accomplished this week and plan for next week.

Claude: I'd be happy to help! Let me gather information about your week.

[Calls plorp_get_review_tasks for each day of the past week]

Here's your week in review:

**Monday 2025-09-30**
• Completed: 8 tasks
• Reflection: "Good focus day, completed authentication refactor"

**Tuesday 2025-10-01**
• Completed: 6 tasks
• Reflection: "Productive meetings, less coding time"

**Wednesday 2025-10-02**
• Completed: 10 tasks ⚡
• Reflection: "Best day this week, cleared backlog"

**Thursday 2025-10-03**
• Completed: 5 tasks
• Reflection: "Struggled with unclear requirements"

**Friday 2025-10-04**
• Completed: 7 tasks
• Reflection: "Code review day, unblocked team"

**Week Summary:**
• Total completed: 36 tasks
• Average: 7.2 tasks/day
• Best day: Wednesday (10 tasks)

**Patterns I notice:**
• You're most productive mid-week
• Meeting-heavy days (Tuesday) reduce coding output
• Unclear requirements slow you down (Thursday)

**Outstanding items:**
• 3 overdue tasks (would you like to review these?)
• 12 tasks due next week

Would you like to:
1. Review and reschedule overdue tasks?
2. Plan priorities for next week?
3. Set goals for the upcoming week?
```

### Project Planning

#### Via Claude Desktop

```
You: I'm starting a new project called "Customer Portal v2". Can you help me set it up?

Claude: Great! Let's set up your project systematically. I'll help you:
1. Create a project note
2. Set up initial tasks
3. Link everything together

First, tell me about the project. What are the main objectives?

You: Build a new customer portal with modern UI, authentication, and dashboard features.

Claude: [Calls plorp_create_note with note_type="project"]

✅ Created project note: /vault/projects/customer-portal-v2.md

Now let's break this down into phases. I'm thinking:
1. **Planning Phase** - Requirements, design, architecture
2. **Development Phase** - UI, auth, dashboard implementation
3. **Testing Phase** - QA, user testing
4. **Launch Phase** - Deployment, monitoring

Does that structure work?

You: Yes, perfect.

Claude: Let me create tasks for the planning phase:

[Creates multiple tasks]

✅ Created Planning Phase tasks:
1. "Write technical requirements doc" (Priority: H, Due: Oct 13)
2. "Design UI mockups" (Priority: H, Due: Oct 15)
3. "Define API architecture" (Priority: M, Due: Oct 15)
4. "Set up development environment" (Priority: M, Due: Oct 10)

All tasks are:
• Tagged with `+customer-portal-v2`
• Linked to your project note
• Set with reasonable due dates (can adjust)

Next steps:
• I can create tasks for the other phases when you're ready
• Would you like me to help draft the requirements doc?
• Should we schedule a planning meeting?

What would you like to focus on first?
```

## Integration Examples

### TaskWarrior + Obsidian Sync

```bash
# Create task with context in TaskWarrior
task add "Implement OAuth flow" project:customer-portal due:friday priority:H +backend

# Task UUID: xyz-789

# Create linked note via plorp
brainplorp note "OAuth Implementation Notes" --task xyz-789 --type project

# Now:
# - Task in TaskWarrior has annotation: "Note: vault/projects/oauth-implementation-notes.md"
# - Note in Obsidian has frontmatter: tasks: [xyz-789]
# - Bidirectional link maintained
```

### Daily Note → Task Creation

When working in your daily note, you might identify new tasks:

```markdown
# 2025-10-06 Sunday

## Notes

- Need to fix the CSS bug in the header
- Should refactor the authentication module
- Call Sarah about the design review
```

#### Via Claude Desktop

```
You: I found some action items in my daily note. Can you help me convert them to tasks?

[Share the notes section]

Claude: I see three action items! Let me create tasks for these:

[Calls plorp_create_task_from_inbox for each]

✅ Created 3 tasks from your notes:

1. **Fix CSS bug in header**
   • Priority: M (can adjust)
   • UUID: task-css-001

2. **Refactor authentication module**
   • Priority: M (can adjust)
   • UUID: task-auth-002

3. **Call Sarah about design review**
   • Priority: M (can adjust)
   • UUID: task-sarah-003

For the call with Sarah, should I set a due date? Phone calls are usually time-sensitive.

You: Set it for tomorrow morning.

Claude: [Calls plorp_defer_task or creates with due date]

✅ Updated task "Call Sarah about design review"
   • Due: 2025-10-07 09:00

Would you like me to create a meeting note for the design review discussion?
```

## Tips & Tricks

### 1. Morning Power Hour

```bash
# Generate daily note
brainplorp start

# Focus on high-priority items
task status:pending priority:H export | jq -r '.[] | "→ \(.description)"'

# Time-block your day in calendar
```

### 2. Batch Inbox Processing

Process inbox items weekly during review:

```bash
# Every Friday
crontab -e

# Add:
0 16 * * 5 cd ~/Documents/brainplorp && brainplorp inbox process
```

### 3. Project Templates

Create a script to initialize new projects:

```bash
#!/bin/bash
# new-project.sh

PROJECT_NAME="$1"
brainplorp note "$PROJECT_NAME" --type project

echo "Created project note for $PROJECT_NAME"
echo "Next: Create initial tasks with tags +${PROJECT_NAME,,}"
```

### 4. Task Context Capture

When creating tasks, always link to notes:

```bash
# Instead of:
task add "Fix authentication bug"

# Do:
brainplorp note "Auth Bug Investigation" --type general
brainplorp link <task-uuid> notes/auth-bug-investigation.md
```

Now you have a place to capture:
- Debugging notes
- Root cause analysis
- Solution approaches
- Testing steps

## Conclusion

brainplorp v1.1 works seamlessly with both CLI and Claude Desktop. Choose the interface that fits your workflow:

- **CLI**: Quick commands, scripting, automation
- **Claude Desktop**: Natural language, guided workflows, intelligent suggestions

Both interfaces share the same data, so you can mix and match based on context!
