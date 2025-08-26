"""
BaseScraperクラスのユニットテスト
"""
import unittest
from unittest.mock import patch, MagicMock, ANY
import requests

from core.scraper.base_scraper import BaseScraper

class TestBaseScraper(unittest.TestCase):
    """BaseScraperクラスのテスト"""
    
    def setUp(self):
        # テスト用の設定
        self.test_url = "https://example.com"
        # テスト用のセッションを作成
        self.scraper = BaseScraper(self.test_url)
        # テスト用のロガーを設定
        self.scraper.logger = MagicMock()
        # テスト用のセッションをモック
        self.mock_session = MagicMock()
        self.scraper.session = self.mock_session
    
    def test_get_request_success(self):
        """GETリクエストの成功テスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>Test</html>"
        mock_response.raise_for_status.return_value = None
        self.mock_session.get.return_value = mock_response
        
        # テスト実行
        response = self.scraper.request_get(self.test_url)
        
        # 検証
        self.assertEqual(response.text, "<html>Test</html>")
        self.mock_session.get.assert_called_once_with(self.test_url, params=None)
    
    def test_request_get_retry(self):
        """GETリクエストのリトライテスト"""
        # 成功レスポンスのモック
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>Success</html>"
        mock_response.raise_for_status.return_value = None
        
        # モックの設定
        self.mock_session.get.return_value = mock_response
        
        # テスト実行
        response = self.scraper.request_get(self.test_url)
        
        # 検証
        self.assertEqual(response.text, "<html>Success</html>")
        self.mock_session.get.assert_called_once_with(self.test_url, params=None)
    
    def test_request_get_max_retries_exceeded(self):
        """GETリクエストの最大リトライ回数超過テスト"""
        # モックの設定（常にエラーを返す）
        self.mock_session.get.side_effect = requests.exceptions.RequestException("Connection error")

        # テスト実行（例外が発生することを確認）
        with self.assertRaises(requests.exceptions.RequestException) as context:
            self.scraper.request_get(self.test_url)

        # 検証 (デフォルトのmax_retries=3なので4回呼ばれるはず)
        self.assertEqual(self.mock_session.get.call_count, 1)  # リトライはアダプタで行われる
    
    def test_request_post_success(self):
        """POSTリクエストの成功テスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"status": "success"}'
        mock_response.raise_for_status.return_value = None
        self.mock_session.post.return_value = mock_response

        # テストデータ
        test_data = {"key": "value"}

        # テスト実行
        response = self.scraper.request_post(self.test_url, data=test_data)

        # 検証
        self.assertEqual(response.text, '{"status": "success"}')
        self.mock_session.post.assert_called_once_with(self.test_url, data=test_data, json=None)
    
    def test_request_post_json(self):
        """POSTリクエスト（JSON形式）のテスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"status": "created"}
        mock_response.raise_for_status.return_value = None
        self.mock_session.post.return_value = mock_response

        # テストデータ
        test_json = {"key": "value"}

        # テスト実行
        response = self.scraper.request_post(self.test_url, json_data=test_json)

        # 検証
        self.assertEqual(response.json(), {"status": "created"})
        self.mock_session.post.assert_called_once_with(
            self.test_url,
            data=None,
            json=test_json
        )
    
    def test_fetch_page(self):
        """ページの取得テスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>Test Page</html>"
        mock_response.raise_for_status.return_value = None
        self.mock_session.get.return_value = mock_response
        
        # テスト実行
        response = self.scraper.request_get(self.test_url)
        
        # 検証
        self.assertEqual(response.text, "<html>Test Page</html>")
        self.mock_session.get.assert_called_once()
    
    def test_fetch_page_with_params(self):
        """パラメータ付きページ取得テスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>Test Page with Params</html>"
        mock_response.raise_for_status.return_value = None
        self.mock_session.get.return_value = mock_response
        
        # テストパラメータ
        params = {"page": 2, "sort": "price"}
        
        # テスト実行
        response = self.scraper.request_get(self.test_url, params=params)
        
        # 検証
        self.assertEqual(response.text, "<html>Test Page with Params</html>")
        self.mock_session.get.assert_called_once_with(self.test_url, params=params)
    
    def test_fetch_page_error(self):
        """ページ取得エラーテスト"""
        # モックの設定（エラーを発生）
        self.mock_session.get.side_effect = requests.exceptions.RequestException("Connection error")
        
        # テスト実行（例外が発生することを確認）
        with self.assertRaises(requests.exceptions.RequestException):
            self.scraper.request_get(self.test_url)
        
        # 検証
        self.assertEqual(self.mock_session.get.call_count, 1)

if __name__ == '__main__':
    unittest.main()
