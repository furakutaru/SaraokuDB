import os
import sys
import logging
import asyncio
import random
from dataclasses import dataclass
from typing import Optional
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


@dataclass
class PrizeUpdatePacing:
    """競馬ブック負荷・BAN回避のための待機・並列度（GitHub Actions の既定もここに合わせる）"""
    max_concurrent_horses: int = 2
    inter_horse_delay_min: float = 0.6
    inter_horse_delay_max: float = 2.8
    pause_every_n_horses: int = 12
    pause_extra_min: float = 4.0
    pause_extra_max: float = 10.0
    keibabook_min_request_interval: float = 1.35
    keibabook_request_jitter_max: float = 0.45
    between_batch_min: float = 0.8
    between_batch_max: float = 2.5


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
        
        # 賞金履歴を記録（created_atを明示的に設定）
        from datetime import datetime, timezone
        now_utc = datetime.now(timezone.utc)
        prize_history = HorsePrizeHistory(
            horse_id=horse_id,
            prize=prize,
            created_at=now_utc,  # 明示的にcreated_atを設定
            updated_at=now_utc
        )
        db.add(prize_history)
        db.commit()
        
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
        
        # 既に競馬ブックのURLが登録されている場合は、検索をスキップして直接アクセス
        if hasattr(horse, 'keibabook_url') and horse.keibabook_url:
            logger.info(f"馬ID {horse_id} は登録済みのURLに直接アクセスします: {horse.keibabook_url}")
            prize = await scraper.get_horse_prize(horse.keibabook_url)
            horse_info = {'prize': prize, 'detail_url': horse.keibabook_url}
            
            # URLが正しくない場合などのためのフォールバック
            if prize is None:
                logger.warning(f"登録済みのURLからの賞金取得に失敗しました。再検索を実行します。")
                horse_info = None
        else:
            horse_info = None

        if not horse_info:
            horse_info = await scraper.get_horse_info(
                name=search_name,
                father='',
                mother='',
                auction_date=auction_date,  # オークション日を設定
                gender=None
            )
            
            # 検索に成功してURLが取得できた場合は保存
            if horse_info and horse_info.get('detail_url'):
                horse.keibabook_url = horse_info['detail_url']
                logger.info(f"馬ID {horse_id} の競馬ブックURLを保存しました: {horse.keibabook_url}")

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

async def _process_one_batch(db, batch_size: int, pacing: PrizeUpdatePacing) -> tuple[int, int, bool]:
    """1バッチ分を処理し、(成功件数, 失敗件数, 致命的エラーで中断したか) を返す"""
    horses = get_horses_to_update(db, batch_size)
    if not horses:
        return 0, 0, False

    from scripts.keibabook_scraper import KeibaBookScraper as RealKeibaBookScraper
    scraper_ctx = RealKeibaBookScraper(
        verify_ssl=False,
        min_request_interval=pacing.keibabook_min_request_interval,
        request_spacing_jitter_max=pacing.keibabook_request_jitter_max,
    )

    async with scraper_ctx as scraper:
        concurrent = max(1, int(pacing.max_concurrent_horses))
        semaphore = asyncio.Semaphore(concurrent)
        completed_horses = [0]
        pause_lock = asyncio.Lock()
        delay_lo = float(pacing.inter_horse_delay_min)
        delay_hi = max(delay_lo, float(pacing.inter_horse_delay_max))
        pause_n = int(pacing.pause_every_n_horses)
        pause_lo = min(float(pacing.pause_extra_min), float(pacing.pause_extra_max))
        pause_hi = max(float(pacing.pause_extra_min), float(pacing.pause_extra_max))

        async def run_with_sem(h):
            async with semaphore:
                await asyncio.sleep(random.uniform(delay_lo, delay_hi))
                result = await process_horse(scraper, db, h)
            async with pause_lock:
                completed_horses[0] += 1
                if pause_n > 0 and completed_horses[0] % pause_n == 0:
                    await asyncio.sleep(random.uniform(pause_lo, pause_hi))
                    logger.info(
                        "定期小休止: 累計 %s 頭処理後（%s 頭ごと）",
                        completed_horses[0],
                        pause_n,
                    )
            return result

        tasks = [asyncio.create_task(run_with_sem(h)) for h in horses]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    success_count = sum(1 for r in results if r is True)
    failure_count = len(results) - success_count
    had_exception = any(isinstance(r, BaseException) for r in results)

    logger.info(f"バッチ完了 (成功: {success_count}件, 失敗: {failure_count}件)")
    if had_exception:
        for r in results:
            if isinstance(r, BaseException):
                tb = getattr(r, "__traceback__", None)
                if tb is not None:
                    logger.error("バッチ内の例外: %s", r, exc_info=(type(r), r, tb))
                else:
                    logger.error("バッチ内の例外: %s", r)

    return success_count, failure_count, had_exception


