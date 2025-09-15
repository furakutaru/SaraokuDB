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
        
        # データ構造を正規化
        if isinstance(data, dict) and 'horses' in data:
            # 新しい形式のデータ（辞書に'horses'キーがある）
            print(f"[DEBUG] 新しい形式のデータを検出: 馬の数={len(data.get('horses', []))}")
            print(f"[DEBUG] メタデータ: {data.get('metadata', {})}")
            
            # デバッグ用に最初の3頭を表示
            horses = data.get('horses', [])
            print("\n[DEBUG] 保存前の馬データ (最初の3件):")
            for i, h in enumerate(horses[:3]):
                print(f"{i+1}. {h.get('name')} (ID: {h.get('id')})")
                print(f"    父: {h.get('sire')}, 母: {h.get('dam')}, 母父: {h.get('damsire')}")
        elif isinstance(data, list):
            # 古い形式のデータ（馬のリスト）を新しい形式に変換
            print(f"[DEBUG] 古い形式のデータを検出: 馬の数={len(data)}")
            horses = data
            data = {
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "total_horses": len(horses),
                    "version": "1.0.0"
                },
                "horses": horses
            }
            print(f"[DEBUG] 新しい形式に変換しました: 馬の数={len(horses)}")
        else:
            # その他の形式のデータ
            print(f"[DEBUG] 不明なデータ形式: {type(data)}")
            data = {
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "total_horses": 0,
                    "version": "1.0.0"
                },
                "horses": []
            }
        
        # ファイルに保存
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 保存したファイルを読み込んで確認
        with open(file_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            saved_horses = saved_data.get('horses', [])
            print("\n[DEBUG] 保存されたデータ (最初の3件):")
            for i, h in enumerate(saved_horses[:3]):
                print(f"{i+1}. {h.get('name')} (ID: {h.get('id')})")
                print(f"    父: {h.get('sire')}, 母: {h.get('dam')}, 母父: {h.get('damsire')}")
                
        # 必須フィールドの存在確認
        print("\n[DEBUG] 必須フィールドの確認 (最初の3件):")
        for i, h in enumerate(saved_horses[:3]):
            missing_fields = [field for field in ['name', 'sex', 'age', 'sire', 'dam', 'damsire', 'seller', 'auction_date'] 
                            if not h.get(field)]
            status = "OK" if not missing_fields else f"不足フィールド: {', '.join(missing_fields)}"
            print(f"{i+1}. {h.get('name')}: {status}")
        
        print(f"\n[DEBUG] ファイル保存完了: {file_path}")
        print(f"[DEBUG] ファイルの存在確認: {os.path.exists(file_path)}")
        print(f"[DEBUG] ファイルサイズ: {os.path.getsize(file_path) if os.path.exists(file_path) else 0} バイト")
        
    except Exception as e:
        print(f"[ERROR] ファイル保存中にエラーが発生しました: {str(e)}")
        print(f"[ERROR] ファイルパス: {file_path}")
        print(f"[ERROR] データタイプ: {type(data)}")
        if hasattr(data, 'keys'):
            print(f"[ERROR] データキー: {list(data.keys())}")
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
    """馬の情報をJSONファイルに保存する
    
    Args:
        horse_data: 保存する馬の情報
        data_dir: データディレクトリのパス
        
    Returns:
        str: 保存された馬のID
    """
    # IDが設定されていない場合は新規IDを生成
    if 'id' not in horse_data or not horse_data['id']:
        horse_data['id'] = str(uuid.uuid4())
        print(f"[DEBUG] 新しいIDを生成しました: {horse_data['id']}")
    else:
        print(f"[DEBUG] 既存のIDを使用します: {horse_data['id']}")
    # ファイルパスを設定
    os.makedirs(data_dir, exist_ok=True)
    horses_file = os.path.join(data_dir, 'horses.json')
    
    # デバッグ情報の表示
    print(f"[DEBUG] データ保存先: {horses_file}")
    print(f"[DEBUG] 現在の作業ディレクトリ: {os.getcwd()}")
    print(f"[DEBUG] 相対データディレクトリ: {data_dir}")
    print(f"[DEBUG] 絶対データディレクトリ: {os.path.abspath(data_dir)}")
    
    # ファイルを読み込む
    data = load_json_file(horses_file)
    
    # データ構造を正規化
    if isinstance(data, list):
        # 配列形式の場合は辞書に変換
        horses = data
        data = {
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "total_horses": len(horses),
                "version": "1.0.0"
            },
            "horses": horses
        }
        print("[DEBUG] 配列形式のデータを辞書形式に変換しました")
    elif isinstance(data, dict):
        # 辞書形式の場合は'horses'キーを確認
        if 'horses' not in data:
            print("[WARNING] 'horses'キーが見つかりません。新しいデータ構造を作成します")
            data = {
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "total_horses": 0,
                    "version": "1.0.0"
                },
                "horses": []
            }
    else:
        # その他の形式の場合は空のデータ構造を作成
        print(f"[WARNING] 不明なデータ形式: {type(data)}. 空のデータ構造を作成します")
        data = {
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "total_horses": 0,
                "version": "1.0.0"
            },
            "horses": []
        }
    
    horses = data.get('horses', [])
    
    # 必須フィールドを確認し、デフォルト値を設定
    required_fields = {
        'sex': '',
        'sire': '',
        'dam': '',
        'damsire': '',
        'seller': '',
        'auction_date': ''
    }
    
    # 必須フィールドを確認し、不足している場合はデフォルト値を設定
    for field, default in required_fields.items():
        if field not in horse_data or horse_data[field] is None:
            horse_data[field] = default
            print(f"[WARNING] 必須フィールド '{field}' が不足しているため、空文字を設定しました")
    
    # 既存の馬を検索（IDまたは名前と年齢で照合）
    existing_horse = None
    existing_index = -1
    
    for i, horse in enumerate(horses):
        # IDで照合（優先）
        if 'id' in horse and 'id' in horse_data and horse['id'] == horse_data['id']:
            existing_horse = horse
            existing_index = i
            print(f"[DEBUG] IDで既存の馬を検出: {horse_data['id']}")
            break
        # 名前と年齢で照合（互換性のため）
        elif (horse.get('name') == horse_data.get('name') and 
              str(horse.get('age')) == str(horse_data.get('age'))):
            existing_horse = horse
            existing_index = i
            print(f"[DEBUG] 名前と年齢で既存の馬を検出: {horse_data.get('name')} ({horse_data.get('age')}歳)")
            # 既存の馬にIDがなければ新しいIDを割り当てる
            if 'id' not in horse or not horse['id']:
                horse['id'] = str(uuid.uuid4())
                print(f"[DEBUG] 既存の馬に新しいIDを割り当てました: {horse['id']}")
            break
    
    # 現在のタイムスタンプを取得
    now = datetime.now().isoformat()
    
    # 既存の馬がいる場合は更新、いない場合は追加
    if existing_horse is not None:
        # 既存のデータを更新（IDは変更しない）
        existing_id = existing_horse.get('id')
        if not existing_id:
            existing_id = str(uuid.uuid4())
            print(f"[DEBUG] 既存の馬に新しいIDを生成しました: {existing_id}")
        horse_data['id'] = existing_id  # 既存のIDを保持
        horses[existing_index].update(horse_data)
        horse_id = existing_id
        print(f"[INFO] 馬情報を更新しました: {horse_data.get('name')} (ID: {horse_id})")
    else:
        # 新しい馬を追加（既にIDは設定済み）
        if 'id' not in horse_data or not horse_data['id']:
            horse_data['id'] = str(uuid.uuid4())
            print(f"[DEBUG] 新しい馬にIDを生成しました: {horse_data['id']}")
        horse_id = horse_data['id']
        horses.append(horse_data)
        print(f"[INFO] 新しい馬を追加しました: {horse_data.get('name')} (ID: {horse_id})")
    
    # データ構造を更新
    data['horses'] = horses
    data['metadata'] = {
        'last_updated': now,
        'total_horses': len(horses),
        'version': data.get('metadata', {}).get('version', '1.2.0')  # バージョンを更新
    }
    
    # 必須フィールドの確認とデフォルト値の設定
    required_fields = ['id', 'name', 'sex', 'age', 'sire', 'dam', 'damsire', 'seller', 'auction_date']
    for horse in horses:
        # IDがなければ生成
        if 'id' not in horse or not horse['id']:
            horse['id'] = str(uuid.uuid4())
            print(f"[DEBUG] 新しいIDを生成しました: {horse['id']} (馬名: {horse.get('name', '不明')})")
            
        # 必須フィールドのチェック
        missing_fields = [field for field in required_fields if field not in horse or not horse[field]]
        if missing_fields:
            print(f"[WARNING] 必須フィールドが不足しています: {', '.join(missing_fields)} (馬名: {horse.get('name', '不明')})")
            # 空文字で初期化
            for field in missing_fields:
                if field != 'id':  # IDは既に生成済み
                    horse[field] = ''
    
    # デバッグ用に保存前のデータを表示
    print(f"[DEBUG] 保存前のデータ構造 (最初の3件): {json.dumps(horses[:3], ensure_ascii=False, indent=2)}")
    print(f"[DEBUG] メタデータ: {json.dumps(data['metadata'], ensure_ascii=False, indent=2)}")
    
    # デバッグ用に更新された馬情報をログ出力
    updated_horse = next((h for h in horses if h.get('id') == horse_id), None)
    if updated_horse:
        print(f"[DEBUG] 更新された馬情報 (ID: {horse_id}):")
        print(f"  名前: {updated_horse.get('name')}")
        print(f"  父: {updated_horse.get('sire')}")
        print(f"  母: {updated_horse.get('dam')}")
        print(f"  母父: {updated_horse.get('damsire')}")
    
    try:
        # データ構造を確認
        print(f"[DEBUG] 保存前のデータ構造: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}...")
        
        # ファイルに保存（dataオブジェクト全体を保存）
        with open(horses_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 保存したファイルを読み込んで確認
        with open(horses_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            print(f"[DEBUG] 保存されたデータ構造: {json.dumps(saved_data, ensure_ascii=False, indent=2)[:500]}...")
        
        print(f"[DEBUG] 馬情報を保存しました: {horses_file}")
        return horse_id
    except Exception as e:
        print(f"[ERROR] ファイル保存中にエラーが発生しました: {str(e)}")
        raise

def save_auction_history(auction_data, data_dir='static-frontend/public/data'):
    """オークション履歴をJSONファイルに保存する
    
    Args:
        auction_data: 保存するオークション履歴データ
        data_dir: データディレクトリのパス
        
    Returns:
        bool: 保存に成功した場合はTrue、失敗した場合はFalse
    """
    try:
        # 必須フィールドの確認
        required_fields = ['horse_id', 'auction_date', 'sold_price']
        if not all(field in auction_data for field in required_fields):
            print("[ERROR] 必須フィールドが不足しています")
            return False
            
        # horse_idが数値IDであることを確認
        try:
            horse_id = str(int(auction_data['horse_id']))  # 数値に変換してから文字列に
            auction_data['horse_id'] = horse_id
        except (ValueError, TypeError) as e:
            print(f"[ERROR] 無効な馬ID形式です: {auction_data['horse_id']}")
            return False
            
        # 保存先ディレクトリが存在するか確認し、なければ作成
        os.makedirs(data_dir, exist_ok=True)
        
        # ファイルパス
        file_path = os.path.join(data_dir, 'auction_history.json')
        
        # 既存のデータを読み込む（存在する場合）
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        existing_data = []
                except json.JSONDecodeError:
                    existing_data = []
        else:
            existing_data = []
        
        # 既存のデータを更新または新規追加
        updated = False
        for i, item in enumerate(existing_data):
            if (str(item.get('horse_id')) == str(auction_data['horse_id']) and 
                item.get('auction_date') == auction_data['auction_date']):
                # 既存のデータを更新
                existing_data[i].update(auction_data)
                updated = True
                break
                
        if not updated:
            # 新しいデータを追加
            existing_data.append(auction_data)
        
        # データをJSONファイルに保存
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
        print(f"[INFO] オークション履歴を保存しました: {file_path}")
        return True
        
    except Exception as e:
        print(f"[ERROR] オークション履歴の保存中にエラーが発生しました: {str(e)}")
        return False
