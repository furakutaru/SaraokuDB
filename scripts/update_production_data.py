import json
import os
from datetime import datetime
from pathlib import Path

def load_json_file(file_path):
    """JSONファイルを読み込む"""
    if not os.path.exists(file_path):
        print(f"ファイルが存在しません: {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"JSONのデコードエラー ({file_path}): {e}")
        return None
    except Exception as e:
        print(f"エラーが発生しました ({file_path}): {e}")
        return None

def save_json_file(data, file_path):
    """データをJSONファイルに保存する"""
    try:
        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"データを保存しました: {file_path}")
        return True
    except Exception as e:
        print(f"ファイルの保存に失敗しました ({file_path}): {e}")
        return False

def convert_to_production_format(scraped_data):
    """スクレイピングデータを本番形式に変換する"""
    horses = []
    auction_history = []
    
    current_time = datetime.now().isoformat()
    
    for item in scraped_data:
        try:
            # 馬の基本情報
            horse = {
                'id': str(item.get('id', '')),  # 文字列に変換
                'name': item.get('name', ''),
                'sire': item.get('sire', ''),
                'dam': item.get('dam', ''),
                'damsire': item.get('damsire', ''),
                'sex': item.get('sex', ''),
                'age': item.get('age', 0),
                'image_url': item.get('image_url', ''),
                'jbis_url': item.get('jbis_url', ''),
                'auction_url': item.get('auction_url', ''),
                'disease_tags': item.get('disease_tags', []),
                'created_at': current_time,
                'updated_at': current_time
            }
            
            # オークション履歴
            history = {
                'id': f"{item.get('id', '')}_{current_time}",  # 一意のIDを生成
                'horse_id': str(item.get('id', '')),  # 馬IDを文字列に
                'auction_date': item.get('auction_date', ''),
                'sold_price': item.get('sold_price'),
                'total_prize_start': item.get('total_prize_start', 0.0),
                'total_prize_latest': item.get('total_prize_latest', 0.0),
                'weight': item.get('weight'),
                'seller': item.get('seller', ''),
                'is_unsold': item.get('is_unsold', False),
                'comment': item.get('comment', ''),
                'created_at': current_time
            }
            
            horses.append(horse)
            auction_history.append(history)
            
        except Exception as e:
            print(f"データの変換中にエラーが発生しました: {e}")
            continue
    
    return horses, auction_history

def update_production_data(scraped_data_path, output_dir):
    """本番データを更新する"""
    # スクレイピングデータを読み込む
    scraped_data = load_json_file(scraped_data_path)
    if not scraped_data:
        print("スクレイピングデータの読み込みに失敗しました")
        return False
    
    print(f"スクレイピングデータを読み込みました: {len(scraped_data)}件")
    
    # 本番形式に変換
    horses, auction_history = convert_to_production_format(scraped_data)
    
    # 既存の本番データを読み込む
    horses_file = os.path.join(output_dir, 'horses.json')
    history_file = os.path.join(output_dir, 'auction_history.json')
    
    # 既存の馬データを読み込む（存在する場合）
    existing_horses = []
    if os.path.exists(horses_file):
        existing_horses = load_json_file(horses_file) or []
    
    # 既存のオークション履歴を読み込む（存在する場合）
    existing_history = []
    if os.path.exists(history_file):
        existing_history = load_json_file(history_file) or []
    
    # 重複を避けてデータをマージ
    existing_horse_ids = {h.get('id') for h in existing_horses}
    updated_horses = existing_horses.copy()
    
    for horse in horses:
        if horse['id'] not in existing_horse_ids:
            updated_horses.append(horse)
    
    # オークション履歴を追加
    updated_history = existing_history + auction_history
    
    # データを保存
    success = True
    success &= save_json_file(updated_horses, horses_file)
    success &= save_json_file(updated_history, history_file)
    
    if success:
        print(f"\n更新が完了しました:")
        print(f"- 馬データ: {len(updated_horses)}件 (新規: {len(horses) - len(existing_horses)})件")
        print(f"- オークション履歴: {len(updated_history)}件 (新規: {len(auction_history)}件)")
    else:
        print("\n更新中にエラーが発生しました")
    
    return success

if __name__ == "__main__":
    # スクレイピングデータのパス
    scraped_data_path = "/Users/yum.ishii/SaraokuDB/cache/20250818/processed_horses.json"
    
    # 本番データの出力先ディレクトリ
    output_dir = "/Users/yum.ishii/SaraokuDB/backend/data"
    
    # 本番データを更新
    update_production_data(scraped_data_path, output_dir)
