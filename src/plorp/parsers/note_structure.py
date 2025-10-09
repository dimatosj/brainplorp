# ABOUTME: Parser for markdown note structure - headers, bullets, tags, project detection
# ABOUTME: Pattern matching functions for analyzing note content and structure
"""
Note structure parsing for plorp.

Provides functions to extract and analyze markdown structure:
- Headers and sections
- Bullet points
- Inline tags
- Project-like headers (heuristic detection)

All functions are pure - no side effects, just parsing.
"""

import re
from typing import List, Dict, Any


def extract_headers(content: str, level: int | None = None) -> List[Dict[str, Any]]:
    """
    Extract all headers from markdown content.

    Args:
        content: Markdown text
        level: Filter by header level (1-6), None = all levels

    Returns:
        List of Header dicts with text, level, line_number

    Example:
        >>> content = "# Title\\n\\n## Section 1\\n\\n### Subsection"
        >>> headers = extract_headers(content, level=2)
        >>> headers[0]["text"]
        'Section 1'
    """
    headers = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines):
        # Match markdown headers (# Header)
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if match:
            header_level = len(match.group(1))  # Count # symbols
            header_text = match.group(2).strip()

            # Filter by level if specified
            if level is None or header_level == level:
                headers.append(
                    {
                        "text": header_text,
                        "level": header_level,
                        "line_number": line_num,
                    }
                )

    return headers


def find_header_content(content: str, header: str) -> str:
    """
    Get content under specific header (until next same-level header).

    Args:
        content: Markdown text
        header: Header text to find (without # prefix)

    Returns:
        Content under header (empty string if header not found)

    Example:
        >>> content = "## Goals\\n\\nBe awesome\\n\\n## Next"
        >>> find_header_content(content, "Goals")
        '\\nBe awesome\\n\\n'
    """
    lines = content.split("\n")

    # Find header line and level
    header_pattern = re.compile(r"^(#{1,6})\s+" + re.escape(header) + r"\s*$")
    header_line = None
    header_level = None

    for i, line in enumerate(lines):
        match = header_pattern.match(line)
        if match:
            header_line = i
            header_level = len(match.group(1))
            break

    if header_line is None:
        return ""

    # Find next header at same or higher level
    next_header = len(lines)
    for i in range(header_line + 1, len(lines)):
        # Check if line is a header
        header_match = re.match(r"^(#{1,6})\s+", lines[i])
        if header_match:
            next_level = len(header_match.group(1))
            # Stop at same or higher level header
            if next_level <= header_level:
                next_header = i
                break

    # Extract content between header and next header
    section_lines = lines[header_line + 1 : next_header]
    return "\n".join(section_lines)


def detect_project_headers(content: str) -> List[str]:
    """
    Find ### headers that look like project names.

    Pattern matching heuristics:
    - Level 3 headers (###)
    - Not in "Notes" or "Tasks" sections
    - Title-case or kebab-case format
    - Not common section names (Overview, Summary, etc.)

    Args:
        content: Markdown text (typically from daily note)

    Returns:
        List of potential project names

    Example:
        >>> content = "### Website Redesign\\n\\n### Tasks\\n\\n### api-rewrite"
        >>> detect_project_headers(content)
        ['Website Redesign', 'api-rewrite']
    """
    # Common section names to exclude (not projects)
    EXCLUDED_HEADERS = {
        "notes",
        "tasks",
        "overview",
        "summary",
        "goals",
        "done",
        "todo",
        "completed",
        "in progress",
        "blocked",
        "backlog",
        "questions",
        "ideas",
        "meetings",
        "links",
        "references",
    }

    headers = extract_headers(content, level=3)
    projects = []

    for header in headers:
        text = header["text"]
        text_lower = text.lower()

        # Exclude common section names
        if text_lower in EXCLUDED_HEADERS:
            continue

        # Heuristic: Projects are often Title Case or kebab-case
        # Accept if:
        # - Contains uppercase letter (Title Case) OR
        # - Contains hyphen (kebab-case)
        has_uppercase = any(c.isupper() for c in text)
        has_hyphen = "-" in text

        if has_uppercase or has_hyphen:
            projects.append(text)

    return projects


def extract_bullet_points(content: str, section: str | None = None) -> List[str]:
    """
    Get all bullet points (- or *), optionally under specific section.

    Args:
        content: Markdown text
        section: Header name to extract bullets from (None = all bullets)

    Returns:
        List of bullet text (without - prefix)

    Example:
        >>> content = "## Tasks\\n\\n- Buy milk\\n- Call Bob"
        >>> extract_bullet_points(content, section="Tasks")
        ['Buy milk', 'Call Bob']
    """
    # If section specified, extract only that section's content
    if section is not None:
        content = find_header_content(content, section)

    bullets = []
    lines = content.split("\n")

    for line in lines:
        # Match bullet points (- or * at start, optional whitespace)
        match = re.match(r"^\s*[-*]\s+(.+)$", line)
        if match:
            bullet_text = match.group(1).strip()
            bullets.append(bullet_text)

    return bullets


def extract_tags(content: str) -> List[str]:
    """
    Extract all #tags from content (Obsidian-style inline tags).

    Args:
        content: Markdown text

    Returns:
        List of unique tags (without # prefix)

    Example:
        >>> content = "This is #important and #urgent"
        >>> extract_tags(content)
        ['important', 'urgent']
    """
    # Pattern: # followed by word characters (letters, numbers, underscore, hyphen)
    # Not inside code blocks or inline code
    tag_pattern = r"(?:^|[^`])#([\w-]+)"
    matches = re.findall(tag_pattern, content, re.MULTILINE)

    # Return unique tags (preserve order)
    seen = set()
    unique_tags = []
    for tag in matches:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)

    return unique_tags
