#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime

# パスの設定
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_JSON_PATH = os.path.join(BASE_DIR, 'static-frontend', 'public', 'data', 'horses_history.json')
DISEASE_JSON_PATH = os.path.join(BASE_DIR, 'static-frontend', 'public', 'data', 'horses_history_with_disease.json')

# デバッグ用：パス確認
print(f"HISTORY_JSON_PATH: {HISTORY_JSON_PATH}")
print(f"DISEASE_JSON_PATH: {DISEASE_JSON_PATH}")
print(f"Current working directory: {os.getcwd()}")
print(f"HISTORY_JSON exists: {os.path.exists(HISTORY_JSON_PATH)}")
print(f"DISEASE_JSON exists: {os.path.exists(DISEASE_JSON_PATH)}")

def load_json(file_path):
    """JSONファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"エラー: {file_path} の読み込みに失敗しました: {e}")
        return None

def save_json(data, file_path):
    """JSONファイルを保存する"""
    try:
        # バックアップを作成
        backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        import shutil
        shutil.copy2(file_path, backup_path)
        print(f"バックアップを作成しました: {backup_path}")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"保存しました: {file_path}")
        return True
    except Exception as e:
        print(f"エラー: {file_path} の保存に失敗しました: {e}")
        return False

def update_disease_tags():
    """病気タグを更新する"""
    print("\n=== 病気タグの更新を開始します ===")
    
    # 元のデータと病気タグデータを読み込む
    print("\n[INFO] ファイルを読み込んでいます...")
    history_data = load_json(HISTORY_JSON_PATH)
    disease_data = load_json(DISEASE_JSON_PATH)
    
    if not history_data or not disease_data:
        print("[ERROR] 必要なファイルの読み込みに失敗しました。")
        return False
    
    history_horses = history_data.get('horses', [])
    disease_horses = disease_data.get('horses', [])
    
    print(f"[INFO] 元データ: 馬{len(history_horses)}頭、更新データ: 馬{len(disease_horses)}頭")
    
    # 馬名をキーとして病気タグをマッピング
    print("\n[INFO] 病気タグのマッピングを作成しています...")
    disease_mapping = {}
    
    # 病気タグデータを処理
    for horse in disease_horses:
        horse_name = horse.get('name')
        if not horse_name:
            continue
            
        # 馬名をキーとして、その馬の履歴リストを保存
        if horse_name not in disease_mapping:
            disease_mapping[horse_name] = []
            
        # 各履歴の病気タグをマッピング
        for history in horse.get('history', []):
            disease_tags = history.get('disease_tags', '')
            # 病気タグが空でない場合のみ処理
            if disease_tags and disease_tags != 'なし' and disease_tags != 'None':
                disease_mapping[horse_name].append(disease_tags)
                print(f"  [マッピング] 馬名: {horse_name}, 病気タグ: {disease_tags}")
    
    print(f"\n[INFO] 合計{sum(len(tags) for tags in disease_mapping.values())}件の病気タグが見つかりました。")
    
    # 元のデータを更新（病気タグのみ）
    print("\n[INFO] 元データを更新しています...")
    updated_count = 0
    
    for horse in history_horses:
        horse_name = horse.get('name')
        if not horse_name or horse_name not in disease_mapping:
            continue
            
        print(f"\n[処理中] 馬名: {horse_name}")
        
        # この馬の病気タグリストを取得
        disease_tags_list = disease_mapping[horse_name]
        
        # 各履歴をチェック（historyのインデックスに基づいてマッピング）
        for i, history in enumerate(horse.get('history', [])):
            # インデックスが病気タグリストの範囲内にあるか確認
            if i < len(disease_tags_list):
                current_disease_tags = history.get('disease_tags', '')
                new_disease_tags = disease_tags_list[i]
                
                # 現在のタグと異なる場合のみ更新
                if current_disease_tags != new_disease_tags:
                    print(f"  [更新] 履歴 {i+1}件目")
                    print(f"    現在のタグ: {current_disease_tags}")
                    print(f"    新しいタグ: {new_disease_tags}")
                    
                    # 病気タグを更新
                    history['disease_tags'] = new_disease_tags
                    updated_count += 1
    
    # 更新したデータを保存
    print("\n=== 更新結果 ===")
    if updated_count > 0:
        print(f"[SUCCESS] 合計{updated_count}件の病気タグを更新しました。")
        
        # バックアップを作成してから保存
        if save_json(history_data, HISTORY_JSON_PATH):
            print(f"[SUCCESS] ファイルを保存しました: {HISTORY_JSON_PATH}")
            return True
        else:
            print("[ERROR] ファイルの保存に失敗しました。")
            return False
    else:
        print("[INFO] 更新する病気タグは見つかりませんでした。")
        return False

if __name__ == "__main__":
    update_disease_tags()
