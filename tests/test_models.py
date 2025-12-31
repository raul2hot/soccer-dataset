"""Tests for data models."""

import pytest
from datetime import datetime

from src.flashscore_scraper.models import (
    Score,
    Team,
    Match,
    MatchStatus,
    MatchResult,
)


class TestScore:
    """Tests for Score model."""

    def test_score_creation(self):
        score = Score(home=2, away=1)
        assert score.home == 2
        assert score.away == 1

    def test_score_total(self):
        score = Score(home=2, away=1)
        assert score.total == 3

    def test_score_diff(self):
        score = Score(home=2, away=1)
        assert score.diff == 1

    def test_score_result(self):
        assert Score(home=2, away=1).result == "H"
        assert Score(home=1, away=2).result == "A"
        assert Score(home=1, away=1).result == "D"

    def test_score_string(self):
        score = Score(home=2, away=1)
        assert str(score) == "2-1"


class TestTeam:
    """Tests for Team model."""

    def test_team_creation(self):
        team = Team(name="Arsenal")
        assert team.name == "Arsenal"
        assert team.flashscore_id is None

    def test_team_string(self):
        team = Team(name="Liverpool")
        assert str(team) == "Liverpool"


class TestMatchResult:
    """Tests for MatchResult model."""

    def test_empty_result(self):
        result = MatchResult()
        assert result.half_time is None
        assert result.full_time is None

    def test_result_with_scores(self):
        result = MatchResult(
            half_time=Score(1, 0),
            full_time=Score(2, 1),
        )
        assert result.half_time.home == 1
        assert result.full_time.home == 2


class TestMatch:
    """Tests for Match model."""

    def test_match_creation(self):
        match = Match(
            match_id="ABC123",
            url="https://flashscore.com/match/ABC123/",
            country="England",
            league="Premier League",
            season="2023-2024",
            stage="Round 1",
            date=datetime(2024, 1, 1),
            status=MatchStatus.FINISHED,
            home_team=Team("Arsenal"),
            away_team=Team("Liverpool"),
            result=MatchResult(
                half_time=Score(1, 0),
                full_time=Score(2, 1),
            ),
        )

        assert match.match_id == "ABC123"
        assert match.home_team.name == "Arsenal"
        assert match.result.full_time.home == 2

    def test_match_string(self):
        match = Match(
            match_id="ABC123",
            url="test",
            country="England",
            league="Premier League",
            season="2023-2024",
            stage=None,
            date=datetime.utcnow(),
            status=MatchStatus.FINISHED,
            home_team=Team("Arsenal"),
            away_team=Team("Liverpool"),
            result=MatchResult(full_time=Score(2, 1)),
        )

        assert "Arsenal" in str(match)
        assert "Liverpool" in str(match)
        assert "2-1" in str(match)
