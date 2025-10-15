import os
import sys
import time
from pathlib import Path

# Add the scripts directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))

from improved_scraper import CacheManager, ScraperConfig, ImprovedRakutenScraper

def test_cache():
    # Create a test cache directory
    test_cache_dir = Path("test_cache")
    if not test_cache_dir.exists():
        test_cache_dir.mkdir()
    
    # Initialize cache manager
    cache = CacheManager(test_cache_dir)
    
    # Test data
    test_url = "https://example.com/test"
    test_content = "<html><body>Test content</body></html>"
    
    # Test saving to cache
    print(f"Saving to cache: {test_url}")
    cache.save_html(test_url, test_content)
    
    # Test loading from cache
    print(f"Loading from cache: {test_url}")
    loaded_content = cache.load_html(test_url)
    
    if loaded_content == test_content:
        print("✓ Basic cache test passed!")
    else:
        print("✗ Basic cache test failed!")
        return False
    
    # Test with real scraper
    print("\nTesting with real scraper...")
    config = ScraperConfig(
        use_cache=True,
        cache_dir=test_cache_dir,
        max_workers=1  # Use 1 worker for testing
    )
    
    scraper = ImprovedRakutenScraper(config)
    test_auction_url = "https://auction.keiba.rakuten.co.jp/"
    
    print(f"Fetching {test_auction_url}...")
    start_time = time.time()
    horses = scraper.scrape_horse_list(test_auction_url, use_cache=True)
    end_time = time.time()
    
    print(f"Fetched {len(horses)} horses in {end_time - start_time:.2f} seconds")
    
    # Check if cache files were created
    cache_files = list(test_cache_dir.glob('**/*.html'))
    print(f"Found {len(cache_files)} cache files in {test_cache_dir}")
    
    if not horses:
        print("✗ No horses found in the page")
        return False
    
    print("\nFirst horse details:")
    for key, value in horses[0].items():
        print(f"{key}: {value}")
    
    print("\n✓ Scraper test completed successfully!")
    return True

if __name__ == "__main__":
    test_cache()
