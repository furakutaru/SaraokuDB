import os
import sys
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# プロジェクトのルートディレクトリをシステムパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# データベースモデルをインポート
from backend.database.models import Base, Horse, engine, SessionLocal

def create_sample_horses():
    """サンプルの馬データを作成"""
    # 現在の日付を取得
    today = datetime.now().date()
    
    # サンプルデータ
    sample_horses = [
        {
            "name": "サクラバクシンオー",
            "sex": json.dumps(["牡"]),
            "age": json.dumps([3]),
            "sire": "キングカメハメハ",
            "dam": "サクラチトセオー",
            "dam_sire": "サクラユタカオー",
            "race_record": json.dumps({"1": "1-1-1-0", "2": "2-0-0-1"}),
            "weight": 480,
            "total_prize_start": 5000.0,
            "total_prize_latest": 12000.0,
            "sold_price": json.dumps([15000000]),
            "auction_date": json.dumps([(today - timedelta(days=30)).strftime("%Y-%m-%d")]),
            "seller": json.dumps(["社台ファーム"]),
            "disease_tags": "",
            "comment": json.dumps(["バランスの取れた馬体", "走りに伸びがある"]),
            "image_url": "https://example.com/horse1.jpg",
            "primary_image": "https://example.com/horse1_primary.jpg",
            "unsold_count": 0
        },
        {
            "name": "ダイワスカーレット",
            "sex": json.dumps(["牝"]),
            "age": json.dumps([4]),
            "sire": "ディープインパクト",
            "dam": "スカーレットブーケ",
            "dam_sire": "フレンチデピュティ",
            "race_record": json.dumps({"1": "1-2-0-1", "2": "3-1-0-0"}),
            "weight": 460,
            "total_prize_start": 8000.0,
            "total_prize_latest": 20000.0,
            "sold_price": json.dumps([25000000]),
            "auction_date": json.dumps([(today - timedelta(days=15)).strftime("%Y-%m-%d")]),
            "seller": json.dumps(["ノーザンファーム"]),
            "disease_tags": "",
            "comment": json.dumps(["気性が良く、素直な性格", "スタミナに定評あり"]),
            "image_url": "https://example.com/horse2.jpg",
            "primary_image": "https://example.com/horse2_primary.jpg",
            "unsold_count": 0
        },
        {
            "name": "キタサンブラック",
            "sex": json.dumps(["牡"]),
            "age": json.dumps([5]),
            "sire": "ブラックタイド",
            "dam": "サクラパワー",
            "dam_sire": "サクラユタカオー",
            "race_record": json.dumps({"1": "2-0-1-1", "2": "1-1-0-2"}),
            "weight": 500,
            "total_prize_start": 3000.0,
            "total_prize_latest": 10000.0,
            "sold_price": json.dumps([18000000]),
            "auction_date": json.dumps([(today - timedelta(days=7)).strftime("%Y-%m-%d")]),
            "seller": json.dumps(["社台ファーム"]),
            "disease_tags": "",
            "comment": json.dumps(["パワフルな走り", "スタミナ十分"]),
            "image_url": "https://example.com/horse3.jpg",
            "primary_image": "https://example.com/horse3_primary.jpg",
            "unsold_count": 0
        }
    ]
    
    return sample_horses

def insert_sample_data():
    """サンプルデータをデータベースに挿入"""
    # データベースセッションを作成
    db = SessionLocal()
    
    try:
        # サンプルデータを取得
        horses = create_sample_horses()
        
        # 各馬データをデータベースに追加
        for horse_data in horses:
            horse = Horse(**horse_data)
            db.add(horse)
        
        # 変更をコミット
        db.commit()
        print(f"{len(horses)}件のサンプルデータを挿入しました。")
        
    except Exception as e:
        # エラーが発生した場合はロールバック
        db.rollback()
        print(f"エラーが発生しました: {e}")
    finally:
        # セッションを閉じる
        db.close()

if __name__ == "__main__":
    print("サンプルデータをデータベースに挿入します...")
    insert_sample_data()
    print("完了しました。")
