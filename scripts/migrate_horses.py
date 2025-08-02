#!/usr/bin/env python3
"""
horses.jsonを新しい形式に変換するスクリプト
"""
import json
import os
from datetime import datetime

def migrate_horses_file(file_path: str):
    # ファイルを読み込む
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 既に新しい形式の場合は何もしない
    if isinstance(data, dict) and 'horses' in data:
        print(f"ファイルは既に新しい形式です: {file_path}")
        return
    
    # 古い形式から新しい形式に変換
    new_data = {
        "metadata": {
            "last_updated": datetime.now().isoformat(),
            "total_horses": len(data),
            "version": "1.0.0"
        },
        "horses": data
    }
    
    # バックアップを作成
    backup_path = f"{file_path}.bak"
    os.rename(file_path, backup_path)
    print(f"バックアップを作成しました: {backup_path}")
    
    # 新しい形式で保存
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    
    print(f"ファイルを新しい形式に変換しました: {file_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("使用方法: python migrate_horses.py <horses.jsonのパス>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"エラー: ファイルが見つかりません: {file_path}")
        sys.exit(1)
    
    migrate_horses_file(file_path)
