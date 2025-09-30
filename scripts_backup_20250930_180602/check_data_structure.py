#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path

def analyze_data(file_path):
    print(f"\nAnalyzing: {file_path}")
    print("=" * 50)
    
    try:
        # ファイルの存在確認
        if not file_path.exists():
            print(f"Error: ファイルが見つかりません: {file_path}")
            return
            
        # ファイルサイズの確認
        file_size = file_path.stat().st_size
        print(f"ファイルサイズ: {file_size} バイト")
        
        # ファイルの内容を読み込む
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                print("\nJSONデータの構造:")
                print("-" * 30)
                
                # トップレベルのキーを表示
                print(f"トップレベルのキー: {list(data.keys())}")
                
                # 馬のデータがあるか確認
                if 'horses' in data and isinstance(data['horses'], list):
                    print(f"\n馬のデータ数: {len(data['horses'])}")
                    
                    if data['horses']:
                        # 最初の馬のデータを表示
                        first_horse = data['horses'][0]
                        print("\n最初の馬のフィールド:")
                        for i, (key, value) in enumerate(first_horse.items(), 1):
                            print(f"  {i}. {key}: {value}")
                        
                        # 必須フィールドの確認
                        print("\n必須フィールドの確認:")
                        required_fields = ['name', 'auction_date', 'sire', 'dam', 'damsire']
                        for field in required_fields:
                            exists = field in first_horse
                            value = first_horse.get(field, 'MISSING')
                            print(f"  {field}: {value} {'(MISSING)' if not exists else ''}")
                
            except json.JSONDecodeError as e:
                print(f"\nJSONデコードエラー: {e}")
                
                # エラーが発生した場合はファイルの先頭を表示
                with open(file_path, 'r', encoding='utf-8') as f:
                    print("\nファイルの先頭100文字:")
                    print(f.read(100))
                    
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")

def main():
    # 確認するファイルパス
    target_files = [
        Path("/Users/yum.ishii/SaraokuDB/static-frontend/public/data/horses.json"),
        Path("/Users/yum.ishii/SaraokuDB/static-frontend/public/data/horses.json.backup"),
        Path("/Users/yum.ishii/SaraokuDB/backend/data/horses.json")
    ]
    
    for file_path in target_files:
        analyze_data(file_path)
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()
