#!/usr/bin/env python3
"""
シンプルなデータ移行スクリプト

horses.jsonとauction_history.jsonを統合し、新しい形式で保存します。
"""
import json
import os
from datetime import datetime

def load_json(file_path):
    """JSONファイルを読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, file_path):
    """データをJSONファイルに保存する"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def create_backup(file_path):
    """ファイルのバックアップを作成する"""
    if not os.path.exists(file_path):
        return
        
    backup_path = f"{file_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
    import shutil
    shutil.copy2(file_path, backup_path)
    print(f"バックアップを作成しました: {backup_path}")

def migrate_data(horses_data, auction_data):
    """データを新しい形式に変換する"""
    # オークションデータを馬IDでグループ化
    auction_by_horse = {}
    for auction in auction_data:
        horse_id = auction.get('horse_id')
        if horse_id:
            if horse_id not in auction_by_horse:
                auction_by_horse[horse_id] = []
            auction_by_horse[horse_id].append(auction)
    
    # 馬データを変換
    new_data = {
        'metadata': {
            'version': '1.0',
            'last_updated': datetime.now().isoformat(),
            'total_horses': len(horses_data)
        },
        'horses': []
    }
    
    for horse in horses_data:
        horse_id = horse.get('id')
        
        # 新しい形式の馬データを作成
        new_horse = {
            'id': horse_id,
            'basic_info': {
                'name': horse.get('name', ''),
                'sex': horse.get('sex', ''),
                'age': horse.get('age'),
                'sire': horse.get('sire', ''),
                'dam': horse.get('dam', ''),
                'damsire': horse.get('damsire', '')
            },
            'race_records': {
                'total_prize_money': horse.get('total_prize_money', 0)
            },
            'auction_history': []
        }
        
        # オークション履歴を追加
        if horse_id in auction_by_horse:
            for auction in auction_by_horse[horse_id]:
                new_auction = {
                    'date': auction.get('auction_date'),
                    'price': auction.get('sold_price'),
                    'weight': auction.get('weight'),
                    'seller': auction.get('seller', ''),
                    'is_unsold': auction.get('is_unsold', False)
                }
                new_horse['auction_history'].append(new_auction)
        
        new_data['horses'].append(new_horse)
    
    return new_data

def main():
    # ファイルパス
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    horses_path = os.path.join(base_dir, 'static-frontend', 'public', 'data', 'horses.json')
    auction_path = os.path.join(base_dir, 'static-frontend', 'public', 'data', 'auction_history.json')
    output_path = os.path.join(base_dir, 'static-frontend', 'public', 'data', 'horses_combined.json')
    
    # バックアップを作成
    create_backup(horses_path)
    create_backup(auction_path)
    
    # データを読み込む
    print("データを読み込んでいます...")
    horses_data = load_json(horses_path)
    auction_data = load_json(auction_path)
    
    # 古い形式のデータをサポート
    if isinstance(horses_data, dict) and 'horses' in horses_data:
        horses_data = horses_data['horses']
    
    # データを変換
    print("データを変換しています...")
    new_data = migrate_data(horses_data, auction_data)
    
    # 結果を保存
    print(f"結果を保存しています: {output_path}")
    save_json(new_data, output_path)
    
    print("\n完了しました！")
    print(f"処理した馬の数: {len(new_data['horses'])}")
    print(f"出力先: {output_path}")

if __name__ == "__main__":
    main()
