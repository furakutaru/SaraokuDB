import json
import traceback
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from database.models import Base, Horse, DATABASE_URL
from datetime import datetime
import os
import sys

# データベースエンジンを作成
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def print_table_info(engine):
    """Print information about tables in the database"""
    inspector = inspect(engine)
    print("\n=== Database Tables ===")
    for table_name in inspector.get_table_names():
        print(f"\nTable: {table_name}")
        print("Columns:")
        for column in inspector.get_columns(table_name):
            print(f"  {column['name']}: {column['type']}")

def import_horses():
    db = SessionLocal()
    
    # Print database schema info
    print("\n=== Database Schema ===")
    print_table_info(engine)
    
    # JSONファイルを読み込む
    json_path = '/Users/yum.ishii/SaraokuDB/static-frontend/public/data/horses.json'
    print(f"\nReading JSON file from: {json_path}")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            horses_data = json.load(f)
        print(f"Successfully loaded {len(horses_data)} horses from JSON file")
        
        # Print sample data
        print("\n=== Sample Data ===")
        print(json.dumps(horses_data[0], ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"Error loading JSON file: {str(e)}", file=sys.stderr)
        traceback.print_exc()
        db.close()
        return
    
    imported_count = 0
    error_count = 0
    
    try:
        print("\n=== Starting Data Import ===")
        for i, horse_data in enumerate(horses_data, 1):
            try:
                # データの前処理
                horse_id = int(horse_data.get('id'))
                if not horse_id:
                    print(f"Skipping record {i}: Invalid ID")
                    error_count += 1
                    continue
                
                # 画像URLの処理
                image_url = ''
                if isinstance(horse_data.get('image_url'), dict):
                    image_url = horse_data['image_url'].get('image_url', '')
                
                # 落札価格の処理
                sold_price = None
                if 'sold_price' in horse_data and horse_data['sold_price'] is not None:
                    sold_price = json.dumps([str(horse_data['sold_price'])])
                
                # 販売者の処理
                seller = json.dumps([horse_data.get('seller', '')]) if 'seller' in horse_data else '[]'
                
                # 賞金の処理
                prize_money = None
                if isinstance(horse_data.get('prize_money'), dict) and 'total_prize' in horse_data['prize_money']:
                    prize_money = float(horse_data['prize_money']['total_prize'])
                
                # 詳細URLから楽天オークションのURLを生成
                detail_url = horse_data.get('detail_url', '')
                rakuten_url = ''
                if 'auction.keiba.rakuten.co.jp' in detail_url:
                    rakuten_url = detail_url
                
                # オークション日付の処理
                auction_date = horse_data.get('auction_date')
                if auction_date and not isinstance(auction_date, str):
                    auction_date = str(auction_date)
                
                # 馬のデータを作成
                horse = Horse(
                    id=horse_id,
                    auction_id=horse_data.get('auction_id'),
                    name=horse_data.get('name', ''),
                    sex=json.dumps([horse_data.get('sex')]) if 'sex' in horse_data else '[]',
                    age=json.dumps([horse_data.get('age')]) if 'age' in horse_data else '[]',
                    sire=horse_data.get('sire', ''),
                    dam=horse_data.get('dam', ''),
                    dam_sire=horse_data.get('damsire', ''),
                    image_url=image_url,
                    jbis_url=horse_data.get('jbis_url', ''),
                    detail_url=detail_url,
                    rakuten_url=rakuten_url,  # 楽天オークションURLを追加
                    weight=horse_data.get('weight'),
                    race_record=json.dumps(horse_data.get('race_records', {})),
                    total_prize_start=float(horse_data.get('total_prize_start', 0)),
                    total_prize_latest=prize_money,
                    sold_price=sold_price or '[]',
                    auction_date=json.dumps([auction_date]) if auction_date else '[]',
                    seller=seller,
                    disease_tags=json.dumps(horse_data.get('disease_tags', [])),
                    comment=horse_data.get('comment', ''),
                    created_at=datetime.utcnow(),
                )
                
                # 既存のレコードを確認
                existing_horse = db.query(Horse).filter(Horse.id == horse_id).first()
                if existing_horse:
                    # 既存のレコードを更新
                    for key, value in horse.__dict__.items():
                        if not key.startswith('_') and hasattr(existing_horse, key):
                            # 既存の値が空でない場合は上書きしない（空の場合は上書き）
                            if key in ['jbis_url', 'detail_url', 'rakuten_url'] and getattr(existing_horse, key, None):
                                continue
                            setattr(existing_horse, key, value)
                    existing_horse.updated_at = datetime.utcnow()
                else:
                    # 新しいレコードを追加
                    db.add(horse)
                
                # 100件ごとにコミット
                    db.commit()
                    print(f"Processed {i} records...")
                
                imported_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"\nError processing record {i} (ID: {horse_data.get('id')}): {str(e)}")
                traceback.print_exc()
                db.rollback()
        
        # 最終コミット
        db.commit()
        
        # 結果を表示
        print("\n=== Import Summary ===")
        print(f"Total records processed: {len(horses_data)}")
        print(f"Successfully imported: {imported_count}")
        print(f"Errors: {error_count}")
        
        # インポートしたデータを表示
        print("\n=== Sample Imported Data ===")
        with engine.connect() as conn:
            result = conn.execute("SELECT id, name, seller FROM horses ORDER BY id LIMIT 5")
            for row in result:
                print(f"ID: {row[0]}, 名前: {row[1]}")
    
    except Exception as e:
        print(f"\nFatal error during import: {str(e)}", file=sys.stderr)
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("データのインポートを開始します...")
    import_horses()
    print("データのインポートが完了しました。")
