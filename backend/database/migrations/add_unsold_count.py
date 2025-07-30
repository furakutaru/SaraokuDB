import sqlite3
import os

# データベース設定
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, 'data', 'horses.db')

def add_unsold_count_column():
    """horsesテーブルにunsold_countカラムを追加する"""
    try:
        # SQLiteデータベースに接続
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # カラムが存在するか確認
        cursor.execute("PRAGMA table_info(horses)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # unsold_countカラムが存在しない場合のみ追加
        if 'unsold_count' not in columns:
            cursor.execute("ALTER TABLE horses ADD COLUMN unsold_count INTEGER DEFAULT 0")
            conn.commit()
            print("✅ Added 'unsold_count' column to 'horses' table")
        else:
            print("ℹ️ 'unsold_count' column already exists in 'horses' table")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise
    finally:
        # 接続を閉じる
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Starting database migration...")
    try:
        add_unsold_count_column()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise
