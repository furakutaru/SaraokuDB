"""
AuctionPrizeExtractor のテストモジュール
"""
import pytest
from bs4 import BeautifulSoup
from components.prize_money.auction_prize_extractor import AuctionPrizeExtractor

def create_test_soup(html_content):
    """HTML文字列からBeautifulSoupオブジェクトを作成するヘルパー関数"""
    return BeautifulSoup(html_content, 'html.parser')

class TestAuctionPrizeExtractor:
    """AuctionPrizeExtractor のテストクラス"""
    
    def test_extract_with_valid_prize(self):
        """有効な賞金情報が存在する場合のテスト"""
        html = """
        <div class="auction-info">
            <span class="auction-prize">1,234.5万円</span>
        </div>
        """
        extractor = AuctionPrizeExtractor()
        result = extractor.extract(html, "テスト馬")
        
        assert result['auction_prize'] == 1234.5
    
    def test_extract_without_auction_section(self):
        """オークション情報セクションが存在しない場合のテスト"""
        html = '<div class="other-section">テスト</div>'
        extractor = AuctionPrizeExtractor()
        result = extractor.extract(html, "テスト馬")
        
        assert result['auction_prize'] is None
    
    def test_extract_without_prize_element(self):
        """賞金要素が存在しない場合のテスト"""
        html = """
        <div class="auction-info">
            <span class="other-class">テスト</span>
        </div>
        """
        extractor = AuctionPrizeExtractor()
        result = extractor.extract(html, "テスト馬")
        
        assert result['auction_prize'] is None
    
    def test_extract_with_invalid_prize_format(self):
        """不正な賞金フォーマットの場合のテスト"""
        html = """
        <div class="auction-info">
            <span class="auction-prize">不正な金額</span>
        </div>
        """
        extractor = AuctionPrizeExtractor()
        result = extractor.extract(html, "テスト馬")
        
        assert result['auction_prize'] is None
