"""
RakutenScraperの初期化テスト
"""
import os
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from scrapers.rakuten_scraper import RakutenAuctionScraper

def test_rakuten_scraper_init():
    # Test initialization of RakutenAuctionScraper
    try:
        # Initialize the scraper
        scraper = RakutenAuctionScraper()
        print("✅ RakutenAuctionScraper initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize RakutenScraper: {e}")
        return False

if __name__ == "__main__":
    test_rakuten_scraper_init()
