"""
PriceExtractorのテスト
"""
import unittest
from bs4 import BeautifulSoup
from components.price_extractor import PriceExtractor

class TestPriceExtractor(unittest.TestCase):
    def test_extract_starting_price(self):
        """開始価格を正しく抽出できるかテスト"""
        html = '''
        <div>開始価格：1,000,000円</div>
        '''
        result = PriceExtractor.extract_price(html)
        self.assertEqual(result['starting_price'], 1000000)
    
    def test_extract_sold_price(self):
        """落札価格を正しく抽出できるかテスト"""
        html = '''
        <div>落札価格：2,500,000円</div>
        '''
        result = PriceExtractor.extract_price(html)
        self.assertEqual(result['sold_price'], 2500000)
        self.assertFalse(result['is_unsold'])
    
    def test_extract_current_price(self):
        """現在価格を正しく抽出できるかテスト"""
        html = '''
        <div>現在価格：1,800,000円</div>
        '''
        result = PriceExtractor.extract_price(html)
        self.assertEqual(result['sold_price'], 1800000)
    
    def test_extract_unsold_by_bid_count(self):
        """入札数0の場合に主取りと判定できるかテスト"""
        html = '''
        <div>入札数: 0</div>
        '''
        result = PriceExtractor.extract_price(html)
        self.assertTrue(result['is_unsold'])
        self.assertIsNone(result['sold_price'])
    
    def test_extract_from_bid_history(self):
        """入札履歴から価格を正しく抽出できるかテスト"""
        html = '''
        <script>
        var bid_history = [
            {"price": "1000000", "time": "10:00"},
            {"price": "1500000", "time": "10:05"}
        ];
        </script>
        '''
        result = PriceExtractor.extract_price(html)
        self.assertEqual(result['sold_price'], 1500000)
    
    def test_extract_from_json_price(self):
        """JSON形式の価格を正しく抽出できるかテスト"""
        html = '''
        <script>
        var data = {"current_price": "2000000"};
        </script>
        '''
        result = PriceExtractor.extract_price(html)
        self.assertEqual(result['sold_price'], 2000000)
    
    def test_extract_from_html_element(self):
        """HTML要素から価格を正しく抽出できるかテスト"""
        html = '''
        <div class="price">3,000,000円</div>
        '''
        result = PriceExtractor.extract_price(html)
        self.assertEqual(result['sold_price'], 3000000)
    
    def test_extract_no_price(self):
        """価格情報がない場合のテスト"""
        html = '''
        <div>価格情報はありません</div>
        '''
        result = PriceExtractor.extract_price(html)
        self.assertIsNone(result['sold_price'])
        self.assertFalse(result['is_unsold'])

if __name__ == '__main__':
    unittest.main()
