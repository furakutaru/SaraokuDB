"""コメント抽出のテスト"""
import unittest
from unittest.mock import MagicMock
from bs4 import BeautifulSoup
from scripts.components.comment_extractor import CommentExtractor

class TestCommentExtractor(unittest.TestCase):
    """CommentExtractorのテストクラス"""
    
    def setUp(self):
        """テストの前処理"""
        self.logger = MagicMock()
        self.extractor = CommentExtractor(logger=self.logger)
    
    def test_extract_comment_success(self):
        """コメントの抽出テスト（成功ケース）"""
        # テスト用のHTMLを作成
        html = '''
        <table style="margin-bottom:10px;" bgcolor="#fff7bc" cellspacing="0" cellpadding="10" border="0" width="100%">
            <tbody>
                <tr>
                    <td>
                        <b>本馬について</b>
                        <hr style="margin-bottom:5px;" noshade="" size="1">
                        <pre style="white-space: pre-wrap;word-wrap: break-word;">
                            母レオソレイユは、現役時代に芝の短距離戦で1勝を挙げたスピードタイプの競走馬です。
                            繁殖牝馬としても優秀で、重賞2勝のレオアクティブや、JRAで3勝を挙げたレオフラッパーを輩出しています。
                        </pre>
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
        self.assertIn('comment', result)
        self.assertIn('母レオソレイユは、現役時代に芝の短距離戦で1勝を挙げたスピードタイプの競走馬です。', result['comment'])
    
    def test_extract_comment_no_comment(self):
        """コメントが存在しない場合のテスト"""
        # コメントを含まないHTML
        html = '<div><p>コメントはありません</p></div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result, success = self.extractor.extract(soup)
        
        # 検証
        self.assertFalse(success)
        self.assertIsNone(result)
        self.logger.debug.assert_called_with('コメントが見つかりませんでした')
    
    def test_extract_comment_empty_comment(self):
        """空のコメント要素がある場合のテスト"""
        # 空のコメントを含むHTML
        html = '''
        <div class="comment">
            <pre style="white-space: pre-wrap;word-wrap: break-word;"></pre>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result, success = self.extractor.extract(soup)
        
        # 検証
        self.assertFalse(success)
        self.assertIsNone(result)
        self.logger.debug.assert_called_with('コメントが見つかりませんでした')
    
    def test_extract_comment_with_html_tags(self):
        """HTMLタグを含むコメントのテスト"""
        # HTMLタグを含むコメント
        html = '''
        <table style="margin-bottom:10px;" bgcolor="#fff7bc" cellspacing="0" cellpadding="10" border="0" width="100%">
            <tbody>
                <tr>
                    <td>
                        <b>本馬について</b>
                        <hr style="margin-bottom:5px;" noshade="" size="1">
                        <pre style="white-space: pre-wrap;word-wrap: break-word;">
                            この馬は<strong>非常に</strong>速いです。
                            レースで<font color="red">1位</font>を取るでしょう。
                        </pre>
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
        self.assertIn('comment', result)
        # 改行を含むテキストを検証
        self.assertIn('この馬は\n非常に\n速いです。', result['comment'])
        self.assertIn('レースで\n1位\nを取るでしょう。', result['comment'])
        # HTMLタグが除去されていることを確認
        self.assertNotIn('<strong>', result['comment'])
        self.assertNotIn('</strong>', result['comment'])
        self.assertNotIn('<font', result['comment'])
        self.assertNotIn('</font>', result['comment'])


if __name__ == '__main__':
    unittest.main()
