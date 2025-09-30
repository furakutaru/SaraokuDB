#!/usr/bin/env python3
"""
テスト用の履歴データを作成するスクリプト
新しい履歴リセット機能をテストするために複数の履歴エントリを追加
"""

import json
import os
from datetime import datetime, timedelta

def create_test_history():
    """テスト用の履歴データを作成"""
    history_file = "/Users/yum.ishii/SaraokuDB/static-frontend/public/data/horses_history.json"
    
    if not os.path.exists(history_file):
        print("❌ 履歴ファイルが存在しません")
        return False
    
    # 既存データを読み込み
    with open(history_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    horses = data.get('horses', [])
    if not horses:
        print("❌ 馬データが存在しません")
        return False
    
    print(f"📊 テスト用履歴データを作成中: {len(horses)}頭の馬を処理")
    
    # 各馬に追加の履歴エントリを作成
    for horse in horses[:10]:  # 最初の10頭のみテスト用に追加
        current_history = horse.get('history', [])
        if not current_history:
            continue
            
        # 現在の履歴をベースに過去の履歴を作成
        base_history = current_history[0].copy()
        
        # 3つの異なる日付の履歴を追加
        test_dates = [
            '2025-07-20',  # 6日前
            '2025-07-23',  # 3日前
            '2025-07-26'   # 現在（既存）
        ]
        
        new_history = []
        for i, date in enumerate(test_dates):
            history_entry = base_history.copy()
            history_entry['auction_date'] = date
            history_entry['sold_price'] = base_history.get('sold_price', 1000000) + (i * 100000)
            new_history.append(history_entry)
        
        horse['history'] = new_history
        print(f"  ✅ {horse.get('name', 'Unknown')}: {len(current_history)}件 -> {len(new_history)}件")
    
    # メタデータを更新
    total_history = sum(len(horse.get('history', [])) for horse in horses)
    data['metadata']['last_updated'] = datetime.now().isoformat()
    data['metadata']['total_history_entries'] = total_history
    data['metadata']['test_data_created'] = True
    data['metadata']['test_creation_date'] = datetime.now().isoformat()
    
    # ファイルに保存
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ テスト用履歴データの作成が完了しました")
    print(f"  総履歴数: {total_history}件")
    print(f"  保存先: {history_file}")
    
    return True

if __name__ == "__main__":
    success = create_test_history()
    if not success:
        exit(1)
