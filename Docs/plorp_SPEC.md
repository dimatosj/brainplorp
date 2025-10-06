# plorp Specification

**Date:** October 6, 2025
**Version:** 1.0.0
**Purpose:** Workflow automation layer on TaskWarrior + Obsidian

---

## Table of Contents

1. [Overview](#overview)
2. [Core Philosophy](#core-philosophy)
3. [Architecture](#architecture)
4. [Three Core Workflows](#three-core-workflows)
5. [Data Storage](#data-storage)
6. [Integration Points](#integration-points)
7. [Commands Reference](#commands-reference)
8. [Design Decisions](#design-decisions)
9. [Success Criteria](#success-criteria)

---

## Overview

### Success Criteria

### plorp is successful if:

1. **Daily workflow works:**
   - `plorp start` generates daily note with tasks
   - User works in Obsidian (checks boxes, adds notes)
   - `plorp review` syncs back to TaskWarrior

2. **Inbox workflow works:**
   - Emails captured to inbox file automatically
   - `plorp inbox process` converts to tasks/notes
   - No items lost in process

3. **Integration works:**
   - Tasks created via plorp show in TaskWarrior
   - Notes link to tasks bidirectionally
   - TaskWarrior native commands still work

4. **Less complexity than V1:**
   - No custom database
   - Fewer commands
   - Clearer architecture

5. **Extensible:**
   - Easy to add new workflows
   - TaskWarrior ecosystem accessible
   - Obsidian plugins compatible

---

## Next Steps

1. **Review this specification** - Is this the right design?
2. **Create architecture document** - Technical implementation details
3. **Create implementation plan** - Phase-by-phase build-out
4. **Set up project** - Fresh repository, dependencies, structure
5. **Build Phase 1** - Core daily workflow

---

**Document Version:** 1.0
**Last Updated:** October 6, 2025
**Status:** Draft for review
