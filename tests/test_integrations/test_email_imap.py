"""
Tests for email IMAP integration.

Note: These are unit tests with mocking, not integration tests.
Real Gmail integration testing must be manual.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from brainplorp.integrations.email_imap import (
    connect_gmail,
    fetch_unread_emails,
    mark_emails_as_seen,
    disconnect,
    convert_email_body_to_bullets,
)


@patch("brainplorp.integrations.email_imap.imaplib.IMAP4_SSL")
def test_connect_gmail_success(mock_imap):
    """Test successful Gmail connection."""
    mock_client = Mock()
    mock_imap.return_value = mock_client
    mock_client.login.return_value = ("OK", [b"Success"])

    client = connect_gmail("user@gmail.com", "password")

    assert client == mock_client
    mock_imap.assert_called_once_with("imap.gmail.com", 993)
    mock_client.login.assert_called_once_with("user@gmail.com", "password")


@patch("brainplorp.integrations.email_imap.imaplib.IMAP4_SSL")
def test_connect_gmail_auth_failure(mock_imap):
    """Test Gmail connection with bad credentials."""
    mock_client = Mock()
    mock_imap.return_value = mock_client
    mock_client.login.side_effect = Exception("Authentication failed")

    with pytest.raises(Exception, match="Authentication failed"):
        connect_gmail("user@gmail.com", "bad_password")


def test_fetch_unread_emails_empty():
    """Test fetching when no unread emails exist."""
    mock_client = Mock()
    mock_client.select.return_value = ("OK", [])
    mock_client.search.return_value = ("OK", [b""])

    emails = fetch_unread_emails(mock_client, "INBOX", limit=20)

    assert emails == []
    mock_client.select.assert_called_once_with("INBOX", readonly=False)
    mock_client.search.assert_called_once_with(None, "UNSEEN")


def test_mark_emails_as_seen():
    """Test marking emails as SEEN."""
    mock_client = Mock()
    email_ids = ["12345", "67890"]

    mark_emails_as_seen(mock_client, email_ids)

    assert mock_client.store.call_count == 2
    mock_client.store.assert_any_call(b"12345", "+FLAGS", "\\Seen")
    mock_client.store.assert_any_call(b"67890", "+FLAGS", "\\Seen")


def test_disconnect():
    """Test IMAP disconnect."""
    mock_client = Mock()

    disconnect(mock_client)

    mock_client.close.assert_called_once()
    mock_client.logout.assert_called_once()


def test_disconnect_already_closed():
    """Test disconnect when already disconnected."""
    mock_client = Mock()
    mock_client.close.side_effect = Exception("Already closed")

    # Should not raise
    disconnect(mock_client)


def test_convert_email_body_plain_text_with_bullets():
    """Test preserving existing markdown bullets."""
    body_text = "- Task 1\n  - Subtask A\n- Task 2"
    body_html = ""
    result = convert_email_body_to_bullets(body_text, body_html)
    assert "- Task 1" in result
    assert "  - Subtask A" in result
    assert "- Task 2" in result


def test_convert_email_body_plain_text_paragraphs():
    """Test converting paragraphs to bullets."""
    body_text = "First paragraph here.\n\nSecond paragraph here."
    body_html = ""
    result = convert_email_body_to_bullets(body_text, body_html)
    assert "- First paragraph here." in result
    assert "- Second paragraph here." in result


def test_convert_email_body_html_list():
    """Test HTML list conversion."""
    body_text = ""
    body_html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
    result = convert_email_body_to_bullets(body_text, body_html)
    # html2text converts <ul><li> to markdown bullets
    assert "Item 1" in result
    assert "Item 2" in result


def test_convert_email_body_empty():
    """Test empty email body."""
    result = convert_email_body_to_bullets("", "")
    assert result == ""


def test_convert_email_body_signature_removal():
    """Test signature removal."""
    body_text = "Important task\n\n-- \nBest regards,\nJohn"
    body_html = ""
    result = convert_email_body_to_bullets(body_text, body_html)
    assert "Important task" in result
    assert "Best regards" not in result
    assert "John" not in result


def test_convert_email_body_html_fallback():
    """Test HTML fallback when html2text not available."""
    # Test with simple HTML that should work with fallback
    body_text = ""
    body_html = "<p>Paragraph 1</p><p>Paragraph 2</p>"

    # We can't easily mock the ImportError for html2text in this test,
    # but we can test that the fallback function works
    from brainplorp.integrations.email_imap import _strip_html_tags

    stripped = _strip_html_tags(body_html)
    assert "Paragraph 1" in stripped
    assert "Paragraph 2" in stripped
    assert "<p>" not in stripped


def test_has_markdown_bullets():
    """Test detection of markdown bullets."""
    from brainplorp.integrations.email_imap import _has_markdown_bullets

    assert _has_markdown_bullets("- Task 1\n- Task 2")
    assert _has_markdown_bullets("* Task 1\n* Task 2")
    assert _has_markdown_bullets("+ Task 1\n+ Task 2")
    assert not _has_markdown_bullets("No bullets here")
    assert not _has_markdown_bullets("Just plain text")


def test_paragraphs_to_bullets():
    """Test paragraph to bullet conversion."""
    from brainplorp.integrations.email_imap import _paragraphs_to_bullets

    text = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
    result = _paragraphs_to_bullets(text)
    assert "- Paragraph 1" in result
    assert "- Paragraph 2" in result
    assert "- Paragraph 3" in result


def test_remove_signature():
    """Test signature removal patterns."""
    from brainplorp.integrations.email_imap import _remove_signature

    text = "Important content\n\n-- \nSignature here"
    result = _remove_signature(text)
    assert "Important content" in result
    assert "Signature here" not in result

    text2 = "Task here\n\nSent from my iPhone"
    result2 = _remove_signature(text2)
    assert "Task here" in result2
    assert "Sent from" not in result2


def test_strip_html_tags():
    """Test HTML tag stripping fallback."""
    from brainplorp.integrations.email_imap import _strip_html_tags

    html = "<html><body><p>Test content</p></body></html>"
    result = _strip_html_tags(html)
    assert "Test content" in result
    assert "<p>" not in result
    assert "<html>" not in result
