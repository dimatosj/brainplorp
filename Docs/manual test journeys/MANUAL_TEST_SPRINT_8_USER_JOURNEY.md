# Sprint 8 Manual Testing Guide: User Journey

**Purpose:** Validate Sprint 8 project management implementation through real-world workflows.

**Test Environment:**
- Vault: `/Users/jsd/vault` (configured in `~/.config/plorp/config.yaml`)
- TaskWarrior: Must be installed and configured
- Obsidian: Should have Bases plugin enabled (optional for this test)

**Duration:** ~30 minutes

---

## Pre-Flight Check

### 1. Verify Environment

```bash
# Check brainplorp is installed
brainplorp --version

# Check TaskWarrior is working
task diagnostics | grep "Version"

# Check vault exists
ls -la /Users/jsd/vault/projects/

# Check current focus state
brainplorp focus get
```

**Expected:**
- brainplorp version shown
- TaskWarrior 3.x detected
- `/Users/jsd/vault/projects/` directory exists (may have existing projects)
- Default focus is "home"

---

## Journey 1: Personal Project Setup

**Scenario:** User wants to track a home improvement project

### Step 1: Create a Personal Project

```bash
brainplorp project create \
  --name "kitchen-remodel" \
  --domain "home" \
  --workstream "house" \
  --description "Kitchen renovation project"
```

**Expected Output:**
```
✓ Created project: home.house.kitchen-remodel
  Path: /Users/jsd/vault/projects/home.house.kitchen-remodel.md
```

### Step 2: Verify Project File

```bash
cat /Users/jsd/vault/projects/home.house.kitchen-remodel.md
```

**Expected Content:**
```yaml
---
domain: home
workstream: house
project_name: kitchen-remodel
full_path: home.house.kitchen-remodel
state: active
created_at: 2025-10-07T...
description: Kitchen renovation project
task_uuids: []
needs_review: false
tags: [project, home, house]
---

# Kitchen Remodel

Kitchen renovation project

## Tasks

<!-- Tasks will appear here -->
```

### Step 3: Create Tasks in Project

```bash
# Create first task
brainplorp project add-task \
  home.house.kitchen-remodel \
  "Get contractor quotes" \
  --due "friday" \
  --priority "H"

# Create second task
brainplorp project add-task \
  home.house.kitchen-remodel \
  "Choose countertop material" \
  --priority "M"

# Create third task
brainplorp project add-task \
  home.house.kitchen-remodel \
  "Order appliances" \
  --due "2025-10-20"
```

**Expected Output (each):**
```
✓ Created task in project home.house.kitchen-remodel
  UUID: abc-123-...
```

### Step 4: Verify TaskWarrior Integration

```bash
# Check tasks exist in TaskWarrior
task project:home.house.kitchen-remodel export | python3 -m json.tool

# Check one task's annotations
task <uuid-from-above> info | grep annotation
```

**Expected:**
- 3 tasks shown with project field set
- Each task has annotation: `plorp-project:home.house.kitchen-remodel`

### Step 5: Verify Bidirectional Linking

```bash
# Re-read project file
cat /Users/jsd/vault/projects/home.house.kitchen-remodel.md
```

**Expected:**
- `task_uuids:` array now contains 3 UUIDs
- UUIDs match those returned by TaskWarrior

### Step 6: List Project Tasks

```bash
# CLI: List all tasks in project
brainplorp project tasks home.house.kitchen-remodel

# CLI: Get project info (includes task count)
brainplorp project info home.house.kitchen-remodel
```

**Expected:**
- 3 tasks listed with descriptions and metadata
- Project info shows `task_count: 3`

---

## Journey 2: Work Projects with Multiple Workstreams

**Scenario:** User manages multiple work initiatives

### Step 7: Set Work Focus

```bash
brainplorp focus set work
brainplorp focus get
```

**Expected:**
```
✓ Focused on domain: work
Current focus: work
```

### Step 8: Create Multiple Work Projects

```bash
# Marketing workstream
brainplorp project create \
  --name "website-redesign" \
  --domain "work" \
  --workstream "marketing" \
  --description "Redesign company website"

brainplorp project create \
  --name "blog-launch" \
  --domain "work" \
  --workstream "marketing" \
  --state "planning"

# Engineering workstream
brainplorp project create \
  --name "api-v2" \
  --domain "work" \
  --workstream "engineering" \
  --description "Build API v2"

# Direct domain project (no workstream)
brainplorp project create \
  --name "quarterly-review" \
  --domain "work" \
  --description "Q4 performance review"
```

**Expected:**
- 4 projects created
- Files created:
  - `work.marketing.website-redesign.md`
  - `work.marketing.blog-launch.md`
  - `work.engineering.api-v2.md`
  - `work.quarterly-review.md` (2-segment path)

### Step 9: List Projects with Filters

```bash
# List all work projects
brainplorp project list --domain work

# List only marketing projects
brainplorp project list --domain work --workstream marketing

# List all active projects
brainplorp project list --state active

# List all projects (no filter)
brainplorp project list
```

