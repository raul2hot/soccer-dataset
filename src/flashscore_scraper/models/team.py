"""Team data model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Team:
    """Represents a soccer team."""

    name: str
    flashscore_id: Optional[str] = None
    logo_url: Optional[str] = None
    country: Optional[str] = None

    def __str__(self) -> str:
        return self.name
