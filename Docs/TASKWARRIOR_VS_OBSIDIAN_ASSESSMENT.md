# TaskWarrior vs Obsidian Bases: Strategic Assessment

**Date:** 2025-10-08
**Context:** Evaluating whether brainplorp should continue using TaskWarrior as task backend, or pivot to Obsidian Bases/plugins for task management
**Decision Impact:** Affects Sprint 9+ architecture and plorp's core value proposition

---

## ✅ DECISION RECORD

**Decision Made:** 2025-10-08
**Decision Maker:** User (Product Owner)
**Decision:** **Recommendation 1: Keep TaskWarrior (Primary)**

**Summary:**
After comprehensive analysis of TaskWarrior vs Obsidian Bases capabilities, the decision is to **continue using TaskWarrior as plorp's task computation engine** while enhancing Obsidian integration through Sprint 9's general note management features.

**Rationale:**
- TaskWarrior provides sophisticated features (urgency algorithm, dependency tracking, recurring tasks) that would require 3-4 sprints to replicate in Obsidian
- Obsidian Bases cannot natively track inline tasks (checkboxes) - it queries note-level properties only
- The two systems are complementary: TaskWarrior = computation engine, Obsidian = context layer
- Sprint 9's note management enhances the TaskWarrior bridge by providing richer context around tasks

**Status:** ✅ APPROVED - Proceed with Sprint 9 as planned (general note management)
**Next Review:** Sprint 11+ (when Obsidian Bases matures further, or if user feedback indicates need for backend flexibility)

---

## Executive Summary

**Recommendation: Keep TaskWarrior as the task computation engine, enhance integration with Obsidian.**

TaskWarrior provides sophisticated task management features (urgency calculation, dependency tracking, recurring tasks) that would be difficult and time-consuming to replicate in Obsidian Bases. Obsidian Bases excels at note-level organization and visualization, but cannot natively track inline tasks (checkboxes). The two systems are complementary, not competing.

**Sprint 9's note management layer makes the TaskWarrior bridge MORE valuable**, not less - by enabling brainplorp to read project notes, meeting notes, and context around tasks, while TaskWarrior handles the computational heavy lifting.

---

## Research Findings

### TaskWarrior Strengths

#### 1. Sophisticated Urgency Algorithm
TaskWarrior calculates urgency using a polynomial expression with 15+ configurable coefficients:

**Default Coefficients:**
- `urgency.user.tag.next.coefficient: 15.0` - Tasks tagged +next
- `urgency.due.coefficient: 12.0` - Overdue/approaching due date
- `urgency.blocking.coefficient: 8.0` - Blocking other tasks
- `urgency.uda.priority.H.coefficient: 6.0` - High priority
- `urgency.scheduled.coefficient: 5.0` - Scheduled tasks
- `urgency.active.coefficient: 4.0` - Already started
- `urgency.age.coefficient: 2.0` - Older tasks
- `urgency.annotations.coefficient: 1.0` - Has notes
- `urgency.tags.coefficient: 1.0` - Has tags
- `urgency.project.coefficient: 1.0` - Assigned to project
- `urgency.waiting.coefficient: -3.0` - Waiting state
- `urgency.blocked.coefficient: -5.0` - Blocked by others

**User Customization:**
```bash
# Boost urgency for problem tasks
task config urgency.user.tag.problem.coefficient 4.5

# Reduce urgency for "later" items
task config urgency.user.tag.later.coefficient -6.0
```

**Why This Matters:**
- Automatically surfaces the "next best task" without user intervention
- Balances multiple factors (age, priority, due date, dependencies)
- Customizable per user's workflow
- **No equivalent in Obsidian ecosystem**

#### 2. Dependency Tracking
- Tasks can block other tasks
- Tasks can be blocked by dependencies
- Affects urgency calculation
- Built-in dependency resolution
- **Critical for complex project workflows**

