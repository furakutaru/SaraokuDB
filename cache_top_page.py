#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
楽天競馬オークションのトップページをキャッシュに保存するスクリプト
"""

import logging
from pathlib import Path
import sys

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.improved_scraper import ImprovedRakutenScraper, ScraperConfig

def setup_logging():
    """ロギングの設定"""
    log_dir = Path('debug_logs')
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'cache_top_page.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def main():
    """メイン処理"""
    # ロギングの設定
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # キャッシュを使用する設定（必ずキャッシュを有効にする）
        config = ScraperConfig(
            use_cache=True,  # キャッシュを使用
            max_retries=3,   # リトライ回数を増やす
            max_workers=1,   # 並列処理を無効化
            timeout=30,      # タイムアウトを長めに設定
            use_mobile=True  # モバイル版を使用
        )
        
        logger.info("楽天競馬オークションのトップページをキャッシュに保存します...")
        
        # スクレイパーを初期化
        scraper = ImprovedRakutenScraper(config=config)
        
        # トップページのURL
        top_url = "https://auction.keiba.rakuten.co.jp/"
        
        # トップページを取得（キャッシュに保存される）
        logger.info(f"トップページを取得中: {top_url}")
        html_content = scraper._fetch_html(top_url, use_cache=False)  # use_cache=Falseで必ず取得
        
        if html_content:
            logger.info("トップページの取得に成功し、キャッシュに保存しました")
            
            # キャッシュディレクトリを確認
            cache_dir = Path('cache')
            if cache_dir.exists():
                # キャッシュファイルを探す
                cache_files = list(cache_dir.glob('**/*'))
                logger.info(f"キャッシュディレクトリ: {cache_dir.absolute()}")
                logger.info(f"キャッシュファイル数: {len(cache_files)}")
                
                # トップページのキャッシュが存在するか確認
                top_cache_exists = any('auction.keiba.rakuten.co.jp' in str(f) for f in cache_files)
                if top_cache_exists:
                    logger.info("トップページのキャッシュが正常に保存されました")
                else:
                    logger.warning("トップページのキャッシュが見つかりませんでした")
                    
            return True
        else:
            logger.error("トップページの取得に失敗しました")
            return False
            
    except Exception as e:
        logger.exception("予期せぬエラーが発生しました")
        return False

if __name__ == "__main__":
    main()
