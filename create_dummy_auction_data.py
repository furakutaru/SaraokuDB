import psycopg2
from datetime import datetime

def create_dummy_auction_data(db_url):
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    # horsesテーブルからIDを取得
    cursor.execute("SELECT id FROM horses;")
    horse_ids = [row[0] for row in cursor.fetchall()]
    
    # ダミーデータを生成して挿入
    for i, horse_id in enumerate(horse_ids, 1):
        cursor.execute("""
            INSERT INTO auction_histories (
                horse_id, auction_date, price, seller, buyer, 
                auction_house, auction_name, lot_number, auction_url,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            horse_id,  # horse_id
            '2025-10-25',  # auction_date
            1000000 + (i * 100000),  # price
            f'セラー{i}',  # seller
            f'バイヤー{i}',  # buyer
            'テスト競馬場',  # auction_house
            'テストオークション',  # auction_name
            i,  # lot_number
            f'https://example.com/auction/{i}',  # auction_url
            datetime.now(),  # created_at
            datetime.now()   # updated_at
        ))
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Inserted {len(horse_ids)} dummy records into auction_histories table")

if __name__ == "__main__":
    db_url = 'postgresql://neondb_owner:npg_PpdcmHfn73bl@ep-sweet-term-adm0rzzh-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require'
    create_dummy_auction_data(db_url)
