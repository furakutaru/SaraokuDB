"""
ロガーユーティリティのユニットテスト
"""
import unittest
import logging
import os
import shutil
from unittest.mock import patch, MagicMock
from pathlib import Path

from core.utils.logger import setup_logger, get_logger, LoggerMixin

class TestLogger(unittest.TestCase):
    """ロガーユーティリティのテスト"""
    
    def setUp(self):
        """テストの前処理"""
        # テスト用のログディレクトリを作成
        self.test_log_dir = os.path.join(os.path.dirname(__file__), 'test_logs')
        os.makedirs(self.test_log_dir, exist_ok=True)
        
        # 既存のロガーをクリア
        logging.Logger.manager.loggerDict.clear()
    
    def tearDown(self):
        """テストの後処理"""
        # テスト用のログディレクトリを削除
        if os.path.exists(self.test_log_dir):
            shutil.rmtree(self.test_log_dir)
        
        # ロガーをリセット
        logging.Logger.manager.loggerDict.clear()
    
    def test_setup_logger(self):
        """ロガーのセットアップテスト"""
        # ロガーをセットアップ
        logger_name = "test_logger"
        log_file = os.path.join(self.test_log_dir, "test.log")
        
        # ロガーをセットアップ
        logger = setup_logger(
            name=logger_name,
            log_file=log_file,
            level=logging.DEBUG,
            console_level=logging.INFO
        )
        
        # ロガーが正しく設定されていることを確認
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, logger_name)
        self.assertEqual(logger.level, logging.DEBUG)
        
        # ハンドラーが正しく設定されていることを確認
        self.assertEqual(len(logger.handlers), 2)  # FileHandlerとStreamHandler
        
        # ログファイルが作成されていることを確認
        self.assertTrue(os.path.exists(log_file))
    
    def test_get_logger(self):
        """ロガーの取得テスト"""
        # ロガーを取得（存在しない場合は新規作成）
        logger_name = "test_get_logger"
        logger = get_logger(logger_name)
        
        # ロガーが正しく取得/作成されていることを確認
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, logger_name)
        
        # 再度同じ名前でロガーを取得（既存のロガーが返されることを確認）
        same_logger = get_logger(logger_name)
        self.assertIs(logger, same_logger)
    
    def test_logger_mixin(self):
        """LoggerMixinのテスト"""
        # LoggerMixinを継承したテストクラス
        class TestClass(LoggerMixin):
            def __init__(self):
                super().__init__()
                self.logger = get_logger(self.__class__.__name__)
        
        # テストクラスのインスタンスを作成
        test_obj = TestClass()
        
        # ロガーが正しく設定されていることを確認
        self.assertIsInstance(test_obj.logger, logging.Logger)
        self.assertEqual(test_obj.logger.name, "TestClass")
    
    @patch('logging.Logger.log')
    def test_log_levels(self, mock_log):
        """ログレベルのテスト"""
        # ロガーをセットアップ
        logger_name = "test_log_levels"
        logger = setup_logger(
            name=logger_name,
            log_file=os.path.join(self.test_log_dir, "test_levels.log"),
            level=logging.DEBUG
        )
        
        # 各レベルのログを出力
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        # 各レベルのログが正しく記録されたことを確認
        expected_calls = [
            ((logging.DEBUG, "Debug message"), {}),
            ((logging.INFO, "Info message"), {}),
            ((logging.WARNING, "Warning message"), {}),
            ((logging.ERROR, "Error message"), {}),
            ((logging.CRITICAL, "Critical message"), {})
        ]
        
        # モックが期待通りに呼び出されたことを確認
        mock_log.assert_has_calls(expected_calls, any_order=True)
    
    def test_log_file_rotation(self):
        """ログファイルのローテーションテスト"""
        # ロガーをセットアップ（最大1KB、3世代まで保持）
        logger_name = "test_rotation"
        log_file = os.path.join(self.test_dir, "rotation.log")
        
        logger = setup_logger(
            name=logger_name,
            log_file=log_file,
            max_bytes=1024,  # 1KB
            backup_count=3,
            level=logging.INFO
        )
        
        # ログを大量に出力してローテーションを発生させる
        for i in range(1000):
            logger.info(f"Test log message {i}" * 10)
        
        # ログファイルがローテーションされていることを確認
        log_files = [f for f in os.listdir(self.test_dir) if f.startswith("rotation.log")]
        self.assertLessEqual(len(log_files), 4)  # 現在のログ + 3世代のバックアップ
    
    @patch('logging.StreamHandler')
    def test_console_logging(self, mock_handler):
        """コンソールロギングのテスト"""
        # モックの設定
        mock_handler.return_value = MagicMock()
        
        # ロガーをセットアップ（コンソール出力のみ）
        logger_name = "test_console"
        logger = setup_logger(
            name=logger_name,
            log_file=None,  # ファイル出力なし
            console=True,
            console_level=logging.WARNING
        )
        
        # ログを出力
        logger.debug("This should not appear")
        logger.warning("This should appear")
        
        # コンソールハンドラーが設定されていることを確認
        self.assertTrue(any(isinstance(h, MagicMock) for h in logger.handlers))
        
        # ログレベルが正しく設定されていることを確認
        mock_handler.return_value.setLevel.assert_called_once_with(logging.WARNING)
    
    def test_custom_formatter(self):
        """カスタムフォーマッタのテスト"""
        # カスタムフォーマットを定義
        custom_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        # ロガーをセットアップ
        logger_name = "test_custom_format"
        log_file = os.path.join(self.test_log_dir, "custom_format.log")
        
        logger = setup_logger(
            name=logger_name,
            log_file=log_file,
            log_format=custom_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # ログを出力
        test_message = "Test message with custom format"
        logger.info(test_message)
        
        # ログファイルを読み込んでフォーマットを確認
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # ログのフォーマットが正しいことを確認
        self.assertIn(logger_name, log_content)
        self.assertIn("INFO", log_content)
        self.assertIn(test_message, log_content)

if __name__ == '__main__':
    unittest.main()
