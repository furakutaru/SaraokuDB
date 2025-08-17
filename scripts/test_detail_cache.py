#!/usr/bin/env python3
"""
詳細ページのキャッシュ保存をテストするスクリプト

このスクリプトは、詳細ページのキャッシュ保存機能が正しく動作するかをテストします。
"""

import os
import sys
import logging
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.improved_scraper import ImprovedRakutenScraper

# ロギング設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_detail_cache():
    """詳細ページのキャッシュ保存をテスト"""
    
    # テスト用のキャッシュディレクトリ
    test_cache_dir = "test_detail_cache"
    
    try:
        # スクレイパーを初期化（キャッシュ保存有効）
        scraper = ImprovedRakutenScraper(
            timeout=30,
            max_retries=3,
            test_mode=False,  # 本番モードでキャッシュ保存をテスト
            cache_dir=test_cache_dir
        )
        
        # キャッシュセッションを開始
        try:
            scraper.current_session_id = scraper.cache_manager.start_new_session()
            logger.info(f"キャッシュセッションを開始しました: {scraper.current_session_id}")
        except Exception as e:
            logger.error(f"キャッシュセッションの開始に失敗: {e}")
            return
        
        logger.info("詳細ページのキャッシュ保存テストを開始します")
        
        # テスト用の詳細ページURL（実際のURLに置き換えてください）
        test_urls = [
            "https://auction.keiba.rakuten.co.jp/item/14687",
            "https://auction.keiba.rakuten.co.jp/item/14688",
            "https://auction.keiba.rakuten.co.jp/item/14689"
        ]
        
        # 各URLで詳細ページを取得してキャッシュに保存
        for url in test_urls:
            logger.info(f"詳細ページを取得中: {url}")
            
            try:
                # 馬IDを抽出
                horse_id = scraper._extract_horse_id(url)
                logger.info(f"抽出された馬ID: {horse_id}")
                
                # 詳細ページを取得（キャッシュ保存有効）
                detail_data = scraper.scrape_horse_detail(
                    url,
                    horse_name="テスト馬",
                    horse_id=horse_id,
                    save_html=True
                )
                
                if detail_data:
                    logger.info(f"詳細データを取得しました: {detail_data.get('name', 'N/A')}")
                else:
                    logger.warning(f"詳細データの取得に失敗: {url}")
                    
            except Exception as e:
                logger.error(f"詳細ページの取得中にエラーが発生: {url} - {e}")
                continue
        
        # キャッシュディレクトリの内容を確認
        logger.info("キャッシュディレクトリの内容を確認中...")
        cache_path = Path(test_cache_dir)
        
        if cache_path.exists():
            # 最新のセッションディレクトリを取得
            session_dirs = [d for d in cache_path.iterdir() if d.is_dir()]
            if session_dirs:
                latest_session = max(session_dirs, key=lambda x: x.stat().st_mtime)
                logger.info(f"最新のセッション: {latest_session}")
                
                # セッション内のファイルを確認
                list_file = latest_session / "list.html"
                details_dir = latest_session / "details"
                metadata_file = latest_session / "metadata.json"
                
                if list_file.exists():
                    logger.info(f"一覧ページが保存されています: {list_file}")
                else:
                    logger.warning("一覧ページが保存されていません")
                
                if details_dir.exists():
                    detail_files = list(details_dir.glob("*.html"))
                    logger.info(f"詳細ページが {len(detail_files)} 件保存されています:")
                    for detail_file in detail_files:
                        logger.info(f"  - {detail_file.name}")
                else:
                    logger.warning("詳細ページディレクトリが存在しません")
                
                if metadata_file.exists():
                    logger.info(f"メタデータファイルが保存されています: {metadata_file}")
                else:
                    logger.warning("メタデータファイルが保存されていません")
            else:
                logger.warning("セッションディレクトリが見つかりません")
        else:
            logger.warning("キャッシュディレクトリが存在しません")
        
        logger.info("テストが完了しました")
        
    except Exception as e:
        logger.error(f"テスト中にエラーが発生しました: {e}")
        raise

if __name__ == "__main__":
    test_detail_cache()
