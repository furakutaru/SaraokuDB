"""
データ操作のためのヘルパー関数群
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import uuid

def load_json_file(file_path: str) -> List[Dict[str, Any]]:
    """JSONファイルを読み込む"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    return []

def save_json_file(file_path: str, data: List[Dict[str, Any]]) -> None:
    """JSONファイルにデータを保存する"""
    # ディレクトリが存在しない場合は作成
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def find_horse_by_name_and_age(horses: List[Dict[str, Any]], name: str, age: int) -> Optional[Dict[str, Any]]:
    """名前と年齢で馬を検索"""
    for horse in horses:
        if horse.get('name') == name and horse.get('age') == age:
            return horse
    return None

def find_auction_history(history: List[Dict[str, Any]], horse_id: str, auction_date: str) -> Optional[Dict[str, Any]]:
    """馬IDとオークション日で履歴を検索"""
    for entry in history:
        if entry.get('horse_id') == horse_id and entry.get('auction_date') == auction_date:
            return entry
    return None

def merge_disease_tags(existing_tags: List[str], new_tags: List[str]) -> List[str]:
    """疾病タグをマージ（重複を削除）"""
    if not existing_tags:
        return list(set(new_tags))
    if not new_tags:
        return existing_tags
    return list(set(existing_tags + new_tags))

def save_horse(horse_data: Dict[str, Any], data_dir: str = 'static-frontend/public/data') -> str:
    """馬情報を保存し、馬IDを返す"""
    horses_file = os.path.join(data_dir, 'horses.json')
    horses = load_json_file(horses_file)
    
    # 必須フィールドのバリデーション
    required_fields = ['name', 'age']
    for field in required_fields:
        if field not in horse_data:
            raise ValueError(f"Missing required field: {field}")
    
    # 既存の馬を検索
    existing_horse = find_horse_by_name_and_age(
        horses, horse_data['name'], horse_data['age']
    )
    
    now = datetime.now().isoformat()
    
    if existing_horse:
        # 既存の馬情報を更新
        horse_id = existing_horse['id']
        existing_horse.update({
            'sire': horse_data.get('sire', existing_horse.get('sire', '')),
            'dam': horse_data.get('dam', existing_horse.get('dam', '')),
            'damsire': horse_data.get('damsire', existing_horse.get('damsire', '')),
            'sex': horse_data.get('sex', existing_horse.get('sex', '')),
            'image_url': horse_data.get('image_url', existing_horse.get('image_url', '')),
            'jbis_url': horse_data.get('jbis_url', existing_horse.get('jbis_url', '')),
            'auction_url': horse_data.get('auction_url', existing_horse.get('auction_url', '')),
            'disease_tags': merge_disease_tags(
                existing_horse.get('disease_tags', []),
                horse_data.get('disease_tags', [])
            ),
            'updated_at': now
        })
    else:
        # 新規の馬を追加
        horse_id = str(uuid.uuid4())
        horse_data.update({
            'id': horse_id,
            'created_at': now,
            'updated_at': now
        })
        # 空の配列をデフォルト値として設定
        if 'disease_tags' not in horse_data:
            horse_data['disease_tags'] = []
        horses.append(horse_data)
    
    # ファイルに保存
    save_json_file(horses_file, horses)
    return horse_id

def save_auction_history(history_data: Dict[str, Any], data_dir: str = 'static-frontend/public/data') -> bool:
    """オークション履歴を保存し、成功可否を返す"""
    history_file = os.path.join(data_dir, 'auction_history.json')
    history = load_json_file(history_file)
    
    # 必須フィールドのバリデーション
    required_fields = ['horse_id', 'auction_date']
    for field in required_fields:
        if field not in history_data:
            raise ValueError(f"Missing required field: {field}")
    
    # 重複チェック
    existing_entry = find_auction_history(
        history, history_data['horse_id'], history_data['auction_date']
    )
    
    now = datetime.now().isoformat()
    
    if existing_entry:
        # 既存の履歴を更新
        existing_entry.update({
            'sold_price': history_data.get('sold_price', existing_entry.get('sold_price')),
            'total_prize_start': history_data.get('total_prize_start', existing_entry.get('total_prize_start')),
            'total_prize_latest': history_data.get('total_prize_latest', existing_entry.get('total_prize_latest')),
            'weight': history_data.get('weight', existing_entry.get('weight')),
            'seller': history_data.get('seller', existing_entry.get('seller', '')),
            'is_unsold': history_data.get('is_unsold', existing_entry.get('is_unsold', False)),
            'comment': history_data.get('comment', existing_entry.get('comment', ''))
        })
    else:
        # 新しい履歴を追加
        history_data.update({
            'id': str(uuid.uuid4()),
            'created_at': now
        })
        history.append(history_data)
    
    # ファイルに保存
    save_json_file(history_file, history)
    return True
