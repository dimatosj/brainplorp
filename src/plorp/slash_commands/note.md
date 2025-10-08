Help me create a note in Obsidian using plorp MCP tools.

Steps:
1. Ask me for note details:
   - Title (required)
   - Content (optional - can be added later in Obsidian)
   - Note type (optional: general, meeting, project, etc. - defaults to general)
2. Ask if I want to link this note to an existing task
3. If linking to a task:
   - Ask for the task UUID
   - Use `plorp_create_note_with_task` to create the note with bidirectional link
4. If no task link:
   - Use `plorp_create_note` to create a standalone note
5. Provide the file path so I can open it in Obsidian

Be helpful in creating well-structured notes!
