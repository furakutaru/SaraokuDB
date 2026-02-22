from sqlalchemy.orm import Session
from sqlalchemy.inspection import inspect
from typing import List, Dict, Optional
from datetime import datetime
import json
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.database.models import Horse, get_db
from scrapers.rakuten_scraper import RakutenAuctionScraper

class HorseService:
    def __init__(self):
        self.rakuten_scraper = RakutenAuctionScraper()
    
    def create_horse(self, db: Session, horse_data: Dict) -> Horse:
        """
        馬データをデータベースに保存
        
        Args:
            db: データベースセッション
            horse_data: 保存する馬データ（auction_idを含む）
            
        Returns:
            Horse: 保存された馬データ
            
        Raises:
            ValueError: 必須フィールドが不足している場合
        """
        try:
            # デバッグ用に馬体重データをログに出力
            weight = horse_data.get('weight')
            if weight is not None:
                print(f"[HorseService] 馬体重データを検出: {weight}kg (型: {type(weight)})")
            else:
                print("[HorseService] 警告: 馬体重データが見つかりません")
                
            print(f"[HorseService] 受信データ: {horse_data}")
            
            # レースレコードが辞書型の場合はJSON文字列に変換
            if 'race_record' in horse_data and horse_data['race_record'] is not None:
                if isinstance(horse_data['race_record'], dict):
                    try:
                        horse_data['race_record'] = json.dumps(horse_data['race_record'], ensure_ascii=False)
                        print(f"[HorseService] レースレコードをJSONに変換: {horse_data['race_record']}")
                    except Exception as e:
                        print(f"[HorseService] レースレコードのJSON変換エラー: {str(e)}")
                        raise
            
            # auction_idが指定されている場合は、既存の馬を検索
            if 'auction_id' in horse_data and horse_data['auction_id']:
                existing_horse = self.get_horse_by_auction_id(db, horse_data['auction_id'])
                if existing_horse:
                    # 既存の馬を更新
                    print(f"[HorseService] 既存の馬を更新します (auction_id: {horse_data['auction_id']})")
                    return self.update_horse(db, existing_horse.id, horse_data)
            
            # 必須フィールドのバリデーション
            required_fields = ['name', 'auction_id']
            for field in required_fields:
                if field not in horse_data or not horse_data[field]:
                    raise ValueError(f"必須フィールド '{field}' が不足しています")
            
            print(f"[HorseService] 保存前データ: {horse_data}")
            
            try:
                horse = Horse(**horse_data)
                db.add(horse)
                db.commit()
                db.refresh(horse)
                print(f"[HorseService] 保存成功: 馬ID {horse.id}, オークションID {horse.auction_id}")
                return horse
                
            except Exception as e:
                db.rollback()
                print(f"[HorseService] データベースエラー: {str(e)}")
                print(f"[HorseService] エラーのあるデータ: {horse_data}")
                raise
                
        except Exception as e:
            print(f"[HorseService] エラーが発生しました: {str(e)}")
            import traceback
            print(f"[HorseService] トレースバック: {traceback.format_exc()}")
            raise
    
    def get_horses(self, db: Session, skip: int = 0, limit: int = 100) -> List[Horse]:
        """馬データを取得"""
        return db.query(Horse).offset(skip).limit(limit).all()
    
    def get_horse_by_id(self, db: Session, horse_id: int) -> Optional[Horse]:
        """IDで馬データを取得"""
        return db.query(Horse).filter(Horse.id == horse_id).first()
        
    def get_horse_by_auction_id(self, db: Session, auction_id: str) -> Optional[Horse]:
        """オークションIDで馬データを取得"""
        return db.query(Horse).filter(Horse.auction_id == auction_id).first()
    
    def get_horses_by_auction_date(self, db: Session, auction_date: str) -> List[Horse]:
        """開催日で馬データを取得"""
        return db.query(Horse).filter(Horse.auction_date == auction_date).all()
    
    def update_horse(self, db: Session, horse_id: int, horse_data: Dict) -> Optional[Horse]:
        """馬データを更新"""
        # レースレコードが辞書型の場合はJSON文字列に変換
        if 'race_record' in horse_data and isinstance(horse_data['race_record'], dict):
            horse_data['race_record'] = json.dumps(horse_data['race_record'], ensure_ascii=False)
            
        horse = db.query(Horse).filter(Horse.id == horse_id).first()
        if horse:
            for key, value in horse_data.items():
                # total_prize_latest が None または空文字列の場合は更新をスキップ
                if key == 'total_prize_latest' and (value is None or value == ''):
                    continue
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
        """スクレイピングしてデータベースに保存（履歴カラム対応）"""
        try:
            # 楽天オークションからデータを取得
            horses_data = self.rakuten_scraper.scrape_all_horses(auction_date)
            
            if not horses_data:
                print("取得した馬データがありません。")
                return []
            
            # netkeiba_scraper関連の処理を全て削除
            
            # データベースに保存
            saved_horses = []
            for horse_data in horses_data:
                # 主取り回数の管理
                unsold_count = 0
                if 'unsold' in horse_data and horse_data['unsold']:
                    unsold_count = 1
                    # unsoldがTrueの場合はis_unsoldも明示的に設定
                    horse_data['is_unsold'] = True
                    print(f"[デバッグ] 馬 {horse_data.get('name', '不明')} の主取りフラグを検出: unsold_count={unsold_count}")
                
                existing_horse = db.query(Horse).filter(
                    Horse.name == horse_data['name']
                ).first()
                
                if existing_horse:
                    # 既存馬のunsold_countを累積
                    prev_unsold_count = getattr(existing_horse, 'unsold_count', 0) or 0
                    if 'unsold' in horse_data and horse_data['unsold']:
                        unsold_count = prev_unsold_count + 1
                    else:
                        unsold_count = prev_unsold_count
                    
                    # 既存のis_unsoldを保持（明示的に設定されていない場合）
                    if 'is_unsold' not in horse_data and hasattr(existing_horse, 'is_unsold'):
                        horse_data['is_unsold'] = existing_horse.is_unsold
                        print(f"[デバッグ] 既存のis_unsoldを保持: {horse_data['is_unsold']}")
                
                horse_data['unsold_count'] = unsold_count
                # 各履歴カラムの新値
                new_date = horse_data.get('auction_date', '') or ''
                new_age = horse_data.get('age', '') or ''
                new_sex = horse_data.get('sex', '') or ''
                new_seller = horse_data.get('seller', '') or ''
                new_sold_price = horse_data.get('sold_price', '') or ''
                new_comment = horse_data.get('comment', '') or ''
                
                if existing_horse:
                    # auction_date/age履歴
                    try:
                        existing_dates = json.loads(getattr(existing_horse, 'auction_date', '')) if getattr(existing_horse, 'auction_date', '') else []
                    except Exception:
                        existing_dates = []
                    try:
                        existing_ages = json.loads(getattr(existing_horse, 'age', '')) if getattr(existing_horse, 'age', '') else []
                    except Exception:
                        existing_ages = []
                    # sex履歴
                    try:
                        existing_sexes = json.loads(getattr(existing_horse, 'sex', '')) if getattr(existing_horse, 'sex', '') else []
                    except Exception:
                        existing_sexes = []
                    # seller履歴
                    try:
                        existing_sellers = json.loads(getattr(existing_horse, 'seller', '')) if getattr(existing_horse, 'seller', '') else []
                    except Exception:
                        existing_sellers = []
                    # sold_price履歴
                    try:
                        existing_prices = json.loads(getattr(existing_horse, 'sold_price', '')) if getattr(existing_horse, 'sold_price', '') else []
                    except Exception:
                        existing_prices = []
                    # comment履歴
                    try:
                        existing_comments = json.loads(getattr(existing_horse, 'comment', '')) if getattr(existing_horse, 'comment', '') else []
                    except Exception:
                        existing_comments = []
                    # auction_date/age: 新しい日付がなければappend
                    if new_date not in existing_dates:
                        existing_dates.append(new_date)
                        existing_ages.append(new_age)
                    # sex: 直前と異なればappend
                    if not existing_sexes or (new_sex and new_sex != existing_sexes[-1]):
                        existing_sexes.append(new_sex)
                    # seller: 直前と異なればappend
                    if not existing_sellers or (new_seller and new_seller != existing_sellers[-1]):
                        existing_sellers.append(new_seller)
                    # sold_price: 常にappend
                    existing_prices.append(new_sold_price)
                    # comment: 常にappend
                    existing_comments.append(new_comment)
                    # 昇順ソート（auction_date/ageのみ）
                    if len(existing_dates) == len(existing_ages):
                        paired = sorted(zip(existing_dates, existing_ages), key=lambda x: x[0])
                        existing_dates, existing_ages = zip(*paired)
                        existing_dates = list(existing_dates)
                        existing_ages = list(existing_ages)
                    # 保存
                    existing_horse.auction_date = json.dumps(existing_dates, ensure_ascii=False)
                    existing_horse.age = json.dumps(existing_ages, ensure_ascii=False)
                    existing_horse.sex = json.dumps(existing_sexes, ensure_ascii=False)
                    existing_horse.seller = json.dumps(existing_sellers, ensure_ascii=False)
                    existing_horse.sold_price = json.dumps(existing_prices, ensure_ascii=False)
                    existing_horse.comment = json.dumps(existing_comments, ensure_ascii=False)
                    # その他の情報も更新
                    for key, value in horse_data.items():
                        if key not in ['auction_date', 'age', 'sex', 'seller', 'sold_price', 'comment']:
                            # is_unsoldが存在する場合は必ず更新する
                            # total_prize_latest はスキップ（楽天からは更新しない）
                            if key == 'total_prize_latest':
                                continue
                            if key == 'is_unsold' or not hasattr(existing_horse, key) or getattr(existing_horse, key) != value:
                                setattr(existing_horse, key, value)
                                print(f"[デバッグ] フィールドを更新: {key} = {value}")
                    existing_horse.updated_at = datetime.utcnow()
                    saved_horses.append(existing_horse)
                else:
                    # 新規データ（履歴カラムは配列で初期化）
                    horse_data['auction_date'] = json.dumps([new_date], ensure_ascii=False)
                    horse_data['age'] = json.dumps([new_age], ensure_ascii=False)
                    horse_data['sex'] = json.dumps([new_sex], ensure_ascii=False)
                    horse_data['seller'] = json.dumps([new_seller], ensure_ascii=False)
                    horse_data['sold_price'] = json.dumps([new_sold_price], ensure_ascii=False)
                    horse_data['comment'] = json.dumps([new_comment], ensure_ascii=False)
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
            # netkeibaからの賞金情報更新ロジックは削除
            pass
        
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
