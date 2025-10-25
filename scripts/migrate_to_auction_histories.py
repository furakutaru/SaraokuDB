#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from pathlib import Path

# 環境変数の読み込み
def load_environment():
    """環境変数を読み込む"""
    # スクリプトのルートディレクトリを取得
    root_dir = Path(__file__).parent.parent
    
    # .envファイルのパスを設定
    env_path = root_dir / 'backend' / '.env'
    
    if env_path.exists():
        load_dotenv(env_path, override=True)
        print(f"環境変数を読み込みました: {env_path}")
    else:
        print(f"警告: .envファイルが見つかりません: {env_path}")
        print("環境変数が設定されていることを確認してください。")

def get_db_connection_string():
    """環境変数からデータベース接続文字列を取得"""
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME")
    
    if not all([db_user, db_password, db_name]):
        raise ValueError("データベース接続情報が不足しています。.envファイルを確認してください。")
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require"

def migrate_to_auction_histories():
    """horsesテーブルからauction_historiesテーブルにデータを移行する"""
    # データベース接続設定
    try:
        db_url = get_db_connection_string()
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("データベースに接続しました")
        
        # 既存の馬データを取得（オークション履歴があるもののみ）
        print("オークション履歴がある馬データを取得しています...")
        # クエリを実行して結果を取得
        result = db.execute(
            text("""
                SELECT id, name, sire, dam, dam_sire, sold_price, auction_date, 
                       seller, detail_url
                FROM horses
                WHERE sold_price IS NOT NULL AND auction_date IS NOT NULL
            """)
        )
        # カラム名を明示的に指定して辞書形式で取得し、JSON配列から最初の値を取得
        import json
        columns = [column[0] for column in result.cursor.description]
        horses = []
        for row in result.fetchall():
            horse = dict(zip(columns, row))
            # JSON配列から最初の値を取得
            if isinstance(horse.get('sold_price'), str) and horse['sold_price'].startswith('['):
                try:
                    horse['sold_price'] = json.loads(horse['sold_price'])[0]
                except (json.JSONDecodeError, IndexError):
                    horse['sold_price'] = None
            if isinstance(horse.get('auction_date'), str) and horse['auction_date'].startswith('['):
                try:
                    horse['auction_date'] = json.loads(horse['auction_date'])[0]
                except (json.JSONDecodeError, IndexError):
                    horse['auction_date'] = None
            if isinstance(horse.get('seller'), str) and horse['seller'].startswith('['):
                try:
                    horse['seller'] = json.loads(horse['seller'])[0]
                except (json.JSONDecodeError, IndexError):
                    horse['seller'] = '不明'
            horses.append(horse)
        
        if not horses:
            print("オークション履歴がある馬データは見つかりませんでした。")
            return
            
        print(f"{len(horses)}件の馬データを取得しました。移行を開始します...")
        
        migrated_count = 0
        skipped_count = 0
        
        for i, horse in enumerate(horses, 1):
            try:
                # 同じ馬で同じ日付のオークション履歴が既に存在するかチェック
                existing = db.execute(
                    text("""
                        SELECT 1 FROM auction_histories 
                        WHERE horse_name = :horse_name
                        AND sire_name = :sire_name
                        AND dam_name = :dam_name
                        AND damsire_name = :damsire_name
                        AND auction_date = :auction_date
                        LIMIT 1
                    """),
                    {
                        'horse_name': horse['name'],
                        'sire_name': horse.get('sire'),
                        'dam_name': horse.get('dam'),
                        'damsire_name': horse.get('dam_sire'),
                        'auction_date': horse['auction_date']
                    }
                ).scalar()
                
                if existing:
                    skipped_count += 1
                    print(f"[{i}/{len(horses)}] スキップ: 既存のオークション履歴が存在します - {horse.name} ({horse.auction_date})")
                    continue
                
                # 新しいオークション履歴レコードを作成
                db.execute(
                    text("""
                        INSERT INTO auction_histories (
                            horse_id, horse_name, sire_name, dam_name, damsire_name,
                            auction_date, price, seller, auction_house, auction_name,
                            lot_number, auction_url, created_at, updated_at
                        ) VALUES (
                            :horse_id, :horse_name, :sire_name, :dam_name, :damsire_name,
                            :auction_date, :price, :seller, :auction_house, :auction_name,
                            :lot_number, :auction_url, NOW(), NOW()
                        )
                    """),
                    {
                        'horse_id': horse['id'],
                        'horse_name': horse['name'],
                        'sire_name': horse['sire'],
                        'dam_name': horse['dam'],
                        'damsire_name': horse.get('dam_sire'),  # getメソッドを使用して安全にアクセス
                        'auction_date': horse['auction_date'],
                        'price': horse['sold_price'],
                        'seller': horse.get('seller', '不明'),  # デフォルト値を設定
                        'auction_house': '不明',  # 元のテーブルに存在しないためデフォルト値を設定
                        'auction_name': '不明',   # 元のテーブルに存在しないためデフォルト値を設定
                        'lot_number': None,  # 元のテーブルに存在しないためNoneを設定
                        'auction_url': horse.get('detail_url')
                    }
                )
                
                migrated_count += 1
                
                if migrated_count % 10 == 0:
                    db.commit()
                    print(f"[{i}/{len(horses)}] 移行中... {migrated_count}件処理しました")
            
            except Exception as e:
                db.rollback()
                print(f"[エラー] 馬ID {horse.get('id', '不明')} の移行中にエラーが発生しました: {str(e)}")
                continue
        
        db.commit()
        print(f"\n移行が完了しました。")
        print(f"合計: {len(horses)}件中 {migrated_count}件を移行、{skipped_count}件をスキップしました。")
        
    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}")
        if 'db' in locals():
            db.rollback()
    finally:
        if 'db' in locals():
            db.close()
            print("データベース接続を閉じました。")

if __name__ == "__main__":
    print("=== オークションデータ移行ツール ===")
    print("horsesテーブルからauction_historiesテーブルにデータを移行します。")
    
    # 環境変数の読み込み
    load_environment()
    
    # 移行の実行
    migrate_to_auction_histories()
    
    print("\n処理が完了しました。")
    print("注意: 移行が完了したら、アプリケーションを再起動して変更を反映してください。")
