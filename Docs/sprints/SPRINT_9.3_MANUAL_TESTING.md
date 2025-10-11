# Sprint 9.3 Manual Testing Guide
## Quick Add to Inbox (macOS)

**Version:** 1.5.3
**Sprint:** 9.3
**Testing Date:** _____________
**Tester:** _____________

---

## Prerequisites

- plorp v1.5.3 installed
- macOS system (for Raycast testing)
- Obsidian vault configured
- Raycast installed (recommended frontend)

---

## Test Environment Setup

### Verify Version
```bash
plorp --version  # Should show 1.5.3
```

### Verify Inbox File Exists
```bash
ls ~/vault/inbox/2025-10.md
cat ~/vault/inbox/2025-10.md
```

### Check Current Inbox Content
Note the current line count to verify additions:
```bash
wc -l ~/vault/inbox/2025-10.md
```

---

## Phase 1: CLI Command Tests

### Test 1.1: Basic Quick Add
**Command:** `plorp inbox add Buy milk`

**Steps:**
```bash
plorp inbox add Buy milk
```

**Expected Results:**
- ✅ Success message: "✓ Added to inbox: Buy milk"
- ✅ Bullet added to inbox file under "## Unprocessed"
- ✅ Format: `- Buy milk`
- ✅ Exit code 0

**Verify in File:**
```bash
tail -5 ~/vault/inbox/2025-10.md
```

**Pass/Fail:** ______

---

### Test 1.2: Multi-Word Without Quotes
**Command:** `plorp inbox add Call dentist tomorrow morning`

**Steps:**
```bash
plorp inbox add Call dentist tomorrow morning
```

**Expected Results:**
- ✅ Works without quotes (nargs=-1)
- ✅ Full text captured: "Call dentist tomorrow morning"
- ✅ Success message shown

**Pass/Fail:** ______

---

### Test 1.3: Urgent Flag (Short Form)
**Command:** `plorp inbox add -u Fix critical bug`

**Steps:**
```bash
plorp inbox add -u Fix critical bug
```

**Expected Results:**
- ✅ Urgent marker added: `- 🔴 Fix critical bug`
- ✅ Red circle emoji present
- ✅ Success message mentions urgent

**Pass/Fail:** ______

---

### Test 1.4: Urgent Flag (Long Form)
**Command:** `plorp inbox add --urgent Important meeting today`

**Steps:**
```bash
plorp inbox add --urgent Important meeting today
```

**Expected Results:**
- ✅ Works with --urgent
- ✅ Urgent marker added: `- 🔴 Important meeting today`
- ✅ Same behavior as -u

**Pass/Fail:** ______

---

### Test 1.5: Single Word Item
**Command:** `plorp inbox add Groceries`

**Steps:**
```bash
plorp inbox add Groceries
```

**Expected Results:**
- ✅ Single word accepted
- ✅ Bullet added correctly: `- Groceries`

**Pass/Fail:** ______

---

### Test 1.6: Very Long Item
**Command:** `plorp inbox add` + 200 character text

**Steps:**
```bash
plorp inbox add This is a very long task description that goes on and on with lots of details about what needs to be done including multiple aspects and considerations that should all be captured in the inbox for later processing
```

**Expected Results:**
- ✅ Full text captured
- ✅ No truncation
- ✅ Success

**Pass/Fail:** ______

---

### Test 1.7: Special Characters
**Command:** `plorp inbox add Buy @groceries & coffee (urgent!)`

**Steps:**
```bash
plorp inbox add Buy @groceries & coffee (urgent!)
```

**Expected Results:**
- ✅ Special characters preserved: @, &, (), !
- ✅ Exact text: `- Buy @groceries & coffee (urgent!)`

**Pass/Fail:** ______

---

### Test 1.8: Emoji in Text
**Command:** `plorp inbox add 🎉 Celebrate project completion`

**Steps:**
```bash
plorp inbox add 🎉 Celebrate project completion
```

**Expected Results:**
- ✅ Emoji preserved
- ✅ Full text: `- 🎉 Celebrate project completion`

**Pass/Fail:** ______

---

### Test 1.9: Verify Append Behavior
**Steps:**
1. Note current inbox content
2. Add 3 items in sequence
3. Check order in file

