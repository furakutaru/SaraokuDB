#!/usr/bin/env python3
"""
直接スクレイパーのテストを実行するスクリプト
"""
import os
import sys
import logging
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
sys.path.insert(0, str(Path(__file__).parent))  # scriptsディレクトリをパスに追加

# 必要なモジュールをインポート
try:
    from scripts.improved_scraper import ImprovedRakutenScraper
    from scripts.cache_manager import CacheManager
    logger.info("モジュールのインポートに成功しました")
except ImportError as e:
    logger.error(f"モジュールのインポートに失敗しました: {e}")
    sys.exit(1)

def main():
    """メインのテスト関数"""
    try:
        logger.info("===== スクレイパーテストを開始 =====")
        
        # キャッシュディレクトリを設定
        cache_dir = "test_cache"
        os.makedirs(cache_dir, exist_ok=True)
        
        # キャッシュマネージャーを初期化
        cache_manager = CacheManager(cache_dir)
        logger.info(f"キャッシュディレクトリ: {os.path.abspath(cache_dir)}")
        
        # スクレイパーを初期化
        scraper = ImprovedRakutenScraper(cache_manager=cache_manager)
        
        # テスト用のURL
        test_url = "https://auction.keiba.rakuten.co.jp/"
        
        # スクレイピングを実行
        logger.info(f"スクレイピングを開始: {test_url}")
        result = scraper.scrape_horse_list(test_url, use_cache=True)
        
        # 結果を表示
        if result is not None:
            logger.info(f"スクレイピング結果: {len(result)}件の馬データを取得")
            if result:
                logger.info("最初の馬のデータ:")
                for key, value in result[0].items():
                    logger.info(f"  {key}: {value}")
        else:
            logger.error("スクレイピングに失敗しました")
        
        # キャッシュの確認
        cache_key = f"list_{hash(test_url) & 0xFFFFFFFFFFFFFFFF}"  # 64ビットのハッシュ値
        cache_file = Path(cache_dir) / f"{cache_key}.html"
        
        if cache_file.exists():
            logger.info(f"キャッシュファイルが存在します: {cache_file}")
            logger.info(f"キャッシュファイルサイズ: {os.path.getsize(cache_file)} バイト")
        else:
            logger.warning(f"キャッシュファイルが存在しません: {cache_file}")
            
            # キャッシュディレクトリの内容を確認
            logger.info("キャッシュディレクトリの内容:")
            for f in Path(cache_dir).glob("*"):
                logger.info(f"  - {f.name} ({os.path.getsize(f)} バイト)")
        
        logger.info("===== スクレイパーテスト完了 =====")
        return 0
        
    except Exception as e:
        logger.error(f"テスト中にエラーが発生しました: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
