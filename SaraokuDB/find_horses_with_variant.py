import os
import psycopg2
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv('../.env')

def find_detailed_variant_horses():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in .env")
        return

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # 「繫」を含む馬を詳細に検索
        query = """
        SELECT id, name, race_record, comment 
        FROM horses 
        WHERE name LIKE '%繫%' 
           OR race_record LIKE '%繫%' 
           OR comment LIKE '%繫%'
           OR name = 'ナツハヨル';
        """
        
        cur.execute(query)
        rows = cur.fetchall()
        
        print(f"FOUND_COUNT: {len(rows)}")
        print("-" * 50)
        
        for row in rows:
            id, name, race_record, comment = row
            is_variant = False
            match_locations = []
            
            if name and '繫' in name:
                is_variant = True
                match_locations.append(f"name: {name}")
            
            if race_record and '繫' in str(race_record):
                is_variant = True
                # race_recordがJSONの場合は文字列に
                record_str = str(race_record)
                start = max(0, record_str.find('繫') - 20)
                end = min(len(record_str), record_str.find('繫') + 20)
                match_locations.append(f"race_record: ...{record_str[start:end]}...")
            
            if comment and '繫' in comment:
                is_variant = True
                start = max(0, comment.find('繫') - 30)
                end = min(len(comment), comment.find('繫') + 30)
                match_locations.append(f"comment: ...{comment[start:end]}...")
            
            if name == 'ナツハヨル':
                print(f"TARGET: ナツハヨル (ID: {id})")
                print(f"  Current Race Record: {race_record}")
                if not is_variant:
                    print("  Note: '繫' not found in this record (maybe it matched '繁' before or used for testing)")
            
            if is_variant:
                print(f"ID: {id}, Name: {name}")
                for loc in match_locations:
                    print(f"  Match in {loc}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_detailed_variant_horses()
