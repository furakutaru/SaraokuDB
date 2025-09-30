#!/usr/bin/env python3
"""
馬データを新しい統合スキーマに移行するスクリプト

使用方法:
    python migrate_to_unified_schema.py <horses.jsonのパス> <auction_history.jsonのパス> <出力ファイルパス>
"""
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


def load_json_file(file_path: str) -> Any:
    """JSONファイルを読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data: Any, file_path: str):
    """データをJSONファイルに保存する"""
    # ディレクトリが存在しない場合は作成
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # 既存のファイルがあればバックアップを作成
    if os.path.exists(file_path):
        backup_path = f"{file_path}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
        os.rename(file_path, backup_path)
        print(f"バックアップを作成しました: {backup_path}")
    
    # 新しいファイルを保存
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"ファイルを保存しました: {file_path}")


def migrate_horse_data(horse_data: Dict, auction_data: List[Dict]) -> Dict:
    """馬データを新しいスキーマに変換する"""
    # オークション履歴を馬IDでグループ化
    auction_by_horse: Dict[str, List[Dict]] = {}
    for auction in auction_data:
        horse_id = auction.get('horse_id')
        if horse_id:
            if horse_id not in auction_by_horse:
                auction_by_horse[horse_id] = []
            auction_by_horse[horse_id].append(auction)
    
    # 馬データを変換
    migrated_horses = []
    for horse in horse_data:
        horse_id = horse.get('id')
        
        # 基本情報
        basic_info = {
            'name': horse.get('name', ''),
            'sex': horse.get('sex', ''),
            'age': horse.get('age'),
            'sire': horse.get('sire', ''),
            'dam': horse.get('dam', ''),
            'damsire': horse.get('damsire', ''),
            'is_retired': horse.get('is_retired', False),
            'retirement_date': horse.get('retirement_date')
        }
        
        # レース記録
        race_records = {
            'total_prize_money': horse.get('total_prize_money', 0),
            'last_race_date': horse.get('last_race_date'),
            'last_prize_update': horse.get('last_prize_update')
        }
        
        # オークション履歴
        auction_history = []
        if horse_id in auction_by_horse:
            for auction in sorted(auction_by_horse[horse_id], 
                                key=lambda x: x.get('auction_date', '')):
                auction_history.append({
                    'date': auction.get('auction_date'),
                    'price': auction.get('sold_price'),
                    'weight': auction.get('weight'),
                    'seller': auction.get('seller', ''),
                    'is_unsold': auction.get('is_unsold', False),
                    'comment': auction.get('comment', '')
                })
        
        # メタデータ
        metadata = {
            'created_at': horse.get('created_at') or datetime.now().isoformat(),
            'updated_at': horse.get('updated_at') or datetime.now().isoformat(),
            'data_source': 'jbis'
        }
        
        # 統合された馬データ
        migrated_horse = {
            'id': horse_id,
            'basic_info': basic_info,
            'race_records': race_records,
            'auction_history': auction_history,
            'metadata': metadata
        }
        
        migrated_horses.append(migrated_horse)
    
    return migrated_horses


def main():
    if len(sys.argv) != 4:
        print("エラー: 引数が正しくありません。")
        print("使用方法: python migrate_to_unified_schema.py <horses.jsonのパス> <auction_history.jsonのパス> <出力ファイルパス>")
        sys.exit(1)
    
    horses_path = sys.argv[1]
    auction_history_path = sys.argv[2]
    output_path = sys.argv[3]
    
    # 入力ファイルの存在確認
    for path in [horses_path, auction_history_path]:
        if not os.path.exists(path):
            print(f"エラー: ファイルが見つかりません: {path}")
            sys.exit(1)
    
    try:
        # データを読み込む
        print("データを読み込んでいます...")
        horses_data = load_json_file(horses_path)
        auction_data = load_json_file(auction_history_path)
        
        # 古い形式のデータをサポート（horsesがルートの配列か、オブジェクト内にhorsesプロパティがあるか）
        if isinstance(horses_data, dict) and 'horses' in horses_data:
            horses_list = horses_data['horses']
        else:
            horses_list = horses_data
        
        # データを移行
        print("データを移行しています...")
        migrated_data = {
            'metadata': {
                'version': '1.1',
                'last_updated': datetime.now().isoformat(),
                'scrape_status': {
                    'last_successful_scrape': datetime.now().isoformat(),
                    'next_scheduled_scrape': (datetime.now() + timedelta(days=1)).isoformat()
                },
                'total_horses': len(horses_list)
            },
            'horses': migrate_horse_data(horses_list, auction_data)
        }
        
        # 結果を保存
        print("結果を保存しています...")
        save_json_file(migrated_data, output_path)
        
        print(f"\n移行が完了しました: {output_path}")
        print(f"処理した馬の数: {len(horses_list)}")
        print(f"処理したオークション履歴の数: {len(auction_data)}")
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    from datetime import timedelta  # 循環インポートを避けるためにここでインポート
    main()
