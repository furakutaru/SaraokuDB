import os
import logging
from bs4 import BeautifulSoup
from race_record_extractor import RaceRecordExtractor

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_race_record_cache.log')
    ]
)
logger = logging.getLogger(__name__)

def test_race_record_extraction():
    """キャッシュされたHTMLからレース記録を抽出してテスト"""
    extractor = RaceRecordExtractor()
    cache_dir = "/Users/yum.ishii/SaraokuDB/cache"
    
    # キャッシュディレクトリ内のHTMLファイルを取得
    html_files = [f for f in os.listdir(cache_dir) if f.endswith('.html')]
    
    if not html_files:
        logger.warning("テスト用のキャッシュファイルが見つかりませんでした。")
        return
    
    # 各HTMLファイルに対してテストを実行
    for html_file in html_files:
        file_path = os.path.join(cache_dir, html_file)
        logger.info(f"\n{'='*50}")
        logger.info(f"テストファイル: {file_path}")
        logger.info(f"{'='*50}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # レース記録を抽出
            result, success = extractor.extract(html_content)
            
            if not success:
                logger.warning("レース記録の抽出に失敗しました")
                continue
                
            # 結果を表示
            logger.info("抽出結果:")
            
            # 繁殖牝馬や未出走馬のチェック
            soup = BeautifulSoup(html_content, 'html.parser')
            horse_type = soup.find('title')
            is_broodmare = '繁殖牝馬' in str(horse_type) if horse_type else False
            
            if is_broodmare:
                logger.info("繁殖牝馬のため、レース記録は存在しません。")
                logger.info("このケースは正常に処理されています。")
                return
                
            # サマリー情報
            if result['summary']:
                logger.info("\nサマリー情報:")
                for key, value in result['summary'].items():
                    logger.info(f"  {key}: {value}")
            else:
                logger.info("サマリー情報: 抽出できませんでした")
                
                # 未出走馬の可能性をチェック
                if '未出走' in html_content or '未出走' in str(soup.text):
                    logger.info("未出走馬のため、レース記録は存在しません。")
                    logger.info("このケースは正常に処理されています。")
                    return
            
            # レース記録
            if result['races']:
                logger.info(f"\nレース記録 ({len(result['races'])}件):")
                for i, race in enumerate(result['races'][:3], 1):  # 最初の3レースのみ表示
                    logger.info(f"  {i}. {race.get('date', '日付不明')} {race.get('race_name', 'レース名不明')}")
                    logger.info(f"     競馬場: {race.get('track', '不明')}, 距離: {race.get('distance', '不明')}")
                    logger.info(f"     着順: {race.get('position', '不明')}, タイム: {race.get('time', '不明')}, 騎手: {race.get('jockey', '不明')}")
                if len(result['races']) > 3:
                    logger.info(f"  ... 他 {len(result['races']) - 3}件のレース記録を省略")
            else:
                logger.info("レース記録: 抽出できませんでした")
                
                # 未出走馬の可能性をチェック
                if '未出走' in html_content or '未出走' in str(soup.text):
                    logger.info("未出走馬のため、レース記録は存在しません。")
                    logger.info("このケースは正常に処理されています。")
            
        except Exception as e:
            logger.error(f"エラーが発生しました: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

if __name__ == "__main__":
    test_race_record_extraction()
    logger.info("\nテストが完了しました。詳細はログファイルを確認してください。")
