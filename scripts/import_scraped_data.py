import sys
import json
from pathlib import Path
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.database.models import SessionLocal, Horse
from backend.scrapers.rakuten_scraper import RakutenAuctionScraper
from backend.services.horse_service import HorseService

def map_horse_data(scraped_data):
    """スクレイピングしたデータをHorseモデルにマッピング"""
    # 必須フィールドのデフォルト値設定
    horse_data = {
        'name': scraped_data.get('name', ''),
        'sex': json.dumps([scraped_data.get('sex', '')]),
        'age': json.dumps([str(scraped_data.get('age', ''))]),
        'sire': scraped_data.get('sire', ''),
        'dam': scraped_data.get('dam', ''),
        'dam_sire': scraped_data.get('dam_sire', ''),
        'race_record': scraped_data.get('race_record', ''),
        'weight': int(scraped_data.get('weight', 0)) if scraped_data.get('weight') else None,
        'total_prize_start': float(scraped_data.get('total_prize_start', 0)) if scraped_data.get('total_prize_start') else 0.0,
        'total_prize_latest': float(scraped_data.get('total_prize_latest', 0)) if scraped_data.get('total_prize_latest') else 0.0,
        'sold_price': json.dumps([str(scraped_data.get('sold_price', ''))]),
        'auction_date': json.dumps([scraped_data.get('auction_date', '')]),
        'seller': json.dumps([scraped_data.get('seller', '')]),
        'disease_tags': json.dumps(scraped_data.get('disease_tags', [])),
        'comment': json.dumps([scraped_data.get('comment', '')]),
        'image_url': scraped_data.get('image_url', ''),
        'primary_image': scraped_data.get('primary_image', ''),
        'unsold_count': int(scraped_data.get('unsold_count', 0)) if scraped_data.get('unsold_count') else 0,
    }
    return horse_data

def main():
    """スクレイピングしたデータをデータベースにインポートする"""
    db = SessionLocal()
    try:
        # スクレイパーを初期化
        scraper = RakutenAuctionScraper()
        horse_service = HorseService()
        
        # スクレイピングを実行（scrape_all_horsesを使用）
        print("=== スクレイピングを開始します ===")
        horses_data = scraper.scrape_all_horses()
        
        if not horses_data:
            print("スクレイピングでデータを取得できませんでした。")
            return
            
        print(f"=== スクレイピング完了: {len(horses_data)}頭の馬データを取得 ===")
        
        # データベースに保存
        print("=== データベースに保存中... ===")
        
        # 既存の馬データを取得（名前で重複チェック）
        existing_horses = {horse.name: horse for horse in db.query(Horse).all()}
        
        new_horses = 0
        updated_horses = 0
        
        for scraped_data in horses_data:
            horse_name = scraped_data.get('name')
            if not horse_name:
                print("警告: 名前のない馬データをスキップします")
                continue
                
            # 既存の馬データをチェック
            if horse_name in existing_horses:
                existing_horse = existing_horses[horse_name]
                # 既存の馬データを更新
                horse_data = map_horse_data(scraped_data)
                for key, value in horse_data.items():
                    setattr(existing_horse, key, value)
                existing_horse.updated_at = datetime.utcnow()
                updated_horses += 1
                print(f"馬 '{horse_name}' のデータを更新しました。")
            else:
                # 新しい馬データを作成
                horse_data = map_horse_data(scraped_data)
                horse = Horse(**horse_data)
                db.add(horse)
                new_horses += 1
                print(f"馬 '{horse_name}' を新規追加しました。")
        
        db.commit()
        print(f"=== データのインポートが完了しました ===")
        print(f"新規追加: {new_horses}頭, 更新: {updated_horses}頭")
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
