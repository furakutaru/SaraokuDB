#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HorseInfoExtractor クラスのテスト
"""

import sys
import unittest
from pathlib import Path
from bs4 import BeautifulSoup

# プロジェクトのルートディレクトリをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# テスト対象のモジュールをインポート
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
            <div id="itemTitle">
                <span itemprop="name">テスト馬（牝4歳）</span>
            </div>
        </body>
        </html>
        """
        
        # 詳細ページから情報を抽出
        result = self.extractor.extract_from_detail_page(detail_html)
        
        # 結果を検証
        self.assertIsNotNone(result)
        self.assertEqual(result.get('sex'), '牝')
        self.assertEqual(result.get('age'), 4)
    
    def test_extract_from_title_with_sex_and_age(self):
        """タイトルから性別と年齢を抽出するテスト"""
        # テスト用の詳細ページHTML（タイトルから情報を抽出）
        detail_html = """
        <html>
        <head>
            <title>テスト馬 - 楽天競馬オークション</title>
        </head>
        <body>
            <div id="itemTitle">
                <span itemprop="name">テスト馬（牡5歳）</span>
            </div>
        </body>
        </html>
        """
        
        # 詳細ページから情報を抽出
        result = self.extractor.extract_from_detail_page(detail_html)
        
        # 結果を検証
        self.assertIsNotNone(result)
        self.assertEqual(result.get('sex'), '牡')
        self.assertEqual(result.get('age'), 5)

if __name__ == '__main__':
    unittest.main()
