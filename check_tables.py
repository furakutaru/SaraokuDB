from sqlalchemy import create_engine, inspect, text

def check_database():
    # データベースエンジンを作成
    DATABASE_URL = 'sqlite:////Users/yum.ishii/SaraokuDB/backend/data/horses.db'
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    # テーブル一覧を取得
    tables = inspector.get_table_names()
    print('テーブル一覧:')
    for table in tables:
        print(f'\nテーブル: {table}')
        print('カラム:')
        for column in inspector.get_columns(table):
            print(f'  - {column["name"]}: {column["type"]}')
    
    # テストデータを確認
    if 'test_table' in tables:
        with engine.connect() as conn:
            result = conn.execute(text('SELECT * FROM test_table'))
            print('\nテストデータ:')
            for row in result:
                print(dict(row._mapping))

if __name__ == "__main__":
    check_database()
