#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HorseInfoExtractor クラスの血統情報抽出機能のテスト
"""

import unittest
from bs4 import BeautifulSoup
from components.horse_info_extractor import HorseInfoExtractor

class TestPedigreeExtraction(unittest.TestCase):
    """HorseInfoExtractor クラスの血統情報抽出機能のテスト"""
    
    def setUp(self):
        """テストの前処理"""
        self.extractor = HorseInfoExtractor()
    
    def test_extract_pedigree(self):
        """血統情報の抽出テスト"""
        # テスト用のHTML
        html = """
        <html>
        <body>
            <pre>父：テスト父馬　母：テスト母馬　母の父：テスト母父馬</pre>
        </body>
        </html>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        pre_elem = soup.find('pre')
        
        # 血統情報を抽出
        result = self.extractor._extract_pedigree(pre_elem)
        
        # 結果を検証
        self.assertEqual(result['sire'], 'テスト父馬')
        self.assertEqual(result['dam'], 'テスト母馬')
        self.assertEqual(result['damsire'], 'テスト母父馬')

if __name__ == '__main__':
    unittest.main()
