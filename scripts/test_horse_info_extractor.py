#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HorseInfoExtractor クラスのテスト
"""

import unittest
from pathlib import Path
from bs4 import BeautifulSoup

# テスト対象のモジュールをインポート
sys.path.insert(0, str(Path(__file__).parent))
from components.horse_info_extractor import HorseInfoExtractor

class TestHorseInfoExtractor(unittest.TestCase):
    """HorseInfoExtractor クラスのテスト"""
    
    def setUp(self):
        """テストの前処理"""
        self.extractor = HorseInfoExtractor()
    
    def test_extract_from_detail_page(self):
        """詳細ページから性別と年齢を正しく抽出できるかテスト"""
        # テスト用の詳細ページHTML
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
        result = self.extractor.extract_from_detail_page(detail_html)
        
        # 結果を検証
        self.assertIsNotNone(result)
        self.assertEqual(result.get('name'), 'テスト馬')
        self.assertEqual(result.get('sex'), '牝')
        self.assertEqual(result.get('age'), '4歳')
    
    def test_extract_from_detail_page_with_title(self):
        """タイトルから性別と年齢を抽出するテスト"""
        # テスト用の詳細ページHTML（クラス名が異なる場合）
        detail_html = """
        <html>
        <head>
            <title>テスト馬（牝4歳） - 楽天競馬オークション</title>
        </head>
        <body>
            <div class="horse-detail">
                <h1 class="horse-name">テスト馬</h1>
                <div class="horse-comment">
                    テスト用のコメントです。
                </div>
            </div>
        </body>
        </html>
        """
        
        # 詳細ページから情報を抽出
        result = self.extractor.extract_from_detail_page(detail_html)
        
        # 結果を検証
        self.assertIsNotNone(result)
        self.assertEqual(result.get('name'), 'テスト馬')
        self.assertEqual(result.get('sex'), '牝')
        self.assertEqual(result.get('age'), '4歳')

if __name__ == '__main__':
    unittest.main()
