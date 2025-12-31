"""Data exporters."""

from .parquet import ParquetExporter
from .csv import CSVExporter
from .json import JSONExporter

__all__ = ["ParquetExporter", "CSVExporter", "JSONExporter"]


def get_exporter(format: str):
    """
    Get exporter instance by format name.

    Args:
        format: Output format ('parquet', 'csv', 'json')

    Returns:
        Exporter instance

    Raises:
        ValueError: If format is not supported
    """
    exporters = {
        "parquet": ParquetExporter,
        "csv": CSVExporter,
        "json": JSONExporter,
    }

    exporter_class = exporters.get(format.lower())
    if not exporter_class:
        raise ValueError(
            f"Unsupported format: {format}. Choose from: {', '.join(exporters.keys())}"
        )

    return exporter_class()
