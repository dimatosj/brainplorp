# Vault Sync Developer Guide

**Sprint 10.3: Server HTTP API for Vault Access**

## Overview

The `VaultClient` library provides HTTP API access to vault documents stored in CouchDB. This enables server-side automation tasks like:
- Email-to-inbox capture (server fetches emails, appends to inbox)
- Analytics and reporting (read daily notes, calculate completion rates)
- Scheduled task creation (cron jobs that add tasks to vault)

## When to Use VaultClient

**Use VaultClient when:**
- ✅ Running on brainplorp server (Fly.io, no local vault)
- ✅ Automating vault modifications (email fetch, batch operations)
- ✅ Reading vault data for analytics
- ✅ Writing to vault from remote scripts

**Don't use VaultClient when:**
- ❌ Running locally on user's Mac (use local file operations instead)
- ❌ User-facing CLI commands (use direct file I/O for performance)

## Installation

VaultClient is part of brainplorp:

```python
from brainplorp.integrations.vault_client import VaultClient
```

Dependencies (already in `pyproject.toml`):
- `requests>=2.31.0`

## Quick Start

### Initialize Client

```python
from brainplorp.integrations.vault_client import VaultClient

client = VaultClient(
    server_url="https://couch-brainplorp-sync.fly.dev",
    database="user-jsd-vault",
    username="user-jsd",
    password="<password-from-keyring>"
)
```

### Read a Document

```python
# Read today's daily note
doc = client.read_document("daily/2025-10-12.md")

print(doc['_id'])       # 'daily/2025-10-12.md'
print(doc['_rev'])      # '3-abc123' (CouchDB revision)
print(doc['content'])   # '# Daily Note - 2025-10-12\n\n## Tasks\n...'
```

### Write a Document

```python
# Write to inbox
client.write_document(
    path="inbox/2025-10.md",
    content="## Unprocessed\n- [ ] Email: Meeting reminder\n"
)
```

### Update a Document (MVCC-Safe)

```python
def add_email(content):
    """Append email to inbox."""
    return content + "\n- [ ] Email: New project kickoff"

# Handles MVCC conflicts automatically with retry
client.update_document("inbox/2025-10.md", add_email)
```

## API Reference

### VaultClient.__init__

```python
VaultClient(
    server_url: str,
    database: str,
    username: str,
    password: str
)
```

**Args:**
- `server_url`: CouchDB server URL (e.g., `https://couch-brainplorp-sync.fly.dev`)
- `database`: Database name (e.g., `user-jsd-vault`)
- `username`: CouchDB username
- `password`: CouchDB password

**Connection Pooling:**
- 10 persistent connections with keep-alive
- Automatic retry on connection failures (3 retries)

### read_document

```python
client.read_document(path: str) -> dict
```

Read a vault document by path.

**Args:**
- `path`: Document path (e.g., `"daily/2025-10-12.md"`)

**Returns:**
Dict with keys:
- `_id`: Document ID (same as path)
- `_rev`: CouchDB revision (for MVCC)
- `content`: Markdown content
- `path`: Document path
- `type`: Usually `"markdown"`

**Raises:**
- `VaultDocumentNotFoundError`: Document doesn't exist
- `requests.RequestException`: HTTP error

**Example:**
```python
try:
    doc = client.read_document("daily/2025-10-12.md")
    print(f"Content: {doc['content']}")
except VaultDocumentNotFoundError:
    print("Document not found")
```

### write_document

```python
client.write_document(
    path: str,
    content: str,
    metadata: Optional[Dict] = None
) -> dict
```

Write a document (create new or overwrite existing).

**WARNING:** Does NOT handle MVCC conflicts. Use `update_document()` for safe updates.

**Args:**
- `path`: Document path
- `content`: Markdown content
- `metadata`: Optional metadata (mtime, ctime, etc.)

**Returns:**
CouchDB response: `{ok: True, id: ..., rev: ...}`

