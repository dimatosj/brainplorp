# ABOUTME: Tests for date utilities - validates date formatting and parsing
# ABOUTME: Tests conversion between Python dates and TaskWarrior date formats
"""Tests for date utilities."""
import pytest
from datetime import date
from plorp.utils.dates import (
    format_date_iso,
    format_date_long,
    parse_taskwarrior_date,
    format_taskwarrior_date_short,
)


def test_format_date_iso():
    """Test ISO date formatting."""
    d = date(2025, 10, 6)
    assert format_date_iso(d) == "2025-10-06"


def test_format_date_long():
    """Test long date formatting."""
    d = date(2025, 10, 6)
    result = format_date_long(d)
    assert result == "October 06, 2025"


def test_parse_taskwarrior_date_valid():
    """Test parsing valid TaskWarrior date."""
    tw_date = "20251006T120000Z"
    result = parse_taskwarrior_date(tw_date)
    assert result == date(2025, 10, 6)


def test_parse_taskwarrior_date_invalid():
    """Test parsing invalid TaskWarrior date."""
    assert parse_taskwarrior_date("invalid") is None
    assert parse_taskwarrior_date("") is None
    assert parse_taskwarrior_date("2025-10-06") is None


def test_format_taskwarrior_date_short_valid():
    """Test formatting valid TaskWarrior date."""
    tw_date = "20251006T120000Z"
    result = format_taskwarrior_date_short(tw_date)
    assert result == "2025-10-06"


def test_format_taskwarrior_date_short_invalid():
    """Test formatting invalid TaskWarrior date returns original."""
    invalid = "not-a-date"
    result = format_taskwarrior_date_short(invalid)
    assert result == invalid


def test_format_date_iso_different_dates():
    """Test ISO formatting with various dates."""
    assert format_date_iso(date(2025, 1, 1)) == "2025-01-01"
    assert format_date_iso(date(2025, 12, 31)) == "2025-12-31"


def test_parse_taskwarrior_date_different_times():
    """Test parsing TaskWarrior dates with different times."""
    # Different times should all give same date
    assert parse_taskwarrior_date("20251006T000000Z") == date(2025, 10, 6)
    assert parse_taskwarrior_date("20251006T235959Z") == date(2025, 10, 6)
