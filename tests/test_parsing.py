"""Tests for parsing utilities."""

import pytest
from datetime import datetime

from src.flashscore_scraper.utils.parsing import (
    parse_score,
    parse_ht_score,
    parse_date,
    parse_attendance,
    parse_stat_value,
    clean_text,
    extract_match_id,
)


class TestParseScore:
    """Tests for parse_score function."""

    def test_parse_basic_score(self):
        assert parse_score("2") == 2
        assert parse_score("10") == 10
        assert parse_score("0") == 0

    def test_parse_empty_score(self):
        assert parse_score("") == 0
        assert parse_score(None) == 0

    def test_parse_score_with_noise(self):
        assert parse_score("2 ") == 2
        assert parse_score(" 3") == 3
        assert parse_score("(1)") == 1


class TestParseHTScore:
    """Tests for parse_ht_score function."""

    def test_parse_standard_format(self):
        assert parse_ht_score("(1-0)") == (1, 0)
        assert parse_ht_score("(2-2)") == (2, 2)
        assert parse_ht_score("(0-3)") == (0, 3)

    def test_parse_ht_prefix(self):
        assert parse_ht_score("HT: 1-0") == (1, 0)
        assert parse_ht_score("HT 2-1") == (2, 1)

    def test_parse_colon_format(self):
        assert parse_ht_score("1:0") == (1, 0)
        assert parse_ht_score("(1:0)") == (1, 0)

    def test_parse_with_spaces(self):
        assert parse_ht_score("( 1 - 0 )") == (1, 0)
        assert parse_ht_score("1 - 0") == (1, 0)

    def test_parse_empty(self):
        assert parse_ht_score("") is None
        assert parse_ht_score(None) is None


class TestParseDate:
    """Tests for parse_date function."""

    def test_parse_standard_format(self):
        date = parse_date("31.12.2024")
        assert date.day == 31
        assert date.month == 12
        assert date.year == 2024

    def test_parse_alternative_formats(self):
        date1 = parse_date("31/12/2024", "%d/%m/%Y")
        assert date1.day == 31

        date2 = parse_date("2024-12-31", "%Y-%m-%d")
        assert date2.year == 2024

    def test_parse_invalid(self):
        assert parse_date("invalid") is None
        assert parse_date("") is None


class TestParseAttendance:
    """Tests for parse_attendance function."""

    def test_parse_with_commas(self):
        assert parse_attendance("45,000") == 45000
        assert parse_attendance("75,000") == 75000

    def test_parse_with_spaces(self):
        assert parse_attendance("45 000") == 45000

    def test_parse_plain_number(self):
        assert parse_attendance("45000") == 45000

    def test_parse_invalid(self):
        assert parse_attendance("N/A") == 0
        assert parse_attendance("") is None


class TestParseStatValue:
    """Tests for parse_stat_value function."""

    def test_parse_percentage(self):
        assert parse_stat_value("60%") == 60.0
        assert parse_stat_value("45.5%") == 45.5

    def test_parse_plain_number(self):
        assert parse_stat_value("15") == 15.0
        assert parse_stat_value("2.5") == 2.5

    def test_parse_invalid(self):
        assert parse_stat_value("N/A") == 0.0
        assert parse_stat_value("") is None


class TestCleanText:
    """Tests for clean_text function."""

    def test_clean_extra_whitespace(self):
        assert clean_text("  Hello   World  ") == "Hello World"
        assert clean_text("Test\n\nText") == "Test Text"

    def test_clean_empty(self):
        assert clean_text("") == ""
        assert clean_text(None) == ""


class TestExtractMatchID:
    """Tests for extract_match_id function."""

    def test_extract_standard_url(self):
        url = "https://www.flashscore.com/match/ABC123XYZ/#/match-summary"
        assert extract_match_id(url) == "ABC123XYZ"

    def test_extract_without_fragment(self):
        url = "https://www.flashscore.com/match/DEF456/"
        assert extract_match_id(url) == "DEF456"

    def test_extract_invalid(self):
        assert extract_match_id("https://www.flashscore.com/") is None
        assert extract_match_id("") is None
