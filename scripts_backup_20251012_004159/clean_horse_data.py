#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
馬データのクリーニングスクリプト
- 不要なフィールドを削除
- 母名の誤りを修正
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def clean_horse_data(horse: Dict[str, Any]) -> Dict[str, Any]:
    """馬のデータから不要なフィールドを削除し、データをクリーニングする"""
    # 削除する不要なフィールド（必ず保持するフィールドは除外）
    fields_to_remove = [
        'pedigree_pdf',  # PDFリンクは不要
        # 'birthday',    # 生年月日は保持（必要に応じてコメントアウトを外す）
        # 'scraped_at',  # スクレイピング日時は保持（必要に応じてコメントアウトを外す）
    ]
    
    # 必須フィールドの確認
    required_fields = ['name', 'auction_date', 'sire', 'dam', 'damsire']
    
    # 新しい辞書を作成し、必要なフィールドを残す
    cleaned = {}
    for key, value in horse.items():
        if key not in fields_to_remove and value is not None:
            # 空文字列の場合はNoneに変換
            cleaned[key] = value if value != '' else None
    
    # 母名の修正
    if cleaned.get('dam') == 'テメノスの娘':
        cleaned['dam'] = 'テメノス'  # 正しい母名に修正
    
    # 必須フィールドが存在するか確認
    for field in required_fields:
        if field not in cleaned:
            logger.warning(f"必須フィールドが不足しています: {field} (馬名: {cleaned.get('name', '不明')})")
    
    return cleaned

def process_file(input_path: str, output_path: str = None):
    """JSONファイルを処理してクリーニングする"""
    if output_path is None:
        output_path = input_path
    
    # 入力ファイルを読み込む
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # データをクリーニング
    if 'horses' in data and isinstance(data['horses'], list):
        data['horses'] = [clean_horse_data(horse) for horse in data['horses']]
    
    # 出力先のディレクトリが存在することを確認
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # クリーニングしたデータを保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"データをクリーニングしました: {output_path}")

if __name__ == "__main__":
    # メインのデータファイルを処理
    data_dir = Path("/Users/yum.ishii/SaraokuDB/static-frontend/public/data")
    input_file = data_dir / "horses.json"
    
    # バックアップを作成
    backup_file = data_dir / "horses.json.backup"
    if input_file.exists() and not backup_file.exists():
        import shutil
        shutil.copy2(input_file, backup_file)
        print(f"バックアップを作成しました: {backup_file}")
    
    # ファイルを処理
    if input_file.exists():
        process_file(str(input_file))
    else:
        print(f"エラー: 入力ファイルが見つかりません: {input_file}")
        
    # 他のデータファイルも同様に処理
    other_files = [
        "/Users/yum.ishii/SaraokuDB/backend/static-frontend/public/data/horses.json",
        "/Users/yum.ishii/SaraokuDB/backend/data/horses.json",
        "/Users/yum.ishii/SaraokuDB/scripts/static-frontend/public/data/horses.json",
        "/Users/yum.ishii/SaraokuDB/static-frontend/public/data/backup/horses.json"
    ]
    
    for file_path in other_files:
        if Path(file_path).exists():
            process_file(file_path)
        else:
            print(f"警告: ファイルが存在しません: {file_path}")
