import sys
import os
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from database.models import Base, engine

def init_db():
    print("データベースを初期化しています...")
    # テーブルを作成
    Base.metadata.create_all(bind=engine)
    print("データベースの初期化が完了しました。")

if __name__ == "__main__":
    init_db()
