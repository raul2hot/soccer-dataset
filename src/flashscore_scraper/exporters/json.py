"""JSON exporter."""

import json
from pathlib import Path
from datetime import datetime
from typing import List
from dataclasses import asdict
import logging

from ..models import Match


class JSONExporter:
    """Export match data to JSON format."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def export(
        self,
        matches: List[Match],
        output_dir: str,
        filename_prefix: str,
    ) -> Path:
        """
        Export matches to JSON file.

        Args:
            matches: List of Match objects
            output_dir: Output directory path
            filename_prefix: Prefix for filename

        Returns:
            Path to created JSON file
        """
        self.logger.info(f"Exporting {len(matches)} matches to JSON...")

        # Convert matches to dicts
        data = []
        for match in matches:
            match_dict = self._match_to_dict(match)
            data.append(match_dict)

        # Save to JSON
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = output_path / f"{filename_prefix}_{timestamp}.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        self.logger.info(f"Exported to: {filepath}")
        self.logger.info(f"Matches: {len(data)}")

        return filepath

    def _match_to_dict(self, match: Match) -> dict:
        """Convert Match object to dictionary."""
        return {
            "match_id": match.match_id,
            "url": match.url,
            "date": match.date.isoformat() if match.date else None,
            "country": match.country,
            "league": match.league,
            "season": match.season,
            "stage": match.stage,
            "status": match.status.value,
            "home_team": {
                "name": match.home_team.name,
                "id": match.home_team.flashscore_id,
                "country": match.home_team.country,
            },
            "away_team": {
                "name": match.away_team.name,
                "id": match.away_team.flashscore_id,
                "country": match.away_team.country,
            },
            "result": {
                "half_time": {
                    "home": match.result.half_time.home,
                    "away": match.result.half_time.away,
                } if match.result.half_time else None,
                "full_time": {
                    "home": match.result.full_time.home,
                    "away": match.result.full_time.away,
                } if match.result.full_time else None,
                "extra_time": {
                    "home": match.result.extra_time.home,
                    "away": match.result.extra_time.away,
                } if match.result.extra_time else None,
                "penalties": {
                    "home": match.result.penalties.home,
                    "away": match.result.penalties.away,
                } if match.result.penalties else None,
            },
            "info": {
                "venue": match.info.venue,
                "referee": match.info.referee,
                "attendance": match.info.attendance,
                "weather": match.info.weather,
            } if match.info else None,
            "statistics": [
                {
                    "category": stat.category,
                    "home_value": stat.home_value,
                    "away_value": stat.away_value,
                    "home_numeric": stat.home_numeric,
                    "away_numeric": stat.away_numeric,
                }
                for stat in match.statistics
            ],
            "commentary": [
                {
                    "minute": event.minute,
                    "added_time": event.added_time,
                    "event_type": event.event_type,
                    "team": event.team,
                    "player": event.player,
                    "description": event.description,
                }
                for event in match.commentary
            ],
            "scraped_at": match.scraped_at.isoformat() if match.scraped_at else None,
        }
