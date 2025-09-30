#!/usr/bin/env python3
"""
スクレイピング結果をデータベースに反映するスクリプト
"""
import os
import sys
import json
from datetime import datetime

# プロジェクトのルートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.models import SessionLocal, Horse, Base
from sqlalchemy import create_engine

def load_json_data(file_path):
    """JSONファイルを読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def init_db():
    """データベースを初期化する"""
    # データベースのパスを設定
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend/data/horses.db')
    db_uri = f'sqlite:///{db_path}'
    
    # エンジンを作成
    engine = create_engine(db_uri)
    
    # テーブルが存在しない場合は作成
    Base.metadata.create_all(engine)
    
    # セッションを作成して返す
    Session = SessionLocal
    return Session()

def update_database(session, horses_data):
    """データベースを更新する"""
    try:
        updated_count = 0
        created_count = 0
        
        for horse_data in horses_data:
            # 既存のデータを検索
            horse = session.query(Horse).filter_by(
                auction_id=str(horse_data.get('id', horse_data.get('auction_id', '')))
            ).first()
            
            # 必要なフィールドを準備
            horse_dict = {
                'auction_id': str(horse_data.get('id', horse_data.get('auction_id', ''))),
                'name': horse_data.get('name', ''),
                'sex': json.dumps([horse_data.get('sex', '')]),
                'age': horse_data.get('age'),
                'sire': horse_data.get('sire', ''),
                'dam': horse_data.get('dam', ''),
                'dam_sire': horse_data.get('dam_sire', horse_data.get('damsire', '')),
                'race_record': json.dumps(horse_data.get('race_record', horse_data.get('race_records', {}))),
                'weight': horse_data.get('weight'),
                'total_prize_start': horse_data.get('total_prize_start'),
                'total_prize_latest': horse_data.get('total_prize_latest'),
                'sold_price': json.dumps([horse_data.get('sold_price')]) if 'sold_price' in horse_data else None,
                'auction_date': json.dumps([horse_data.get('auction_date')]) if 'auction_date' in horse_data else None,
                'seller': json.dumps([horse_data.get('seller', '')]),
                'disease_tags': json.dumps(horse_data.get('disease_tags', [])),
                'comment': json.dumps([horse_data.get('comment', '')]),
                'image_url': horse_data.get('image_url', {}).get('image_url', '') if isinstance(horse_data.get('image_url'), dict) else horse_data.get('image_url', ''),
                'primary_image': horse_data.get('primary_image', ''),
                'updated_at': datetime.utcnow()
            }
            
            if horse:
                # 既存のデータを更新
                for key, value in horse_dict.items():
                    setattr(horse, key, value)
                updated_count += 1
            else:
                # 新しいデータを作成
                horse = Horse(**horse_dict)
                session.add(horse)
                created_count += 1
        
        # 変更をコミット
        session.commit()
        print(f"データベースを更新しました。新規: {created_count}件, 更新: {updated_count}件")
        
    except Exception as e:
        session.rollback()
        print(f"エラーが発生しました: {str(e)}")
        raise

def main():
    """メイン処理"""
    # JSONファイルのパス
    json_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static-frontend', 'public', 'data', 'horses.json'
    )
    
    if not os.path.exists(json_file):
        print(f"エラー: {json_file} が見つかりません。")
        return 1
    
    try:
        # JSONデータを読み込む
        print(f"ファイルを読み込んでいます: {json_file}")
        horses_data = load_json_data(json_file)
        
        # データベースを初期化
        print("データベースに接続しています...")
        session = init_db()
        
        # データベースを更新
        print("データベースを更新しています...")
        update_database(session, horses_data)
        
        print("処理が完了しました。")
        return 0
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
