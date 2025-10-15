import sys
import os
import logging
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.append(project_root)

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_scraper.log')
    ]
)
logger = logging.getLogger(__name__)

try:
    logger.info("スクレイパーのインポートを開始します...")
    from scripts.improved_scraper import ImprovedRakutenScraper
    
    logger.info("スクレイパーの初期化を開始します...")
    scraper = ImprovedRakutenScraper(test_mode=True)
    
    logger.info("馬のリストを取得します...")
    result = scraper.scrape_horse_list()
    
    print(f"\n取得した馬の数: {len(result)}")
    if result:
        print("\n最初の馬の情報:")
        for key, value in result[0].items():
            print(f"  {key}: {value}")
    else:
        print("馬の情報を取得できませんでした。")
        
except Exception as e:
    logger.error("エラーが発生しました:", exc_info=True)
    print(f"\nエラーが発生しました: {str(e)}")
    print("\n詳細はログファイルを確認してください。")
    
    # スタックトレースを表示
    import traceback
    traceback.print_exc()
