# Sprint 9.2 Manual Testing Guide
## Email Inbox Capture (Gmail IMAP)

**Version:** 1.5.2
**Sprint:** 9.2
**Testing Date:** _____________
**Tester:** _____________

---

## Prerequisites

- brainplorp v1.5.2 installed
- Gmail account with 2FA enabled
- Gmail App Password generated
- Test emails in Gmail inbox/label
- Obsidian vault configured

---

## Test Environment Setup

### Step 1: Generate Gmail App Password

1. Go to https://myaccount.google.com/apppasswords
2. Generate password for "plorp"
3. Copy 16-character password
4. Store securely

### Step 2: Configure plorp

```bash
# Edit config file
vim ~/.config/plorp/config.yaml
```

Add email configuration:
```yaml
email:
  enabled: true
  imap_server: imap.gmail.com
  imap_port: 993
  username: your@gmail.com
  password: "xxxx xxxx xxxx xxxx"  # App Password from Step 1
  inbox_label: "plorp"  # Optional: only fetch from this label
  fetch_limit: 20
```

### Step 3: Create Test Emails

Send yourself test emails with:
1. Plain text body with bullets
2. HTML body with `<ul><li>` lists
3. Plain text paragraphs (no bullets)
4. Mixed content
5. Email with signature
6. Empty body email

### Step 4: Verify Inbox File

```bash
# Check monthly inbox exists
ls ~/vault/inbox/2025-10.md

# View current content
cat ~/vault/inbox/2025-10.md
```

---

## Phase 1: Basic Fetch Operations

### Test 1.1: First Fetch (Dry Run)
**Command:** `brainplorp inbox fetch --dry-run`

**Steps:**
```bash
brainplorp inbox fetch --dry-run
```

**Expected Results:**
- ✅ Connects to Gmail IMAP
- ✅ Lists unread emails
- ✅ Shows email body preview
- ✅ NO changes to inbox file
- ✅ Exit code 0

**Actual Output:**
```
(Paste output here)
```

**Pass/Fail:** ______

---

### Test 1.2: First Real Fetch
**Command:** `brainplorp inbox fetch`

**Steps:**
```bash
brainplorp inbox fetch
```

**Expected Results:**
- ✅ Connects to Gmail
- ✅ Fetches unread emails
- ✅ Appends bullets to inbox file
- ✅ Marks emails as SEEN in Gmail
- ✅ Success message with count

**Actual Emails Fetched:** ______
**Check Inbox File:** ______

**Pass/Fail:** ______

---

### Test 1.3: Verify No Duplicates
**Command:** `brainplorp inbox fetch` (run twice)

**Steps:**
```bash
brainplorp inbox fetch
# Wait 5 seconds
brainplorp inbox fetch
```

**Expected Results:**
- ✅ First run: fetches emails
- ✅ Second run: no new emails (already marked SEEN)
- ✅ No duplicate bullets in inbox file

**Pass/Fail:** ______

---

### Test 1.4: Fetch with Limit
**Command:** `brainplorp inbox fetch --limit 5`

**Steps:**
1. Mark 20 emails as unread in Gmail
2. Run: `brainplorp inbox fetch --limit 5`

**Expected Results:**
- ✅ Only 5 emails fetched
- ✅ Others remain unread
- ✅ Limit respected

**Actual Fetched:** ______

**Pass/Fail:** ______

---

### Test 1.5: Fetch from Specific Label
**Command:** `brainplorp inbox fetch --label work`

**Steps:**
1. Create label "work" in Gmail
2. Add emails to that label
3. Run: `brainplorp inbox fetch --label work`

**Expected Results:**
- ✅ Only emails from "work" label fetched
- ✅ Other emails ignored
- ✅ Correct label filter applied

**Pass/Fail:** ______

---

### Test 1.6: Fetch from Gmail System Folder
**Command:** `brainplorp inbox fetch --label "[Gmail]/Sent"`

**Steps:**
```bash
brainplorp inbox fetch --label "[Gmail]/Sent" --limit 3
```

**Expected Results:**
- ✅ Connects to Gmail system folder
- ✅ Fetches sent emails
- ✅ No error on special folder name

**Pass/Fail:** ______

---

### Test 1.7: Verbose Output
**Command:** `brainplorp inbox fetch --verbose`

**Steps:**
```bash
brainplorp inbox fetch --verbose --limit 3
```

**Expected Results:**
- ✅ Shows detailed logging
- ✅ Displays email body preview (first 200 chars)
- ✅ NO subject shown (user requirement)
- ✅ Shows IMAP connection details

**Pass/Fail:** ______

---

## Phase 2: Email Format Conversion

### Test 2.1: Plain Text with Existing Bullets
**Email Body:**
```
- First item
- Second item
  - Nested item
- Third item
```

**Steps:**
1. Send email with above content
2. Run: `brainplorp inbox fetch`
3. Check inbox file

**Expected Results:**
- ✅ Bullets preserved exactly
- ✅ Nesting preserved
- ✅ No conversion needed (Strategy 1)

**Pass/Fail:** ______

---

