import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('../.env')

def check_raw_name_variants():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found")
        return

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # 繁殖牝馬判定のロジックで使われるキーワード (バリアント)
        # 実際には raw_name (現在のDBでは name カラムに相当) をチェック
        variants = ['繫']
        
        for v in variants:
            print(f"Searching for '{v}' in name column...")
            cur.execute(f"SELECT id, name, race_record FROM horses WHERE name LIKE '%{v}%'")
            rows = cur.fetchall()
            print(f"Found {len(rows)} cases.")
            for row in rows:
                print(f"ID: {row[0]}, Name: {row[1]}, Record: {row[2]}")
            print("-" * 30)

        # 念のため、現在 '繁殖牝馬' となっている馬の数も確認
        cur.execute("SELECT COUNT(*) FROM horses WHERE race_record = '繁殖牝馬'")
        print(f"Total current broodmares in DB: {cur.fetchone()[0]}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_raw_name_variants()
