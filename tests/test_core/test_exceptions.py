"""
Tests for plorp.core.exceptions module.

Tests custom exception classes to ensure they include
proper attributes and messages.
"""

import pytest
from plorp.core.exceptions import (
    PlorpError,
    VaultNotFoundError,
    DailyNoteExistsError,
    DailyNoteNotFoundError,
    TaskNotFoundError,
    NoteNotFoundError,
    NoteOutsideVaultError,
    InboxNotFoundError,
)


def test_plorp_error_base_class():
    """Test PlorpError base exception."""
    error = PlorpError("Something went wrong")
    assert str(error) == "Something went wrong"
    assert isinstance(error, Exception)


def test_vault_not_found_error():
    """Test VaultNotFoundError exception."""
    error = VaultNotFoundError("/path/to/vault")

    assert error.vault_path == "/path/to/vault"
    assert "Vault not found" in str(error)
    assert "/path/to/vault" in str(error)
    assert isinstance(error, PlorpError)


def test_daily_note_exists_error():
    """Test DailyNoteExistsError exception."""
    error = DailyNoteExistsError("2025-10-06", "/vault/daily/2025-10-06.md")

    assert error.date == "2025-10-06"
    assert error.note_path == "/vault/daily/2025-10-06.md"
    assert "already exists" in str(error)
    assert isinstance(error, PlorpError)


def test_daily_note_not_found_error():
    """Test DailyNoteNotFoundError exception."""
    error = DailyNoteNotFoundError("2025-10-06")

    assert error.date == "2025-10-06"
    assert "not found" in str(error)
    assert "2025-10-06" in str(error)
    assert isinstance(error, PlorpError)


def test_task_not_found_error():
    """Test TaskNotFoundError exception."""
    error = TaskNotFoundError("abc-123")

    assert error.uuid == "abc-123"
    assert "Task not found" in str(error)
    assert "abc-123" in str(error)
    assert isinstance(error, PlorpError)


def test_note_not_found_error():
    """Test NoteNotFoundError exception."""
    error = NoteNotFoundError("/vault/notes/missing.md")

    assert error.note_path == "/vault/notes/missing.md"
    assert "Note not found" in str(error)
    assert isinstance(error, PlorpError)


def test_note_outside_vault_error():
    """Test NoteOutsideVaultError exception."""
    error = NoteOutsideVaultError("/home/user/note.md", "/vault")

    assert error.note_path == "/home/user/note.md"
    assert error.vault_path == "/vault"
    assert "outside vault" in str(error)
    assert isinstance(error, PlorpError)


def test_inbox_not_found_error():
    """Test InboxNotFoundError exception."""
    error = InboxNotFoundError("/vault/inbox/2025-10.md")

    assert error.inbox_path == "/vault/inbox/2025-10.md"
    assert "Inbox not found" in str(error)
    assert isinstance(error, PlorpError)


def test_exception_can_be_raised_and_caught():
    """Test that exceptions can be raised and caught."""
    with pytest.raises(VaultNotFoundError) as exc_info:
        raise VaultNotFoundError("/missing/vault")

    assert exc_info.value.vault_path == "/missing/vault"


def test_exception_inheritance():
    """Test that all custom exceptions inherit from PlorpError."""
    exceptions = [
        VaultNotFoundError("/path"),
        DailyNoteExistsError("2025-10-06", "/path"),
        DailyNoteNotFoundError("2025-10-06"),
        TaskNotFoundError("uuid"),
        NoteNotFoundError("/path"),
        NoteOutsideVaultError("/note", "/vault"),
        InboxNotFoundError("/inbox"),
    ]

    for exc in exceptions:
        assert isinstance(exc, PlorpError)
        assert isinstance(exc, Exception)