**Expected:**
- First command: 4 work projects
- Second command: 2 marketing projects
- Third command: All active projects (should exclude "blog-launch" which is "planning")
- Fourth command: All projects from all domains (5 total: 1 home + 4 work)

### Step 10: Update Project State

```bash
# Start the blog launch project
brainplorp project update-state work.marketing.blog-launch active

# Complete the quarterly review
brainplorp project update-state work.quarterly-review completed

# Block the API project
brainplorp project update-state work.engineering.api-v2 blocked
```

**Expected:**
- Each command shows: `✓ Updated project state`
- Verify with `brainplorp project info <full-path>` for each

---

## Journey 3: Task Querying Across Projects

**Scenario:** User wants to see all tasks for a domain or workstream

### Step 11: Create Tasks in Work Projects

```bash
# Add tasks to marketing projects
brainplorp project add-task work.marketing.website-redesign "Design homepage mockup" --priority H
brainplorp project add-task work.marketing.website-redesign "Write copy" --priority M
brainplorp project add-task work.marketing.blog-launch "Research blog platform" --due tomorrow

# Add tasks to engineering project
brainplorp project add-task work.engineering.api-v2 "Design API schema" --priority H
brainplorp project add-task work.engineering.api-v2 "Setup database" --due friday
```

**Expected:**
- 5 tasks created across 3 projects
- All have `project:work.*.something` in TaskWarrior

### Step 12: Query Tasks by Domain

```bash
# List all tasks in work domain
brainplorp tasks list --domain work

# List all tasks in home domain
brainplorp tasks list --domain home
```

**Expected:**
- Work domain: 5 tasks
- Home domain: 3 tasks (from kitchen-remodel)

### Step 13: Query Tasks by Workstream

```bash
# List all marketing tasks
brainplorp tasks list --domain work --workstream marketing

# List all engineering tasks
brainplorp tasks list --domain work --workstream engineering
```

**Expected:**
- Marketing: 3 tasks
- Engineering: 2 tasks

### Step 14: Find Orphaned Tasks

```bash
# Create orphaned task (project field but no project note)
task add "Random work task" project:work.nonexistent.project

# Query orphaned tasks
brainplorp tasks list --orphaned
```

**Expected:**
- Shows the orphaned task with warning message
- Indicates project file doesn't exist

---

## Journey 4: MCP Integration Testing

**Scenario:** User interacts via Claude Code MCP tools

### Step 15: Test MCP Tools (via CLI simulation)

```bash
# Simulate MCP: Get focused domain
python3 -c "
from plorp.core.projects import get_focused_domain_mcp
print(f'MCP Focus: {get_focused_domain_mcp()}')
"

# Simulate MCP: Set focus
python3 -c "
from plorp.core.projects import set_focused_domain_mcp
set_focused_domain_mcp('personal')
print('Set MCP focus to personal')
"

# Verify CLI and MCP focuses are independent
brainplorp focus get
python3 -c "
from plorp.core.projects import get_focused_domain_mcp
print(f'MCP Focus: {get_focused_domain_mcp()}')
"
```

**Expected:**
- CLI focus: `work` (from Step 7)
- MCP focus: `personal` (just set)
- Two separate focus files exist:
  - `~/.config/plorp/cli_focus.txt` → "work"
  - `~/.config/plorp/mcp_focus.txt` → "personal"

### Step 16: Test MCP Project Creation

```bash
python3 -c "
from plorp.core.projects import create_project
project = create_project(
    name='vacation-planning',
    domain='personal',
    workstream='travel',
    description='Plan summer vacation'
)
print(f'Created: {project[\"full_path\"]}')
print(f'State: {project[\"state\"]}')
"
```

**Expected:**
- Project created: `personal.travel.vacation-planning`
- File exists at `/Users/jsd/vault/projects/personal.travel.vacation-planning.md`

### Step 17: Test MCP Project Listing

```bash
python3 -c "
from plorp.core.projects import list_projects
result = list_projects(domain='work')
print(f'Total work projects: {len(result[\"projects\"])}')
for p in result['projects']:
    print(f'  - {p[\"full_path\"]} ({p[\"state\"]})')
"
```

**Expected:**
- Lists all work projects with their states
- Grouped dict should show projects organized by domain → workstream → project

---

## Journey 5: Edge Cases & Error Handling

### Step 18: Invalid Domain

```bash
brainplorp project create \
  --name "test" \
  --domain "invalid-domain" \
  2>&1 | grep -i error
```

**Expected:**
```
Error: Invalid domain: invalid-domain. Must be one of ['work', 'home', 'personal']
```

### Step 19: Duplicate Project

```bash
# Try to create project that already exists
brainplorp project create \
  --name "kitchen-remodel" \
  --domain "home" \
  --workstream "house" \
  2>&1 | grep -i error
```

**Expected:**
```
Error: Project already exists: home.house.kitchen-remodel
```

