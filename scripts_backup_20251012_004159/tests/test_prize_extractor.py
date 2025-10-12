"""PrizeInfoExtractorのテスト"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

# テスト対象のモジュールをインポート
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from components.prize_info_extractor import PrizeInfoExtractor

class TestPrizeExtractor(unittest.TestCase):    
    def setUp(self):
        """テストの前処理"""
        self.logger = MagicMock()
        self.extractor = PrizeInfoExtractor(logger=self.logger)
        
        # テスト用HTMLの読み込み
        test_data_path = os.path.join(os.path.dirname(__file__), 'test_data/prize_test.html')
        with open(test_data_path, 'r', encoding='utf-8') as f:
            self.test_html = f.read()
        
        self.soup = BeautifulSoup(self.test_html, 'html.parser')
    
    def test_extract_auction_prize(self):
        """オークション時点の賞金抽出テスト"""
        # テスト実行
        result, success = self.extractor.extract(self.soup)
        
        # 検証
        self.assertTrue(success)
        self.assertIn('total_prize_start', result)
        self.assertEqual(result['total_prize_start'], 12340000)  # 1,234万円 → 12,340,000円
        
        # ログの検証
        self.logger.debug.assert_any_call('オークション時点の賞金を抽出しました: 12340000円')
    
    @patch('requests.get')
    def test_extract_jbis_prize(self, mock_get):
        """JBISからの賞金抽出テスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.text = """
        <html>
        <body>
            <dt>総賞金</dt>
            <dd>5,678.9万円</dd>
        </body>
        </html>
        """
        mock_get.return_value = mock_response
        
        # テスト実行
        result = self.extractor.extract_from_jbis('https://www.jbis.or.jp/horse/1234567890/')
        
        # 検証
        self.assertEqual(result, 56789000)  # 5,678.9万円 → 56,789,000円
        self.logger.debug.assert_any_call('dt/ddタグから賞金情報を検出')
    
    def test_extract_jbis_with_pedigree_url(self):
        """血統情報ページURLの正規化テスト"""
        # テスト用のレスポンスを設定
        test_html = """
        <html>
        <body>
            <dt>総賞金</dt>
            <dd>1,000.0万円</dd>
        </body>
        </html>
        """
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = test_html
            mock_get.return_value = mock_response
            
            # 血統情報ページのURLでテスト
            result = self.extractor.extract_from_jbis('https://www.jbis.or.jp/horse/1234567890/pedigree/')
            
            # 正規化されたURLでリクエストが行われたことを確認
            mock_get.assert_called_once()
            args, _ = mock_get.call_args
            self.assertIn('https://www.jbis.or.jp/horse/1234567890/', args[0])
    
    def test_extract_with_invalid_html(self):
        """不正なHTMLからの抽出テスト"""
        # 賞金情報のないHTML
        invalid_html = "<html><body><div>No prize info here</div></body></html>"
        soup = BeautifulSoup(invalid_html, 'html.parser')
        
        # テスト実行
        result, success = self.extractor.extract(soup)
        
        # 検証
        self.assertFalse(success)
        self.assertIsNone(result)
        self.logger.debug.assert_any_call('賞金情報を取得できませんでした')

if __name__ == '__main__':
    unittest.main()
