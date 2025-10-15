"""
SexExtractor のテストモジュール
"""

import unittest
from unittest.mock import MagicMock
from bs4 import BeautifulSoup
from components.extractors.sex_extractor import SexExtractor

class TestSexExtractor(unittest.TestCase):
    """SexExtractor のテストクラス"""
    
    def setUp(self):
        """テストの前処理"""
        self.logger = MagicMock()
        self.extractor = SexExtractor(logger=self.logger)
    
    def test_from_text(self):
        """テキストからの性別抽出テスト"""
        test_cases = [
            ('牡', '牡'),
            ('牝', '牝'),
            ('セ', 'セ'),
            ('セン', 'セ'),
            ('牡3歳', '牡'),
            ('牝2歳', '牝'),
            ('セ4歳', 'セ'),
            ('セン4歳', 'セ'),
            ('牡馬', '牡'),
            ('牝馬', '牝'),
            ('せん馬', 'セ'),
            ('セン馬', 'セ'),
            ('牡3歳 鹿毛', '牡'),
            ('性別不明', None),
            ('', None),
            (None, None)
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.extractor.from_text(input_text)
                self.assertEqual(result, expected)
    
    def test_from_element(self):
        """HTML要素からの性別抽出テスト"""
        # テスト用のHTMLを作成
        html_templates = [
            '<div class="horse-info">牡3歳</div>',
            '<span class="sex">牝</span>',
            '<div class="info">セ4歳 鹿毛</div>',
            '<div class="horse-data">牡馬</div>',
            '<div class="horse-detail">性別: 牝</div>'
        ]
        
        expected_results = ['牡', '牝', 'セ', '牡', '牝']
        
        for html, expected in zip(html_templates, expected_results):
            with self.subTest(html=html):
                soup = BeautifulSoup(html, 'html.parser')
                result = self.extractor.from_element(soup)
                self.assertEqual(result, expected)
    
    def test_extract_auto_detection(self):
        """自動検出機能のテスト"""
        # テストケース: テキスト
        self.assertEqual(self.extractor.extract('牡3歳'), '牡')
        self.assertEqual(self.extractor.extract('牝2歳'), '牝')
        self.assertEqual(self.extractor.extract('セ4歳'), 'セ')
        
        # テストケース: BeautifulSoup要素
        html = '<div class="horse-info">牡3歳</div>'
        soup = BeautifulSoup(html, 'html.parser')
        self.assertEqual(self.extractor.extract(soup), '牡')
        
        # テストケース: 辞書（文字列に変換）
        class TestObj:
            def __str__(self):
                return '牝2歳'
                
        self.assertEqual(self.extractor.extract(TestObj()), '牝')
    
    def test_extract_with_source_type(self):
        """ソースタイプ指定での抽出テスト"""
        # テキストソース
        self.assertEqual(self.extractor.extract('牡3歳', 'text'), '牡')
        
        # HTML要素ソース
        html = '<div class="horse-info">牝2歳</div>'
        soup = BeautifulSoup(html, 'html.parser')
        self.assertEqual(self.extractor.extract(soup, 'element'), '牝')
        
        # 無効なソースタイプ
        self.assertIsNone(self.extractor.extract('牡3歳', 'invalid_type'))
    
    def test_edge_cases(self):
        """境界値・エッジケースのテスト"""
        # 空の入力
        self.assertIsNone(self.extractor.extract(''))
        self.assertIsNone(self.extractor.extract(None))
        
        # 性別が含まれていないテキスト
        self.assertIsNone(self.extractor.extract('鹿毛 3歳'))
        
        # 複数の性別が含まれる場合（最初に見つかったものを返す）
        self.assertEqual(self.extractor.extract('牡 牝 セ'), '牡')
        
        # 部分一致（「牡」が「特」に含まれるケース）
        self.assertEqual(self.extractor.extract('特別'), None)  # 「特」だけでは抽出しない
        self.assertEqual(self.extractor.extract('特牡'), '牡')  # 正しく抽出

if __name__ == '__main__':
    unittest.main()
