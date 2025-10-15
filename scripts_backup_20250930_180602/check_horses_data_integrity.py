#!/usr/bin/env python3
"""
馬データの整合性チェックスクリプト
- horses_history.json の全馬データをチェックし、必須項目の欠落を検出
"""

import json
import os
from typing import Dict, List, Set, Optional
from collections import defaultdict

def load_horses_data(file_path: str) -> Dict:
    """horses_history.json を読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"ファイルの読み込みに失敗しました: {e}")
        return {}

def check_horse_integrity(horse: Dict) -> Dict:
    """1頭分の馬データの整合性をチェック"""
    required_fields = [
        'id', 'name', 'sex', 'age', 'sire', 'dam', 'damsire', 'weight',
        'seller', 'auction_date', 'comment', 'disease_tags', 'primary_image',
        'total_prize_latest', 'jbis_url', 'detail_url'
    ]
    
    result = {
        'id': horse.get('id'),
        'name': horse.get('name'),
        'missing_fields': [],
        'empty_fields': [],
        'history_count': len(horse.get('history', [])),
        'history_missing_fields': defaultdict(int),
        'history_empty_fields': defaultdict(int)
    }
    
    # トップレベルの必須フィールドチェック
    for field in required_fields:
        if field not in horse:
            result['missing_fields'].append(field)
        elif not horse[field] and horse[field] != 0:  # 0は有効な値として扱う
            result['empty_fields'].append(field)
    
    # 履歴データのチェック
    history_required_fields = [
        'auction_date', 'sold_price', 'total_prize_start', 'total_prize_latest'
    ]
    
    for history in horse.get('history', []):
        for field in history_required_fields:
            if field not in history:
                result['history_missing_fields'][field] += 1
            elif not history[field] and history[field] != 0:  # 0は有効な値として扱う
                result['history_empty_fields'][field] += 1
    
    return result

def main():
    # ファイルパス
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    history_file = os.path.join(project_root, 'static-frontend', 'public', 'data', 'horses_history.json')
    
    # データ読み込み
    print(f"データファイルを読み込み中: {history_file}")
    data = load_horses_data(history_file)
    
    if not data or 'horses' not in data:
        print("無効なデータ形式、またはデータが空です。")
        return
    
    horses = data['horses']
    print(f"\n=== 馬データ整合性チェック ===")
    print(f"総馬数: {len(horses)}頭")
    
    # 全馬の整合性チェック
    results = []
    for horse in horses:
        results.append(check_horse_integrity(horse))
    
    # 集計
    missing_fields = defaultdict(int)
    empty_fields = defaultdict(int)
    history_missing = defaultdict(int)
    history_empty = defaultdict(int)
    
    for result in results:
        for field in result['missing_fields']:
            missing_fields[field] += 1
        for field in result['empty_fields']:
            empty_fields[field] += 1
        
        for field, count in result['history_missing_fields'].items():
            history_missing[field] += count
        for field, count in result['history_empty_fields'].items():
            history_empty[field] += count
    
    # 結果表示
    print("\n=== トップレベルの欠落フィールド ===")
    if missing_fields:
        for field, count in sorted(missing_fields.items(), key=lambda x: x[1], reverse=True):
            print(f"  {field}: {count}頭")
    else:
        print("  欠落フィールドはありません")
    
    print("\n=== トップレベルの空フィールド ===")
    if empty_fields:
        for field, count in sorted(empty_fields.items(), key=lambda x: x[1], reverse=True):
            print(f"  {field}: {count}頭")
    else:
        print("  空フィールドはありません")
    
    print("\n=== 履歴データの欠落フィールド ===")
    if history_missing:
        for field, count in sorted(history_missing.items(), key=lambda x: x[1], reverse=True):
            print(f"  {field}: {count}件")
    else:
        print("  欠落フィールドはありません")
    
    print("\n=== 履歴データの空フィールド ===")
    if history_empty:
        for field, count in sorted(history_empty.items(), key=lambda x: x[1], reverse=True):
            print(f"  {field}: {count}件")
    else:
        print("  空フィールドはありません")
    
    # 問題がある馬の詳細を表示
    problem_horses = [r for r in results if r['missing_fields'] or r['empty_fields'] or 
                     r['history_missing_fields'] or r['history_empty_fields']]
    
    if problem_horses:
        print("\n=== 問題のある馬の詳細 ===")
        for horse in problem_horses[:10]:  # 最初の10頭のみ表示
            print(f"\nID: {horse['id']}, 馬名: {horse['name']}")
            if horse['missing_fields']:
                print(f"  欠落フィールド: {', '.join(horse['missing_fields'])}")
            if horse['empty_fields']:
                print(f"  空フィールド: {', '.join(horse['empty_fields'])}")
            if horse['history_missing_fields']:
                print(f"  履歴欠落: {dict(horse['history_missing_fields'])}")
            if horse['history_empty_fields']:
                print(f"  履歴空: {dict(horse['history_empty_fields'])}")
        
        if len(problem_horses) > 10:
            print(f"\n...他{len(problem_horses) - 10}頭の馬に問題があります")
    else:
        print("\n問題は見つかりませんでした。")

if __name__ == "__main__":
    main()
