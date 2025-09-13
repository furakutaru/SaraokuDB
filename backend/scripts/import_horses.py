import json
import sqlite3
from datetime import datetime
from pathlib import Path

def import_horses():
    # データベースのパス
    db_path = Path(__file__).parent.parent / 'data' / 'horses.db'
    
    # フロントエンドのhorses.jsonのパス
    json_path = Path(__file__).parent.parent.parent / 'frontend' / 'public' / 'data' / 'horses.json'
    
    # データベースに接続
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 既存のデータを削除（必要に応じてコメントアウト）
    cursor.execute("DELETE FROM horses")
    
    # horses.jsonを読み込む
    with open(json_path, 'r', encoding='utf-8') as f:
        horses = json.load(f)
    
    # 現在の日時を取得
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    
    # 各馬のデータをデータベースに挿入
    for horse in horses:
        # 必須フィールドの確認
        if 'name' not in horse:
            print(f"Skipping horse with missing name: {horse}")
            continue
        
        # オークション履歴を処理
        history = horse.get('history', [])
        auction_dates = []
        sold_prices = []
        sellers = []
        
        for entry in history:
            auction_dates.append(entry.get('auction_date', ''))
            sold_prices.append(entry.get('sold_price'))
            sellers.append(entry.get('seller', ''))
        
        # 馬の基本情報を準備
        horse_data = {
            'name': horse['name'],
            'sex': json.dumps([horse.get('sex', '')]),
            'age': json.dumps([horse.get('age', 0)]),
            'sire': horse.get('sire', ''),
            'dam': horse.get('dam', ''),
            'dam_sire': horse.get('damsire', horse.get('dam_sire', '')),
            'race_record': json.dumps(horse.get('race_record', '')),
            'weight': horse.get('weight'),
            'total_prize_start': horse.get('total_prize_start', 0.0),
            'total_prize_latest': horse.get('total_prize_latest', 0.0),
            'sold_price': json.dumps(sold_prices) if sold_prices else None,
            'auction_date': json.dumps(auction_dates) if auction_dates else None,
            'seller': json.dumps(sellers) if sellers else None,
            'disease_tags': json.dumps(horse.get('disease_tags', [])),
            'comment': json.dumps([entry.get('comment', '') for entry in history] if history else ''),
            'image_url': horse.get('image_url', ''),
            'primary_image': horse.get('primary_image', ''),
            'unsold_count': horse.get('unsold_count', 0),
            'created_at': horse.get('created_at', now),
            'updated_at': now
        }
        
        # データベースに挿入
        columns = ', '.join(horse_data.keys())
        placeholders = ', '.join(['?'] * len(horse_data))
        query = f"INSERT INTO horses ({columns}) VALUES ({placeholders})"
        
        try:
            cursor.execute(query, list(horse_data.values()))
            print(f"Imported: {horse['name']}")
        except sqlite3.IntegrityError as e:
            print(f"Error importing {horse['name']}: {e}")
    
    # 変更をコミット
    conn.commit()
    conn.close()
    print("Import completed!")

if __name__ == "__main__":
    import_horses()
