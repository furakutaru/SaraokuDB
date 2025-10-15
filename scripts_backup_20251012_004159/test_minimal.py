#!/usr/bin/env python3
"""
Minimal test script for RakutenAuctionScraper
"""
import sys
import os
import logging
from pathlib import Path

# Set up basic logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the scraper
try:
    from scripts.improved_scraper import RakutenAuctionScraper, ImprovedRakutenScraper, ScraperConfig
    logger.info("Successfully imported scraper modules")
    
    # Test basic initialization
    config = ScraperConfig(use_cache=False, max_workers=1)
    logger.info("ScraperConfig created successfully")
    
    scraper = RakutenAuctionScraper()
    logger.info("RakutenAuctionScraper initialized successfully")
    
    # Test a simple method
    print("\nTesting scrape_all_horses method...")
    try:
        result = scraper.scrape_all_horses()
        print(f"Result type: {type(result)}")
        if isinstance(result, list):
            print(f"Found {len(result)} horses")
            if result:
                print("First horse:", result[0])
    except Exception as e:
        logger.error("Error in scrape_all_horses: %s", str(e), exc_info=True)
    
except ImportError as e:
    logger.error("Failed to import modules: %s", str(e), exc_info=True)
    sys.exit(1)
except Exception as e:
    logger.error("Unexpected error: %s", str(e), exc_info=True)
    sys.exit(1)
