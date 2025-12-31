"""Match detail scraper - extract comprehensive match data."""

import re
from datetime import datetime
from typing import Optional, List
from urllib.parse import urlparse, parse_qs

from .base import TLSClientScraper
from ..models import (
    Match,
    MatchStatus,
    MatchResult,
    MatchInfo,
    Team,
    Score,
    Statistic,
)
from ..constants import Selectors
from ..utils.parsing import (
    parse_score,
    parse_ht_score,
    parse_date,
    parse_attendance,
    parse_stat_value,
    clean_text,
)


class MatchDetailScraper(TLSClientScraper):
    """Scrapes individual match details using tls_client for better reliability."""

    async def scrape_match(
        self,
        match_id: str,
        url: str,
        country: str,
        league: str,
        season: str,
    ) -> Optional[Match]:
        """
        Scrape complete match data.

        Args:
            match_id: Flashscore match ID
            url: Match URL
            country: Country name
            league: League name
            season: Season name

        Returns:
            Match object or None if scraping fails
        """
        self.logger.info(f"Scraping match: {match_id}")

        try:
            # Fetch match page HTML
            soup = await self.fetch_soup(url)

            # Extract basic match data
            home_team, away_team = self._extract_teams(soup)
            match_date = self._extract_date(soup)
            status = self._extract_status(soup)
            stage = self._extract_stage(soup)

            # Extract scores (CRITICAL - half-time scores!)
            result = self._extract_scores(soup)

            # Create match object
            match = Match(
                match_id=match_id,
                url=url,
                country=country,
                league=league,
                season=season,
                stage=stage,
                date=match_date or datetime.utcnow(),
                status=status,
                home_team=home_team,
                away_team=away_team,
                result=result,
            )

            # Extract match info
            match.info = self._extract_match_info(soup)

            # Fetch and extract statistics
            await self.random_delay()
            stats_url = self._build_stats_url(url)
            stats_soup = await self.fetch_soup(stats_url)
            match.statistics = self._extract_statistics(stats_soup)

            return match

        except Exception as e:
            self.logger.error(f"Error scraping match {match_id}: {e}")
            return None

    def _extract_teams(self, soup) -> tuple[Team, Team]:
        """Extract home and away teams."""
        home_name = "Unknown"
        away_name = "Unknown"

        # Try to find team names
        home_el = soup.select_one(Selectors.HOME_TEAM_NAME)
        away_el = soup.select_one(Selectors.AWAY_TEAM_NAME)

        if home_el:
            home_name = clean_text(home_el.get_text())
        if away_el:
            away_name = clean_text(away_el.get_text())

        # Alternative: look for participant names
        if home_name == "Unknown":
            participants = soup.select(".participant__participantName")
            if len(participants) >= 2:
                home_name = clean_text(participants[0].get_text())
                away_name = clean_text(participants[1].get_text())

        home_team = Team(name=home_name)
        away_team = Team(name=away_name)

        return home_team, away_team

    def _extract_date(self, soup) -> Optional[datetime]:
        """Extract match date."""
        date_el = soup.select_one(Selectors.MATCH_DATE)
        if date_el:
            date_str = clean_text(date_el.get_text())
            return parse_date(date_str)

        # Alternative: look for datetime attribute
        time_els = soup.select("[datetime]")
        for el in time_els:
            dt_str = el.get("datetime")
            if dt_str:
                try:
                    # Parse ISO format
                    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                except:
                    pass

        return None

    def _extract_status(self, soup) -> MatchStatus:
        """Extract match status."""
        status_el = soup.select_one(Selectors.MATCH_STATUS)
        if status_el:
            status_text = clean_text(status_el.get_text()).lower()

            if "finished" in status_text or "ft" in status_text:
                return MatchStatus.FINISHED
            elif "half time" in status_text or "ht" in status_text:
                return MatchStatus.HALF_TIME
            elif "postponed" in status_text:
                return MatchStatus.POSTPONED
            elif "cancelled" in status_text:
                return MatchStatus.CANCELLED
            elif "aet" in status_text:
                return MatchStatus.AFTER_EXTRA_TIME
            elif "pen" in status_text:
                return MatchStatus.AFTER_PENALTIES

        return MatchStatus.FINISHED

    def _extract_stage(self, soup) -> Optional[str]:
        """Extract match stage/round."""
        stage_el = soup.select_one(Selectors.MATCH_STAGE)
        if stage_el:
            return clean_text(stage_el.get_text())

        # Alternative: look for round information
        for el in soup.select(".tournamentHeader__country, .tournamentHeader__country a"):
            text = clean_text(el.get_text())
            if "round" in text.lower() or "final" in text.lower():
                return text

        return None

    def _extract_scores(self, soup) -> MatchResult:
        """
        Extract half-time and full-time scores.

        THIS IS THE MOST CRITICAL FUNCTION - half-time scores are essential for ML.

        Multiple fallback strategies to maximize HT score capture rate.
        """
        result = MatchResult()

        # Strategy 1: Look for main score display
        score_home = soup.select_one(Selectors.SCORE_HOME)
        score_away = soup.select_one(Selectors.SCORE_AWAY)

        if score_home and score_away:
            home_score = parse_score(score_home.get_text())
            away_score = parse_score(score_away.get_text())
            result.full_time = Score(home=home_score, away=away_score)

        # Strategy 2: Look for detailScore wrapper
        if not result.full_time:
            score_wrapper = soup.select(".detailScore__wrapper span")
            if len(score_wrapper) >= 2:
                # Filter out the divider
                scores = [s for s in score_wrapper if "divider" not in s.get("class", [])]
                if len(scores) >= 2:
                    result.full_time = Score(
                        home=parse_score(scores[0].get_text()),
                        away=parse_score(scores[1].get_text()),
                    )

        # Strategy 3: Half-time score - look for explicit HT element
        ht_el = soup.select_one(Selectors.HALF_TIME_SCORE)
        if ht_el:
            ht_text = clean_text(ht_el.get_text())
            ht_scores = parse_ht_score(ht_text)
            if ht_scores:
                result.half_time = Score(home=ht_scores[0], away=ht_scores[1])

        # Strategy 4: Look for HT score in page text (common pattern: "(1-0)")
        if not result.half_time:
            # Find all text that looks like scores in parentheses
            page_text = soup.get_text()
            ht_matches = re.findall(r"\((\d+)\s*[-:]\s*(\d+)\)", page_text)
            if ht_matches:
                # Usually the first one is HT score
                result.half_time = Score(home=int(ht_matches[0][0]), away=int(ht_matches[0][1]))

        # Strategy 5: Look in detailScore__halftime class
        if not result.half_time:
            ht_els = soup.select(".detailScore__halftime, .detailScore__halfTime")
            for el in ht_els:
                ht_text = clean_text(el.get_text())
                ht_scores = parse_ht_score(ht_text)
                if ht_scores:
                    result.half_time = Score(home=ht_scores[0], away=ht_scores[1])
                    break

        # Strategy 6: Look for score in match info section
        if not result.half_time:
            info_sections = soup.select(".mi__item, .smv__incident")
            for section in info_sections:
                text = clean_text(section.get_text())
                if "half-time" in text.lower() or "ht" in text.lower():
                    ht_scores = parse_ht_score(text)
                    if ht_scores:
                        result.half_time = Score(home=ht_scores[0], away=ht_scores[1])
                        break

        # Validation: HT score should not exceed FT score
        if result.half_time and result.full_time:
            if (result.half_time.home > result.full_time.home or
                result.half_time.away > result.full_time.away):
                self.logger.warning(
                    f"Invalid HT score: HT {result.half_time} > FT {result.full_time}"
                )
                result.half_time = None

        return result

    def _extract_match_info(self, soup) -> MatchInfo:
        """Extract match information (venue, referee, etc.)."""
        info = MatchInfo()

        # Look for match info items
        info_items = soup.select(Selectors.MATCH_INFO_ITEM)

        for item in info_items:
            text = clean_text(item.get_text())

            # Referee
            if "referee" in text.lower():
                # Extract name after "Referee:"
                parts = text.split(":")
                if len(parts) > 1:
                    info.referee = clean_text(parts[1])

            # Venue/Stadium
            if "venue" in text.lower() or "stadium" in text.lower():
                parts = text.split(":")
                if len(parts) > 1:
                    info.venue = clean_text(parts[1])

            # Attendance
            if "attendance" in text.lower():
                attendance_str = re.search(r"[\d,\s]+", text)
                if attendance_str:
                    info.attendance = parse_attendance(attendance_str.group())

        return info

    def _extract_statistics(self, soup) -> List[Statistic]:
        """Extract match statistics from stats page."""
        statistics = []

        # Look for stat sections
        stat_sections = soup.select(".stat__row, ._row_")

        for section in stat_sections:
            # Get category name
            category_el = section.select_one(".stat__category, ._category_, .stat__categoryName")
            if not category_el:
                continue

            category = clean_text(category_el.get_text())

            # Get home and away values
            value_els = section.select(".stat__homeValue, .stat__awayValue, ._homeValue_, ._awayValue_")

            if len(value_els) >= 2:
                home_val = clean_text(value_els[0].get_text())
                away_val = clean_text(value_els[1].get_text())

                stat = Statistic(
                    category=category,
                    home_value=home_val,
                    away_value=away_val,
                    home_numeric=parse_stat_value(home_val),
                    away_numeric=parse_stat_value(away_val),
                )

                statistics.append(stat)

        # Alternative: look for different structure
        if not statistics:
            stat_rows = soup.select(".section > div")
            for row in stat_rows:
                # Try to extract category and values
                texts = [clean_text(el.get_text()) for el in row.select("div")]
                if len(texts) >= 3:
                    # Format: [home_value, category, away_value]
                    stat = Statistic(
                        category=texts[1],
                        home_value=texts[0],
                        away_value=texts[2],
                        home_numeric=parse_stat_value(texts[0]),
                        away_numeric=parse_stat_value(texts[2]),
                    )
                    statistics.append(stat)

        self.logger.info(f"Extracted {len(statistics)} statistics")
        return statistics

    def _build_stats_url(self, match_url: str) -> str:
        """Build URL for statistics page."""
        # Remove any fragments or query params
        base_url = match_url.split("#")[0].split("?")[0]

        # Ensure it ends with /match-summary/match-statistics
        if not base_url.endswith("/"):
            base_url += "/"

        # Replace /match-summary with /match-summary/match-statistics
        if "match-summary" in base_url:
            stats_url = base_url.replace("match-summary/", "match-summary/match-statistics/")
        else:
            stats_url = base_url + "match-summary/match-statistics/"

        return stats_url
