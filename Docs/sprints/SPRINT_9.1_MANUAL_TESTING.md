# Sprint 9.1 Manual Testing Guide
## Fast Task Query Commands

**Version:** 1.5.1
**Sprint:** 9.1
**Testing Date:** _____________
**Tester:** _____________

---

## Prerequisites

- brainplorp v1.5.1 installed
- TaskWarrior configured with sample tasks
- Claude Desktop with brainplorp MCP server configured
- Test tasks with various priorities, projects, due dates

---

## Test Environment Setup

```bash
# Verify version
brainplorp --version  # Should show 1.5.1

# Create test tasks
task add "Urgent API bug" priority:H project:work.api-rewrite due:today
task add "Write documentation" priority:M project:work.docs due:tomorrow
task add "Buy groceries" project:home due:today
task add "Plan vacation" priority:L due:2025-10-20
task add "Overdue task" due:2025-10-01

# Verify tasks exist
task status:pending count  # Should show 5+
```

---

## Tier 1: CLI Commands (<100ms)

### Test 1.1: Basic Task List
**Command:** `brainplorp tasks`

**Steps:**
```bash
brainplorp tasks
```

**Expected Results:**
- ✅ Rich table output with colors
- ✅ Shows priority emojis (🔴 H, 🟡 M)
- ✅ Human-readable dates ("today", "tomorrow", "2d ago")
- ✅ Default limit 50 tasks
- ✅ Response time <100ms

**Pass/Fail:** ______

---

### Test 1.2: Urgent Tasks Filter
**Command:** `brainplorp tasks --urgent`

**Steps:**
```bash
brainplorp tasks --urgent
```

**Expected Results:**
- ✅ Only priority:H tasks shown
- ✅ All have 🔴 emoji
- ✅ Correct count
- ✅ Response time <100ms

**Pass/Fail:** ______

---

### Test 1.3: Important Tasks Filter
**Command:** `brainplorp tasks --important`

**Steps:**
```bash
brainplorp tasks --important
```

**Expected Results:**
- ✅ Only priority:M tasks shown
- ✅ All have 🟡 emoji
- ✅ Correct count

**Pass/Fail:** ______

---

### Test 1.4: Project Filter
**Command:** `brainplorp tasks --project work`

**Steps:**
```bash
brainplorp tasks --project work
```

**Expected Results:**
- ✅ Only tasks in 'work' project shown
- ✅ Subprojects included (work.api-rewrite, work.docs)
- ✅ Correct project column values

**Pass/Fail:** ______

---

### Test 1.5: Due Today Filter
**Command:** `brainplorp tasks --due today`

**Steps:**
```bash
brainplorp tasks --due today
```

**Expected Results:**
- ✅ Only tasks due today shown
- ✅ Date shown as "today" in human-readable format
- ✅ Correct count

**Pass/Fail:** ______

---

### Test 1.6: Due Tomorrow Filter
**Command:** `brainplorp tasks --due tomorrow`

**Steps:**
```bash
brainplorp tasks --due tomorrow
```

**Expected Results:**
- ✅ Only tasks due tomorrow shown
- ✅ Date shown as "tomorrow"
- ✅ Correct count

**Pass/Fail:** ______

---

### Test 1.7: Overdue Filter
**Command:** `brainplorp tasks --due overdue`

**Steps:**
```bash
brainplorp tasks --due overdue
```

**Expected Results:**
- ✅ Only overdue tasks shown
- ✅ Dates in past
- ✅ Human-readable ("5d ago", etc.)

**Pass/Fail:** ______

---

### Test 1.8: Due This Week Filter
**Command:** `brainplorp tasks --due week`

**Steps:**
```bash
brainplorp tasks --due week
```

**Expected Results:**
- ✅ Tasks due within 7 days shown
- ✅ Includes today and future dates
- ✅ Correct count

**Pass/Fail:** ______

---

### Test 1.9: Limit Results
**Command:** `brainplorp tasks --limit 5`

**Steps:**
```bash
brainplorp tasks --limit 5
```

**Expected Results:**
- ✅ Exactly 5 tasks shown (or fewer if less exist)
- ✅ Most urgent/recent first
- ✅ Clear output

**Pass/Fail:** ______

---

### Test 1.10: Combined Filters
**Command:** `brainplorp tasks --urgent --project work`

**Steps:**
```bash
brainplorp tasks --urgent --project work
```

**Expected Results:**
- ✅ Only urgent tasks in work project shown
- ✅ Both filters applied correctly
- ✅ Correct count

