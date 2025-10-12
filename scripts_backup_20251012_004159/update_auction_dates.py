#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
既存の馬データのオークション日を更新するスクリプト

このスクリプトは、既存の馬データに対してオークション日を取得・更新します。
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.improved_scraper import ImprovedRakutenScraper, ScraperConfig

# ロギング設定
def setup_logging():
    """ロギングの設定を行う"""
    log_dir = Path('debug_logs')
    log_dir.mkdir(exist_ok=True, mode=0o755)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'update_auction_dates.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def load_horses_data() -> list:
    """馬データを読み込む"""
    data_dir = project_root / 'static-frontend' / 'public' / 'data'
    horses_file = data_dir / 'horses.json'
    
    if not horses_file.exists():
        logger.error(f"馬データファイルが見つかりません: {horses_file}")
        return []
    
    try:
        with open(horses_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'items' in data:
                return data['items']
            return data if isinstance(data, list) else []
    except Exception as e:
        logger.error(f"馬データの読み込み中にエラーが発生しました: {e}", exc_info=True)
        return []

def save_horses_data(horses: list):
    """馬データを保存する"""
    data_dir = project_root / 'static-frontend' / 'public' / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # バックアップを作成
    backup_dir = data_dir / 'backups'
    backup_dir.mkdir(exist_ok=True)
    
    # 既存のファイルをバックアップ
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    horses_file = data_dir / 'horses.json'
    if horses_file.exists():
        backup_file = backup_dir / f'horses_backup_{timestamp}.json'
        import shutil
        shutil.copy2(horses_file, backup_file)
        logger.info(f"バックアップを作成しました: {backup_file}")
    
    # データを保存
    try:
        with open(horses_file, 'w', encoding='utf-8') as f:
            json.dump({'items': horses, 'total': len(horses), 'updated_at': timestamp}, f, 
                     ensure_ascii=False, indent=2)
        logger.info(f"馬データを更新しました: {horses_file}")
        return True
    except Exception as e:
        logger.error(f"馬データの保存中にエラーが発生しました: {e}", exc_info=True)
        return False

def update_auction_dates():
    """既存の馬データのオークション日を更新する"""
    logger.info("オークション日更新処理を開始します")
    
    # スクレイパーを初期化
    config = ScraperConfig(
        use_cache=True,
        max_retries=3,
        timeout=30
    )
    scraper = ImprovedRakutenScraper(config=config)
    
    # 馬データを読み込む
    horses = load_horses_data()
    if not horses:
        logger.error("馬データを読み込めませんでした")
        return False
    
    logger.info(f"{len(horses)}件の馬データを読み込みました")
    
    updated_count = 0
    
    for horse in horses:
        horse_id = horse.get('id')
        horse_name = horse.get('name', '不明')
        
        if not horse_id:
            logger.warning(f"IDが設定されていない馬がいます: {horse}")
            continue
        
        # 既にオークション日が設定されているか確認
        current_auction_date = horse.get('auction_date')
        if current_auction_date:
            logger.info(f"[{horse_id}] {horse_name}: 既にオークション日が設定されています: {current_auction_date}")
            continue
        
        logger.info(f"[{horse_id}] {horse_name}: オークション日を取得中...")
        
        try:
            # オークション日を取得
            auction_date = scraper.get_auction_date(
                url=f"https://auction.keiba.rakuten.co.jp/item/{horse_id}"
            )
            
            if auction_date:
                horse['auction_date'] = auction_date
                updated_count += 1
                logger.info(f"  → オークション日を更新しました: {auction_date}")
            else:
                logger.warning("  → オークション日を取得できませんでした")
                
        except Exception as e:
            logger.error(f"  → エラーが発生しました: {e}", exc_info=True)
    
    # 更新があった場合のみ保存
    if updated_count > 0:
        logger.info(f"{updated_count}件の馬データを更新しました")
        return save_horses_data(horses)
    else:
        logger.info("更新するデータはありませんでした")
        return True

if __name__ == "__main__":
    logger = setup_logging()
    
    try:
        success = update_auction_dates()
        if success:
            logger.info("オークション日更新処理が正常に完了しました")
            sys.exit(0)
        else:
            logger.error("オークション日更新処理に失敗しました")
            sys.exit(1)
    except Exception as e:
        logger.critical(f"予期しないエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)
