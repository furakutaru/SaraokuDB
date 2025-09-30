"""
HorseWeightExtractorのテストモジュール
"""
import unittest
import logging
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup

# テスト対象のモジュールをインポート
from components.horse_weight_extractor import HorseWeightExtractor

class TestHorseWeightExtractor(unittest.TestCase):
    """HorseWeightExtractorのテストクラス"""
    
    def setUp(self):
        """テストの前処理"""
        # テスト用のロガーモックを作成
        self.logger = MagicMock(spec=logging.Logger)
        self.extractor = HorseWeightExtractor(logger=self.logger)
    
    def test_extract_with_weight(self):
        """馬体重が含まれるHTMLからの抽出テスト"""
        html = """
        <table style="margin-bottom:10px;" cellspacing="0" cellpadding="0" border="0" height="112" width="100%">
            <tbody>
                <tr>
                    <td style="background:url(/img/common/list_name_bg-item.gif) no-repeat" align="right">
                        <table cellpadding="0" cellspacing="0" border="0" width="85%">
                            <tbody>
                                <tr><td height="50"><b>テスト馬名</b></td></tr>
                                <tr>
                                    <td height="50">
                                        <pre style="white-space: pre-wrap;word-wrap: break-word;">
                                            父：テスト父　母：テスト母　母の父：テスト母父
                                            通算成績：21戦1勝［1-0-3-17］　　　　最終出走馬体重：464kg
                                            中央獲得賞金：540.0万円　　　地方獲得賞金：75.6万円
                                        </pre>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </td>
                </tr>
            </tbody>
        </table>
        """
        result = self.extractor.extract(html)
        self.assertEqual(result, {'weight_kg': 464})
    
    def test_extract_without_weight(self):
        """馬体重が含まれないHTMLからの抽出テスト"""
        html = """
        <table style="margin-bottom:10px;" cellspacing="0" cellpadding="0" border="0" height="112" width="100%">
            <tbody>
                <tr>
                    <td style="background:url(/img/common/list_name_bg-item.gif) no-repeat" align="right">
                        <table cellpadding="0" cellspacing="0" border="0" width="85%">
                            <tbody>
                                <tr><td height="50"><b>テスト馬名</b></td></tr>
                                <tr>
                                    <td height="50">
                                        <pre style="white-space: pre-wrap;word-wrap: break-word;">
                                            父：テスト父　母：テスト母　母の父：テスト母父
                                            通算成績：21戦1勝［1-0-3-17］
                                            中央獲得賞金：540.0万円　　　地方獲得賞金：75.6万円
                                        </pre>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </td>
                </tr>
            </tbody>
        </table>
        """
        result = self.extractor.extract(html)
        self.assertEqual(result, {'weight_kg': None})
    
    def test_extract_with_bs4_object(self):
        """BeautifulSoupオブジェクトを直接渡した場合のテスト"""
        html = """
        <div>通算成績：21戦1勝［1-0-3-17］　　　　最終出走馬体重：464kg</div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        result = self.extractor.extract(soup)
        self.assertEqual(result, {'weight_kg': 464})
    
    def test_extract_with_invalid_input(self):
        """無効な入力に対するテスト"""
        # Noneを渡した場合
        result = self.extractor.extract(None)
        self.assertEqual(result, {'weight_kg': None})
        
        # 空の文字列を渡した場合
        result = self.extractor.extract("")
        self.assertEqual(result, {'weight_kg': None})
        
        # 数値以外を渡した場合
        result = self.extractor.extract("最終出走馬体重：abc kg")
        self.assertEqual(result, {'weight_kg': None})

if __name__ == '__main__':
    unittest.main()
