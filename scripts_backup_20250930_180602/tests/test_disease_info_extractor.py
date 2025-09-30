"""
DiseaseInfoExtractorのテストモジュール
"""
import unittest
import logging
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup

# テスト対象のモジュールをインポート
from components.disease_info_extractor import DiseaseInfoExtractor, HEALTH_KEYWORDS

class TestDiseaseInfoExtractor(unittest.TestCase):
    """DiseaseInfoExtractorのテストクラス"""
    
    def setUp(self):
        """テストの前処理"""
        # テスト用のロガーモックを作成
        self.logger = MagicMock(spec=logging.Logger)
        self.extractor = DiseaseInfoExtractor(logger=self.logger)
    
    def test_extract_no_comment(self):
        """コメントが空の場合のテスト"""
        result = self.extractor.extract("")
        self.assertEqual(result, {})
    
    def test_extract_no_diseases(self):
        """疾病情報がない場合のテスト"""
        comment = "この馬は健康で順調に成長しています。"
        result = self.extractor.extract(comment)
        self.assertEqual(result, {'diseases': [], 'has_health_issues': False})
    
    def test_extract_single_disease(self):
        """1つの疾病情報がある場合のテスト"""
        comment = "過去に骨折の経験がありますが、現在は完治しています。"
        result = self.extractor.extract(comment)
        self.assertEqual(result, {
            'diseases': ['骨折'],
            'has_health_issues': True
        })
    
    def test_extract_multiple_diseases(self):
        """複数の疾病情報がある場合のテスト"""
        comment = "過去に骨折と皮膚病の治療歴がありますが、現在は完治しています。"
        result = self.extractor.extract(comment)
        self.assertEqual(len(result['diseases']), 2)
        self.assertIn('骨折', result['diseases'])
        self.assertIn('皮膚病', result['diseases'])
        self.assertTrue(result['has_health_issues'])
    
    def test_extract_all_keywords(self):
        """全てのキーワードが含まれる場合のテスト"""
        comment = " ".join(HEALTH_KEYWORDS)
        result = self.extractor.extract(comment)
        self.assertEqual(len(result['diseases']), len(HEALTH_KEYWORDS))
        self.assertTrue(result['has_health_issues'])
    
    def test_extract_disease_tags(self):
        """後方互換性のためのextract_disease_tagsメソッドのテスト"""
        comment = "過去に骨折と皮膚病の治療歴があります。"
        result = self.extractor.extract_disease_tags(comment)
        self.assertCountEqual(result.split(','), ['骨折', '皮膚病'])
        
        # 重複するキーワードを含む場合のテスト
        comment = "骨折の治療歴があり、その後も骨折を繰り返しています。"
        result = self.extractor.extract_disease_tags(comment)
        self.assertEqual(result, "骨折")
        
        # 複数回出現するキーワードを含む場合のテスト
        comment = "骨折と皮膚病、骨折の治療歴があります。皮膚病も再発しています。"
        result = self.extractor.extract_disease_tags(comment)
        self.assertCountEqual(result.split(','), ['骨折', '皮膚病'])
    
    def test_extract_disease_tags_no_diseases(self):
        """疾病情報がない場合のextract_disease_tagsメソッドのテスト"""
        result = self.extractor.extract_disease_tags("健康です。")
        self.assertEqual(result, "")
        
        # 空文字列の場合のテスト
        result = self.extractor.extract_disease_tags("")
        self.assertEqual(result, "")

if __name__ == '__main__':
    unittest.main()
