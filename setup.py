#!/usr/bin/env python3
"""
サラブレッドオークション データベース セットアップスクリプト
"""

import os
import subprocess
import sys

def run_command(command, description):
    """コマンドを実行"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description}完了")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description}失敗: {e}")
        print(f"エラー出力: {e.stderr}")
        return False

def get_python_command():
    """適切なPythonコマンドを取得"""
    # python3を優先的に使用
    try:
        subprocess.run(["python3", "--version"], check=True, capture_output=True)
        return "python3"
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            subprocess.run(["python", "--version"], check=True, capture_output=True)
            return "python"
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Pythonが見つかりません。Python 3.7以上をインストールしてください。")
            sys.exit(1)

def main():
    print("🐎 サラブレッドオークション データベース セットアップ")
    print("=" * 50)
    
    # 適切なPythonコマンドを取得
    python_cmd = get_python_command()
    print(f"✅ Pythonコマンド: {python_cmd}")
    
    # Pythonの依存関係をインストール
    if not run_command(f"{python_cmd} -m pip install -r requirements.txt", "Python依存関係のインストール"):
        print("❌ セットアップに失敗しました")
        sys.exit(1)
    
    # データディレクトリを作成
    os.makedirs("data", exist_ok=True)
    print("✅ データディレクトリを作成")
    
    # データベースを初期化
    if not run_command(f"{python_cmd} -m backend.database.init_db", "データベースの初期化"):
        print("❌ セットアップに失敗しました")
        sys.exit(1)
    
    # フロントエンドの依存関係をインストール
    if not run_command("cd frontend && npm install", "フロントエンド依存関係のインストール"):
        print("❌ セットアップに失敗しました")
        sys.exit(1)
    
    print("\n🎉 セットアップ完了！")
    print("\n使用方法:")
    print("1. バックエンドサーバーを起動:")
    print(f"   {python_cmd} -m uvicorn backend.main:app --reload")
    print("\n2. フロントエンドサーバーを起動（別ターミナル）:")
    print("   cd frontend && npm start")
    print("\n3. ブラウザで http://localhost:3000 にアクセス")

if __name__ == "__main__":
    main() 