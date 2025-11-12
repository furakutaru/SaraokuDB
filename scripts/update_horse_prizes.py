import asyncio
import logging
from datetime import datetime, timedelta
import random
import os
import sys
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import argparse
import requests
import sqlalchemy
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm.attributes import flag_modified
from dateutil.relativedelta import relativedelta
import psycopg2

# モデルクラスのインポート
from backend.models.horse import Horse
from backend.models.horse_prize_history import HorsePrizeHistory

# プロジェクトのルートディレクトリをパスに追加
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# 環境変数から認証情報を取得
import os
import requests
from typing import Dict, Any, Optional

# APIのベースURLを取得
API_BASE_URL = os.getenv("PROD_API_BASE_URL")
TOKEN = os.getenv("TOKEN")
AUTH_HEADER = os.getenv("AUTH_HEADER")

if not API_BASE_URL or not TOKEN or not AUTH_HEADER:
    raise ValueError("Required environment variables (PROD_API_BASE_URL, TOKEN, AUTH_HEADER) are not set")

# APIクライアントクラス
class ApiClient:
    def __init__(self, base_url: str, token: str, auth_header: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': auth_header,
            'Content-Type': 'application/json'
        })
        
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint: str, data: Dict) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.post(url, json=data, timeout=30)
        response.raise_for_status()
        return response.json()

# グローバルAPIクライアントを初期化
api_client = ApiClient(API_BASE_URL, TOKEN, AUTH_HEADER)

# データベース接続の代わりにAPIを使用するためのヘルパー関数
def get_db():
    """APIを使用してデータベースセッションをエミュレート"""
    class DBSession:
        def __init__(self, api_client):
            self.api_client = api_client
            
        def query(self, model):
            return QueryBuilder(self.api_client, model)
            
        def commit(self):
            pass
            
        def close(self):
            pass
            
        def __enter__(self):
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.close()

    return DBSession(api_client)

class QueryBuilder:
    """APIを使用してSQLAlchemyのクエリをエミュレート"""
    def __init__(self, api_client, model):
        self.api_client = api_client
        self.model = model
        self.filters = {}
        
    def filter(self, **kwargs):
        self.filters.update(kwargs)
        return self
        
    def all(self):
        endpoint = f"api/{self.model.__tablename__}"
        response = self.api_client.get(endpoint, params=self.filters)
        return [self.model(**item) for item in response.get('items', [])]
    
    def first(self):
        result = self.all()
        return result[0] if result else None

# データベース接続の代わりにAPIを使用
SessionLocal = get_db

# リトライ用のユーティリティ関数
def retry_on_db_error(max_retries=3, delay=5):
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (sqlalchemy.exc.OperationalError, psycopg2.OperationalError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (attempt + 1)
                        print(f"Database operation failed (attempt {attempt + 1}/{max_retries}). "
                              f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    continue
            raise last_exception
        return wrapper
    return decorator

# ロガーの設定
logger = logging.getLogger(__name__)

# テーブル作成は不要（API経由で行う）

# モデルをインポート
from scripts.keibabook_scraper import KeibaBookScraper

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('update_horse_prizes.log')
    ]
)

def get_horses_to_update(db: Session, batch_size: int = 10) -> List[Horse]:
    """更新対象の馬を取得
    
    Args:
        db (Session): データベースセッション
        batch_size (int): 一度に取得する馬の数
        
    Returns:
        List[Horse]: 更新対象の馬のリスト
    """
    try:
        now = datetime.now()
        
        # 更新対象の馬を取得
        # 1. 次回更新日が現在日時より前のもの
        # 2. もしくは、次回更新日が設定されていないもの
        # 3. 最終更新日が古い順に並べ替え
        stmt = (
            select(Horse)
            .options(
                selectinload(Horse.prize_histories),
                selectinload(Horse.latest_auction)
            )
            .where(
                Horse.is_retired == False,  # 引退していない馬のみ
                or_(
                    Horse.next_update_due_date <= now,
                    Horse.next_update_due_date.is_(None)
                )
            )
            .order_by(
                Horse.last_prize_update.asc()  # 古いものから順に取得
            )
            .limit(batch_size)  # 一度に処理する件数を制限
        )
        
        result = db.execute(stmt)
        horses = result.scalars().all()
        
        if not horses:
            logger.info("更新対象の馬は見つかりませんでした")
            return []
            
        logger.info(f"更新対象の馬が {len(horses)} 件見つかりました")
        return horses
        
    except Exception as e:
        logger.error(f"更新対象の馬の取得中にエラーが発生しました: {str(e)}", exc_info=True)
        return []

