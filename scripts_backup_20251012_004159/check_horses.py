#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from pathlib import Path

def main():
    # 最新のファイルを探す
    output_dir = Path('output')
    if not output_dir.exists():
        print("出力ディレクトリが見つかりません")
        return
    
    # 最新のファイルを取得
    horse_files = sorted(output_dir.glob('horses_*.json'), key=os.path.getmtime, reverse=True)
    if not horse_files:
        print("馬のデータファイルが見つかりません")
        return
    
    latest_file = horse_files[0]
    print(f"最新のファイル: {latest_file}")
    
    # ファイルを読み込む
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 最初の5件を表示
        print("\n=== 最初の5件の馬データ ===")
        for i, horse in enumerate(data[:5], 1):
            print(f"\n--- 馬 {i} ---")
            print(f"名前: {horse.get('name', 'N/A')}")
            print(f"性別: {horse.get('sex', 'N/A')}")
            print(f"年齢: {horse.get('age', 'N/A')}")
            
        # 名前が省略されていないかチェック
        print("\n=== 名前の省略チェック ===")
        for i, horse in enumerate(data, 1):
            name = horse.get('name', '')
            if '...' in name or '…' in name or (len(name) > 0 and name[-1] in ('.', '…')):
                print(f"省略された名前を検出: {name} (馬 {i}件目)")
        
        print("\nチェックが完了しました")
        
    except Exception as e:
        print(f"ファイルの読み込み中にエラーが発生しました: {e}")

if __name__ == "__main__":
    main()
