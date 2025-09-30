import os
import sys
from sqlalchemy import inspect
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import Base, engine, SessionLocal

def init_database():
    """データベースとテーブルを作成する"""
    try:
        # データベースファイルのディレクトリを取得
        db_dir = os.path.dirname(os.path.abspath(engine.url.database))
        print(f"データベースディレクトリ: {db_dir}")
        
        # ディレクトリが存在しない場合は作成
        os.makedirs(db_dir, exist_ok=True)
        print(f"データベースファイル: {engine.url.database}")
        
        # テーブルが存在するか確認
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        print(f"既存のテーブル: {existing_tables}")
        
        # テーブルを作成
        print("テーブルを作成中...")
        Base.metadata.create_all(bind=engine)
        
        # テーブルが作成されたか確認
        inspector = inspect(engine)
        created_tables = inspector.get_table_names()
        print(f"作成されたテーブル: {created_tables}")
        
        if 'horses' in created_tables:
            print("✓ horsesテーブルが正常に作成されました")
        else:
            print("✗ horsesテーブルの作成に失敗しました")
            
        print("\nデータベースが正常に初期化されました。")
        
    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("データベースを初期化しています...")
    init_database()