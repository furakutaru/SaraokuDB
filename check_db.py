import os
import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

def check_database():
    # データベースのパスを確認
    db_path = '/Users/yum.ishii/SaraokuDB/backend/data/horses.db'
    db_url = f'sqlite:///{db_path}'
    
    print(f"Database path: {db_path}")
    print(f"Database URL: {db_url}")
    print(f"File exists: {os.path.exists(db_path)}")
    
    # データベースエンジンを作成
    try:
        engine = create_engine(db_url)
        print("\nSuccessfully connected to the database")
        
        # テーブル一覧を取得
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print("\nTables in database:")
        for table in tables:
            print(f"- {table}")
            print("  Columns:")
            for column in inspector.get_columns(table):
                print(f"    - {column['name']}: {column['type']}")
        
        if not tables:
            print("No tables found in the database")
            
            # テーブルを作成してみる
            print("\nAttempting to create tables...")
            from backend.database.models import Base
            Base.metadata.create_all(engine)
            print("Tables created successfully")
            
            # 再度テーブル一覧を確認
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print("\nTables after creation:")
            for table in tables:
                print(f"- {table}")
                
    except Exception as e:
        print(f"\nError: {e}")
        print("\nTroubleshooting steps:")
        print("1. Check if the database directory exists and is writable")
        print("2. Check if SQLite is properly installed")
        print("3. Check for any permission issues")
        print("4. Try deleting the database file and let the application create a new one")

if __name__ == "__main__":
    check_database()
