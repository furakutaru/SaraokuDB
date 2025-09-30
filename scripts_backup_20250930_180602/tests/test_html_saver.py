"""
HTML保存ユーティリティのユニットテスト
"""
import unittest
import os
import shutil
from unittest.mock import patch, MagicMock
from pathlib import Path

from core.utils.html_saver import HTMLSaver

class TestHTMLSaver(unittest.TestCase):
    """HTMLSaverクラスのテスト"""
    
    def setUp(self):
        """テストの前処理"""
        # テスト用の一時ディレクトリを作成
        self.test_dir = os.path.join(os.path.dirname(__file__), 'test_cache')
        os.makedirs(self.test_dir, exist_ok=True)
        
        # テスト用のHTMLSaverインスタンスを作成
        self.html_saver = HTMLSaver(base_dir=Path(self.test_dir))
    
    def tearDown(self):
        """テストの後処理"""
        # テスト用の一時ディレクトリを削除
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_save_html(self):
        """HTMLの保存と読み込みのテスト"""
        # テストデータ
        key = "test_key"
        html_content = "<html><body><h1>Test HTML</h1></body></html>"
        
        # HTMLを保存
        filepath = self.html_saver.save_html(key, html_content)
        
        # ファイルが存在することを確認
        self.assertTrue(os.path.exists(filepath))
        
        # 保存された内容を確認
        with open(filepath, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        self.assertEqual(saved_content, html_content)
        
        # ファイル名が正しいことを確認
        self.assertIn(key, filepath)
        self.assertTrue(filepath.endswith('.html'))
    
    def test_load_html(self):
        """HTMLの読み込みテスト"""
        # テストデータ
        key = "test_key"
        html_content = "<html><body><h1>Test HTML</h1></body></html>"
        
        # テスト用のHTMLファイルを作成
        filepath = os.path.join(self.test_dir, f"{key}.html")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # HTMLを読み込む
        loaded_content = self.html_saver.load_html(key)
        
        # 読み込んだ内容が正しいことを確認
        self.assertEqual(loaded_content, html_content)
    
    def test_load_html_not_found(self):
        """存在しないHTMLの読み込みテスト"""
        # 存在しないキーを指定
        key = "non_existent_key"
        
        # HTMLを読み込む（存在しない場合はNoneを返す）
        loaded_content = self.html_saver.load_html(key)
        
        # Noneが返されることを確認
        self.assertIsNone(loaded_content)
    
    def test_get_file_path(self):
        """ファイルパスの取得テスト"""
        # テストデータ
        key = "test_key"
        
        # ファイルパスを取得
        filepath = self.html_saver.get_file_path(key)
        
        # 期待されるファイルパス
        expected_path = os.path.join(self.test_dir, f"{key}.html")
        
        # ファイルパスが正しいことを確認
        self.assertEqual(filepath, expected_path)
    
    def test_clear_cache(self):
        """キャッシュのクリアテスト"""
        # テスト用のHTMLファイルを作成
        keys = ["test1", "test2", "test3"]
        for key in keys:
            filepath = os.path.join(self.test_dir, f"{key}.html")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"<html><body><h1>{key}</h1></body></html>")
        
        # キャッシュをクリア
        self.html_saver.clear_cache()
        
        # ディレクトリ内のファイルを確認
        files = os.listdir(self.test_dir)
        self.assertEqual(len(files), 0)
    
    @patch('core.utils.html_saver.os.path.getmtime')
    @patch('core.utils.html_saver.os.listdir')
    def test_get_latest_file(self, mock_listdir, mock_getmtime):
        """最新ファイルの取得テスト"""
        # モックの設定
        mock_listdir.return_value = [
            'file1.html',
            'file2.html',
            'file3.html'
        ]
        
        # ファイルの更新日時を設定（file2が最新）
        mock_getmtime.side_effect = [
            1000,  # file1.html
            3000,  # file2.html
            2000   # file3.html
        ]
        
        # 最新のファイルを取得
        latest_file = self.html_saver._get_latest_file(self.test_dir)
        
        # 最新のファイルが正しいことを確認
        self.assertEqual(latest_file, os.path.join(self.test_dir, 'file2.html'))
    
    @patch('core.utils.html_saver.HTMLSaver._get_latest_file')
    def test_load_latest_html(self, mock_get_latest_file):
        """最新のHTMLを読み込むテスト"""
        # モックの設定
        latest_file = os.path.join(self.test_dir, 'latest.html')
        mock_get_latest_file.return_value = latest_file
        
        # テスト用のHTMLファイルを作成
        html_content = "<html><body><h1>Latest HTML</h1></body></html>"
        with open(latest_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 最新のHTMLを読み込む
        loaded_content = self.html_saver.load_latest_html()
        
        # 読み込んだ内容が正しいことを確認
        self.assertEqual(loaded_content, html_content)
        mock_get_latest_file.assert_called_once_with(self.test_dir)
    
    def test_load_latest_html_no_files(self):
        """ファイルが存在しない場合の最新HTML読み込みテスト"""
        # 空のディレクトリでテスト
        empty_dir = os.path.join(self.test_dir, 'empty')
        os.makedirs(empty_dir, exist_ok=True)
        
        # 空のディレクトリを指定してHTMLSaverを作成
        empty_saver = HTMLSaver(cache_dir=empty_dir)
        
        # 最新のHTMLを読み込む（ファイルが存在しない場合はNoneを返す）
        loaded_content = empty_saver.load_latest_html()
        
        # Noneが返されることを確認
        self.assertIsNone(loaded_content)

if __name__ == '__main__':
    unittest.main()