### Test 2.2: HTML Email with List
**Email Body (HTML):**
```html
<ul>
  <li>First HTML item</li>
  <li>Second HTML item</li>
  <ul>
    <li>Nested HTML item</li>
  </ul>
</ul>
```

**Steps:**
1. Send HTML email with list
2. Run: `brainplorp inbox fetch`
3. Check inbox file

**Expected Results:**
- ✅ Converted to markdown bullets (Strategy 2)
- ✅ Uses html2text library
- ✅ Nesting preserved
- ✅ Format: `- First HTML item`

**Pass/Fail:** ______

---

### Test 2.3: Plain Text Paragraphs
**Email Body:**
```
This is the first paragraph.

This is the second paragraph.

This is the third paragraph.
```

**Steps:**
1. Send plain text email with paragraphs
2. Run: `brainplorp inbox fetch`
3. Check inbox file

**Expected Results:**
- ✅ Each paragraph becomes a bullet (Strategy 3)
- ✅ Empty lines removed
- ✅ Format: `- This is the first paragraph.`

**Pass/Fail:** ______

---

### Test 2.4: Email with Signature
**Email Body:**
```
Here's my task list:
- Buy groceries
- Call dentist

--
Sent from my iPhone
```

**Steps:**
1. Send email with signature
2. Run: `brainplorp inbox fetch`
3. Check inbox file

**Expected Results:**
- ✅ Signature removed (everything after "-- ")
- ✅ Only bullets before signature kept
- ✅ Clean output

**Pass/Fail:** ______

---

### Test 2.5: Email with "Sent from" Signature
**Email Body:**
```
- Task 1
- Task 2

Sent from my Android device
```

**Steps:**
1. Send email with mobile signature
2. Run: `brainplorp inbox fetch`

**Expected Results:**
- ✅ "Sent from" signature removed
- ✅ Only tasks kept

**Pass/Fail:** ______

---

### Test 2.6: Mixed HTML and Plain Text
**Email:** Multipart MIME (both HTML and plain text)

**Steps:**
1. Send multipart email
2. Run: `brainplorp inbox fetch`

**Expected Results:**
- ✅ HTML part processed if available
- ✅ Falls back to plain text if HTML fails
- ✅ No error

**Pass/Fail:** ______

---

### Test 2.7: Empty Body Email
**Email Body:** (empty)

**Steps:**
1. Send email with subject but no body
2. Run: `brainplorp inbox fetch`

**Expected Results:**
- ✅ Email processed without error
- ✅ No bullets added to inbox (nothing to add)
- ✅ Email marked as SEEN
- ✅ No crash

**Pass/Fail:** ______

---

### Test 2.8: Very Long Email
**Email Body:** 5000+ words

**Steps:**
1. Send very long email
2. Run: `brainplorp inbox fetch`

**Expected Results:**
- ✅ Entire body processed (no length limit per Q8)
- ✅ All paragraphs converted to bullets
- ✅ No truncation

**Pass/Fail:** ______

---

## Phase 3: Error Handling

### Test 3.1: Invalid Credentials
**Steps:**
1. Change password in config to wrong value
2. Run: `brainplorp inbox fetch`

**Expected Results:**
- ✅ Clear authentication error message
- ✅ No crash
- ✅ Suggests checking credentials
- ✅ Exit code non-zero

**Pass/Fail:** ______

---

### Test 3.2: Network Disconnected
**Steps:**
1. Disconnect network/WiFi
2. Run: `brainplorp inbox fetch`

**Expected Results:**
- ✅ Connection error message
- ✅ No crash
- ✅ Graceful failure
- ✅ Exit code non-zero

**Pass/Fail:** ______

---

### Test 3.3: Gmail Rate Limit (if applicable)
**Steps:**
1. Run fetch 50+ times rapidly
2. Observe behavior

**Expected Results:**
- ✅ Handles rate limiting gracefully
- ✅ Clear error message
- ✅ Suggests retry later

**Pass/Fail:** ______

---

### Test 3.4: Missing Inbox Folder
**Steps:**
1. Delete `~/vault/inbox/` folder
2. Run: `brainplorp inbox fetch`

