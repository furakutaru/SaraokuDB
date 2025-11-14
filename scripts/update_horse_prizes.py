import os
import sys
import json
import logging
import asyncio
import requests
import psycopg2
import argparse
import time
import random
from pathlib import Path
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Optional, Dict, Any, Union, Tuple
from dotenv import load_dotenv

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# 環境変数の読み込み
env_path = Path(__file__).parent.parent / 'backend' / '.env'
if env_path.exists():
    load_dotenv(env_path, override=True)

# 環境変数から認証情報を取得
PROD_API_BASE_URL = os.getenv('PROD_API_BASE_URL')
PROD_API_USERNAME = os.getenv('PROD_API_USERNAME')
PROD_API_PASSWORD = os.getenv('PROD_API_PASSWORD')

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

class APIClient:
    def __init__(self):
        self.base_url = PROD_API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SaraokuDB-Updater/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        self.authenticate()
        
    def authenticate(self):
        """API認証を行いトークンを取得"""
        if not all([self.base_url, PROD_API_USERNAME, PROD_API_PASSWORD]):
            raise ValueError("API認証情報が正しく設定されていません")
            
        try:
            # 認証URLを修正（/api を削除）
            auth_url = f"{self.base_url.rstrip('/')}/auth/token"
            logger.info(f"認証URL: {auth_url}")
            
            # 認証リクエストを送信（x-www-form-urlencoded形式で送信）
            response = self.session.post(
                auth_url,
                data={
                    'username': PROD_API_USERNAME,
                    'password': PROD_API_PASSWORD,
                    'grant_type': 'password'  # OAuth2の場合は必要
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                }
            )
            
            # レスポンスのステータスコードを確認
            response.raise_for_status()
            
            # トークンを取得
            token_data = response.json()
            access_token = token_data.get('access_token')
            
            if not access_token:
                raise ValueError("認証トークンを取得できませんでした")
                
            # セッションに認証ヘッダーを設定
            self.session.headers.update({
                'Authorization': f'Bearer {access_token}'
            })
            
            logger.info("認証に成功しました")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"認証に失敗しました: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"レスポンス: {e.response.text}")
            raise
    
    def get(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

def get_api_client():
    """APIクライアントを取得する"""
    return APIClient()

# ロギング設定
from pathlib import Path
import argparse
import requests
import sqlalchemy
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_, and_, exists
from sqlalchemy.orm.attributes import flag_modified
from dateutil.relativedelta import relativedelta
import psycopg2

# モデルクラスのインポート
from backend.models.horse import Horse
from backend.models.horse_prize_history import HorsePrizeHistory

# スクレイパークラスのインポート
from keibabook_scraper import KeibaBookScraper

# プロジェクトのルートディレクトリをパスに追加
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# 環境変数から設定を取得
import os
import requests
from typing import Dict, Any, Optional

# 更新間隔（日数）
# テスト時: 1、本番環境: 90 に変更する
UPDATE_INTERVAL_DAYS = 1

# データベース接続設定
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL が設定されていません。.env ファイルを確認してください。")

# SQLAlchemy エンジンの作成
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 接続プールの設定
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 古い環境変数チェックコードを削除

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

# データベースセッションを取得する関数
def get_db():
    """
    APIクライアントを取得するジェネレータ
    
    Yields:
        APIClient: APIクライアントインスタンス
    """
    try:
        client = APIClient()
        yield client
    except Exception as e:
        logger.error(f"APIクライアントの初期化に失敗しました: {str(e)}")
        raise
    finally:
        if 'client' in locals():
            # 必要に応じてクリーンアップ処理を追加
            pass

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

# データベースセッションを取得する関数
def get_db():
    """データベースセッションを取得するジェネレータ"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# データベース接続の代わりにAPIを使用
# SessionLocalは実際のセッションクラスを指す必要があります
# この部分は、FastAPIのセットアップに応じて調整が必要です
# 例: SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# または、APIクライアントを使用する場合は、適切なクライアントクラスを設定

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
    """更新対象の馬を取得（API経由）
    
    Args:
        db (Session): APIクライアント
        batch_size (int): 一度に取得する馬の数
        
    Returns:
        List[Horse]: 更新対象の馬のリスト
    """
    try:
        # APIから更新が必要な馬を取得
        logger.info("デバッグ: APIから更新対象の馬を取得します...")
        
        # APIクライアントを取得
        api_client = get_api_client()
        
        # 更新が必要な馬を取得
        try:
            response = api_client.get("api/horses", params={
                "needs_prize_update": "true",
                "limit": batch_size
            })
            
            logger.debug(f"APIレスポンス: {response}")
            
            # レスポンスが辞書で'horses'キーを持つ場合
            if isinstance(response, dict) and 'horses' in response:
                horses = response['horses']
            # レスポンスがリストの場合はそのまま使用
            elif isinstance(response, list):
                horses = response
            # レスポンスが辞書で'items'キーを持つ場合
            elif isinstance(response, dict) and 'items' in response:
                horses = response['items']
            # その他の形式の場合は空リストを返す
            else:
                logger.warning(f"予期しないAPIレスポンス形式: {type(response)}")
                return []
                
            logger.info(f"更新対象の馬が {len(horses)} 件見つかりました")
            
            # Horseモデルの有効な属性のみを抽出してHorseオブジェクトを作成
            valid_attrs = set(column.name for column in Horse.__table__.columns)
            result_horses = []
            
            for horse_data in horses:
                # race_record の処理
                if 'race_record' in horse_data and horse_data['race_record'] is not None:
                    if not isinstance(horse_data['race_record'], str):
                        # 辞書やリストの場合はJSON文字列に変換
                        horse_data['race_record'] = json.dumps(horse_data['race_record'], ensure_ascii=False)
                else:
                    horse_data['race_record'] = '{}'  # 空のJSONオブジェクトを表す文字列
                
                # 有効な属性のみを抽出（dam_sireは無視）
                valid_horse_data = {k: v for k, v in horse_data.items() 
                                 if k in valid_attrs and k != 'dam_sire'}
                result_horses.append(Horse(**valid_horse_data))
                
            return result_horses
            
        except Exception as e:
            logger.error(f"APIリクエスト中にエラーが発生しました: {str(e)}")
            return []
            
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
        logger.error(f"馬ID {horse_id} の賞金履歴の更新中にエラーが発生しました: {str(e)}")
        raise

async def update_horse_prize(db, horse, prize: int) -> bool:
    """馬の賞金情報を更新し、次回の更新間隔を調整
    
    Args:
        db: データベースセッション
        horse: 更新対象の馬（Horseオブジェクト）
        prize (int): 新しい賞金額（円）
        
    Returns:
        bool: 更新が成功したかどうか
    """
    try:
        now = datetime.now()
        horse_id = horse.id
        
        # 前回の賞金を取得
        last_prize = db.query(
            func.coalesce(func.max(HorsePrizeHistory.prize), 0)
        ).filter(
            HorsePrizeHistory.horse_id == horse_id
        ).scalar() or 0
        
        # 賞金履歴を記録
        history = HorsePrizeHistory(horse_id=horse_id, prize=prize)
        db.add(history)
        db.commit()
        logger.info(f"馬ID {horse_id} の賞金履歴を更新しました: {prize}円")
        
        # 賞金に変化がなかった場合
        if prize == last_prize:
            # 更新間隔を延長
            if horse.update_interval_months < 12:  # 1年未満の場合
                horse.update_interval_months = min(horse.update_interval_months * 2, 12)
            else:
                horse.update_interval_months = 12  # 最大1年ごと
                
            # 3年間変化がなければ引退とみなす
            if horse.last_prize_update and (now - horse.last_prize_update).days >= 3 * 365:
                horse.is_retired = True
                horse.next_update_due_date = None
                logger.info(f"馬ID {horse_id} は3年間賞金に変化がなかったため、引退とみなします")
            else:
                horse.next_update_due_date = now + relativedelta(months=horse.update_interval_months)
                logger.info(f"馬ID {horse_id} の次回更新間隔を {horse.update_interval_months} ヶ月後に設定")
        else:
            # 賞金に変化があれば間隔をリセット
            horse.update_interval_months = 3
            horse.next_update_due_date = now + relativedelta(months=3)
            logger.info(f"馬ID {horse_id} の賞金が更新されたため、更新間隔を3ヶ月にリセット")
        
        # 最終更新日を更新
        horse.last_prize_update = now
        horse.total_prize_latest = prize
        
        db.commit()
        logger.info(f"馬ID {horse_id} の賞金情報を更新しました: {prize}円")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"馬ID {horse_id} の更新中にエラーが発生しました: {str(e)}", exc_info=True)
        return False

async def process_horse(scraper, db, horse):
    """個々の馬の賞金情報を更新する非同期関数
    
    Args:
        scraper: スクレイピング用のクライアント
        db: データベースセッション
        horse: 更新対象の馬（Horseオブジェクト）
        
    Returns:
        bool: 処理が成功したかどうか
    """
    try:
        horse_id = horse.id
        horse_name = horse.name
        logger.info(f"馬 '{horse_name}' (ID: {horse_id}) の賞金情報を更新中...")
        
        # スクレイピングで馬の情報を取得
        # ここでは仮に1000万円を返すようにしていますが、実際のロジックに合わせて修正してください
        prize = 10000000  # 仮の値
        
        if prize is not None:
            # 賞金情報を更新
            return await update_horse_prize(db, horse, prize)
        else:
            logger.warning(f"馬 '{horse_name}' (ID: {horse_id}) の賞金情報を取得できませんでした")
            return False
            
    except Exception as e:
        logger.error(f"馬 '{horse_name if 'horse_name' in locals() else '不明'}' (ID: {horse_id if 'horse_id' in locals() else '不明'}) の更新中にエラーが発生しました: {str(e)}")
        return False
        await asyncio.sleep(delay)
def get_db():
    """データベースセッションを取得する"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# APIクライアントを初期化
try:
    api_client = APIClient()
    logger.info("APIクライアントの初期化に成功しました")
except Exception as e:
    logger.error(f"APIクライアントの初期化に失敗しました: {str(e)}")
    raise

async def process_horses_async(batch_size=10):
    """馬の賞金情報を非同期で更新"""
    global api_client
    if api_client is None:
        logger.error("APIクライアントが初期化されていません")
        return

    try:
        logger.info("賞金情報の更新を開始します")
        
        # データベースセッションを取得
        db = next(get_db())
        
        try:
            # 更新対象の馬を取得
            horses = get_horses_to_update(db, batch_size)
            if not horses:
                logger.info("更新対象の馬はありません")
                return

            logger.info(f"更新対象の馬が {len(horses)} 件見つかりました")
            
            # 各馬の賞金情報を更新
            for horse in horses:
                scraper = None
                try:
                    scraper = KeibaBookScraper()
                    success = await process_horse(scraper, db, horse)
                    if success:
                        logger.info(f"馬 '{horse.name}' (ID: {horse.id}) の賞金情報を更新しました")
                    else:
                        logger.warning(f"馬 '{horse.name}' (ID: {horse.id}) の賞金情報の更新に失敗しました")
                except Exception as e:
                    logger.error(f"馬 '{horse.name}' (ID: {horse.id}) の処理中にエラーが発生しました: {str(e)}", exc_info=True)
                finally:
                    # 各馬の処理後にセッションをクローズ
                    if scraper is not None and hasattr(scraper, 'close'):
                        await scraper.close()
                    await asyncio.sleep(1)  # レートリミット対策

        finally:
            # セッションをクローズ
            db.close()

    except Exception as e:
        logger.error(f"賞金情報の更新中にエラーが発生しました: {str(e)}", exc_info=True)
        raise
    finally:
        # セッションをクローズ
        if 'db' in locals():
            try:
                db.close()
            except Exception as e:
                logger.error(f"データベースセッションのクローズ中にエラーが発生しました: {str(e)}")

async def process_horses():
    """非同期処理を行うメイン関数"""
    parser = argparse.ArgumentParser(description='馬の賞金情報を更新します')
    parser.add_argument('--batch-size', type=int, default=10, help='一度に処理する馬の数')
    args = parser.parse_args()
    
    await process_horses_async(batch_size=args.batch_size)

async def main():
    try:
        await process_horses()
        return 0
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}", exc_info=True)
        return 1
    finally:
        # グローバルなAPIクライアントをクローズ
        if 'api_client' in globals() and api_client is not None:
            if hasattr(api_client, 'session') and hasattr(api_client.session, 'close'):
                if hasattr(api_client.session, '__aexit__'):
                    await api_client.session.close()
                elif callable(getattr(api_client.session, 'close', None)):
                    api_client.session.close()
                logger.info("APIクライアントをクローズしました")

def run_async():
    """非同期処理を実行するラッパー関数"""
    try:
        return asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("処理をユーザーにより中断されました")
        return 0
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(run_async())
