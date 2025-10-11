"""
IMAP email client for Gmail inbox fetching.

This module provides Gmail-specific IMAP operations for fetching emails
and extracting body content as markdown bullets.
"""

from typing import List, Dict, Any
import imaplib
from email import policy
from email.parser import BytesParser
import re
import html as html_module


def connect_gmail(
    username: str, password: str, server: str = "imap.gmail.com", port: int = 993
) -> imaplib.IMAP4_SSL:
    """
    Connect to Gmail IMAP server.

    Args:
        username: Gmail address
        password: Gmail App Password (16-char, no spaces)
        server: IMAP server hostname
        port: IMAP SSL port

    Returns:
        Connected IMAP4_SSL client

    Raises:
        imaplib.IMAP4.error: If connection or login fails
    """
    client = imaplib.IMAP4_SSL(server, port)
    client.login(username, password)
    return client


def fetch_unread_emails(
    client: imaplib.IMAP4_SSL, folder: str = "INBOX", limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Fetch unread emails and extract body content.

    Args:
        client: Connected IMAP client
        folder: Folder/label name (e.g., "INBOX", "[Gmail]/plorp")
        limit: Maximum number of emails to fetch

    Returns:
        List of email dicts with keys: id, body_text, body_html

    Example:
        [
            {
                "id": "12345",
                "body_text": "- Task 1\n- Task 2",
                "body_html": "<ul><li>Task 1</li></ul>"
            }
        ]
    """
    client.select(folder, readonly=False)  # Need write access to mark as SEEN

    # Search for unseen emails
    status, message_ids = client.search(None, "UNSEEN")
    if status != "OK":
        return []

    email_ids = message_ids[0].split()
    if not email_ids:
        return []

    # Apply limit
    email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids

    emails = []
    for email_id in email_ids:
        status, msg_data = client.fetch(email_id, "(RFC822)")
        if status != "OK":
            continue

        # Parse email
        raw_email = msg_data[0][1]
        msg = BytesParser(policy=policy.default).parsebytes(raw_email)

        # Extract body content (both plain text and HTML)
        body_text = ""
        body_html = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body_text = part.get_content()
                elif content_type == "text/html":
                    body_html = part.get_content()
        else:
            if msg.get_content_type() == "text/plain":
                body_text = msg.get_content()
            elif msg.get_content_type() == "text/html":
                body_html = msg.get_content()

        emails.append(
            {
                "id": email_id.decode(),
                "body_text": body_text.strip() if body_text else "",
                "body_html": body_html.strip() if body_html else "",
            }
        )

    return emails


def convert_email_body_to_bullets(body_text: str, body_html: str) -> str:
    """
    Convert email body to markdown bullets.

    Priority: Use plain text if it has bullets, otherwise use HTML if available,
    otherwise convert plain text paragraphs to bullets.

    Args:
        body_text: Plain text email body
        body_html: HTML email body

    Returns:
        Markdown formatted bullets

    Examples:
        # Plain text with bullets
        "- Task 1\\n  - Subtask\\n- Task 2"
        → "- Task 1\\n  - Subtask\\n- Task 2"

        # Plain text paragraphs
        "Paragraph 1\\n\\nParagraph 2"
        → "- Paragraph 1\\n- Paragraph 2"

        # HTML list
        "<ul><li>Item 1</li></ul>"
        → "- Item 1"
    """
    # Strategy 1: Check if plain text already has bullets
    if body_text and _has_markdown_bullets(body_text):
        return _clean_text_content(body_text)

    # Strategy 2: Try HTML conversion if available
    if body_html:
        try:
            import html2text

            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = True
            markdown = h.handle(body_html)
            return _clean_text_content(markdown)
        except ImportError:
            # Fallback: basic HTML stripping
            text = _strip_html_tags(body_html)
            return _paragraphs_to_bullets(text)

    # Strategy 3: Convert plain text paragraphs to bullets
    if body_text:
        return _paragraphs_to_bullets(body_text)

    return ""


def _has_markdown_bullets(text: str) -> bool:
    """Check if text already contains markdown bullets (-, *, +)."""
    lines = text.split("\n")
    bullet_lines = [l for l in lines if l.strip().startswith(("-", "*", "+"))]
    return len(bullet_lines) > 0


def _paragraphs_to_bullets(text: str) -> str:
    """Convert paragraphs to bullets."""
    # Remove email signatures (common patterns)
    text = _remove_signature(text)

    # Split into paragraphs (double newline or more)
    paragraphs = re.split(r"\n\s*\n", text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    # Convert each paragraph to bullet
    bullets = [f"- {p}" for p in paragraphs]
    return "\n".join(bullets)


def _clean_text_content(text: str) -> str:
    """Clean up extracted text content."""
    # Remove email signatures
    text = _remove_signature(text)

    # Remove excessive blank lines
    text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)

    return text.strip()


def _remove_signature(text: str) -> str:
    """Best-effort removal of email signatures."""
    # Common signature markers
    signature_markers = [
        "-- ",  # Standard signature separator
        "___",
        "Sent from",
        "Best regards",
        "Thanks",
        "Cheers",
    ]

    for marker in signature_markers:
        if marker in text:
            # Remove everything after marker
            text = text.split(marker)[0]
            break

    return text.strip()


def _strip_html_tags(html: str) -> str:
    """Fallback HTML stripper if html2text not available."""
    # Remove script and style elements
    text = re.sub(
        r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE
    )
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode HTML entities
    text = html_module.unescape(text)
    # Clean up whitespace
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()


def mark_emails_as_seen(client: imaplib.IMAP4_SSL, email_ids: List[str]) -> None:
    """
    Mark emails as SEEN (read) to avoid re-fetching.

    Args:
        client: Connected IMAP client
        email_ids: List of email IDs to mark
    """
    for email_id in email_ids:
        client.store(email_id.encode(), "+FLAGS", "\\Seen")


def disconnect(client: imaplib.IMAP4_SSL) -> None:
    """Close IMAP connection."""
    try:
        client.close()
        client.logout()
    except:
        pass  # Already disconnected