**Pass/Fail:** ______

---

### Test 1.11: Simple Format
**Command:** `brainplorp tasks --format simple`

**Steps:**
```bash
brainplorp tasks --format simple --limit 3
```

**Expected Results:**
- ✅ Plain text output (no emojis)
- ✅ No table borders
- ✅ Machine-readable format
- ✅ Good for scripts/parsing

**Pass/Fail:** ______

---

### Test 1.12: JSON Format
**Command:** `brainplorp tasks --format json`

**Steps:**
```bash
brainplorp tasks --format json --limit 3
```

**Expected Results:**
- ✅ Valid JSON output
- ✅ Array of task objects
- ✅ All fields present (uuid, description, priority, etc.)
- ✅ Can be parsed with `jq`

**Pass/Fail:** ______

---

### Test 1.13: Multiple Filters + Limit
**Command:** `brainplorp tasks --project work --due today --limit 10`

**Steps:**
```bash
brainplorp tasks --project work --due today --limit 10
```

**Expected Results:**
- ✅ All filters applied
- ✅ Max 10 results
- ✅ Correct filtering

**Pass/Fail:** ______

---

## Tier 2: Slash Commands (1-2s in Claude Desktop)

### Test 2.1: /tasks Command
**Command:** `/tasks` in Claude Desktop

**Steps:**
1. Open Claude Desktop
2. Type `/tasks` and press Enter
3. Observe response time

**Expected Results:**
- ✅ All pending tasks displayed
- ✅ Rich table format
- ✅ Response time 1-2 seconds
- ✅ Same output as `brainplorp tasks`

**Pass/Fail:** ______

---

### Test 2.2: /urgent Command
**Command:** `/urgent` in Claude Desktop

**Steps:**
1. Type `/urgent` and press Enter
2. Verify filtering

**Expected Results:**
- ✅ Only priority:H tasks shown
- ✅ Response time 1-2 seconds
- ✅ Same output as `brainplorp tasks --urgent`

**Pass/Fail:** ______

---

### Test 2.3: /today Command
**Command:** `/today` in Claude Desktop

**Steps:**
1. Type `/today` and press Enter

**Expected Results:**
- ✅ Only tasks due today shown
- ✅ Response time 1-2 seconds
- ✅ Same output as `brainplorp tasks --due today`

**Pass/Fail:** ______

---

### Test 2.4: /overdue Command
**Command:** `/overdue` in Claude Desktop

**Steps:**
1. Type `/overdue` and press Enter

**Expected Results:**
- ✅ Only overdue tasks shown
- ✅ Response time 1-2 seconds
- ✅ Same output as `brainplorp tasks --due overdue`

**Pass/Fail:** ______

---

### Test 2.5: /work-tasks Command
**Command:** `/work-tasks` in Claude Desktop

**Steps:**
1. Type `/work-tasks` and press Enter

**Expected Results:**
- ✅ Only work project tasks shown
- ✅ Response time 1-2 seconds
- ✅ Same output as `brainplorp tasks --project work`

**Pass/Fail:** ______

---

## Tier 3: Natural Language (5-8s)

### Test 3.1: Simple Query with Natural Language
**Query:** "Show me my urgent tasks"

**Steps:**
1. Ask in natural language
2. Observe tool usage

**Expected Results:**
- ✅ Uses plorp_get_tasks MCP tool (or recognizes to use slash command)
- ✅ Response time 5-8 seconds (agent reasoning)
- ✅ Correct filtering applied
- ✅ Human-friendly response

**Pass/Fail:** ______

---

### Test 3.2: Complex Query with Natural Language
**Query:** "Show me urgent tasks in the work project due this week"

**Steps:**
1. Ask in natural language

**Expected Results:**
- ✅ Multiple filters applied
- ✅ Correct interpretation
- ✅ Response time 5-8 seconds
- ✅ Proper results

**Pass/Fail:** ______

---

### Test 3.3: Analytical Query (Tier 3 Appropriate)
**Query:** "Analyze my task distribution by project and priority"

**Steps:**
1. Ask complex analytical question

**Expected Results:**
- ✅ Agent uses multiple tool calls
- ✅ Provides analysis/insights
- ✅ Response time 5-8 seconds (expected for intelligence)
- ✅ Value-added beyond simple query

**Pass/Fail:** ______

---

## Performance Benchmarks

### Benchmark 1: CLI Speed
**Test:** Run `brainplorp tasks --limit 5` 10 times

