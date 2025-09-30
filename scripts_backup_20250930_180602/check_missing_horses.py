#!/usr/bin/env python3
"""
`horses.json` と `horses_history.json` を比較して、不足している馬を特定するスクリプト
"""

import json
import os

def load_json_file(file_path: str) -> dict:
    """JSONファイルを読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    # ファイルパスを設定
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # ファイルパス
    horses_file = os.path.join(project_root, "static-frontend", "public", "data", "horses.json")
    history_file = os.path.join(project_root, "static-frontend", "public", "data", "horses_history.json")
    
    print(f"horses.json: {horses_file}")
    print(f"horses_history.json: {history_file}")
    
    # ファイルを読み込む
    print("\nデータを読み込んでいます...")
    horses_data = load_json_file(horses_file)
    history_data = load_json_file(history_file)
    
    # 馬のIDを取得
    horses = {horse['id']: horse['name'] for horse in horses_data.get('horses', [])}
    history_horses = {horse['id']: horse['name'] for horse in history_data.get('horses', [])}
    
    print(f"\nhorses.json の馬の数: {len(horses)}")
    print(f"horses_history.json の馬の数: {len(history_horses)}")
    
    # 不足している馬を特定
    missing_ids = set(horses.keys()) - set(history_horses.keys())
    print(f"\n不足している馬の数: {len(missing_ids)}")
    
    if missing_ids:
        print("\n不足している馬の詳細:")
        for horse_id in missing_ids:
            print(f"- ID: {horse_id}, 名前: {horses[horse_id]}")
            
            # 馬の詳細情報を表示
            horse_info = next((h for h in horses_data['horses'] if h['id'] == horse_id), None)
            if horse_info:
                print(f"  性別: {horse_info.get('sex', '不明')}, 年齢: {horse_info.get('age', '不明')}")
                print(f"  父: {horse_info.get('sire', '不明')}, 母: {horse_info.get('dam', '不明')}")
                print(f"  母父: {horse_info.get('damsire', '不明')}")
                print(f"  落札価格: {horse_info.get('sold_price', '不明')}")
                print(f"  売主: {horse_info.get('seller', '不明')}")
                print(f"  オークション日: {horse_info.get('auction_date', '不明')}")
                print()
    else:
        print("\n不足している馬はありません。")

if __name__ == "__main__":
    main()
