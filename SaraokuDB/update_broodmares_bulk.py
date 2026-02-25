import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('../.env')

def update_broodmares_bulk():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found")
        return

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # 更新対象を抽出するキーワード
        keywords = ['繁殖牝馬', '繫殖牝馬', '※繁殖牝馬', '※繫殖牝馬', '受胎', '空胎']
        
        # 対象IDを取得
        target_ids = set()
        for kw in keywords:
            cur.execute(f"SELECT id FROM horses WHERE raw_name LIKE '%{kw}%'")
            for r in cur.fetchall():
                target_ids.add(r[0])
        
        if not target_ids:
            print("No horses found to update.")
            return

        print(f"Total horses to update: {len(target_ids)}")
        
        # 更新クエリ実行
        # race_record を文字列 '繁殖牝馬' に、is_broodmare を TRUE に更新
        # is_broodmare カラムが存在することを前提とする
        update_query = """
        UPDATE horses 
        SET race_record = '繁殖牝馬',
            is_broodmare = TRUE
        WHERE id = %s;
        """
        
        updated_count = 0
        for hid in target_ids:
            cur.execute(update_query, (hid,))
            updated_count += 1
            
        conn.commit()
        print(f"Successfully updated {updated_count} horses.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    update_broodmares_bulk()
