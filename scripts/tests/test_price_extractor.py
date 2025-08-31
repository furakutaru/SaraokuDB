"""
PriceInfoExtractorのテスト
"""
import os
import unittest
from bs4 import BeautifulSoup
from components.price_info_extractor import PriceInfoExtractor

# テスト用のHTMLファイルのパス
TEST_HTML_PATH = os.path.join(os.path.dirname(__file__), 'test_data/price_test.html')

class TestPriceInfoExtractor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """テストクラスのセットアップ"""
        cls.extractor = PriceInfoExtractor()
        
        # テスト用のHTMLを読み込む
        with open(TEST_HTML_PATH, 'r', encoding='utf-8') as f:
            cls.test_html = f.read()
        
        cls.soup = BeautifulSoup(cls.test_html, 'html.parser')
    
    def test_extract_price_normal(self):
        """通常の価格表示から正しく価格を抽出できるかテスト"""
        # テスト用のHTMLから価格要素を取得
        price_div = self.soup.select_one('div.price')
        self.assertIsNotNone(price_div, "価格要素が見つかりません")
        
        # 価格を抽出
        result, success = self.extractor.extract(price_div)
        
        # 結果を検証
        self.assertTrue(success, "価格の抽出に失敗しました")
        self.assertEqual(result['sold_price'], 830000, "価格が正しく抽出されていません")
        self.assertFalse(result['is_unsold'], "主取りフラグが正しく設定されていません")
    
    def test_extract_unsold(self):
        """主取りの表示を正しく検出できるかテスト"""
        # テスト用のHTMLから主取り要素を取得
        unsold_div = self.soup.select_one('div.unsold')
        self.assertIsNotNone(unsold_div, "主取り要素が見つかりません")
        
        # 価格を抽出
        result, success = self.extractor.extract(unsold_div)
        
        # 結果を検証
        self.assertTrue(success, "主取りの検出に失敗しました")
        self.assertTrue(result['is_unsold'], "主取りフラグが正しく設定されていません")
        self.assertNotIn('sold_price', result, "主取りの場合はsold_priceが存在するべきではありません")
    
    def test_extract_invalid_element(self):
        """無効な要素を渡した場合のテスト"""
        # 無効な要素を渡す
        result, success = self.extractor.extract(None)
        
        # 結果を検証
        self.assertFalse(success, "無効な要素で成功したと返しています")
        self.assertIsNone(result, "無効な要素の場合はNoneを返すべきです")

if __name__ == '__main__':
    unittest.main()
