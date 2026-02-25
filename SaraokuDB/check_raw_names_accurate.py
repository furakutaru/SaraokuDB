import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('../.env')

def check_raw_name_variants_properly():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found")
        return

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # 繁殖牝馬判定キーワード
        keywords = ['繁殖', '繫殖', '受胎', '空胎']
        
        found_total = []
        
        for kw in keywords:
            print(f"Scanning raw_name for '{kw}'...")
            query = f"SELECT id, name, raw_name, race_record FROM horses WHERE raw_name LIKE '%{kw}%'"
            cur.execute(query)
            rows = cur.fetchall()
            print(f"  -> Found {len(rows)} matching '{kw}'")
            for r in rows:
                found_total.append(r)
        
        # 重複除去
        unique_matches = {}
        for r in found_total:
            unique_matches[r[0]] = r

        print("\n--- 繁殖判定対象馬レクト ---")
        match_count = 0
        for rid, rname, rraw, rrecord in unique_matches.values():
            # 繁殖牝馬判定ロジックの核: raw_name に特定の語が含まれるか
            is_broodmare_candidate = any(k in rraw for k in ['繁殖牝馬', '繫殖牝馬', '※繁殖牝馬', '※繫殖牝馬', '受胎', '空胎'])
            
            if is_broodmare_candidate:
                match_count += 1
                status = "STILL_JSON" if (rrecord and '{' in str(rrecord)) else str(rrecord)
                print(f"[{match_count}] ID: {rid}, Name: {rname}")
                print(f"    Raw: {rraw}")
                print(f"    Current Record Status: {status}")

        print(f"\nTotal Candidates filtered: {match_count}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_raw_name_variants_properly()
