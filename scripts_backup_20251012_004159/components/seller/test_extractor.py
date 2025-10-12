"""
SellerExtractorのテスト
"""
import unittest
from ..seller.extractor import SellerExtractor

class TestSellerExtractor(unittest.TestCase):
    """SellerExtractorのテストケース"""
    
    def setUp(self):
        self.extractor = SellerExtractor()

    def test_extract_seller(self):
        """販売者情報抽出のテスト"""
        pass

if __name__ == '__main__':
    unittest.main()
