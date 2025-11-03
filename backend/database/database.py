"""
データベース接続設定
"""
import os
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# データベース接続URLを環境変数から取得
# 環境変数が設定されていない場合はデフォルト値を使用
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./saraokudb.sqlite3")

# テスト用のデータベースURL
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_saraokudb.sqlite3")
