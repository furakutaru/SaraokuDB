import sys
import os
import json
import logging
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.absolute()))

from improved_scraper import ImprovedRakutenScraper

def setup_logging():
    """ロギングの設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_horse_details.log')
        ]
    )

def main():
    # ロギングの設定
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # スクレイパーの初期化（キャッシュ有効）
        logger.info("スクレイパーを初期化しています...")
        scraper = ImprovedRakutenScraper(use_cache=True)
        
        # テスト用の馬ID（horses.jsonから最初の馬のIDを使用）
        horses_file = Path('static-frontend/public/data/horses.json')
        if not horses_file.exists():
            logger.error(f"馬データファイルが見つかりません: {horses_file}")
            return 1
            
        # 馬データを読み込む
        try:
            with open(horses_file, 'r', encoding='utf-8') as f:
                horses_data = json.load(f)
                
            if not horses_data.get('horses'):
                logger.error("馬データが空です")
                return 1
                
            # テスト用の馬ID（実際のオークションサイトから取得した有効な馬ID）
            # 例: 実際のオークションサイトで確認した馬のIDに置き換えてください
            test_horse_id = "12345"  # ここに有効な馬IDを設定
            
            if not test_horse_id:
                logger.error("馬IDを抽出できませんでした")
                return 1
                
            logger.info(f"テスト対象の馬ID: {test_horse_id}")
            
            # 馬の詳細情報を取得
            logger.info(f"馬ID: {test_horse_id} の詳細情報を取得します...")
            horse_details = scraper.scrape_horse_details(test_horse_id)
            
            if horse_details:
                # 結果を表示
                logger.info("取得した馬の詳細情報:")
                for key, value in horse_details.items():
                    if key == 'race_records' and isinstance(value, list):
                        logger.info(f"{key}: レコード数 {len(value)}件")
                        # 最初の3件を表示
                        for i, record in enumerate(value[:3], 1):
                            logger.info(f"  レコード {i}: {record}")
                    else:
                        logger.info(f"{key}: {value}")
                
                # 結果をファイルに保存
                output_file = Path('test_horse_details.json')
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(horse_details, f, ensure_ascii=False, indent=2, default=str)
                logger.info(f"結果を {output_file} に保存しました")
                return 0
            else:
                logger.error("馬の詳細情報の取得に失敗しました")
                return 1
                
        except json.JSONDecodeError as e:
            logger.error(f"JSONの解析に失敗しました: {e}")
            return 1
            
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
