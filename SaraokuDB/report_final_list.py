import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('../.env')

def report_final_list():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in .env")
        return

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # 1. 「繫」 (U+7E6B) を含む馬で更新が必要そうなもの
        # 名前に「繫」を含む、またはコメントに「繫殖牝馬」を含むが race_record が '繁殖牝馬' ではない
        query = """
        SELECT id, name, comment 
        FROM horses 
        WHERE (comment LIKE '%繫殖牝馬%' OR comment LIKE '%繫殖牝%')
          AND (race_record IS NULL OR race_record != '繁殖牝馬');
        """
        cur.execute(query)
        rows = cur.fetchall()
        
        variant_targets = []
        for row in rows:
            hid, name, comment = row
            # 種牡馬等の説明を除外
            if comment and not ('初年度は' in comment and '種付け' in comment):
                variant_targets.append(f"{name} (ID: {hid})")
        
        # 2. ナツハヨルの状態
        cur.execute("SELECT id, name, race_record FROM horses WHERE name = 'ナツハヨル'")
        natsuhayoru = cur.fetchone()
        
        print("--- 調査レポート ---")
        print(f"1. 「繫」バリアントを含む更新対象候補: {len(variant_targets)}頭")
        for t in variant_targets:
            print(f"   - {t}")
            
        print(f"\n2. ナツハヨル (ID: {natsuhayoru[0] if natsuhayoru else 'N/A'})")
        print(f"   現在の戦績: {natsuhayoru[2] if natsuhayoru else 'N/A'}")
        
        # 3. その他、繁殖関連キーワードを含むが未更新の馬（参考）
        query_others = """
        SELECT COUNT(*) 
        FROM horses 
        WHERE (comment LIKE '%繁殖%' OR comment LIKE '%受胎%' OR comment LIKE '%空胎%')
          AND (race_record IS NULL OR race_record != '繁殖牝馬');
        """
        cur.execute(query_others)
        count_others = cur.fetchone()[0]
        print(f"\n3. その他の繁殖キーワード（繁体字含む）で未更新の候補: 約{count_others}頭")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    report_final_list()
