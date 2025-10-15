"""Tests for CouchDB client."""

import pytest
import responses
from brainplorp.integrations.couchdb import CouchDBClient, CouchDBError


@pytest.fixture
def couchdb_client():
    """Create a CouchDBClient for testing."""
    return CouchDBClient(
        server_url="https://test-couch.example.com",
        admin_username="admin",
        admin_password="secret"
    )


@responses.activate
def test_grant_database_access_with_empty_security_doc(couchdb_client):
    """Test granting access when security doc has empty members structure."""
    database = "test-db"
    username = "user-test"

    # Mock GET request - returns security doc with empty members
    responses.add(
        responses.GET,
        "https://test-couch.example.com/test-db/_security",
        json={
            "admins": {"names": [], "roles": []},
            "members": {}  # Missing 'names' and 'roles' keys
        },
        status=200
    )

    # Mock PUT request - should succeed
    responses.add(
        responses.PUT,
        "https://test-couch.example.com/test-db/_security",
        json={"ok": True},
        status=200
    )

    # Should not raise KeyError
    result = couchdb_client.grant_database_access(database, username)
    assert result is True

    # Verify the security doc was updated correctly
    put_call = responses.calls[1]
    assert put_call.request.url == "https://test-couch.example.com/test-db/_security"

    # Verify username was added to members.names
    import json
    body = json.loads(put_call.request.body)
    assert username in body["members"]["names"]


@responses.activate
def test_grant_database_access_with_existing_members(couchdb_client):
    """Test granting access when security doc already has members."""
    database = "test-db"
    username = "user-test"

    # Mock GET request - returns security doc with existing members
    responses.add(
        responses.GET,
        "https://test-couch.example.com/test-db/_security",
        json={
            "admins": {"names": [], "roles": []},
            "members": {"names": ["existing-user"], "roles": []}
        },
        status=200
    )

    # Mock PUT request
    responses.add(
        responses.PUT,
        "https://test-couch.example.com/test-db/_security",
        json={"ok": True},
        status=200
    )

    result = couchdb_client.grant_database_access(database, username)
    assert result is True

    # Verify both users are in members.names
    import json
    put_call = responses.calls[1]
    body = json.loads(put_call.request.body)
    assert "existing-user" in body["members"]["names"]
    assert username in body["members"]["names"]


@responses.activate
def test_grant_database_access_creates_new_security_doc_on_404(couchdb_client):
    """Test creating new security doc when none exists."""
    database = "test-db"
    username = "user-test"

    # Mock GET request - returns 404
    responses.add(
        responses.GET,
        "https://test-couch.example.com/test-db/_security",
        status=404
    )

    # Mock PUT request
    responses.add(
        responses.PUT,
        "https://test-couch.example.com/test-db/_security",
        json={"ok": True},
        status=200
    )

    result = couchdb_client.grant_database_access(database, username)
    assert result is True

    # Verify new security doc was created correctly
    import json
    put_call = responses.calls[1]
    body = json.loads(put_call.request.body)
    assert username in body["members"]["names"]
    assert body["admins"]["names"] == []
    assert body["members"]["roles"] == []