**Example:**
```python
client.write_document(
    "notes/new-idea.md",
    "# New Idea\n\nBrainstorming session notes...",
    metadata={"mtime": "2025-10-12T14:30:00Z"}
)
```

### update_document (Recommended)

```python
client.update_document(
    path: str,
    update_fn: Callable[[str], str],
    max_retries: int = 4
) -> dict
```

Update document with MVCC conflict handling.

**How it works:**
1. Read current document + revision
2. Apply `update_fn` to content
3. Save with current revision
4. If conflict (another client updated): retry with exponential backoff
5. Max 5 attempts (initial + 4 retries)

**Args:**
- `path`: Document path
- `update_fn`: Function that takes current content, returns updated content
- `max_retries`: Max retry attempts (default: 4)

**Returns:**
CouchDB response after successful update

**Raises:**
- `VaultUpdateConflictError`: Max retries exceeded
- `VaultDocumentNotFoundError`: Document doesn't exist

**Example 1: Append to inbox**
```python
def add_email(content):
    return content + "\n- [ ] Email: Quarterly review"

client.update_document("inbox/2025-10.md", add_email)
```

**Example 2: Update specific line**
```python
def mark_task_done(content):
    return content.replace(
        "- [ ] Buy groceries",
        "- [x] Buy groceries"
    )

client.update_document("daily/2025-10-12.md", mark_task_done)
```

**Retry Strategy:**
- Attempt 1: Immediate
- Attempt 2: 100ms delay
- Attempt 3: 200ms delay
- Attempt 4: 400ms delay
- Attempt 5: 800ms delay

Total max time: 1.5 seconds if all retries fail.

### list_documents

```python
client.list_documents(prefix: str = "") -> List[str]
```

List all documents in vault, optionally filtered by prefix.

**Args:**
- `prefix`: Only return documents starting with this prefix (e.g., `"daily/"`)

**Returns:**
List of document IDs (paths)

**Example:**
```python
# Get all daily notes
daily_notes = client.list_documents(prefix="daily/")
# ['daily/2025-10-01.md', 'daily/2025-10-02.md', ...]

# Get all documents
all_docs = client.list_documents()
```

### batch_read

```python
client.batch_read(paths: List[str]) -> Dict[str, Dict]
```

Read multiple documents in a single HTTP request (efficient).

**Args:**
- `paths`: List of document paths

**Returns:**
Dict mapping path → document

**Example:**
```python
# Read a week of daily notes
week_paths = [
    "daily/2025-10-06.md",
    "daily/2025-10-07.md",
    "daily/2025-10-08.md",
    "daily/2025-10-09.md",
    "daily/2025-10-10.md",
    "daily/2025-10-11.md",
    "daily/2025-10-12.md"
]

docs = client.batch_read(week_paths)

for path, doc in docs.items():
    print(f"{path}: {len(doc['content'])} bytes")
```

### document_exists

```python
client.document_exists(path: str) -> bool
```

Check if document exists.

**Example:**
```python
if client.document_exists("daily/2025-10-12.md"):
    print("Today's note exists")
else:
    print("Create today's note")
```

### delete_document

```python
client.delete_document(path: str) -> dict
```

Delete a document.

**Example:**
```python
client.delete_document("old-notes/archived.md")
```

## Common Use Cases

### Use Case 1: Email-to-Inbox Automation

Server fetches emails from Gmail, appends to monthly inbox file.

```python
from brainplorp.integrations.vault_client import VaultClient
import datetime

# Initialize client (get credentials from Fly.io secrets)
client = VaultClient(
    server_url=os.getenv('COUCHDB_SERVER'),
    database=os.getenv('COUCHDB_DATABASE'),
    username=os.getenv('COUCHDB_USERNAME'),
    password=os.getenv('COUCHDB_PASSWORD')
)

# Fetch emails (pseudocode)
emails = fetch_emails_from_gmail()

# Get current month's inbox path
month = datetime.date.today().strftime('%Y-%m')
inbox_path = f"inbox/{month}.md"

# Define update function
def append_emails(content):
    new_items = "\n".join(f"- [ ] Email: {email.subject}" for email in emails)
    return content + "\n" + new_items

# Update inbox (handles MVCC conflicts automatically)
client.update_document(inbox_path, append_emails)

print(f"Added {len(emails)} emails to {inbox_path}")
```

