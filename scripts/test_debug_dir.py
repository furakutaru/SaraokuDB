"""
Debug directory creation and file saving test script.
"""
import os
import sys
from pathlib import Path
from datetime import datetime

def test_debug_dir():
    # プロジェクトのルートディレクトリを取得
    project_root = Path(__file__).parent.parent
    debug_dir = project_root / 'debug'
    
    # 日付ベースのサブディレクトリを作成
    date_str = datetime.now().strftime("%Y%m%d")
    date_dir = debug_dir / date_str
    detail_dir = date_dir / 'detail'
    
    # ディレクトリを作成
    for directory in [debug_dir, date_dir, detail_dir]:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✓ ディレクトリが作成/確認されました: {directory}")
            
            # パーミッションを確認
            if os.access(directory, os.W_OK):
                print(f"  ✓ 書き込み可能: {directory}")
            else:
                print(f"  ✗ 書き込み権限がありません: {directory}")
                
        except Exception as e:
            print(f"✗ ディレクトリの作成に失敗しました {directory}: {e}")
    
    # テストファイルを作成
    test_file = detail_dir / 'test_file.txt'
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("This is a test file.\n")
            f.write(f"Created at: {datetime.now()}\n")
        print(f"✓ テストファイルが作成されました: {test_file}")
    except Exception as e:
        print(f"✗ テストファイルの作成に失敗しました: {e}")
        
    # カレントディレクトリの情報を表示
    print("\n現在の作業ディレクトリ:", os.getcwd())
    print("スクリプトの場所:", Path(__file__).resolve())
    print("デバッグディレクトリ:", debug_dir.resolve())
    print("日付ディレクトリ:", date_dir.resolve())
    print("詳細ディレクトリ:", detail_dir.resolve())

if __name__ == "__main__":
    print("=== デバッグディレクトリテストを開始します ===\n")
    test_debug_dir()
    print("\n=== テストが完了しました ===")
