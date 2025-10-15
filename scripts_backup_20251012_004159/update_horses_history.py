#!/usr/bin/env python3
"""
`horses.json` のデータを `horses_history.json` に反映させるスクリプト
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any

def load_json_file(file_path: str) -> Any:
    """JSONファイルを読み込む"""
    if not os.path.exists(file_path):
        return {"metadata": {"last_updated": "", "total_horses": 0}, "horses": []}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(file_path: str, data: Any) -> None:
    """JSONファイルにデータを保存する"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def convert_to_history_format(horses_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """馬のデータを履歴形式に変換する"""
    now = datetime.now().isoformat()
    
    # メタデータを準備
    metadata = {
        "last_updated": now,
        "total_horses": len(horses_data),
        "version": "1.0.0"
    }
    
    # 各馬のデータを変換
    horses_history = []
    for horse in horses_data:
        # 必須フィールドのデフォルト値を設定
        horse_id = horse.get('id', '')
        name = horse.get('name', '不明')
        age = horse.get('age', 0)
        
        # 履歴データを作成
        history_entry = {
            "id": horse_id,
            "name": name,
            "age": age,
            "sex": horse.get('sex', ''),
            "sire": horse.get('sire', ''),
            "dam": horse.get('dam', ''),
            "damsire": horse.get('damsire', ''),
            "image_url": horse.get('image_url', ''),
            "jbis_url": horse.get('jbis_url', ''),
            "auction_url": horse.get('auction_url', ''),
            "disease_tags": horse.get('disease_tags', []),
            "comment": horse.get('comment', ''),
            "race_record": horse.get('race_record', ''),
            "weight": horse.get('weight', ''),
            "seller": horse.get('seller', ''),
            "auction_date": horse.get('auction_date', ''),
            "total_prize_start": horse.get('total_prize_start', 0.0),
            "total_prize_latest": horse.get('total_prize_latest', 0.0),
            "created_at": horse.get('created_at', now),
            "updated_at": horse.get('updated_at', now),
            "history": [
                {
                    "auction_date": horse.get('auction_date', ''),
                    "sold_price": horse.get('sold_price', None),
                    "seller": horse.get('seller', ''),
                    "weight": horse.get('weight', None),
                    "comment": horse.get('comment', ''),
                    "created_at": horse.get('created_at', now)
                }
            ]
        }
        horses_history.append(history_entry)
    
    return {
        "metadata": metadata,
        "horses": horses_history
    }

def main():
    # ファイルパスを設定
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # 入力ファイルと出力ファイルのパス
    input_file = os.path.join(project_root, "static-frontend", "public", "data", "horses.json")
    output_file = os.path.join(project_root, "static-frontend", "public", "data", "horses_history.json")
    
    print(f"入力ファイル: {input_file}")
    print(f"出力ファイル: {output_file}")
    
    # 既存のデータを読み込む
    print("データを読み込んでいます...")
    existing_history = load_json_file(output_file)
    horses_data = load_json_file(input_file).get("horses", [])
    
    # データを変換
    print(f"{len(horses_data)}頭の馬データを処理中...")
    history_data = convert_to_history_format(horses_data)
    
    # 既存の履歴とマージ（必要に応じて実装）
    # ここでは単純に上書きする
    
    # ファイルに保存
    print(f"データを保存しています...")
    save_json_file(output_file, history_data)
    
    print(f"完了しました！ {len(history_data['horses'])}頭の馬データを保存しました。")
    print(f"出力先: {output_file}")

if __name__ == "__main__":
    main()
