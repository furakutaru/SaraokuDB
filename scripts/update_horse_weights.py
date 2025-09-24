#!/usr/bin/env python3
"""
馬体重データを更新するスクリプト
- auction_history.jsonから最新の馬体重を取得し、horses.jsonの各馬に反映する
"""

import json
import os
from datetime import datetime
from collections import defaultdict

# ファイルパスの設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
HORSES_FILE = os.path.join(PROJECT_ROOT, "static-frontend", "public", "data", "horses.json")
AUCTION_HISTORY_FILE = os.path.join(PROJECT_ROOT, "static-frontend", "public", "data", "auction_history.json")

def load_json_file(file_path):
    """JSONファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def save_json_file(file_path, data):
    """JSONファイルを保存する"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved to {file_path}")
        return True
    except Exception as e:
        print(f"Error saving {file_path}: {e}")
        return False

def get_latest_weights(auction_history):
    """最新のオークション履歴から各馬の最新体重を取得"""
    latest_weights = {}
    
    for entry in auction_history:
        horse_id = entry.get('horse_id')
        weight = entry.get('weight')
        auction_date_str = entry.get('auction_date')
        
        if not all([horse_id, weight, auction_date_str]):
            continue
            
        try:
            auction_date = datetime.strptime(auction_date_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            continue
            
        # 同じ馬でより新しい日付のデータがある場合は更新
        if horse_id not in latest_weights or latest_weights[horse_id]['date'] < auction_date:
            latest_weights[horse_id] = {
                'weight': weight,
                'date': auction_date
            }
    
    return {k: v['weight'] for k, v in latest_weights.items()}

def update_horses_with_weights(horses, latest_weights):
    """馬データを最新の体重で更新"""
    updated_count = 0
    
    for horse in horses:
        horse_id = horse.get('id')
        if horse_id in latest_weights:
            horse['weight'] = latest_weights[horse_id]
            updated_count += 1
    
    return updated_count

def main():
    print("Starting to update horse weights...")
    
    # データを読み込む
    print("Loading data files...")
    horses = load_json_file(HORSES_FILE)
    auction_history = load_json_file(AUCTION_HISTORY_FILE)
    
    if not horses or not auction_history:
        print("Failed to load data files. Exiting.")
        return
    
    print(f"Loaded {len(horses)} horses and {len(auction_history)} auction history entries")
    
    # 最新の馬体重を取得
    print("Finding latest weights...")
    latest_weights = get_latest_weights(auction_history)
    print(f"Found latest weights for {len(latest_weights)} horses")
    
    # 馬データを更新
    print("Updating horse data...")
    updated_count = update_horses_with_weights(horses, latest_weights)
    print(f"Updated weights for {updated_count} horses")
    
    # バックアップを作成
    backup_file = HORSES_FILE + ".bak" + datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"Creating backup at {backup_file}...")
    save_json_file(backup_file, horses)
    
    # 更新したデータを保存
    print(f"Saving updated data to {HORSES_FILE}...")
    if save_json_file(HORSES_FILE, horses):
        print("Successfully updated horse weights!")
    else:
        print("Failed to save updated data")

if __name__ == "__main__":
    main()
