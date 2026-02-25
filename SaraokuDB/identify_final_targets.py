import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('../.env')

def identify_final_targets():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in .env")
        return

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # 繁殖牝馬関連のキーワード（バリアント含む）
        keywords = ['繫殖牝馬', '繫殖牝', '受胎', '空胎']
        
        targets = []
        
        for kw in keywords:
            query = f"""
            SELECT id, name, race_record, comment 
            FROM horses 
            WHERE (name LIKE '%{kw}%' OR race_record LIKE '%{kw}%' OR comment LIKE '%{kw}%')
              AND (race_record IS NULL OR race_record != '繁殖牝馬');
            """
            cur.execute(query)
            rows = cur.fetchall()
            for row in rows:
                hid, name, record, comment = row
                
                # 種牡馬の解説っぽいものは除外（簡易フィルタ）
                # 通常、繁殖牝馬自身のデータには「母であり」「自身も」「オークション」などの言葉が含まれるか、単に「繫殖牝馬」とある
                # 解説文は「初年度は150頭を...」のようなものが多い
                is_stallion_desc = False
                if comment:
                    if '初年度は' in comment and '種付け' in comment:
                        is_stallion_desc = True
                    if '種牡馬として' in comment and '繫養' in comment:
                        is_stallion_desc = True
                
                if not is_stallion_desc:
                    targets.append({"id": hid, "name": name, "reason": kw, "record": record})
        
        # IDの重複を除去
        seen_ids = set()
        final_targets = []
        for t in targets:
            if t["id"] not in seen_ids:
                final_targets.append(t)
                seen_ids.add(t["id"])
                
        # ナツハヨルが漏れていないか個別に確認
        cur.execute("SELECT id, name, race_record, comment FROM horses WHERE name = 'ナツハヨル'")
        row = cur.fetchone()
        if row and row[0] not in seen_ids:
             # ナツハヨルのコメントを詳しくチェック（なぜキーワード検索にかからなかったか）
             # 文字列の完全一致などを確認
             final_targets.append({"id": row[0], "name": row[1], "reason": "Manually checked (ナツハヨル)", "record": row[2]})

        print(f"FINAL_TARGET_COUNT: {len(final_targets)}")
        for t in final_targets:
            print(f"ID: {t['id']}, Name: {t['name']}, Current Record: {t['record']}, Match: {t['reason']}")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    identify_final_targets()
