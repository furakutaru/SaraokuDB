#!/usr/bin/env python3
"""
販売者抽出ロジックのテストスクリプト

新しいキャッシュ形式を使用して、販売者抽出ロジックを検証します。
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
import logging

# モジュールのパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.improved_scraper import ImprovedRakutenScraper

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('seller_extraction_test.log')
    ]
)
logger = logging.getLogger(__name__)

def test_seller_extraction():
    """新しいキャッシュ形式を使用して販売者抽出をテスト"""
    # スクレイパーを初期化（新しいキャッシュディレクトリを指定）
    scraper = ImprovedRakutenScraper(
        cache_dir="cache_new",  # 変換したキャッシュディレクトリ
        test_mode=True  # テストモードで実行
    )
    
    # 馬の一覧を取得
    logger.info("馬の一覧を取得中...")
    horses = scraper.scrape_horse_list()
    
    if not horses:
        logger.error("馬の一覧を取得できませんでした")
        return False
    
    logger.info(f"{len(horses)}頭の馬を取得しました")
    
    # テスト結果を保存するリスト
    results = []
    
    # 各馬の詳細を処理
    for horse in horses[:5]:  # 最初の5頭のみテスト
        try:
            logger.info(f"\n馬名: {horse.get('name', '不明')}")
            
            # 詳細ページを取得
            detail_url = horse.get('url', '')
            if not detail_url:
                logger.warning("詳細ページのURLがありません")
                continue
                
            # 詳細ページを取得（キャッシュから）
            response = scraper._make_request(detail_url, use_cache_on_error=True)
            if not response or not hasattr(response, 'text'):
                logger.warning("詳細ページの取得に失敗しました")
                continue
            
            # 販売者情報を抽出
            seller = scraper._extract_seller(page_text=response.text)
            
            # 結果を記録
            result = {
                'name': horse.get('name', '不明'),
                'seller': seller,
                'url': detail_url,
                'success': bool(seller)
            }
            results.append(result)
            
            logger.info(f"抽出した販売者: {seller}")
            
        except Exception as e:
            logger.error(f"処理中にエラーが発生しました: {e}", exc_info=True)
    
    # 結果を表示
    success_count = sum(1 for r in results if r['success'])
    total = len(results)
    
    print("\n===== テスト結果 =====")
    print(f"テスト件数: {total}件")
    print(f"成功: {success_count}件")
    print(f"失敗: {total - success_count}件")
    
    # 失敗したケースを表示
    if success_count < total:
        print("\n===== 失敗したケース =====")
        for r in results:
            if not r['success']:
                print(f"馬名: {r['name']}")
                print(f"URL: {r['url']}")
                print()
    
    return success_count == total

def main():
    """メイン関数"""
    # テストを実行
    success = test_seller_extraction()
    
    if success:
        print("\n✅ テストが正常に完了しました")
        return 0
    else:
        print("\n❌ テスト中にエラーが発生しました")
        return 1

if __name__ == "__main__":
    sys.exit(main())