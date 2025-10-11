# Sprint 9 Manual Testing Guide
## General Note Management & Vault Interface

**Version:** 1.5.0
**Sprint:** 9
**Testing Date:** _____________
**Tester:** _____________

---

## Prerequisites

- brainplorp v1.5.0 installed
- Obsidian vault configured at `~/.config/plorp/config.yaml`
- Test vault with sample notes in multiple folders
- Claude Desktop with brainplorp MCP server configured

---

## Test Environment Setup

```bash
# Verify version
brainplorp --version  # Should show 1.5.0

# Check MCP server is configured
cat ~/.config/claude/config.json | grep plorp-mcp

# Verify test vault exists
ls ~/vault/daily ~/vault/inbox ~/vault/notes ~/vault/projects
```

---

## Phase 1: Note I/O Operations (8 MCP Tools)

### Test 1.1: Read Note (Full Mode)
**Tool:** `plorp_read_note`

**Steps:**
1. Open Claude Desktop
2. Ask: "Read the full content of my daily note from yesterday"
3. Verify it uses `plorp_read_note` with mode="full"

**Expected Results:**
- ✅ Full note content returned
- ✅ Frontmatter included
- ✅ All sections visible

**Pass/Fail:** ______

---

### Test 1.2: Read Note (Preview Mode)
**Tool:** `plorp_read_note`

**Steps:**
1. Ask: "Give me a preview of my latest project note"
2. Verify mode="preview" is used

**Expected Results:**
- ✅ First ~500 words returned
- ✅ Truncation message if note is longer
- ✅ No context warning for short notes

**Pass/Fail:** ______

---

### Test 1.3: Read Note (Metadata Mode)
**Tool:** `plorp_read_note`

**Steps:**
1. Ask: "What's in the frontmatter of my project note?"
2. Verify mode="metadata" is used

**Expected Results:**
- ✅ Only YAML frontmatter returned
- ✅ No body content
- ✅ Properly parsed metadata fields

**Pass/Fail:** ______

---

### Test 1.4: Read Note (Structure Mode)
**Tool:** `plorp_read_note`

**Steps:**
1. Ask: "What's the structure of my project note?"
2. Verify mode="structure" is used

