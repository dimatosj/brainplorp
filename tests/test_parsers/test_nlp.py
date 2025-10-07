# ABOUTME: Tests for NLP parsing of dates and priority keywords from informal task text
# ABOUTME: Covers Sprint 7 natural language parsing requirements
"""
Tests for NLP parser module.

Comprehensive test coverage for date and priority keyword parsing.
"""
from datetime import date
import pytest
from plorp.parsers.nlp import (
    parse_due_date,
    parse_priority_keywords,
    extract_clean_description,
)


# ============================================================================
# Date Parsing Tests
# ============================================================================


def test_parse_due_date_today():
    """Test parsing 'today' keyword."""
    reference = date(2025, 10, 7)  # Monday
    result, ok = parse_due_date("call mom today", reference)
    assert result == "2025-10-07"
    assert ok is True


def test_parse_due_date_today_case_insensitive():
    """Test 'today' with different cases (Q13)."""
    reference = date(2025, 10, 7)

    for text in ["call TODAY", "call Today", "call today"]:
        result, ok = parse_due_date(text, reference)
        assert result == "2025-10-07"
        assert ok is True


def test_parse_due_date_tomorrow():
    """Test parsing 'tomorrow' keyword."""
    reference = date(2025, 10, 7)  # Monday
    result, ok = parse_due_date("finish report tomorrow", reference)
    assert result == "2025-10-08"
    assert ok is True


def test_parse_due_date_tomorrow_case_insensitive():
    """Test 'tomorrow' case insensitive."""
    reference = date(2025, 10, 7)
    result, ok = parse_due_date("finish TOMORROW", reference)
    assert result == "2025-10-08"
    assert ok is True


def test_parse_due_date_friday_from_monday():
    """Test 'Friday' from Monday reference (Q12 example)."""
    reference = date(2025, 10, 7)  # Tuesday Oct 7 (actually this is a Tuesday, let me fix)
    # Wait, let me verify: Oct 7, 2025 is actually a Tuesday
    # Spec says Oct 7 is Monday, but let's check the actual calendar
    # For testing, I'll use the spec's assumption that we can parse relative to reference_date
    # Let me use a known Monday: Oct 6, 2025 is a Monday
    reference = date(2025, 10, 6)  # Monday
    result, ok = parse_due_date("meeting on Friday", reference)
    assert result == "2025-10-10"  # Friday Oct 10
    assert ok is True


def test_parse_due_date_friday_when_today_is_friday():
    """Test 'Friday' when reference date is Friday - should return next Friday (Q12)."""
    reference = date(2025, 10, 10)  # Friday
    result, ok = parse_due_date("meeting Friday", reference)
    assert result == "2025-10-17"  # Next Friday (7 days later)
    assert ok is True


def test_parse_due_date_next_monday():
    """Test 'next Monday' from Monday (Q12)."""
    reference = date(2025, 10, 6)  # Monday
    result, ok = parse_due_date("review next Monday", reference)
    assert result == "2025-10-13"  # Next Monday (7 days)
    assert ok is True


def test_parse_due_date_next_monday_from_friday():
    """Test 'next Monday' from Friday."""
    reference = date(2025, 10, 10)  # Friday
    result, ok = parse_due_date("standup next Monday", reference)
    assert result == "2025-10-13"  # Following Monday
    assert ok is True


def test_parse_due_date_all_weekdays():
    """Test all weekday names are parsed correctly."""
    reference = date(2025, 10, 6)  # Monday

    # Expected dates for next occurrence of each weekday from Monday Oct 6
    expected = {
        "monday": "2025-10-13",  # Next Monday (skip today per Q12)
        "tuesday": "2025-10-07",
        "wednesday": "2025-10-08",
        "thursday": "2025-10-09",
        "friday": "2025-10-10",
        "saturday": "2025-10-11",
        "sunday": "2025-10-12",
    }

    for weekday, expected_date in expected.items():
        result, ok = parse_due_date(f"task on {weekday}", reference)
        assert result == expected_date, f"Failed for {weekday}"
        assert ok is True


def test_parse_due_date_invalid_date_text():
    """Test unparseable date text triggers NEEDS_REVIEW (parsing failure).

    If text contains date prepositions (on, by, at) followed by text
    that doesn't match any known pattern, it's marked as parsing failed.
    This triggers NEEDS_REVIEW in Step 1.
    """
    reference = date(2025, 10, 7)
    result, ok = parse_due_date("call on Invalid-Date", reference)
    assert result is None
    assert ok is False  # Parsing failed - triggers NEEDS_REVIEW


def test_parse_due_date_no_date_in_text():
    """Test text without date returns (None, True) - not an error."""
    reference = date(2025, 10, 7)
    result, ok = parse_due_date("buy groceries", reference)
    assert result is None
    assert ok is True


