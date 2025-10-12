#!/usr/bin/env python3
"""
オークション日を抽出するスクリプト
"""
import os
import re
import logging
from bs4 import BeautifulSoup
from datetime import datetime

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

def extract_auction_date(html_content: str) -> str:
    """HTMLからオークション日を抽出する"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. キャッシュのメタデータから日付を取得
        cache_meta = soup.find(string=lambda text: 'CACHE_METADATA' in str(text))
        if cache_meta:
            # キャッシュの保存日時を取得
            match = re.search(r'"saved_at":"([^"]+)"', cache_meta)
            if match:
                saved_at = match.group(1)
                # 日付部分のみを抽出 (YYYY-MM-DD)
                auction_date = saved_at.split('T')[0]
                logger.debug(f"キャッシュの保存日からオークション日を抽出: {auction_date}")
                return auction_date
        
        # 2. 開始日時を探す
        date_patterns = [
            (r'(\d{4})年(\d{1,2})月(\d{1,2})日', 'YYYY年MM月DD日形式'),
            (r'(\d{4})/(\d{1,2})/(\d{1,2})', 'YYYY/MM/DD形式'),
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', 'YYYY-MM-DD形式'),
        ]
        
        # 開始日時や終了日時を含む可能性のあるテキストを検索
        date_keywords = ['開始日時', '終了日時', 'オークション日', '開催日', 'auction_date']
        
        for keyword in date_keywords:
            elements = soup.find_all(string=lambda text: text and keyword in str(text))
            for elem in elements:
                parent = elem.parent
                # 同じ行のテキストを取得
                text = parent.get_text(' ', strip=True)
                logger.debug(f"キーワード '{keyword}' を含むテキスト: {text[:100]}...")
                
                # 日付パターンにマッチするか確認
                for pattern, pattern_name in date_patterns:
                    match = re.search(pattern, text)
                    if match:
                        year, month, day = match.groups()
                        date_str = f"{year}-{int(month):02d}-{int(day):02d}"
                        logger.debug(f"{pattern_name} で日付を抽出: {date_str}")
                        return date_str
        
        # 3. ページ内の日付を探す
        for pattern, pattern_name in date_patterns:
            matches = re.finditer(pattern, soup.get_text())
            for match in matches:
                year, month, day = match.groups()
                date_str = f"{year}-{int(month):02d}-{int(day):02d}"
                logger.debug(f"テキストから{pattern_name}で日付を抽出: {date_str}")
                return date_str
        
        logger.warning("オークション日が見つかりませんでした")
        return ""
        
    except Exception as e:
        logger.error(f"オークション日の抽出中にエラーが発生しました: {str(e)}")
        return ""

def test_auction_date_extraction(html_file_path: str):
    """指定されたHTMLファイルからオークション日を抽出してテスト"""
    logger.info(f"Testing auction date extraction for: {html_file_path}")
    
    # ファイルの存在確認
    if not os.path.exists(html_file_path):
        logger.error(f"File not found: {html_file_path}")
        return
    
    # HTMLファイルを読み込む
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # オークション日を抽出
    auction_date = extract_auction_date(html_content)
    
    # 結果を表示
    if auction_date:
        logger.info(f"抽出されたオークション日: {auction_date}")
    else:
        logger.warning("オークション日を抽出できませんでした")
    
    return auction_date

if __name__ == "__main__":
    # テストする馬のHTMLファイルパス
    test_file = "/Users/yum.ishii/SaraokuDB/cache/20250929/details/15058.html"
    
    logger.info(f"Starting auction date extraction test for horse ID: 15058")
    auction_date = test_auction_date_extraction(test_file)
    
    if auction_date:
        logger.info(f"Successfully extracted auction date: {auction_date}")
    else:
        logger.warning("Failed to extract auction date")
    
    logger.info("Test completed")
