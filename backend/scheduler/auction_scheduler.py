import schedule
import time
import threading
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.database.models import get_db, SessionLocal
from backend.services.horse_service import HorseService
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuctionScheduler:
    def __init__(self):
        self.horse_service = HorseService()
        self.is_running = False
        self.scheduler_thread = None
        
    def get_next_auction_date(self) -> str:
        """次のオークション開催日を計算"""
        today = datetime.now()
        
        # 木曜オークション（火曜18:00以降に実行）
        if today.weekday() == 1:  # 火曜日
            if today.hour >= 18:
                # 次の木曜日
                days_until_thursday = (3 - today.weekday()) % 7
                next_thursday = today + timedelta(days=days_until_thursday)
                return next_thursday.strftime("%Y-%m-%d")
        
        # 日曜オークション（土曜18:00以降に実行）
        if today.weekday() == 5:  # 土曜日
            if today.hour >= 18:
                # 次の日曜日
                days_until_sunday = (6 - today.weekday()) % 7
                next_sunday = today + timedelta(days=days_until_sunday)
                return next_sunday.strftime("%Y-%m-%d")
        
        return None
    
    def should_run_scraping(self) -> bool:
        """スクレイピングを実行すべきかチェック"""
        auction_date = self.get_next_auction_date()
        if not auction_date:
            return False
            
        # データベースに既にデータがあるかチェック
        db = SessionLocal()
        try:
            existing_horses = self.horse_service.get_horses_by_auction_date(db, auction_date)
            return len(existing_horses) == 0
        finally:
            db.close()
    
    def run_scraping_job(self):
        """スクレイピングジョブを実行"""
        try:
            logger.info("自動スクレイピングを開始します...")
            
            auction_date = self.get_next_auction_date()
            if not auction_date:
                logger.info("今日はスクレイピング対象日ではありません")
                return
            
            db = SessionLocal()
            try:
                horses = self.horse_service.scrape_and_save_horses(db, auction_date)
                logger.info(f"自動スクレイピング完了: {len(horses)}頭の馬データを取得")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"自動スクレイピングでエラーが発生: {e}")
    
    def run_prize_update_job(self):
        """賞金更新ジョブを実行"""
        try:
            logger.info("自動賞金更新を開始します...")
            
            db = SessionLocal()
            try:
                updated_count = self.horse_service.update_prize_money_for_all(db)
                logger.info(f"自動賞金更新完了: {updated_count}頭の馬を更新")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"自動賞金更新でエラーが発生: {e}")
    
    def setup_schedule(self):
        """スケジュールを設定"""
        # 火曜日18:00に木曜オークションのスクレイピング
        schedule.every().tuesday.at("18:00").do(self.run_scraping_job)
        
        # 土曜日18:00に日曜オークションのスクレイピング
        schedule.every().saturday.at("18:00").do(self.run_scraping_job)
        
        # 毎日午前2:00に賞金情報を更新
        schedule.every().day.at("02:00").do(self.run_prize_update_job)
        
        logger.info("スケジュールを設定しました")
    
    def start(self):
        """スケジューラーを開始"""
        if self.is_running:
            logger.warning("スケジューラーは既に実行中です")
            return
        
        self.is_running = True
        self.setup_schedule()
        
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # 1分ごとにチェック
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("スケジューラーを開始しました")
    
    def stop(self):
        """スケジューラーを停止"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        logger.info("スケジューラーを停止しました")
    
    def get_status(self) -> dict:
        """スケジューラーの状態を取得"""
        return {
            "is_running": self.is_running,
            "next_scraping": self.get_next_auction_date(),
            "should_run": self.should_run_scraping(),
            "scheduled_jobs": [
                "火曜日18:00 - 木曜オークションスクレイピング",
                "土曜日18:00 - 日曜オークションスクレイピング",
                "毎日02:00 - 賞金情報更新"
            ]
        }

# グローバルスケジューラーインスタンス
scheduler = AuctionScheduler() 