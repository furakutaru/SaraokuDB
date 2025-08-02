"""
データ操作のためのヘルパー関数群
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import uuid

def load_json_file(file_path: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """JSONファイルを読み込む
    
    Returns:
        Union[Dict[str, Any], List[Dict[str, Any]]]: 
            - 新しい形式の場合は辞書 {'metadata': ..., 'horses': [...]}
            - 古い形式の場合は馬のリスト [...]
            - エラーの場合は空のリスト []
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 新しい形式かどうかをチェック
                if isinstance(data, dict) and 'horses' in data:
                    return data
                return data  # 古い形式の場合はそのまま返す
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading {file_path}: {e}")
    return []

def save_json_file(file_path: str, data: Any) -> None:
    """JSONファイルにデータを保存する
    
    Args:
        file_path: 保存先のファイルパス
        data: 保存するデータ（リストまたは辞書）
    """
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
    """馬情報を保存し、馬IDを返す
    
    Args:
        horse_data: 保存する馬情報の辞書
        data_dir: データディレクトリのパス
        
    Returns:
        str: 馬の一意識別子（UUID）
        
    Raises:
        ValueError: 必須フィールドが不足している場合
    """
    horses_file = os.path.join(data_dir, 'horses.json')
    data = load_json_file(horses_file)
    
    # 古い形式の場合は新しい形式に変換
    if isinstance(data, list):
        data = {
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "total_horses": len(data),
                "version": "1.0.0"
            },
            "horses": data
        }
    
    horses = data.get('horses', [])
    
    # 必須フィールドのバリデーション
    required_fields = ['name', 'age', 'sex', 'sire', 'dam', 'damsire']
    for field in required_fields:
        if field not in horse_data or not horse_data[field]:
            print(f"警告: 必須フィールドが不足しています: {field} (馬名: {horse_data.get('name', '不明')})")
            horse_data[field] = ''  # 空文字で初期化
    
    # 既存の馬を検索
    existing_horse = find_horse_by_name_and_age(
        horses, horse_data['name'], horse_data['age']
    )
    
    now = datetime.now().isoformat()
    horse_id = None
    
    if existing_horse:
        # 既存の馬情報を更新
        if 'id' not in existing_horse:
            existing_horse['id'] = str(uuid.uuid4())
            
        horse_id = existing_horse['id']
        
        # 更新するフィールドをマージ
        update_fields = {
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
            'updated_at': now,
            # 賞金情報を明示的にマージ（0の場合も含む）
            'total_prize_start': horse_data.get('total_prize_start', existing_horse.get('total_prize_start', 0)),
            'total_prize_latest': horse_data.get('total_prize_latest', existing_horse.get('total_prize_latest', 0))
        }
        
        # その他の重要なフィールドもマージ
        for key in ['comment', 'race_record', 'weight', 'seller', 'auction_date']:
            if key in horse_data:
                update_fields[key] = horse_data[key]
        
        # 既存の馬情報を更新
        existing_horse.update(update_fields)
    else:
        # 新規の馬を追加
        horse_id = str(uuid.uuid4())
        # 必要なフィールドを確実に含める
        new_horse = {
            'id': horse_id,
            'name': horse_data['name'],
            'age': horse_data['age'],
            'total_prize_start': float(horse_data.get('total_prize_start', 0.0)),
            'total_prize_latest': float(horse_data.get('total_prize_latest', 0.0)),
            'sex': horse_data.get('sex', ''),
            'sire': horse_data.get('sire', ''),
            'dam': horse_data.get('dam', ''),
            'damsire': horse_data.get('damsire', ''),
            'image_url': horse_data.get('image_url', ''),
            'jbis_url': horse_data.get('jbis_url', ''),
            'auction_url': horse_data.get('auction_url', ''),
            'disease_tags': horse_data.get('disease_tags', []),
            'total_prize_start': horse_data.get('total_prize_start', 0),
            'total_prize_latest': horse_data.get('total_prize_latest', 0),
            'comment': horse_data.get('comment', ''),
            'race_record': horse_data.get('race_record', ''),
            'weight': horse_data.get('weight', ''),
            'seller': horse_data.get('seller', ''),
            'auction_date': horse_data.get('auction_date', ''),
            'created_at': now,
            'updated_at': now
        }
        horses.append(new_horse)
    
    # メタデータを更新
    data['metadata'] = {
        'last_updated': now,
        'total_horses': len(horses),
        'version': data.get('metadata', {}).get('version', '1.1.0')  # バージョンを更新
    }
    
    # ファイルに保存
    save_json_file(horses_file, data)
    return horse_id

def save_auction_history(history_data: Dict[str, Any], data_dir: str = 'static-frontend/public/data') -> bool:
    """オークション履歴を保存し、成功可否を返す
    
    Args:
        history_data: 保存するオークション履歴データ
        data_dir: データディレクトリのパス
        
    Returns:
        bool: 保存が成功したかどうか
        
    Raises:
        ValueError: 必須フィールドが不足している場合
    """
    history_file = os.path.join(data_dir, 'auction_history.json')
    history = load_json_file(history_file)
    
    # 必須フィールドのバリデーション
    required_fields = ['horse_id', 'auction_date']
    missing_fields = [field for field in required_fields if field not in history_data]
    if missing_fields:
        raise ValueError(f"必須フィールドが不足しています: {', '.join(missing_fields)}. 受信データ: {history_data}")
    
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
