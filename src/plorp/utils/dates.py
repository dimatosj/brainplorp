# ABOUTME: Date formatting utilities for consistent date handling across plorp
# ABOUTME: Converts between Python dates and TaskWarrior/Obsidian date formats
"""
Date utilities.

Helper functions for date formatting and conversion.
"""
from datetime import date, datetime
from typing import Optional


def format_date_iso(d: date) -> str:
    """
    Format date as ISO string (YYYY-MM-DD).

    Args:
        d: Date to format

    Returns:
        ISO formatted date string

    Example:
        >>> from datetime import date
        >>> format_date_iso(date(2025, 10, 6))
        '2025-10-06'
    """
    return d.strftime("%Y-%m-%d")


def format_date_long(d: date) -> str:
    """
    Format date as long string (Month DD, YYYY).

    Args:
        d: Date to format

    Returns:
        Long formatted date string

    Example:
        >>> format_date_long(date(2025, 10, 6))
        'October 06, 2025'
    """
    return d.strftime("%B %d, %Y")


def parse_taskwarrior_date(tw_date: str) -> Optional[date]:
    """
    Parse TaskWarrior date format (YYYYMMDDTHHMMSSZ) to Python date.

    Args:
        tw_date: TaskWarrior date string

    Returns:
        Python date object, or None if parsing fails

    Example:
        >>> parse_taskwarrior_date('20251006T120000Z')
        date(2025, 10, 6)
    """
    try:
        dt = datetime.strptime(tw_date, "%Y%m%dT%H%M%SZ")
        return dt.date()
    except (ValueError, AttributeError):
        return None


def format_taskwarrior_date_short(tw_date: str) -> str:
    """
    Format TaskWarrior date to short string (YYYY-MM-DD).

    Args:
        tw_date: TaskWarrior date string

    Returns:
        Short formatted date, or original string if parsing fails

    Example:
        >>> format_taskwarrior_date_short('20251006T120000Z')
        '2025-10-06'
    """
    parsed = parse_taskwarrior_date(tw_date)
    if parsed:
        return format_date_iso(parsed)
    return tw_date
