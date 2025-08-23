"""
PriceExtractorのテスト
"""
import unittest
from bs4 import BeautifulSoup
from components.price_extractor import PriceExtractor

class TestPriceExtractor(unittest.TestCase):    
    def test_extract_price_normal(self):
        """通常の落札価格を正しく抽出できるかテスト"""
        html = '''
        <div class="sold-price">1,234万円</div>
        '''
        result = PriceExtractor.extract_price(html)
        self.assertEqual(result['sold_price'], 1234.0)
        self.assertFalse(result['is_unsold'])
    
    def test_extract_unsold(self):
        """主取りの場合を正しく判定できるかテスト"""
        html = '''
        <div class="unsold">主取り</div>
        '''
        result = PriceExtractor.extract_price(html)
        self.assertIsNone(result['sold_price'])
        self.assertTrue(result['is_unsold'])
    
    def test_extract_no_price(self):
        """価格要素がない場合のテスト"""
        html = '''
        <div>価格情報なし</div>
        '''
        result = PriceExtractor.extract_price(html)
        self.assertIsNone(result['sold_price'])
        self.assertFalse(result['is_unsold'])

if __name__ == '__main__':
    unittest.main()
