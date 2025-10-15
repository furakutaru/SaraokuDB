"""
AgeExtractor のテストモジュール
"""

import unittest
from unittest.mock import MagicMock
from bs4 import BeautifulSoup
from components.extractors.age_extractor import AgeExtractor

class TestAgeExtractor(unittest.TestCase):
    """AgeExtractor のテストクラス"""
    
    def setUp(self):
        """テストの前処理"""
        self.logger = MagicMock()
        self.extractor = AgeExtractor(logger=self.logger)
    
    def test_from_text(self):
        """テキストからの年齢抽出テスト"""
        test_cases = [
            ('3歳', 3),
            ('2才', 2),
            ('1歳 牡', 1),
            ('4才 鹿毛', 4),
            ('年齢不明', None),
            ('', None),
            (None, None)
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.extractor.from_text(input_text)
                self.assertEqual(result, expected)
    
    def test_from_element(self):
        """HTML要素からの年齢抽出テスト"""
        # テスト用のHTMLを作成
        html_templates = [
            '<div class="horseLabelWrapper"><div class="horseLabelWrapper__horseAge">3歳</div></div>',
            '<div class="age">2才</div>',
            '<span class="horse-age">1歳</span>',
            '<div class="horseInfo"><span>4才</span></div>',
            '<div class="no-age">年齢不明</div>'
        ]
        
        expected_results = [3, 2, 1, 4, None]
        
        for html, expected in zip(html_templates, expected_results):
            with self.subTest(html=html):
                soup = BeautifulSoup(html, 'html.parser')
                result = self.extractor.from_element(soup)
                self.assertEqual(result, expected)
    
    def test_from_horse_label_wrapper(self):
        """実際のHTML構造に基づくテスト"""
        html = '''
        <div data-v-4bfd299b="" data-v-a815ad89="" class="horseLabelWrapper" style="margin-right: 24px;">
            <div data-v-4bfd299b="" class="horseLabelWrapper__horseAge">3歳</div>
            <div data-v-4bfd299b="" style="background-color: rgb(123, 211, 255);" class="horseLabelWrapper__horseSex">牡</div>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        result = self.extractor.from_element(soup)
        self.assertEqual(result, 3)
    
    def test_extract_auto_detection(self):
        """自動検出機能のテスト"""
        # テストケース: テキスト
        self.assertEqual(self.extractor.extract('3歳'), 3)
        self.assertEqual(self.extractor.extract('2才'), 2)
        
        # テストケース: BeautifulSoup要素
        html = '<div class="horseLabelWrapper"><div class="horseLabelWrapper__horseAge">4歳</div></div>'
        soup = BeautifulSoup(html, 'html.parser')
        self.assertEqual(self.extractor.extract(soup), 4)
        
        # テストケース: 辞書（文字列に変換）
        class TestObj:
            def __str__(self):
                return '1才'
                
        self.assertEqual(self.extractor.extract(TestObj()), 1)
    
    def test_extract_with_source_type(self):
        """ソースタイプ指定での抽出テスト"""
        # テキストソース
        self.assertEqual(self.extractor.extract('3歳', 'text'), 3)
        
        # HTML要素ソース
        html = '<div class="horseLabelWrapper"><div class="horseLabelWrapper__horseAge">2才</div></div>'
        soup = BeautifulSoup(html, 'html.parser')
        self.assertEqual(self.extractor.extract(soup, 'element'), 2)
        
        # 無効なソースタイプ
        self.assertIsNone(self.extractor.extract('3歳', 'invalid_type'))
    
    def test_edge_cases(self):
        """境界値・エッジケースのテスト"""
        # 空の入力
        self.assertIsNone(self.extractor.extract(''))
        self.assertIsNone(self.extractor.extract(None))
        
        # 年齢が含まれていないテキスト
        self.assertIsNone(self.extractor.extract('鹿毛 牡'))
        
        # 不正な年齢
        self.assertIsNone(self.extractor.extract('歳'))
        self.assertIsNone(self.extractor.extract('才'))
        self.assertIsNone(self.extractor.extract('abc歳'))

if __name__ == '__main__':
    unittest.main()
