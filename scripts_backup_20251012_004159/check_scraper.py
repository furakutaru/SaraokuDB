#!/usr/bin/env python3
"""
スクレイパーの動作確認用スクリプト
"""
import os
import sys
import logging
import hashlib
from pathlib import Path

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# モジュールのインポート
try:
    from scripts.improved_scraper import ImprovedRakutenScraper
    from scripts.cache_manager import CacheManager
    logger.info("モジュールのインポートに成功しました")
except ImportError as e:
    logger.error(f"モジュールのインポートに失敗しました: {e}")
    sys.exit(1)

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
        
        # 1回目: ウェブから取得（キャッシュに保存）
        logger.info("1回目: ウェブから取得（キャッシュに保存）")
        horses1 = scraper.scrape_horse_list(test_url, use_cache=True)
        logger.info(f"取得した馬の数: {len(horses1) if horses1 else 0}")
        
        # キャッシュの確認
        cache_key = f"list_{hashlib.md5(test_url.encode()).hexdigest()}"
        cache_file = Path(cache_dir) / f"{cache_key}.html"
        if cache_file.exists():
            logger.info(f"✅ キャッシュファイルが存在します: {cache_file}")
            logger.info(f"    サイズ: {os.path.getsize(cache_file)} バイト")
        else:
            logger.error(f"❌ キャッシュファイルが存在しません: {cache_file}")
        
        logger.info("===== スクレイパーテスト完了 =====")
        return 0
        
    except Exception as e:
        logger.error(f"テスト中にエラーが発生しました: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(test_scraper())
