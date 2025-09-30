"""
ImageExtractor のテストモジュール
"""
import pytest
from bs4 import BeautifulSoup
from components.image_extractor import ImageExtractor

def create_test_soup(html_content):
    """HTML文字列からBeautifulSoupオブジェクトを作成するヘルパー関数"""
    return BeautifulSoup(html_content, 'html.parser')

class TestImageExtractor:
    """ImageExtractor のテストクラス"""
    
    def test_extract_with_valid_image(self):
        """有効な画像URLが存在する場合のテスト"""
        html = """
        <div class="horseImage">
            <img class="photo" src="https://example.com/horse1.jpg" alt="テスト馬">
        </div>
        """
        extractor = ImageExtractor()
        result = extractor.extract(html)
        
        assert result == "https://example.com/horse1.jpg"
    
    def test_extract_without_image(self):
        """画像要素が存在しない場合のテスト"""
        html = '<div class="horseInfo">馬の情報</div>'
        extractor = ImageExtractor()
        result = extractor.extract(html)
        
        assert result is None
    
    def test_extract_image_without_src(self):
        """画像要素はあるがsrc属性がない場合のテスト"""
        html = '<img class="photo" alt="テスト馬">'
        extractor = ImageExtractor()
        result = extractor.extract(html)
        
        assert result is None
    
    def test_extract_with_empty_html(self):
        """空のHTMLが渡された場合のテスト"""
        html = ""
        extractor = ImageExtractor()
        result = extractor.extract(html)
        
        assert result is None
