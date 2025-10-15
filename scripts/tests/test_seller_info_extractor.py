"""販売者情報抽出のテスト"""
import unittest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
from components.seller_info_extractor import SellerInfoExtractor

class TestSellerInfoExtractor(unittest.TestCase):
    """SellerInfoExtractorのテストクラス"""
    
    def setUp(self):
        """テストの前処理"""
        self.logger = MagicMock()
        self.extractor = SellerInfoExtractor(logger=self.logger)
    
    def test_extract_success(self):
        """販売者情報の抽出テスト（成功ケース）"""
        test_cases = [
            {
                'name': '標準的なケース',
                'html': '<div class="seller">出品者：テスト牧場</div>',
                'expected': 'テスト牧場'
            },
            {
                'name': 'クラス名に複数値があるケース',
                'html': '<div class="seller info">テスト牧場</div>',
                'expected': 'テスト牧場'
            },
            {
                'name': '余分な空白があるケース',
                'html': '<div class="seller">  テスト牧場  </div>',
                'expected': 'テスト牧場'
            },
            {
                'name': '改行を含むケース',
                'html': '''<div class="seller">
                    テスト牧場
                </div>''',
                'expected': 'テスト牧場'
            },
            {
                'name': '出品者表記のバリエーション1',
                'html': '<div class="seller">出品者: テスト牧場</div>',
                'expected': 'テスト牧場'
            },
            {
                'name': '出品者表記のバリエーション2',
                'html': '<div class="seller">販売者：テスト牧場</div>',
                'expected': 'テスト牧場'
            },
            {
                'name': 'URLを含むケース',
                'html': '<div class="seller"><a href="http://example.com">テスト牧場</a></div>',
                'expected': 'テスト牧場'
            },
            {
                'name': 'コメントを含むケース',
                'html': '<div class="seller">テスト牧場<!-- コメント --></div>',
                'expected': 'テスト牧場'
            },
            {
                'name': '特殊文字を含むケース',
                'html': '<div class="seller">テスト牧場（有）</div>',
                'expected': 'テスト牧場（有）'
            }
        ]
        
        for case in test_cases:
            with self.subTest(case['name']):
                soup = BeautifulSoup(case['html'], 'html.parser')
                result, success = self.extractor.extract(soup)
                self.assertTrue(success, f"Failed case: {case['name']}")
                self.assertEqual(result['seller'], case['expected'])
    
    def test_extract_missing_seller(self):
        """販売者情報が存在しない場合のテスト"""
        test_cases = [
            {
                'name': 'クラス名が異なる',
                'html': '<div class="other">テスト牧場</div>'
            },
            {
                'name': '空のHTML',
                'html': ''
            },
            {
                'name': 'Noneを渡した場合',
                'html': None
            }
        ]
        
        for case in test_cases:
            with self.subTest(case['name']):
                soup = BeautifulSoup(case['html'], 'html.parser') if case['html'] is not None else None
                result, success = self.extractor.extract(soup)
                self.assertFalse(success)
                self.assertIsNone(result)
    
    def test_clean_seller_name(self):
        """販売者名のクリーンアップテスト"""
        test_cases = [
            # 前後の空白・改行
            ('  テスト牧場  ', 'テスト牧場'),
            ('テスト牧場\n', 'テスト牧場'),
            ('テスト牧場\t', 'テスト牧場'),
            ('\nテスト牧場\n', 'テスト牧場'),
            
            # 接頭辞・接尾辞の除去
            ('出品者：テスト牧場', 'テスト牧場'),
            ('出品者:テスト牧場', 'テスト牧場'),
            ('販売者：テスト牧場', 'テスト牧場'),
            ('販売者:テスト牧場', 'テスト牧場'),
            ('テスト牧場（有）', 'テスト牧場（有）'),
            
            # 特殊な文字
            ('テスト牧場　', 'テスト牧場'),  # 全角スペース
            ('　テスト牧場　', 'テスト牧場'),
            ('テスト牧場　　', 'テスト牧場'),
            
            # 空文字・None
            ('', ''),
            (None, ''),
            
            # 複合パターン
            ('  出品者：テスト牧場  \n', 'テスト牧場'),
            ('  販売者：テスト牧場（有）  ', 'テスト牧場（有）')
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.extractor._clean_seller_name(input_text)
                self.assertEqual(result, expected, f"Input: '{input_text}'")
    
    def test_extract_exception_handling(self):
        """例外発生時のテスト"""
        # 例外を発生させるためのモック
        with patch.object(BeautifulSoup, 'find', side_effect=Exception('Test error')):
            result, success = self.extractor.extract(BeautifulSoup('', 'html.parser'))
            
            # 検証
            self.assertFalse(success)
            self.assertIsNone(result)
            self.logger.error.assert_called()
    
    def test_extract_with_various_html_structures(self):
        """様々なHTML構造でのテスト"""
        test_cases = [
            {
                'name': 'ネストされた要素',
                'html': '''
                <div class="seller">
                    <div class="seller-name">テスト牧場</div>
                    <div class="seller-contact">連絡先</div>
                </div>
                ''',
                'expected': 'テスト牧場 連絡先'
            },
            {
                'name': '複数の要素',
                'html': '''
                <div class="seller">
                    <span>テスト牧場</span>
                    <span>代表: 山田太郎</span>
                </div>
                ''',
                'expected': 'テスト牧場 代表: 山田太郎'
            },
            {
                'name': 'スクリプトタグを含む',
                'html': '''
                <div class="seller">
                    テスト牧場
                    <script>console.log('test');</script>
                </div>
                ''',
                'expected': 'テスト牧場'
            },
            {
                'name': 'コメントを含む',
                'html': '''
                <div class="seller">
                    テスト牧場<!-- これはコメントです -->
                </div>
                ''',
                'expected': 'テスト牧場'
            }
        ]
        
        for case in test_cases:
            with self.subTest(case['name']):
                soup = BeautifulSoup(case['html'], 'html.parser')
                result, success = self.extractor.extract(soup)
                self.assertTrue(success, f"Failed case: {case['name']}")
                self.assertEqual(result['seller'], case['expected'])

if __name__ == '__main__':
    unittest.main()
