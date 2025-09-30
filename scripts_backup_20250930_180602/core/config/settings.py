"""Configuration settings for the scraper."""
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent.parent
CACHE_DIR = BASE_DIR / "html_cache"
OUTPUT_DIR = BASE_DIR.parent / "data"
LOG_DIR = BASE_DIR / "logs"

# Base URL for scraping
BASE_URL = "https://auction.keiba.rakuten.co.jp/"

# Request settings
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
BACKOFF_FACTOR = 1
MAX_WORKERS = 4

# Logging settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = LOG_DIR / "scraper.log"

# Health keywords for disease detection
HEALTH_KEYWORDS = [
    '手術歴', '骨折', '皮膚病', '屈腱炎', '腫れ', '咽頭虚脱', '脱臼', '跛行', '打撲'
]

# Ensure directories exist
for directory in [CACHE_DIR, OUTPUT_DIR, LOG_DIR]:
    directory.mkdir(exist_ok=True, parents=True)
