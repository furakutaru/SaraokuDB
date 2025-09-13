#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
馬データの保存機能をテストするスタンドアロンスクリプト
"""
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional

# 保存先ディレクトリのパス
data_dir = Path('data')
json_file = data_dir / 'horses_test.json'

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

def save_horse(horse_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    馬データをJSONファイルに保存する（スタンドアロンバージョン）
    
    Args:
        horse_data: 保存する馬データの辞書
        
    Returns:
        Dict: 保存結果を含む辞書
    """
    try:
        # 保存先ディレクトリが存在するか確認し、なければ作成
        data_dir.mkdir(exist_ok=True, parents=True)
        
        # 既存のデータを読み込む（存在する場合）
        if json_file.exists():
            with open(json_file, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        existing_data = []
                except json.JSONDecodeError:
                    existing_data = []
        else:
            existing_data = []
        
        # 馬IDが既存のデータに存在するか確認
        horse_id = horse_data.get('id')
        if not horse_id:
            return {'error': 'Horse ID is missing'}
            
        # 既存の馬データを更新または新規追加
        updated = False
        for i, horse in enumerate(existing_data):
            if str(horse.get('id')) == str(horse_id):
                # 既存の馬データを更新
                existing_data[i].update(horse_data)
                updated = True
                break
                
        if not updated:
            # 新しい馬データを追加
            existing_data.append(horse_data)
        
        # データをJSONファイルに保存
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
        
        return {'success': True, 'id': horse_id, 'action': 'updated' if updated else 'created'}
        
    except Exception as e:
        return {'error': str(e), 'traceback': traceback.format_exc()}

def test_save_horse():
    """馬データの保存をテストする"""
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
                    print(f"ファイルパス: {json_file.absolute()}")
                    return True
                else:
                    print("\n❌ テスト失敗: テストデータが見つかりません")
                    
            except json.JSONDecodeError as e:
                print(f"\n❌ JSONの読み込みに失敗しました: {e}")
    else:
        print(f"\n❌ ファイルが作成されていません: {json_file}")
    
    return False

if __name__ == "__main__":
    test_save_horse()
