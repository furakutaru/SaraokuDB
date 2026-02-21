import os
import sys
import logging
import asyncio
import argparse
import re
from pathlib import Path
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# 環境変数の読み込み
# GitHub Actionsでは.envファイルを読み込まない
if not os.getenv('GITHUB_ACTIONS'):
    env_path = Path(__file__).parent.parent / 'backend' / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('update_horse_prizes.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from sqlalchemy import create_engine, select, or_
from sqlalchemy.orm import sessionmaker
from backend.models.horse import Horse
from backend.models.horse_prize_history import HorsePrizeHistory

DATABASE_URL = os.getenv('DATABASE_URL')
print(f"DEBUG: DATABASE_URL = {DATABASE_URL}")
print(f"DEBUG: DATABASE_URL type = {type(DATABASE_URL)}")
print(f"DEBUG: DATABASE_URL length = {len(DATABASE_URL) if DATABASE_URL else 'None'}")
print(f"DEBUG: GITHUB_ACTIONS = {os.getenv('GITHUB_ACTIONS')}")

# DATABASE_URLが空の場合はエラー
if not DATABASE_URL:
    print("DEBUG: DATABASE_URL is None or empty!")
    raise ValueError("DATABASE_URL が設定されていません。環境変数を確認してください。")

# DATABASE_URLがSQLiteの場合はエラー
if DATABASE_URL.startswith('sqlite'):
    print(f"DEBUG: DATABASE_URL is SQLite: {DATABASE_URL}")
    raise ValueError(f"SQLiteは使用できません。DATABASE_URLをPostgreSQLに設定してください: {DATABASE_URL}")

# DATABASE_URLが短すぎる場合はエラー（***など）
if len(DATABASE_URL) < 50:
    print(f"DEBUG: DATABASE_URL is too short: {DATABASE_URL}")
    raise ValueError(f"DATABASE_URLが正しく設定されていません。GitHub SecretsのDATABASE_URLを確認してください: {DATABASE_URL}")

print(f"DEBUG: DATABASE_URL starts with postgresql: {DATABASE_URL.startswith('postgresql://')}")

# 同期エンジン・セッション作成
# PostgreSQLドライバーを明示的に指定
if DATABASE_URL.startswith('postgresql://'):
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600, echo=True)
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_horses_to_update(db, batch_size: int = 10):
    """更新対象の馬を取得"""
    logger.info("デバッグ: DBから更新対象の馬を取得します...")
    try:
        now_utc = datetime.now(timezone.utc)
        
        # auction_historiesのJOINを避けてシンプルに取得
        stmt = select(Horse).where(
            Horse.is_broodmare == False,
            Horse.is_retired == False,
            Horse.name.isnot(None),
            or_(
                Horse.next_update_due_date.is_(None),
                Horse.next_update_due_date <= now_utc
            )
        ).order_by(
            Horse.next_update_due_date.asc().nullsfirst()
        ).limit(batch_size)
        
        horses = db.execute(stmt).scalars().all()
        logger.info(f"更新対象の馬が {len(horses)} 件見つかりました")
        return horses
        
    except Exception as e:
        logger.error(f"更新対象の馬の取得中にエラーが発生しました: {str(e)}", exc_info=True)
        return []

def update_horse_prize(db, horse, prize: int) -> bool:
    """馬の賞金情報を更新し、次回の更新間隔を調整"""
    try:
        horse_id = horse.id
        
        # current_prize属性がない場合はtotal_prize_latestを利用する
        last_prize = int(getattr(horse, 'current_prize', horse.total_prize_latest) or 0)
        
        # 賞金履歴を記録
        HorsePrizeHistory.create(db, horse_id, prize)
        
        # 更新間隔の調整
        update_interval_months = horse.update_interval_months or 3
        next_update_due_date = None
        is_retired = False
        now_utc = datetime.now(timezone.utc)
        
        # 賞金に変化がなかった場合
        if prize == last_prize:
            if update_interval_months < 12:
                update_interval_months = min(update_interval_months * 2, 12)
            else:
                update_interval_months = 12
                
            # 3年間変化がなければ引退とみなす
            last_update = horse.last_prize_update
            if last_update:
                if last_update.tzinfo is None:
                    last_update = last_update.replace(tzinfo=timezone.utc)
                if (now_utc - last_update).days >= 3 * 365:
                    is_retired = True
                    logger.info(f"馬ID {horse_id} は3年間賞金に変化がなかったため、引退とみなします")
                else:
                    next_update_due_date = now_utc + relativedelta(months=update_interval_months)
                    logger.info(f"馬ID {horse_id} の次回更新間隔を {update_interval_months} ヶ月後に設定")
            else:
                next_update_due_date = now_utc + relativedelta(months=update_interval_months)
        else:
            # 賞金に変化があった場合は更新間隔をリセット
            update_interval_months = 3
            next_update_due_date = now_utc + relativedelta(months=3)
            logger.info(f"馬ID {horse_id} の賞金が更新されたため、更新間隔を3ヶ月にリセット")
        
        # 馬の情報を更新
        if hasattr(horse, 'current_prize'):
            horse.current_prize = prize
        horse.total_prize_latest = prize
        horse.last_prize_update = now_utc
        horse.update_interval_months = update_interval_months
        horse.is_retired = is_retired
        if next_update_due_date:
            horse.next_update_due_date = next_update_due_date
            
        db.commit()
        logger.info(f"馬ID {horse_id} の情報を更新しました: {prize}円")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"馬ID {horse.id} の情報更新中にエラーが発生しました: {str(e)}", exc_info=True)
        return False