def test_parse_due_date_with_punctuation():
    """Test date parsing handles punctuation (Q14)."""
    reference = date(2025, 10, 7)

    # Should still match despite punctuation
    result, ok = parse_due_date("meeting today!", reference)
    assert result == "2025-10-07"
    assert ok is True

    result, ok = parse_due_date("urgent!!! tomorrow!!!", reference)
    assert result == "2025-10-08"
    assert ok is True


# ============================================================================
# Priority Parsing Tests
# ============================================================================


def test_parse_priority_urgent():
    """Test 'urgent' keyword → H priority."""
    assert parse_priority_keywords("urgent task") == "H"


def test_parse_priority_critical():
    """Test 'critical' keyword → H priority."""
    assert parse_priority_keywords("critical bug") == "H"


def test_parse_priority_asap():
    """Test 'asap' keyword → H priority."""
    assert parse_priority_keywords("fix asap") == "H"


def test_parse_priority_important():
    """Test 'important' keyword → M priority."""
    assert parse_priority_keywords("important meeting") == "M"


def test_parse_priority_default():
    """Test no keywords → L priority."""
    assert parse_priority_keywords("buy groceries") == "L"
    assert parse_priority_keywords("random task with no priority words") == "L"


def test_parse_priority_case_insensitive():
    """Test priority keywords are case-insensitive (Q13)."""
    assert parse_priority_keywords("URGENT task") == "H"
    assert parse_priority_keywords("Urgent task") == "H"
    assert parse_priority_keywords("uRgEnT task") == "H"

    assert parse_priority_keywords("IMPORTANT") == "M"
    assert parse_priority_keywords("Important") == "M"


def test_parse_priority_with_punctuation():
    """Test priority keywords with punctuation (Q14)."""
    assert parse_priority_keywords("urgent!") == "H"
    assert parse_priority_keywords("urgent!!!") == "H"
    assert parse_priority_keywords("URGENT???") == "H"
    assert parse_priority_keywords("critical!!!") == "H"


def test_parse_priority_word_boundaries():
    """Test word boundary matching - 'urgently' should NOT match (Q14)."""
    # 'urgently' is different word, should not match 'urgent'
    assert parse_priority_keywords("do this urgently") == "L"

    # But 'urgent' as whole word should match
    assert parse_priority_keywords("urgent task") == "H"


def test_parse_priority_multiple_keywords():
    """Test multiple keywords - first/highest wins (Q14)."""
    # Has both urgent and important, urgent is H priority (higher)
    assert parse_priority_keywords("urgent and important task") == "H"
    assert parse_priority_keywords("important and urgent task") == "H"


# ============================================================================
# Clean Description Tests
# ============================================================================


def test_extract_clean_description_remove_today():
    """Test removing 'today' from description."""
    result = extract_clean_description("call mom today", "today")
    assert result == "call mom"


def test_extract_clean_description_remove_tomorrow():
    """Test removing 'tomorrow' from description."""
    result = extract_clean_description("finish report tomorrow", "tomorrow")
    assert result == "finish report"


def test_extract_clean_description_remove_friday():
    """Test removing weekday name from description.

    Note: Trailing prepositions like "on", "at", "by" are also removed
    to avoid awkward phrasing like "meeting on" → cleaned to "meeting".
    """
    result = extract_clean_description("meeting on Friday", "friday")
    assert result == "meeting"  # "on" is also removed (trailing preposition)


def test_extract_clean_description_keep_other_dates():
    """Test keeping non-parsed date words in description (Q15)."""
    # Parsed 'today', keep 'Friday'
    result = extract_clean_description("call mom today about Friday meeting", "today")
    assert "Friday" in result
    assert "today" not in result.lower()


def test_extract_clean_description_remove_priority_keywords():
    """Test removing priority keywords from description."""
    result = extract_clean_description("urgent task to complete", None)
    # Should remove 'urgent'
    assert "urgent" not in result.lower()


def test_extract_clean_description_no_date():
    """Test description with no date to remove."""
    result = extract_clean_description("buy groceries", None)
    assert result == "buy groceries"


def test_extract_clean_description_strip_whitespace():
    """Test extra whitespace is cleaned up after removal."""
    result = extract_clean_description("call mom  today  ", "today")
    # Should not have trailing spaces or double spaces
    assert result.strip() == result
    assert "  " not in result


def test_extract_clean_description_case_insensitive():
    """Test case-insensitive removal."""
    result = extract_clean_description("call mom TODAY", "today")
    assert "today" not in result.lower()
    assert result.strip() == "call mom"


# ============================================================================
# Edge Cases
# ============================================================================


def test_parse_due_date_empty_string():
    """Test empty string input."""
    reference = date(2025, 10, 7)
    result, ok = parse_due_date("", reference)
    assert result is None
    assert ok is True  # Not an error, just no date


def test_parse_priority_keywords_empty_string():
    """Test empty string → default priority."""
    assert parse_priority_keywords("") == "L"


def test_extract_clean_description_empty():
    """Test empty description."""
    result = extract_clean_description("", None)
    assert result == ""
