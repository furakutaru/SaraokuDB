"""
CurrentPrizeExtractor のテストモジュール
"""
import pytest
from bs4 import BeautifulSoup
from components.prize_money.current_prize_extractor import CurrentPrizeExtractor

def create_test_soup(html_content):
    """HTML文字列からBeautifulSoupオブジェクトを作成するヘルパー関数"""
    return BeautifulSoup(html_content, 'html.parser')

class TestCurrentPrizeExtractor:
    """CurrentPrizeExtractor のテストクラス"""
    
    def test_extract_with_valid_prize(self):
        """有効な賞金情報が存在する場合のテスト"""
        html = """
        <div class="prize-info">
            <span class="current-prize">5,678.9万円</span>
        </div>
        """
        extractor = CurrentPrizeExtractor()
        result = extractor.extract(html, "テスト馬")
        
        assert result['current_prize'] == 5678.9
        assert result['is_breeding_mare'] is False
    
    def test_extract_breeding_mare(self):
        """繁殖牝馬の場合のテスト"""
        html = """
        <div class="prize-info">
            繁殖牝馬のため賞金情報はありません
        </div>
        """
        extractor = CurrentPrizeExtractor()
        result = extractor.extract(html, "繁殖牝馬")
        
        assert result['current_prize'] is None
        assert result['is_breeding_mare'] is True
    
    def test_extract_without_prize_section(self):
        """賞金情報セクションが存在しない場合のテスト"""
        html = '<div class="other-section">テスト</div>'
        extractor = CurrentPrizeExtractor()
        result = extractor.extract(html, "テスト馬")
        
        assert result['current_prize'] is None
        assert result['is_breeding_mare'] is False
    
    def test_extract_without_prize_element(self):
        """賞金要素が存在しない場合のテスト"""
        html = """
        <div class="prize-info">
            <span class="other-class">テスト</span>
        </div>
        """
        extractor = CurrentPrizeExtractor()
        result = extractor.extract(html, "テスト馬")
        
        assert result['current_prize'] is None
        assert result['is_breeding_mare'] is False
    
    def test_extract_with_invalid_prize_format(self):
        """不正な賞金フォーマットの場合のテスト"""
        html = """
        <div class="prize-info">
            <span class="current-prize">不正な金額</span>
        </div>
        """
        extractor = CurrentPrizeExtractor()
        result = extractor.extract(html, "テスト馬")
        
        assert result['current_prize'] is None
        assert result['is_breeding_mare'] is False
