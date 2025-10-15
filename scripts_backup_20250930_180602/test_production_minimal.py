#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本番環境でのミニマムテストスクリプト
"""
import sys
import logging
from pathlib import Path
from bs4 import BeautifulSoup

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_production.log')
    ]
)
logger = logging.getLogger(__name__)

# プロジェクトのルートパスを追加
sys.path.insert(0, str(Path(__file__).parent))

from improved_scraper import ImprovedRakutenScraper

def run_minimal_test():
    """本番環境でのミニマムテストを実行"""
    try:
        logger.info("=== 本番環境ミニマムテストを開始します ===")
        
        # スクレイパーの初期化（本番モード）
        scraper = ImprovedRakutenScraper(
            use_cache=False,  # キャッシュは無効
            max_workers=3,    # 並列処理のワーカー数を制限
            timeout=30,       # タイムアウトを30秒に設定
            retries=2         # リトライ回数を2回に設定
        )
        
        # テスト対象の馬のID（実際のオークション詳細ページのID）
        test_horse_ids = ["14851", "14852", "14853"]  # 実際のオークションIDに変更してください
        
        # テスト実行
        results = []
        for horse_id in test_horse_ids:
            try:
                logger.info(f"馬ID {horse_id} の情報を取得中...")
                
                # 馬の詳細ページのURLを構築
                detail_url = f"https://auction.keiba.rakuten.co.jp/item/{horse_id}"
                
                # 詳細ページからHTMLを取得
                html_content = scraper._fetch_html(detail_url, use_cache=False)
                
                # デバッグ用にHTMLを保存
                debug_file = f"debug_horse_{horse_id}.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.info(f"デバッグ用HTMLを保存しました: {debug_file}")
                
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # デバッグ用に主要な要素を確認
                debug_elements = {
                    'title': soup.title,
                    'horse_name': soup.select_one('.horseName'),
                    'horse_info': soup.select_one('.horseInfo')
                }
                logger.debug(f"デバッグ要素: {debug_elements}")
                
                # 馬情報を抽出
                horse_info = scraper._extract_horse_info(soup)
                
                if horse_info:
                    logger.info(f"取得成功: {horse_info.get('name')} (ID: {horse_id})")
                    logger.info(f"性別: {horse_info.get('sex')}, 年齢: {horse_info.get('age')}")
                    logger.info(f"血統: 父 {horse_info.get('sire', 'N/A')}, 母 {horse_info.get('dam', 'N/A')}")
                    results.append(True)
                else:
                    logger.error(f"馬ID {horse_id} の情報を抽出できませんでした")
                    results.append(False)
                    
            except Exception as e:
                logger.error(f"馬ID {horse_id} の処理中にエラーが発生しました: {str(e)}", exc_info=True)
                results.append(False)
        
        # テスト結果のサマリー
        success_count = sum(1 for r in results if r)
        logger.info(f"\n=== テスト結果 ===")
        logger.info(f"総テスト数: {len(test_horse_ids)}")
        logger.info(f"成功: {success_count}")
        logger.info(f"失敗: {len(test_horse_ids) - success_count}")
        
        return all(results)
        
    except Exception as e:
        logger.error(f"テストの実行中にエラーが発生しました: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = run_minimal_test()
    sys.exit(0 if success else 1)
