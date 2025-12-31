"""Parquet exporter with ML-ready features."""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List
import logging

from ..models import Match


class ParquetExporter:
    """Export match data to Parquet format optimized for ML."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def export(
        self,
        matches: List[Match],
        output_dir: str,
        filename_prefix: str,
    ) -> Path:
        """
        Export matches to ML-ready Parquet file.

        Creates a denormalized table with:
        - Half-time features (for prediction)
        - Full-time targets (to predict)
        - Derived betting line outcomes
        - Match statistics

        Args:
            matches: List of Match objects
            output_dir: Output directory path
            filename_prefix: Prefix for filename

        Returns:
            Path to created Parquet file
        """
        self.logger.info(f"Exporting {len(matches)} matches to Parquet...")

        # Convert to flat records
        records = [self._match_to_record(m) for m in matches]

        # Create DataFrame
        df = pd.DataFrame(records)

        # Add derived ML features and targets
        df = self._add_ml_features(df)

        # Sort by date
        if "date" in df.columns:
            df = df.sort_values("date")

        # Save to Parquet
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = output_path / f"{filename_prefix}_{timestamp}.parquet"

        df.to_parquet(filepath, index=False, engine="pyarrow", compression="snappy")

        self.logger.info(f"Exported to: {filepath}")
        self.logger.info(f"Rows: {len(df)}, Columns: {len(df.columns)}")

        return filepath

    def _match_to_record(self, match: Match) -> dict:
        """Convert Match object to flat dictionary."""
        record = {
            # Identifiers
            "match_id": match.match_id,
            "url": match.url,
            "date": match.date,
            "scraped_at": match.scraped_at,
            # Competition info
            "country": match.country,
            "league": match.league,
            "season": match.season,
            "stage": match.stage,
            "status": match.status.value,
            # Teams
            "home_team": match.home_team.name,
            "away_team": match.away_team.name,
            "home_team_id": match.home_team.flashscore_id,
            "away_team_id": match.away_team.flashscore_id,
        }

        # Half-time scores (FEATURES for ML)
        if match.result.half_time:
            record["ht_home_goals"] = match.result.half_time.home
            record["ht_away_goals"] = match.result.half_time.away
        else:
            record["ht_home_goals"] = None
            record["ht_away_goals"] = None

        # Full-time scores (TARGETS for ML)
        if match.result.full_time:
            record["ft_home_goals"] = match.result.full_time.home
            record["ft_away_goals"] = match.result.full_time.away
        else:
            record["ft_home_goals"] = None
            record["ft_away_goals"] = None

        # Extra time
        if match.result.extra_time:
            record["et_home_goals"] = match.result.extra_time.home
            record["et_away_goals"] = match.result.extra_time.away
        else:
            record["et_home_goals"] = None
            record["et_away_goals"] = None

        # Penalties
        if match.result.penalties:
            record["pen_home_goals"] = match.result.penalties.home
            record["pen_away_goals"] = match.result.penalties.away
        else:
            record["pen_home_goals"] = None
            record["pen_away_goals"] = None

        # Match info
        if match.info:
            record["venue"] = match.info.venue
            record["referee"] = match.info.referee
            record["attendance"] = match.info.attendance
            record["weather"] = match.info.weather
        else:
            record["venue"] = None
            record["referee"] = None
            record["attendance"] = None
            record["weather"] = None

        # Statistics (flatten to columns)
        stat_mapping = {
            "ball possession": "possession",
            "possession": "possession",
            "shots": "shots",
            "total shots": "shots",
            "shots on goal": "shots_on_target",
            "shots on target": "shots_on_target",
            "corner kicks": "corners",
            "corners": "corners",
            "fouls": "fouls",
            "yellow cards": "yellow_cards",
            "red cards": "red_cards",
            "offsides": "offsides",
            "goalkeeper saves": "saves",
            "saves": "saves",
            "total passes": "passes",
            "passes": "passes",
            "passes accurate": "passes_accurate",
            "tackles": "tackles",
        }

        for stat in match.statistics:
            stat_key = stat_mapping.get(stat.category.lower())
            if stat_key:
                record[f"stat_{stat_key}_home"] = stat.home_numeric
                record[f"stat_{stat_key}_away"] = stat.away_numeric

        # Odds
        if match.odds:
            record["odds_home_win"] = match.odds.home_win
            record["odds_draw"] = match.odds.draw
            record["odds_away_win"] = match.odds.away_win
            record["odds_over_0_5"] = match.odds.over_0_5
            record["odds_under_0_5"] = match.odds.under_0_5
            record["odds_over_1_5"] = match.odds.over_1_5
            record["odds_under_1_5"] = match.odds.under_1_5
            record["odds_over_2_5"] = match.odds.over_2_5
            record["odds_under_2_5"] = match.odds.under_2_5
            record["odds_over_3_5"] = match.odds.over_3_5
            record["odds_under_3_5"] = match.odds.under_3_5
            record["odds_btts_yes"] = match.odds.btts_yes
            record["odds_btts_no"] = match.odds.btts_no

        return record

    def _add_ml_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add derived ML features and target variables.

        Features (from half-time):
        - ht_total_goals, ht_goal_diff, ht_result

        Targets (to predict):
        - ft_total_goals, ft_goal_diff, ft_result
        - ft_over_X_5 (betting lines)
        - ft_btts (both teams to score)
        - 2h_* (second half specific)
        """
        # Half-time derived features
        if "ht_home_goals" in df.columns and "ht_away_goals" in df.columns:
            df["ht_total_goals"] = df["ht_home_goals"] + df["ht_away_goals"]
            df["ht_goal_diff"] = df["ht_home_goals"] - df["ht_away_goals"]

            # Half-time result
            def get_result(row):
                if pd.isna(row["ht_home_goals"]) or pd.isna(row["ht_away_goals"]):
                    return None
                if row["ht_home_goals"] > row["ht_away_goals"]:
                    return "H"
                elif row["ht_home_goals"] < row["ht_away_goals"]:
                    return "A"
                return "D"

            df["ht_result"] = df.apply(get_result, axis=1)

        # Full-time derived targets
        if "ft_home_goals" in df.columns and "ft_away_goals" in df.columns:
            df["ft_total_goals"] = df["ft_home_goals"] + df["ft_away_goals"]
            df["ft_goal_diff"] = df["ft_home_goals"] - df["ft_away_goals"]

            # Full-time result (TARGET)
            def get_ft_result(row):
                if pd.isna(row["ft_home_goals"]) or pd.isna(row["ft_away_goals"]):
                    return None
                if row["ft_home_goals"] > row["ft_away_goals"]:
                    return "H"
                elif row["ft_home_goals"] < row["ft_away_goals"]:
                    return "A"
                return "D"

            df["ft_result"] = df.apply(get_ft_result, axis=1)

            # Over/Under targets
            df["ft_over_0_5"] = (df["ft_total_goals"] > 0.5).astype("boolean")
            df["ft_over_1_5"] = (df["ft_total_goals"] > 1.5).astype("boolean")
            df["ft_over_2_5"] = (df["ft_total_goals"] > 2.5).astype("boolean")
            df["ft_over_3_5"] = (df["ft_total_goals"] > 3.5).astype("boolean")
            df["ft_over_4_5"] = (df["ft_total_goals"] > 4.5).astype("boolean")

            df["ft_under_0_5"] = (df["ft_total_goals"] < 0.5).astype("boolean")
            df["ft_under_1_5"] = (df["ft_total_goals"] < 1.5).astype("boolean")
            df["ft_under_2_5"] = (df["ft_total_goals"] < 2.5).astype("boolean")
            df["ft_under_3_5"] = (df["ft_total_goals"] < 3.5).astype("boolean")

            # Both Teams to Score (BTTS)
            df["ft_btts"] = (
                (df["ft_home_goals"] > 0) & (df["ft_away_goals"] > 0)
            ).astype("boolean")

        # Second half analysis
        if all(col in df.columns for col in ["ft_home_goals", "ft_away_goals", "ht_home_goals", "ht_away_goals"]):
            df["2h_home_goals"] = df["ft_home_goals"] - df["ht_home_goals"]
            df["2h_away_goals"] = df["ft_away_goals"] - df["ht_away_goals"]
            df["2h_total_goals"] = df["2h_home_goals"] + df["2h_away_goals"]
            df["2h_goal_diff"] = df["2h_home_goals"] - df["2h_away_goals"]

            # Second half result
            def get_2h_result(row):
                if pd.isna(row["2h_home_goals"]) or pd.isna(row["2h_away_goals"]):
                    return None
                if row["2h_home_goals"] > row["2h_away_goals"]:
                    return "H"
                elif row["2h_home_goals"] < row["2h_away_goals"]:
                    return "A"
                return "D"

            df["2h_result"] = df.apply(get_2h_result, axis=1)

        # Statistical features (if available)
        stat_cols = [col for col in df.columns if col.startswith("stat_")]
        if stat_cols:
            # Calculate possession difference
            if "stat_possession_home" in df.columns and "stat_possession_away" in df.columns:
                df["stat_possession_diff"] = (
                    df["stat_possession_home"] - df["stat_possession_away"]
                )

            # Calculate shot accuracy
            if "stat_shots_home" in df.columns and "stat_shots_on_target_home" in df.columns:
                df["stat_shot_accuracy_home"] = (
                    df["stat_shots_on_target_home"] / df["stat_shots_home"] * 100
                ).fillna(0)

            if "stat_shots_away" in df.columns and "stat_shots_on_target_away" in df.columns:
                df["stat_shot_accuracy_away"] = (
                    df["stat_shots_on_target_away"] / df["stat_shots_away"] * 100
                ).fillna(0)

        return df
