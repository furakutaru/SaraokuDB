#!/usr/bin/env python3
"""
SaraokuDB データ更新エントリーポイントスクリプト

このスクリプトは、以下の処理を順番に実行します：
1. オークションデータのスクレイピング (improved_scraper.py)
2. JBIS賞金情報の更新 (update_jbis_history_data.py)

各スクリプトは独立して実行され、エラーが発生しても次のスクリプトの実行を試みます。
"""

import sys
import os
import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('run_updates.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def run_script(script_name: str, script_func, *args, **kwargs) -> bool:
    """スクリプトを実行し、結果をログに記録するヘルパー関数"""
    logger.info(f"=== {script_name} を開始します ===")
    start_time = datetime.now()
    
    try:
        # スクリプトを実行
        result = script_func(*args, **kwargs)
        
        # 実行時間を計算
        duration = datetime.now() - start_time
        logger.info(f"=== {script_name} が正常に完了しました (所要時間: {duration}) ===")
        return True
        
    except Exception as e:
        # エラーをログに記録
        error_msg = f"{script_name} の実行中にエラーが発生しました: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return False

def run_auction_scraper() -> bool:
    """オークションデータのスクレイピングを実行"""
    try:
        from improved_scraper import main as auction_main
        return auction_main() == 0  # main() は 0 を返すと成功
    except ImportError as e:
        logger.error("improved_scraper.py のインポートに失敗しました")
        logger.error(traceback.format_exc())
        return False

def run_jbis_updater() -> bool:
    """JBIS賞金情報の更新を実行"""
    try:
        from update_jbis_history_data import main as jbis_main
        jbis_main()
        return True
    except ImportError as e:
        logger.error("update_jbis_history_data.py のインポートに失敗しました")
        logger.error(traceback.format_exc())
        return False

def main() -> int:
    """メイン実行関数"""
    logger.info("=== SaraokuDB データ更新処理を開始します ===")
    start_time = datetime.now()
    
    # 各スクリプトの実行結果を記録
    results = {
        'auction_scraper': False,
        'jbis_updater': False
    }
    
    # 1. オークションデータのスクレイピング
    results['auction_scraper'] = run_script(
        "オークションデータスクレイピング",
        run_auction_scraper
    )
    
    # 2. JBIS賞金情報の更新
    results['jbis_updater'] = run_script(
        "JBIS賞金情報更新",
        run_jbis_updater
    )
    
    # 実行結果のサマリーをログに記録
    total_duration = datetime.now() - start_time
    success_count = sum(1 for r in results.values() if r)
    total_count = len(results)
    
    logger.info("\n=== 実行結果サマリー ===")
    logger.info(f"完了した処理: {success_count}/{total_count}")
    logger.info(f"合計所要時間: {total_duration}")
    
    for name, success in results.items():
        status = "成功" if success else "失敗"
        logger.info(f"- {name}: {status}")
    
    # いずれかの処理が失敗していたらエラーコードを返す
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    sys.exit(main())
