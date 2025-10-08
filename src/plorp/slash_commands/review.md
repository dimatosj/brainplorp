Use plorp MCP tools to help me review my day interactively.

Steps:
1. Call `plorp_get_review_tasks` to see what tasks remain uncompleted from today
2. For each uncompleted task, ask me what I want to do:
   - Mark it complete
   - Defer it to a new date
   - Change its priority
   - Delete it
   - Skip it
3. After reviewing tasks, ask me for end-of-day reflections:
   - What went well?
   - What could improve?
   - Notes for tomorrow?
4. Call `plorp_add_review_notes` to save my reflections

Be supportive and help me reflect on my day!
