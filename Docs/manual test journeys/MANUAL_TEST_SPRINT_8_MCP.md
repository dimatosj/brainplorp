# Sprint 8 MCP Testing Guide: Project Management via Claude

**Purpose:** Test Sprint 8 project management through Claude Desktop MCP integration

**Prerequisites:**
- Claude Desktop with plorp MCP server configured
- TaskWarrior 3.x installed
- Vault at `/Users/jsd/vault/` configured

**Duration:** ~15-20 minutes

---

## Setup Verification

### Step 0: Verify MCP Server is Running

**In Claude Desktop, send this message:**

> "Can you check if the plorp MCP tools are available? List the project management tools."

**Expected Response:**
Claude should list MCP tools including:
- `plorp_create_project`
- `plorp_list_projects`
- `plorp_get_project_info`
- `plorp_update_project_state`
- `plorp_delete_project`
- `plorp_create_task_in_project`
- `plorp_list_project_tasks`
- `plorp_list_tasks_by_domain`
- `plorp_list_orphaned_tasks`
- `plorp_set_focused_domain`
- `plorp_get_focused_domain`

If tools are not available, check MCP server configuration.

---

## Test Journey 1: Create Work Project

### Test 1.1: Create Marketing Project

**Say to Claude:**

> "Create a new project called 'website-redesign' in the work domain under the marketing workstream. The description should be 'Redesign company website with modern UI'."

**Expected:**
- Claude calls `plorp_create_project`
- Returns project info with full path `work.marketing.website-redesign`
- Confirms project state is `active`
- Shows project was created at `/Users/jsd/vault/projects/work.marketing.website-redesign.md`

**Verify the file:**

> "Can you show me the contents of the project file?"

**Expected:**
- Claude reads the markdown file
- Shows YAML frontmatter with correct metadata
- Confirms `task_uuids` is empty array

---

### Test 1.2: Add Tasks to Project

**Say to Claude:**

> "Add these tasks to the website-redesign project:
> 1. Design homepage mockup - high priority, due Friday
> 2. Write copy for landing page - medium priority
> 3. Setup staging environment - due tomorrow"

**Expected:**
- Claude calls `plorp_create_task_in_project` three times
- Each task returns a UUID
- Confirms tasks added to TaskWarrior with correct project field
- Shows bidirectional linking created

**Verify tasks:**

> "Show me all tasks in the website-redesign project"

**Expected:**
- Claude calls `plorp_list_project_tasks`
- Lists 3 tasks with descriptions, priorities, and due dates
- Shows UUIDs match those in project frontmatter

---

## Test Journey 2: Multiple Projects and Focus

### Test 2.1: Set Domain Focus

**Say to Claude:**

> "Set my domain focus to 'work'"

**Expected:**
- Claude calls `plorp_set_focused_domain`
- Confirms focus set to work
- MCP focus file created at `~/.config/plorp/mcp_focus.txt`

**Verify focus persists:**

> "What's my current domain focus?"

**Expected:**
- Claude calls `plorp_get_focused_domain`
- Returns "work"

---

### Test 2.2: Create Multiple Work Projects

**Say to Claude:**

> "Create these work projects for me:
> 1. 'blog-launch' in marketing workstream, state should be 'planning'
> 2. 'api-v2' in engineering workstream, description 'Build REST API version 2'
> 3. 'quarterly-review' directly under work domain (no workstream)"

**Expected:**
- Claude creates 3 projects
- Shows full paths:
  - `work.marketing.blog-launch` (state: planning)
  - `work.engineering.api-v2` (state: active)
  - `work.quarterly-review` (state: active)

---

### Test 2.3: List Projects with Filters

**Say to Claude:**

> "List all my work projects"

**Expected:**
- Claude calls `plorp_list_projects` with domain filter
- Shows 4 projects (website-redesign, blog-launch, api-v2, quarterly-review)
- Groups projects by workstream

**Then ask:**

> "Show me only the marketing projects"

**Expected:**
- Lists 2 projects: website-redesign and blog-launch

**Then ask:**

> "Show me only active projects"

**Expected:**
- Lists 3 projects (excludes blog-launch which is in planning state)

---

## Test Journey 3: Personal Project

### Test 3.1: Switch Focus and Create Project

