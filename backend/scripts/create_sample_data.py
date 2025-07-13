#!/usr/bin/env python3
"""
テスト用サンプルデータ作成スクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.models import SessionLocal, Horse
from datetime import datetime, timedelta
import random

def create_sample_data():
    """サンプルデータを作成"""
    db = SessionLocal()
    
    try:
        # 既存データをクリア
        db.query(Horse).delete()
        db.commit()
        
        # サンプル馬データ
        sample_horses = [
            {
                'name': 'サクラエイシン',
                'sex': '牡',
                'age': 3,
                'sire': 'ディープインパクト',
                'dam': 'サクラエイシン',
                'dam_sire': 'サクラチトセオー',
                'race_record': '5戦2勝［2-1-0-2］',
                'weight': 456,
                'total_prize_start': 120.5,
                'total_prize_latest': 180.2,
                'sold_price': 15000000,
                'auction_date': '2024-01-15',
                'seller': '社台レースホース',
                'disease_tags': '喉頭片麻痺',
                'comment': '本馬は優秀な血統を持ち、競走能力も高い。調教も順調で、今後の活躍が期待される。',
                'netkeiba_url': 'https://db.netkeiba.com/horse/2020101234/',
                'primary_image': 'https://keiba.r10s.jp/auction/data/item/1/240115_horse_01/240115_horse_01_bt.jpg',
                'created_at': datetime.now() - timedelta(days=30),
                'updated_at': datetime.now()
            },
            {
                'name': 'トウカイテイオー',
                'sex': '牝',
                'age': 4,
                'sire': 'ロードカナロア',
                'dam': 'トウカイテイオー',
                'dam_sire': 'トウカイテイオー',
                'race_record': '8戦3勝［3-2-1-2］',
                'weight': 442,
                'total_prize_start': 85.3,
                'total_prize_latest': 95.7,
                'sold_price': 8500000,
                'auction_date': '2024-01-15',
                'seller': 'ノースヒルズ',
                'disease_tags': '',
                'comment': '安定した走りを見せる牝馬。距離適性も広く、様々なレースで活躍できる。',
                'netkeiba_url': 'https://db.netkeiba.com/horse/2020105678/',
                'primary_image': 'https://keiba.r10s.jp/auction/data/item/1/240115_horse_02/240115_horse_02_bt.jpg',
                'created_at': datetime.now() - timedelta(days=30),
                'updated_at': datetime.now()
            },
            {
                'name': 'オグリキャップ',
                'sex': '牡',
                'age': 3,
                'sire': 'キングカメハメハ',
                'dam': 'オグリキャップ',
                'dam_sire': 'オグリキャップ',
                'race_record': '6戦1勝［1-2-1-2］',
                'weight': 468,
                'total_prize_start': 45.2,
                'total_prize_latest': 52.8,
                'sold_price': 5500000,
                'auction_date': '2024-01-22',
                'seller': 'サンデーレーシング',
                'disease_tags': '脚部不安',
                'comment': '脚部に不安があるが、能力は高い。適切な管理により活躍の可能性がある。',
                'netkeiba_url': 'https://db.netkeiba.com/horse/2020111111/',
                'primary_image': 'https://keiba.r10s.jp/auction/data/item/1/240122_horse_01/240122_horse_01_bt.jpg',
                'created_at': datetime.now() - timedelta(days=20),
                'updated_at': datetime.now()
            },
            {
                'name': 'シンボリルドルフ',
                'sex': '牡',
                'age': 4,
                'sire': 'ディープインパクト',
                'dam': 'シンボリルドルフ',
                'dam_sire': 'シンボリルドルフ',
                'race_record': '10戦4勝［4-3-1-2］',
                'weight': 450,
                'total_prize_start': 200.1,
                'total_prize_latest': 280.5,
                'sold_price': 25000000,
                'auction_date': '2024-01-22',
                'seller': 'シンボリ牧場',
                'disease_tags': '',
                'comment': '優秀な成績を残している実力馬。血統も良く、繁殖馬としても期待される。',
                'netkeiba_url': 'https://db.netkeiba.com/horse/2020123456/',
                'primary_image': 'https://keiba.r10s.jp/auction/data/item/1/240122_horse_02/240122_horse_02_bt.jpg',
                'created_at': datetime.now() - timedelta(days=20),
                'updated_at': datetime.now()
            },
            {
                'name': 'メジロマックイーン',
                'sex': '牝',
                'age': 3,
                'sire': 'ロードカナロア',
                'dam': 'メジロマックイーン',
                'dam_sire': 'メジロマックイーン',
                'race_record': '7戦2勝［2-2-1-2］',
                'weight': 438,
                'total_prize_start': 75.8,
                'total_prize_latest': 88.3,
                'sold_price': 7200000,
                'auction_date': '2024-01-29',
                'seller': 'メジロ牧場',
                'disease_tags': '関節炎',
                'comment': '関節炎の既往があるが、現在は安定している。適切な管理により競走生活を続けられる。',
                'netkeiba_url': 'https://db.netkeiba.com/horse/2020135790/',
                'primary_image': 'https://keiba.r10s.jp/auction/data/item/1/240129_horse_01/240129_horse_01_bt.jpg',
                'created_at': datetime.now() - timedelta(days=10),
                'updated_at': datetime.now()
            }
        ]
        
        # データベースに保存
        for horse_data in sample_horses:
            horse = Horse(**horse_data)
            db.add(horse)
        
        db.commit()
        print(f"✅ {len(sample_horses)}頭のサンプルデータを作成しました")
        
    except Exception as e:
        print(f"❌ サンプルデータの作成に失敗: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data() 