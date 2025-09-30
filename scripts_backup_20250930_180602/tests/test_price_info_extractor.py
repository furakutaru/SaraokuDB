"""価格情報抽出のテスト"""
import unittest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
from components.price_info_extractor import PriceInfoExtractor

class TestPriceInfoExtractor(unittest.TestCase):
    """PriceInfoExtractorのテストクラス"""
    
    def setUp(self):
        """テストの前処理"""
        self.logger = MagicMock()
        self.extractor = PriceInfoExtractor(logger=self.logger)
    
    def test_extract_sold_price(self):
        """落札価格の抽出テスト"""
        # テスト用のHTMLを作成
        html = '''
        <div class="price">
            落札価格: 12,345,678円
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result, success = self.extractor.extract(soup)
        
        # 検証
        self.assertTrue(success)
        self.assertEqual(result['sold_price'], 12345678)
        self.assertFalse(result.get('is_unsold', False))
        self.logger.debug.assert_called_with('価格情報を抽出しました: {\'sold_price\': 12345678}')
    
    def test_extract_starting_price(self):
        """開始価格の抽出テスト"""
        # テスト用のHTMLを作成
        html = '''
        <div class="start-price">
            開始価格: 1,000,000円
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result, success = self.extractor.extract(soup)
        
        # 検証
        self.assertTrue(success)
        self.assertEqual(result['starting_price'], 1000000)
        self.logger.debug.assert_called_with('価格情報を抽出しました: {\'starting_price\': 1000000}')
    
    def test_extract_unsold(self):
        """未落札のテスト"""
        # テスト用のHTMLを作成
        html = '''
        <div class="price">
            未落札
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result, success = self.extractor.extract(soup)
        
        # 検証
        self.assertTrue(success)
        self.assertTrue(result['is_unsold'])
    
    def test_extract_no_price(self):
        """価格情報が存在しない場合のテスト"""
        # テスト用のHTML（価格情報なし）
        html = '<div class="other">テスト</div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result, success = self.extractor.extract(soup)
        
        # 検証
        self.assertFalse(success)
        self.assertIsNone(result)
        self.logger.debug.assert_called_with('価格情報が見つかりませんでした')
    
    def test_is_unsold(self):
        """未落札判定のテスト"""
        test_cases = [
            ('未落札', True),
            ('売れ残り', True),
            ('不成立', True),
            ('キャンセル', True),
            ('UNSOLD', True),
            ('Not Sold', True),
            ('Cancelled', True),
            ('No Bid', True),
            ('12,345,678円', False),
            ('', False),
            (None, False)
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.extractor._is_unsold(input_text)
                self.assertEqual(result, expected)
    
    def test_extract_exception_handling(self):
        """例外発生時のテスト"""
        # 例外を発生させるためのモック
        with patch('bs4.BeautifulSoup.select_one', side_effect=Exception('Test error')):
            result, success = self.extractor.extract(BeautifulSoup('', 'html.parser'))
            
            # 検証
            self.assertFalse(success)
            self.assertIsNone(result)
            self.logger.error.assert_called()

if __name__ == '__main__':
    unittest.main()
