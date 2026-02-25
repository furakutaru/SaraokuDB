import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('../.env')

def analyze_318_candidates():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in .env")
        return

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # 318頭を抽出した「元の」条件
        # (comment LIKE '%繁殖%' OR comment LIKE '%受胎%' OR comment LIKE '%空胎%')
        # AND (race_record IS NULL OR race_record != '繁殖牝馬')
        
        query = """
        SELECT id, name, race_record, comment 
        FROM horses 
        WHERE (comment LIKE '%繁殖%' OR comment LIKE '%受胎%' OR comment LIKE '%空胎%')
          AND (race_record IS NULL OR race_record != '繁殖牝馬');
        """
        cur.execute(query)
        rows = cur.fetchall()
        
        print(f"Total entries analyzed: {len(rows)}")
        print("-" * 50)
        
        # 分析：どのようなパターンがあるか
        patterns = {
            "just_broodmare": [], # 「繁殖牝馬」という単語が含まれる
            "stallion_context": [], # 他の馬（父馬など）の説明
            "medical": [], # 疾病名など
            "others": []
        }
        
        for row in rows:
            hid, name, record, comment = row
            if not comment: continue
            
            # 1. 繁殖牝馬自身のデータ（ポジティブパターン）
            if '繁殖牝馬' in comment:
                patterns["just_broodmare"].append(f"{name} (ID: {hid})")
            
            # 2. ネガティブパターン（誤検知の可能性）
            elif '種付け' in comment or '産駒' in comment or '種牡馬' in comment:
                patterns["stallion_context"].append(f"{name} (ID: {hid})")
            
            elif '繫靭帯' in comment or '繁殖力' in comment:
                 patterns["medical"].append(f"{name} (ID: {hid})")
            
            else:
                patterns["others"].append(f"{name} (ID: {hid})")
        
        print(f"分析結果:")
        print(f"- 『繁殖牝馬』という語を直接含む: {len(patterns['just_broodmare'])}件")
        print(f"- 種牡馬の説明文や産駒情報の文脈の可能性: {len(patterns['stallion_context'])}件")
        print(f"- 疾病（繫靭帯炎等）やその他の文脈: {len(patterns['medical'])}件")
        print(f"- その他（受胎/空胎のみ等）: {len(patterns['others'])}件")
        
        print("\n『繁殖牝馬』を直接含む馬のサンプル (先頭10件):")
        for s in patterns["just_broodmare"][:10]:
            print(f"  - {s}")
            
        print("\n誤検知の疑いがあるサンプルのコメント内容:")
        if patterns["stallion_context"]:
            cur.execute(f"SELECT comment FROM horses WHERE name = '{patterns['stallion_context'][0].split(' ')[0]}'")
            print(f"サンプル1: {cur.fetchone()[0][:150]}...")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_318_candidates()
