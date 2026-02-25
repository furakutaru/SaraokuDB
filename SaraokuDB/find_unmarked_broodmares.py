import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('../.env')

def find_potential_unmarked_broodmares():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in .env")
        return

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # 繁殖牝馬関連のキーワード（バリアント含む）
        keywords = ['繁殖', '繫殖', '受胎', '空胎']
        
        print("Scanning database for potential unmarked broodmares...")
        
        # race_recordが '繁殖牝馬' 以外で、name, race_record, commentのいずれかにキーワードを含むものを検索
        kw_conditions = " OR ".join([f"name LIKE '%{kw}%' OR race_record LIKE '%{kw}%' OR comment LIKE '%{kw}%'" for kw in keywords])
        
        query = f"""
        SELECT id, name, race_record, comment 
        FROM horses 
        WHERE ({kw_conditions})
          AND (race_record IS NULL OR race_record != '繁殖牝馬');
        """
        
        cur.execute(query)
        rows = cur.fetchall()
        
        print(f"Total potential candidates found: {len(rows)}")
        print("-" * 50)
        
        for row in rows:
            hid, name, record, comment = row
            # 判定ロジックの再現（簡易版）
            found_kw = []
            for kw in keywords:
                if (name and kw in name) or (record and kw in str(record)) or (comment and kw in comment):
                    found_kw.append(kw)
            
            # セン馬(セ)や牡馬(牡)を除外したい（もしデータにあれば）
            # でも今のクエリでは性別を見ていない
            
            print(f"ID: {hid}, Name: {name}")
            print(f"  Current Record: {record}")
            print(f"  Matched Keywords: {', '.join(found_kw)}")
            if comment:
                # 「繫殖牝馬を集め」のような stallion の説明文っぽいものを除外キーワードでフィルタリングしてみる
                ignore_patterns = ['集め', '繫養されたポリッシュパトリオット']
                if any(p in comment for p in ignore_patterns):
                    print("  [INFO] Likely a false positive (Stallion context or medical)")
            print("-" * 10)
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_potential_unmarked_broodmares()
