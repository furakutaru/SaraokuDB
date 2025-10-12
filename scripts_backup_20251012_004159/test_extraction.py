#!/usr/bin/env python3
"""
Test script to verify the extraction of horse information from the test cache file.
"""
import os
import sys
import re
import json
from pathlib import Path
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

def extract_weight(html_content):
    """Extract weight from HTML content using the current implementation."""
    # パターン: 「最終出走馬体重：392kg」の形式のみを抽出
    weight_match = re.search(r'最終出走馬体重[：:](\d+)kg', html_content)
    
    if weight_match:
        try:
            weight = int(weight_match.group(1))
            logger.debug(f"馬体重を抽出しました: {weight}kg")
            return weight
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"馬体重の数値変換に失敗: {weight_match.groups()} - {str(e)}")
    
    # デバッグ用にHTMLの一部を出力
    logger.warning("馬体重を抽出できませんでした")
    debug_section = re.search(r'(?:最終出走馬体重|馬体重)[^\d]*(\d+)', html_content[:1000])
    if debug_section:
        logger.debug(f"一致しなかったパターンの例: {debug_section.group(0)}")
    return None

def test_weight_extraction(html_content, horse_name):
    """Test weight extraction from HTML content."""
    logger.info(f"\n{'='*50}")
    logger.info(f"Testing weight extraction for: {horse_name}")
    
    weight = extract_weight(html_content)
    if weight is not None:
        logger.info(f"✅ 成功: 馬体重 = {weight}kg")
        return True
    else:
        logger.warning("❌ 失敗: 馬体重を抽出できませんでした")
        # デバッグ用にHTMLの一部を表示
        weight_section = re.search(r'(?:最終出走馬体重|馬体重)[^<]*', html_content)
        if weight_section:
            logger.debug(f"一致したセクション: {weight_section.group(0).strip()}")
        return False

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
    weight_test_results = []
    
    for i, card in enumerate(horse_cards):
        logger.info(f"\n{'='*50}\nProcessing horse card {i+1}")
        
        # Extract basic horse info
        horse_info = scraper._extract_horse_info_from_row(card)
        all_horses.append(horse_info)
        logger.info(f"Extracted info: {json.dumps(horse_info, ensure_ascii=False, indent=2)}")
        
        # Test weight extraction if detail link is available
        if 'detail_link' in horse_info and horse_info['detail_link']:
            try:
                # Get the directory of the current cache file
                cache_dir = os.path.dirname(os.path.abspath(cache_file))
                
                # Extract item ID from detail link
                item_id = re.search(r'item[_-]?(\d+)', horse_info['detail_link'])
                if item_id:
                    item_id = item_id.group(1)
                    detail_file = os.path.join(cache_dir, 'details', f"sess_*_item_{item_id}.html")
                    
                    # Find matching detail file
                    import glob
                    matching_files = glob.glob(detail_file)
                    
                    if matching_files:
                        with open(matching_files[0], 'r', encoding='utf-8') as f:
                            detail_content = f.read()
                            # Test weight extraction
                            success = test_weight_extraction(detail_content, horse_info.get('name', f'Horse {i+1}'))
                            weight_test_results.append(success)
            except Exception as e:
                logger.error(f"Error testing weight extraction: {str(e)}")
    
    # Save the results to a JSON file
    output_file = 'test_extraction_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_horses, f, ensure_ascii=False, indent=2, default=str)
    
    # Print test summary
    logger.info(f"\n{'='*50}")
    logger.info("Extraction Test Summary:")
    logger.info(f"- Successfully processed {len(all_horses)} horses")
    
    if weight_test_results:
        success_count = sum(1 for r in weight_test_results if r)
        logger.info(f"- Weight extraction: {success_count}/{len(weight_test_results)} successful ({success_count/len(weight_test_results)*100:.1f}%)")
    
    logger.info(f"\nDetailed results saved to {output_file}")
    
    # Print a summary of the extracted data
    if all_horses:
        logger.info("\nExtraction Summary (first 5 horses):")
        for i, horse in enumerate(all_horses[:5]):
            weight_info = f"Weight: {horse.get('weight', 'N/A')}kg" if 'weight' in horse else ""
            logger.info(f"{i+1}. {horse.get('name', 'N/A')} - "
                      f"Age: {horse.get('age', 'N/A')}, "
                      f"Sex: {horse.get('sex', 'N/A')}, "
                      f"{weight_info}")
        if len(all_horses) > 5:
            logger.info(f"... and {len(all_horses) - 5} more")

if __name__ == "__main__":
    test_extraction()
