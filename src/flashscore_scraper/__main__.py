"""Main entry point for Flashscore scraper."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
import typer

from .config import Config, setup_logging
from .scraper import MatchListScraper, MatchDetailScraper
from .exporters import get_exporter
from .constants import FLASHSCORE_FOOTBALL_URL

console = Console()
app = typer.Typer(help="⚽ Flashscore ML Dataset Scraper", no_args_is_help=True)


@app.command(name="scrape")
def scrape_command(
    country: str = typer.Argument(..., help="Country name (e.g., 'england')"),
    league: str = typer.Argument(..., help="League slug (e.g., 'premier-league')"),
    season: str = typer.Option(None, help="Season (e.g., '2023-2024'). If not specified, scrapes current season"),
    output: str = typer.Option("./data", help="Output directory"),
    format: str = typer.Option("parquet", help="Output format: parquet, csv, json"),
    concurrency: int = typer.Option(10, help="Number of concurrent scrapers"),
    proxy: str = typer.Option(None, help="Proxy URL (http://user:pass@host:port)"),
    headless: bool = typer.Option(True, help="Run browser in headless mode"),
    include_stats: bool = typer.Option(True, help="Include match statistics"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose logging"),
):
    """
    Scrape soccer match data from Flashscore.

    Examples:
        python -m src.flashscore_scraper england premier-league --season 2023-2024
        python -m src.flashscore_scraper scrape england premier-league --season 2023-2024

    Example with proxy:
        python -m src.flashscore_scraper spain laliga --proxy "http://user:pass@proxy.com:8080"
    """
    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(level=log_level, log_file="./logs/scraper.log")

    # Load proxy from config file if not provided
    if not proxy:
        config_file = Path("config/settings.yaml")
        if config_file.exists():
            try:
                file_config = Config.from_yaml(str(config_file))
                proxy = file_config.proxy_url
            except Exception:
                pass

    # Create config
    config = Config(
        country=country,
        league=league,
        season=season,
        output_dir=output,
        output_format=format,
        concurrency=concurrency,
        proxy_url=proxy,
        headless=headless,
        include_statistics=include_stats,
    )

    # Run scraper
    asyncio.run(run_scraper(config))


async def run_scraper(config: Config):
    """Main scraping orchestrator."""
    logger = logging.getLogger("Orchestrator")

    console.print("\n[bold blue]⚽ Flashscore ML Dataset Scraper[/bold blue]\n")
    console.print(f"Country:     [cyan]{config.country}[/cyan]")
    console.print(f"League:      [cyan]{config.league}[/cyan]")
    console.print(f"Season:      [cyan]{config.season or 'current'}[/cyan]")
    console.print(f"Output:      [cyan]{config.output_dir}[/cyan]")
    console.print(f"Format:      [cyan]{config.output_format}[/cyan]")
    if config.proxy_url:
        proxy_display = config.proxy_url.split("@")[-1]
        console.print(f"Proxy:       [cyan]{proxy_display}[/cyan]")
    console.print()

    # Initialize scrapers
    match_list_scraper = MatchListScraper(
        headless=config.headless,
        proxy_url=config.proxy_url,
        timeout=config.timeout,
    )

    match_detail_scraper = MatchDetailScraper(
        proxy_url=config.proxy_url,
        timeout=config.timeout // 1000,  # Convert to seconds
    )

    # Create browser context for match list
    playwright, browser, context = await match_list_scraper.create_context()

    try:
        # Build league URL
        if config.season:
            league_url = f"{FLASHSCORE_FOOTBALL_URL}/{config.country}/{config.league}-{config.season}/"
        else:
            league_url = f"{FLASHSCORE_FOOTBALL_URL}/{config.country}/{config.league}/"

        logger.info(f"League URL: {league_url}")

        # Get all match links
        with console.status("[yellow]📋 Loading match list...[/yellow]"):
            results_matches = await match_list_scraper.get_match_links(
                context, league_url, "results"
            )
            fixture_matches = await match_list_scraper.get_match_links(
                context, league_url, "fixtures"
            )

        all_matches = results_matches + fixture_matches
        console.print(f"[green]✓ Found {len(all_matches)} matches[/green]\n")

        if not all_matches:
            console.print("[red]❌ No matches found. Check country/league/season name.[/red]")
            console.print(f"[yellow]💡 Tried URL: {league_url}[/yellow]")
            return

        # Scrape match details with concurrency control
        matches_data = []
        failed_matches = []
        semaphore = asyncio.Semaphore(config.concurrency)

        async def scrape_with_semaphore(match_info):
            async with semaphore:
                try:
                    match = await match_detail_scraper.scrape_match(
                        match_id=match_info["id"],
                        url=match_info["url"],
                        country=config.country,
                        league=config.league,
                        season=config.season or "current",
                    )
                    await match_detail_scraper.random_delay(
                        config.min_delay, config.max_delay
                    )
                    return match
                except Exception as e:
                    logger.error(f"Failed to scrape {match_info['id']}: {e}")
                    return None

        # Progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                "[cyan]Scraping matches...", total=len(all_matches)
            )

            tasks = []
            for match_info in all_matches:
                task_coro = scrape_with_semaphore(match_info)
                tasks.append(task_coro)

            for coro in asyncio.as_completed(tasks):
                match_data = await coro

                if match_data:
                    matches_data.append(match_data)

                    # Incremental save
                    if len(matches_data) % config.save_interval == 0:
                        await save_checkpoint(matches_data, config)
                else:
                    failed_matches.append(match_info)

                progress.advance(task)

        # Summary
        console.print()
        console.print(f"[green]✓ Successfully scraped: {len(matches_data)} matches[/green]")
        if failed_matches:
            console.print(f"[red]✗ Failed: {len(failed_matches)} matches[/red]")

        if not matches_data:
            console.print("[red]❌ No matches scraped successfully.[/red]")
            return

        # Final save
        console.print(f"\n[yellow]💾 Saving {len(matches_data)} matches...[/yellow]")

        exporter = get_exporter(config.output_format)
        output_path = exporter.export(
            matches_data,
            config.output_dir,
            f"{config.country}_{config.league}_{config.season or 'current'}",
        )

        console.print(f"[bold green]✅ Done! Data saved to: {output_path}[/bold green]\n")

        # Print summary statistics
        print_summary(matches_data)

    finally:
        await context.close()
        await browser.close()
        await playwright.stop()
        await match_detail_scraper.close()


async def save_checkpoint(matches, config):
    """Save checkpoint to prevent data loss."""
    logger = logging.getLogger("Checkpoint")
    logger.info(f"Saving checkpoint with {len(matches)} matches")

    # Quick save to JSON
    import json
    from pathlib import Path

    checkpoint_dir = Path(config.output_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_file = checkpoint_dir / "checkpoint.json"

    data = []
    for match in matches:
        data.append({
            "match_id": match.match_id,
            "home_team": match.home_team.name,
            "away_team": match.away_team.name,
            "date": match.date.isoformat() if match.date else None,
        })

    with open(checkpoint_file, "w") as f:
        json.dump(data, f, indent=2)


def print_summary(matches):
    """Print summary statistics about scraped data."""
    total = len(matches)
    with_ht = sum(1 for m in matches if m.result.half_time is not None)
    with_ft = sum(1 for m in matches if m.result.full_time is not None)
    with_stats = sum(1 for m in matches if len(m.statistics) > 0)

    console.print("\n[bold]📊 Summary:[/bold]")
    console.print(f"  Total matches:       {total}")
    console.print(f"  With FT scores:      {with_ft} ({100*with_ft/total:.1f}%)")
    console.print(f"  With HT scores:      {with_ht} ({100*with_ht/total:.1f}%)")
    console.print(f"  With statistics:     {with_stats} ({100*with_stats/total:.1f}%)")

    # Calculate average statistics
    if with_ht and with_ft:
        avg_ft_goals = sum(
            m.result.full_time.total
            for m in matches
            if m.result.full_time
        ) / with_ft

        avg_ht_goals = sum(
            m.result.half_time.total
            for m in matches
            if m.result.half_time
        ) / with_ht

        console.print(f"\n  Avg FT goals:        {avg_ft_goals:.2f}")
        console.print(f"  Avg HT goals:        {avg_ht_goals:.2f}")


@app.command()
def test_proxy(
    proxy: str = typer.Option(None, help="Proxy URL to test"),
):
    """Test proxy connection to Flashscore."""
    import asyncio

    async def _test():
        from .scraper.base import TLSClientScraper

        # Load proxy from config if not provided
        if not proxy:
            config_file = Path("config/settings.yaml")
            if config_file.exists():
                config = Config.from_yaml(str(config_file))
                test_proxy = config.proxy_url
            else:
                console.print("[red]No proxy provided and no config file found[/red]")
                return
        else:
            test_proxy = proxy

        console.print(f"\n[yellow]Testing proxy: {test_proxy.split('@')[-1]}[/yellow]\n")

        scraper = TLSClientScraper(proxy_url=test_proxy)

        try:
            html = await scraper.fetch_html("https://www.flashscore.com")
            if "flashscore" in html.lower():
                console.print("[green]✓ Proxy working! Successfully connected to Flashscore[/green]")
            else:
                console.print("[yellow]⚠ Connected but response looks unexpected[/yellow]")
        except Exception as e:
            console.print(f"[red]✗ Proxy failed: {e}[/red]")
        finally:
            await scraper.close()

    asyncio.run(_test())


def main():
    """Main entry point with smart command detection."""
    import sys

    # If no arguments or first arg is a known command, use typer normally
    if len(sys.argv) == 1 or sys.argv[1] in ['scrape', 'test-proxy', '--help', '-h']:
        app()
    else:
        # First argument looks like a country name - inject 'scrape' command
        sys.argv.insert(1, 'scrape')
        app()


if __name__ == "__main__":
    main()
