"""
AuctionInfoExtractorのテスト
"""
import unittest
from ..auction_info.extractor import AuctionInfoExtractor

class TestAuctionInfoExtractor(unittest.TestCase):
    """AuctionInfoExtractorのテストケース"""
    
    def setUp(self):
        self.extractor = AuctionInfoExtractor()

    def test_extract_auction_info(self):
        """オークション情報抽出のテスト"""
        pass

    def test_extract_lot_number(self):
        """ロット番号抽出のテスト"""
        pass

if __name__ == '__main__':
    unittest.main()
