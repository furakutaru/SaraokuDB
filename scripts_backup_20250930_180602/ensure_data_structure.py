#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

# データファイルのパス
DATA_DIR = Path(__file__).parent.parent / 'static-frontend' / 'public' / 'data'
HISTORY_FILE = DATA_DIR / 'horses_history.json'

def clean_text(text: Any) -> str:
    """テキストをクリーンアップ（改行と連続した空白を1つのスペースに）"""
    if not isinstance(text, str):
        return ""
    # 改行とタブをスペースに置換
    text = text.replace('\n', ' ').replace('\t', ' ')
    # 連続したスペースを1つに
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def ensure_structure(data: Dict) -> Dict:
    """データ構造を保証する（値は変更しない）"""
    # メタデータはそのまま保持
    result = {
        'metadata': data.get('metadata', {}),
        'horses': []
    }
    
    # 各馬のデータを処理
    for horse in data.get('horses', []):
        # 新しい馬データを作成（既存のデータを保持）
        new_horse = {**horse}
        
        # 必須フィールドが存在することを確認（存在しなければNoneを設定）
        for field in ['id', 'name', 'sex', 'age', 'sire', 'dam', 'dam_sire', 
                     'weight', 'seller', 'auction_date', 'sold_price', 
                     'detail_url', 'image_url', 'comment', 'disease_tags', 
                     'primary_image', 'total_prize_latest', 'jbis_url', 
                     'created_at', 'updated_at']:
            if field not in new_horse:
                if field == 'disease_tags':
                    new_horse[field] = []
                elif field == 'weight' or field == 'sold_price' or field == 'total_prize_latest':
                    new_horse[field] = None
                else:
                    new_horse[field] = ""
        
        # テキストフィールドのクリーンアップ
        for field in ['name', 'sex', 'age', 'sire', 'dam', 'dam_sire', 'seller', 
                     'comment', 'primary_image', 'detail_url', 'image_url', 'jbis_url']:
            if field in new_horse and new_horse[field] is not None:
                new_horse[field] = clean_text(new_horse[field])
        
        # 履歴データの処理
        if 'history' not in new_horse or not isinstance(new_horse['history'], list):
            new_horse['history'] = []
        
        # 各履歴エントリを処理
        for i, history in enumerate(new_horse['history']):
            new_history = {**history}
            
            # 必須フィールドが存在することを確認
            for field in ['auction_date', 'sold_price', 'total_prize_start', 'total_prize_latest']:
                if field not in new_history:
                    new_history[field] = None
            
            # テキストフィールドのクリーンアップ
            if 'auction_date' in new_history and new_history['auction_date'] is not None:
                new_history['auction_date'] = clean_text(new_history['auction_date'])
            
            new_horse['history'][i] = new_history
        
        # 更新日時を設定
        new_horse['updated_at'] = datetime.now().isoformat()
        
        # 作成日時がなければ現在時刻を設定
        if not new_horse.get('created_at'):
            new_horse['created_at'] = datetime.now().isoformat()
        
        result['horses'].append(new_horse)
    
    return result

def main():
    try:
        print("=== データ構造の整合性を確認・修正します ===")
        
        # データを読み込む
        print(f"データファイルを読み込み中: {HISTORY_FILE}")
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # データ構造を整える
        print("データ構造を確認・修正中...")
        fixed_data = ensure_structure(data)
        
        # 修正したデータを保存
        print(f"修正したデータを保存中: {HISTORY_FILE}")
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(fixed_data, f, ensure_ascii=False, indent=2)
        
        print("=== データ構造の修正が完了しました ===")
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    from datetime import datetime
    exit(main())