async def process_horses_async(
    batch_size: int = 10,
    until_empty: bool = False,
    max_batches: Optional[int] = None,
    pacing: Optional[PrizeUpdatePacing] = None,
):
    """馬の賞金情報を非同期で更新。

    until_empty が True のときは、更新対象がなくなるまで batch_size 件ずつ繰り返す。
    max_batches が指定されていれば、その回数で打ち切る（無限ループ防止用）。
    """
    pacing = pacing or PrizeUpdatePacing()
    logger.info("賞金情報の更新を開始します")
    logger.info(
        "ペーシング: concurrent=%s, horse_delay=%.2f〜%.2f秒, pause_every=%s頭, kb_interval=%.2fs+j%.2fs",
        pacing.max_concurrent_horses,
        pacing.inter_horse_delay_min,
        pacing.inter_horse_delay_max,
        pacing.pause_every_n_horses,
        pacing.keibabook_min_request_interval,
        pacing.keibabook_request_jitter_max,
    )
    if until_empty:
        logger.info(f"モード: 対象が尽きるまで繰り返し (batch_size={batch_size}, max_batches={max_batches})")

    total_success = 0
    total_failure = 0
    batch_index = 0
    any_batch_ok = False

    try:
        while True:
            batch_index += 1
            if until_empty and batch_index > 1:
                bb_lo = min(pacing.between_batch_min, pacing.between_batch_max)
                bb_hi = max(pacing.between_batch_min, pacing.between_batch_max)
                await asyncio.sleep(random.uniform(bb_lo, bb_hi))
            if max_batches is not None and batch_index > max_batches:
                logger.warning(f"max_batches={max_batches} に達したため終了します")
                break

            db = SessionLocal()
            try:
                success_count, failure_count, had_exception = await _process_one_batch(db, batch_size, pacing)
            except Exception as e:
                logger.error(f"賞金情報の更新中にエラーが発生しました: {str(e)}", exc_info=True)
                return False
            finally:
                db.close()

            if success_count == 0 and failure_count == 0:
                if batch_index == 1:
                    logger.info("更新対象の馬が見つかりませんでした")
                else:
                    logger.info("以降、更新対象の馬はありませんでした")
                break

            total_success += success_count
            total_failure += failure_count
            if success_count > 0:
                any_batch_ok = True

            if had_exception:
                logger.error("バッチ内に未処理例外があったため終了します")
                return False

            if not until_empty:
                ok = success_count > 0 and failure_count == 0
                if not ok:
                    logger.info("1バッチ内に失敗があったため終了します (--until-empty で再試行可能)")
                return ok

            if failure_count > 0:
                logger.info("このバッチに失敗があったため、--until-empty モードを終了します")
                return False

        logger.info(f"賞金情報の更新が完了しました (合計 成功: {total_success}件, 失敗: {total_failure}件)")
        return any_batch_ok or (total_success == 0 and total_failure == 0)

    except Exception as e:
        logger.error(f"賞金情報の更新中にエラーが発生しました: {str(e)}", exc_info=True)
        return False

async def main_async():
    try:
        parser = argparse.ArgumentParser(description='馬の賞金情報を更新するスクリプト')
        parser.add_argument('--batch-size', type=int, default=10, help='一度に処理する馬の数')
        parser.add_argument(
            '--until-empty',
            action='store_true',
            help='next_update_due が来ている馬を、対象がなくなるまで batch_size 件ずつ繰り返し処理する（手動一括用）',
        )
        parser.add_argument(
            '--max-batches',
            type=int,
            default=None,
            metavar='N',
            help='--until-empty 時に最大 N バッチで打ち切る（未指定なら制限なし）',
        )
        parser.add_argument(
            '--max-concurrent-horses',
            type=int,
            default=2,
            help='同時にスクレイプする馬の頭数の上限（既定2）',
        )
        parser.add_argument(
            '--inter-horse-delay-min',
            type=float,
            default=0.6,
            help='各馬の処理開始前ランダム待ちの下限秒',
        )
        parser.add_argument(
            '--inter-horse-delay-max',
            type=float,
            default=2.8,
            help='各馬の処理開始前ランダム待ちの上限秒',
        )
        parser.add_argument(
            '--pause-every-n-horses',
            type=int,
            default=12,
            metavar='N',
            help='N 頭ごとに追加の小休止（0で無効）',
        )
        parser.add_argument(
            '--pause-extra-min',
            type=float,
            default=4.0,
            help='小休止のランダム秒・下限',
        )
        parser.add_argument(
            '--pause-extra-max',
            type=float,
            default=10.0,
            help='小休止のランダム秒・上限',
        )
        parser.add_argument(
            '--keibabook-min-interval',
            type=float,
            default=1.35,
            help='競馬ブックへの連続HTTPの最短間隔（秒）',
        )
        parser.add_argument(
            '--keibabook-request-jitter-max',
            type=float,
            default=0.45,
            help='上記に加えるランダム待ちの上限秒（0で無効）',
        )
        args = parser.parse_args()

        delay_max = max(float(args.inter_horse_delay_min), float(args.inter_horse_delay_max))
        pe_lo, pe_hi = float(args.pause_extra_min), float(args.pause_extra_max)
        if pe_lo > pe_hi:
            pe_lo, pe_hi = pe_hi, pe_lo
        pacing = PrizeUpdatePacing(
            max_concurrent_horses=max(1, int(args.max_concurrent_horses)),
            inter_horse_delay_min=float(args.inter_horse_delay_min),
            inter_horse_delay_max=delay_max,
            pause_every_n_horses=max(0, int(args.pause_every_n_horses)),
            pause_extra_min=pe_lo,
            pause_extra_max=pe_hi,
            keibabook_min_request_interval=float(args.keibabook_min_interval),
            keibabook_request_jitter_max=max(0.0, float(args.keibabook_request_jitter_max)),
        )

        return await process_horses_async(
            batch_size=args.batch_size,
            until_empty=args.until_empty,
            max_batches=args.max_batches,
            pacing=pacing,
        )
        
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