```bash
plorp inbox add First item
plorp inbox add Second item
plorp inbox add Third item
tail -5 ~/vault/inbox/2025-10.md
```

**Expected Results:**
- ✅ Items appended in order
- ✅ No items overwritten
- ✅ All three visible

**Pass/Fail:** ______

---

### Test 1.10: Help Text
**Command:** `plorp inbox add --help`

**Steps:**
```bash
plorp inbox add --help
```

**Expected Results:**
- ✅ Usage information shown
- ✅ --urgent flag documented
- ✅ Examples provided
- ✅ Clear description

**Pass/Fail:** ______

---

## Phase 2: Raycast Integration Tests

**Note:** Requires Raycast installed and configured

### Setup: Install Raycast Script

**Steps:**
1. Copy `raycast/quick-add-inbox.sh` to Raycast scripts folder:
```bash
mkdir -p ~/Library/Application\ Support/Raycast/Scripts
cp raycast/quick-add-inbox.sh ~/Library/Application\ Support/Raycast/Scripts/
chmod +x ~/Library/Application\ Support/Raycast/Scripts/quick-add-inbox.sh
```

2. Edit script to verify `PLORP_PATH` is correct:
```bash
cat ~/Library/Application\ Support/Raycast/Scripts/quick-add-inbox.sh | grep PLORP_PATH
# Should show: /Users/jsd/Documents/plorp/.venv/bin/plorp
# Update if needed
```

3. Open Raycast preferences → Extensions → Scripts
4. Verify "Quick Add to Inbox" appears
5. Assign keyboard shortcut: ⌘⌥I

---

### Test 2.1: Raycast Basic Add
**Shortcut:** ⌘⌥I

**Steps:**
1. Press ⌘⌥I anywhere on macOS
2. Raycast window opens with text input
3. Type: "Test item from Raycast"
4. Press Enter

**Expected Results:**
- ✅ Raycast window appears instantly
- ✅ Text input is focused
- ✅ Item added to inbox after Enter
- ✅ Success notification from Raycast
- ✅ Total time <3 seconds

**Pass/Fail:** ______

---

### Test 2.2: Raycast Urgent Add
**Steps:**
1. Press ⌘⌥I
2. Type: "🔴 Urgent task test"
3. Press Enter

**Expected Results:**
- ✅ Item added with 🔴 prefix
- ✅ Manual emoji works (user can type it)
- ✅ Success notification

**Pass/Fail:** ______

---

### Test 2.3: Raycast Multi-Word
**Steps:**
1. Press ⌘⌥I
2. Type: "Buy groceries call dentist schedule meeting"
3. Press Enter

**Expected Results:**
- ✅ Full text captured
- ✅ No quotes needed
- ✅ Success

**Pass/Fail:** ______

---

### Test 2.4: Raycast Empty Input
**Steps:**
1. Press ⌘⌥I
2. Press Enter immediately (no text)

**Expected Results:**
- ✅ Error message: "No text provided"
- ✅ Window closes gracefully
- ✅ No blank bullet added to inbox

**Pass/Fail:** ______

---

### Test 2.5: Raycast from Different Apps
**Steps:**
1. Open various apps: Chrome, VS Code, Terminal, Finder
2. From each app, press ⌘⌥I and add an item
3. Verify all work

**Expected Results:**
- ✅ Works from ANY application
- ✅ Global keyboard shortcut
- ✅ No app-specific issues

**Pass/Fail:** ______

---

### Test 2.6: Raycast Performance (Speed Test)
**Steps:**
1. Press ⌘⌥I
2. Start timer
3. Type: "Speed test item"
4. Press Enter
5. Stop timer when notification appears

**Expected Results:**
- ✅ Total time <3 seconds (ideally <2s)
- ✅ Instant Raycast popup
- ✅ Quick execution

**Actual Time:** ______ seconds

**Pass/Fail:** ______

---

### Test 2.7: Raycast Rapid Fire
**Steps:**
1. Add 5 items in quick succession (< 30 seconds total)

```
⌘⌥I → "Item 1" → Enter
⌘⌥I → "Item 2" → Enter
⌘⌥I → "Item 3" → Enter
⌘⌥I → "Item 4" → Enter
⌘⌥I → "Item 5" → Enter
```

