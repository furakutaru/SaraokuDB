#!/usr/bin/env python3
"""
Test script to verify the extraction of horse information from the test cache file.
"""
import os
import sys
import json
from bs4 import BeautifulSoup
from improved_scraper import ImprovedRakutenScraper

# Set up logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_extraction.log', 'w', 'utf-8')
    ]
)
logger = logging.getLogger(__name__)

def test_extraction():
    """Test the extraction of horse information from the test cache file."""
    # Initialize the scraper in test mode
    scraper = ImprovedRakutenScraper(test_mode=True)
    
    # Path to the test cache file
    cache_file = "test_cache/fixed_auction_list_updated.html"
    
    if not os.path.exists(cache_file):
        logger.error(f"Test cache file not found: {os.path.abspath(cache_file)}")
        return
    
    logger.info(f"Testing extraction with cache file: {os.path.abspath(cache_file)}")
    
    # Read and parse the test cache file
    with open(cache_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all horse cards
    horse_cards = soup.select('.auctionTableCard')
    logger.info(f"Found {len(horse_cards)} horse cards in the test cache")
    
    # Extract information from each horse card
    all_horses = []
    for i, card in enumerate(horse_cards):
        logger.info(f"\n{'='*50}\nProcessing horse card {i+1}")
        horse_info = scraper._extract_horse_info_from_row(card)
        all_horses.append(horse_info)
        logger.info(f"Extracted info: {json.dumps(horse_info, ensure_ascii=False, indent=2)}")
    
    # Save the results to a JSON file
    output_file = 'test_extraction_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_horses, f, ensure_ascii=False, indent=2, default=str)
    
    logger.info(f"\nExtraction test completed. Results saved to {output_file}")
    logger.info(f"Successfully extracted information for {len(all_horses)} horses")
    
    # Print a summary of the extracted data
    if all_horses:
        logger.info("\nExtraction Summary:")
        for i, horse in enumerate(all_horses[:5]):  # Show first 5 for brevity
            logger.info(f"{i+1}. {horse.get('name', 'N/A')} - Age: {horse.get('age', 'N/A')}, "
                       f"Sex: {horse.get('sex', 'N/A')}, Seller: {horse.get('seller', 'N/A')}")
        if len(all_horses) > 5:
            logger.info(f"... and {len(all_horses) - 5} more")

if __name__ == "__main__":
    test_extraction()
