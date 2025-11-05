import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# .env ファイルから環境変数を読み込む
load_dotenv()

# データベース接続設定
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL が設定されていません。.envファイルを確認してください。")

def main():
    print(f"データベースに接続しています: {DATABASE_URL.split('@')[-1] if DATABASE_URL else '不明'}")
    
    # エンジンとセッションの作成
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # テーブルが存在するか確認
        result = db.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'horses')"))
        if not result.scalar():
            print("エラー: 'horses' テーブルが見つかりません。")
            return
            
        print("1/3: 既存の unified_race_records カラムを削除しています...")
        db.execute(text('ALTER TABLE horses DROP COLUMN IF EXISTS unified_race_records;'))
        db.commit()
        
        print("2/3: 新しい unified_race_records カラムを追加しています...")
        db.execute(text('ALTER TABLE horses ADD COLUMN unified_race_records BOOLEAN DEFAULT false;'))
        db.commit()
        
        print("3/3: レコードを更新しています...")
        update_sql = """
            UPDATE horses 
            SET unified_race_records = (
                CASE 
                    WHEN race_record IS NULL THEN true
                    WHEN race_record::json->>'total_races' IS NULL THEN true
                    WHEN (race_record::json->>'total_races')::int = 0 THEN true
                    ELSE false 
                END
            )
        """
        db.execute(text(update_sql))
        db.commit()
        
        # 更新結果を確認
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN unified_race_records = true THEN 1 ELSE 0 END) as unraced,
                SUM(CASE WHEN unified_race_records = false THEN 1 ELSE 0 END) as raced
            FROM horses
        """))
        
        stats = result.fetchone()
        print("\n更新が完了しました。")
        print(f"総レコード数: {stats[0]}")
        print(f"未出走馬: {stats[1]}")
        print(f"出走経験馬: {stats[2]}")
        
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
