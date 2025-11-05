import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# データベース接続設定
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/saraokudb")

def main():
    # エンジンとセッションの作成
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("Dropping existing unified_race_records column if it exists...")
        db.execute(text('ALTER TABLE horses DROP COLUMN IF EXISTS unified_race_records;'))
        db.commit()
        
        print("Adding new unified_race_records column as boolean...")
        db.execute(text('ALTER TABLE horses ADD COLUMN unified_race_records BOOLEAN DEFAULT false;'))
        db.commit()
        
        print("Updating unified_race_records based on race_record data...")
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
        
        print("Successfully updated unified_race_records column.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
