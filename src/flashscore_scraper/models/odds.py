"""Betting odds data model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Odds:
    """Pre-match betting odds from various markets."""

    # Match winner (1X2)
    home_win: Optional[float] = None
    draw: Optional[float] = None
    away_win: Optional[float] = None

    # Over/Under goals
    over_0_5: Optional[float] = None
    under_0_5: Optional[float] = None
    over_1_5: Optional[float] = None
    under_1_5: Optional[float] = None
    over_2_5: Optional[float] = None
    under_2_5: Optional[float] = None
    over_3_5: Optional[float] = None
    under_3_5: Optional[float] = None

    # Both Teams to Score (BTTS)
    btts_yes: Optional[float] = None
    btts_no: Optional[float] = None

    # Asian Handicap
    asian_handicap_line: Optional[float] = None
    asian_handicap_home: Optional[float] = None
    asian_handicap_away: Optional[float] = None

    # Double Chance
    home_or_draw: Optional[float] = None
    away_or_draw: Optional[float] = None
    home_or_away: Optional[float] = None
