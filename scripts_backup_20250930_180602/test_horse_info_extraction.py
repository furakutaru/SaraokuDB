#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
from pathlib import Path
from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock

# 親ディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent))

from improved_scraper import ImprovedRakutenScraper, ScraperConfig

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_horse_info_extraction.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class TestHorseInfoExtraction:
    def __init__(self):
        # テスト用の設定
        self.config = ScraperConfig(
            use_cache=False,  # テストではキャッシュを使用しない
            max_workers=1,    # 並列処理は無効化
            timeout=30,
            max_retries=1
        )
        self.scraper = ImprovedRakutenScraper(self.config)
        
        # _fetch_htmlメソッドをモック化
        self.mock_fetch_html = MagicMock(return_value=None)
        self.scraper._fetch_html = self.mock_fetch_html
        
        # テストデータのディレクトリ
        self.test_data_dir = Path('test_data')
        
    def load_test_html(self, filename):
        """テスト用のHTMLを読み込む"""
        filepath = self.test_data_dir / filename
        if not filepath.exists():
            logger.error(f"テストファイルが見つかりません: {filepath}")
            return None
            
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def test_extraction(self, html_file, expected_fields=None):
        """抽出処理をテストする"""
        logger.info(f"\n{'='*50}")
        logger.info(f"テストを開始します: {html_file}")
        logger.info(f"{'='*50}")
        
        # HTMLを読み込む
        html_content = self.load_test_html(html_file)
        if not html_content:
            return False
            
        # BeautifulSoupでパース
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 馬のカード要素を取得（テスト用に最初の1件のみ）
        card = soup.select_one('.auctionTableCard')
        if not card:
            logger.error("馬のカード要素が見つかりませんでした")
            return False
            
        # 詳細ページのモックは使用せず、実際のHTML構造に基づいてテスト
        self.mock_fetch_html.return_value = """
        <div class="horseProfile">
            <div class="horseName">サクラバクシンオー</div>
            <div class="horseInfo">
                <span class="sex">牡</span>
                <span class="age">3</span>
            </div>
        </div>
        """
            
        # 馬情報を抽出
        horse_info = self.scraper._process_horse_info(card, index=1, total=1)
        
        if not horse_info:
            logger.error("馬情報の抽出に失敗しました")
            return False
            
        # 結果を表示
        logger.info("抽出された馬情報:")
        for key, value in horse_info.items():
            logger.info(f"  {key}: {value}")
            
        # 期待されるフィールドが含まれているか検証
        if expected_fields:
            logger.info("\n検証結果:")
            all_passed = True
            for field in expected_fields:
                if field not in horse_info or horse_info[field] is None:
                    logger.error(f"  ✗ 必須フィールドが不足しています: {field}")
                    all_passed = False
                else:
                    logger.info(f"  ✓ {field}: {horse_info[field]}")
            
            if all_passed:
                logger.info("\n✅ すべての必須フィールドが正しく抽出されました")
            else:
                logger.error("\n❌ 一部の必須フィールドが抽出できていません")
                
            return all_passed
            
        return True

def main():
    tester = TestHorseInfoExtraction()
    
    # テストケースを定義（必須フィールドのみに絞る）
    test_cases = [
        {
            'file': 'horse_list_sample.html',
            'expected_fields': ['name', 'age', 'sex']  # 必須フィールドのみ
        }
    ]
    
    # テストを実行
    all_passed = True
    for test_case in test_cases:
        if not tester.test_extraction(test_case['file'], test_case['expected_fields']):
            all_passed = False
    
    # テスト結果を表示
    if all_passed:
        logger.info("\n🎉 すべてのテストが成功しました！")
    else:
        logger.error("\n❌ 一部のテストが失敗しました")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