def update_prize_history(db: Session, horse_id: int, prize: int) -> HorsePrizeHistory:
    """賞金履歴を更新
    
    Args:
        db (Session): データベースセッション
        horse_id (int): 馬ID
        prize (int): 賞金額（円）
        
    Returns:
        HorsePrizeHistory: 作成した賞金履歴レコード
    """
    try:
        history = HorsePrizeHistory(horse_id=horse_id, prize=prize)
        db.add(history)
        db.commit()
        db.refresh(history)
        logger.info(f"馬ID {horse_id} の賞金履歴を更新しました: {prize}円")
        return history
    except Exception as e:
        db.rollback()
        logger.error(f"馬ID {horse_id} の賞金履歴の更新中にエラーが発生しました: {str(e)}")
        raise

def update_horse_prize(db: Session, horse: Horse, prize: int) -> bool:
    """馬の賞金情報を更新し、次回の更新間隔を調整
    
    Args:
        db (Session): データベースセッション
        horse (Horse): 更新対象の馬
        prize (int): 新しい賞金額（円）
        
    Returns:
        bool: 更新が成功したかどうか
    """
    try:
        now = datetime.now()
        
        # 前回の賞金を取得
        last_prize = db.scalar(
            select(func.coalesce(func.max(HorsePrizeHistory.prize), 0))
            .where(HorsePrizeHistory.horse_id == horse.id)
        ) or 0
        
        # 賞金履歴を記録
        update_prize_history(db, horse.id, prize)
        
        # 賞金に変化がなかった場合
        if prize == last_prize:
            # 更新間隔を延長
            if horse.update_interval_months < 12:  # 1年未満の場合
                horse.update_interval_months *= 2
            else:
                horse.update_interval_months = 12  # 最大1年ごと
                
            # 3年間変化がなければ引退とみなす
            if horse.last_prize_update and (now - horse.last_prize_update).days >= 3 * 365:
                horse.is_retired = True
                horse.next_update_due_date = None
                logger.info(f"馬ID {horse.id} は3年間賞金に変化がなかったため、引退とみなします")
            else:
                horse.next_update_due_date = now + relativedelta(months=horse.update_interval_months)
                logger.info(f"馬ID {horse.id} の次回更新間隔を {horse.update_interval_months} ヶ月後に設定")
        else:
            # 賞金に変化があれば間隔をリセット
            horse.update_interval_months = 3
            horse.next_update_due_date = now + relativedelta(months=3)
            logger.info(f"馬ID {horse.id} の賞金が更新されたため、更新間隔を3ヶ月にリセット")
        
        # 最終更新日を更新
        horse.last_prize_update = now
        horse.total_prize_latest = prize
        
        db.add(horse)
        db.commit()
        db.refresh(horse)
        
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"馬ID {horse.id} の賞金更新中にエラーが発生しました: {str(e)}", exc_info=True)
        return False

