"""
RakutenAuctionScraperのテスト
"""
import unittest
import json
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
from ..scrapers.rakuten_scraper import RakutenAuctionScraper, get_horse_links

class TestRakutenAuctionScraper(unittest.TestCase):
    """RakutenAuctionScraperのテストケース"""
    
    def setUp(self):
        """テストの前処理"""
        self.scraper = RakutenAuctionScraper()
        
        # テスト用のHTMLサンプル
        self.sample_html = """
        <!DOCTYPE html>
        <html>
        <head><title>テスト用ページ</title></head>
        <body>
            <h1 class="horseName">テスト馬</h1>
            <div class="horseTitle">牡3歳</div>
            <div class="weight">500kg</div>
            <div class="seller">テスト牧場</div>
            <div class="price">1,234万円</div>
            <div class="bid-num">5</div>
            <div class="comment">テストコメント</div>
        </body>
        </html>
        """
    
    def test_scrape_horse_detail(self):
        """馬の詳細情報の抽出テスト"""
        # テスト用のレスポンスをモック
        with patch('requests.Session.get') as mock_get:
            # モックの設定
            mock_response = MagicMock()
            mock_response.text = self.sample_html
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # テスト実行
            horse_data, auction_data = self.scraper.scrape_horse_detail("http://example.com/horse/1")
            
            # アサーション
            self.assertEqual(horse_data['name'], 'テスト馬')
            self.assertEqual(horse_data['sex'], '牡')
            self.assertEqual(horse_data['age'], 3)
            self.assertEqual(auction_data['seller'], 'テスト牧場')
            self.assertEqual(auction_data['sold_price'], 1234)
            self.assertEqual(auction_data['bid_num'], '5')
            self.assertEqual(auction_data['comment'], 'テストコメント')
    
    @patch('requests.Session.get')
    def test_process_horses(self, mock_get):
        """複数の馬の処理テスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.text = self.sample_html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # テストデータ
        test_horses = [
            {'name': 'テスト馬1', 'detail_url': 'http://example.com/horse/1'},
            {'name': 'テスト馬2', 'detail_url': 'http://example.com/horse/2'}
        ]
        
        # テスト実行
        processed = self.scraper.process_horse_details(test_horses)
        
        # アサーション
        self.assertEqual(len(processed), 2)
        self.assertEqual(processed[0]['name'], 'テスト馬1')
        self.assertEqual(processed[1]['name'], 'テスト馬2')

class TestHorseLinks(unittest.TestCase):
    """馬のリンク取得のテストケース"""
    
    @patch('requests.get')
    def test_get_horse_links(self, mock_get):
        """馬のリンク取得テスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.text = """
        <html>
        <body>
            <a href="/horse/1" class="horse-link">馬1</a>
            <a href="/horse/2" class="horse-link">馬2</a>
        </body>
        </html>
        """
        mock_get.return_value = mock_response
        
        # テスト実行
        links = get_horse_links()
        
        # アサーション
        self.assertEqual(len(links), 2)
        self.assertIn('https://auction.keiba.rakuten.co.jp/horse/1', links)
        self.assertIn('https://auction.keiba.rakuten.co.jp/horse/2', links)

if __name__ == '__main__':
    unittest.main()
