"""Commentary event data model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CommentaryEvent:
    """Individual event from match commentary/timeline."""

    minute: int  # Match minute (0-90+)
    added_time: Optional[int]  # Stoppage time minutes
    event_type: str  # goal, yellow_card, red_card, substitution, etc.
    team: Optional[str]  # home, away, or None
    player: Optional[str]  # Player name if available
    description: str  # Full event description
    is_half_time: bool = False  # Flag for half-time event

    def __str__(self) -> str:
        time_str = f"{self.minute}'"
        if self.added_time:
            time_str += f"+{self.added_time}"
        return f"[{time_str}] {self.description}"
