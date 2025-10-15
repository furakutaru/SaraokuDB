#!/usr/bin/env python3
"""
直近の9頭のデータをクリアするスクリプト

使用方法:
    python3 clear_recent_horses.py

注意:
- 実行前に自動でバックアップを作成します
- 処理内容を確認してから実行を続行します
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 設定
BASE_DIR = Path(__file__).parent.parent  # scripts/ の親ディレクトリ（SaraokuDB/）
DATA_DIR = BASE_DIR / "static-frontend/public/data"
HISTORY_FILE = DATA_DIR / "horses_history.json"
BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True, parents=True)

def create_backup() -> str:
    """タイムスタンプ付きのバックアップを作成"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"horses_history_{timestamp}.json"
    
    # バックアップ作成
    with open(HISTORY_FILE, 'r', encoding='utf-8') as src, \
         open(backup_file, 'w', encoding='utf-8') as dst:
        dst.write(src.read())
    
    return str(backup_file)

def load_data() -> dict:
    """データを読み込む"""
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data: dict) -> None:
    """データを保存"""
    temp_file = f"{HISTORY_FILE}.tmp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # アトミックな置き換え
    os.replace(temp_file, HISTORY_FILE)

def clear_recent_horses(data: dict) -> tuple[dict, int]:
    """特定のID（46-54）の馬を削除"""
    if not data['horses']:
        return data, 0
    
    # 削除対象のID（46-54）
    target_ids = set(range(46, 55))  # 55は含まれないので46-54
    
    # 削除対象の馬の情報を表示用に取得
    removed_horses = [
        {'id': h['id'], 'name': h.get('name', '名前不明'), 'updated_at': h.get('updated_at', '不明')}
        for h in data['horses'] if h['id'] in target_ids
    ]
    
    # 削除対象のIDに一致する全てのエントリを削除
    original_count = len(data['horses'])
    data['horses'] = [h for h in data['horses'] if h['id'] not in target_ids]
    removed_count = original_count - len(data['horses'])
    
    # 削除された馬の情報を表示
    print("\n削除された馬:")
    for i, horse in enumerate(removed_horses, 1):
        print(f"{i}. {horse['name']} (ID: {horse['id']}, 更新日時: {horse.get('updated_at', '不明')})")
    
    # メタデータ更新
    if 'metadata' in data:
        data['metadata']['total_horses'] = len(data['horses'])
        data['metadata']['last_updated'] = datetime.now().isoformat()
    
    return data, removed_count

def main():
    print("=== 直近の9頭のデータをクリアします ===")
    print(f"対象ファイル: {HISTORY_FILE.absolute()}")
    
    # バックアップ作成
    print("\n[1/3] バックアップを作成しています...")
    backup_file = create_backup()
    print(f"✓ バックアップを作成しました: {backup_file}")
    
    # データ読み込み
    print("\n[2/3] データを処理しています...")
    try:
        data = load_data()
        original_count = len(data['horses'])
        
        # データ処理
        data, removed_count = clear_recent_horses(data)
        
        # 保存
        save_data(data)
        
        # 結果表示
        print("\n[3/3] 完了しました！")
        print(f"✓ 元の馬の数: {original_count}頭")
        print(f"✓ 削除した馬: {removed_count}頭")
        print(f"✓ 残りの馬: {len(data['horses'])}頭")
        print("\n次にスクレイピングを実行すると、削除した馬のデータが再取得されます。")
        
    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}")
        print(f"バックアップから復元してください: {backup_file}")
        sys.exit(1)

if __name__ == "__main__":
    main()
