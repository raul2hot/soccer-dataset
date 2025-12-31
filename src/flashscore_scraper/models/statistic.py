"""Match statistic data model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Statistic:
    """Represents a match statistic (e.g., possession, shots)."""

    category: str
    home_value: str
    away_value: str

    # Parsed numeric values where applicable
    home_numeric: Optional[float] = None
    away_numeric: Optional[float] = None

    def __str__(self) -> str:
        return f"{self.category}: {self.home_value} - {self.away_value}"
