#!/usr/bin/env python3
"""
Test script to verify the extraction of horse weight information.
"""
import os
import sys
import re
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_weight_extraction.log', 'w', 'utf-8')
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
            logger.info(f"馬体重を抽出しました: {weight}kg")
            return weight
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"馬体重の数値変換に失敗: {weight_match.groups()} - {str(e)}")
    
    # デバッグ用にHTMLの一部を出力
    logger.warning("馬体重を抽出できませんでした")
    debug_section = re.search(r'(?:最終出走馬体重|馬体重)[^\d]*(\d+)', html_content[:1000])
    if debug_section:
        logger.debug(f"一致しなかったパターンの例: {debug_section.group(0)}")
    return None

def test_weight_extraction():
    """Test weight extraction from test files."""
    test_files = [
        "debug_detail_page.html",  # テスト用のHTMLファイル
        "cache/20250818/details/sess_14705.html"  # 別のテストファイル
    ]
    
    for file_path in test_files:
        full_path = os.path.join(os.path.dirname(__file__), '..', file_path)
        if not os.path.exists(full_path):
            logger.warning(f"Test file not found: {full_path}")
            continue
            
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing file: {file_path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 馬体重を抽出
        weight = extract_weight(html_content)
        
        if weight is not None:
            logger.info(f"✅ 成功: 馬体重 = {weight}kg")
        else:
            logger.warning("❌ 失敗: 馬体重を抽出できませんでした")
            
            # デバッグ用にHTMLの一部を表示
            weight_section = re.search(r'(?:最終出走馬体重|馬体重)[^<]*', html_content)
            if weight_section:
                logger.debug(f"一致したセクション: {weight_section.group(0).strip()}")

if __name__ == "__main__":
    test_weight_extraction()
