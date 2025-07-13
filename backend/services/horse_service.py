from sqlalchemy.orm import Session
from backend.database.models import Horse, get_db
from backend.scrapers.rakuten_scraper import RakutenAuctionScraper
from backend.scrapers.netkeiba_scraper import NetkeibaScraper
from typing import List, Dict, Optional
from datetime import datetime

class HorseService:
    def __init__(self):
        self.rakuten_scraper = RakutenAuctionScraper()
        self.netkeiba_scraper = NetkeibaScraper()
    
    def create_horse(self, db: Session, horse_data: Dict) -> Horse:
        """馬データをデータベースに保存"""
        horse = Horse(**horse_data)
        db.add(horse)
        db.commit()
        db.refresh(horse)
        return horse
    
    def get_horses(self, db: Session, skip: int = 0, limit: int = 100) -> List[Horse]:
        """馬データを取得"""
        return db.query(Horse).offset(skip).limit(limit).all()
    
    def get_horse_by_id(self, db: Session, horse_id: int) -> Optional[Horse]:
        """IDで馬データを取得"""
        return db.query(Horse).filter(Horse.id == horse_id).first()
    
    def get_horses_by_auction_date(self, db: Session, auction_date: str) -> List[Horse]:
        """開催日で馬データを取得"""
        return db.query(Horse).filter(Horse.auction_date == auction_date).all()
    
    def update_horse(self, db: Session, horse_id: int, horse_data: Dict) -> Optional[Horse]:
        """馬データを更新"""
        horse = db.query(Horse).filter(Horse.id == horse_id).first()
        if horse:
            for key, value in horse_data.items():
                setattr(horse, key, value)
            horse.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(horse)
        return horse
    
    def delete_horse(self, db: Session, horse_id: int) -> bool:
        """馬データを削除"""
        horse = db.query(Horse).filter(Horse.id == horse_id).first()
        if horse:
            db.delete(horse)
            db.commit()
            return True
        return False
    
    def scrape_and_save_horses(self, db: Session, auction_date: str = None) -> List[Horse]:
        """スクレイピングしてデータベースに保存"""
        try:
            # 楽天オークションからデータを取得
            horses_data = self.rakuten_scraper.scrape_all_horses(auction_date)
            
            if not horses_data:
                print("取得した馬データがありません。")
                return []
            
            # netkeibaから最新賞金情報を取得
            horses_data = self.netkeiba_scraper.batch_update_prize_money(horses_data)
            
            # データベースに保存
            saved_horses = []
            for horse_data in horses_data:
                # 既存データをチェック
                existing_horse = db.query(Horse).filter(
                    Horse.name == horse_data['name'],
                    Horse.auction_date == horse_data['auction_date']
                ).first()
                
                if existing_horse:
                    # 既存データを更新
                    for key, value in horse_data.items():
                        setattr(existing_horse, key, value)
                    existing_horse.updated_at = datetime.utcnow()
                    saved_horses.append(existing_horse)
                else:
                    # 新規データを作成
                    horse = self.create_horse(db, horse_data)
                    saved_horses.append(horse)
            
            db.commit()
            print(f"{len(saved_horses)}頭の馬データを保存しました。")
            return saved_horses
            
        except Exception as e:
            print(f"スクレイピングと保存に失敗: {e}")
            db.rollback()
            return []
    
    def update_prize_money_for_all(self, db: Session) -> int:
        """全馬の賞金情報を更新"""
        horses = db.query(Horse).all()
        updated_count = 0
        
        for horse in horses:
            update_data = self.netkeiba_scraper.update_horse_prize_money(horse.name)
            if update_data:
                horse.total_prize_latest = update_data.get('total_prize_latest')
                horse.netkeiba_url = update_data.get('netkeiba_url')
                horse.updated_at = datetime.utcnow()
                updated_count += 1
        
        db.commit()
        return updated_count
    
    def get_statistics(self, db: Session) -> Dict:
        """統計情報を取得"""
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        total_horses = db.query(Horse).count()
        
        # 平均落札価格
        avg_price = db.query(Horse).filter(Horse.sold_price > 0).with_entities(
            func.avg(Horse.sold_price)
        ).scalar() or 0
        
        # 平均成長率
        horses_with_growth = db.query(Horse).filter(
            Horse.total_prize_start > 0,
            Horse.total_prize_latest > 0
        ).all()
        
        total_growth = 0
        growth_count = 0
        for horse in horses_with_growth:
            if horse.total_prize_start > 0:
                growth_rate = (horse.total_prize_latest - horse.total_prize_start) / horse.total_prize_start * 100
                total_growth += growth_rate
                growth_count += 1
        
        avg_growth = total_growth / growth_count if growth_count > 0 else 0
        
        # 日付フォーマット調整
        last_scraping_date = db.query(Horse).order_by(Horse.created_at.desc()).first()
        last_scraping = last_scraping_date.created_at.strftime("%Y.%m.%d") if last_scraping_date else None
        today = datetime.now()
        next_auction_date = None
        # データが1件もなければ日付を返す
        if total_horses == 0:
            # 木曜オークション（火曜18:00以降に実行）
            if today.weekday() == 1 and today.hour >= 18:
                days_until_thursday = (3 - today.weekday()) % 7
                next_thursday = today + timedelta(days=days_until_thursday)
                next_auction_date = next_thursday.strftime("%m.%d")
            # 日曜オークション（土曜18:00以降に実行）
            if today.weekday() == 5 and today.hour >= 18:
                days_until_sunday = (6 - today.weekday()) % 7
                next_sunday = today + timedelta(days=days_until_sunday)
                next_auction_date = next_sunday.strftime("%m.%d")
            if not next_auction_date:
                if today.weekday() < 3:
                    days_until_thursday = 3 - today.weekday()
                    next_auction_date = (today + timedelta(days=days_until_thursday)).strftime("%m.%d")
                else:
                    days_until_sunday = (6 - today.weekday()) % 7
                    next_auction_date = (today + timedelta(days=days_until_sunday)).strftime("%m.%d")
            return {
                'total_horses': total_horses,
                'average_price': int(avg_price),
                'average_growth_rate': round(avg_growth, 2),
                'horses_with_growth_data': growth_count,
                'last_scraping_date': last_scraping,
                'next_auction_date': next_auction_date
            }
        # データが1件でもあれば日付情報は返さない
        return {
            'total_horses': total_horses,
            'average_price': int(avg_price),
            'average_growth_rate': round(avg_growth, 2),
            'horses_with_growth_data': growth_count
        } 