**Expected Results:**
- ✅ List of headers returned (##, ###, etc.)
- ✅ Header hierarchy preserved
- ✅ No body content

**Pass/Fail:** ______

---

### Test 1.5: Read Folder
**Tool:** `plorp_read_folder`

**Steps:**
1. Ask: "List all notes in my projects folder"
2. Verify folder scan works

**Expected Results:**
- ✅ All .md files in folder listed
- ✅ File paths shown
- ✅ Metadata previews included
- ✅ No errors for missing frontmatter

**Pass/Fail:** ______

---

### Test 1.6: Read Folder with Filters
**Tool:** `plorp_read_folder`

**Steps:**
1. Ask: "Show me all notes in projects folder with tag 'active'"
2. Verify filtering works

**Expected Results:**
- ✅ Only notes with tag 'active' returned
- ✅ Other notes excluded
- ✅ Correct count

**Pass/Fail:** ______

---

### Test 1.7: Append to Note
**Tool:** `plorp_append_to_note`

**Steps:**
1. Ask: "Append a bullet point 'Test entry from Sprint 9' to my daily note"
2. Verify append operation
3. Open note in Obsidian to confirm

**Expected Results:**
- ✅ Content appended to end of note
- ✅ No existing content modified
- ✅ Proper newline spacing

**Pass/Fail:** ______

---

### Test 1.8: Update Note Section
**Tool:** `plorp_update_note_section`

**Steps:**
1. Create note with section `## Test Section`
2. Ask: "Replace the 'Test Section' with 'Updated content'"
3. Verify section replacement

**Expected Results:**
- ✅ Section content replaced
- ✅ Other sections unchanged
- ✅ Headers preserved

**Pass/Fail:** ______

---

### Test 1.9: Search Notes by Tag
**Tool:** `plorp_search_notes_by_tag`

**Steps:**
1. Create notes with tags #work, #personal
2. Ask: "Find all notes tagged #work"

**Expected Results:**
- ✅ All notes with #work returned
- ✅ Inline tags detected (#work in body)
- ✅ Frontmatter tags detected (tags: [work])

**Pass/Fail:** ______

---

### Test 1.10: Search Notes by Field
**Tool:** `plorp_search_notes_by_field`

**Steps:**
1. Ask: "Find notes where status is 'active'"
2. Verify metadata search

**Expected Results:**
- ✅ Notes with matching metadata returned
- ✅ List fields searched correctly (value in list)
- ✅ Scalar fields exact match

**Pass/Fail:** ______

---

### Test 1.11: Create Note in Folder
**Tool:** `plorp_create_note_in_folder`

**Steps:**
1. Ask: "Create a new note called 'Sprint 9 Test' in the notes folder"
2. Verify file creation

**Expected Results:**
- ✅ File created in correct folder
- ✅ Frontmatter added with date
- ✅ Title as H1 header

**Pass/Fail:** ______

---

### Test 1.12: List Vault Folders
**Tool:** `plorp_list_vault_folders`

**Steps:**
1. Ask: "What folders are in my vault?"

**Expected Results:**
- ✅ All folders listed
- ✅ File counts shown
- ✅ Recursive scan works

**Pass/Fail:** ______

---

## Phase 2: Pattern Matching Operations (4 MCP Tools)

### Test 2.1: Extract Headers
**Tool:** `plorp_extract_headers`

**Steps:**
1. Ask: "Extract all headers from my project note"

**Expected Results:**
- ✅ All headers returned (##, ###, ####)
- ✅ Hierarchy preserved
- ✅ Level numbers correct (2, 3, 4)

**Pass/Fail:** ______

---

### Test 2.2: Get Section Content
**Tool:** `plorp_get_section_content`

**Steps:**
1. Ask: "Get the content under the 'Next Steps' section in my project note"

**Expected Results:**
- ✅ Section content returned
- ✅ Subsections included
- ✅ Stops at next same-level header

**Pass/Fail:** ______

---

### Test 2.3: Detect Projects in Note
**Tool:** `plorp_detect_projects_in_note`

**Steps:**
1. Create note with headers "## API Rewrite" and "## database-migration"
2. Ask: "What projects are mentioned in this note?"

**Expected Results:**
- ✅ Title Case headers detected as projects
- ✅ kebab-case headers detected as projects
- ✅ Common sections excluded (Notes, TODO, etc.)

**Pass/Fail:** ______

---

### Test 2.4: Extract Bullets
**Tool:** `plorp_extract_bullets`

**Steps:**
1. Ask: "Extract all bullet points from my daily note"

**Expected Results:**
- ✅ All bullets returned (-, *, +)
- ✅ Nested bullets preserved
- ✅ Checkboxes included (- [ ], - [x])

**Pass/Fail:** ______

---

## Phase 3: Permission & Security Tests

### Test 3.1: Allowed Folders
**Steps:**
1. Ask: "Read a note from the daily folder" (should work)
2. Ask: "Read a note from the _bases folder" (should fail)

**Expected Results:**
- ✅ Allowed folders accessible (daily, inbox, projects, notes, Docs)
- ✅ Disallowed folders rejected (_bases, .obsidian)
- ✅ Clear error message for permission denied

**Pass/Fail:** ______

---

### Test 3.2: Context Warnings
**Steps:**
1. Create a note >10,000 words
2. Ask to read it in full mode

**Expected Results:**
- ✅ Warning displayed about large file
- ✅ Token estimate shown (~13k tokens)
- ✅ Operation still completes

**Pass/Fail:** ______

---

### Test 3.3: UTF-8 Only
**Steps:**
1. Create note with non-UTF-8 encoding (if possible)
2. Try to read it

**Expected Results:**
- ✅ Error message about encoding
- ✅ File skipped, no crash

**Pass/Fail:** ______

---

## Phase 4: Error Handling Tests

### Test 4.1: Missing File
**Steps:**
1. Ask: "Read the file 'nonexistent-note.md'"

**Expected Results:**
- ✅ Clear "file not found" error
- ✅ No crash
- ✅ Helpful suggestion (check path)

**Pass/Fail:** ______

---

### Test 4.2: Missing Section
**Steps:**
1. Ask: "Update the 'Nonexistent Section' in my daily note"

**Expected Results:**
- ✅ HeaderNotFoundError raised
- ✅ Clear message about section not found
- ✅ List of available sections suggested

**Pass/Fail:** ______

---

### Test 4.3: Malformed YAML
**Steps:**
1. Create note with broken YAML frontmatter
2. Try to read it with mode="metadata"

**Expected Results:**
- ✅ Graceful failure (empty metadata returned)
- ✅ Warning about malformed YAML
- ✅ File not skipped entirely

**Pass/Fail:** ______

---

### Test 4.4: Empty Note
**Steps:**
1. Create empty .md file
2. Try to read it

**Expected Results:**
- ✅ Returns empty content
- ✅ No crash
- ✅ Metadata shows as empty dict

**Pass/Fail:** ______

---

## Phase 5: Integration Tests

### Test 5.1: Multi-Tool Workflow
**Steps:**
1. Ask: "List my project notes, then read the most recent one"
2. Verify both tools used sequentially

**Expected Results:**
- ✅ plorp_read_folder called first
- ✅ plorp_read_note called second
- ✅ Results combined coherently

**Pass/Fail:** ______

---

### Test 5.2: Create + Update Workflow
**Steps:**
1. Ask: "Create a note called 'Workflow Test', then add a section 'Next Steps'"

**Expected Results:**
- ✅ Note created with plorp_create_note_in_folder
- ✅ Section added with plorp_append_to_note
- ✅ Final note has both parts

**Pass/Fail:** ______

---

### Test 5.3: Search + Read Workflow
**Steps:**
1. Ask: "Find notes tagged #urgent, then read the first one"

**Expected Results:**
- ✅ Search executed first
- ✅ Read executed on result
- ✅ Correct file read

**Pass/Fail:** ______

---

## Test Summary

**Total Tests:** 31
**Passed:** ______
**Failed:** ______
**Skipped:** ______

---

## Issues Found

| Test # | Issue Description | Severity | Notes |
|--------|-------------------|----------|-------|
|        |                   |          |       |
|        |                   |          |       |
|        |                   |          |       |

---

## Sign-Off

**Tester Signature:** _____________
**Date:** _____________
**Status:** [ ] PASS [ ] FAIL [ ] NEEDS REVIEW

---

## Notes

(Additional observations, edge cases, performance notes, etc.)
