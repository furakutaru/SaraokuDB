#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
馬の年齢抽出テスト（horseLabelWrapper__horseAge セレクタ用）
"""

import unittest
from bs4 import BeautifulSoup
import sys
from pathlib import Path

# テスト対象のモジュールをインポート
sys.path.insert(0, str(Path(__file__).parent))
from components.horse_info_extractor import HorseInfoExtractor

class TestHorseLabelWrapper(unittest.TestCase):
    """horseLabelWrapper__horseAge セレクタを使用した年齢抽出のテスト"""
    
    def setUp(self):
        """テストの前処理"""
        self.extractor = HorseInfoExtractor()
    
    def test_extract_from_horse_label_wrapper(self):
        """horseLabelWrapper から年齢と性別を正しく抽出できるかテスト"""
        # テスト用のHTML
        test_html = """
        <div class="horseLabelWrapper">
            <div class="horseLabelWrapper__horseName">テスト馬</div>
            <div class="horseLabelWrapper__horseAge">3</div>
            <div class="horseLabelWrapper__horseSex">牡</div>
        </div>
        """
        
        # HTMLをパース
        soup = BeautifulSoup(test_html, 'html.parser')
        horse_element = soup.select_one('.horseLabelWrapper')
        
        # 年齢と性別を抽出
        result = self.extractor._extract_sex_and_age(horse_element)
        
        # 結果を検証
        self.assertEqual(result.get('age'), '3歳', '年齢が正しく抽出できていません')
        self.assertEqual(result.get('sex'), '牡', '性別が正しく抽出できていません')
    
    def test_extract_with_only_required_selectors(self):
        """必要なセレクタのみが存在する場合のテスト"""
        # テスト用のHTML（必要なセレクタのみ）
        test_html = """
        <div class="horseLabelWrapper">
            <div class="horseLabelWrapper__horseAge">4</div>
            <div class="horseLabelWrapper__horseSex">牝</div>
        </div>
        """
        
        # HTMLをパース
        soup = BeautifulSoup(test_html, 'html.parser')
        horse_element = soup.select_one('.horseLabelWrapper')
        
        # 年齢と性別を抽出
        result = self.extractor._extract_sex_and_age(horse_element)
        
        # 結果を検証
        self.assertEqual(result.get('age'), '4歳', '年齢が正しく抽出できていません')
        self.assertEqual(result.get('sex'), '牝', '性別が正しく抽出できていません')

if __name__ == '__main__':
    unittest.main()
