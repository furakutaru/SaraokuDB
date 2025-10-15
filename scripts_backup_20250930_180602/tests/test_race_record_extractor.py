"""通算成績抽出のテスト"""
import unittest
from unittest.mock import MagicMock
from bs4 import BeautifulSoup
from scripts.components.race_record_extractor import RaceRecordExtractor

class TestRaceRecordExtractor(unittest.TestCase):
    """RaceRecordExtractorのテストクラス"""
    
    def setUp(self):
        """テストの前処理"""
        self.logger = MagicMock()
        self.extractor = RaceRecordExtractor(logger=self.logger)
    
    def test_extract_record_success(self):
        """通算成績の抽出テスト（成功ケース）"""
        # テスト用のHTMLを作成
        html = '''
        <table style="margin-bottom:10px;" cellspacing="0" cellpadding="0" border="0" height="112" width="100%">
            <tbody>
                <tr>
                    <td style="background:url(/img/common/list_name_bg-item.gif) no-repeat" align="right">
                        <table cellpadding="0" cellspacing="0" border="0" width="85%">
                            <tbody>
                                <tr>
                                    <td height="50">
                                        <b>ジークシュベルト　Sieg Schwert　　牡　　鹿毛　　2020年3月19日生　5歳</b>
                                    </td>
                                </tr>
                                <tr>
                                    <td height="50">
                                        <pre style="white-space: pre-wrap;word-wrap: break-word;">
                                            父：ファインニードル　母：レオソレイユ　母の父：オペラハウス
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
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result, success = self.extractor.extract(soup)
        
        # 検証
        self.assertTrue(success)
        self.assertIsNotNone(result)
        self.assertIn('record', result)
        self.assertEqual(result['record'], '21戦1勝［1-0-3-17］')
    
    def test_extract_record_no_record(self):
        """通算成績が存在しない場合のテスト"""
        # 通算成績を含まないHTML
        html = '''
        <div>
            <pre>父：ファインニードル　母：レオソレイユ　母の父：オペラハウス</pre>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result, success = self.extractor.extract(soup)
        
        # 検証
        self.assertFalse(success)
        self.assertIsNone(result)
        self.logger.debug.assert_called_with('通算成績のパターンが一致しませんでした')
    
    def test_extract_record_empty_pre(self):
        """空のpreタグがある場合のテスト"""
        # 空のpreタグを含むHTML
        html = '''
        <table>
            <tr>
                <td>
                    <pre style="white-space: pre-wrap;word-wrap: break-word;"></pre>
                </td>
            </tr>
        </table>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result, success = self.extractor.extract(soup)
        
        # 検証
        self.assertFalse(success)
        self.assertIsNone(result)
    
    def test_extract_record_multiple_matches(self):
        """複数のマッチがある場合のテスト（最初のマッチを返す）"""
        # 複数の通算成績を含むHTML
        html = '''
        <div>
            <pre>
                通算成績：10戦2勝［2-1-3-4］
                通算成績：5戦1勝［1-0-1-3］
            </pre>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result, success = self.extractor.extract(soup)
        
        # 検証
        self.assertTrue(success)
        self.assertIsNotNone(result)
        self.assertIn('record', result)
        self.assertEqual(result['record'], '10戦2勝［2-1-3-4］')


if __name__ == '__main__':
    unittest.main()
