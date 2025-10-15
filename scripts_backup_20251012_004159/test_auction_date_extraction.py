#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
オークション日抽出のテストスクリプト

このスクリプトは、オークション日の抽出機能をテストします。
"""

import os
import sys
import logging
from pathlib import Path

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.improved_scraper import ImprovedRakutenScraper, ScraperConfig

# ロギング設定
def setup_logging():
    """ロギングの設定を行う"""
    log_dir = Path('debug_logs')
    log_dir.mkdir(exist_ok=True, mode=0o755)
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'test_auction_date.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def test_auction_date_extraction():
    """オークション日抽出のテストを実行する"""
    logger = setup_logger()
    logger.info("オークション日抽出テストを開始します")
    
    # テスト用の設定
    config = ScraperConfig(
        use_cache=True,
        max_retries=3,
        timeout=30
    )
    
    # スクレイパーを初期化
    scraper = ImprovedRakutenScraper(config=config)
    
    # テスト用の馬ID（実際のテストでは適切な馬IDに置き換えてください）
    test_horse_id = "12345"  # テスト用の適切な馬IDに置き換えてください
    
    try:
        # オークション日を取得
        auction_date = scraper.get_auction_date(url=f"https://auction.keiba.rakuten.co.jp/item/{test_horse_id}")
        
        if auction_date:
            logger.info(f"オークション日を正常に取得しました: {auction_date}")
            return True, f"Success: {auction_date}"
        else:
            logger.warning("オークション日を取得できませんでした")
            return False, "Failed to extract auction date"
            
    except Exception as e:
        logger.error(f"テスト中にエラーが発生しました: {e}", exc_info=True)
        return False, f"Error: {str(e)}"

if __name__ == "__main__":
    success, message = test_auction_date_extraction()
    print(f"テスト結果: {message}")
    sys.exit(0 if success else 1)
