#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
スクレイパーのデバッグ用スクリプト
"""
import logging
import sys
from pathlib import Path

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("テストスクリプトを開始します")
        
        # スクレイパーのインポート
        from improved_scraper import ImprovedRakutenScraper, ScraperConfig
        
        # 設定
        config = ScraperConfig(
            use_cache=False,  # キャッシュを無効化
            max_workers=1,    # シングルスレッドで実行
            timeout=30,       # タイムアウト30秒
            max_retries=3     # 最大3回リトライ
        )
        
        logger.info("スクレイパーを初期化しています...")
        scraper = ImprovedRakutenScraper(config=config)
        
        # テスト用のURL（必要に応じて変更）
        test_url = "https://auction.keiba.rakuten.co.jp/"
        
        logger.info("スクレイピングを開始します...")
        result = scraper.scrape_horse_list(url=test_url, use_cache=False)
        
        if result:
            logger.info(f"成功: {len(result)}件の馬情報を取得しました")
            # 最初の3件を表示
            for i, horse in enumerate(result[:3], 1):
                logger.info(f"馬{i}: {horse.get('name', '名前不明')} (性別: {horse.get('sex', '不明')}, 年齢: {horse.get('age', '不明')})")
        else:
            logger.warning("馬情報を取得できませんでした")
            
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
