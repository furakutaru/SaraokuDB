"""
スクリプトの説明: データベースにauction_idカラムを追加するマイグレーションスクリプト
"""
import os
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from database.models import Base, engine

def run_migration():
    """データベースマイグレーションを実行する"""
    print("\n=== データベースマイグレーションを開始します ===")
    
    # データベース接続の確認
    try:
        # トランザクションを開始
        with engine.begin() as conn:
            # テーブルが存在するか確認
            inspector = inspect(engine)
            if 'horses' not in inspector.get_table_names():
                print("エラー: 'horses' テーブルが見つかりません。")
                return False
                
            # 既にauction_idカラムが存在するか確認
            columns = [col['name'] for col in conn.execute(text("PRAGMA table_info(horses)"))]
            if 'auction_id' in columns:
                print("auction_idカラムは既に存在します。")
                return True
                
            # auction_idカラムを追加
            print("horsesテーブルにauction_idカラムを追加しています...")
            conn.execute(text("ALTER TABLE horses ADD COLUMN auction_id VARCHAR(20)"))
            
            # インデックスを作成
            print("auction_idにインデックスを作成しています...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_horses_auction_id ON horses(auction_id)"))
            
            # 変更をコミット
            print("✓ マイグレーションが正常に完了しました")
            return True
            
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        return False

if __name__ == "__main__":
    run_migration()
