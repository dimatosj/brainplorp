You are closing your PM/Architect session. Ensure clean handoff to next PM instance.

## Your Task

Perform these checks in order:

### 1. Run /update-handoff (if not already done)

If you haven't run /update-handoff in the last 30 minutes, run it now to capture recent work.

### 2. Verify HANDOFF.md Completeness

Check `/Users/jsd/Documents/plorp/Docs/PM_HANDOFF.md`:

- [ ] SESSION HISTORY has entry for THIS session
- [ ] CURRENT STATE section reflects latest reality
- [ ] Sprint statuses are COMPLETE or INCOMPLETE (no ambiguous states)
- [ ] Lead engineer handoff notes captured (if any sprint completed)
- [ ] Next PM Instance instructions are clear
- [ ] No contradictions between CURRENT STATE and last SESSION HISTORY entry

### 3. Verify Sprint Specs Match Reality

Run these commands and check results:

```bash
# Check sprint spec statuses
grep "^**Status:" /Users/jsd/Documents/plorp/Docs/sprints/SPRINT_*.md

# Check MCP tools count
grep -c "name=\"plorp_" /Users/jsd/Documents/plorp/src/plorp/mcp/server.py

# Check core modules exist
ls /Users/jsd/Documents/plorp/src/plorp/core/
```

Compare results to HANDOFF.md SPRINT COMPLETION REGISTRY. Do they match?

### 4. Check SPRINT COMPLETION REGISTRY

For each sprint in registry:
- Does completion date match when work finished?
- Does test count match actual tests passing?
- Are key deliverables listed accurately?

### 5. Flag Missing Information

If ANY of these are unclear or missing:
- What work is blocked
- What next PM instance should do first
- Any sprint status ambiguity
- Any lead engineer work in progress but not documented

**Report these explicitly to user before ending.**

### 6. Final Verification Checklist

Run through this mentally:
- [ ] Can next PM instance load HANDOFF.md and understand current state?
- [ ] Are there any conflicting status reports between docs?
- [ ] Did I copy (not just reference) all handoff notes?
- [ ] Is CURRENT STATE truly current?
- [ ] Did I update SPRINT COMPLETION REGISTRY if any sprints completed?

### 7. Summary for User

Tell user:

```
Session close checklist complete:

✅ HANDOFF.md updated with session [N] notes
✅ Sprint statuses verified: [list statuses from registry]
✅ Codebase matches docs: [confirm or note discrepancies]
✅ Next PM instance instructions: [summarize what's in CURRENT STATE]

[Flag any issues found]

Ready to end session.
```

## If Problems Found

**DO NOT end session until:**
- All contradictions resolved
- Missing information added to HANDOFF.md
- Sprint statuses corrected
- User acknowledges any blocking issues

## Important

This is your last chance to ensure clean context handoff. Take 5 minutes to be thorough - it saves hours for next PM instance.
