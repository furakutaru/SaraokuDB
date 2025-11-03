import sys
import os
from pathlib import Path

# プロジェクトのルートディレクトリを取得
project_root = Path(__file__).parent
print(f"Project root: {project_root}")

# Pythonのパスを表示
print("\nPython path:")
for p in sys.path:
    print(f"- {p}")

# バックエンドディレクトリの存在を確認
backend_path = project_root / "backend"
print(f"\nBackend path exists: {backend_path.exists()}")

# バックエンドモジュールのインポートを試みる
print("\nTrying to import backend.database...")
try:
    # プロジェクトのルートをPythonパスに追加
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # バックエンドモジュールをインポート
    from backend.database import models
    print("Successfully imported backend.database.models")
    
    # データベース接続を確認
    print("\nDatabase connection:")
    print(f"DATABASE_URL: {models.DATABASE_URL}")
    
except Exception as e:
    print(f"Error importing backend.database: {e}")
    import traceback
    traceback.print_exc()

# dateutilのインポートを試みる
print("\nTrying to import dateutil.parser...")
try:
    from dateutil import parser
    print(f"Successfully imported dateutil.parser: {parser.__file__}")
except ImportError as e:
    print(f"Error importing dateutil.parser: {e}")
