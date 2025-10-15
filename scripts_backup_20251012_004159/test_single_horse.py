#!/usr/bin/env python3
"""
Test script to verify the extraction of horse weight information from a single cache file.
"""
import os
import sys
import re
import logging
from pathlib import Path
from bs4 import BeautifulSoup

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent))

# Import the extractor class
from scripts.components.horse_info_extractor import HorseInfoExtractor

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # DEBUGレベルで詳細なログを出力
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

def test_single_horse(html_file_path):
    """Test weight extraction from a single HTML file."""
    logger.info(f"Testing weight extraction for: {html_file_path}")
    
    # ファイルの存在確認
    if not os.path.exists(html_file_path):
        logger.error(f"File not found: {html_file_path}")
        return
    
    # HTMLファイルを読み込む
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # BeautifulSoupでパース
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 馬情報を含む要素を特定（必要に応じて調整）
    horse_element = soup.find('table', {'class': 'horse_info'}) or soup
    
    # 抽出器を初期化
    extractor = HorseInfoExtractor(logger=logger)
    
    # 体重を抽出
    weight = extractor._extract_weight(horse_element)
    
    # 結果を表示
    logger.info(f"Extracted weight: {weight}kg")
    
    # デバッグ用にHTMLの一部を表示
    logger.debug(f"First 500 chars of HTML: {str(horse_element)[:500]}...")
    
    return weight

if __name__ == "__main__":
    # テストする馬のHTMLファイルパス
    test_file = "/Users/yum.ishii/SaraokuDB/cache/20250929/details/15058.html"
    
    logger.info(f"Starting test for horse ID: 15058")
    weight = test_single_horse(test_file)
    
    if weight is not None:
        logger.info(f"Successfully extracted weight: {weight}kg")
    else:
        logger.warning("Failed to extract weight")
    
    logger.info("Test completed")
