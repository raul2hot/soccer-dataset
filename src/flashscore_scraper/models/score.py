"""Score data model."""

from dataclasses import dataclass


@dataclass
class Score:
    """Represents a score at a specific point in the match."""

    home: int
    away: int

    @property
    def total(self) -> int:
        """Total goals scored."""
        return self.home + self.away

    @property
    def diff(self) -> int:
        """Goal difference (home - away)."""
        return self.home - self.away

    @property
    def result(self) -> str:
        """Match result: H (home win), D (draw), A (away win)."""
        if self.home > self.away:
            return "H"
        elif self.away > self.home:
            return "A"
        return "D"

    def __str__(self) -> str:
        return f"{self.home}-{self.away}"
