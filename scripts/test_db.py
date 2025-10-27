import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# 環境変数の読み込み
load_dotenv()

# データベース接続
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("エラー: DATABASE_URL が設定されていません。.envファイルを確認してください。")
    exit(1)

engine = create_engine(DATABASE_URL)

# 接続テスト
with engine.connect() as conn:
    # テーブルの存在確認
    try:
        tables = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
        
        print("利用可能なテーブル:")
        for table in tables:
            print(f"- {table[0]}")

        # horsesテーブルのレコード数を確認
        count = conn.execute(text("SELECT COUNT(*) FROM horses")).scalar()
        print(f"\nhorsesテーブルのレコード数: {count}")

        # サンプルデータを表示
        if count > 0:
            print("\n最初の5件のレコード:")
            result = conn.execute(text("SELECT id, name, auction_date FROM horses LIMIT 5"))
            for row in result:
                print(row)
                
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
