#!/usr/bin/env python3
"""
ImprovedRakutenScraperの動作テスト用スクリプト
"""
import os
import sys
import logging
from pathlib import Path
from improved_scraper import ImprovedRakutenScraper
from cache_manager import CacheManager

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_scraper():
    """スクレイパーのテストを実行"""
    try:
        logger.info("===== スクレイパーテストを開始 =====")
        
        # キャッシュディレクトリを設定
        cache_dir = "test_scraper_cache"
        os.makedirs(cache_dir, exist_ok=True)
        
        # キャッシュマネージャーを初期化
        cache_manager = CacheManager(cache_dir)
        
        # スクレイパーを初期化
        scraper = ImprovedRakutenScraper(cache_manager=cache_manager)
        
        # テスト用のURL（楽天競馬オークションのトップページ）
        test_url = "https://auction.keiba.rakuten.co.jp/"
        
        # 1回目: ウェブから取得（キャッシュに保存される）
        logger.info("1回目: ウェブから取得（キャッシュに保存）")
        horses1 = scraper.scrape_horse_list(test_url, use_cache=True)
        logger.info(f"取得した馬の数: {len(horses1) if horses1 else 0}")
        
        # 2回目: キャッシュから読み込み
        logger.info("2回目: キャッシュから読み込み")
        horses2 = scraper.scrape_horse_list(test_url, use_cache=True)
        logger.info(f"取得した馬の数: {len(horses2) if horses2 else 0}")
        
        # キャッシュの確認
        cache_key = f"list_{hashlib.md5(test_url.encode()).hexdigest()}"
        cache_file = Path(cache_dir) / f"{cache_key}.html"
        if cache_file.exists():
            logger.info(f"キャッシュファイルが正常に保存されました: {cache_file}")
            logger.info(f"キャッシュファイルサイズ: {os.path.getsize(cache_file)} バイト")
        else:
            logger.error("キャッシュファイルが保存されていません")
        
        logger.info("===== スクレイパーテスト完了 =====")
        
    except Exception as e:
        logger.error(f"テスト中にエラーが発生しました: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    import hashlib  # キャッシュキー生成用に追加
    sys.exit(test_scraper())