**Expected Results:**
- ✅ All 5 items added successfully
- ✅ No race conditions
- ✅ Correct order in inbox
- ✅ No errors

**Pass/Fail:** ______

---

## Phase 3: Edge Cases & Error Handling

### Test 3.1: Empty Text
**Command:** `plorp inbox add`

**Steps:**
```bash
plorp inbox add
```

**Expected Results:**
- ✅ Error: "Error: Missing argument 'TEXT...'"
- ✅ Usage information shown
- ✅ Exit code non-zero

**Pass/Fail:** ______

---

### Test 3.2: Whitespace Only
**Command:** `plorp inbox add "   "`

**Steps:**
```bash
plorp inbox add "   "
```

**Expected Results:**
- ✅ Whitespace trimmed
- ✅ Error or empty bullet not added
- ✅ Graceful handling

**Pass/Fail:** ______

---

### Test 3.3: Missing Inbox Folder
**Steps:**
1. Delete inbox folder: `rm -rf ~/vault/inbox/`
2. Run: `plorp inbox add Test item`

**Expected Results:**
- ✅ Folder auto-created
- ✅ Monthly inbox file auto-created
- ✅ Proper structure (## Unprocessed, ## Processed)
- ✅ Item added successfully

**Pass/Fail:** ______

---

### Test 3.4: Missing Inbox File
**Steps:**
1. Delete current month's inbox: `rm ~/vault/inbox/2025-10.md`
2. Run: `plorp inbox add Test item`

**Expected Results:**
- ✅ File auto-created
- ✅ Proper structure
- ✅ Item added

**Pass/Fail:** ______

---

### Test 3.5: Corrupt Inbox File
**Steps:**
1. Add random binary data to inbox file
2. Run: `plorp inbox add Test item`

**Expected Results:**
- ✅ Error message or auto-fix
- ✅ No data loss if possible
- ✅ Clear error if unfixable

**Pass/Fail:** ______

---

### Test 3.6: Missing Unprocessed Section
**Steps:**
1. Remove "## Unprocessed" header from inbox
2. Run: `plorp inbox add Test item`

**Expected Results:**
- ✅ Section auto-created
- ✅ Item added correctly
- ✅ No error

**Pass/Fail:** ______

---

### Test 3.7: Vault Path Not Configured
**Steps:**
1. Remove `vault_path` from config
2. Run: `plorp inbox add Test`

**Expected Results:**
- ✅ Clear error: vault path not configured
- ✅ Suggests editing config
- ✅ Exit code non-zero

**Pass/Fail:** ______

---

## Phase 4: Integration Tests

### Test 4.1: Quick Add + Process Workflow
**Steps:**
```bash
# Add items
plorp inbox add Buy groceries
plorp inbox add Call dentist
plorp inbox add -u Fix bug

# Process them
plorp inbox process
```

**Expected Results:**
- ✅ Items appear in process workflow
- ✅ Can be converted to tasks or notes
- ✅ Urgent items have 🔴 marker
- ✅ Full GTD workflow works

**Pass/Fail:** ______

---

### Test 4.2: Cross-Month Boundary
**Steps:**
1. Change system date to last day of month (if possible)
2. Add item
3. Change date to first day of next month
4. Add another item
5. Verify both files

**Expected Results:**
- ✅ October item in `2025-10.md`
- ✅ November item in `2025-11.md`
- ✅ Correct month detection

**Pass/Fail:** ______

---

### Test 4.3: Concurrent Adds
**Steps:**
```bash
# Run two adds simultaneously
plorp inbox add "Item 1" &
plorp inbox add "Item 2" &
wait
```

**Expected Results:**
- ✅ Both items added
- ✅ No file corruption
- ✅ No lost writes

**Pass/Fail:** ______

---

## Phase 5: Alternative Frontends (Optional)

### Test 5.1: macOS Shortcuts (if configured)
**Steps:**
1. Create Shortcut with "Run Shell Script"
2. Call: `plorp inbox add "$text"`
3. Test via Siri or Shortcuts app

**Expected Results:**
- ✅ Works from Shortcuts
- ✅ Siri integration possible
- ✅ iOS/macOS sync

**Pass/Fail:** ______

---

### Test 5.2: Alfred Workflow (if installed)
**Steps:**
1. Install Alfred
2. Create workflow calling plorp
3. Test via Alfred

**Expected Results:**
- ✅ Works from Alfred
- ✅ Fast trigger
- ✅ Alternative to Raycast

**Pass/Fail:** ______

---

### Test 5.3: Direct CLI Usage
**Benchmark:** Compare all frontends

**Steps:**
1. Time Raycast add
2. Time CLI add
3. Time Shortcuts add (if available)

**Expected Results:**
- ✅ All <3 seconds
- ✅ Raycast fastest (1-2s)
- ✅ CLI instant (<100ms)

**Timings:**
- Raycast: ______ seconds
- CLI: ______ seconds
- Shortcuts: ______ seconds

**Pass/Fail:** ______

---

## Phase 6: User Experience Tests

### Test 6.1: Pure Capture Philosophy
**Observation Test**

**Steps:**
1. Add items with various complexity
2. Verify NO prompts for:
   - Project assignment
   - Due dates
   - Tags
   - Priority (except manual --urgent flag)

**Expected Results:**
- ✅ Zero friction capture
- ✅ No metadata prompts
- ✅ Fast entry
- ✅ Processing happens later via `plorp inbox process`

**Pass/Fail:** ______

---

### Test 6.2: Separation of Concerns
**Workflow Test**

**Capture Phase:**
```bash
plorp inbox add Buy milk
plorp inbox add Schedule meeting
plorp inbox add Review PR
```

**Processing Phase:**
```bash
plorp inbox process
# Now assign projects, dates, etc.
```

**Expected Results:**
- ✅ Capture is instant (no decisions)
- ✅ Processing is thoughtful (with decisions)
- ✅ Clear separation
- ✅ GTD-compliant

**Pass/Fail:** ______

---

### Test 6.3: Ubiquitous Capture
**Real-World Test**

**Steps:**
Throughout one workday:
1. Capture thoughts as they occur
2. Don't process immediately
3. Count captures

**Expected Results:**
- ✅ Can capture from anywhere
- ✅ No interruption to flow
- ✅ Easy to process later
- ✅ Nothing lost

**Capture Count:** ______

**Pass/Fail:** ______

---

## Test Summary

**Total Tests:** 35
**Passed:** ______
**Failed:** ______
**Skipped:** ______

**Performance:**
- CLI Average: ______ ms
- Raycast Average: ______ seconds (target: <3s)

---

## Issues Found

| Test # | Issue Description | Severity | Notes |
|--------|-------------------|----------|-------|
|        |                   |          |       |
|        |                   |          |       |

---

## Sign-Off

**Tester Signature:** _____________
**Date:** _____________
**Status:** [ ] PASS [ ] FAIL [ ] NEEDS REVIEW

---

## GTD Workflow Verification

**Core Principle:** Ubiquitous capture without friction

- [ ] Can capture from anywhere on macOS (⌘⌥I)
- [ ] Capture takes <3 seconds
- [ ] No metadata required during capture
- [ ] Processing happens separately via `plorp inbox process`
- [ ] No thoughts lost due to friction
- [ ] Separation of capture (fast) from organization (thoughtful)

**GTD Compliance:** [ ] PASS [ ] FAIL

---

## Notes

(Observations about capture friction, timing, integration with other apps, workflow suggestions, etc.)

---

## Appendix: Raycast Script Troubleshooting

### Issue: Script Not Appearing in Raycast
**Solution:**
1. Check file permissions: `ls -l ~/Library/Application\ Support/Raycast/Scripts/`
2. Ensure executable: `chmod +x quick-add-inbox.sh`
3. Reload Raycast: ⌘R in Raycast window

### Issue: PLORP_PATH Not Found
**Solution:**
1. Edit script: `vim ~/Library/Application\ Support/Raycast/Scripts/quick-add-inbox.sh`
2. Update `PLORP_PATH` to correct location
3. Verify: `which plorp` or `find ~ -name plorp -type f`

### Issue: Permission Denied
**Solution:**
1. Check vault permissions: `ls -ld ~/vault/inbox/`
2. Ensure write access: `touch ~/vault/inbox/test.txt`