#### 3. Recurring Task Logic
- Built-in support for recurring tasks
- Automatic task generation on completion
- Complex recurrence patterns (every 3rd Tuesday, etc.)
- **Mature and battle-tested since 2006**

#### 4. Powerful Filtering & Querying
- Complex filter syntax: `status:pending due.before:today +urgent -waiting project:work`
- Virtual tags (OVERDUE, DUETODAY, BLOCKED, etc.)
- JSON export for interop
- Scriptable and pipeable (Unix philosophy)

#### 5. Mature Ecosystem
- 18+ years of development
- Active community
- Mobile sync solutions (Inthe.AM, Taskwarrior Server)
- CLI-first design (scriptable, automatable)

---

### Obsidian Bases Strengths

#### 1. Visual Interface
- No code required (unlike Dataview queries)
- Drag-and-drop filtering
- In-line editing of properties
- Card view with cover images
- **More user-friendly than TaskWarrior CLI**

#### 2. Note-Level Organization
- Excellent for organizing project notes
- Query by frontmatter properties
- Dynamic dashboards
- Fast rendering (faster than Dataview)

#### 3. Contextual Richness
- Notes can include documentation, links, images
- Full markdown support
- Bi-directional linking
- Graph view integration

---

### Obsidian Bases Limitations for Tasks

#### 1. Cannot Track Inline Tasks
**Critical Limitation:** Bases can only query note-level properties (frontmatter), not inline checkboxes.

**Current Workarounds:**
- **Task-as-Note Approach**: Every task becomes a separate note (heavy overhead)
- **Property Aggregation**: Surface task counts to frontmatter (`completed: 5, total: 10, progress: 50%`)
- **Tasks Plugin**: Separate plugin for inline task tracking (not Bases-native)

**Quote from community:**
> "At the moment, Bases can only list notes that follow certain criteria. To be a complete replacement for Dataview it would be nice to also be able to create a Base on 'Tasks' as a base element."

#### 2. No Urgency Algorithm
- No built-in priority calculation
- No automatic task ordering
- User must manually sort/prioritize
- **Would require custom plugin or formula system**

#### 3. No Dependency Tracking
- No concept of blocking/blocked tasks
- No dependency resolution
- **Would need manual tracking via properties**

#### 4. Limited Recurrence Support
- No built-in recurring task logic
- Tasks plugin has basic recurrence, but less sophisticated than TaskWarrior
- **Complex patterns (every 3rd Tuesday) not supported**

---

### Obsidian Tasks Plugin (Alternative to Bases)

The Tasks plugin is a separate ecosystem:

**Strengths:**
- Can track inline checkboxes across vault
- Query language for filtering tasks
- Due dates, recurrence, done dates supported
- Custom visualizations possible

**Weaknesses vs TaskWarrior:**
- No urgency calculation algorithm
- Simpler recurrence patterns
- No dependency tracking
- No prioritization beyond manual sorting
- **Community plugin, not core Obsidian feature**

**Quote from user:**
> "One of the reasons I love managing tasks in Obsidian is because I can create custom visualizations that help motivate me and keep me moving forward."

---

## Comparison Matrix

| Feature | TaskWarrior | Obsidian Bases | Obsidian Tasks Plugin |
|---------|-------------|----------------|----------------------|
| **Urgency calculation** | ✅ Yes (15+ coefficients) | ❌ No | ❌ No |
| **Dependency tracking** | ✅ Yes (blocking/blocked) | ❌ No | ❌ No |
| **Recurring tasks** | ✅ Yes (complex patterns) | ❌ No | ⚠️ Basic patterns |
| **Inline task tracking** | ❌ No (checkbox ≠ TaskWarrior task) | ❌ No (note-level only) | ✅ Yes |
| **Visual interface** | ❌ CLI only | ✅ Yes (GUI) | ✅ Yes (in-note) |
| **Filtering/queries** | ✅ Yes (powerful syntax) | ✅ Yes (GUI-based) | ✅ Yes (query blocks) |
| **Mobile support** | ⚠️ Limited (Inthe.AM) | ✅ Yes (Obsidian Mobile) | ✅ Yes (Obsidian Mobile) |
| **Context/notes** | ⚠️ Annotations only | ✅ Rich markdown notes | ✅ Rich markdown notes |
| **Maturity** | ✅ 18+ years | ⚠️ Beta (2024+) | ⚠️ Community plugin |
| **Scriptability** | ✅ Yes (CLI, JSON export) | ⚠️ Limited (API) | ⚠️ Via Obsidian API |
| **Sync** | ✅ TaskServer, Inthe.AM | ✅ Obsidian Sync | ✅ Obsidian Sync |

