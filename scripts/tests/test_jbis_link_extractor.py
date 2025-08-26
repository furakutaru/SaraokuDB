"""JBISリンク抽出のテスト"""
import unittest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
from scripts.components.jbis_link_extractor import JbisLinkExtractor

class TestJbisLinkExtractor(unittest.TestCase):
    """JbisLinkExtractorのテストクラス"""
    
    def setUp(self):
        """テストの前処理"""
        self.extractor = JbisLinkExtractor()
    
    def test_extract_from_list_page(self):
        """リストページからのJBISリンク抽出テスト"""
        # テスト用のHTML（リストページ）
        html = '''
        <table style="margin-bottom:5px;" cellspacing="0" cellpadding="5" border="0" height="34" width="210">
            <tbody>
                <tr>
                    <td style="background:url(/img/common/list_btm_data.gif) no-repeat" valign="top">
                        <b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                            <a style="color:#fff;margin-left:5px;" href="https://www.jbis.or.jp/horse/0001318364/record/">
                                <font color="#FFFFFF" size="-1">競走成績を検索</font>
                            </a>
                        </b>
                    </td>
                </tr>
            </tbody>
        </table>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result = self.extractor.extract(soup)
        
        # 検証
        self.assertIn('jbis_url', result)
        # /record/ が削除されていることを確認
        self.assertEqual(result['jbis_url'], 'https://www.jbis.or.jp/horse/0001318364/')
    
    def test_extract_from_detail_page(self):
        """詳細ページからのJBISリンク抽出テスト"""
        # テスト用のHTML（詳細ページ）
        html = '''
        <div class="horse-link">
            <a href="https://www.jbis.or.jp/horse/0001318364/pedigree/">
                <span>血統情報を見る</span>
            </a>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result = self.extractor.extract(soup)
        
        # 検証
        self.assertIn('jbis_url', result)
        # /pedigree/ が削除されていることを確認
        self.assertEqual(result['jbis_url'], 'https://www.jbis.or.jp/horse/0001318364/')
    
    def test_extract_relative_url(self):
        """相対URLからのJBISリンク抽出テスト"""
        # テスト用のHTML（相対URL）
        html = '''
        <a href="/horse/0001318364/record/">競走成績</a>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        base_url = 'https://www.jbis.or.jp'
        
        # テスト実行
        result = self.extractor.extract(soup, base_url=base_url)
        
        # 検証
        self.assertIn('jbis_url', result)
        # ベースURLと結合され、/record/ が削除されていることを確認
        self.assertEqual(result['jbis_url'], 'https://www.jbis.or.jp/horse/0001318364/')
    
    def test_extract_no_link(self):
        """JBISリンクが存在しない場合のテスト"""
        # JBISリンクを含まないHTML
        html = '''
        <div>
            <a href="/other/page">他のページ</a>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result = self.extractor.extract(soup)
        
        # 検証
        self.assertIn('jbis_url', result)
        self.assertEqual(result['jbis_url'], '')
    
    def test_extract_multiple_links(self):
        """複数のJBISリンクがある場合のテスト（最初の有効なリンクを返す）"""
        # 複数のJBISリンクを含むHTML
        html = '''
        <div>
            <a href="https://www.jbis.or.jp/horse/0001111111/pedigree/">血統情報1</a>
            <a href="https://www.jbis.or.jp/horse/0001318364/record/">競走成績</a>
            <a href="https://www.jbis.or.jp/horse/0002222222/pedigree/">血統情報2</a>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result = self.extractor.extract(soup)
        
        # 検証（最初の有効なリンクが返される）
        self.assertIn('jbis_url', result)
        self.assertEqual(result['jbis_url'], 'https://www.jbis.or.jp/horse/0001111111/')


if __name__ == '__main__':
    unittest.main()
