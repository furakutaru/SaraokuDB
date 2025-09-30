#!/usr/bin/env python3
"""
Test script to verify the extraction of horse weight information from live URLs.
"""
import logging
import sys
import requests
from pathlib import Path
from bs4 import BeautifulSoup

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent))

# Import the extractor class
from scripts.components.horse_info_extractor import HorseInfoExtractor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_weight_from_url.log', 'w', 'utf-8')
    ]
)
logger = logging.getLogger(__name__)

def get_horse_weight_from_url(url: str) -> dict:
    """
    Extract horse weight from a given URL.
    
    Args:
        url: URL of the horse detail page
        
    Returns:
        dict: Dictionary containing the URL and extracted weight, or error information
    """
    result = {
        'url': url,
        'weight_kg': None,
        'success': False,
        'error': None
    }
    
    try:
        # Set headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Fetch the page
        logger.info(f"Fetching URL: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize the extractor
        extractor = HorseInfoExtractor()
        
        # Try to extract weight using the extractor
        weight = extractor._extract_weight(soup)
        
        if weight is not None:
            result['weight_kg'] = weight
            result['success'] = True
            logger.info(f"Successfully extracted weight: {weight}kg from {url}")
        else:
            result['error'] = "Weight not found"
            logger.warning(f"Weight not found in {url}")
            
            # Debug: Save HTML for inspection
            with open('debug_weight_extraction.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info("Saved debug HTML to debug_weight_extraction.html")
            
    except Exception as e:
        error_msg = f"Error processing {url}: {str(e)}"
        result['error'] = error_msg
        logger.error(error_msg, exc_info=True)
    
    return result

def main():
    """Main function to test weight extraction from URLs."""
    # Example URLs (replace with actual URLs from the top page)
    test_urls = [
        # Add test URLs here
    ]
    
    if not test_urls:
        logger.error("No test URLs provided. Please add some URLs to test.")
        return
    
    logger.info(f"Starting weight extraction test for {len(test_urls)} URLs...")
    
    results = []
    for url in test_urls:
        result = get_horse_weight_from_url(url)
        results.append(result)
    
    # Print summary
    success_count = sum(1 for r in results if r['success'])
    logger.info(f"Test completed. Success: {success_count}/{len(results)}")
    
    # Print detailed results
    for i, result in enumerate(results, 1):
        status = "SUCCESS" if result['success'] else "FAILED"
        logger.info(f"{i}. {status} - URL: {result['url']}")
        if result['success']:
            logger.info(f"   Weight: {result['weight_kg']}kg")
        else:
            logger.error(f"   Error: {result['error']}")

if __name__ == "__main__":
    main()
