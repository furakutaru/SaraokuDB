#!/usr/bin/env python3
"""
スクレイパーを実行するためのラッパースクリプト
"""
import os
import sys

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# スクリプトのディレクトリをPythonパスに追加
scripts_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, scripts_dir)

# スクレイパーをインポートして実行
from improved_scraper import main

if __name__ == "__main__":
    import sys
    import traceback
    try:
        sys.exit(main())
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {str(e)}")
        print("トレースバック:")
        traceback.print_exc()
        sys.exit(1)