### Step 20: Invalid State Transition

```bash
brainplorp project update-state work.marketing.website-redesign invalid-state 2>&1 | grep -i error
```

**Expected:**
```
Error: Invalid state: invalid-state. Must be one of [active, planning, completed, blocked, archived]
```

### Step 21: Task in Nonexistent Project

```bash
brainplorp project add-task nonexistent.project.path "Test task" 2>&1 | grep -i error
```

**Expected:**
```
Error: Project not found: nonexistent.project.path
```

---

## Journey 6: Obsidian Integration

### Step 22: View Projects in Obsidian

**Manual Steps:**
1. Open Obsidian
2. Navigate to `vault/projects/` folder
3. Open `work.marketing.website-redesign.md`

**Expected:**
- Frontmatter is properly formatted YAML
- Tags appear in Obsidian's tag system
- Note body shows project description
- Task UUIDs are in frontmatter array

### Step 23: Verify Bases Plugin Integration (if enabled)

**Manual Steps:**
1. Create a `.base` file in vault root: `projects.base`
2. Add query:
   ```yaml
   query: |
     FROM "projects"
     WHERE state = "active"
     SELECT domain, workstream, project_name, state
   ```
3. Open in Obsidian

**Expected (if Bases plugin enabled):**
- Table view shows all active projects
- Columns: domain, workstream, project_name, state
- Can sort and filter interactively

**If Bases plugin NOT enabled:**
- Note to user: "Install Bases plugin to enable table views"

---

## Journey 7: Cleanup & State Verification

### Step 24: Project Deletion

```bash
# Delete completed project
brainplorp project delete work.quarterly-review

# Verify it's gone
brainplorp project list --domain work | grep quarterly
ls /Users/jsd/vault/projects/ | grep quarterly
```

**Expected:**
- Project deleted successfully
- Not in list output
- File removed from vault

### Step 25: Final State Check

```bash
# Count all projects
echo "Total projects:"
ls /Users/jsd/vault/projects/ | wc -l

# Count all tasks in TaskWarrior with project field
echo "Total tasks with projects:"
task project.any: export | python3 -c "import sys, json; print(len(json.load(sys.stdin)))"

# Show summary by domain
brainplorp project list --domain work | head -5
brainplorp project list --domain home | head -5
brainplorp project list --domain personal | head -5
```

**Expected Summary:**
- **Work:** 3 projects (website-redesign, blog-launch, api-v2)
- **Home:** 1 project (kitchen-remodel)
- **Personal:** 1 project (vacation-planning)
- **Total tasks:** 8 tasks linked to projects

---

## Test Results Checklist

After completing all journeys, verify:

- [ ] Project notes created in `vault/projects/` with correct frontmatter
- [ ] Tasks created in TaskWarrior with correct `project:` field
- [ ] Bidirectional linking works (tasks have annotations, projects have UUIDs)
- [ ] CLI commands work (`brainplorp project`, `brainplorp focus`)
- [ ] MCP integration works (Python imports and function calls)
- [ ] Focus mechanism persists across sessions
- [ ] CLI and MCP focus are independent
- [ ] Filtering by domain/workstream/state works
- [ ] Error handling is graceful and informative
- [ ] Project deletion cleans up files
- [ ] Obsidian can read project notes correctly

---

## Known Limitations (Expected Behavior)

1. **Orphaned UUIDs:** If you delete a task in TaskWarrior, the UUID remains in project frontmatter
   - **Expected:** Warning shown in `brainplorp project tasks` output
   - **Future:** Sprint 9 will add `brainplorp project sync` command

2. **Workstream validation:** Any workstream name is accepted
   - **Expected:** No warnings for unusual workstreams
   - **Future:** Sprint 9 will add suggested workstream validation

3. **Project-task sync:** Deleting project note doesn't delete tasks
   - **Expected:** Tasks remain in TaskWarrior with orphaned `project:` field
   - **Future:** Sprint 9 will add cleanup workflows

---

## Troubleshooting

**Issue:** `plorp: command not found`
- Solution: Ensure virtual environment activated: `source .venv/bin/activate`
- Or use: `uv run plorp` instead

**Issue:** `task: command not found`
- Solution: Install TaskWarrior 3.x: `brew install task` (macOS) or equivalent

**Issue:** Project directory doesn't exist
- Solution: Verify vault path in config: `cat ~/.config/plorp/config.yaml`

**Issue:** Permission errors
- Solution: Check vault path in config: `~/.config/plorp/config.yaml`

**Issue:** Python import errors
- Solution: Reinstall plorp: `pip install -e .` or `uv sync`

---

## Next Steps After Testing

1. **Report findings** to lead engineer or PM
2. **Document any bugs** discovered
3. **Suggest UX improvements** based on real usage
4. **Decide Sprint 9 scope** based on pain points found

---

**Test Date:** __________
**Tester:** __________
**Result:** ☐ Pass  ☐ Fail (details: _________________________)
