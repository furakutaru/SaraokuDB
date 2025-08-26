"""
PedigreeExtractor のテストモジュール
"""

import unittest
from unittest.mock import MagicMock
from bs4 import BeautifulSoup
from components.extractors.pedigree_extractor import PedigreeExtractor

class TestPedigreeExtractor(unittest.TestCase):
    """PedigreeExtractor のテストクラス"""
    
    def setUp(self):
        """テストの前処理"""
        self.logger = MagicMock()
        self.extractor = PedigreeExtractor(logger=self.logger)
    
    def test_extract_from_text(self):
        """テキストからの血統情報抽出テスト"""
        test_cases = [
            (
                '父：リアルインパクト　母：ディオニージア　母の父：Tejano Run',
                {
                    'sire': 'リアルインパクト',
                    'dam': 'ディオニージア',
                    'damsire': 'Tejano Run'
                }
            ),
            (
                '父:キングカメハメハ 母: トーセンレーヴ 母の父: サンデーサイレンス',
                {
                    'sire': 'キングカメハメハ',
                    'dam': 'トーセンレーヴ',
                    'damsire': 'サンデーサイレンス'
                }
            ),
            (
                '父：ディープインパクト　母：ウインドインハーヘア',
                {
                    'sire': 'ディープインパクト',
                    'dam': 'ウインドインハーヘア',
                    'damsire': None
                }
            ),
            (
                '父：ロードカナロア　母：レッドディザイア　母の父：マンハッタンカフェ',
                {
                    'sire': 'ロードカナロア',
                    'dam': 'レッドディザイア',
                    'damsire': 'マンハッタンカフェ'
                }
            ),
            (
                '血統情報なし',
                {
                    'sire': None,
                    'dam': None,
                    'damsire': None
                }
            ),
            (
                '',
                {
                    'sire': None,
                    'dam': None,
                    'damsire': None
                }
            ),
            (
                None,
                {
                    'sire': None,
                    'dam': None,
                    'damsire': None
                }
            )
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.extractor.extract(input_text)
                self.assertEqual(result, expected)
    
    def test_extract_from_html(self):
        """HTML要素からの血統情報抽出テスト"""
        html = '''
        <div id="itemDetails">
            <table>
                <tr>
                    <td>
                        <table>
                            <tr>
                                <td><b>ステラマテュティナ　Stella Matutina　牝　青鹿毛　2022年2月22日生　3歳</b></td>
                            </tr>
                            <tr>
                                <td>
                                    <pre>父：リアルインパクト　母：ディオニージア　母の父：Tejano Run
通算成績：7戦0勝［0-0-1-6］　　　　最終出走馬体重：427kg
中央獲得賞金：296.0万円　　　地方獲得賞金：0.0万円</pre>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </div>
        '''
        
        expected = {
            'sire': 'リアルインパクト',
            'dam': 'ディオニージア',
            'damsire': 'Tejano Run'
        }
        
        soup = BeautifulSoup(html, 'html.parser')
        result = self.extractor.extract(soup)
        self.assertEqual(result, expected)
    
    def test_individual_extractors(self):
        """個別の抽出メソッドのテスト"""
        text = '父：キタサンブラック　母：ウインドインハーヘア　母の父：キングカメハメハ'
        
        self.assertEqual(self.extractor.extract_sire(text), 'キタサンブラック')
        self.assertEqual(self.extractor.extract_dam(text), 'ウインドインハーヘア')
        self.assertEqual(self.extractor.extract_damsire(text), 'キングカメハメハ')
    
    def test_edge_cases(self):
        """境界値・エッジケースのテスト"""
        # 空の入力
        self.assertEqual(
            self.extractor.extract(''),
            {'sire': None, 'dam': None, 'damsire': None}
        )
        
        # None入力
        self.assertEqual(
            self.extractor.extract(None),
            {'sire': None, 'dam': None, 'damsire': None}
        )
        
        # 父のみ
        self.assertEqual(
            self.extractor.extract('父：ディープインパクト'),
            {'sire': 'ディープインパクト', 'dam': None, 'damsire': None}
        )
        
        # 空のフィールド
        self.assertEqual(
            self.extractor.extract('父：  母：  母の父：'),
            {'sire': None, 'dam': None, 'damsire': None}
        )
        
        # 不正な形式
        self.assertEqual(
            self.extractor.extract('適当なテキスト'),
            {'sire': None, 'dam': None, 'damsire': None}
        )
        
        # 部分的な情報（父と母のみ）
        self.assertEqual(
            self.extractor.extract('父：キングカメハメハ 母：トーセンレーヴ'),
            {'sire': 'キングカメハメハ', 'dam': 'トーセンレーヴ', 'damsire': None}
        )

if __name__ == '__main__':
    unittest.main()
