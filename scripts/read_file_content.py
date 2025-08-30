#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from pathlib import Path

def main():
    file_path = Path('output/horses_20250829_104742.json')
    
    # ファイルの存在確認
    if not file_path.exists():
        print(f"エラー: ファイルが見つかりません: {file_path.absolute()}")
        return
    
    # ファイルサイズの確認
    file_size = file_path.stat().st_size
    print(f"ファイルサイズ: {file_size} バイト")
    
    # バイナリモードで読み込む
    with open(file_path, 'rb') as f:
        content = f.read()
        print(f"\nファイルの先頭100バイト: {content[:100]}")
    
    # テキストとしてデコードを試みる
    try:
        text = content.decode('utf-8')
        print("\nUTF-8でデコード成功:")
        print(text[:200] + "..." if len(text) > 200 else text)
    except UnicodeDecodeError as e:
        print(f"\nUTF-8でのデコードに失敗: {e}")
    
    # JSONとして読み込んでみる
    try:
        data = json.loads(content)
        print("\nJSONの読み込みに成功しました。最初の3件を表示します:")
        for i, horse in enumerate(data[:3], 1):
            print(f"\n--- 馬 {i} ---")
            print(f"名前: {horse.get('name', 'N/A')}")
            print(f"性別: {horse.get('sex', 'N/A')}")
            print(f"年齢: {horse.get('age', 'N/A')}")
    except json.JSONDecodeError as e:
        print(f"\nJSONのパースに失敗: {e}")

if __name__ == "__main__":
    main()
