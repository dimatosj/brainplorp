# ABOUTME: Natural language parsing for dates and priority keywords in informal tasks
# ABOUTME: Implements Sprint 7 NLP requirements with case-insensitive, word-boundary matching
"""
NLP Parser for Task Processing (Sprint 7).

Provides natural language parsing for:
- Due dates (today, tomorrow, weekday names)
- Priority keywords (urgent, important, etc.)
- Clean description extraction
"""
import re
from datetime import date, timedelta


def parse_due_date(text: str, reference_date: date) -> tuple[str | None, bool]:
    """
    Extract due date from natural language text.

    Args:
        text: Task text to parse
        reference_date: Reference date for relative parsing (usually today)

    Returns:
        Tuple of (date_string, parsing_succeeded):
        - date_string: YYYY-MM-DD format or None if no date found
        - parsing_succeeded: False if unparseable date detected (NEEDS_REVIEW)

    Supported patterns (case-insensitive, per Q13):
        - "today" → reference_date
        - "tomorrow" → reference_date + 1 day
        - "Friday", "Monday", etc. → next occurrence (skip today per Q12)
        - "next Monday" → next occurrence of Monday

    Examples:
        >>> parse_due_date("call mom today", date(2025, 10, 7))
        ("2025-10-07", True)

        >>> parse_due_date("meeting Friday", date(2025, 10, 6))  # Monday
        ("2025-10-10", True)

        >>> parse_due_date("buy groceries", date(2025, 10, 7))
        (None, True)  # No date found, not an error
    """
    if not text:
        return (None, True)

    text_lower = text.lower()

    # Pattern 1: "today"
    if "today" in text_lower:
        return (reference_date.strftime("%Y-%m-%d"), True)

    # Pattern 2: "tomorrow"
    if "tomorrow" in text_lower:
        tomorrow = reference_date + timedelta(days=1)
        return (tomorrow.strftime("%Y-%m-%d"), True)

    # Pattern 3: Weekday names (Monday, Tuesday, etc.)
    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    # Check for "next [weekday]" pattern
    next_pattern_found = False
    for weekday_name in weekdays.keys():
        if f"next {weekday_name}" in text_lower:
            # "next Monday" always means next occurrence (7 days if today is Monday)
            target_weekday = weekdays[weekday_name]
            current_weekday = reference_date.weekday()
            days_ahead = (target_weekday - current_weekday) % 7
            if days_ahead == 0:
                days_ahead = 7  # Skip today, go to next week (Q12)
            target_date = reference_date + timedelta(days=days_ahead)
            return (target_date.strftime("%Y-%m-%d"), True)

    # Check for standalone weekday names
    for weekday_name, weekday_num in weekdays.items():
        # Use word boundaries to avoid matching partial words
        if re.search(rf"\b{weekday_name}\b", text_lower):
            current_weekday = reference_date.weekday()
            days_ahead = (weekday_num - current_weekday) % 7

            # Q12: If same weekday, skip to next occurrence
            if days_ahead == 0:
                days_ahead = 7

            target_date = reference_date + timedelta(days=days_ahead)
            return (target_date.strftime("%Y-%m-%d"), True)

    # Check for unparseable date patterns
    # If there's text after date prepositions that we couldn't parse, mark as error
    date_preposition_pattern = r"\b(on|by|at)\s+(\S+)"
    preposition_match = re.search(date_preposition_pattern, text_lower)
    if preposition_match:
        # Found a date preposition, but didn't match any known patterns
        # This suggests an unparseable date (e.g., "on Invalid-Date")
        return (None, False)

    # No date pattern found - this is OK, not an error
    return (None, True)


def parse_priority_keywords(text: str) -> str:
    """
    Infer priority from keywords in text.

    Args:
        text: Task text to parse

    Returns:
        Priority level: "H" (high), "M" (medium), or "L" (low)

    Keyword mapping (case-insensitive, word boundaries per Q14):
        - "urgent", "critical", "asap" → "H"
        - "important" → "M"
        - default → "L"

    Examples:
        >>> parse_priority_keywords("urgent task")
        "H"

        >>> parse_priority_keywords("important meeting")
        "M"

        >>> parse_priority_keywords("buy groceries")
        "L"
    """
    if not text:
        return "L"

    text_lower = text.lower()

    # High priority keywords (word boundaries to avoid false positives like "urgently")
    if re.search(r"\b(urgent|critical|asap)\b", text_lower):
        return "H"

    # Medium priority keywords
    if re.search(r"\b(important)\b", text_lower):
        return "M"

    # Default priority
    return "L"


def extract_clean_description(text: str, parsed_date_keyword: str | None) -> str:
    """
    Remove date and priority keywords from description.

    Args:
        text: Original task text
        parsed_date_keyword: The date keyword that was parsed (e.g., "today", "friday")
                            None if no date was parsed

    Returns:
        Cleaned description with keywords removed

    Behavior (per Q15):
        - Remove only the parsed date keyword (keep other date words)
        - Remove all priority keywords
        - Clean up extra whitespace
        - Case-insensitive removal

    Examples:
        >>> extract_clean_description("call mom today", "today")
        "call mom"

        >>> extract_clean_description("call mom today about Friday meeting", "today")
        "call mom about Friday meeting"

        >>> extract_clean_description("urgent task to complete", None)
        "task to complete"
    """
    if not text:
        return ""

    cleaned = text

    # Remove the parsed date keyword (case-insensitive)
    if parsed_date_keyword:
        # Use word boundaries and case-insensitive flag
        pattern = rf"\b{re.escape(parsed_date_keyword)}\b"
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Remove priority keywords (always remove these)
    priority_keywords = ["urgent", "critical", "asap", "important"]
    for keyword in priority_keywords:
        pattern = rf"\b{keyword}\b"
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Remove common connecting words that may be left over
    # e.g., "call mom on today" → "call mom on" → "call mom"
    cleaned = re.sub(r"\b(on|at|by|for)\s*$", "", cleaned, flags=re.IGNORECASE)

    # Clean up extra whitespace
    cleaned = re.sub(r"\s+", " ", cleaned)  # Multiple spaces → single space
    cleaned = cleaned.strip()  # Remove leading/trailing spaces

    return cleaned


# Future expansion placeholders (Sprint 8+)

def parse_project_hints(text: str) -> str | None:
    """
    Extract project from text (placeholder for Sprint 8).

    Examples:
        "work on plorp" → "plorp"
        "project:home cleanup" → "home"
    """
    # TODO: Implement in Sprint 8
    return None


def parse_tags(text: str) -> list[str]:
    """
    Extract tags from text (placeholder for Sprint 8).

    Examples:
        "#important task" → ["important"]
        "meeting #work #urgent" → ["work", "urgent"]
    """
    # TODO: Implement in Sprint 8
    return []
