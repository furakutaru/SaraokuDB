#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ImprovedRakutenScraper の統合テスト
"""

import unittest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

# テスト用のモックを設定
import sys
sys.modules['core'] = MagicMock()
sys.modules['core.utils'] = MagicMock()
sys.modules['core.utils.html_saver'] = MagicMock()
sys.modules['core.cache'] = MagicMock()
sys.modules['core.cache.cache_manager'] = MagicMock()

# テスト対象のモジュールをインポート
from improved_scraper import ImprovedRakutenScraper, ScraperConfig
from components.horse_info_extractor import HorseInfoExtractor

class TestImprovedRakutenScraperIntegration(unittest.TestCase):
    """ImprovedRakutenScraper の統合テスト"""
    
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
        
        # テスト用のHTML
        self.list_html = """
        <div class="auctionTableCard">
            <a href="/auction/12345" class="auctionTableCard__name">テスト馬</a>
            <!-- 性別と年齢が欠けている -->
        </div>
        """
        
        self.detail_html = """
        <html>
        <head>
            <title>テスト馬 - 楽天競馬オークション</title>
        </head>
        <body>
            <div id="itemTitle">
                <span itemprop="name">テスト馬（牝4歳）</span>
            </div>
        </body>
        </html>
        """
    
    @patch('improved_scraper.ImprovedRakutenScraper._fetch_html')
    def test_process_horse_info_with_fallback(self, mock_fetch_html):
        """リストページで不足している情報を詳細ページから取得できるかテスト"""
        # モックの設定
        mock_fetch_html.return_value = self.detail_html
        
        # HTMLをパース
        soup = BeautifulSoup(self.list_html, 'html.parser')
        card = soup.find('div', class_='auctionTableCard')
        
        # 馬情報を処理
        result = self.scraper._process_horse_info(card, index=1, total=1)
        
        # 結果を検証
        self.assertIsNotNone(result)
        self.assertEqual(result.get('name'), 'テスト馬')
        self.assertEqual(result.get('sex'), '牝')
        self.assertEqual(result.get('age'), 4)
        
        # 詳細ページが呼び出されたことを確認
        mock_fetch_html.assert_called_once_with(
            'https://auction.keiba.rakuten.co.jp/auction/12345',
            use_cache=True
        )
    
    @patch('improved_scraper.ImprovedRakutenScraper._fetch_html')
    def test_process_horse_info_no_fallback_needed(self, mock_fetch_html):
        """リストページにすべての情報がある場合は詳細ページを呼び出さないテスト"""
        # リストページに性別と年齢が含まれているHTML
        complete_list_html = """
        <div class="auctionTableCard">
            <a href="/auction/12345" class="auctionTableCard__name">テスト馬</a>
            <div class="auctionTableCard__sex">牡</div>
            <div class="auctionTableCard__age">3歳</div>
        </div>
        """
        
        # HTMLをパース
        soup = BeautifulSoup(complete_list_html, 'html.parser')
        card = soup.find('div', class_='auctionTableCard')
        
        # 馬情報を処理
        result = self.scraper._process_horse_info(card, index=1, total=1)
        
        # 結果を検証
        self.assertIsNotNone(result)
        self.assertEqual(result.get('name'), 'テスト馬')
        self.assertEqual(result.get('sex'), '牡')
        self.assertEqual(result.get('age'), 3)
        
        # 詳細ページは呼び出されていないことを確認
        mock_fetch_html.assert_not_called()

if __name__ == '__main__':
    unittest.main()
