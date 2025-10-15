import unittest
from unittest.mock import patch, MagicMock
from improved_scraper import ImprovedRakutenScraper

class TestHorseProcessing(unittest.TestCase):    
    def setUp(self):
        """テストのセットアップ"""
        self.scraper = ImprovedRakutenScraper(test_mode=True)
        
    def test_process_horse_detail_complete_data(self):
        """必須フィールドが全て揃っている場合のテスト"""
        test_data = {
            'url': 'http://example.com/horse/1',
            'name': 'テスト馬',
            'prize_money': 1000.0,
            'id': 'test_horse_1'
        }
        
        # モックの設定
        with patch.object(self.scraper, 'scrape_horse_detail') as mock_scrape:
            mock_scrape.return_value = {
                'name': 'テスト馬',
                'sex': '牡',
                'age': 3,
                'sire': '父馬',
                'dam': '母馬',
                'damsire': '母父馬',
                'seller': 'テスト牧場',
                'price': 5000.0
            }
            
            result = self.scraper._process_horse_detail(test_data, '2025-08-22')
            
            # 結果の検証
            self.assertIsNotNone(result)
            self.assertEqual(result['name'], 'テスト馬')
            self.assertEqual(result['sex'], '牡')
            self.assertEqual(result['auction_date'], '2025-08-22')
    
    def test_process_horse_detail_missing_fields(self):
        """一部の必須フィールドが欠けている場合のテスト"""
        test_data = {
            'url': 'http://example.com/horse/2',
            'name': 'テスト馬2',
            'prize_money': 2000.0,
            'id': 'test_horse_2'
        }
        
        # モックの設定（一部フィールドが欠けている）
        with patch.object(self.scraper, 'scrape_horse_detail') as mock_scrape:
            mock_scrape.return_value = {
                'name': 'テスト馬2',
                'sex': '',  # 空文字
                'age': 0,   # 0
                'sire': '父馬',
                # dam が欠けている
                'damsire': '母父馬',
                # seller が欠けている
                'price': 3000.0
            }
            
            result = self.scraper._process_horse_detail(test_data, '2025-08-22')
            
            # 結果の検証
            self.assertIsNotNone(result)
            self.assertEqual(result['name'], 'テスト馬2')
            self.assertEqual(result['sex'], '不明')  # デフォルト値が設定される
            self.assertEqual(result['age'], 0)       # 0のまま
            self.assertEqual(result['dam'], '不明')   # デフォルト値が設定される
            self.assertEqual(result['seller'], '不明') # デフォルト値が設定される
    
    def test_process_horse_detail_no_required_fields(self):
        """必須フィールドが全くない場合のテスト"""
        test_data = {
            'url': 'http://example.com/horse/3',
            'name': 'テスト馬3',
            'prize_money': 3000.0,
            'id': 'test_horse_3'
        }
        
        # モックの設定（必須フィールドが全くない）
        with patch.object(self.scraper, 'scrape_horse_detail') as mock_scrape:
            mock_scrape.return_value = {
                'name': 'テスト馬3',
                'price': 4000.0
            }
            
            result = self.scraper._process_horse_detail(test_data, '2025-08-22')
            
            # 結果の検証
            self.assertIsNotNone(result)
            self.assertEqual(result['name'], 'テスト馬3')
            self.assertEqual(result['sex'], '不明')
            self.assertEqual(result['age'], 0)
            self.assertEqual(result['sire'], '不明')
            self.assertEqual(result['dam'], '不明')
            self.assertEqual(result['damsire'], '不明')
            self.assertEqual(result['seller'], '不明')
            self.assertEqual(result['auction_date'], '2025-08-22')

if __name__ == '__main__':
    unittest.main()
