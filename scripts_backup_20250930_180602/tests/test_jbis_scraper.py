"""
JBISスクレイパーのユニットテスト
"""
import unittest
from unittest.mock import patch, MagicMock
import os
from datetime import datetime

from bs4 import BeautifulSoup

from core.scraper.jbis_scraper import JBISScraper
from core.models.horse import Horse, Sex

class TestJBISScraper(unittest.TestCase):
    """JBISScraperクラスのテスト"""
    
    def setUp(self):
        """テストの前処理"""
        self.scraper = JBISScraper()
        
        # テスト用のHTMLファイルを読み込むディレクトリ
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    
    def _load_test_html(self, filename):
        """テスト用のHTMLファイルを読み込む"""
        filepath = os.path.join(self.test_data_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    @patch('core.scraper.jbis_scraper.JBISScraper.fetch_page')
    def test_fetch_horse_info(self, mock_fetch_page):
        """馬情報取得のテスト"""
        # モックの設定
        mock_fetch_page.return_value = self._load_test_html('jbis_horse_info.html')
        
        # テスト実行
        horse_id = "1234567890"
        result = self.scraper.fetch_horse_info(horse_id)
        
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
    
    def test_parse_horse_info(self):
        """馬情報のパーステスト"""
        # テスト用のHTMLを読み込む
        html = self._load_test_html('jbis_horse_info.html')
        
        # テスト実行
        result = self.scraper._parse_horse_info(html)
        
        # 検証
        self.assertIsInstance(result, dict)
        self.assertIn('total_prize', result)
        self.assertIn('race_record', result)
        self.assertIn('comment', result)
    
    def test_extract_prize_money(self):
        """賞金情報の抽出テスト"""
        # テスト用のHTMLを読み込む
        html = self._load_test_html('jbis_horse_info.html')
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result = self.scraper._extract_prize_money(soup)
        
        # 検証
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0.0)
    
    def test_extract_race_record(self):
        """レース成績の抽出テスト"""
        # テスト用のHTMLを読み込む
        html = self._load_test_html('jbis_horse_info.html')
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result = self.scraper._extract_race_record(soup)
        
        # 検証
        self.assertIsInstance(result, str)
        self.assertRegex(result, r'\d+-\d+-\d+-\d+')
    
    def test_extract_comment(self):
        """コメントの抽出テスト"""
        # テスト用のHTMLを読み込む
        html = self._load_test_html('jbis_horse_info.html')
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result = self.scraper._extract_comment(soup)
        
        # 検証
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
    
    def test_extract_horse_id(self):
        """馬IDの抽出テスト"""
        # テストケース
        test_cases = [
            ("https://www.jbis.or.jp/horse/0000000001/", "0000000001"),
            ("https://www.jbis.or.jp/horse/1234567890/", "1234567890"),
            ("https://www.jbis.or.jp/horse/9876543210/record/", "9876543210"),
            ("invalid_url", None),
        ]
        
        for url, expected in test_cases:
            with self.subTest(url=url):
                result = self.scraper._extract_horse_id(url)
                self.assertEqual(result, expected)
    
    @patch('core.scraper.jbis_scraper.JBISScraper.fetch_page')
    def test_search_horse(self, mock_fetch_page):
        """馬名検索のテスト"""
        # モックの設定
        mock_fetch_page.return_value = self._load_test_html('jbis_search_results.html')
        
        # テスト実行
        horse_name = "テスト馬"
        result = self.scraper.search_horse(horse_name)
        
        # 検証
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        # 検索結果の各項目を検証
        for item in result:
            self.assertIn('name', item)
            self.assertIn('url', item)
            self.assertIn('id', item)
    
    def test_parse_search_results(self):
        """検索結果のパーステスト"""
        # テスト用のHTMLを読み込む
        html = self._load_test_html('jbis_search_results.html')
        
        # テスト実行
        results = self.scraper._parse_search_results(html)
        
        # 検証
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # 検索結果の各項目を検証
        for result in results:
            self.assertIn('name', result)
            self.assertIn('url', result)
            self.assertIn('id', result)
    
    @patch('core.scraper.jbis_scraper.JBISScraper.fetch_page')
    def test_get_horse_id_by_name(self, mock_fetch_page):
        """馬名から馬IDを取得するテスト"""
        # モックの設定
        mock_fetch_page.return_value = self._load_test_html('jbis_search_results.html')
        
        # テスト実行
        horse_name = "テスト馬"
        result = self.scraper.get_horse_id_by_name(horse_name)
        
        # 検証
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertRegex(result, r'^\d{10}$')
    
    @patch('core.scraper.jbis_scraper.JBISScraper.fetch_page')
    def test_get_horse_info_by_name(self, mock_fetch_page):
        """馬名から馬情報を取得するテスト"""
        # モックの設定
        search_html = self._load_test_html('jbis_search_results.html')
        info_html = self._load_test_html('jbis_horse_info.html')
        
        # 検索結果と詳細情報のモックを設定
        mock_fetch_page.side_effect = [search_html, info_html]
        
        # テスト実行
        horse_name = "テスト馬"
        result = self.scraper.get_horse_info_by_name(horse_name)
        
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
