"""Data parsing utilities."""

import re
from datetime import datetime
from typing import Optional, Tuple


def parse_score(text: str) -> int:
    """
    Parse score text to integer.

    Args:
        text: Score string like "2", "10", etc.

    Returns:
        Integer score, 0 if parsing fails
    """
    if not text:
        return 0
    cleaned = re.sub(r"[^\d]", "", text.strip())
    return int(cleaned) if cleaned else 0


def parse_ht_score(text: str) -> Optional[Tuple[int, int]]:
    """
    Parse half-time score from various formats.

    Supports formats like:
    - (1-0)
    - HT: 1-0
    - 1:0
    - (1:0)

    Args:
        text: Half-time score string

    Returns:
        Tuple of (home_score, away_score) or None if parsing fails
    """
    if not text:
        return None

    # Match patterns like "(1-0)", "1-0", "HT: 1-0", "1:0"
    match = re.search(r"(\d+)\s*[-:]\s*(\d+)", text)
    if match:
        return int(match.group(1)), int(match.group(2))

    return None


def parse_date(date_str: str, format: str = "%d.%m.%Y") -> Optional[datetime]:
    """
    Parse date string to datetime.

    Args:
        date_str: Date string
        format: Date format string

    Returns:
        datetime object or None if parsing fails
    """
    if not date_str:
        return None

    try:
        return datetime.strptime(date_str.strip(), format)
    except ValueError:
        # Try alternative formats
        alt_formats = [
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%d.%m.%Y %H:%M",
            "%d/%m/%Y %H:%M",
        ]
        for alt_format in alt_formats:
            try:
                return datetime.strptime(date_str.strip(), alt_format)
            except ValueError:
                continue

    return None


def parse_attendance(text: str) -> Optional[int]:
    """
    Parse attendance number from text.

    Handles formats like:
    - "45,000"
    - "45000"
    - "45 000"

    Args:
        text: Attendance string

    Returns:
        Integer attendance or None if parsing fails
    """
    if not text:
        return None

    # Remove all non-digit characters
    cleaned = re.sub(r"[^\d]", "", text)

    try:
        return int(cleaned)
    except ValueError:
        return None


def parse_stat_value(value: str) -> Optional[float]:
    """
    Parse statistic value to numeric.

    Handles:
    - Percentages: "60%" -> 60.0
    - Plain numbers: "15" -> 15.0
    - Decimals: "2.5" -> 2.5

    Args:
        value: Statistic value string

    Returns:
        Float value or None if parsing fails
    """
    if not value:
        return None

    # Remove % and other symbols, keep digits and decimal point
    cleaned = re.sub(r"[^\d.]", "", value)

    try:
        return float(cleaned)
    except ValueError:
        return None


def clean_text(text: Optional[str]) -> str:
    """
    Clean text by removing extra whitespace.

    Args:
        text: Input text

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Replace multiple whitespace with single space
    cleaned = re.sub(r"\s+", " ", text.strip())
    return cleaned


def extract_match_id(url: str) -> Optional[str]:
    """
    Extract match ID from Flashscore URL.

    Example:
        https://www.flashscore.com/match/ABC123XYZ/#/match-summary
        -> ABC123XYZ

    Args:
        url: Flashscore match URL

    Returns:
        Match ID or None if extraction fails
    """
    if not url:
        return None

    # Pattern: /match/{id}/
    match = re.search(r"/match/([^/]+)", url)
    if match:
        return match.group(1).rstrip("#")

    return None
