"""
BasePrizeExtractor のテストモジュール
"""
import pytest
from bs4 import BeautifulSoup
from components.prize_money.base_prize_extractor import BasePrizeExtractor

# テスト用の具象クラス
class ConcretePrizeExtractor(BasePrizeExtractor):
    def extract(self, content: str, horse_name: str = '') -> dict:
        # テストでは使用しないが、抽象メソッドを実装する必要がある
        return {}

class TestBasePrizeExtractor:
    """BasePrizeExtractor のテストクラス"""
    
    def setup_method(self, method):
        self.extractor = ConcretePrizeExtractor()
    
    def test_extract_prize_value_with_comma(self):
        """カンマを含む賞金の抽出テスト"""
        result = self.extractor._extract_prize_value("1,234.5万円", "テスト馬")
        assert result == 1234.5
    
    def test_extract_prize_value_without_comma(self):
        """カンマを含まない賞金の抽出テスト"""
        result = self.extractor._extract_prize_value("1234.5万円", "テスト馬")
        assert result == 1234.5
    
    def test_extract_prize_value_integer(self):
        """整数値の賞金の抽出テスト"""
        result = self.extractor._extract_prize_value("1234万円", "テスト馬")
        assert result == 1234.0
    
    def test_extract_prize_value_invalid_format(self):
        """不正なフォーマットの賞金の抽出テスト"""
        result = self.extractor._extract_prize_value("不正な金額", "テスト馬")
        assert result is None
    
    def test_extract_prize_value_empty_string(self):
        """空文字列の賞金の抽出テスト"""
        result = self.extractor._extract_prize_value("", "テスト馬")
        assert result is None
    
    def test_extract_prize_value_none(self):
        """Noneの賞金の抽出テスト"""
        result = self.extractor._extract_prize_value(None, "テスト馬")
        assert result is None