**Say to Claude:**

> "Switch my focus to 'home' and create a project called 'kitchen-remodel' in the house workstream. It's for renovating my kitchen."

**Expected:**
- Claude calls `plorp_set_focused_domain` with "home"
- Calls `plorp_create_project`
- Creates `home.house.kitchen-remodel`
- Confirms focus changed and project created

---

### Test 3.2: Add Tasks to Home Project

**Say to Claude:**

> "Add these tasks to the kitchen-remodel project:
> - Get contractor quotes (high priority, due Friday)
> - Choose countertop material (medium priority)
> - Order appliances (due Oct 20)"

**Expected:**
- 3 tasks created in project
- Each linked to `home.house.kitchen-remodel`
- Tasks visible in TaskWarrior

---

## Test Journey 4: Cross-Domain Queries

### Test 4.1: List All Projects

**Say to Claude:**

> "Show me all my projects across all domains"

**Expected:**
- Claude calls `plorp_list_projects` with no filter
- Returns 5 projects total:
  - 4 work projects
  - 1 home project
- Grouped by domain → workstream → project

---

### Test 4.2: Query Tasks by Domain

**Say to Claude:**

> "Show me all tasks in my work domain"

**Expected:**
- Claude calls `plorp_list_tasks_by_domain` with domain="work"
- Lists 3 tasks from website-redesign project
- Shows project path for each task

**Then ask:**

> "Show me all my home domain tasks"

**Expected:**
- Lists 3 tasks from kitchen-remodel project

---

## Test Journey 5: Project Management

### Test 5.1: Get Project Details

**Say to Claude:**

> "Give me detailed information about the website-redesign project"

**Expected:**
- Claude calls `plorp_get_project_info`
- Shows all metadata: domain, workstream, state, created_at, description
- Lists task UUIDs
- Shows task count

---

### Test 5.2: Update Project State

**Say to Claude:**

> "The blog-launch project is now active, please update its state"

**Expected:**
- Claude calls `plorp_update_project_state`
- Updates state from "planning" to "active"
- Confirms update in frontmatter

**Then:**

> "Mark the quarterly-review project as completed"

**Expected:**
- Updates state to "completed"
- Shows confirmation

---

### Test 5.3: Block a Project

**Say to Claude:**

> "The api-v2 project is blocked waiting for design approval"

**Expected:**
- Claude calls `plorp_update_project_state` with state="blocked"
- Updates project state
- Confirms blocked status

---

## Test Journey 6: Error Handling

### Test 6.1: Invalid Domain

**Say to Claude:**

> "Create a project called 'test' in the 'invalid-domain' domain"

**Expected:**
- Claude calls `plorp_create_project`
- MCP tool returns error: "Invalid domain: invalid-domain"
- Claude reports error to user

---

### Test 6.2: Duplicate Project

**Say to Claude:**

> "Create a project called 'website-redesign' in work.marketing"

**Expected:**
- Error: Project already exists
- Claude explains project already exists at that path

---

### Test 6.3: Task for Nonexistent Project

**Say to Claude:**

> "Add a task 'Do something' to project 'work.nonexistent.project'"

**Expected:**
- Error: Project not found
- Claude explains the project doesn't exist

---

## Test Journey 7: Orphaned Tasks

### Test 7.1: Create Orphaned Task in TaskWarrior

**Use CLI to create orphaned task:**
```bash
task add "Orphaned task" project:work.missing.project
```

### Test 7.2: Query Orphaned Tasks

**Say to Claude:**

> "Show me any orphaned tasks (tasks with project field but no project note)"

**Expected:**
- Claude calls `plorp_list_orphaned_tasks`
- Lists the orphaned task
- Warns that project file doesn't exist

---

## Test Journey 8: Integration with Existing Features

### Test 8.1: Create Task with Project from Daily Note

**Say to Claude:**

> "Create a task 'Review PR #123' in the website-redesign project, due tomorrow, high priority"

**Expected:**
- Task created in TaskWarrior
- Linked to project via annotation
- UUID added to project frontmatter
- Task shows up in project task list

---

### Test 8.2: View Project File in Obsidian

**In Obsidian:**
1. Navigate to `/Users/jsd/vault/projects/`
2. Open `work.marketing.website-redesign.md`

