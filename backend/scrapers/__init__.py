# Scrapers package

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Import from the local rakuten_scraper
from scrapers.rakuten_scraper import RakutenAuctionScraper

__all__ = ['RakutenAuctionScraper']