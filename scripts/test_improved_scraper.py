#!/usr/bin/env python3
"""
improved_scraper.pyのテストスクリプト
1件だけスクレイピングを実行して動作確認する
"""
import os
import sys
import logging
from improved_scraper import ImprovedRakutenScraper, save_scraped_data

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_scraper():
    """スクレイパーのテストを実行"""
    try:
        # データディレクトリのパスを設定
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                              'static-frontend', 'public', 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        logger.info("スクレイパーを初期化中...")
        scraper = ImprovedRakutenScraper(timeout=30, max_retries=3)
        
        # オークション日を取得
        logger.info("オークション情報を取得中...")
        auction_date = scraper.get_auction_date()
        if not auction_date:
            logger.error("オークション日を取得できませんでした")
            return False
            
        logger.info(f"オークション日: {auction_date}")
        
        # テスト用に1件だけ取得
        logger.info("馬リストを取得中...")
        horse_list = scraper.scrape_horse_list()
        
        if not horse_list or len(horse_list) == 0:
            logger.error("馬リストを取得できませんでした")
            return False
            
        # 1件目の馬の詳細を取得
        test_horse = horse_list[0]
        detail_url = test_horse.get('detail_url')
        
        if not detail_url:
            logger.error("詳細URLが見つかりませんでした")
            return False
            
        logger.info(f"テスト対象の馬: {test_horse.get('name', 'N/A')}")
        logger.info(f"詳細URL: {detail_url}")
        
        # 詳細情報を取得
        logger.info("詳細情報を取得中...")
        horse_data = scraper.scrape_horse_detail(detail_url)
        
        if not horse_data:
            logger.error("詳細情報を取得できませんでした")
            return False
            
        logger.info("\n===== 取得した情報 =====")
        for key, value in horse_data.items():
            logger.info(f"{key}: {value}")
            
        # データを保存
        logger.info("\nデータを保存中...")
        success, message = save_scraped_data(horse_data, data_dir)
        
        if success:
            logger.info(f"保存に成功しました: {message}")
        else:
            logger.error(f"保存に失敗しました: {message}")
            
        return success
        
    except Exception as e:
        logger.error(f"テスト中にエラーが発生しました: {str(e)}", exc_info=True)
        return False
    finally:
        if 'scraper' in locals() and hasattr(scraper, 'session'):
            try:
                scraper.session.close()
                logger.info("セッションをクローズしました")
            except Exception as e:
                logger.error(f"セッションのクローズ中にエラーが発生しました: {str(e)}")

if __name__ == "__main__":
    logger.info("===== スクレイピングテストを開始 =====")
    result = test_scraper()
    status = "成功" if result else "失敗"
    logger.info(f"===== スクレイピングテスト {status} =====")
    sys.exit(0 if result else 1)
