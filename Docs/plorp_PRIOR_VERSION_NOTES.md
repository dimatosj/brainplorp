# plorp - Prior Version Notes

**Purpose:** Reference documentation for features from a prior iteration that were intentionally not carried forward into the current implementation.

---

## Context

This is plorp V1 - a fresh start. These notes capture what existed in a previous system to inform future decisions if needed.

---

## Features Not Implemented in Current Version

### Removed Features

❌ **Printout codes** (m1, p1, etc.)
❌ **Domain switching** (personal/home/work)
❌ **VA queue**
❌ **Snapshots**
❌ **Journal table**
❌ **Custom projects table**
❌ **Custom recurring_tasks table**
❌ **routine_instances table**
❌ **Streak tracking**
❌ **State management**
❌ **printout_code system**
❌ **SQLite database** (`plorp_claude.db` or similar)

### Rationale for Not Including

1. **TaskWarrior already does it** - Tasks, recurring tasks, projects
2. **Obsidian already does it** - Notes, daily notes
3. **Adds complexity** - Codes, state management, sync logic
4. **Current version focuses on workflows** - Not reinventing task management

### Core Workflows Preserved

✅ **Inbox workflow** (email → process → action)
✅ **Daily ritual** (start, work, review)
✅ **Notes system** (via Obsidian)
✅ **Task-note linking**
✅ **Project tracking** (via TaskWarrior + Obsidian)
✅ **Recurring tasks** (via TaskWarrior)

---

## Design Decisions from Prior Version

### 1. Codes (m1, p1, etc.) - Not Implemented

**Previous approach:** Printout codes for quick completion

**Current decision:** Don't use codes

**Rationale:**
- Adds complexity (code assignment, collision detection)
- UUIDs are stable identifiers
- Daily note checkboxes are simpler interface
- Can use short UUIDs if needed: `task abc done`

### 2. Separate Database - Not Implemented

**Previous approach:** Custom SQLite database (`plorp_claude.db` or similar)

**Current decision:** No plorp database

**Rationale:**
- TaskWarrior already has SQLite database
- Obsidian stores notes in markdown
- plorp is stateless orchestration layer
- Eliminates sync/consistency issues

### 3. Domain Switching - Not Implemented

**Previous approach:** Domain switching (personal/home vs work)

**Current decision:** Not implemented initially, use TaskWarrior contexts if needed later

**Rationale:**
- TaskWarrior contexts provide this functionality
- Current version focuses on core workflows
- Can add later: `task context personal`

### 4. Streak Tracking - Not Implemented

**Previous approach:** Track streaks for recurring tasks

**Current decision:** No streak tracking

**Rationale:**
- TaskWarrior recurring tasks work differently than previous system's routines
- Can calculate streaks from TaskWarrior history later if needed
- Focus current implementation on core workflows

---

**Document Version:** 1.0
**Last Updated:** October 6, 2025
**Status:** Reference only - not for implementation
