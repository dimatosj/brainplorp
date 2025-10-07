Use plorp MCP tools to process informal tasks in my daily note. Two-step workflow to convert informal checkboxes into TaskWarrior tasks.

Steps:
1. Call `plorp_process_daily_note` to start the workflow
2. If Step 1 (proposals):
   - Show me the proposals generated from my informal tasks
   - Explain the natural language parsing (dates, priorities detected)
   - Tell me to review the ## TBD Processing section in my daily note
   - Remind me to mark [Y] to approve or [N] to reject each proposal
   - Suggest running /process again when I'm done reviewing
3. If Step 2 (task creation):
   - Show me which tasks were created in TaskWarrior
   - Show me which tasks were rejected and kept in original locations
   - If any NEEDS_REVIEW items remain, explain what I need to fix
   - Confirm the note has been reorganized

Be clear about the two-step process and help me understand what's happening at each stage!
