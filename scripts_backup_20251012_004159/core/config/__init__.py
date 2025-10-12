"""
Configuration settings for the scraper.

This module provides access to all configuration settings through a centralized
configuration manager that supports environment variable overrides.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import os

# Base directories
BASE_DIR = Path(__file__).parent.parent.parent
CACHE_DIR = BASE_DIR.parent / "cache"  # Moved to project root
OUTPUT_DIR = BASE_DIR.parent / "data"
LOG_DIR = BASE_DIR.parent / "logs"

# Ensure directories exist
for directory in [CACHE_DIR, OUTPUT_DIR, LOG_DIR]:
    directory.mkdir(exist_ok=True, parents=True)

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
HEALTH_KEYWORDS: List[str] = [
    '手術歴', '骨折', '皮膚病', '屈腱炎', '腫れ', '咽頭虚脱', '脱臼', '跛行', '打撲'
]

# Database settings
DATABASE_CONFIG: Dict[str, str] = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'horsedb'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

# Scraper settings
SCRAPER_CONFIG: Dict[str, Any] = {
    'use_cache': os.getenv('SCRAPER_USE_CACHE', 'true').lower() == 'true',
    'max_retries': int(os.getenv('SCRAPER_MAX_RETRIES', str(MAX_RETRIES))),
    'timeout': int(os.getenv('SCRAPER_TIMEOUT', str(DEFAULT_TIMEOUT))),
    'user_agent': os.getenv(
        'SCRAPER_USER_AGENT',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    )
}

# Output settings
OUTPUT_CONFIG: Dict[str, Any] = {
    'output_dir': Path(os.getenv('OUTPUT_DIR', str(OUTPUT_DIR))),
    'output_file': Path(os.getenv('OUTPUT_FILE', str(OUTPUT_DIR / 'horses.json'))),
    'pretty_print': os.getenv('OUTPUT_PRETTY_PRINT', 'true').lower() == 'true',
    'ensure_ascii': os.getenv('OUTPUT_ENSURE_ASCII', 'false').lower() == 'true'
}

# Cache settings
CACHE_CONFIG: Dict[str, Any] = {
    'enabled': os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
    'cache_dir': Path(os.getenv('CACHE_DIR', str(CACHE_DIR))),
    'expire_after': int(os.getenv('CACHE_EXPIRE_AFTER', str(60 * 60 * 24 * 7))),  # 1週間
    'compress': os.getenv('CACHE_COMPRESS', 'true').lower() == 'true'
}

# Import the configuration manager
from .manager import ConfigManager, config  # noqa: E402

# Create a default config instance
try:
    config = ConfigManager()
except Exception as e:
    import logging
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to initialize configuration: {e}")
    raise
