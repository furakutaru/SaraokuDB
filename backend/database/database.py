"""
データベース接続設定
"""
import os
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# データベース接続URLを環境変数から取得
# 環境変数が設定されていない場合はエラーを発生
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URLが設定されていません。環境変数を設定してください。")

# テスト用のデータベースURL
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    raise ValueError("TEST_DATABASE_URLが設定されていません。環境変数を設定してください。")
