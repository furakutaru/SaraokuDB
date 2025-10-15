#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
馬IDをUUIDからオークションページのIDに移行するスクリプト
"""
import json
import os
from pathlib import Path

def load_json_file(file_path):
    """JSONファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        print(f"[ERROR] {file_path} の読み込みに失敗しました")
        return None

def save_json_file(file_path, data):
    """JSONファイルに保存する"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[INFO] {file_path} を保存しました")
        return True
    except Exception as e:
        print(f"[ERROR] {file_path} の保存中にエラーが発生しました: {str(e)}")
        return False

def migrate_auction_history(history_file, output_file=None):
    """オークション履歴のIDを移行する"""
    if output_file is None:
        output_file = history_file
        print(f"[INFO] 元のファイルを上書きします: {history_file}")
    
    # データを読み込む
    history_data = load_json_file(history_file)
    if history_data is None:
        return False
    
    # 変更の有無を追跡
    changed = False
    
    # 各履歴を処理
    for item in history_data:
        # 既に数値IDの場合はスキップ
        if 'horse_id' in item and isinstance(item['horse_id'], str) and item['horse_id'].isdigit():
            continue
            
        # 馬名とオークション日からIDを特定する必要がある
        # ここでは例として、元のIDを保持したまま新しいフィールドを追加
        if 'original_horse_id' not in item:
            item['original_horse_id'] = item.get('horse_id')
            changed = True
    
    # 変更があった場合のみ保存
    if changed:
        return save_json_file(output_file, history_data)
    else:
        print("[INFO] 変更の必要はありませんでした")
        return True

def main():
    # ファイルパス
    base_dir = Path("static-frontend/public/data")
    history_file = base_dir / "auction_history.json"
    backup_file = base_dir / "auction_history.backup.json"
    
    # バックアップを作成
    if history_file.exists():
        import shutil
        shutil.copy2(history_file, backup_file)
        print(f"[INFO] バックアップを作成しました: {backup_file}")
    
    # 移行を実行
    if migrate_auction_history(history_file):
        print("[SUCCESS] 移行が完了しました")
    else:
        print("[ERROR] 移行中にエラーが発生しました")
        if backup_file.exists():
            print(f"[INFO] バックアップから復元するには以下のコマンドを実行してください:")
            print(f"cp {backup_file} {history_file}")

if __name__ == "__main__":
    main()
