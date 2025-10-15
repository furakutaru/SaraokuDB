"""賞金情報抽出のテスト"""
import unittest
from unittest.mock import patch, MagicMock, ANY
import requests
from bs4 import BeautifulSoup

from scripts.components.prize_info_extractor import PrizeInfoExtractor

class TestPrizeInfoExtractor(unittest.TestCase):
    """PrizeInfoExtractorのテストクラス"""
    
    def setUp(self):
        self.logger = MagicMock()
        self.extractor = PrizeInfoExtractor(logger=self.logger)
        
        # requestsモジュールのモックをセットアップ
        self.requests_patcher = patch('requests.get')
        self.mock_requests_get = self.requests_patcher.start()
        
    def tearDown(self):
        # 各テスト後にモックをリセット
        self.requests_patcher.stop()
    
    def test_extract_success(self):
        """賞金情報の抽出テスト（成功ケース）"""
        # テスト用のHTMLを作成
        html = '''
        <div class="prize-money">
            総賞金：1,234万円
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result, success = self.extractor.extract(soup)
        
        # 検証
        self.assertTrue(success)
        self.assertEqual(result['prize_money'], 12340000)  # 1,234万円 → 12,340,000円
        self.logger.debug.assert_called_with('賞金情報を抽出しました: {\'prize_money\': 12340000}')
    
    def test_extract_missing_prize_info(self):
        """賞金情報が存在しない場合のテスト"""
        # テスト用のHTML（賞金情報なし）
        html = '<div class="other">テスト</div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result, success = self.extractor.extract(soup)
        
        # 検証
        self.assertFalse(success)
        self.assertIsNone(result)
        self.logger.debug.assert_called_with('賞金情報の要素が見つかりませんでした')
    
    def test_extract_invalid_format(self):
        """不正な形式の賞金情報のテスト"""
        # テスト用のHTML（不正な形式）
        html = '''
        <div class="prize-money">
            賞金: 不正な値
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result, success = self.extractor.extract(soup)
        
        # 検証
        self.assertFalse(success)
        self.assertIsNone(result)
        self.logger.debug.assert_called_with('賞金情報のパターンが一致しませんでした')
    
    def test_extract_exception_handling(self):
        """例外発生時のテスト"""
        # 例外を発生させるためのモック
        with patch.object(BeautifulSoup, 'find', side_effect=Exception('Test error')):
            result, success = self.extractor.extract(BeautifulSoup('', 'html.parser'))
            
            # 検証
            self.assertFalse(success)
            self.assertIsNone(result)
            self.logger.error.assert_called()
    
    def test_extract_from_jbis(self):
        """JBISからの賞金情報取得のテスト（モック使用）"""
        # モックのレスポンスを設定
        mock_response = MagicMock()
        mock_response.text = '''
        <html>
            <body>
                <div class="dbdata_main">
                    <div class="dbdata_main_prize">
                        <div class="dbdata_main_prize_money">
                            <span>総賞金</span>
                            <span>1,234</span>
                            <span>万円</span>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        '''
        self.mock_requests_get.return_value = mock_response
        
        # テスト実行
        result = self.extractor.extract_from_jbis('https://www.jbis.or.jp/horse/0000000000/')
        
        # 検証
        self.assertEqual(result, 12340000)  # 1,234万円 → 12,340,000円
        self.mock_requests_get.assert_called_once_with('https://www.jbis.or.jp/horse/0000000000/')
    
    def test_extract_from_jbis_missing_prize_info(self):
        """JBISページに賞金情報が存在しない場合のテスト"""
        # モックのレスポンスを設定（賞金情報なし）
        mock_response = MagicMock()
        mock_response.text = '<html><body><div class="dbdata_main"></div></body></html>'
        self.mock_requests_get.return_value = mock_response
        
        # テスト実行
        result = self.extractor.extract_from_jbis('https://www.jbis.or.jp/horse/0000000001/')
        
        # 検証
        self.assertIsNone(result)
        self.mock_requests_get.assert_called_once_with('https://www.jbis.or.jp/horse/0000000001/')
    
    def test_extract_from_jbis_invalid_url(self):
        """無効なURLが渡された場合のテスト"""
        result = self.extractor.extract_from_jbis('')
        self.assertIsNone(result)
        
        result = self.extractor.extract_from_jbis(None)
        self.assertIsNone(result)
    
    def test_extract_from_jbis_request_error(self):
        """リクエストエラーが発生した場合のテスト"""
        # モックの例外を設定
        from requests.exceptions import RequestException
        self.mock_requests_get.side_effect = RequestException('Connection error')
        
        # テスト実行
        result = self.extractor.extract_from_jbis('https://www.jbis.or.jp/horse/0000000002/')
        
        # 検証
        self.assertIsNone(result)
        self.logger.error.assert_called_with('JBISへのリクエスト中にエラーが発生しました: Connection error')
        self.mock_requests_get.assert_called_once_with('https://www.jbis.or.jp/horse/0000000002/')
    
    def test_extract_from_jbis_invalid_format(self):
        """不正な形式の賞金情報が含まれる場合のテスト"""
        # モックのレスポンスを設定（不正な形式の賞金情報）
        mock_response = MagicMock()
        mock_response.text = '''
        <html>
            <body>
                <div class="dbdata_main">
                    <div class="dbdata_main_prize">
                        <div class="dbdata_main_prize_money">
                            <span>Invalid Prize Info</span>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        '''
        self.mock_requests_get.return_value = mock_response
        
        # テスト実行
        result = self.extractor.extract_from_jbis('https://www.jbis.or.jp/horse/0000000003/')
        
        # 検証
        self.assertIsNone(result)
        self.mock_requests_get.assert_called_once_with('https://www.jbis.or.jp/horse/0000000003/')
        self.logger.debug.assert_called_with('賞金情報のパターンが一致しませんでした: Invalid Prize Info')

if __name__ == '__main__':
    unittest.main()
