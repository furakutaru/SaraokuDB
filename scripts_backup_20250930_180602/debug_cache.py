#!/usr/bin/env python3
"""
Debug script to analyze the structure of the test cache file.
"""
import os
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_output.log', 'w', 'utf-8')
    ]
)
logger = logging.getLogger(__name__)

def analyze_horse_card(card, index):
    """Analyze a single horse card and extract available information."""
    logger.info(f"\n{'='*50}\nAnalyzing horse card {index+1}")
    logger.info(f"Card classes: {card.get('class', [])}")
    
    # Extract all text content
    text_content = card.get_text(' | ', strip=True)
    logger.info(f"Text content (first 200 chars): {text_content[:200]}...")
    
    # Look for specific elements
    name_elem = card.select_one('.horseName, [class*="name"], [class*="title"]')
    if name_elem:
        logger.info(f"Name element found: {name_elem.get_text(strip=True)}")
    
    # Look for price information
    price_elem = card.select_one('.price, [class*="price"], [class*="bid"]')
    if price_elem:
        logger.info(f"Price element: {price_elem.get_text(strip=True)}")
    
    # Look for seller information
    seller_elem = card.select_one('.seller, [class*="seller"], [class*="owner"]')
    if seller_elem:
        logger.info(f"Seller element: {seller_elem.get_text(strip=True)}")
    
    # Look for horse details (age, sex, etc.)
    details = card.select('.detail, [class*="detail"], [class*="info"]')
    for i, detail in enumerate(details[:3]):  # Show first 3 details
        logger.info(f"Detail {i+1}: {detail.get_text(strip=True)}")
    
    # Look for links that might be to horse details
    links = card.select('a[href*="detail"], a[href*="horse"]')
    for i, link in enumerate(links[:2]):  # Show first 2 links
        logger.info(f"Link {i+1} - Text: {link.get_text(strip=True)[:50]} | Href: {link.get('href', '')}")

def analyze_cache_file(file_path):
    """Analyze the structure of the test cache file."""
    if not os.path.exists(file_path):
        logger.error(f"Cache file not found: {file_path}")
        return
    
    logger.info(f"Analyzing cache file: {file_path}")
    logger.info(f"File size: {os.path.getsize(file_path) / 1024:.2f} KB")
    
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')
    
    # Look for all auctionTableCard elements
    horse_cards = soup.select('.auctionTableCard')
    logger.info(f"Found {len(horse_cards)} auctionTableCard elements")
    
    if horse_cards:
        # Analyze the first 2 cards in detail
        for i, card in enumerate(horse_cards[:2]):
            analyze_horse_card(card, i)
    else:
        logger.warning("No auctionTableCard elements found. Looking for other potential containers...")
        
        # Try to find any divs with content
        divs = soup.find_all('div')
        logger.info(f"Found {len(divs)} divs in total")
        
        # Look for divs with content that might be horse items
        for i, div in enumerate(divs[:20]):
            if div.get_text(strip=True):
                classes = div.get('class', [])
                if classes and any(c for c in classes if 'horse' in c or 'item' in c or 'card' in c):
                    logger.info(f"Potential horse container - Div {i+1} classes: {classes}")
                    logger.info(f"Content sample: {div.get_text(strip=True)[:100]}...")
    
    # Save the full HTML for manual inspection
    with open('debug_output.html', 'w', encoding='utf-8') as f:
        f.write(str(soup))
    logger.info("\nSaved full parsed HTML to debug_output.html for manual inspection")
    
    # Save first 1000 characters of the file
    logger.info("\nFirst 1000 characters of the file:")
    logger.info(content[:1000])

if __name__ == "__main__":
    cache_file = "/Users/yum.ishii/SaraokuDB/scripts/test_cache/fixed_auction_list_updated.html"
    analyze_cache_file(cache_file)
