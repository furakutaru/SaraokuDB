#!/usr/bin/env python3
"""
既存データの馬体重をトップレベルに追加するスクリプト
履歴内の最新体重をトップレベルの weight フィールドに設定
"""

import json
import os
from typing import Dict, List, Optional

def get_latest_weight(history: List[Dict]) -> Optional[int]:
    """履歴から最新の体重を取得"""
    if not history:
        return None
    
    # 履歴を日付順でソート（最新が最後）
    sorted_history = sorted(history, key=lambda x: x.get('auction_date', ''))
    
    # 最新の履歴から体重を取得
    for entry in reversed(sorted_history):
        weight = entry.get('weight')
        if weight is not None:
            return weight
    
    return None

def fix_weight_data():
    """既存データの体重をトップレベルに追加"""
    # プロジェクトルートからの絶対パスを使用
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    history_file = os.path.join(project_root, "static-frontend", "public", "data", "horses_history.json")
    
    print(f"=== 馬体重データ修正開始 ===")
    print(f"対象ファイル: {history_file}")
    
    # 既存データを読み込み
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません: {history_file}")
        return False
    except json.JSONDecodeError as e:
        print(f"エラー: JSONの読み込みに失敗しました: {e}")
        return False
    
    horses = data.get('horses', [])
    print(f"総馬数: {len(horses)}頭")
    
    # 各馬の体重データを修正
    fixed_count = 0
    already_fixed_count = 0
    no_weight_count = 0
    
    for horse in horses:
        horse_name = horse.get('name', 'Unknown')
        current_weight = horse.get('weight')
        history = horse.get('history', [])
        
        # 履歴から最新体重を取得
        latest_weight = get_latest_weight(history)
        
        if latest_weight is not None:
            if current_weight != latest_weight:
                horse['weight'] = latest_weight
                fixed_count += 1
                print(f"修正: {horse_name} -> {latest_weight}kg")
            else:
                already_fixed_count += 1
        else:
            no_weight_count += 1
            # 体重データがない場合はNoneを明示的に設定
            horse['weight'] = None
    
    print(f"\n=== 修正結果 ===")
    print(f"修正した馬: {fixed_count}頭")
    print(f"既に正しい馬: {already_fixed_count}頭")
    print(f"体重データなし: {no_weight_count}頭")
    
    # 修正したデータを保存
    if fixed_count > 0 or no_weight_count > 0:
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n✅ データファイルを更新しました: {history_file}")
            return True
        except Exception as e:
            print(f"❌ ファイルの保存に失敗しました: {e}")
            return False
    else:
        print("\n✅ 修正の必要がありませんでした")
        return True

if __name__ == "__main__":
    success = fix_weight_data()
    if success:
        print("\n🎉 馬体重データの修正が完了しました！")
    else:
        print("\n❌ 馬体重データの修正に失敗しました")
