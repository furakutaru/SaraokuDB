"""
CommentExtractorのテスト
"""
import unittest
from ..comment.extractor import CommentExtractor

class TestCommentExtractor(unittest.TestCase):
    """CommentExtractorのテストケース"""
    
    def setUp(self):
        self.extractor = CommentExtractor()

    def test_extract_comment(self):
        """コメント抽出のテスト"""
        pass

if __name__ == '__main__':
    unittest.main()
