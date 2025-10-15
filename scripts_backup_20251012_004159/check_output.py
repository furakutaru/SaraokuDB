#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os

def main():
    file_path = '/Users/yum.ishii/SaraokuDB/scripts/output/horses_20250829_104339.json'
    
    # ファイルの存在確認
    if not os.path.exists(file_path):
        print(f"エラー: ファイルが見つかりません: {file_path}")
        return
    
    # ファイルサイズの確認
    file_size = os.path.getsize(file_path)
    print(f"ファイルサイズ: {file_size} バイト")
    
    # ファイルの内容をバイナリモードで読み込む
    with open(file_path, 'rb') as f:
        content = f.read()
        print(f"\nファイルの先頭100バイト: {content[:100]}")
    
    # JSONとして読み込んでみる
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print("\nJSONの読み込みに成功しました。最初の3件を表示します:")
            for i, horse in enumerate(data[:3], 1):
                print(f"\n--- 馬 {i} ---")
                print(f"名前: {horse.get('name', 'N/A')}")
                print(f"性別: {horse.get('sex', 'N/A')}")
                print(f"年齢: {horse.get('age', 'N/A')}")
    except Exception as e:
        print(f"\nJSONの読み込み中にエラーが発生しました: {e}")

if __name__ == "__main__":
    main()
