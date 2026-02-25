import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('../.env')

def find_target_broodmares():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in .env")
        return

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # 「繫殖牝馬」を含む馬を検索（U+7E6B 繫 を使用）
        keywords = ['繫殖牝馬', '※繫殖牝馬', '繫殖']
        
        for kw in keywords:
            print(f"Searching for '{kw}'...")
            query = f"""
            SELECT id, name, race_record, comment 
            FROM horses 
            WHERE name LIKE '%{kw}%' 
               OR race_record LIKE '%{kw}%' 
               OR comment LIKE '%{kw}%';
            """
            cur.execute(query)
            rows = cur.fetchall()
            print(f"Found {len(rows)} horses for '{kw}'")
            for row in rows:
                print(f"  ID: {row[0]}, Name: {row[1]}")
            print("-" * 30)
            
        # ナツハヨルについて直接確認
        print("Checking 'ナツハヨル' status...")
        cur.execute("SELECT id, name, race_record, comment FROM horses WHERE name = 'ナツハヨル'")
        row = cur.fetchone()
        if row:
            print(f"Target Found! ID: {row[0]}, Name: {row[1]}, Race Record: {row[2]}")
            if row[3]:
                print(f"Comment Preview: {row[3][:100]}...")
        else:
            print("Horse 'ナツハヨル' not found in database.")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_target_broodmares()
