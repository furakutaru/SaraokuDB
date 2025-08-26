"""
楽天競馬オークションスクレイパーのユニットテスト
"""
import unittest
from unittest.mock import patch, MagicMock
import os
from datetime import datetime

from bs4 import BeautifulSoup

from core.scraper.rakuten_scraper import RakutenScraper
from core.models.horse import Horse, Sex
from core.models.auction import Auction

class TestRakutenScraper(unittest.TestCase):
    """RakutenScraperクラスのテスト"""
    
    def setUp(self):
        """テストの前処理"""
        self.scraper = RakutenScraper()
        
        # テスト用のHTMLファイルを読み込む
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        
    def _load_test_html(self, filename):
        """テスト用のHTMLファイルを読み込む"""
        filepath = os.path.join(self.test_data_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    @patch('core.scraper.rakuten_scraper.RakutenScraper.fetch_page')
    def test_fetch_horse_list(self, mock_fetch_page):
        """馬一覧取得のテスト"""
        # モックの設定
        mock_fetch_page.return_value = self._load_test_html('horse_list.html')
        
        # テスト実行
        url = "https://www.rakuten-keiba-auction.net/auction/auction_list.php"
        result = self.scraper.fetch_horse_list(url)
        
        # 検証
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        # 最初の馬の情報を検証
        first_horse = result[0]
        self.assertIn('name', first_horse)
        self.assertIn('url', first_horse)
        self.assertIn('sire', first_horse)
        self.assertIn('dam', first_horse)
        self.assertIn('damsire', first_horse)
    
    @patch('core.scraper.rakuten_scraper.RakutenScraper.fetch_page')
    def test_fetch_horse_detail(self, mock_fetch_page):
        """馬詳細情報取得のテスト"""
        # モックの設定
        mock_fetch_page.return_value = self._load_test_html('horse_detail.html')
        
        # テスト実行
        url = "https://www.rakuten-keiba-auction.net/auction/detail.php?key=test123"
        result = self.scraper.fetch_horse_detail(url)
        
        # 検証
        self.assertIsInstance(result, dict)
        self.assertIn('horse', result)
        self.assertIn('auction', result)
        
        # 馬情報の検証
        horse = result['horse']
        self.assertIsInstance(horse, Horse)
        self.assertIsNotNone(horse.name)
        self.assertIn(horse.sex, [Sex.MALE, Sex.FEMALE, Sex.GELDING])
        self.assertIsInstance(horse.age, int)
        self.assertIsNotNone(horse.sire)
        self.assertIsNotNone(horse.dam)
        self.assertIsNotNone(horse.damsire)
        
        # オークション情報の検証
        auction = result['auction']
        self.assertIsInstance(auction, Auction)
        self.assertIsNotNone(auction.auction_id)
        self.assertIsNotNone(auction.horse_id)
        self.assertIsInstance(auction.auction_date, datetime)
        self.assertIsNotNone(auction.seller)
        self.assertIsInstance(auction.price, float)
    
    def test_parse_horse_info(self):
        """馬情報のパーステスト"""
        # テスト用のHTMLを読み込む
        html = self._load_test_html('horse_detail.html')
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        horse_info = self.scraper._parse_horse_info(soup)
        
        # 検証
        self.assertIsInstance(horse_info, dict)
        self.assertIn('name', horse_info)
        self.assertIn('sex', horse_info)
        self.assertIn('age', horse_info)
        self.assertIn('sire', horse_info)
        self.assertIn('dam', horse_info)
        self.assertIn('damsire', horse_info)
        self.assertIn('total_prize', horse_info)
        self.assertIn('race_record', horse_info)
        self.assertIn('comment', horse_info)
    
    def test_parse_auction_info(self):
        """オークション情報のパーステスト"""
        # テスト用のHTMLを読み込む
        html = self._load_test_html('horse_detail.html')
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        auction_info = self.scraper._parse_auction_info(soup)
        
        # 検証
        self.assertIsInstance(auction_info, dict)
        self.assertIn('auction_id', auction_info)
        self.assertIn('horse_id', auction_info)
        self.assertIn('auction_date', auction_info)
        self.assertIn('seller', auction_info)
        self.assertIn('buyer', auction_info)
        self.assertIn('price', auction_info)
        self.assertIn('is_unsold', auction_info)
        self.assertIn('comment', auction_info)
    
    def test_extract_sex_and_age(self):
        """性別と年齢の抽出テスト"""
        # テストケース
        test_cases = [
            ("サンプル馬名 牡3", ("牡", 3)),
            ("テスト馬 牝4", ("牝", 4)),
            ("サンプル セ5", ("セン", 5)),
            ("テスト セ6", ("セン", 6)),
        ]
        
        for input_str, expected in test_cases:
            with self.subTest(input_str=input_str):
                result = self.scraper._extract_sex_and_age(input_str)
                self.assertEqual(result, expected)
    
    def test_extract_pedigree(self):
        """血統情報の抽出テスト"""
        # テストケース
        test_cases = [
            ("父：ディープインパクト 母：ウインドインハーヘア 母の父：サンデーサイレンス",
             ("ディープインパクト", "ウインドインハーヘア", "サンデーサイレンス")),
            ("父:キタサンブラック 母: トーセンジョーダン 母の父: シンボリクリスエス",
             ("キタサンブラック", "トーセンジョーダン", "シンボリクリスエス")),
        ]
        
        for input_str, expected in test_cases:
            with self.subTest(input_str=input_str):
                result = self.scraper._extract_pedigree(input_str)
                self.assertEqual(result, expected)
    
    def test_extract_prize_money(self):
        """賞金情報の抽出テスト"""
        # テストケース
        test_cases = [
            ("総賞金 12,345,678円", 1234.57),
            ("賞金：9,876,543円", 987.65),
            ("賞金: 1,234円", 0.12),
            ("賞金なし", 0.0),
        ]
        
        for input_str, expected in test_cases:
            with self.subTest(input_str=input_str):
                result = self.scraper._extract_prize_money(input_str)
                self.assertAlmostEqual(result, expected, places=2)
    
    def test_extract_race_record(self):
        """レース成績の抽出テスト"""
        # テストケース
        test_cases = [
            ("10-3-2-1", (10, 3, 2, 1)),
            ("5-1-0-0", (5, 1, 0, 0)),
            ("20-5-3-2", (20, 5, 3, 2)),
        ]
        
        for input_str, expected in test_cases:
            with self.subTest(input_str=input_str):
                result = self.scraper._extract_race_record(input_str)
                self.assertEqual(result, expected)
    
    @patch('core.scraper.rakuten_scraper.RakutenScraper._get_jbis_horse_info')
    def test_get_jbis_horse_info(self, mock_jbis_info):
        """JBIS馬情報取得のテスト"""
        # モックの設定
        mock_jbis_info.return_value = {
            'total_prize': 1500.5,
            'race_record': '10-3-2-1',
            'comment': 'テストコメント'
        }
        
        # テストデータ
        horse_name = "テスト馬"
        
        # テスト実行
        result = self.scraper._get_jbis_horse_info(horse_name)
        
        # 検証
        self.assertIsInstance(result, dict)
        self.assertEqual(result['total_prize'], 1500.5)
        self.assertEqual(result['race_record'], '10-3-2-1')
        self.assertEqual(result['comment'], 'テストコメント')
        mock_jbis_info.assert_called_once_with(horse_name)
    
    @patch('core.scraper.rakuten_scraper.RakutenScraper.fetch_page')
    def test_get_jbis_horse_info_integration(self, mock_fetch_page):
        """JBIS馬情報取得の統合テスト"""
        # モックの設定
        mock_fetch_page.return_value = self._load_test_html('jbis_horse_info.html')
        
        # テスト実行
        horse_name = "テスト馬"
        result = self.scraper._get_jbis_horse_info(horse_name)
        
        # 検証
        self.assertIsInstance(result, dict)
        self.assertIn('total_prize', result)
        self.assertIn('race_record', result)
        self.assertIn('comment', result)
        
        # 賞金情報の検証
        self.assertIsInstance(result['total_prize'], float)
        self.assertGreaterEqual(result['total_prize'], 0.0)
        
        # レース成績の検証
        self.assertIsInstance(result['race_record'], str)
        self.assertRegex(result['race_record'], r'\d+-\d+-\d+-\d+')
        
        # コメントの検証
        self.assertIsInstance(result['comment'], str)
        self.assertGreater(len(result['comment']), 0)

if __name__ == '__main__':
    unittest.main()