**Expected Results:**
- ✅ Folder auto-created
- ✅ Inbox file auto-created
- ✅ Proper structure (## Unprocessed, ## Processed)
- ✅ No error

**Pass/Fail:** ______

---

### Test 3.5: Corrupt Inbox File
**Steps:**
1. Add random binary data to inbox file
2. Run: `brainplorp inbox fetch`

**Expected Results:**
- ✅ File validated/corrected if possible
- ✅ Error message if can't fix
- ✅ Data not lost

**Pass/Fail:** ______

---

### Test 3.6: Label Doesn't Exist
**Steps:**
```bash
brainplorp inbox fetch --label nonexistent
```

**Expected Results:**
- ✅ Clear error: label not found
- ✅ Lists available labels
- ✅ No crash

**Pass/Fail:** ______

---

### Test 3.7: Email Encoding Issues
**Steps:**
1. Send email with special characters (emoji, unicode)
2. Run: `brainplorp inbox fetch`

**Expected Results:**
- ✅ Special characters handled correctly
- ✅ UTF-8 encoding preserved
- ✅ No garbled text

**Pass/Fail:** ______

---

## Phase 4: Configuration Tests

### Test 4.1: Disabled Email Fetching
**Steps:**
1. Set `email.enabled: false` in config
2. Run: `brainplorp inbox fetch`

**Expected Results:**
- ✅ Clear message: email fetching disabled
- ✅ No connection attempted
- ✅ Exit gracefully

**Pass/Fail:** ______

---

### Test 4.2: Missing Configuration
**Steps:**
1. Remove entire `email:` section from config
2. Run: `brainplorp inbox fetch`

**Expected Results:**
- ✅ Clear error: configuration missing
- ✅ Shows example configuration
- ✅ Exit code non-zero

**Pass/Fail:** ______

---

### Test 4.3: App Password with Whitespace
**Steps:**
1. Add spaces/newlines to app password in config
2. Run: `brainplorp inbox fetch`

**Expected Results:**
- ✅ Whitespace stripped automatically (per Q10)
- ✅ Authentication succeeds
- ✅ No manual trimming needed

**Pass/Fail:** ______

---

## Phase 5: Integration Tests

### Test 5.1: Fetch + Process Workflow
**Steps:**
```bash
brainplorp inbox fetch
brainplorp inbox process
```

**Expected Results:**
- ✅ Emails fetched and added to inbox
- ✅ Items processable with inbox process command
- ✅ Full workflow works end-to-end

**Pass/Fail:** ______

---

### Test 5.2: Cron Job Simulation
**Steps:**
```bash
# Run every minute for 5 minutes
for i in {1..5}; do
  brainplorp inbox fetch
  sleep 60
done
```

**Expected Results:**
- ✅ Runs reliably every minute
- ✅ No duplicate fetches
- ✅ No memory leaks
- ✅ Consistent behavior

**Pass/Fail:** ______

---

### Test 5.3: Shell Redirection for Logging
**Steps:**
```bash
brainplorp inbox fetch >> /tmp/plorp-fetch.log 2>&1
cat /tmp/plorp-fetch.log
```

**Expected Results:**
- ✅ Output redirected correctly (per Q18)
- ✅ Both stdout and stderr captured
- ✅ Suitable for cron logging

**Pass/Fail:** ______

---

## Phase 6: Inbox File Format Tests

### Test 6.1: Verify Bullet Format
**Steps:**
1. Run: `brainplorp inbox fetch`
2. Open inbox file

**Expected Results:**
- ✅ Plain bullets (`- `) NOT checkboxes (per Q2)
- ✅ Items under "## Unprocessed" section
- ✅ No metadata, no subject (per Q9)
- ✅ Just body content

**Pass/Fail:** ______

---

### Test 6.2: Mixed Format Handling
**Steps:**
1. Manually add checkboxes to inbox
2. Run: `brainplorp inbox fetch`
3. Check result

**Expected Results:**
- ✅ New items added as plain bullets (per Q5)
- ✅ Existing checkboxes preserved
- ✅ Mixed format acceptable

**Pass/Fail:** ______

---

### Test 6.3: Section Auto-Creation
**Steps:**
1. Delete "## Unprocessed" section from inbox
2. Run: `brainplorp inbox fetch`

**Expected Results:**
- ✅ Section auto-created (per Q16)
- ✅ Items added correctly
- ✅ No error

**Pass/Fail:** ______

---

## Performance Tests

### Test P1: Fetch Speed (5 emails)
**Steps:**
```bash
time brainplorp inbox fetch --limit 5
```

**Expected Results:**
- ✅ Completes in <10 seconds
- ✅ Reasonable IMAP performance

**Actual Time:** ______ seconds

**Pass/Fail:** ______

---

### Test P2: Fetch Speed (20 emails)
**Steps:**
```bash
time brainplorp inbox fetch --limit 20
```

**Expected Results:**
- ✅ Completes in <30 seconds
- ✅ Scales reasonably

**Actual Time:** ______ seconds

**Pass/Fail:** ______

---

### Test P3: HTML Conversion Performance
**Steps:**
1. Send 10 HTML emails
2. Time the fetch

**Expected Results:**
- ✅ html2text library performs well
- ✅ No significant slowdown vs plain text

**Actual Time:** ______ seconds

**Pass/Fail:** ______

---

## Test Summary

**Total Tests:** 40
**Passed:** ______
**Failed:** ______
**Skipped:** ______

**Performance:**
- 5 emails: ______ seconds
- 20 emails: ______ seconds

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

## Notes

(Email format observations, Gmail-specific behavior, suggestions, etc.)

---

## Appendix: Sample Emails for Testing

### A1: Plain Text with Bullets
```
Subject: Test Email 1

- Task one
- Task two
- Task three
```

### A2: HTML Email
```html
Subject: Test Email 2

<html>
<body>
<ul>
  <li>HTML task one</li>
  <li>HTML task two</li>
</ul>
</body>
</html>
```

### A3: Paragraphs
```
Subject: Test Email 3

First paragraph here.

Second paragraph here.

Third paragraph here.
```

### A4: With Signature
```
Subject: Test Email 4

- Important task
- Another task

--
Best regards,
Test User
```
