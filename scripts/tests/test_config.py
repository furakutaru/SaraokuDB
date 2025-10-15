"""
設定モジュールのユニットテスト
"""
import unittest
import os
import tempfile
import json
from unittest.mock import patch, mock_open

from core.config.settings import Config, ConfigError

class TestConfig(unittest.TestCase):
    """Configクラスのテスト"""
    
    def setUp(self):
        """テストの前処理"""
        # テスト用の一時ディレクトリを作成
        self.test_dir = tempfile.mkdtemp()
        self.test_config_path = os.path.join(self.test_dir, 'test_config.json')
        
        # テスト用の設定データ
        self.test_config_data = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "test_db",
                "user": "test_user"
            },
            "scraper": {
                "timeout": 30,
                "max_retries": 3,
                "user_agent": "Test User Agent"
            },
            "logging": {
                "level": "INFO",
                "file": "/var/log/test.log"
            }
        }
        
        # テスト用の設定ファイルを作成
        with open(self.test_config_path, 'w') as f:
            json.dump(self.test_config_data, f)
    
    def tearDown(self):
        """テストの後処理"""
        # テスト用の一時ディレクトリを削除
        if os.path.exists(self.test_dir):
            for filename in os.listdir(self.test_dir):
                file_path = os.path.join(self.test_dir, filename)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            os.rmdir(self.test_dir)
    
    def test_load_config_success(self):
        """設定ファイルの読み込みテスト（成功）"""
        # 設定をロード
        config = Config(self.test_config_path)
        
        # 設定が正しくロードされたことを確認
        self.assertEqual(config.get("database.host"), "localhost")
        self.assertEqual(config.get("database.port"), 5432)
        self.assertEqual(config.get("scraper.timeout"), 30)
        self.assertEqual(config.get("logging.level"), "INFO")
    
    def test_load_config_file_not_found(self):
        """設定ファイルが存在しない場合のテスト"""
        # 存在しないファイルを指定
        non_existent_file = os.path.join(self.test_dir, 'non_existent.json')
        
        # ファイルが存在しない場合はConfigErrorが発生することを確認
        with self.assertRaises(ConfigError) as context:
            Config(non_existent_file)
        
        self.assertIn("設定ファイルが見つかりません", str(context.exception))
    
    def test_load_config_invalid_json(self):
        """無効なJSONファイルの場合のテスト"""
        # 無効なJSONファイルを作成
        invalid_json_path = os.path.join(self.test_dir, 'invalid.json')
        with open(invalid_json_path, 'w') as f:
            f.write("{invalid json")
        
        # 無効なJSONの場合はConfigErrorが発生することを確認
        with self.assertRaises(ConfigError) as context:
            Config(invalid_json_path)
        
        self.assertIn("設定ファイルの形式が無効です", str(context.exception))
    
    def test_get_nested_value(self):
        """ネストされた値の取得テスト"""
        # 設定をロード
        config = Config(self.test_config_path)
        
        # ネストされた値を取得
        self.assertEqual(config.get("database.host"), "localhost")
        self.assertEqual(config.get("scraper.timeout"), 30)
        
        # 存在しないキーはデフォルト値を返す
        self.assertIsNone(config.get("non.existent.key"))
        self.assertEqual(config.get("non.existent.key", default="default"), "default")
    
    def test_get_with_default_value(self):
        """デフォルト値のテスト"""
        # 設定をロード
        config = Config(self.test_config_path)
        
        # 存在するキーはその値を返す
        self.assertEqual(config.get("database.host", default="default"), "localhost")
        
        # 存在しないキーはデフォルト値を返す
        self.assertEqual(config.get("non.existent.key", default="default"), "default")
        self.assertIsNone(config.get("non.existent.key"))
    
    def test_set_value(self):
        """値の設定テスト"""
        # 設定をロード
        config = Config(self.test_config_path)
        
        # 新しい値を設定
        config.set("new.key", "value")
        self.assertEqual(config.get("new.key"), "value")
        
        # 既存の値を上書き
        config.set("database.host", "127.0.0.1")
        self.assertEqual(config.get("database.host"), "127.0.0.1")
        
        # ネストされた値を設定
        config.set("nested.value.key", 123)
        self.assertEqual(config.get("nested.value.key"), 123)
    
    def test_save_config(self):
        """設定の保存テスト"""
        # 新しい設定ファイルのパス
        new_config_path = os.path.join(self.test_dir, 'new_config.json')
        
        # 設定をロードして新しいファイルに保存
        config = Config(self.test_config_path)
        config.save(new_config_path)
        
        # ファイルが作成されたことを確認
        self.assertTrue(os.path.exists(new_config_path))
        
        # 保存された内容を確認
        with open(new_config_path, 'r') as f:
            saved_config = json.load(f)
        
        self.assertEqual(saved_config["database"]["host"], "localhost")
        self.assertEqual(saved_config["scraper"]["timeout"], 30)
    
    @patch('os.makedirs')
    def test_save_config_create_directory(self, mock_makedirs):
        """ディレクトリが存在しない場合の保存テスト"""
        # 新しい設定ファイルのパス（存在しないディレクトリ）
        new_dir = os.path.join(self.test_dir, 'new_dir')
        new_config_path = os.path.join(new_dir, 'config.json')
        
        # 設定をロードして新しいファイルに保存
        config = Config(self.test_config_path)
        config.save(new_config_path)
        
        # ディレクトリが作成されたことを確認
        mock_makedirs.assert_called_once_with(new_dir, exist_ok=True)
    
    def test_reload_config(self):
        """設定の再読み込みテスト"""
        # 設定をロード
        config = Config(self.test_config_path)
        
        # 元の値を確認
        self.assertEqual(config.get("database.host"), "localhost")
        
        # 設定ファイルを更新
        updated_config = self.test_config_data.copy()
        updated_config["database"]["host"] = "127.0.0.1"
        
        with open(self.test_config_path, 'w') as f:
            json.dump(updated_config, f)
        
        # 設定を再読み込み
        config.reload()
        
        # 値が更新されたことを確認
        self.assertEqual(config.get("database.host"), "127.0.0.1")
    
    def test_contains(self):
        """in演算子のテスト"""
        # 設定をロード
        config = Config(self.test_config_path)
        
        # 存在するキー
        self.assertTrue("database.host" in config)
        self.assertTrue("scraper.timeout" in config)
        
        # 存在しないキー
        self.assertFalse("non.existent.key" in config)
    
    def test_getitem(self):
        """__getitem__のテスト"""
        # 設定をロード
        config = Config(self.test_config_path)
        
        # 存在するキー
        self.assertEqual(config["database.host"], "localhost")
        self.assertEqual(config["scraper.timeout"], 30)
        
        # 存在しないキーはKeyErrorを発生
        with self.assertRaises(KeyError):
            _ = config["non.existent.key"]
    
    def test_setitem(self):
        """__setitem__のテスト"""
        # 設定をロード
        config = Config(self.test_config_path)
        
        # 新しい値を設定
        config["new.key"] = "value"
        self.assertEqual(config["new.key"], "value")
        
        # 既存の値を上書き
        config["database.host"] = "127.0.0.1"
        self.assertEqual(config["database.host"], "127.0.0.1")
    
    def test_delitem(self):
        """__delitem__のテスト"""
        # 設定をロード
        config = Config(self.test_config_path)
        
        # キーが存在することを確認
        self.assertTrue("database.host" in config)
        
        # キーを削除
        del config["database.host"]
        
        # キーが削除されたことを確認
        self.assertFalse("database.host" in config)
        
        # 存在しないキーを削除しようとするとKeyError
        with self.assertRaises(KeyError):
            del config["non.existent.key"]
    
    def test_str_and_repr(self):
        """文字列表現のテスト"""
        # 設定をロード
        config = Config(self.test_config_path)
        
        # __str__と__repr__が正しく動作することを確認
        self.assertIsInstance(str(config), str)
        self.assertIsInstance(repr(config), str)
        self.assertIn("Config", repr(config))

if __name__ == '__main__':
    unittest.main()
