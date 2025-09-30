import json
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Horse, get_db, SessionLocal
from datetime import datetime

def load_json_data(file_path):
    """JSONファイルを読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def init_db():
    """データベースを初期化する"""
    # セッションを取得
    db = SessionLocal()
    
    try:
        # テーブルが存在しない場合は作成
        Base.metadata.create_all(db.bind)
        return db
    except Exception as e:
        db.rollback()
        raise e

def import_horses(session, horses_data):
    """馬データをデータベースにインポートする"""
    try:
        # 既存のデータを削除
        deleted_count = session.query(Horse).delete()
        print(f"既存のデータ {deleted_count} 件を削除しました。")
        
        # 新しいデータを追加
        imported_count = 0
        for idx, horse_data in enumerate(horses_data, 1):
            # image_urlが辞書型の場合はURLを取得
            image_url = horse_data.get('image_url', '')
            if isinstance(image_url, dict):
                image_url = image_url.get('image_url', '')
            
            # 必要なフィールドを準備
            horse_dict = {
                'auction_id': str(horse_data.get('id', horse_data.get('auction_id', ''))),  # JSONのidまたはauction_idを使用
                'name': horse_data.get('name', ''),
                'sex': json.dumps([horse_data.get('sex', '')]),  # 性別を配列として保存
                'age': horse_data.get('age'),
                'sire': horse_data.get('sire', ''),
                'dam': horse_data.get('dam', ''),
                'dam_sire': horse_data.get('dam_sire', horse_data.get('damsire', '')),  # damsireも確認
                'race_record': json.dumps(horse_data.get('race_record', horse_data.get('race_records', {}))),
                'weight': horse_data.get('weight'),
                'total_prize_start': horse_data.get('total_prize_start'),
                'total_prize_latest': horse_data.get('total_prize_latest'),
                'sold_price': json.dumps([horse_data.get('sold_price')]) if 'sold_price' in horse_data else None,
                'auction_date': json.dumps([horse_data.get('auction_date')]) if 'auction_date' in horse_data else None,
                'seller': json.dumps([horse_data.get('seller', '')]),
                'disease_tags': json.dumps(horse_data.get('disease_tags', [])),
                'comment': json.dumps([horse_data.get('comment', '')]),
                'image_url': image_url,
                'primary_image': horse_data.get('primary_image', '')
            }
            
            # 馬オブジェクトを作成
            horse = Horse(**horse_dict)
            session.add(horse)
            
            # 進捗表示
            if idx % 100 == 0 or idx == len(horses_data):
                print(f"処理中: {idx}/{len(horses_data)} 件")
            
            # バッチコミット（1000件ごと）
            if idx % 1000 == 0:
                session.commit()
                print(f"{idx} 件をコミットしました。")
        
        # 残りの変更をコミット
        session.commit()
        print(f"合計 {len(horses_data)} 件の馬データをインポートしました。")
        return len(horses_data)
        
    except Exception as e:
        session.rollback()
        print(f"エラーが発生しました: {str(e)}")
        raise

if __name__ == '__main__':
    if len(sys.argv) < 2:
        # デフォルトで latest_horses.json を使用
        json_file = os.path.join(os.path.dirname(__file__), '../data/latest_horses.json')
        print(f"デフォルトのファイルを使用します: {json_file}")
    else:
        json_file = sys.argv[1]
    
    try:
        # JSONデータを読み込む
        print(f"ファイルを読み込んでいます: {json_file}")
        horses_data = load_json_data(json_file)
        
        # データベースを初期化
        print("データベースに接続しています...")
        session = init_db()
        
        # データをインポート
        print("データをインポートしています...")
        import_horses(session, horses_data)
        
        print("インポートが完了しました。")
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        sys.exit(1)
