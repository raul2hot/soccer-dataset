# ⚽ Flashscore ML Dataset Scraper

A Python-based web scraping system to collect comprehensive soccer match data from **Flashscore.com** for machine learning research. The primary use case is **predicting full-time outcomes from half-time data** across various betting lines.

## 🎯 Key Features

- **Half-time and Full-time Scores**: Critical data for ML prediction models
- **Match Statistics**: Possession, shots, corners, fouls, cards, etc.
- **Pre-match Odds**: Betting lines from multiple markets (optional)
- **Live Commentary**: Timeline events and key moments (optional)
- **ML-Ready Output**: Denormalized Parquet/CSV format optimized for training
- **Robust Scraping**: Uses both `tls_client` (fast, bypasses Cloudflare) and Playwright (dynamic content)
- **Proxy Support**: Premium residential proxy integration
- **Concurrent Scraping**: Configurable concurrency with rate limiting
- **Incremental Saves**: Checkpoint system to prevent data loss

## 📊 Use Cases

1. **Half-time to Full-time Prediction**: Predict final score from HT data
2. **Over/Under Goals**: Predict O/U 2.5 goals from live match state
3. **Both Teams to Score (BTTS)**: Predict scoring patterns
4. **Second Half Analysis**: Predict 2H winner, goals, momentum shifts
5. **Statistical Analysis**: Possession, shots, corners correlation with outcomes

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/flashscore-ml-scraper.git
cd flashscore-ml-scraper

# Install dependencies
pip install -e .

# Install Playwright browsers (only if you want to use Playwright)
playwright install chromium
```

### Basic Usage

```bash
# Scrape Premier League 2023-2024
python -m src.flashscore_scraper england premier-league --season 2023-2024

# Scrape La Liga current season
python -m src.flashscore_scraper spain laliga

# Use custom output directory and format
python -m src.flashscore_scraper germany bundesliga \
    --season 2023-2024 \
    --output ./datasets \
    --format csv

# With proxy
python -m src.flashscore_scraper italy serie-a \
    --proxy "http://user:pass@proxy.com:8080"

# Verbose mode for debugging
python -m src.flashscore_scraper france ligue-1 -v
```

### Test Proxy Connection

```bash
# Test proxy from config file
python -m src.flashscore_scraper test-proxy

# Test specific proxy
python -m src.flashscore_scraper test-proxy --proxy "http://user:pass@host:port"
```

## ⚙️ Configuration

Edit `config/settings.yaml` to customize settings:

```yaml
# Proxy settings
proxy:
  enabled: true
  url: "http://user:pass@proxy.com:8080"

# Scraping settings
scraping:
  use_tls_client: true      # Fast HTTP client (recommended)
  use_playwright: true      # Browser automation for dynamic content
  concurrency: 10           # Concurrent scrapers
  min_delay: 1.0           # Minimum delay between requests (seconds)
  max_delay: 3.0           # Maximum delay
  save_interval: 20        # Save checkpoint every N matches

# Output settings
output:
  format: parquet          # parquet, csv, or json
  directory: ./data

# Feature flags
features:
  include_statistics: true
  include_commentary: false
  include_odds: false
```

## 📦 Output Format

### Parquet/CSV Columns

The scraper generates an ML-ready dataset with the following columns:

#### Identifiers
- `match_id`, `url`, `date`, `country`, `league`, `season`, `stage`

#### Teams
- `home_team`, `away_team`

#### Half-Time Data (FEATURES)
- `ht_home_goals`, `ht_away_goals`, `ht_total_goals`, `ht_goal_diff`, `ht_result`

#### Full-Time Data (TARGETS)
- `ft_home_goals`, `ft_away_goals`, `ft_total_goals`, `ft_goal_diff`, `ft_result`
- `ft_over_0_5`, `ft_over_1_5`, `ft_over_2_5`, `ft_over_3_5`
- `ft_btts` (both teams to score)

#### Second Half Analysis
- `2h_home_goals`, `2h_away_goals`, `2h_total_goals`, `2h_result`

#### Statistics
- `stat_possession_home/away`
- `stat_shots_home/away`
- `stat_shots_on_target_home/away`
- `stat_corners_home/away`
- `stat_fouls_home/away`
- `stat_yellow_cards_home/away`
- `stat_red_cards_home/away`

#### Match Info
- `venue`, `referee`, `attendance`

### Example Output

```python
import pandas as pd

# Load dataset
df = pd.read_parquet("data/england_premier_league_2023_2024_20241231.parquet")

# View sample
print(df.head())

# Filter matches with half-time data
ht_matches = df[df['ht_home_goals'].notna()]

