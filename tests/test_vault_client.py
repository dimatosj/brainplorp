"""
Tests for VaultClient - CouchDB HTTP API client
"""

import pytest
import responses
from brainplorp.integrations.vault_client import (
    VaultClient,
    VaultUpdateConflictError,
    VaultDocumentNotFoundError
)


@pytest.fixture
def client():
    """Create VaultClient instance for testing."""
    return VaultClient(
        server_url="https://couch.test.dev",
        database="test-vault",
        username="test-user",
        password="test-pass"
    )


@responses.activate
def test_read_document(client):
    """Test reading a document from CouchDB."""
    responses.add(
        responses.GET,
        'https://couch.test.dev/test-vault/daily%2F2025-10-12.md',
        json={
            '_id': 'daily/2025-10-12.md',
            '_rev': '1-abc123',
            'type': 'markdown',
            'path': 'daily/2025-10-12.md',
            'content': '# Daily Note - 2025-10-12\n\n## Tasks\n- [ ] Review inbox'
        },
        status=200
    )

    doc = client.read_document('daily/2025-10-12.md')

    assert doc['_id'] == 'daily/2025-10-12.md'
    assert doc['_rev'] == '1-abc123'
    assert '# Daily Note' in doc['content']


@responses.activate
def test_read_document_not_found(client):
    """Test reading non-existent document raises exception."""
    responses.add(
        responses.GET,
        'https://couch.test.dev/test-vault/missing.md',
        json={'error': 'not_found', 'reason': 'missing'},
        status=404
    )

    with pytest.raises(VaultDocumentNotFoundError, match="Document not found: missing.md"):
        client.read_document('missing.md')


@responses.activate
def test_write_document_new(client):
    """Test writing a new document."""
    # First GET returns 404 (document doesn't exist)
    responses.add(
        responses.GET,
        'https://couch.test.dev/test-vault/inbox%2F2025-10.md',
        json={'error': 'not_found'},
        status=404
    )

    # PUT creates the document
    responses.add(
        responses.PUT,
        'https://couch.test.dev/test-vault/inbox%2F2025-10.md',
        json={'ok': True, 'id': 'inbox/2025-10.md', 'rev': '1-xyz'},
        status=201
    )

    result = client.write_document('inbox/2025-10.md', '## Unprocessed\n- [ ] Task 1')

    assert result['ok'] is True
    assert result['id'] == 'inbox/2025-10.md'


@responses.activate
def test_write_document_existing(client):
    """Test overwriting existing document."""
    # GET returns existing document with revision
    responses.add(
        responses.GET,
        'https://couch.test.dev/test-vault/inbox%2F2025-10.md',
        json={
            '_id': 'inbox/2025-10.md',
            '_rev': '2-abc',
            'content': 'Old content'
        },
        status=200
    )

    # PUT updates with revision
    responses.add(
        responses.PUT,
        'https://couch.test.dev/test-vault/inbox%2F2025-10.md',
        json={'ok': True, 'id': 'inbox/2025-10.md', 'rev': '3-def'},
        status=201
    )

    result = client.write_document('inbox/2025-10.md', 'New content')

    assert result['ok'] is True
    assert result['rev'] == '3-def'


@responses.activate
def test_update_document_success(client):
    """Test updating document with update function."""
    # GET returns document
    responses.add(
        responses.GET,
        'https://couch.test.dev/test-vault/inbox%2F2025-10.md',
        json={
            '_id': 'inbox/2025-10.md',
            '_rev': '1-abc',
            'path': 'inbox/2025-10.md',
            'content': '- [ ] Task 1'
        },
        status=200
    )

    # PUT succeeds (no conflict)
    responses.add(
        responses.PUT,
        'https://couch.test.dev/test-vault/inbox%2F2025-10.md',
        json={'ok': True, 'id': 'inbox/2025-10.md', 'rev': '2-def'},
        status=201
    )

    def add_task(content):
        return content + '\n- [ ] Task 2'

    result = client.update_document('inbox/2025-10.md', add_task)

    assert result['ok'] is True
    assert result['rev'] == '2-def'


@responses.activate
def test_update_document_mvcc_retry(client):
    """Test MVCC conflict retry with exponential backoff."""
    # First attempt: GET returns rev 1
    responses.add(
        responses.GET,
        'https://couch.test.dev/test-vault/inbox%2F2025-10.md',
        json={
            '_id': 'inbox/2025-10.md',
            '_rev': '1-abc',
            'path': 'inbox/2025-10.md',
            'content': 'Original'
        },
        status=200
    )

    # First PUT: Conflict (another client updated it)
    responses.add(
        responses.PUT,
        'https://couch.test.dev/test-vault/inbox%2F2025-10.md',
        json={'error': 'conflict', 'reason': 'Document update conflict'},
        status=409
    )

    # Second attempt: GET returns rev 2 (updated by other client)
    responses.add(
        responses.GET,
        'https://couch.test.dev/test-vault/inbox%2F2025-10.md',
        json={
            '_id': 'inbox/2025-10.md',
            '_rev': '2-def',
            'path': 'inbox/2025-10.md',
            'content': 'Original + Update from other client'
        },
        status=200
    )

    # Second PUT: Success
    responses.add(
        responses.PUT,
        'https://couch.test.dev/test-vault/inbox%2F2025-10.md',
        json={'ok': True, 'id': 'inbox/2025-10.md', 'rev': '3-ghi'},
        status=201
    )

    def add_task(content):
        return content + '\n- [ ] My update'

    result = client.update_document('inbox/2025-10.md', add_task)

    assert result['ok'] is True
    assert result['rev'] == '3-ghi'


