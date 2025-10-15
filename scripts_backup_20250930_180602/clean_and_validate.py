#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data_cleaning.log')
    ]
)
logger = logging.getLogger(__name__)

class HorseDataCleaner:
    def __init__(self, input_file: str, output_file: str):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.data: Dict[str, Any] = {}
        self.required_fields = ['name', 'auction_date', 'sire', 'dam', 'damsire', 'sex', 'age']
        self.backup_created = False

    def load_data(self) -> bool:
        """データを読み込む"""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            logger.info(f"データを読み込みました: {len(self.data.get('horses', []))} 件の馬データ")
            return True
        except Exception as e:
            logger.error(f"データの読み込みに失敗しました: {e}")
            return False

    def create_backup(self) -> bool:
        """バックアップを作成"""
        if not self.input_file.exists():
            logger.error("入力ファイルが見つかりません")
            return False
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.input_file.parent / f"{self.input_file.stem}_backup_{timestamp}{self.input_file.suffix}"
        
        try:
            import shutil
            shutil.copy2(self.input_file, backup_file)
            logger.info(f"バックアップを作成しました: {backup_file}")
            self.backup_created = True
            return True
        except Exception as e:
            logger.error(f"バックアップの作成に失敗しました: {e}")
            return False

    def clean_data(self) -> bool:
        """データをクリーニング"""
        if not self.data or 'horses' not in self.data:
            logger.error("クリーニングするデータがありません")
            return False

        cleaned_horses = []
        missing_fields = set()
        
        for horse in self.data.get('horses', []):
            # 必要なフィールドの存在を確認
            missing = [field for field in self.required_fields if field not in horse or not horse[field]]
            if missing:
                missing_fields.update(missing)
                logger.warning(f"馬 '{horse.get('name', '不明')}' に不足しているフィールド: {', '.join(missing)}")
            
            # 母馬名の修正
            if horse.get('dam') == 'テメノスの娘':
                horse['dam'] = 'テメノス'
                logger.info(f"母馬名を修正: テメノスの娘 → テメノス (馬名: {horse.get('name', '不明')})")
            
            # 必要なフィールドのみを保持
            cleaned_horse = {
                'id': horse.get('id'),
                'name': horse.get('name'),
                'sex': horse.get('sex'),
                'age': horse.get('age'),
                'seller': horse.get('seller'),
                'detail_url': horse.get('detail_url'),
                'jbis_url': horse.get('jbis_url'),
                'sire': horse.get('sire'),
                'dam': horse.get('dam'),
                'damsire': horse.get('damsire'),
                'auction_date': horse.get('auction_date', datetime.now().strftime('%Y-%m-%d')),
                'created_at': horse.get('created_at', datetime.now().isoformat()),
                'updated_at': datetime.now().isoformat()
            }
            
            # オークション履歴がある場合は追加
            if 'history' in horse:
                cleaned_horse['history'] = horse['history']
            
            cleaned_horses.append(cleaned_horse)
        
        if missing_fields:
            logger.warning(f"以下の必須フィールドが不足しているデータがあります: {', '.join(missing_fields)}")
        
        self.data['horses'] = cleaned_horses
        self.data['metadata'] = {
            'last_updated': datetime.now().isoformat(),
            'total_horses': len(cleaned_horses),
            'version': '1.0.0',
            'cleaned_at': datetime.now().isoformat()
        }
        
        return True

    def save_data(self) -> bool:
        """データを保存"""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            logger.info(f"データを保存しました: {self.output_file}")
            return True
        except Exception as e:
            logger.error(f"データの保存に失敗しました: {e}")
            return False

def main():
    # 入力ファイルと出力ファイルのパス
    input_file = "/Users/yum.ishii/SaraokuDB/static-frontend/public/data/horses.json"
    output_file = "/Users/yum.ishii/SaraokuDB/static-frontend/public/data/horses_cleaned.json"
    
    cleaner = HorseDataCleaner(input_file, output_file)
    
    # バックアップを作成
    if not cleaner.create_backup():
        logger.error("バックアップの作成に失敗したため、処理を中止します")
        return
    
    # データを読み込む
    if not cleaner.load_data():
        return
    
    # データをクリーニング
    if not cleaner.clean_data():
        return
    
    # データを保存
    if not cleaner.save_data():
        return
    
    logger.info("データのクリーニングが完了しました")

if __name__ == "__main__":
    main()