### Use Case 2: Weekly Task Completion Report

Analyze a week of daily notes to calculate task completion rate.

```python
import re
from datetime import date, timedelta

def calculate_weekly_completion(client, start_date):
    # Generate paths for 7 days
    paths = [
        f"daily/{start_date + timedelta(days=i)}.md"
        for i in range(7)
    ]

    # Batch read all daily notes
    docs = client.batch_read(paths)

    total_tasks = 0
    completed_tasks = 0

    for path, doc in docs.items():
        content = doc['content']

        # Count all tasks
        all_tasks = re.findall(r'- \[[x ]\]', content)
        total_tasks += len(all_tasks)

        # Count completed tasks
        completed = re.findall(r'- \[x\]', content)
        completed_tasks += len(completed)

    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    return {
        'total': total_tasks,
        'completed': completed_tasks,
        'rate': completion_rate
    }

# Run report
stats = calculate_weekly_completion(client, date(2025, 10, 6))
print(f"Week completion: {stats['completed']}/{stats['total']} ({stats['rate']:.1f}%)")
```

### Use Case 3: Scheduled Task Creation

Cron job that adds recurring tasks to today's daily note.

```python
from datetime import date

def add_recurring_tasks(client):
    today = date.today()
    daily_path = f"daily/{today}.md"

    # Check if daily note exists
    if not client.document_exists(daily_path):
        # Create new daily note
        content = f"# Daily Note - {today}\n\n## Tasks\n"
        client.write_document(daily_path, content)

    # Add recurring tasks
    def append_tasks(content):
        tasks = [
            "- [ ] Review inbox",
            "- [ ] Plan tomorrow",
            "- [ ] Process email"
        ]
        return content + "\n" + "\n".join(tasks)

    client.update_document(daily_path, append_tasks)
    print(f"Added recurring tasks to {daily_path}")
```

## MVCC Conflict Handling

### What is MVCC?

**Multi-Version Concurrency Control** - CouchDB's conflict detection mechanism.

Every document has a revision number (`_rev`). To update a document, you must provide the current `_rev`. If another client updated the document, your `_rev` is stale, and CouchDB rejects the update with HTTP 409 Conflict.

### How VaultClient Handles Conflicts

`update_document()` implements automatic retry with exponential backoff:

```
Attempt 1: Read rev 1-abc, update, save → Conflict (someone else wrote rev 2-def)
         Wait 100ms
Attempt 2: Read rev 2-def, update, save → Success!
```

**Retry delays:**
- 100ms → 200ms → 400ms → 800ms
- Total: 1.5 seconds max

### Best Practices

**✅ Always use `update_document()` for concurrent writes:**
```python
# Good: Handles conflicts automatically
client.update_document("inbox/2025-10.md", lambda c: c + "\n- [ ] New item")
```

**❌ Don't use `write_document()` for concurrent updates:**
```python
# Bad: Will fail if another client updates simultaneously
doc = client.read_document("inbox/2025-10.md")
content = doc['content'] + "\n- [ ] New item"
client.write_document("inbox/2025-10.md", content)  # Race condition!
```

### Handling Update Failures

```python
from brainplorp.integrations.vault_client import VaultUpdateConflictError

try:
    client.update_document("inbox/2025-10.md", add_email)
except VaultUpdateConflictError as e:
    # Max retries exceeded - log and alert
    print(f"Failed to update after 5 attempts: {e}")
    send_alert("Vault sync conflict - please investigate")
```

## Performance Considerations

### Batch vs. Individual Reads

**Individual reads:**
```python
# Slow: 7 HTTP requests
for i in range(7):
    doc = client.read_document(f"daily/2025-10-{6+i:02d}.md")
    # Process doc
```

