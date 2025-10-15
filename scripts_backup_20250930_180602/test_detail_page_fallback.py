#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
詳細ページからの情報取得フォールバック機能のテスト
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

# テスト対象のモジュールをインポートする前にモックを設定
sys.modules['core'] = Mock()
sys.modules['core.utils'] = Mock()
sys.modules['core.utils.html_saver'] = Mock()
sys.modules['core.cache'] = Mock()
sys.modules['core.cache.cache_manager'] = Mock()

# 相対インポートを使用
from .improved_scraper import ImprovedRakutenScraper, ScraperConfig
from .components.horse_info_extractor import HorseInfoExtractor

class TestDetailPageFallback(unittest.TestCase):
    """詳細ページからの情報取得フォールバック機能のテスト"""
    
    def setUp(self):
        """テストの前処理"""
        # テスト用の設定
        self.config = ScraperConfig(
            use_cache=False,  # テストではキャッシュを使用しない
            max_workers=1,
            timeout=10
        )
        
        # テスト用のスクレイパーインスタンスを作成
        self.scraper = ImprovedRakutenScraper(config=self.config)
        
        # テスト用のHTMLファイルのパス
        self.test_data_dir = Path(__file__).parent / 'test_data'
        self.test_data_dir.mkdir(exist_ok=True)
    
    def test_extract_from_detail_page(self):
        """詳細ページから性別と年齢を正しく抽出できるかテスト"""
        # テスト用の詳細ページHTMLを読み込む
        detail_html = """
        <html>
        <head>
            <title>テスト馬 - 楽天競馬オークション</title>
        </head>
        <body>
            <div class="horse-detail">
                <h1 class="horse-name">テスト馬</h1>
                <div class="horse-info">
                    <span class="horse-sex">牝</span>
                    <span class="horse-age">4歳</span>
                </div>
                <div class="horse-comment">
                    テスト用のコメントです。
                </div>
            </div>
        </body>
        </html>
        """
        
        # 詳細ページから情報を抽出
        extractor = HorseInfoExtractor()
        result = extractor.extract_from_detail_page(detail_html)
        
        # 結果を検証
        self.assertIsNotNone(result)
        self.assertEqual(result.get('name'), 'テスト馬')
        self.assertEqual(result.get('sex'), '牝')
        self.assertEqual(result.get('age'), '4歳')
    
    @patch('scripts.improved_scraper.ImprovedRakutenScraper._fetch_html')
    def test_fallback_to_detail_page(self, mock_fetch_html):
        """リストページで取得できない情報を詳細ページから取得できるかテスト"""
        # テスト用のリストページHTML（性別と年齢が欠けている）
        list_html = """
        <div class="horse-card">
            <a href="/auction/12345" class="horseName">テスト馬</a>
            <div class="horse-info">
                <!-- 性別と年齢が欠けている -->
            </div>
        </div>
        """
        
        # テスト用の詳細ページHTML
        detail_html = """
        <div class="horse-detail">
            <h1 class="horse-name">テスト馬</h1>
            <div class="horse-info">
                <span class="horse-sex">牝</span>
                <span class="horse-age">4歳</span>
            </div>
        </div>
        """
        
        # モックの設定
        mock_fetch_html.return_value = detail_html
        
        # BeautifulSoupでHTMLをパース
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(list_html, 'html.parser')
        card = soup.find('div', class_='horse-card')
        
        # 馬情報を抽出
        result = self.scraper._process_horse_info(card, index=1, total=1)
        
        # 結果を検証
        self.assertIsNotNone(result)
        self.assertEqual(result.get('name'), 'テスト馬')
        self.assertEqual(result.get('sex'), '牝')
        self.assertEqual(result.get('age'), '4歳')
        
        # 詳細ページが呼び出されたことを確認
        mock_fetch_html.assert_called_once_with('https://auction.keiba.rakuten.co.jp/auction/12345', use_cache=True)

if __name__ == '__main__':
    unittest.main()
