"""Match list scraper - get all matches from a league."""

import re
from typing import List, Dict
from urllib.parse import urljoin

from .base import BaseScraper
from ..constants import FLASHSCORE_BASE_URL, Selectors
from ..utils.parsing import extract_match_id


class MatchListScraper(BaseScraper):
    """Scrapes list of matches from a league page."""

    async def get_match_links(
        self, context, league_url: str, tab: str = "results"
    ) -> List[Dict[str, str]]:
        """
        Get all match links from a league page.

        Args:
            context: Playwright browser context
            league_url: League URL (e.g., https://www.flashscore.com/football/england/premier-league/)
            tab: Tab to scrape - 'results' or 'fixtures'

        Returns:
            List of dicts with 'id' and 'url' keys
        """
        page = await context.new_page()

        try:
            # Build URL with tab
            if tab == "results":
                url = f"{league_url}results/"
            elif tab == "fixtures":
                url = f"{league_url}fixtures/"
            else:
                url = league_url

            self.logger.info(f"Fetching {tab} from: {url}")
            await self.safe_goto(page, url)

            # Wait for matches to load
            await page.wait_for_timeout(2000)

            # Try to load all matches by clicking "Show more"
            total_loaded = await self.scroll_and_load_all(
                page,
                load_more_selector=Selectors.LOAD_MORE_BUTTON,
                item_selector=Selectors.MATCH_ROW,
                max_clicks=100,
            )

            self.logger.info(f"Loaded {total_loaded} match rows")

            # Extract match links
            matches = []
            match_elements = await page.query_selector_all(Selectors.MATCH_ROW)

            for element in match_elements:
                # Get match link
                link_el = await element.query_selector("a")
                if not link_el:
                    continue

                href = await link_el.get_attribute("href")
                if not href:
                    continue

                # Build full URL
                match_url = urljoin(FLASHSCORE_BASE_URL, href)

                # Extract match ID
                match_id = extract_match_id(match_url)
                if not match_id:
                    # Try to extract from ID attribute
                    element_id = await element.get_attribute("id")
                    if element_id and element_id.startswith("g_1_"):
                        match_id = element_id.replace("g_1_", "")
                    else:
                        continue

                matches.append({"id": match_id, "url": match_url})

            self.logger.info(f"Extracted {len(matches)} match links")
            return matches

        finally:
            await page.close()

    async def get_leagues_from_country(
        self, context, country: str
    ) -> List[Dict[str, str]]:
        """
        Get all leagues from a country.

        Args:
            context: Playwright browser context
            country: Country name (e.g., 'england')

        Returns:
            List of dicts with league info
        """
        page = await context.new_page()

        try:
            url = f"{FLASHSCORE_BASE_URL}/football/{country.lower()}/"
            self.logger.info(f"Fetching leagues from: {url}")

            await self.safe_goto(page, url)
            await page.wait_for_timeout(2000)

            # Extract league links
            leagues = []
            league_elements = await page.query_selector_all("a.leagueRow")

            for element in league_elements:
                name_el = await element.query_selector(".leagueRow__participantName")
                if not name_el:
                    continue

                name = await name_el.text_content()
                href = await element.get_attribute("href")

                if name and href:
                    leagues.append({
                        "name": name.strip(),
                        "url": urljoin(FLASHSCORE_BASE_URL, href),
                    })

            self.logger.info(f"Found {len(leagues)} leagues")
            return leagues

        finally:
            await page.close()
