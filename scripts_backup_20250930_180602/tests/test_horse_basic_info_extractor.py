"""
HorseBasicInfoExtractor のテストモジュール
"""
import logging
import pytest
from bs4 import BeautifulSoup
from components.horse_basic_info_extractor import HorseBasicInfoExtractor

def create_test_soup(html_content):
    """HTML文字列からBeautifulSoupオブジェクトを作成するヘルパー関数"""
    return BeautifulSoup(html_content, 'html.parser')

class TestHorseBasicInfoExtractor:
    """HorseBasicInfoExtractor のテストクラス"""
    
    def test_extract_with_valid_data(self):
        """有効なHTMLから正しく情報を抽出できることをテスト"""
        # テスト用のHTML
        html = """
        <div class="horseName">テスト馬名</div>
        <div class="ageSex">牡3歳</div>
        """
        soup = create_test_soup(html)
        
        # テスト実行
        result = HorseBasicInfoExtractor.extract(soup)
        
        # 結果の検証
        assert result['name'] == 'テスト馬名'
        assert result['sex'] == '牡'
        assert result['age'] == 3
    
    def test_extract_with_female_horse(self):
        """牝馬の情報を正しく抽出できることをテスト"""
        html = """
        <div class="horseName">テスト牝馬</div>
        <div class="ageSex">牝4歳</div>
        """
        soup = create_test_soup(html)
        
        result = HorseBasicInfoExtractor.extract(soup)
        
        assert result['name'] == 'テスト牝馬'
        assert result['sex'] == '牝'
        assert result['age'] == 4
    
    def test_extract_with_missing_name(self):
        """馬名が存在しない場合のテスト"""
        html = '<div class="ageSex">セ2歳</div>'
        soup = create_test_soup(html)
        
        result = HorseBasicInfoExtractor.extract(soup)
        
        assert result['name'] == ''  # 空文字列が返る
        assert result['sex'] == 'セ'
        assert result['age'] == 2
    
    def test_extract_with_missing_age_sex(self):
        """性別・年齢情報が存在しない場合のテスト"""
        html = '<div class="horseName">名前のみの馬</div>'
        soup = create_test_soup(html)
        
        result = HorseBasicInfoExtractor.extract(soup)
        
        assert result['name'] == '名前のみの馬'
        assert result['sex'] == ''  # 空文字列が返る
        assert result['age'] is None  # Noneが返る
    
    def test_extract_with_invalid_age(self, caplog):
        """不正な年齢が含まれる場合のテスト"""
        # 数字が含まれない年齢表現のテスト
        html1 = """
        <div class="horseName">年齢不正馬1</div>
        <div class="ageSex">牡あ歳</div>
        """
        # 数字が含まれるが、数値変換に失敗するテストケース
        # 実際の実装では、数字が含まれていれば正しく変換されるため、このケースは不要
        
        # ケース1: 数字が含まれない場合
        soup = create_test_soup(html1)
        with caplog.at_level(logging.WARNING):
            caplog.clear()
            result = HorseBasicInfoExtractor.extract(soup)
            
            # 数字が含まれない場合は警告は出さない（マッチしないだけ）
            assert len(caplog.records) == 0
        
        assert result['name'] == '年齢不正馬1'
        assert result['sex'] == '牡'
        assert result['age'] is None
    
    def test_extract_with_only_sex(self):
        """性別のみが含まれる場合のテスト"""
        html = '<div class="ageSex">牝</div>'
        soup = create_test_soup(html)
        
        result = HorseBasicInfoExtractor.extract(soup)
        
        assert result['sex'] == '牝'
        assert result['age'] is None
    
    def test_extract_with_only_age(self):
        """年齢のみが含まれる場合のテスト"""
        html = '<div class="ageSex">3歳</div>'
        soup = create_test_soup(html)
        
        result = HorseBasicInfoExtractor.extract(soup)
        
        assert result['sex'] == ''
        assert result['age'] == 3
    
    def test_extract_with_empty_input(self):
        """空のBeautifulSoupオブジェクトが渡された場合のテスト"""
        soup = create_test_soup("")
        
        result = HorseBasicInfoExtractor.extract(soup)
        
        assert result['name'] == ''
        assert result['sex'] == ''
        assert result['age'] is None
