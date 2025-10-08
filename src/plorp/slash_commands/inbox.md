Use plorp MCP tools to help me process my inbox.

Steps:
1. Call `plorp_get_inbox_items` to see unprocessed inbox items
2. For each item, ask me what I want to do:
   - Create a task (use `plorp_create_task_from_inbox`)
   - Create a note (use `plorp_create_note_from_inbox`)
   - Create both task and note linked together (use `plorp_create_both_from_inbox`)
   - Discard it (use `plorp_discard_inbox_item`)
   - Skip it for now
3. When creating tasks, ask me for details like due date, priority, and project
4. When creating notes, ask me for title and content
5. Show me a summary when done

Help me efficiently process my inbox!
