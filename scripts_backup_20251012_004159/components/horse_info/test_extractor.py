"""
HorseInfoExtractorのテスト
"""
import unittest
from ..horse_info.extractor import HorseInfoExtractor

class TestHorseInfoExtractor(unittest.TestCase):
    """HorseInfoExtractorのテストケース"""
    
    def setUp(self):
        self.extractor = HorseInfoExtractor()

    def test_extract_horse_info(self):
        """馬情報抽出のテスト"""
        pass

    def test_extract_pedigree(self):
        """血統情報抽出のテスト"""
        pass

if __name__ == '__main__':
    unittest.main()
