"""Match data models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

from .team import Team
from .score import Score
from .odds import Odds
from .statistic import Statistic
from .event import CommentaryEvent


class MatchStatus(Enum):
    """Match status enumeration."""

    NOT_STARTED = "not_started"
    FIRST_HALF = "first_half"
    HALF_TIME = "half_time"
    SECOND_HALF = "second_half"
    FINISHED = "finished"
    AFTER_EXTRA_TIME = "aet"
    AFTER_PENALTIES = "penalties"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"
    ABANDONED = "abandoned"


@dataclass
class MatchResult:
    """Match score results at different stages."""

    # Half-time scores (CRITICAL for ML use case)
    half_time: Optional[Score] = None

    # Full-time scores (90 minutes)
    full_time: Optional[Score] = None

    # Extra time (if applicable)
    extra_time: Optional[Score] = None

    # Penalties (if applicable)
    penalties: Optional[Score] = None


@dataclass
class MatchInfo:
    """Additional match metadata."""

    referee: Optional[str] = None
    venue: Optional[str] = None
    attendance: Optional[int] = None
    weather: Optional[str] = None


@dataclass
class Match:
    """Complete match record."""

    # Identifiers
    match_id: str  # Flashscore unique ID
    url: str  # Full match URL

    # Competition info
    country: str
    league: str
    season: str
    stage: Optional[str]  # Round, Final, Semi-final, etc.

    # Match basics
    date: datetime
    status: MatchStatus
    home_team: Team
    away_team: Team

    # Results (THE KEY DATA)
    result: MatchResult

    # Additional data
    odds: Optional[Odds] = None
    info: Optional[MatchInfo] = None
    statistics: list[Statistic] = field(default_factory=list)
    commentary: list[CommentaryEvent] = field(default_factory=list)

    # Metadata
    scraped_at: datetime = field(default_factory=datetime.utcnow)

    def __str__(self) -> str:
        score_str = "vs"
        if self.result.full_time:
            score_str = str(self.result.full_time)
        return f"{self.home_team} {score_str} {self.away_team}"
