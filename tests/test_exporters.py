"""Tests for exporters."""

import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from src.flashscore_scraper.models import (
    Match,
    MatchStatus,
    MatchResult,
    Team,
    Score,
)
from src.flashscore_scraper.exporters import ParquetExporter, CSVExporter


class TestParquetExporter:
    """Tests for Parquet exporter."""

    @pytest.fixture
    def sample_matches(self):
        """Create sample matches for testing."""
        return [
            Match(
                match_id="ABC123",
                url="https://test.com",
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
            ),
            Match(
                match_id="DEF456",
                url="https://test.com",
                country="England",
                league="Premier League",
                season="2023-2024",
                stage="Round 2",
                date=datetime(2024, 1, 8),
                status=MatchStatus.FINISHED,
                home_team=Team("Chelsea"),
                away_team=Team("Man City"),
                result=MatchResult(
                    half_time=Score(0, 0),
                    full_time=Score(1, 1),
                ),
            ),
        ]

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test outputs."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    def test_export_parquet(self, sample_matches, temp_dir):
        """Test Parquet export."""
        exporter = ParquetExporter()
        output_path = exporter.export(
            sample_matches,
            str(temp_dir),
            "test_league",
        )

        assert output_path.exists()
        assert output_path.suffix == ".parquet"

        # Load and verify
        df = pd.read_parquet(output_path)
        assert len(df) == 2
        assert "ht_home_goals" in df.columns
        assert "ft_home_goals" in df.columns

    def test_ml_features_added(self, sample_matches, temp_dir):
        """Test that ML features are added."""
        exporter = ParquetExporter()
        output_path = exporter.export(sample_matches, str(temp_dir), "test")

        df = pd.read_parquet(output_path)

        # Check derived features exist
        assert "ht_total_goals" in df.columns
        assert "ht_goal_diff" in df.columns
        assert "ht_result" in df.columns
        assert "ft_total_goals" in df.columns
        assert "ft_over_2_5" in df.columns
        assert "ft_btts" in df.columns
        assert "2h_home_goals" in df.columns

    def test_ml_features_values(self, sample_matches, temp_dir):
        """Test that ML feature values are correct."""
        exporter = ParquetExporter()
        output_path = exporter.export(sample_matches, str(temp_dir), "test")

        df = pd.read_parquet(output_path)

        # First match: Arsenal 2-1 Liverpool (HT: 1-0)
        row1 = df.iloc[0]
        assert row1["ht_total_goals"] == 1
        assert row1["ht_goal_diff"] == 1
        assert row1["ht_result"] == "H"
        assert row1["ft_total_goals"] == 3
        assert row1["ft_over_2_5"] == True
        assert row1["ft_btts"] == True
        assert row1["2h_home_goals"] == 1  # 2 - 1 = 1
        assert row1["2h_away_goals"] == 1  # 1 - 0 = 1

        # Second match: Chelsea 1-1 Man City (HT: 0-0)
        row2 = df.iloc[1]
        assert row2["ht_total_goals"] == 0
        assert row2["ht_result"] == "D"
        assert row2["ft_total_goals"] == 2
        assert row2["ft_over_2_5"] == False
        assert row2["ft_result"] == "D"


class TestCSVExporter:
    """Tests for CSV exporter."""

    @pytest.fixture
    def sample_matches(self):
        """Create sample matches for testing."""
        return [
            Match(
                match_id="ABC123",
                url="https://test.com",
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
            ),
        ]

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test outputs."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    def test_export_csv(self, sample_matches, temp_dir):
        """Test CSV export."""
        exporter = CSVExporter()
        output_path = exporter.export(sample_matches, str(temp_dir), "test")

        assert output_path.exists()
        assert output_path.suffix == ".csv"

        # Load and verify
        df = pd.read_csv(output_path)
        assert len(df) == 1
        assert "ht_home_goals" in df.columns