---

## What brainplorp Brings to the Table

### Current Architecture (TaskWarrior + Obsidian)

**TaskWarrior handles:**
- Task storage and urgency calculation
- Due date tracking and overdue detection
- Priority and tag-based filtering
- Recurring task generation
- Dependency resolution

**Obsidian handles:**
- Daily notes (context for tasks)
- Inbox (email → task conversion)
- Project notes (documentation)
- Meeting notes (context)

**brainplorp bridges:**
- Syncs tasks → daily notes (with UUIDs)
- Creates tasks from informal checkboxes
- Links notes ↔ tasks bidirectionally
- Generates daily ritual from TaskWarrior queries

**Value proposition:**
> "I want TaskWarrior's power with Obsidian's context."

---

### Proposed Architecture (All-Obsidian)

**Obsidian Bases would handle:**
- Project notes (✅ already excellent)
- Task storage... somehow?
  - Option A: Task-as-note (every task = separate .md file) → **Heavy overhead**
  - Option B: Task counts in frontmatter (completed: 5, total: 10) → **Loses granularity**
  - Option C: Use Tasks plugin + Dataview queries → **Back to code-based queries**

**What we'd lose:**
- ❌ Urgency algorithm (would need to build from scratch)
- ❌ Dependency tracking (would need custom property system)
- ❌ Mature recurring task logic (would need to implement)
- ❌ TaskWarrior's 18 years of refinement

**What we'd gain:**
- ✅ Simpler architecture (one system instead of two)
- ✅ Better mobile experience (Obsidian Mobile)
- ✅ Visual task management (GUI instead of CLI)
- ✅ No external dependency (TaskWarrior not required)

**Development cost:**
- Reimplement urgency algorithm: ~20 hours
- Build dependency tracking: ~15 hours
- Implement recurring tasks: ~10 hours
- Testing and refinement: ~20 hours
- **Total: ~65 hours = 3-4 sprints**