**Batch read:**
```python
# Fast: 1 HTTP request
paths = [f"daily/2025-10-{6+i:02d}.md" for i in range(7)]
docs = client.batch_read(paths)
# Process docs
```

**Recommendation:** Use `batch_read()` for reading >3 documents.

### Connection Pooling

VaultClient uses connection pooling (10 persistent connections). This means:
- First request: Establishes connection (~100ms overhead)
- Subsequent requests: Reuse connection (~10ms overhead)

**Optimization:** Reuse the same `VaultClient` instance across multiple operations.

```python
# Good: One client instance
client = VaultClient(...)
for i in range(100):
    client.read_document(f"note-{i}.md")

# Bad: New client per operation (slow!)
for i in range(100):
    client = VaultClient(...)  # Reconnects every time
    client.read_document(f"note-{i}.md")
```

## Security

### Credentials Management

**In server scripts (Fly.io):**
```python
import os

client = VaultClient(
    server_url=os.getenv('COUCHDB_SERVER'),
    database=os.getenv('COUCHDB_DATABASE'),
    username=os.getenv('COUCHDB_USERNAME'),
    password=os.getenv('COUCHDB_PASSWORD')
)
```

Set secrets via Fly.io CLI:
```bash
fly secrets set COUCHDB_PASSWORD=abc123... -a brainplorp-server
```

**In local scripts:**
```python
import keyring

password = keyring.get_password("brainplorp-vault-sync", username)
client = VaultClient(server_url, database, username, password)
```

### Authentication

All requests use HTTP Basic Auth over HTTPS:
- Username and password sent in `Authorization` header
- HTTPS encrypts credentials in transit
- CouchDB validates on every request

## Testing

### Unit Tests with Mock HTTP

Use `responses` library to mock CouchDB HTTP responses:

```python
import responses
from brainplorp.integrations.vault_client import VaultClient

@responses.activate
def test_read_document():
    responses.add(
        responses.GET,
        'https://couch.test.dev/vault/daily%2F2025-10-12.md',
        json={
            '_id': 'daily/2025-10-12.md',
            '_rev': '1-abc',
            'content': '# Daily Note'
        },
        status=200
    )

    client = VaultClient('https://couch.test.dev', 'vault', 'user', 'pass')
    doc = client.read_document('daily/2025-10-12.md')

    assert doc['content'] == '# Daily Note'
```

### Integration Tests with Real CouchDB

For testing against real CouchDB (optional):

```bash
# Start test CouchDB container
docker run -d -p 5984:5984 couchdb:3.3.3

# Run integration tests
pytest tests/integration/test_vault_client_real.py

# Cleanup
docker stop <container-id>
```

## Error Handling

### Exception Hierarchy

```
VaultUpdateConflictError - MVCC conflict after max retries
VaultDocumentNotFoundError - Document doesn't exist
requests.RequestException - HTTP/network errors
```

### Example Error Handling

```python
from brainplorp.integrations.vault_client import (
    VaultClient,
    VaultUpdateConflictError,
    VaultDocumentNotFoundError
)
import requests

try:
    client.update_document("inbox/2025-10.md", add_email)

except VaultDocumentNotFoundError:
    # Document doesn't exist - create it first
    client.write_document("inbox/2025-10.md", "## Unprocessed\n")
    client.update_document("inbox/2025-10.md", add_email)

except VaultUpdateConflictError as e:
    # Max retries exceeded - log and alert
    logger.error(f"MVCC conflict: {e}")
    send_alert("Vault sync conflict")

except requests.RequestException as e:
    # HTTP/network error
    logger.error(f"Network error: {e}")
    retry_later()
```

## Next Steps

- See `VAULT_SYNC_ARCHITECTURE.md` for system design details
- See `VAULT_SYNC_USER_GUIDE.md` for end-user setup
- Check `src/brainplorp/integrations/vault_client.py` for implementation
- Review `tests/test_vault_client.py` for test examples
