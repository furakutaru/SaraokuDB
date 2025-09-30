"""
メインアプリケーションの統合テスト
"""
import unittest
import os
import tempfile
import json
from unittest.mock import patch, MagicMock

from scripts.main import HorseAuctionScraper
from core.models.horse import Horse, Sex
from core.models.auction import Auction

class TestHorseAuctionScraper(unittest.TestCase):
    """HorseAuctionScraperクラスの統合テスト"""
    
    def setUp(self):
        """テストの前処理"""
        # テスト用の一時ディレクトリを作成
        self.test_dir = tempfile.mkdtemp()
        self.scraper = HorseAuctionScraper(output_dir=self.test_dir)
        
        # モックの設定
        self.mock_horse = {
            'name': 'テスト馬',
            'sex': '牡',
            'age': 3,
            'sire': 'テスト父',
            'dam': 'テスト母',
            'damsire': 'テスト母父',
            'total_prize': 1000.5,
            'race_record': '10-3-2-1',
            'comment': 'テストコメント'
        }
        
        self.mock_auction = {
            'auction_id': 'A001',
            'horse_id': 'H001',
            'auction_date': '2023-01-01',
            'seller': 'テスト出品者',
            'buyer': 'テスト落札者',
            'price': 3000.5,
            'is_unsold': False,
            'comment': 'テストコメント'
        }
    
    def tearDown(self):
        """テストの後処理"""
        # テスト用の一時ディレクトリを削除
        if os.path.exists(self.test_dir):
            for filename in os.listdir(self.test_dir):
                file_path = os.path.join(self.test_dir, filename)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            os.rmdir(self.test_dir)
    
    @patch('scripts.main.RakutenScraper.fetch_horse_list')
    def test_scrape_horse_list(self, mock_fetch):
        """馬一覧のスクレイピングテスト"""
        # モックの設定
        mock_fetch.return_value = [
            {
                'name': 'テスト馬1',
                'url': 'https://example.com/horse1',
                'sire': '父1',
                'dam': '母1',
                'damsire': '母父1'
            },
            {
                'name': 'テスト馬2',
                'url': 'https://example.com/horse2',
                'sire': '父2',
                'dam': '母2',
                'damsire': '母父2'
            }
        ]
        
        # テスト実行
        url = "https://example.com/horse_list"
        result = self.scraper.scrape_horse_list(url)
        
        # 検証
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'テスト馬1')
        self.assertEqual(result[1]['name'], 'テスト馬2')
        
        # ファイルが作成されたことを確認
        files = os.listdir(self.test_dir)
        self.assertTrue(any(f.startswith('horses_') and f.endswith('.json') for f in files))
    
    @patch('scripts.main.RakutenScraper.fetch_horse_detail')
    @patch('scripts.main.JBISScraper.fetch_horse_info')
    def test_scrape_horse_detail(self, mock_jbis, mock_rakuten):
        """馬詳細情報のスクレイピングテスト"""
        # モックの設定
        mock_rakuten.return_value = {
            'horse': self.mock_horse,
            'auction': self.mock_auction
        }
        
        mock_jbis.return_value = {
            'total_prize': 1500.0,
            'race_record': '15-5-3-2',
            'comment': 'JBISからの追加情報'
        }
        
        # テスト実行
        url = "https://example.com/horse_detail"
        result = self.scraper.scrape_horse_detail(url)
        
        # 検証
        self.assertIn('horse', result)
        self.assertIn('auction', result)
        
        # 馬情報の検証
        horse = result['horse']
        self.assertEqual(horse['name'], 'テスト馬')
        self.assertEqual(horse['sex'], '牡')
        self.assertEqual(horse['age'], 3)
        self.assertEqual(horse['total_prize'], 1500.0)  # JBISの賞金に更新されている
        
        # オークション情報の検証
        auction = result['auction']
        self.assertEqual(auction['auction_id'], 'A001')
        self.assertEqual(auction['price'], 3000.5)
        
        # ファイルが作成されたことを確認
        files = os.listdir(self.test_dir)
        self.assertTrue(any(f.startswith('horse_detail_') and f.endswith('.json') for f in files))
    
    @patch('scripts.main.RakutenScraper.fetch_horse_detail')
    def test_scrape_horse_detail_jbis_error(self, mock_rakuten):
        """JBIS情報の取得に失敗した場合のテスト"""
        # モックの設定（JBISはエラーを返す）
        mock_rakuten.return_value = {
            'horse': self.mock_horse,
            'auction': self.mock_auction
        }
        
        # JBISのモックをパッチしてエラーを発生させる
        with patch('scripts.main.JBISScraper.fetch_horse_info') as mock_jbis:
            mock_jbis.side_effect = Exception("JBIS connection error")
            
            # テスト実行（エラーが発生しても処理は継続）
            url = "https://example.com/horse_detail"
            result = self.scraper.scrape_horse_detail(url)
            
            # 検証
            self.assertIn('horse', result)
            self.assertEqual(result['horse']['total_prize'], 1000.5)  # 元の値が維持されている
    
    def test_extract_horse_id(self):
        """馬IDの抽出テスト"""
        # テストケース
        test_cases = [
            ("https://example.com/horse/12345", "12345"),
            ("https://example.com/horse/abc123?param=value", "abc123"),
            ("no_id_in_url", None)
        ]
        
        for url, expected in test_cases:
            with self.subTest(url=url):
                result = self.scraper._extract_horse_id(url)
                self.assertEqual(result, expected)
    
    @patch('scripts.main.HorseAuctionScraper.scrape_horse_list')
    @patch('scripts.main.HorseAuctionScraper.scrape_horse_detail')
    def test_main_workflow(self, mock_detail, mock_list):
        """メインワークフローのテスト"""
        # モックの設定
        mock_list.return_value = [
            {
                'name': 'テスト馬1',
                'url': 'https://example.com/horse1',
                'sire': '父1',
                'dam': '母1',
                'damsire': '母父1'
            }
        ]
        
        mock_detail.return_value = {
            'horse': self.mock_horse,
            'auction': self.mock_auction
        }
        
        # テスト実行（コマンドライン引数をシミュレート）
        with patch('sys.argv', ['main.py', 'list', 'https://example.com/horse_list']):
            from scripts.main import main
            main()
        
        # モックが呼び出されたことを確認
        mock_list.assert_called_once_with('https://example.com/horse_list')
        
        # ファイルが作成されたことを確認
        files = os.listdir(self.test_dir)
        self.assertTrue(any(f.startswith('horses_') and f.endswith('.json') for f in files))
    
    @patch('builtins.print')
    def test_main_invalid_command(self, mock_print):
        """無効なコマンドのテスト"""
        # テスト実行（無効なコマンド）
        with patch('sys.argv', ['main.py', 'invalid_command']):
            from scripts.main import main
            with self.assertRaises(SystemExit):
                main()
        
        # エラーメッセージが表示されたことを確認
        mock_print.assert_called_with("有効なコマンドを指定してください。")

if __name__ == '__main__':
    unittest.main()