async def process_horse(scraper, db: Session, horse: Horse) -> bool:
    """個々の馬の賞金情報を更新する非同期関数
    
    Args:
        scraper: KeibaBookScraper インスタンス
        db (Session): データベースセッション
        horse (Horse): 更新対象の馬
        
    Returns:
        bool: 処理が成功したかどうか
    """
    horse_name = horse.name
    try:
        logger.info(f"馬 '{horse_name}' (ID: {horse.id}) の賞金情報を更新中...")
        
        # スクレイピングで賞金情報を取得
        # 馬名、父馬名、母馬名、性別を取得
        father = horse.sire or ''
        mother = horse.dam or ''
        gender = horse.sex or ''
        
        # 検索条件を段階的に緩和して検索を試みる
        search_attempts = [
            {'father': father, 'mother': mother, 'desc': f"父: {father}, 母: {mother}"},
            {'father': father, 'mother': "", 'desc': f"父: {father}"},
            {'father': "", 'mother': "", 'desc': "条件なし"}
        ]
        
        search_results = []
        search_desc = ""
        
        for attempt in search_attempts:
            search_desc = attempt['desc']
            logger.info(f"検索を試みます: 馬名='{horse_name}', {search_desc}")
            search_results = await scraper.search_horse(horse_name, father=attempt['father'], mother=attempt['mother'])
            
            if search_results:
                logger.info(f"検索成功: {len(search_results)}件見つかりました ({search_desc})")
                break
            else:
                logger.info(f"検索結果なし: 条件 '{search_desc}' では見つかりませんでした")
        
        # 検索結果が得られなかった場合
        if not search_results:
            logger.warning(f"馬 '{horse_name}' (ID: {horse.id}) の検索結果が見つかりませんでした。次回の更新間隔を延長します。")
            horse.update_interval_months = min(12, (horse.update_interval_months or 3) * 2)
            horse.next_update_due_date = datetime.now() + relativedelta(months=horse.update_interval_months)
            horse.last_prize_update = datetime.now()
            db.add(horse)
            db.commit()
            return False
        
        # 検索結果から最適な馬を選択
        best_match = None
        if len(search_results) > 1:
            # 複数ヒットした場合は、名前が完全一致するものを優先
            for result in search_results:
                if result.get('name') == horse_name:
                    best_match = result
                    logger.info(f"完全一致する馬を見つけました: {best_match}")
                    break
        
        # 完全一致がなければ最初の結果を使用
        best_match = best_match or search_results[0]
        
        # 賞金情報を取得
        prize = best_match.get('prize', 0)
        detail_url = best_match.get('detail_url', '')
        
        logger.info(f"選択した馬の情報: 名前={best_match.get('name')}, 賞金={prize}円, 詳細URL={detail_url}")
        
        # 賞金が0の場合は詳細ページから取得を試みる
        if prize == 0 and detail_url:
            logger.info(f"賞金が0円のため、詳細ページから取得を試みます: {detail_url}")
            try:
                prize = await scraper.get_horse_prize(detail_url)
                logger.info(f"詳細ページから取得した賞金: {prize}円")
            except Exception as e:
                logger.warning(f"詳細ページからの賞金取得に失敗しました: {str(e)}")
        
        # 賞金情報を更新
        if prize is not None and prize > 0:
            success = update_horse_prize(db, horse, prize)
            if success:
                logger.info(f"馬 '{horse_name}' (ID: {horse.id}) の賞金情報を更新しました: {prize}円")
                return True
            else:
                logger.error(f"馬 '{horse_name}' (ID: {horse.id}) の賞金情報の更新に失敗しました")
                return False
        else:
            logger.warning(f"馬 '{horse_name}' (ID: {horse.id}) の有効な賞金情報を取得できませんでした")
            # 次回の更新間隔を短くする
            horse.update_interval_months = max(1, (horse.update_interval_months or 3) // 2)
            horse.next_update_due_date = datetime.now() + relativedelta(months=horse.update_interval_months)
            horse.last_prize_update = datetime.now()
            db.add(horse)
            db.commit()
            return False
            
    except Exception as e:
        logger.error(f"馬 '{horse_name}' (ID: {horse.id}) の処理中にエラーが発生しました: {str(e)}", exc_info=True)
        db.rollback()
        return False
    finally:
        # レートリミット対策（1〜3秒のランダムな遅延）
        delay = random.uniform(1, 3)
        logger.debug(f"{delay:.2f}秒待機します...")
        await asyncio.sleep(delay)

@retry_on_db_error(max_retries=3, delay=5)
def get_db_session():
    """データベースセッションを取得する（リトライ付き）"""
    return SessionLocal()

async def process_horses_async(batch_size: int = 10):
    """賞金情報を更新する非同期メイン処理
    
    Args:
        batch_size (int): 一度に処理する馬の数
    """
    logger.info("賞金情報の更新を開始します")
    
    try:
        # APIから更新対象の馬を取得
        response = api_client.get("api/horses", params={"needs_prize_update": True, "limit": batch_size})
        horses = response.get('items', [])
        
        if not horses:
            logger.info("更新対象の馬はありません")
            return
            
        logger.info(f"{len(horses)}件の馬の賞金情報を更新します")
        
        # スクレイパーを初期化
        scraper = KeibaBookScraper()
        
        # 各馬の処理を実行
        for horse in horses:
            try:
                # 馬の賞金情報を更新
                response = api_client.post(f"api/horses/{horse['id']}/update_prize", {})
                logger.info(f"馬 '{horse.get('name')}' (ID: {horse.get('id')}) の賞金情報を更新しました")
                
                # レートリミット対策（1〜3秒のランダムな遅延）
                delay = random.uniform(1, 3)
                await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"馬の処理中にエラーが発生しました (ID: {horse.get('id')}): {str(e)}")
                continue
        
        logger.info("処理が完了しました")
        
    except Exception as e:
        logger.error(f"処理中にエラーが発生しました: {str(e)}", exc_info=True)
        raise

def process_horses():
    """同期インターフェースを提供するラッパー関数"""
    parser = argparse.ArgumentParser(description='馬の賞金情報を更新します')
    parser.add_argument('--batch-size', type=int, default=10, help='一度に処理する馬の数')
    args = parser.parse_args()
    
    asyncio.run(process_horses_async(batch_size=args.batch_size))

if __name__ == "__main__":
    process_horses()
