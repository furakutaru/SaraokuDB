#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# データファイルのパス
DATA_PATH = Path(__file__).parent.parent / 'static-frontend' / 'public' / 'data' / 'horses_history.json'

class DataIntegrityChecker:
    def __init__(self):
        self.data = self._load_data()
        self.required_fields = {
            'basic': ['id', 'name', 'sex', 'age', 'sire', 'dam', 'damsire', 'weight', 'seller', 'auction_date', 'sold_price', 'detail_url', 'image_url', 'comment', 'disease_tags'],
            'history': ['auction_date', 'sold_price', 'total_prize_start', 'total_prize_latest']
        }
        self.results = {
            'summary': {'total_horses': 0, 'horses_with_issues': 0, 'total_issues': 0},
            'issues': []
        }

    def _load_data(self) -> Dict:
        """データを読み込む"""
        if not DATA_PATH.exists():
            raise FileNotFoundError(f"データファイルが見つかりません: {DATA_PATH}")
        
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _is_valid_value(self, value: Any, field_name: str) -> bool:
        """値が有効かチェックする"""
        if value is None:
            return False
        
        if isinstance(value, (str, list, dict)):
            if not value:  # 空文字、空リスト、空辞書
                return False
            
            if field_name == 'comment' and value == '取得できませんでした':
                return False
                
            if field_name == 'disease_tags' and value == ['']:
                return False
                
        return True

    def check_horse_data(self, horse: Dict) -> List[Dict]:
        """1頭分のデータをチェックする"""
        issues = []
        
        # 基本情報のチェック
        for field in self.required_fields['basic']:
            if field not in horse:
                issues.append({'field': field, 'issue': 'フィールドが存在しません'})
            elif not self._is_valid_value(horse[field], field):
                issues.append({
                    'field': field,
                    'issue': f'無効な値です: {horse[field]}',
                    'value': horse[field]
                })
        
        # 履歴情報のチェック
        if 'history' in horse and horse['history']:
            for i, history in enumerate(horse['history']):
                for field in self.required_fields['history']:
                    if field not in history:
                        issues.append({
                            'field': f'history[{i}].{field}',
                            'issue': 'フィールドが存在しません'
                        })
                    elif not self._is_valid_value(history[field], field):
                        issues.append({
                            'field': f'history[{i}].{field}',
                            'issue': f'無効な値です: {history[field]}',
                            'value': history[field]
                        })
        else:
            issues.append({'field': 'history', 'issue': '履歴情報が存在しません'})
        
        # 画像URLの存在確認
        if 'image_url' in horse and horse['image_url']:
            if not horse['image_url'].startswith(('http://', 'https://')):
                issues.append({
                    'field': 'image_url',
                    'issue': '無効なURL形式です',
                    'value': horse['image_url']
                })
        
        # オークション日付の形式チェック
        if 'auction_date' in horse and horse['auction_date']:
            try:
                datetime.strptime(horse['auction_date'], '%Y-%m-%d')
            except (ValueError, TypeError):
                issues.append({
                    'field': 'auction_date',
                    'issue': '日付形式が不正です (YYYY-MM-DD形式である必要があります)',
                    'value': horse['auction_date']
                })
        
        return issues

    def run_checks(self) -> Dict:
        """全てのチェックを実行する"""
        if 'horses' not in self.data:
            raise ValueError("データに'horses'キーが存在しません")
        
        self.results['summary']['total_horses'] = len(self.data['horses'])
        
        self.results['summary']['horses_with_issues'] = 0
        
        for horse in self.data['horses']:
            issues = self.check_horse_data(horse)
            if issues:
                self.results['summary']['horses_with_issues'] += 1
                self.results['issues'].append({
                    'id': horse.get('id', '不明'),
                    'name': horse.get('name', '不明'),
                    'issues': issues
                })
                self.results['summary']['total_issues'] += len(issues)
        
        return self.results

    def print_results(self):
        """結果を表示する"""
        print("\n=== データ整合性チェック結果 ===\n")
        print(f"総馬数: {self.results['summary']['total_horses']}")
        print(f"問題のある馬: {self.results.get('horses_with_issues', 0)}頭")
        print(f"総問題数: {self.results['summary']['total_issues']}\n")
        
        if not self.results['issues']:
            print("✅ 問題は見つかりませんでした")
            return
        
        for horse_issues in self.results['issues']:
            print(f"\n🐴 {horse_issues['name']} (ID: {horse_issues['id']})")
            for issue in horse_issues['issues']:
                print(f"  ❌ {issue['field']}: {issue['issue']}")
                if 'value' in issue:
                    print(f"     値: {issue['value']}")


def main():
    try:
        checker = DataIntegrityChecker()
        results = checker.run_checks()
        checker.print_results()
        
        # 問題があれば終了コード1で終了
        if results['summary']['total_issues'] > 0:
            exit(1)
            
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        exit(1)


if __name__ == '__main__':
    main()
