#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HorseInfoExtractor クラスのテスト
"""

import sys
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
        # テスト用の詳細ページHTML（実際の詳細ページ形式）
        detail_html = """
        <div class="horse-detail">
            <div class="auctionTableCard__name">
                <span class="value">テスト馬</span>
            </div>
            <div class="horseInfo__data">
                テスト馬 Test Horse　　セ3　　栗毛　　2022年2月22日生（3歳）
            </div>
            <div class="pedigree">
                父：テスト父馬　母：テスト母馬　母の父：テスト母父馬
            </div>
        </div>
        """
        
        # BeautifulSoupでパースしてから情報を抽出
        soup = BeautifulSoup(detail_html, 'html.parser')
        horse_element = soup.select_one('.horse-detail')
        result, _ = self.extractor.extract(horse_element)
        
        # 結果を検証
        self.assertIsNotNone(result)
        self.assertEqual(result.get('name'), 'テスト馬')
        self.assertEqual(result.get('sex'), 'セ')
        self.assertEqual(result.get('age'), 3)
    
    def test_extract_from_detail_page_with_english_name(self):
        """英語名を含む詳細ページから情報を抽出するテスト"""
        # テスト用の詳細ページHTML（英語名を含む）
        detail_html = """
        <div class="horse-detail">
            <div class="auctionTableCard__name">
                <span class="value">グランダイト</span>
            </div>
            <div class="horseInfo__data">
                グランダイト (USA)　　牡4　　鹿毛　　2021年3月15日生（4歳）
            </div>
            <div class="pedigree">
                父：テスト父馬　母：テスト母馬　母の父：テスト母父馬
            </div>
        </div>
        """
        
        # BeautifulSoupでパースしてから情報を抽出
        soup = BeautifulSoup(detail_html, 'html.parser')
        horse_element = soup.select_one('.horse-detail')
        result, _ = self.extractor.extract(horse_element)
        
        # 結果を検証
        self.assertIsNotNone(result)
        self.assertEqual(result.get('name'), 'グランダイト')
        self.assertEqual(result.get('sex'), '牡')  # テストデータに合わせて'牡'を期待
        self.assertEqual(result.get('age'), 4)
    
    def test_extract_pedigree_from_detail_page(self):
        """詳細ページから血統情報を正しく抽出できるかテスト"""
        # テスト用の詳細ページHTML（血統情報を含む）
        detail_html = """
        <div class="horse-detail">
            <h1>テスト馬 Test Horse</h1>
            <div class="horse-info">
                <b>テスト馬 Test Horse　　セン　　栗毛　　2022年2月22日生　3歳</b>
                <div class="pedigree">
                    父：テスト父馬　母：テスト母馬　母の父：テスト母父馬
                </div>
                <div class="record">
                    通算成績：4戦0勝［0-0-0-4］　　　　最終出走馬体重：496kg
                </div>
            </div>
        </div>
        """
        
        # BeautifulSoupでパースしてから情報を抽出
        soup = BeautifulSoup(detail_html, 'html.parser')
        horse_element = soup.select_one('.horse-detail')
        result, _ = self.extractor.extract(horse_element)
        
        # 結果を検証
        self.assertIsNotNone(result)
        self.assertEqual(result.get('sire'), 'テスト父馬')
        self.assertEqual(result.get('dam'), 'テスト母馬')
        self.assertEqual(result.get('damsire'), 'テスト母父馬')

if __name__ == '__main__':
    unittest.main()