**Risk:**
- Rebuilding TaskWarrior features will introduce bugs
- Community has already solved these problems (don't reinvent wheel)
- TaskWarrior has 18 years of edge case handling

---

## User Workflow Analysis

### Scenario 1: "What should I work on next?"

**With TaskWarrior:**
```bash
$ task next
ID  Pri  Due        Description
1   H    today      Fix critical bug (urgency: 18.5)
2   M    tomorrow   Review PR #123 (urgency: 12.3)
3   L    Fri        Update docs (urgency: 8.1)
```
- Urgency calculated automatically
- Balances priority, due date, age, tags, dependencies
- **Zero user effort**

**With Obsidian Bases (no urgency):**
- User must manually sort by priority
- User must check due dates
- User must remember what's blocking what
- **Requires manual cognitive load**

**Verdict:** TaskWarrior wins decisively for prioritization.

---

### Scenario 2: "Show me all work tasks due this week"

**With TaskWarrior:**
```bash
$ task project:work due:week
```

**With Obsidian Bases:**
- Filter by `project: work` and `due: <this week>`
- Visual table view
- Can edit in-line
- **More user-friendly interface**

**Verdict:** Obsidian Bases wins for visual filtering.

---

### Scenario 3: "I need context on this task - what notes are related?"

**Current brainplorp (TaskWarrior + Obsidian):**
```
Task: "Review API design"
Annotations: "Note: vault/projects/api-rewrite.md"
           → brainplorp reads note, shows full context
```

**Future brainplorp with Sprint 9 (enhanced):**
```
Task: "Review API design"
Project: work.engineering.api-rewrite
         → Claude: "Let me read that project note..."
         → plorp_read_note("projects/work.engineering.api-rewrite.md")
         → Full project context available
         → Claude: "Here's the API design doc, recent decisions, and 3 open questions..."
```

**Verdict:** Sprint 9 note management makes the bridge MORE powerful, not obsolete.

---

### Scenario 4: "Create a task from my meeting notes"

**Current plorp:**
```markdown
## Meeting Notes
- [ ] Follow up with Sarah on budget approval
```
→ `brainplorp process` converts to TaskWarrior task with UUID

**With Obsidian Tasks plugin only:**
```markdown
## Meeting Notes
- [ ] Follow up with Sarah on budget approval 📅 2025-10-15
```
→ Task exists in Obsidian, queryable via Tasks plugin
→ **No urgency calculation, no TaskWarrior backend**

**Verdict:** Current brainplorp approach provides more power (urgency, filtering) at cost of complexity.

---

## Strategic Recommendations

### Recommendation 1: Keep TaskWarrior (Primary)

**Rationale:**
1. **Don't reinvent the wheel** - TaskWarrior has 18 years of development solving hard problems (urgency, dependencies, recurrence)
2. **Complementary systems** - TaskWarrior = computation engine, Obsidian = context layer
3. **Sprint 9 enhances the bridge** - Note management makes the integration MORE valuable
4. **Low switching cost now** - Pivoting to all-Obsidian later is possible if needed

**Implementation:**
- Continue using TaskWarrior as task backend
- Enhance Obsidian integration (Sprint 9: general note management)
- Improve bidirectional linking (tasks ↔ notes)

---

### Recommendation 2: Make TaskWarrior Optional (Long-term)

**Rationale:**
- Some users may prefer Obsidian-only workflow
- Mobile-first users struggle with TaskWarrior
- Lighter-weight setup for casual users

**Implementation (Sprint 11+):**
- Create abstraction layer: `plorp.task_backend`
- Two backend implementations:
  - `TaskWarriorBackend` (default, full features)
  - `ObsidianTasksBackend` (simpler, no urgency/dependencies)
- User chooses in config:
  ```yaml
  task_backend: taskwarrior  # or obsidian_tasks
  ```

**Migration path:**
- Sprint 9-10: Enhance TaskWarrior integration (current plan)
- Sprint 11-12: Abstract task backend interface
- Sprint 13+: Implement Obsidian Tasks backend as alternative
- User can switch backends later if desired

---

### Recommendation 3: Leverage Obsidian Bases for Projects (Current Plan)

**Rationale:**
- Sprint 8 already uses Bases for project management
- Projects = note-level entities (perfect fit for Bases)
- Tasks = line-level entities (better fit for TaskWarrior)

**Keep the division:**
- **Obsidian Bases** → Projects, areas, documentation
- **TaskWarrior** → Individual tasks, urgency, filtering
- **plorp** → Bridge between the two

---

### Recommendation 4: Enhance Mobile Experience (Sprint 10+)

**Rationale:**
- TaskWarrior's CLI is desktop-centric
- Obsidian Mobile is excellent
- Users want mobile task management

**Implementation:**
- MCP tools work in Claude Mobile (when available)
- Obsidian Mobile can edit daily notes
- TaskWarrior sync via Inthe.AM or TaskServer
- Mobile-friendly task views via Bases dashboards

---

## Decision Matrix

### Should brainplorp pivot to all-Obsidian?

| Factor | Weight | TaskWarrior Score | All-Obsidian Score |
|--------|--------|-------------------|-------------------|
| Feature completeness | 25% | 9/10 | 5/10 |
| User experience | 20% | 6/10 | 8/10 |
| Mobile support | 15% | 4/10 | 9/10 |
| Development effort | 15% | 8/10 (already built) | 3/10 (rebuild needed) |
| Maintenance burden | 10% | 7/10 | 8/10 |
| Extensibility | 10% | 9/10 (CLI, JSON) | 7/10 (plugin API) |
| Community maturity | 5% | 10/10 (18 years) | 6/10 (beta) |

**Weighted Scores:**
- **TaskWarrior approach: 7.15/10**
- **All-Obsidian approach: 6.35/10**

**Conclusion:** TaskWarrior approach is stronger today. All-Obsidian may become competitive in 1-2 years as Bases matures.

---

## Sprint 9 Implications

### If Keeping TaskWarrior (Recommended):

**Sprint 9 Focus:**
- ✅ General note management (read/write any note)
- ✅ Enhanced task ↔ note linking
- ✅ Project context integration
- ✅ Meeting notes → tasks workflow
- ✅ "Read all SEO notes" → create tasks from insights

**Value Proposition:**
> "brainplorp gives you TaskWarrior's computational power + Obsidian's contextual richness, accessible via Claude."

**Architecture:**
```
User ↔ Claude Desktop ↔ brainplorp MCP
                          ↓
            ┌─────────────┴─────────────┐
            ↓                           ↓
      TaskWarrior                  Obsidian Vault
    (urgency, tasks)          (notes, projects, context)
```

---

### If Pivoting to All-Obsidian (Not Recommended):

**Sprint 9 would need:**
- ❌ Implement urgency algorithm (20 hours)
- ❌ Build dependency tracking (15 hours)
- ❌ Recurring task logic (10 hours)
- ❌ Migration plan for existing TaskWarrior users
- ❌ Regression testing all workflows

**Timeline:** 3-4 sprints instead of 1 sprint

**Risk:** Significant delay, potential for bugs

---

## Conclusion

**Strategic Direction: Keep TaskWarrior, enhance Obsidian integration.**

TaskWarrior and Obsidian solve different problems:
- **TaskWarrior** = Computational engine (urgency, filtering, dependencies)
- **Obsidian** = Context layer (notes, projects, documentation)
- **plorp** = Intelligent bridge (bidirectional sync, MCP interface)

Sprint 9's note management capabilities make this bridge **more powerful**, not less necessary. By enabling Claude to read project notes, meeting notes, and contextual documents, we're enhancing TaskWarrior's value (giving it more context) while preserving its computational strengths.

**The best of both worlds:** TaskWarrior's 18 years of task management refinement + Obsidian's rich note-taking + Claude's intelligence.

---

## Open Questions for User

1. **Do you agree with keeping TaskWarrior?** Or do you see value in an all-Obsidian approach?

2. **Mobile usage:** How important is mobile task management for your workflow?

3. **Urgency algorithm:** Do you actively use TaskWarrior's urgency calculation, or could you live without it?

4. **Future flexibility:** Would you want the option to switch backends later (TaskWarrior ↔ Obsidian Tasks)?

5. **Sprint 9 scope:** Given this analysis, should Sprint 9 focus on note management (enhancing TaskWarrior bridge) or pivot to reimplementing task management in Obsidian?

---

## Recommendation to PM

**Proceed with Sprint 9 as planned:** General note management via MCP.

This enhances plorp's value proposition without requiring a risky architectural pivot. TaskWarrior remains the task computation engine, Obsidian provides context, and brainplorp bridges them intelligently.

**Defer all-Obsidian consideration to Sprint 11+** when:
- Obsidian Bases has matured further (out of beta)
- Task management capabilities are clearer
- User feedback indicates need for simpler setup

**Monitor:** Obsidian Bases development, community sentiment, user pain points with TaskWarrior CLI.
