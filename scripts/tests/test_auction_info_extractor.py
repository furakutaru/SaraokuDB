"""
AuctionInfoExtractorのテストモジュール
"""
import unittest
import logging
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup

# テスト対象のモジュールをインポート
from components.auction_info_extractor import AuctionInfoExtractor

class TestAuctionInfoExtractor(unittest.TestCase):
    """AuctionInfoExtractorのテストクラス"""
    
    def setUp(self):
        """テストの前処理"""
        # テスト用のロガーモックを作成
        self.logger = MagicMock(spec=logging.Logger)
        self.extractor = AuctionInfoExtractor(logger=self.logger)
        
        # テスト用のHTML
        self.test_html = """
        <div class="subData__startTime" data-v-e1d77a5d="">
            <span class="subData__label" data-v-e1d77a5d="">開始時間</span>
            <span class="subData__value" data-v-e1d77a5d="">2025年08月24日 12:00</span>
        </div>
        """
    
    def test_extract_date_with_valid_html(self):
        """有効なHTMLからオークション日を抽出するテスト"""
        result = self.extractor.extract_date(self.test_html)
        self.assertEqual(result, {'auction_date': '2025-08-24'})
    
    def test_extract_date_with_bs4_object(self):
        """BeautifulSoupオブジェクトからオークション日を抽出するテスト"""
        html = """
        <div class="subData__startTime">
            <span class="subData__label">開始時間</span>
            <span class="subData__value">2025年08月24日 12:00</span>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        result = self.extractor.extract_date(soup)
        self.assertEqual(result, {'auction_date': '2025-08-24'})
    
    def test_extract_date_with_invalid_html(self):
        """無効なHTMLからの抽出テスト"""
        # 日付要素が存在しない場合
        html = """<div></div>"""
        result = self.extractor.extract_date(html)
        self.assertEqual(result, {'auction_date': None})
        
        # 空の文字列を渡した場合
        result = self.extractor.extract_date("")
        self.assertEqual(result, {'auction_date': None})
        
        # Noneを渡した場合
        result = self.extractor.extract_date(None)
        self.assertEqual(result, {'auction_date': None})
    
    def test_extract_date_with_different_format(self):
        """異なる日付形式のテスト"""
        # 1桁の月日を含む場合
        html = """
        <div class="subData__startTime">
            <span class="subData__value">2025年8月5日 09:00</span>
        </div>
        """
        result = self.extractor.extract_date(html)
        self.assertEqual(result, {'auction_date': '2025-08-05'})  # 0埋めされることを確認

    def test_set_detail_url(self):
        """詳細ページURLの設定と取得のテスト"""
        test_url = "https://example.com/auction/123"
        self.extractor.set_detail_url(test_url)
        
        # ログが記録されたことを確認
        self.extractor.logger.debug.assert_called_with(
            f'オークション詳細ページのURLを設定しました: {test_url}'
        )
        
        # URLが正しく設定されたことを確認
        self.assertEqual(self.extractor.detail_url, test_url)
    
    def test_get_info_without_soup(self):
        """soupが設定されていない状態でのget_infoのテスト"""
        test_url = "https://example.com/auction/123"
        self.extractor.set_detail_url(test_url)
        
        result = self.extractor.get_info()
        self.assertEqual(result, {
            'auction_date': None,
            'auction_url': test_url
        })
    
    def test_get_info_with_soup(self):
        """soupが設定されている状態でのget_infoのテスト"""
        test_url = "https://example.com/auction/123"
        self.extractor.set_detail_url(test_url)
        self.extractor.extract_date(self.test_html)  # soupを設定
        
        result = self.extractor.get_info()
        self.assertEqual(result, {
            'auction_date': '2025-08-24',
            'auction_url': test_url
        })

if __name__ == '__main__':
    unittest.main()
