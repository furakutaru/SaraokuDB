#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# データファイルのパス
DATA_DIR = Path(__file__).parent.parent / 'static-frontend' / 'public' / 'data'
HISTORY_FILE = DATA_DIR / 'horses_history.json'

# 必須フィールドとデフォルト値
REQUIRED_FIELDS = {
    'basic': {
        'id': None,  # 必須（自動設定）
        'name': '',  # 必須
        'sex': '',
        'age': '',
        'sire': '',
        'dam': '',
        'dam_sire': '',
        'weight': None,
        'seller': '',
        'auction_date': '',
        'sold_price': None,
        'detail_url': '',
        'image_url': '',
        'comment': '',
        'disease_tags': [],
        'primary_image': '',
        'total_prize_latest': 0.0,
        'created_at': '',
        'updated_at': ''
    },
    'history': {
        'auction_date': '',
        'sold_price': None,
        'total_prize_start': 0.0,
        'total_prize_latest': 0.0
    }
}

def load_data(file_path: Path) -> Dict:
    """データを読み込む"""
    if not file_path.exists():
        raise FileNotFoundError(f"データファイルが見つかりません: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(file_path: Path, data: Dict) -> None:
    """データを保存する"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ensure_required_fields(data: Dict) -> Dict:
    """データに必須フィールドが存在することを保証する"""
    # メタデータはそのまま保持
    fixed_data = {
        'metadata': data.get('metadata', {}),
        'horses': []
    }
    
    # 各馬のデータを処理
    for horse in data.get('horses', []):
        fixed_horse = {}
        
        # 基本情報をデフォルト値で初期化
        for field, default_value in REQUIRED_FIELDS['basic'].items():
            if field in horse:
                fixed_horse[field] = horse[field]
            else:
                # デフォルト値がNoneの場合は、元のデータがあればそれを使用
                if default_value is None and field in horse:
                    fixed_horse[field] = horse[field]
                else:
                    fixed_horse[field] = default_value
        
        # historyが存在しない場合は空のリストで初期化
        if 'history' not in horse or not isinstance(horse['history'], list):
            fixed_horse['history'] = []
        else:
            # 各履歴エントリを処理
            fixed_history = []
            for history in horse['history']:
                fixed_entry = {}
                for field, default_value in REQUIRED_FIELDS['history'].items():
                    if field in history:
                        fixed_entry[field] = history[field]
                    else:
                        fixed_entry[field] = default_value
                fixed_history.append(fixed_entry)
            fixed_horse['history'] = fixed_history
        
        # 更新日時を設定
        fixed_horse['updated_at'] = datetime.now().isoformat()
        
        # 作成日時がなければ現在時刻を設定
        if 'created_at' not in fixed_horse or not fixed_horse['created_at']:
            fixed_horse['created_at'] = datetime.now().isoformat()
        
        fixed_data['horses'].append(fixed_horse)
    
    return fixed_data

def main():
    try:
        print("=== データ整合性チェックと修正を開始します ===")
        
        # データを読み込む
        print(f"データファイルを読み込み中: {HISTORY_FILE}")
        data = load_data(HISTORY_FILE)
        
        # データを修正
        print("データの整合性をチェックして修正中...")
        fixed_data = ensure_required_fields(data)
        
        # 修正したデータを保存
        print(f"修正したデータを保存中: {HISTORY_FILE}")
        save_data(HISTORY_FILE, fixed_data)
        
        print("=== データの修正が完了しました ===")
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