**Verify:**
- ✅ YAML frontmatter is properly formatted
- ✅ All fields present (domain, workstream, project_name, full_path, state, etc.)
- ✅ `task_uuids` array contains task UUIDs
- ✅ Tags show in Obsidian tag pane
- ✅ Note body shows description

---

## Test Journey 9: Cleanup

### Test 9.1: Delete Completed Project

**Say to Claude:**

> "Delete the quarterly-review project since it's completed"

**Expected:**
- Claude calls `plorp_delete_project`
- Confirms deletion
- File removed from vault

**Verify:**

> "List all work projects"

**Expected:**
- quarterly-review not in list
- 3 projects remain

---

### Test 9.2: Final Inventory

**Say to Claude:**

> "Give me a summary of all my projects across all domains, grouped by workstream"

**Expected:**
- **Work domain:**
  - marketing: website-redesign (active), blog-launch (active)
  - engineering: api-v2 (blocked)
- **Home domain:**
  - house: kitchen-remodel (active)
- **Total:** 4 projects, ~6-9 tasks

---

## Success Criteria Checklist

After completing all test journeys, verify:

- [ ] MCP tools are accessible from Claude Desktop
- [ ] Can create projects in different domains (work/home/personal)
- [ ] Can create projects with and without workstreams
- [ ] Tasks are created with correct TaskWarrior project field
- [ ] Bidirectional linking works (task UUIDs in frontmatter, annotations in TaskWarrior)
- [ ] Domain focus persists across requests
- [ ] Can filter projects by domain, workstream, state
- [ ] Can filter tasks by domain, workstream
- [ ] Can update project states (active/planning/completed/blocked/archived)
- [ ] Error handling is graceful (invalid domain, duplicate projects, etc.)
- [ ] Orphaned task detection works
- [ ] Project deletion removes file from vault
- [ ] Files in vault are properly formatted with YAML frontmatter
- [ ] Integration with Obsidian works (can view/edit project notes)

---

## Troubleshooting

### Issue: MCP tools not available

**Check MCP server configuration:**
```bash
# Verify MCP server can start
plorp-mcp --version

# Check Claude Desktop config
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Expected in config:**
```json
{
  "mcpServers": {
    "plorp": {
      "command": "/path/to/plorp-mcp",
      "args": []
    }
  }
}
```

### Issue: "Vault not found" error

**Check vault path:**
```bash
cat ~/.config/plorp/config.yaml
ls -la /Users/jsd/vault/
```

Ensure `vault_path` points to correct location.

### Issue: Tasks not showing in project

**Verify bidirectional linking:**
```bash
# Check task annotation
task <uuid> info | grep annotation

# Check project frontmatter
cat /Users/jsd/vault/projects/<project-path>.md | grep task_uuids
```

### Issue: Focus not persisting

**Check focus file:**
```bash
cat ~/.config/plorp/mcp_focus.txt
```

If missing, focus will default to "home".

---

## Next Steps After Testing

1. ✅ Mark Sprint 8 as tested via MCP
2. 📝 Document any UX issues or suggestions
3. 🐛 Report any bugs found
4. 💬 Discuss Sprint 9 scope (validation workflows, cleanup commands)
5. 📊 Consider creating Obsidian Bases views for projects

---

**Test Date:** __________
**Tester:** __________
**Claude Desktop Version:** __________
**Result:** ☐ Pass  ☐ Fail (notes: _________________________)

---

## Example Natural Language Queries

Here are additional queries you can try with Claude:

**Project Creation:**
- "Create a personal project for planning my vacation to Japan"
- "Start a new engineering project for database migration"

**Task Management:**
- "What tasks do I have in the marketing workstream?"
- "Show me all high-priority tasks across all projects"
- "Add a task to review the API documentation in the api-v2 project"

**Project Queries:**
- "Which projects are currently blocked?"
- "What's in my home domain?"
- "List all completed projects"

**State Management:**
- "Archive the old website project"
- "Move blog-launch from planning to active"
- "Block the api-v2 project until we get design approval"

**Focus Management:**
- "What domain am I focused on?"
- "Switch to personal focus"
- "Set my focus back to work"

Try these variations to test Claude's natural language understanding and the robustness of the MCP integration!
