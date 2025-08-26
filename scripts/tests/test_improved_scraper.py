"""
ImprovedRakutenScraperの統合テスト
"""
import unittest
from unittest.mock import MagicMock, patch, ANY, call
from bs4 import BeautifulSoup
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# コンポーネントのインポート
from components.horse_info_extractor import HorseInfoExtractor
from components.seller_info_extractor import SellerInfoExtractor
from components.comment_extractor import CommentExtractor
from components.prize_info_extractor import PrizeInfoExtractor
from components.price_info_extractor import PriceInfoExtractor
from components.race_record_extractor import RaceRecordExtractor

# メインスクリプトのインポート
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from improved_scraper import ImprovedRakutenScraper, ScraperConfig, TestConfig

# テスト用のHTMLサンプル
SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>テスト馬の詳細</title>
</head>
<body>
    <div class="horse-info">
        <h1>テスト馬</h1>
        <div class="age">3歳</div>
        <div class="sex">牡</div>
        <div class="sire">テスト父</div>
        <div class="dam">テスト母</div>
        <div class="damsire">テスト母父</div>
        <a href="https://example.com/horse/123">JBIS</a>
    </div>
    <div class="seller">テスト牧場</div>
    <div class="comment">テストコメント</div>
    <div class="prize">1,000万円</div>
    <div class="price">
        <span class="sold-price">5,000</span>万円
        <span class="starting-price">3,000</span>万円
    </div>