def push_next_update_only(db, horse, months: int = 3) -> bool:
    """賞金未登録想定の馬など、スクレイプを行わず次回更新日だけ先送りする"""
    try:
        now_utc = datetime.now(timezone.utc)
        horse.next_update_due_date = now_utc + relativedelta(months=months)
        db.commit()
        logger.info(f"馬ID {horse.id} は未登録名（年次表記）のためスクレイプをスキップ。次回更新を{months}ヶ月後へ設定")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"馬ID {horse.id} の次回更新日更新に失敗: {str(e)}")
        return False

async def process_horse(scraper, db, horse) -> bool:
    """1頭の馬の賞金情報を更新"""
    try:
        horse_id = horse.id
        horse_name = horse.name or '不明'
        
        try:
            search_name = re.sub(r"の\d{2}$", "", horse_name).strip()
        except Exception:
            search_name = horse_name
        
        logger.info(f"馬ID {horse_id} ({horse_name}) の賞金情報を更新中...")

        try:
            if re.search(r"の\d{2}$", horse_name):
                return push_next_update_only(db, horse, months=3)
        except Exception:
            pass
        
        # オークション日を取得（latest_auctionリレーションから）
        auction_date = None
        if horse.latest_auction:
            auction_date = horse.latest_auction.auction_date
        
        horse_info = await scraper.get_horse_info(
            name=search_name,
            father='',
            mother='',
            auction_date=auction_date,  # オークション日を設定
            gender=None
        )

        if not horse_info or horse_info.get('prize') is None:
            logger.warning(f"馬ID {horse_id} の賞金情報を取得できませんでした（name={horse_name}）")
            push_next_update_only(db, horse, months=1)
            return False
        
        if horse_info.get('prize') == 0:
            logger.info(f"馬ID {horse_id} の賞金は0円（未出走または未入着）。0円として更新します。")

        prize = int(horse_info.get('prize') or 0)
        success = update_horse_prize(db, horse, prize)
        return success
        
    except Exception as e:
        logger.error(f"馬ID {horse.id} の処理中にエラーが発生しました: {str(e)}", exc_info=True)
        return False

async def process_horses_async(batch_size=10):
    """馬の賞金情報を非同期で更新"""
    db = SessionLocal()
    try:
        logger.info("賞金情報の更新を開始します")
        
        horses = get_horses_to_update(db, batch_size)
        if not horses:
            logger.info("更新対象の馬が見つかりませんでした")
            return True
            
        from scripts.keibabook_scraper import KeibaBookScraper as RealKeibaBookScraper
        scraper_ctx = RealKeibaBookScraper(verify_ssl=False)
        
        async with scraper_ctx as scraper:
            semaphore = asyncio.Semaphore(3)

            async def run_with_sem(h):
                async with semaphore:
                    await asyncio.sleep(0.5)
                    return await process_horse(scraper, db, h)

            tasks = []
            for h in horses:
                tasks.append(asyncio.create_task(run_with_sem(h)))

            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if r is True)
        failure_count = len(results) - success_count
        
        logger.info(f"賞金情報の更新が完了しました (成功: {success_count}件, 失敗: {failure_count}件)")
        
        return success_count > 0 and failure_count == 0
            
    except Exception as e:
        logger.error(f"賞金情報の更新中にエラーが発生しました: {str(e)}", exc_info=True)
        return False
    finally:
        db.close()

async def main_async():
    try:
        parser = argparse.ArgumentParser(description='馬の賞金情報を更新するスクリプト')
        parser.add_argument('--batch-size', type=int, default=10, help='一度に処理する馬の数')
        args = parser.parse_args()
        
        return await process_horses_async(batch_size=args.batch_size)
        
    except KeyboardInterrupt:
        logger.info("処理を中断します")
        return 1
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {str(e)}", exc_info=True)
        return 1

def main():
    result = asyncio.run(main_async())
    if isinstance(result, bool):
        return 0 if result else 1
    return result

if __name__ == "__main__":
    sys.exit(main())
