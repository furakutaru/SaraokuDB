"""馬情報抽出のテスト"""
import unittest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
import sys
import os
import re

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scripts.components.horse_info_extractor import HorseInfoExtractor

class TestHorseInfoExtractor(unittest.TestCase):
    """HorseInfoExtractorのテストクラス"""
    
    def setUp(self):
        """テストの前処理"""
        self.logger = MagicMock()
        self.extractor = HorseInfoExtractor(logger=self.logger)
    
    def test_extract_horse_info_complete(self):
        """馬情報の抽出テスト（完全な情報）"""
        # テスト用のHTMLを作成
        html = '''
        <div class="horse-card">
            <div class="horse-name">サラブレッド</div>
            <div class="horse-info">牡3</div>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        horse_info, missing_fields = self.extractor.extract(soup)
        
        # 検証
        self.assertEqual(horse_info['name'], 'サラブレッド')
        self.assertEqual(horse_info['sex'], '牡')
        self.assertEqual(horse_info['age'], 3)
        self.assertEqual(len(missing_fields), 0)
    
    def test_extract_horse_info_missing_fields(self):
        """必須フィールドが不足している場合のテスト"""
        # テスト用のHTML（性別・年齢なし）
        html = '''
        <div class="horse-card">
            <div class="horse-name">サラブレッド</div>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        horse_info, missing_fields = self.extractor.extract(soup)
        
        # 検証
        self.assertEqual(horse_info['name'], 'サラブレッド')
        self.assertIn('sex', missing_fields)
        self.assertIn('age', missing_fields)
        self.logger.warning.assert_called()
        
    def test_extract_horse_info_invalid_html(self):
        """不正なHTMLが渡された場合のテスト"""
        # 不正なHTML（Noneを渡す）
        horse_info, missing_fields = self.extractor.extract(None)
        
        # 検証
        self.assertEqual(horse_info, {})
        self.assertEqual(len(missing_fields), 3)  # name, sex, age
        self.logger.error.assert_called()
    
    def test_extract_horse_info_edge_cases(self):
        """エッジケースのテスト"""
        test_cases = [
            {
                'name': '年齢が境界値',
                'html': '''
                <div class="horse-card">
                    <div class="horse-name">テスト馬1</div>
                    <div class="horse-info">牡1</div>
                </div>
                ''',
                'expected': {'name': 'テスト馬1', 'sex': '牡', 'age': 1},
                'missing': []
            },
            {
                'name': '特殊文字を含む名前',
                'html': '''
                <div class="horse-card">
                    <div class="horse-name">テスト★馬</div>
                    <div class="horse-info">牝5</div>
                </div>
                ''',
                'expected': {'name': 'テスト★馬', 'sex': '牝', 'age': 5},
                'missing': []
            },
            {
                'name': '年齢の表記ゆれ',
                'html': '''
                <div class="horse-card">
                    <div class="horse-name">テスト馬3</div>
                    <div class="horse-info">セ2歳</div>
                </div>
                ''',
                'expected': {'name': 'テスト馬3', 'sex': 'セ', 'age': 2},
                'missing': []
            }
        ]
        
        for case in test_cases:
            with self.subTest(case['name']):
                soup = BeautifulSoup(case['html'], 'html.parser')
                result, missing = self.extractor.extract(soup)
                
                for key, value in case['expected'].items():
                    self.assertEqual(result.get(key), value, 
                                  f"{case['name']} - {key}の検証に失敗: 期待値={value}, 実際の値={result.get(key)}")
                
                self.assertEqual(len(missing), len(case['missing']), 
                               f"{case['name']} - 不足フィールド数が一致しません")
    
    def test_extract_horse_info_with_extra_fields(self):
        """追加フィールドを含む場合のテスト"""
        html = '''
        <div class="horse-card">
            <div class="horse-name">テスト馬</div>
            <div class="horse-info">牡3</div>
            <div class="extra-info">追加情報</div>
            <div class="sire-name">父馬名</div>
            <div class="dam">母馬名</div>
            <div class="damsire">母父名</div>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        horse_info, missing_fields = self.extractor.extract(soup)
        
        # 検証
        self.assertEqual(horse_info['name'], 'テスト馬')
        self.assertEqual(horse_info['sex'], '牡')
        self.assertEqual(horse_info['age'], 3)
        self.assertEqual(horse_info['sire'], '父馬名')
        self.assertEqual(horse_info['dam'], '母馬名')
        self.assertEqual(horse_info['damsire'], '母父名')
        self.assertEqual(len(missing_fields), 0)
    
    def test_clean_horse_name(self):
        """馬名のクリーンアップテスト"""
        test_cases = [
            ('サラブレッド', 'サラブレッド'),
            ('サラブレッド 登録抹消', 'サラブレッド'),
            ('サラブレッド※', 'サラブレッド'),
            ('サラブレッド 新馬', 'サラブレッド'),
            (' サラブレッド ', 'サラブレッド'),  # スペースはトリムする
            ('', '')
        ]
        
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = self.extractor._clean_horse_name(input_name)
                self.assertEqual(result, expected)
    
    def test_extract_sex_and_age(self):
        """性別と年齢の抽出テスト"""
        test_cases = [
            ('牡3', {'sex': '牡', 'age': 3}),
            ('牝4', {'sex': '牝', 'age': 4}),
            ('セ5', {'sex': 'セ', 'age': 5}),
            ('牡', {'sex': '牡'}),
            ('3', {'sex': '3'}),  # 先頭が数字でない場合、最初の文字は性別として扱われる
            ('', {})
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                # テスト用のHTMLを作成
                html = f'<div class="horse-info">{input_text}</div>'
                soup = BeautifulSoup(html, 'html.parser')
                result = self.extractor._extract_sex_and_age(soup)
                self.assertEqual(result, expected)
    
    def test_extract_exception_handling(self):
        """例外発生時のテスト"""
        # 例外を発生させるためのモック
        with patch.object(HorseInfoExtractor, '_extract_name', side_effect=Exception('Test error')):
            html = '''
            <div class="horse-card">
                <div class="horse-name">サラブレッド</div>
                <div class="horse-info">牡3</div>
            </div>
            '''
            soup = BeautifulSoup(html, 'html.parser')
            result, missing_fields = self.extractor.extract(soup)
            
            # 検証
            self.assertEqual(result, {})
            self.assertEqual(len(missing_fields), 3)  # name, sex, age
            self.logger.error.assert_called()

if __name__ == '__main__':
    unittest.main()
