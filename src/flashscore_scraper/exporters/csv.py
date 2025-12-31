"""CSV exporter."""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List
import logging

from ..models import Match
from .parquet import ParquetExporter


class CSVExporter(ParquetExporter):
    """Export match data to CSV format."""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)

    def export(
        self,
        matches: List[Match],
        output_dir: str,
        filename_prefix: str,
    ) -> Path:
        """
        Export matches to CSV file.

        Args:
            matches: List of Match objects
            output_dir: Output directory path
            filename_prefix: Prefix for filename

        Returns:
            Path to created CSV file
        """
        self.logger.info(f"Exporting {len(matches)} matches to CSV...")

        # Convert to flat records
        records = [self._match_to_record(m) for m in matches]

        # Create DataFrame
        df = pd.DataFrame(records)

        # Add derived ML features
        df = self._add_ml_features(df)

        # Sort by date
        if "date" in df.columns:
            df = df.sort_values("date")

        # Save to CSV
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = output_path / f"{filename_prefix}_{timestamp}.csv"

        df.to_csv(filepath, index=False, encoding="utf-8")

        self.logger.info(f"Exported to: {filepath}")
        self.logger.info(f"Rows: {len(df)}, Columns: {len(df.columns)}")

        return filepath
