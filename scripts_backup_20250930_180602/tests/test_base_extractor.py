"""
BaseExtractor のテストモジュール
"""
import logging
import pytest
from unittest.mock import MagicMock, patch
from components.base_extractor import BaseExtractor

# テスト用の具象クラス
class ConcreteExtractor(BaseExtractor):
    def extract(self, *args, **kwargs):
        return {"test": "data"}

class TestBaseExtractor:
    """BaseExtractor のテストクラス"""
    
    def test_init_with_logger(self):
        """ロガーを指定して初期化できることをテスト"""
        # テスト用のロガーを作成
        test_logger = logging.getLogger('test_logger')
        
        # ロガーを指定してインスタンス化
        extractor = ConcreteExtractor(logger=test_logger)
        
        # ロガーが正しく設定されていることを確認
        assert extractor.logger == test_logger
    
    def test_init_without_logger(self):
        """ロガーを指定せずに初期化できることをテスト"""
        # ロガーを指定せずにインスタンス化
        extractor = ConcreteExtractor()
        
        # デフォルトのロガーが設定されていることを確認
        assert extractor.logger is not None
        assert extractor.logger.name == 'components.base_extractor'
    
    def test_extract_is_abstract(self):
        """extract メソッドが抽象メソッドであることをテスト"""
        # 抽象クラスを直接インスタンス化しようとするとエラーになることを確認
        with pytest.raises(TypeError) as excinfo:
            BaseExtractor()
            
        # エラーメッセージを確認
        assert "Can't instantiate abstract class BaseExtractor" in str(excinfo.value)
    
    @patch('components.base_extractor.logging')
    def test_logger_usage(self, mock_logging):
        """ロガーが正しく使用されていることをテスト"""
        # モックロガーを設定
        mock_logger = MagicMock()
        mock_logging.getLogger.return_value = mock_logger
        
        # サブクラスを作成してテスト
        class TestExtractor(BaseExtractor):
            def extract(self, *args, **kwargs):
                self.logger.info("Test message")
                return "test_result"
        
        # テスト実行
        extractor = TestExtractor()
        result = extractor.extract()
        
        # ロガーが正しく呼び出されたことを確認
        mock_logger.info.assert_called_once_with("Test message")
        assert result == "test_result"

    def test_subclass_must_implement_extract(self):
        """サブクラスが extract メソッドを実装する必要があることをテスト"""
        with pytest.raises(TypeError) as excinfo:
            class InvalidExtractor(BaseExtractor):
                pass
            
            # インスタンス化時にエラーが発生することを確認
            InvalidExtractor()
            
        # エラーメッセージを確認
        error_msg = str(excinfo.value)
        assert "Can't instantiate abstract class InvalidExtractor" in error_msg
        assert "abstract method extract" in error_msg

    def test_concrete_subclass_works(self):
        """正しく実装されたサブクラスが動作することをテスト"""
        class ValidExtractor(BaseExtractor):
            def extract(self, *args, **kwargs):
                return {"key": "value"}
        
        # 正しくインスタンス化できることを確認
        extractor = ValidExtractor()
        result = extractor.extract()
        
        # 期待通りの結果が返ることを確認
        assert result == {"key": "value"}
