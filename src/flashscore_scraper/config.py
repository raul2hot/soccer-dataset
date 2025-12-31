"""Configuration management."""

import os
import yaml
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Scraper configuration."""

    # Target league
    country: str
    league: str
    season: Optional[str] = None

    # Proxy settings
    proxy_url: Optional[str] = None

    # Scraping settings
    use_tls_client: bool = True
    use_playwright: bool = True
    concurrency: int = 10
    min_delay: float = 1.0
    max_delay: float = 3.0
    max_retries: int = 3
    timeout: int = 30000
    save_interval: int = 20
    headless: bool = True

    # Output settings
    output_format: str = "parquet"
    output_dir: str = "./data"

    # Feature flags
    include_commentary: bool = False
    include_odds: bool = False
    include_statistics: bool = True
    include_match_info: bool = True

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Config":
        """
        Load configuration from YAML file.

        Args:
            yaml_path: Path to YAML config file

        Returns:
            Config instance
        """
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        # Extract proxy URL (support env variable)
        proxy_url = data.get("proxy", {}).get("url")
        if proxy_url and proxy_url.startswith("${") and proxy_url.endswith("}"):
            env_var = proxy_url[2:-1]
            proxy_url = os.getenv(env_var)

        return cls(
            country=data.get("country", ""),
            league=data.get("league", ""),
            season=data.get("season"),
            proxy_url=proxy_url if data.get("proxy", {}).get("enabled", False) else None,
            use_tls_client=data.get("scraping", {}).get("use_tls_client", True),
            use_playwright=data.get("scraping", {}).get("use_playwright", True),
            concurrency=data.get("scraping", {}).get("concurrency", 10),
            min_delay=data.get("scraping", {}).get("min_delay", 1.0),
            max_delay=data.get("scraping", {}).get("max_delay", 3.0),
            max_retries=data.get("scraping", {}).get("max_retries", 3),
            timeout=data.get("scraping", {}).get("timeout", 30000),
            save_interval=data.get("scraping", {}).get("save_interval", 20),
            headless=data.get("scraping", {}).get("headless", True),
            output_format=data.get("output", {}).get("format", "parquet"),
            output_dir=data.get("output", {}).get("directory", "./data"),
            include_commentary=data.get("features", {}).get("include_commentary", False),
            include_odds=data.get("features", {}).get("include_odds", False),
            include_statistics=data.get("features", {}).get("include_statistics", True),
            include_match_info=data.get("features", {}).get("include_match_info", True),
        )


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """
    Setup logging configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
    """
    import logging
    from rich.logging import RichHandler

    # Create logs directory if needed
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Setup handlers
    handlers = [RichHandler(rich_tracebacks=True, markup=True)]

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=handlers,
    )
