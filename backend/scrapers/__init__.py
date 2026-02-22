# Scrapers package

# Import with absolute package path to work under Docker/Render
from backend.scrapers.rakuten_scraper import RakutenAuctionScraper

__all__ = ['RakutenAuctionScraper']