</body>
</html>
"""

class TestImprovedRakutenScraper(unittest.TestCase):
    """ImprovedRakutenScraperの統合テストクラス"""
    
    def setUp(self):
        """テストの前処理"""
        # モックロガーを作成
        self.mock_logger = MagicMock()
        
        # 各抽出コンポーネントのモックを作成
        self.mock_horse_info_extractor = MagicMock(spec=HorseInfoExtractor)
        self.mock_seller_info_extractor = MagicMock(spec=SellerInfoExtractor)
        self.mock_comment_extractor = MagicMock(spec=CommentExtractor)
        self.mock_prize_info_extractor = MagicMock(spec=PrizeInfoExtractor)
        self.mock_price_info_extractor = MagicMock(spec=PriceInfoExtractor)
        self.mock_race_record_extractor = MagicMock(spec=RaceRecordExtractor)
        
        # モックの戻り値を設定
        self.mock_horse_info_extractor.extract.return_value = ({
            'name': 'テスト馬',
            'age': 3,
            'sex': '牡',
            'sire': 'テスト父',
            'dam': 'テスト母',
            'damsire': 'テスト母父',
            'jbis_url': 'https://example.com/horse/123'
        }, True)
        
        self.mock_seller_info_extractor.extract.return_value = ({
            'seller': 'テスト牧場'
        }, True)
        
        self.mock_comment_extractor.extract.return_value = ({
            'comment': 'テストコメント'
        }, True)
        
        self.mock_prize_info_extractor.extract.return_value = ({
            'prize_money': 1000
        }, True)
        
        self.mock_price_info_extractor.extract.return_value = ({
            'sold_price': 5000,
            'starting_price': 3000,
            'is_unsold': False
        }, True)
        
        # テスト用の設定
        self.test_config = TestConfig(
            use_cache=False,
            cache_dir='test_cache',
            timeout=10
        )
        
        # モックのパッチを作成
        self.patchers = [
            patch('improved_scraper.HorseInfoExtractor', return_value=self.mock_horse_info_extractor),
            patch('improved_scraper.SellerInfoExtractor', return_value=self.mock_seller_info_extractor),
            patch('improved_scraper.CommentExtractor', return_value=self.mock_comment_extractor),
            patch('improved_scraper.PrizeInfoExtractor', return_value=self.mock_prize_info_extractor),
            patch('improved_scraper.PriceInfoExtractor', return_value=self.mock_price_info_extractor),
            patch('improved_scraper.RaceRecordExtractor', return_value=self.mock_race_record_extractor),
            patch('improved_scraper.logging.getLogger', return_value=self.mock_logger),
            patch('improved_scraper.Path.mkdir'),  # ディレクトリ作成をモック
            patch('improved_scraper.Path.exists', return_value=False)  # ファイル存在チェックをモック
        ]
        
        # パッチを適用
        for patcher in self.patchers:
            patcher.start()
        
        # テスト用のスクレイパーインスタンスを作成
        self.scraper = ImprovedRakutenScraper(self.test_config)
    
    def tearDown(self):
        """テストの後処理"""
        # パッチを元に戻す
        for patcher in self.patchers:
            patcher.stop()
    
    def test_initialization(self):
        """初期化のテスト"""
        # デフォルトの設定が正しく適用されていることを確認
        self.assertEqual(self.scraper.base_url, "https://auction.keiba.rakuten.co.jp/")
        self.assertEqual(self.scraper.max_workers, 1)  # TestConfigのデフォルト値
        self.assertFalse(self.scraper.use_cache)  # デフォルトで無効化
        
        # 各抽出コンポーネントが正しく初期化されていることを確認
        self.assertIsNotNone(self.scraper.horse_info_extractor)
        self.assertIsNotNone(self.scraper.seller_info_extractor)
        self.assertIsNotNone(self.scraper.comment_extractor)
        self.assertIsNotNone(self.scraper.prize_info_extractor)
        self.assertIsNotNone(self.scraper.price_info_extractor)
        self.assertIsNotNone(self.scraper.race_record_extractor)
    
    def test_extract_horse_info_success(self):
        """馬情報の抽出成功テスト"""
        # テスト用のHTML要素を作成
        soup = BeautifulSoup(SAMPLE_HTML, 'html.parser')
        mock_horse_element = soup.find('div', class_='horse-info')
        
        # メソッドを実行
        result = self.scraper._extract_horse_info(mock_horse_element, 1, 10)
        
        # 期待される結果を検証
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'テスト馬')
        self.assertEqual(result['seller'], 'テスト牧場')
        self.assertEqual(result['comment'], 'テストコメント')
        self.assertEqual(result['prize_money'], 1000)
        self.assertEqual(result['sold_price'], 5000)
        self.assertEqual(result['starting_price'], 3000)
        self.assertFalse(result['is_unsold'])
        
        # 各抽出メソッドが呼び出されたことを確認
        self.mock_horse_info_extractor.extract.assert_called_once()
        self.mock_seller_info_extractor.extract.assert_called_once()
        self.mock_comment_extractor.extract.assert_called_once()
        self.mock_prize_info_extractor.extract.assert_called_once()
        self.mock_price_info_extractor.extract.assert_called_once()
    
    def test_extract_horse_info_with_missing_required_fields(self):
        """必須フィールドが不足している場合のテスト"""
        # 必須フィールドが不足したモックを設定
        self.mock_horse_info_extractor.extract.return_value = ({
            'name': 'テスト馬',
            # age, sex が不足
        }, False)
        
        # テスト用のHTML要素を作成
        soup = BeautifulSoup(SAMPLE_HTML, 'html.parser')
        mock_horse_element = soup.find('div', class_='horse-info')
        
        # メソッドを実行
        result = self.scraper._extract_horse_info(mock_horse_element, 1, 10)
        
        # 結果がNoneであることを確認
        self.assertIsNone(result)
        
        # エラーログが記録されたことを確認
        self.mock_logger.error.assert_called()
    
    def test_extract_horse_info_with_missing_optional_fields(self):
        """オプションフィールドが不足している場合のテスト"""
        # オプションフィールドが不足したモックを設定
        self.mock_comment_extractor.extract.return_value = ({}, False)
        self.mock_prize_info_extractor.extract.return_value = ({}, False)
        
        # テスト用のHTML要素を作成
        soup = BeautifulSoup(SAMPLE_HTML, 'html.parser')
        mock_horse_element = soup.find('div', class_='horse-info')
        
        # メソッドを実行
        result = self.scraper._extract_horse_info(mock_horse_element, 1, 10)
        
        # 結果がNoneでないことを確認（必須フィールドは揃っているため）
        self.assertIsNotNone(result)
        
        # オプションフィールドが存在しないことを確認
        self.assertNotIn('comment', result)
        self.assertNotIn('prize_money', result)
        
        # デバッグログが記録されたことを確認
        self.mock_logger.debug.assert_any_call('コメントの抽出に失敗しました')
        self.mock_logger.debug.assert_any_call('賞金情報の抽出に失敗しました')
    
    def test_extract_horse_info_with_exception(self):
        # テスト用のHTMLを作成
        html = '<div class="horse-card"></div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result = self.scraper._extract_horse_info(soup)
        
        # 検証: 必須フィールドが不足している場合はNoneが返される
        self.assertIsNone(result)
        self.mock_logger.warning.assert_called_with(
            '必須フィールドが不足しています: %s', ['sex', 'age']
        )
    
    def test_extract_horse_info_exception_handling(self):
        """例外が発生した場合のテスト"""
        # 例外を発生させる
        self.mock_horse_info_extractor.extract.side_effect = Exception('Test error')
        
        # テスト用のHTMLを作成
        html = '<div class="horse-card"></div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result = self.scraper._extract_horse_info(soup)
        
        # 検証: 例外が発生した場合はNoneが返される
        self.assertIsNone(result)
        self.mock_logger.error.assert_called_with(
            '馬情報の抽出中にエラーが発生しました', exc_info=True
        )

if __name__ == '__main__':
    unittest.main()