**Steps:**
```bash
time brainplorp tasks --limit 5
# Run 10 times, record average
```

**Expected Results:**
- ✅ Average <100ms
- ✅ Consistent response time
- ✅ No degradation over multiple runs

**Actual Time:** ______ ms (average)

**Pass/Fail:** ______

---

### Benchmark 2: Slash Command Speed
**Test:** Run `/urgent` 5 times in Claude Desktop

**Steps:**
1. Type `/urgent` and press Enter
2. Note timestamp to response
3. Repeat 5 times

**Expected Results:**
- ✅ Average 1-2 seconds
- ✅ Faster than natural language equivalent
- ✅ Consistent performance

**Actual Time:** ______ seconds (average)

**Pass/Fail:** ______

---

### Benchmark 3: Natural Language Baseline
**Test:** Ask "show me urgent tasks" 5 times

**Steps:**
1. Ask in natural language
2. Measure response time
3. Repeat 5 times

**Expected Results:**
- ✅ Average 5-8 seconds
- ✅ Slower than slash commands (expected)
- ✅ Agent reasoning visible

**Actual Time:** ______ seconds (average)

**Pass/Fail:** ______

---

## Edge Cases

### Test E1: No Tasks Matching Filter
**Steps:**
```bash
brainplorp tasks --urgent --project nonexistent
```

**Expected Results:**
- ✅ Empty table or "No tasks found" message
- ✅ No error/crash
- ✅ Clear messaging

**Pass/Fail:** ______

---

### Test E2: Very Large Task List
**Steps:**
```bash
# Create 100+ tasks
for i in {1..100}; do task add "Test task $i"; done
brainplorp tasks
```

**Expected Results:**
- ✅ Default limit (50) applied
- ✅ Performance still good
- ✅ Table renders correctly

**Pass/Fail:** ______

---

### Test E3: Tasks with No Due Date
**Steps:**
```bash
task add "No due date task"
brainplorp tasks --due today
```

**Expected Results:**
- ✅ Task without due date not shown in --due today
- ✅ Shows in default listing
- ✅ Due column shows empty/dash

**Pass/Fail:** ______

---

### Test E4: Tasks with No Priority
**Steps:**
```bash
task add "No priority task"
brainplorp tasks --urgent
```

**Expected Results:**
- ✅ Task not shown in --urgent
- ✅ Shows in default listing
- ✅ No priority emoji

**Pass/Fail:** ______

---

## User Experience Tests

### Test UX1: Human-Readable Dates
**Steps:**
```bash
# Create tasks with various dates
task add "Task due today" due:today
task add "Task due tomorrow" due:tomorrow
task add "Task due 2 days" due:2d
task add "Task overdue 5 days" due:-5d
brainplorp tasks --limit 10
```

**Expected Results:**
- ✅ Shows "today" not date string
- ✅ Shows "tomorrow" not date string
- ✅ Shows "2d" or "in 2 days"
- ✅ Shows "5d ago" for overdue

**Pass/Fail:** ______

---

### Test UX2: Priority Emojis
**Steps:**
```bash
brainplorp tasks --limit 20
```

**Expected Results:**
- ✅ 🔴 for priority:H
- ✅ 🟡 for priority:M
- ✅ Nothing or dash for priority:L or no priority
- ✅ Consistent across all output

**Pass/Fail:** ______

---

### Test UX3: Help Text
**Steps:**
```bash
brainplorp tasks --help
```

**Expected Results:**
- ✅ All options documented
- ✅ Examples provided
- ✅ Clear descriptions
- ✅ Default values shown

**Pass/Fail:** ______

---

## Test Summary

**Total Tests:** 33
**Passed:** ______
**Failed:** ______
**Skipped:** ______

**Performance:**
- CLI Average: ______ ms (target: <100ms)
- Slash Average: ______ s (target: 1-2s)
- Natural Language Average: ______ s (target: 5-8s)

---

## Speedup Verification

**Baseline (Natural Language):** ______ seconds
**CLI Speedup:** ______x faster (target: 50-80x)
**Slash Speedup:** ______x faster (target: 3-4x)

---

## Issues Found

| Test # | Issue Description | Severity | Notes |
|--------|-------------------|----------|-------|
|        |                   |          |       |
|        |                   |          |       |

---

## Sign-Off

**Tester Signature:** _____________
**Date:** _____________
**Status:** [ ] PASS [ ] FAIL [ ] NEEDS REVIEW

---

## Notes

(Additional observations, performance notes, UX feedback, etc.)
