"""
馬名抽出機能のテスト
"""
import pytest
from bs4 import BeautifulSoup
from scripts.improved_scraper import ImprovedRakutenScraper

class TestHorseNameExtraction:
    """馬名抽出機能のテストクラス"""
    
    @pytest.fixture
    def scraper(self):
        """テスト用のスクレイパーインスタンスを作成"""
        return ImprovedRakutenScraper(test_mode=True)
    
    def test_extract_horse_name_basic(self, scraper):
        """基本的な馬名の抽出をテスト"""
        html = '''
        <div class="auctionTableCard__name">
            サクラバクシンオー
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        name_elem = soup.select_one('.auctionTableCard__name')
        
        name = scraper._clean_horse_name(name_elem)
        assert name == 'サクラバクシンオー'
    
    def test_extract_horse_name_with_ellipsis(self, scraper):
        """省略記号を含む馬名の抽出をテスト"""
        html = '''
        <div class="auctionTableCard__name" title="サクラバクシンオー">
            サクラバク...
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        name_elem = soup.select_one('.auctionTableCard__name')
        
        name = scraper._clean_horse_name(name_elem)
        assert name == 'サクラバクシンオー'
    
    def test_extract_horse_name_with_extra_text(self, scraper):
        """余分なテキストを含む馬名の抽出をテスト"""
        html = '''
        <div class="auctionTableCard__name">
            サクラバクシンオー 販売申込者: テスト牧場
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        name_elem = soup.select_one('.auctionTableCard__name')
        
        name = scraper._clean_horse_name(name_elem)
        assert name == 'サクラバクシンオー'
    
    def test_extract_horse_name_with_price(self, scraper):
        """金額表記を含む馬名の抽出をテスト"""
        html = '''
        <div class="auctionTableCard__name">
            サクラバクシンオー 1,234万円
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        name_elem = soup.select_one('.auctionTableCard__name')
        
        name = scraper._clean_horse_name(name_elem)
        assert name == 'サクラバクシンオー'
    
    def test_extract_horse_name_with_special_chars(self, scraper):
        """特殊文字を含む馬名の抽出をテスト"""
        html = '''
        <div class="auctionTableCard__name">
            ***サクラバクシンオー***
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        name_elem = soup.select_one('.auctionTableCard__name')
        
        name = scraper._clean_horse_name(name_elem)
        assert name == 'サクラバクシンオー'

if __name__ == '__main__':
    pytest.main()
