import unittest
import logging
from bs4 import BeautifulSoup
from scripts.race_record_extractor import RaceRecordExtractor

# ログ設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestRaceRecordExtractor(unittest.TestCase):    
    def setUp(self):
        self.extractor = RaceRecordExtractor()
        
    def test_extract_race_record(self):
        # テスト用のHTMLを作成
        html_content = """
        <table cellpadding="0" cellspacing="0" border="0" width="85%">
            <tbody>
                <tr><td height="50"><b>テスト馬名　Test Horse　　牝　　鹿毛　　2023年2月8日生　2歳</b></td></tr>
                <tr><td height="50">
                    <pre style="white-space: pre-wrap;word-wrap: break-word;">
                        父：テストファーザー　母：テストマザー　母の父：テストグランドパ
                        通算成績：3戦0勝［0-0-0-3］　　　　最終出走馬体重：420kg
                        中央獲得賞金：0.0万円　　　地方獲得賞金：0.0万円
                    </pre>
                </td></tr>
            </tbody>
        </table>
        """
        
        # 抽出を実行
        logger.debug("Extracting race record...")
        result, success = self.extractor.extract(html_content)
        
        # 結果を検証
        logger.debug(f"Extraction result: success={success}, result={result}")
        self.assertTrue(success, "Extraction should be successful")
        self.assertIn('summary', result, "Result should contain 'summary' key")
        self.assertIn('races', result['summary'], "Summary should contain 'races' key")
        self.assertEqual(result['summary']['races'], 3, "Number of races should be 3")
        self.assertEqual(result['summary']['wins'], 0, "Number of wins should be 0")
        self.assertEqual(result['summary']['first'], 0, "Number of 1st places should be 0")
        self.assertEqual(result['summary']['second'], 0, "Number of 2nd places should be 0")
        self.assertEqual(result['summary']['third'], 0, "Number of 3rd places should be 0")
        self.assertEqual(result['summary']['other'], 3, "Number of other places should be 3")
        
    def test_extract_without_record(self):
        # 通算成績がない場合のテスト
        html_content = """
        <table cellpadding="0" cellspacing="0" border="0" width="85%">
            <tbody>
                <tr><td height="50"><b>テスト馬名　Test Horse　　牝　　鹿毛　　2023年2月8日生　2歳</b></td></tr>
                <tr><td height="50">
                    <pre style="white-space: pre-wrap;word-wrap: break-word;">
                        父：テストファーザー　母：テストマザー　母の父：テストグランドパ
                        中央獲得賞金：0.0万円　　　地方獲得賞金：0.0万円
                    </pre>
                </td></tr>
            </tbody>
        </table>
        """
        
        # 抽出を実行
        result, success = self.extractor.extract(html_content)
        
        # 結果を検証（空のサマリーが返る）
        self.assertTrue(success)
        self.assertEqual(result['summary'], {})
        self.assertEqual(result['races'], [])

if __name__ == '__main__':
    unittest.main()
