"""Constants for Flashscore scraping."""

# Base URLs
FLASHSCORE_BASE_URL = "https://www.flashscore.com"
FLASHSCORE_FOOTBALL_URL = f"{FLASHSCORE_BASE_URL}/football"

# CSS Selectors
class Selectors:
    """CSS selectors for Flashscore elements."""

    # Navigation
    COUNTRY_MENU_TOGGLE = "#category-left-menu > div > span"
    COUNTRY_LIST = "#category-left-menu > div > div > a"
    LEAGUE_LIST = "#{country_id} ~ span > a"
    SEASON_ARCHIVE = "div.archive__season > a"

    # Match listings
    LOAD_MORE_BUTTON = 'a.event__more.event__more--static'
    MATCH_ROW = ".event__match"
    MATCH_LINK = "a.eventRowLink"

    # Match detail page
    MATCH_DATE = ".duelParticipant__startTime"
    MATCH_STATUS = ".fixedHeaderDuel__detailStatus"
    MATCH_STAGE = "span.tournamentHeader__country"

    # Teams
    HOME_TEAM_NAME = ".duelParticipant__home .participant__participantName"
    AWAY_TEAM_NAME = ".duelParticipant__away .participant__participantName"
    HOME_TEAM_LOGO = ".duelParticipant__home .participant__image"
    AWAY_TEAM_LOGO = ".duelParticipant__away .participant__image"

    # Scores
    SCORE_HOME = ".detailScore__wrapper > span:first-child"
    SCORE_AWAY = ".detailScore__wrapper > span:last-child"
    HALF_TIME_SCORE = ".detailScore__halftime"
    PENALTIES_LABEL = ".detailScore__status"

    # Match info
    MATCH_INFO_CONTAINER = ".mi__data"
    MATCH_INFO_ITEM = ".mi__item"

    # Statistics
    STATS_TAB = "#detail > div > div.tabs > a:nth-child(2)"
    STATS_SECTION = ".section"
    STAT_CATEGORY = "._category_"
    STAT_HOME_VALUE = "._homeValue_"
    STAT_AWAY_VALUE = "._awayValue_"

    # Commentary/Timeline
    COMMENTARY_TAB = "#detail > div > div.tabs > a[href*='commentary']"
    COMMENTARY_ROW = ".smv__incident"
    COMMENTARY_TIME = ".smv__timeBox"
    COMMENTARY_TEXT = ".smv__incident"

    # Odds
    ODDS_TAB = "#detail > div > div.tabs > a[href*='odds']"
    ODDS_TABLE = ".odds"
    ODDS_ROW = ".odds__row"


# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
]

# Request headers for tls_client
TLS_CLIENT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

# Timeout settings (milliseconds)
DEFAULT_TIMEOUT = 30000
LOAD_MORE_TIMEOUT = 5000
SELECTOR_WAIT_TIMEOUT = 10000

# Retry settings
MAX_RETRIES = 3
RETRY_MIN_WAIT = 2
RETRY_MAX_WAIT = 10

# Rate limiting
MIN_DELAY = 1.0
MAX_DELAY = 3.0
