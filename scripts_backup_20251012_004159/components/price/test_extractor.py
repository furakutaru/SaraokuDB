"""
PriceExtractorのテスト
"""
import unittest
from bs4 import BeautifulSoup
from ..price.extractor import PriceExtractor

class TestPriceExtractor(unittest.TestCase):
    """PriceExtractorのテストケース"""
    
    def setUp(self):
        self.extractor = PriceExtractor()

    def test_extract_price_normal(self):
        """通常の価格抽出テスト"""
        html = '''
        <div class="price">1,234万円</div>
        '''
        expected = {
            'sold_price': 1234.0,
            'is_unsold': False
        }
        result = self.extractor.extract(html)
        self.assertEqual(result, expected)

    def test_extract_price_with_comma(self):
        """カンマを含む価格の抽出テスト"""
        html = '''
        <div class="price">10,500万円</div>
        '''
        expected = {
            'sold_price': 10500.0,
            'is_unsold': False
        }
        result = self.extractor.extract(html)
        self.assertEqual(result, expected)

    def test_extract_unsold(self):
        """主取りの場合のテスト"""
        html = '''
        <div class="unsold">主取り</div>
        '''
        expected = {
            'sold_price': None,
            'is_unsold': True
        }
        result = self.extractor.extract(html)
        self.assertEqual(result, expected)

    def test_extract_no_price(self):
        """価格要素がない場合のテスト"""
        html = '''
        <div>価格情報なし</div>
        '''
        expected = {
            'sold_price': None,
            'is_unsold': False
        }
        result = self.extractor.extract(html)
        self.assertEqual(result, expected)

    def test_extract_invalid_price(self):
        """無効な価格形式のテスト"""
        html = '''
        <div class="price">価格未定</div>
        '''
        expected = {
            'sold_price': None,
            'is_unsold': False
        }
        result = self.extractor.extract(html)
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