@responses.activate
def test_update_document_max_retries_exceeded(client):
    """Test MVCC conflict after max retries raises exception."""
    # Setup: 5 GET requests + 5 PUT conflicts (initial + 4 retries)
    for _ in range(5):
        responses.add(
            responses.GET,
            'https://couch.test.dev/test-vault/inbox%2F2025-10.md',
            json={
                '_id': 'inbox/2025-10.md',
                '_rev': '1-abc',
                'path': 'inbox/2025-10.md',
                'content': 'Content'
            },
            status=200
        )

        responses.add(
            responses.PUT,
            'https://couch.test.dev/test-vault/inbox%2F2025-10.md',
            json={'error': 'conflict'},
            status=409
        )

    def add_task(content):
        return content + '\n- [ ] Task'

    with pytest.raises(VaultUpdateConflictError, match="MVCC conflict after 5 attempts"):
        client.update_document('inbox/2025-10.md', add_task, max_retries=4)


@responses.activate
def test_batch_read(client):
    """Test reading multiple documents in one request."""
    responses.add(
        responses.POST,
        'https://couch.test.dev/test-vault/_all_docs',
        json={
            'rows': [
                {
                    'id': 'daily/2025-10-01.md',
                    'doc': {
                        '_id': 'daily/2025-10-01.md',
                        '_rev': '1-abc',
                        'path': 'daily/2025-10-01.md',
                        'content': '# Oct 1'
                    }
                },
                {
                    'id': 'daily/2025-10-02.md',
                    'doc': {
                        '_id': 'daily/2025-10-02.md',
                        '_rev': '1-def',
                        'path': 'daily/2025-10-02.md',
                        'content': '# Oct 2'
                    }
                }
            ]
        },
        status=200
    )

    results = client.batch_read(['daily/2025-10-01.md', 'daily/2025-10-02.md'])

    assert len(results) == 2
    assert 'daily/2025-10-01.md' in results
    assert 'daily/2025-10-02.md' in results
    assert '# Oct 1' in results['daily/2025-10-01.md']['content']


@responses.activate
def test_list_documents(client):
    """Test listing all documents."""
    responses.add(
        responses.GET,
        'https://couch.test.dev/test-vault/_all_docs',
        json={
            'rows': [
                {'id': 'daily/2025-10-01.md'},
                {'id': 'daily/2025-10-02.md'},
                {'id': 'inbox/2025-10.md'},
                {'id': '_design/analytics'}  # Should be filtered out
            ]
        },
        status=200
    )

    docs = client.list_documents()

    assert len(docs) == 3
    assert 'daily/2025-10-01.md' in docs
    assert '_design/analytics' not in docs


@responses.activate
def test_list_documents_with_prefix(client):
    """Test listing documents with prefix filter."""
    responses.add(
        responses.GET,
        'https://couch.test.dev/test-vault/_all_docs',
        json={
            'rows': [
                {'id': 'daily/2025-10-01.md'},
                {'id': 'daily/2025-10-02.md'},
                {'id': 'inbox/2025-10.md'}
            ]
        },
        status=200
    )

    docs = client.list_documents(prefix='daily/')

    assert len(docs) == 2
    assert all(doc.startswith('daily/') for doc in docs)


@responses.activate
def test_document_exists_true(client):
    """Test checking if document exists (it does)."""
    responses.add(
        responses.GET,
        'https://couch.test.dev/test-vault/daily%2F2025-10-12.md',
        json={'_id': 'daily/2025-10-12.md', '_rev': '1-abc', 'content': 'Exists'},
        status=200
    )

    assert client.document_exists('daily/2025-10-12.md') is True


@responses.activate
def test_document_exists_false(client):
    """Test checking if document exists (it doesn't)."""
    responses.add(
        responses.GET,
        'https://couch.test.dev/test-vault/missing.md',
        json={'error': 'not_found'},
        status=404
    )

    assert client.document_exists('missing.md') is False


@responses.activate
def test_delete_document(client):
    """Test deleting a document."""
    # GET to retrieve current revision
    responses.add(
        responses.GET,
        'https://couch.test.dev/test-vault/old-file.md',
        json={
            '_id': 'old-file.md',
            '_rev': '5-abc',
            'path': 'old-file.md',
            'content': 'Delete me'
        },
        status=200
    )

    # DELETE with revision
    responses.add(
        responses.DELETE,
        'https://couch.test.dev/test-vault/old-file.md',
        json={'ok': True, 'id': 'old-file.md', 'rev': '6-deleted'},
        status=200
    )

    result = client.delete_document('old-file.md')

    assert result['ok'] is True
    assert result['rev'] == '6-deleted'
