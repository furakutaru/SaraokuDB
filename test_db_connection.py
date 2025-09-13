import sys
import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

def test_db_connection():
    # データベースのパスを設定
    db_path = '/Users/yum.ishii/SaraokuDB/backend/data/horses.db'
    db_url = f'sqlite:///{db_path}'
    
    print(f"Database path: {db_path}")
    print(f"Database URL: {db_url}")
    print(f"File exists: {os.path.exists(db_path)}")
    
    try:
        # データベースエンジンを作成
        engine = create_engine(db_url)
        print("\nSuccessfully connected to the database")
        
        # テーブル一覧を取得
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"\nTables in database: {tables}")
        
        # 各テーブルの構造を表示
        for table_name in tables:
            print(f"\nTable: {table_name}")
            columns = [c['name'] for c in inspector.get_columns(table_name)]
            print(f"  Columns: {', '.join(columns)}")
            
            # テーブルの最初の5行を表示
            with engine.connect() as conn:
                try:
                    result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 5"))
                    rows = result.fetchall()
                    print(f"  First {len(rows)} rows:")
                    for row in rows:
                        print(f"    {row}")
                except Exception as e:
                    print(f"  Error querying table {table_name}: {e}")
        
    except Exception as e:
        print(f"\nError connecting to the database: {e}")
        import traceback
        print(f"\nTraceback:\n{traceback.format_exc()}")

if __name__ == "__main__":
    test_db_connection()
