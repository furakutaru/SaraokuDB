#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
馬データの保存機能をテストするスクリプト
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 保存先ディレクトリのパス
data_dir = project_root / 'data'
json_file = data_dir / 'horses.json'

# テスト用の馬データ
test_horse_data = {
    "id": "test_horse_001",
    "name": "テスト馬",
    "age": 3,
    "sex": "牡",
    "sire": "テスト父",
    "dam": "テスト母",
    "damsire": "テスト母父",
    "race_records": {
        "starts": 5,
        "wins": 2,
        "places": 1,
        "shows": 0
    },
    "comment": "これはテスト用の馬データです。",
    "image_url": "https://example.com/test_horse.jpg"
}

def test_save_horse():
    """馬データの保存をテストする"""
    # テスト用の馬データを保存
    from scripts.improved_scraper import save_horse
    
    print("テストを開始します...")
    print(f"テストデータ: {json.dumps(test_horse_data, ensure_ascii=False, indent=2)}")
    
    # 馬データを保存
    result = save_horse(test_horse_data)
    print(f"\n保存結果: {result}")
    
    # 保存されたデータを確認
    if json_file.exists():
        with open(json_file, 'r', encoding='utf-8') as f:
            try:
                saved_data = json.load(f)
                print(f"\n保存されたデータ ({len(saved_data)}件):")
                for i, horse in enumerate(saved_data, 1):
                    print(f"\n馬 {i}:")
                    for key, value in horse.items():
                        print(f"  {key}: {value}")
                
                # テストデータが正しく保存されているか確認
                test_horse = next((h for h in saved_data if h.get('id') == test_horse_data['id']), None)
                if test_horse:
                    print("\n✅ テスト成功: テストデータが正しく保存されました")
                else:
                    print("\n❌ テスト失敗: テストデータが見つかりません")
                    
            except json.JSONDecodeError as e:
                print(f"\n❌ JSONの読み込みに失敗しました: {e}")
    else:
        print("\n❌ ファイルが作成されていません")

if __name__ == "__main__":
    test_save_horse()
