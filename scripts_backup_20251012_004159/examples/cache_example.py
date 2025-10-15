"""
Cache Usage Example

Demonstrates how to use the new cache system for saving and retrieving HTML content.
"""

import logging
from pathlib import Path
import requests

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import our new cache components
from core.cache.cache_saver import get_cache_session
from core.utils.simple_html_saver import SimpleHTMLSaver

def fetch_and_cache(url: str, cache_dir: str = 'cache', html_dir: str = 'html_dump'):
    """Fetch a URL and save it to both cache and HTML dump.
    
    Args:
        url: URL to fetch
        cache_dir: Directory for cache storage
        html_dir: Directory for HTML dumps
    """
    logger = logging.getLogger('cache_example')
    
    # Initialize cache and HTML saver
    cache = get_cache_session(cache_dir)
    html_saver = SimpleHTMLSaver(html_dir)
    
    try:
        # Fetch the URL
        logger.info(f"Fetching URL: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Save to cache
        cache_path = cache.save_html(url, response.text)
        logger.info(f"Saved to cache: {cache_path}")
        
        # Also save to HTML dump
        html_path = html_saver.save(url, response.text)
        logger.info(f"Saved HTML dump: {html_path}")
        
        return cache_path, html_path
        
    except Exception as e:
        logger.error(f"Error processing {url}: {e}", exc_info=True)
        return None, None
    finally:
        # Clean up the cache session
        cache.cleanup()

if __name__ == "__main__":
    # Example usage
    test_urls = [
        "https://auction.rakuten.co.jp/items/list?keyword=%E7%AB%9C%E9%A6%AC",
        "https://auction.rakuten.co.jp/item/12345",
    ]
    
    for url in test_urls:
        cache_path, html_path = fetch_and_cache(url)
        if cache_path and html_path:
            print(f"Processed {url}")
            print(f"  Cache: {cache_path}")
            print(f"  HTML:  {html_path}")
        else:
            print(f"Failed to process {url}")
