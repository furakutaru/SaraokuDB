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
    try:
        # ディレクトリが存在しない場合は作成
        dir_path = os.path.dirname(file_path)
        print(f"[DEBUG] ディレクトリを作成: {dir_path}")
        os.makedirs(dir_path, exist_ok=True)
        
        print(f"[DEBUG] ファイルにデータを保存中: {file_path}")
        print(f"[DEBUG] データタイプ: {type(data)}")
        print(f"[DEBUG] データ内容の一部: {str(data)[:200]}...")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"[DEBUG] ファイル保存完了: {file_path}")
        print(f"[DEBUG] ファイルの存在確認: {os.path.exists(file_path)}")
        print(f"[DEBUG] ファイルサイズ: {os.path.getsize(file_path) if os.path.exists(file_path) else 0} バイト")
    except Exception as e:
        print(f"[ERROR] ファイル保存中にエラーが発生しました: {str(e)}")
        print(f"[ERROR] ファイルパス: {file_path}")
        print(f"[ERROR] データタイプ: {type(data)}")
        raise

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

def merge_disease_tags(existing_tags: Union[List[str], str, None], new_tags: Union[List[str], str, None]) -> List[str]:
    """疾病タグをマージ（重複を削除）
    
    Args:
        existing_tags: 既存のタグ（リストまたは文字列）
        new_tags: 新しいタグ（リストまたは文字列）
        
    Returns:
        List[str]: マージされたユニークなタグのリスト
    """
    # 既存のタグをリストに変換
    if not existing_tags:
        existing_list = []
    elif isinstance(existing_tags, str):
        existing_list = [tag.strip() for tag in existing_tags.split(',') if tag.strip()]
    elif isinstance(existing_tags, list):
        existing_list = [tag for tag in existing_tags if tag and str(tag).strip()]
    else:
        existing_list = []
    
    # 新しいタグをリストに変換
    if not new_tags:
        new_list = []
    elif isinstance(new_tags, str):
        new_list = [tag.strip() for tag in new_tags.split(',') if tag.strip()]
    elif isinstance(new_tags, list):
        new_list = [tag for tag in new_tags if tag and str(tag).strip()]
    else:
        new_list = []
    
    # マージして重複を削除
    return list(set(existing_list + new_list))

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
    # 絶対パスに変換
    abs_data_dir = os.path.abspath(os.path.join(os.getcwd(), data_dir))
    os.makedirs(abs_data_dir, exist_ok=True)
    horses_file = os.path.join(abs_data_dir, 'horses.json')
    
    print(f"[DEBUG] データ保存先: {horses_file}")
    print(f"[DEBUG] 現在の作業ディレクトリ: {os.getcwd()}")
    print(f"[DEBUG] 相対データディレクトリ: {data_dir}")
    print(f"[DEBUG] 絶対データディレクトリ: {abs_data_dir}")
    
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
        
        # 疾病タグを安全にマージ
        existing_disease_tags = existing_horse.get('disease_tags', [])
        new_disease_tags = horse_data.get('disease_tags', [])
        
        # 更新するフィールドをマージ
        update_fields = {
            'sire': horse_data.get('sire', existing_horse.get('sire', '')),
            'dam': horse_data.get('dam', existing_horse.get('dam', '')),
            'damsire': horse_data.get('damsire', existing_horse.get('damsire', '')),
            'sex': horse_data.get('sex', existing_horse.get('sex', '')),
            'image_url': horse_data.get('image_url', existing_horse.get('image_url', '')),
            'jbis_url': horse_data.get('jbis_url', existing_horse.get('jbis_url', '')),
            'auction_url': horse_data.get('auction_url', existing_horse.get('auction_url', '')),
            'disease_tags': merge_disease_tags(existing_disease_tags, new_disease_tags),
            'updated_at': now,
            # 賞金情報を明示的にマージ（0の場合も含む）
            'total_prize_start': horse_data.get('total_prize_start', existing_horse.get('total_prize_start', 0)),
            'total_prize_latest': horse_data.get('total_prize_latest', existing_horse.get('total_prize_latest', 0))
        }
        
        # その他のフィールドをマージ
        for key in ['comment', 'race_record', 'weight', 'seller', 'auction_date']:
            if key in horse_data:
                update_fields[key] = horse_data[key]
        
        # 既存の馬情報を更新
        existing_horse.update(update_fields)
    else:
        # 新規の馬を追加
        horse_id = str(uuid.uuid4())
        horse_data['id'] = horse_id
        horse_data['created_at'] = now
        horse_data['updated_at'] = now
        
        # 疾病タグを初期化
        if 'disease_tags' not in horse_data:
            horse_data['disease_tags'] = []
        elif not isinstance(horse_data['disease_tags'], list):
            # 文字列の場合はリストに変換
            if isinstance(horse_data['disease_tags'], str):
                horse_data['disease_tags'] = [tag.strip() for tag in horse_data['disease_tags'].split(',') if tag.strip()]
            else:
                horse_data['disease_tags'] = []
        
        horses.append(horse_data)
    
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
