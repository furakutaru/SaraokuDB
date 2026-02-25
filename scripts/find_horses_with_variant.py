import os
import psycopg2
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

def find_variant_horses():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in .env")
        return

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # 「繫」を含む馬を検索
        # name, race_record, comment の各カラムを対象とする
        query = """
        SELECT id, name, race_record, comment 
        FROM horses 
        WHERE name LIKE '%繫%' 
           OR race_record LIKE '%繫%' 
           OR comment LIKE '%繫%';
        """
        
        cur.execute(query)
        rows = cur.fetchall()
        
        print(f"「繫」を含む馬の数: {len(rows)}")
        print("-" * 50)
        
        for row in rows:
            print(f"ID: {row[0]}, Name: {row[1]}, Race Record: {row[2]}")
            # コメントに「繫」が含まれているか確認
            if row[3] and '繫' in row[3]:
                print(f"  -> Comment contains '繫'")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_variant_horses()