# Calculate half-time to full-time conversion rate
ht_leads = ht_matches[ht_matches['ht_result'] == 'H']
ht_leads_won = ht_leads[ht_leads['ft_result'] == 'H']
win_rate = len(ht_leads_won) / len(ht_leads)
print(f"Teams leading at HT won: {win_rate:.1%}")
```

## 🏗️ Architecture

```
flashscore_ml_scraper/
├── src/flashscore_scraper/
│   ├── models/              # Data models (Match, Team, Score, etc.)
│   ├── scraper/
│   │   ├── base.py          # Base scrapers (TLSClient + Playwright)
│   │   ├── match_list.py    # League/match list scraper
│   │   └── match_detail.py  # Individual match scraper
│   ├── exporters/
│   │   ├── parquet.py       # Parquet exporter (primary)
│   │   ├── csv.py           # CSV exporter
│   │   └── json.py          # JSON exporter
│   ├── utils/               # Parsing, retry logic, etc.
│   ├── constants.py         # URLs, selectors, headers
│   ├── config.py            # Configuration management
│   └── __main__.py          # CLI entry point
├── config/
│   └── settings.yaml        # Default configuration
├── data/                    # Output directory (gitignored)
└── logs/                    # Log files (gitignored)
```

## 🔧 Technical Details

### Dual Scraping Approach

The scraper uses a hybrid approach for reliability:

1. **tls_client** (Primary)
   - Fast HTTP client with realistic browser fingerprint
   - Bypasses Cloudflare and anti-bot protections
   - Better for simple page fetches
   - Lower resource usage

2. **Playwright** (Fallback/Dynamic Content)
   - Full browser automation
   - Handles JavaScript-heavy pages
   - Clicks "load more" buttons
   - Useful for debugging with screenshots

### Half-Time Score Extraction

The scraper implements **6 fallback strategies** to maximize HT score capture rate:

1. Explicit HT element (`.detailScore__halftime`)
2. Parentheses pattern `(1-0)` in page text
3. Match info section
4. Timeline events at 45'
5. Alternative CSS selectors
6. Regex pattern matching

Validation: Ensures HT score ≤ FT score for each team

### Proxy Support

Supports premium residential proxies (e.g., DataImpulse):

```python
# In config
proxy:
  enabled: true
  url: "http://user:pass@gw.dataimpulse.com:823"
```

Benefits:
- Avoid IP blocking
- Bypass rate limits
- Access geo-restricted content
- Better success rate

## 📈 ML Use Case Example

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# Load data
df = pd.read_parquet("data/premier_league_2023_2024.parquet")

# Filter finished matches with HT data
df = df[
    (df['ft_result'].notna()) &
    (df['ht_home_goals'].notna())
]

# Features: Half-time state
X = df[[
    'ht_home_goals',
    'ht_away_goals',
    'ht_total_goals',
    'ht_goal_diff',
]]

# Target: Over 2.5 goals
y = df['ft_over_2_5']

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Train model
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Evaluate
accuracy = model.score(X_test, y_test)
print(f"Over 2.5 goals prediction accuracy: {accuracy:.2%}")
```

## 🐛 Troubleshooting

### No matches found
- Verify country/league/season names match Flashscore URLs
- Check league URL format: `https://www.flashscore.com/football/england/premier-league-2023-2024/`
- Use `-v` flag for verbose logging

### Half-time scores missing
- Some leagues/matches may not display HT scores
- Historical matches have better HT score availability
- Check match status is "Finished"

### Proxy errors (403, timeout)
- Test proxy connection: `python -m src.flashscore_scraper test-proxy`
- Verify proxy credentials
- Try reducing concurrency (`--concurrency 5`)
- Increase delays in config

### Rate limiting
- Reduce concurrency (default: 10)
- Increase delays (min_delay, max_delay)
- Use premium residential proxy

## 📝 Dependencies

Core:
- `tls-client` - HTTP client with browser fingerprinting
- `playwright` - Browser automation
- `pandas` - Data processing
- `pyarrow` - Parquet support
- `beautifulsoup4` - HTML parsing
- `rich` - Beautiful CLI output
- `typer` - CLI framework

## 📜 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

- Inspired by [FlashscoreScraping](https://github.com/gustavofariaa/FlashscoreScraping)
- Uses [tls_client](https://github.com/FlorianREGAZ/Python-Tls-Client) for advanced HTTP requests
- Proxy support via [DataImpulse](https://dataimpulse.com)

## ⚠️ Disclaimer

This tool is for educational and research purposes only. Please review Flashscore's Terms of Service and use responsibly. The authors are not responsible for any misuse of this software.

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📧 Contact

For questions or issues, please open a GitHub issue.

---

**Happy scraping! ⚽📊**
