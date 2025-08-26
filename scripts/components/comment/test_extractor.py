"""
CommentExtractorのテスト
"""
import unittest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
import sys
import os

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from components.comment_extractor import CommentExtractor

class TestCommentExtractor(unittest.TestCase):
    """CommentExtractorのテストケース"""
    
    def setUp(self):
        self.logger = MagicMock()
        self.extractor = CommentExtractor(logger=self.logger)
    
    def test_extract_comment_success(self):
        """コメント抽出のテスト（成功ケース）"""
        # テスト用のHTMLを作成
        html = '''
        <div class="comment">
            素晴らしい馬体の持ち主です。
            走りも軽やかで、今後の活躍が期待できます。
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result, success = self.extractor.extract(soup)
        
        # 検証
        self.assertTrue(success)
        self.assertIn('comment', result)
        self.assertIn('素晴らしい馬体の持ち主です', result['comment'])
        self.logger.debug.assert_called_with('コメントを抽出しました: 素晴らしい馬体の持ち主です。 走りも軽やかで、今後の活躍が期待できます。...')
    
    def test_extract_comment_alternative_selector(self):
        """代替セレクタを使用したコメント抽出のテスト"""
        # テスト用のHTMLを作成（別のクラス名を使用）
        html = '''
        <p class="description">
            気性は穏やかで、調教も順調にこなしています。
        </p>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result, success = self.extractor.extract(soup)
        
        # 検証
        self.assertTrue(success)
        self.assertIn('comment', result)
        self.assertIn('気性は穏やかで、調教も順調にこなしています', result['comment'])
    
    def test_extract_no_comment(self):
        """コメントが存在しない場合のテスト"""
        # テスト用のHTML（コメントなし）
        html = '<div class="other">テスト</div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result, success = self.extractor.extract(soup)
        
        # 検証
        self.assertFalse(success)
        self.assertIsNone(result)
        self.logger.debug.assert_called_with('コメントが見つかりませんでした')
    
    def test_extract_empty_comment(self):
        """空のコメント要素のテスト"""
        # テスト用のHTML（空のコメント）
        html = '<div class="comment"></div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result, success = self.extractor.extract(soup)
        
        # 検証
        self.assertFalse(success)
        self.assertIsNone(result)
        self.logger.debug.assert_called_with('コメントが見つかりませんでした')
    
    def test_extract_exception_handling(self):
        """例外発生時のテスト"""
        # 例外を発生させるためのモック
        with patch('bs4.BeautifulSoup.find', side_effect=Exception('Test error')):
            result, success = self.extractor.extract(BeautifulSoup('', 'html.parser'))
            
            # 検証
            self.assertFalse(success)
            self.assertIsNone(result)
            self.logger.error.assert_called()

if __name__ == '__main__':
    unittest.main()
