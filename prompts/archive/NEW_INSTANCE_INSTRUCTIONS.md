# Instructions for New Claude Instance

## Your Task
You need to understand the PLORP codebase. Follow these steps IN ORDER.

  Required Reading (in order):

  1. Architecture Foundation

  File: /Users/jsd/Documents/plorp/Docs/MCP_ARCHITECTURE_GUIDE.md
  - Read sections on "MCP Servers vs Agents" and "Stochastic vs Deterministic"
  - Focus on "Recommended Architecture for plorp" section
  - Understand: Core functions return TypedDict, MCP/CLI are thin wrappers

  2. Sprint 7 Implementation Spec

  File: /Users/jsd/Documents/plorp/Docs/sprints/SPRINT_7_SPEC.md
  - Complete spec for your task
  - Note dependencies: requires Sprint 6 Phase 3 (daily note operations)
  - All Q&A questions already resolved
  - Status: READY FOR IMPLEMENTATION

  3. Sprint 6 Reference (for patterns only)

  File: /Users/jsd/Documents/plorp/Docs/sprints/SPRINT_6_SPEC.md
  - Read "Architecture Overview" section (lines 31-80)
  - Read "Core Function Patterns" (lines 200-300)
  - Read "TypedDict Definitions" section
  - Purpose: Understand architectural patterns you must follow
  - Skip: Implementation phases (that's Sprint 6 work, not yours)

  ---
  Required Code Review:

  Existing Core Modules (reference implementations)

  Read these to understand established patterns:

  1. /Users/jsd/Documents/plorp/src/plorp/core/daily.py
    - Example of core function structure
    - TypedDict return patterns
    - Exception handling approach
  2. /Users/jsd/Documents/plorp/src/plorp/integrations/taskwarrior.py
    - Task creation functions you'll call
    - UUID handling patterns
    - Lines 1-150 most relevant
  3. /Users/jsd/Documents/plorp/src/plorp/integrations/obsidian.py
    - Daily note parsing functions
    - Markdown section manipulation
    - Lines 1-200 most relevant
  4. /Users/jsd/Documents/plorp/src/plorp/parsers/dates.py
    - Existing date parsing utilities (if any)
    - You'll extend this or create similar patterns

  Test Patterns

  5. /Users/jsd/Documents/plorp/tests/test_cli.py
    - See how core functions are mocked
    - Test structure expectations
    - Lines 30-150 show typical patterns

  ---
  DO NOT READ (will cause confusion):

  ❌ /Users/jsd/Documents/plorp/Docs/sprints/SPRINT_[0-5]_SPEC.md - Old v1.0
  specs, different architecture
  ❌ /Users/jsd/Documents/plorp/src/plorp/workflows/ - Removed in v1.1, don't
  reference
  ❌ /Users/jsd/Documents/plorp/Docs/MANUAL_TEST_USER_JOURNEY.md - v1.0
  workflows, outdated

  