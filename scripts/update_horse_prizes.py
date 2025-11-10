import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session, selectinload, load_only
from sqlalchemy import select, update
from typing import List, Optional, Generator
import random
import time
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# モデルのインポート前にデータベース設定を読み込む
from backend.database import engine, SessionLocal

# モデルをインポート（リレーションシップを確立するため）
from backend.models import Base

# テーブルを作成
Base.metadata.create_all(bind=engine)

# モデルをインポート
from backend.models.horse import Horse
from backend.models.auction_history import AuctionHistory
from scripts.keibabook_scraper import KeibaBookScraper

# 非同期セッションの取得
def get_db() -> Session:
    """データベースセッションを取得"""
    return SessionLocal()

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_horses_without_prize(db: Session, limit: int = 10) -> List[Horse]:
    """賞金情報が未取得の馬を取得"""
    # 必要なカラムを動的に選択
    columns = [
        Horse.id,
        Horse.name,
        Horse.age,
        Horse.is_unsold,
        Horse.bid_count,
        Horse.created_at,
        Horse.latest_auction_id,
        Horse.total_prize_latest
    ]
    
    # カラムが存在するか確認して追加（sire と sex のみ）
    for col in ['sire', 'sex']:
        if hasattr(Horse, col):
            columns.append(getattr(Horse, col))
    
    stmt = select(*columns).where(Horse.total_prize_latest.is_(None)).limit(limit)
    
    try:
        result = db.execute(stmt)
        # 辞書から Horse オブジェクトを作成
        horses = []
        for row in result.mappings().all():
            horse = Horse()
            for key, value in row.items():
                setattr(horse, key, value)
            horses.append(horse)
        return horses
    except Exception as e:
        logger.error(f"賞金情報が未取得の馬の取得中にエラーが発生しました: {str(e)}")
        return []

def update_horse_prize(db: Session, horse_id: int, prize: int) -> bool:
    """馬の賞金情報を更新"""
    try:
        # 必要なカラムのみを明示的に選択して更新
        stmt = (
            update(Horse)
            .where(Horse.id == horse_id)
            .values(total_prize_latest=prize)
            .execution_options(synchronize_session=False)
        )
        
        result = db.execute(stmt)
        db.commit()
        
        if result.rowcount > 0:
            logger.info(f"馬ID {horse_id} の賞金を更新しました: {prize:,}円")
            return True
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"馬ID {horse_id} の賞金更新中にエラーが発生しました: {str(e)}")
        return False

async def process_horse(scraper, db, horse):
    """個々の馬の賞金情報を更新する非同期関数"""
    try:
        # 初回検索（父馬名を含む）
        horse_info = await scraper.get_horse_info(
            name=horse.name,
            father=horse.sire if hasattr(horse, 'sire') and horse.sire else '',
            mother='',  # 空文字列を渡す
            gender=horse.sex if hasattr(horse, 'sex') and horse.sex else None
        )

        # 初回検索で見つからなかった場合、父馬名を外して再検索
        if not horse_info or 'prize' not in horse_info:
            logger.warning(f"馬ID {horse.id} の検索で候補が見つからないため、検索条件を緩和します")
            horse_info = await scraper.get_horse_info(
                name=horse.name,
                father='',  # 父馬名を外す
                mother='',
                gender=horse.sex if hasattr(horse, 'sex') and horse.sex else None
            )

        if horse_info and 'prize' in horse_info:
            prize = horse_info['prize'] or 0
            success = update_horse_prize(db, horse.id, prize)
            if not success:
                logger.warning(f"馬ID {horse.id} の賞金更新に失敗しました")
            else:
                logger.info(f"馬ID {horse.id} の賞金を {prize} 円で更新しました")
        else:
            logger.warning(f"馬ID {horse.id} の賞金情報を取得できませんでした")
        
        # レートリミット対策（1〜3秒のランダムな遅延）
        delay = random.uniform(1, 3)
        logger.debug(f"{delay:.2f}秒待機します...")
        await asyncio.sleep(delay)
        
    except Exception as e:
        logger.error(f"馬ID {horse.id} の処理中にエラーが発生しました: {str(e)}")
        # エラーが発生した場合、トランザクションをロールバック
        db.rollback()

async def process_horses_async():
    """賞金情報を更新する非同期メイン処理"""
    db = get_db()
    
    try:
        # 賞金情報が未取得の馬を取得
        horses = get_horses_without_prize(db)
        
        if not horses:
            logger.info("更新対象の馬が見つかりませんでした")
            return
        
        logger.info(f"賞金情報を更新する馬が {len(horses)} 件見つかりました")
        
        # KeibaBookScraper インスタンスを作成
        async with KeibaBookScraper() as scraper:
            # 馬ごとに処理を実行
            for horse in horses:
                await process_horse(scraper, db, horse)
    finally:
        db.close()

def process_horses():
    """同期インターフェースを提供するラッパー関数"""
    asyncio.run(process_horses_async())

if __name__ == "__main__":
    process_horses()
