import os
import sys
import json
import logging
import asyncio
import time
import aiohttp
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Generator, Union, Tuple, AsyncGenerator
from urllib.parse import urljoin
from dateutil.relativedelta import relativedelta
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
        # 本番環境の認証情報を優先的に使用
        self.api_base_url = os.getenv('PROD_API_BASE_URL')
        self.api_username = os.getenv('PROD_API_USERNAME')
        self.api_password = os.getenv('PROD_API_PASSWORD')
        
        # デバッグ用ログ
        logger.info(f"API Base URL: {self.api_base_url}")
        logger.info(f"API Username: {'*' * len(self.api_username) if self.api_username else 'Not Set'}")
        
        if not all([self.api_base_url, self.api_username, self.api_password]):
            raise ValueError("API認証情報が正しく設定されていません")
            
        self.api_base_url = self.api_base_url.rstrip('/')
        self.session = None
        self._session = None
        self._headers = {
            'User-Agent': 'SaraokuDB-Updater/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        # 認証は非同期に行うため、ここでは実行しない
    
    async def authenticate(self):
        """API認証を行い、アクセストークンを取得"""
        auth_url = f"{self.api_base_url}/api/auth/token"  
        auth_data = {
            'username': self.api_username,
            'password': self.api_password
        }
        
        # セッションがなければ作成
        if self._session is None:
            self._session = aiohttp.ClientSession(headers=self._headers)
        
        try:
            async with self._session.post(
                auth_url,
                data=auth_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            ) as response:
                response.raise_for_status()
                token_data = await response.json()
                self.access_token = token_data.get('access_token')
                
                if not self.access_token:
                    raise ValueError("認証トークンを取得できませんでした")
                    
                # セッションヘッダーにトークンを設定
                self._headers['Authorization'] = f'Bearer {self.access_token}'
                
                logger.info("認証に成功しました")
                return True
                
        except Exception as e:
            logger.error(f"認証に失敗しました: {str(e)}")
            if hasattr(e, 'status') and hasattr(e, 'text'):
                logger.error(f"ステータスコード: {e.status}")
                logger.error(f"レスポンス: {await e.text() if hasattr(e, 'text') else 'N/A'}")
            raise
    
    async def get(self, endpoint, params=None):
        """GETリクエストを送信"""
        url = f"{self.api_base_url}/{endpoint.lstrip('/')}"
        
        # セッションがなければ作成
        if self._session is None:
            self._session = aiohttp.ClientSession(headers=self._headers)
        
        try:
            # 認証トークンが設定されていればヘッダーに追加
            headers = self._headers.copy()
            if hasattr(self, 'access_token') and self.access_token:
                headers['Authorization'] = f'Bearer {self.access_token}'
            
            # デバッグ用ログ
            logger.debug(f"GETリクエスト: {url}")
            if params:
                logger.debug(f"クエリパラメータ: {params}")
            
            async with self._session.get(url, params=params, headers=headers, timeout=30) as response:
                response.raise_for_status()
                return await response.json()
                
        except Exception as e:
            logger.error(f"GETリクエストに失敗しました: {str(e)}")
            if hasattr(e, 'status') and hasattr(e, 'text'):
                logger.error(f"ステータスコード: {e.status}")
                logger.error(f"レスポンス: {await e.text() if hasattr(e, 'text') else 'N/A'}")
            raise

    async def post(self, endpoint, data=None):
        """POSTリクエストを送信"""
        url = f"{self.api_base_url}/{endpoint.lstrip('/')}"

        if self._session is None:
            self._session = aiohttp.ClientSession(headers=self._headers)

        try:
            headers = self._headers.copy()
            if hasattr(self, 'access_token') and self.access_token:
                headers['Authorization'] = f'Bearer {self.access_token}'

            logger.debug(f"POSTリクエスト: {url}")
            logger.debug(f"ボディ: {data}")

            async with self._session.post(url, json=data, headers=headers, timeout=30) as response:
                response.raise_for_status()
                return await response.json()

        except Exception as e:
            logger.error(f"POSTリクエストに失敗しました: {str(e)}")
            if hasattr(e, 'status') and hasattr(e, 'text'):
                logger.error(f"ステータスコード: {e.status}")
                logger.error(f"レスポンス: {await e.text() if hasattr(e, 'text') else 'N/A'}")
            raise

    async def put(self, endpoint, data=None):
        """PUTリクエストを送信"""
        url = f"{self.api_base_url}/{endpoint.lstrip('/')}"

        if self._session is None:
            self._session = aiohttp.ClientSession(headers=self._headers)

        try:
            headers = self._headers.copy()
            if hasattr(self, 'access_token') and self.access_token:
                headers['Authorization'] = f'Bearer {self.access_token}'

            logger.debug(f"PUTリクエスト: {url}")
            logger.debug(f"ボディ: {data}")

            async with self._session.put(url, json=data, headers=headers, timeout=30) as response:
                response.raise_for_status()
                return await response.json()

        except Exception as e:
            logger.error(f"PUTリクエストに失敗しました: {str(e)}")
            if hasattr(e, 'status') and hasattr(e, 'text'):
                logger.error(f"ステータスコード: {e.status}")
                logger.error(f"レスポンス: {await e.text() if hasattr(e, 'text') else 'N/A'}")
            raise
            
    async def patch(self, endpoint, data=None):
        """PATCHリクエストを送信"""
        url = f"{self.api_base_url}/{endpoint.lstrip('/')}"

        if self._session is None:
            self._session = aiohttp.ClientSession(headers=self._headers)

        try:
            headers = self._headers.copy()
            if hasattr(self, 'access_token') and self.access_token:
                headers['Authorization'] = f'Bearer {self.access_token}'

            logger.debug(f"PATCHリクエスト: {url}")
            logger.debug(f"ボディ: {data}")

            async with self._session.patch(url, json=data, headers=headers, timeout=30) as response:
                response.raise_for_status()
                return await response.json()

        except Exception as e:
            logger.error(f"PATCHリクエストに失敗しました: {str(e)}")
            if hasattr(e, 'status') and hasattr(e, 'text'):
                logger.error(f"ステータスコード: {e.status}")
                logger.error(f"レスポンス: {await e.text() if hasattr(e, 'text') else 'N/A'}")
            raise
            
    async def options(self, endpoint):
        """OPTIONSリクエストを送信して、APIがサポートしているメソッドを取得"""
        url = f"{self.api_base_url}/{endpoint.lstrip('/')}"

        if self._session is None:
            self._session = aiohttp.ClientSession(headers=self._headers)

        try:
            headers = self._headers.copy()
            if hasattr(self, 'access_token') and self.access_token:
                headers['Authorization'] = f'Bearer {self.access_token}'

            logger.debug(f"OPTIONSリクエスト: {url}")

            async with self._session.options(url, headers=headers, timeout=30) as response:
                allowed_methods = response.headers.get('Allow', '').split(',')
                allowed_methods = [m.strip() for m in allowed_methods]
                logger.info(f"エンドポイント {url} で許可されているメソッド: {', '.join(allowed_methods)}")
                return allowed_methods

        except Exception as e:
            logger.error(f"OPTIONSリクエストに失敗しました: {str(e)}")
            if hasattr(e, 'status') and hasattr(e, 'text'):
                logger.error(f"ステータスコード: {e.status}")
                logger.error(f"レスポンス: {await e.text() if hasattr(e, 'text') else 'N/A'}")
            return []


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
        response = asyncio.run(self.api_client.get(endpoint, params=self.filters))
        return [self.model(**item) for item in response.get('items', [])]
    
    def first(self):
        result = self.all()
        return result[0] if result else None

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
UPDATE_INTERVAL_DAYS = 90

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
    client = None
    try:
        client = APIClient()
        logger.info("APIクライアントの初期化に成功しました")
        yield client
    except Exception as e:
        logger.error(f"APIクライアントの初期化に失敗しました: {str(e)}")
        raise
    finally:
        if client is not None and hasattr(client, 'session'):
            client.session.close()

async def get_horses_to_update(db: APIClient, batch_size: int = 10) -> List[Dict]:
    """更新対象の馬を取得（API経由）
    
    Args:
        db (APIClient): APIクライアント
        batch_size (int): 一度に取得する馬の数
        
    Returns:
        List[Dict]: 更新対象の馬のリスト
    """
    try:
        # APIから更新対象の馬を取得
        logger.info("デバッグ: APIから更新対象の馬を取得します...")
        
        try:
            response = await db.get("api/horses", {
                "needs_prize_update": "true",
                "limit": str(batch_size)  # 文字列に変換
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
            else:
                logger.warning(f"予期しないAPIレスポンス形式: {type(response)}")
                return []
                
            if not horses:
                logger.info("更新対象の馬が見つかりませんでした")
                return []

            total = len(horses)
            broodmare_skipped = [h for h in horses if h.get('is_broodmare')]
            if broodmare_skipped:
                logger.info(
                    "繁殖牝馬のため賞金更新対象から除外: %d件 (例: %s)",
                    len(broodmare_skipped),
                    broodmare_skipped[0].get('name', '馬名不明')
                )

            filtered = [h for h in horses if not h.get('is_broodmare')]

            if not filtered:
                logger.info(
                    "取得した %d 件がすべて繁殖牝馬だったため、更新対象はありません",
                    total
                )
                return []

            logger.info(
                "更新対象の馬が %d 件見つかりました (繁殖牝馬で除外: %d件)",
                len(filtered),
                total - len(filtered)
            )
            return filtered
            
        except Exception as e:
            logger.error(f"APIリクエスト中にエラーが発生しました: {str(e)}")
            return []
            
    except Exception as e:
        logger.error(f"更新対象の馬の取得中にエラーが発生しました: {str(e)}", exc_info=True)
        return []

async def update_prize_history(db: APIClient, horse_id: int, prize: int) -> Dict:
    """賞金履歴を更新（API経由）
    
    Args:
        db: APIClientインスタンス
        horse_id: 馬ID
        prize: 賞金額
    
    Returns:
        Dict: 更新された馬情報
    """
    try:
        # 現在の馬の情報を取得
        current_horse = await db.get(f"api/horses/{horse_id}")
        
        # 更新するデータを準備
        update_data = {
            "current_prize": prize,
            "last_prize_update": datetime.now(timezone.utc).isoformat(),
            "next_update_due_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "total_prize_latest": prize
        }
        
        # 馬情報を更新するエンドポイントにPATCHリクエストを送信
        response = await db.patch(f"api/horses/{horse_id}", update_data)
        logger.info(f"馬ID {horse_id} の賞金情報を更新しました: {prize}円")
        return response
    except Exception as e:
        logger.error(f"馬ID {horse_id} の賞金情報の更新中にエラーが発生しました: {str(e)}")
        raise

async def update_horse_prize(db: APIClient, horse: Dict, prize: int) -> bool:
    """馬の賞金情報を更新し、次回の更新間隔を調整（API経由）
    
    Args:
        db (APIClient): APIクライアント
        horse (Dict): 更新対象の馬の情報
        prize (int): 新しい賞金額（円）
        
    Returns:
        bool: 更新が成功したかどうか
    """
    try:
        horse_id = horse.get('id')
        if not horse_id:
            logger.error("馬IDが指定されていません")
            return False
            
        # 前回の賞金を取得
        last_prize = horse.get('current_prize', 0)
        
        # 賞金履歴を記録
        await update_prize_history(db, horse_id, prize)
        
        # 更新間隔の調整
        update_interval_months = horse.get('update_interval_months', 1)
        next_update_due_date = None
        is_retired = False
        
        # 賞金に変化がなかった場合
        if prize == last_prize:
            # 更新間隔を延長
            if update_interval_months < 12:  # 1年未満の場合
                update_interval_months = min(update_interval_months * 2, 12)
            else:
                update_interval_months = 12  # 最大1年ごと
                
            # 3年間変化がなければ引退とみなす
            last_update_str = horse.get('last_prize_update')
            if last_update_str:
                last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
                if (datetime.now(timezone.utc) - last_update).days >= 3 * 365:
                    is_retired = True
                    next_update_due_date = None
                    logger.info(f"馬ID {horse_id} は3年間賞金に変化がなかったため、引退とみなします")
                else:
                    next_update_due_date = (datetime.now(timezone.utc) + 
                                          relativedelta(months=update_interval_months)).isoformat()
                    logger.info(f"馬ID {horse_id} の次回更新間隔を {update_interval_months} ヶ月後に設定")
            else:
                next_update_due_date = (datetime.now(timezone.utc) + 
                                      relativedelta(months=update_interval_months)).isoformat()
        else:
            # 賞金に変化があった場合は更新間隔をリセット
            update_interval_months = 3
            next_update_due_date = (datetime.now(timezone.utc) + 
                                  relativedelta(months=3)).isoformat()
            logger.info(f"馬ID {horse_id} の賞金が更新されたため、更新間隔を3ヶ月にリセット")
        
        # 馬の情報を更新
        update_data = {
            "current_prize": prize,
            "last_prize_update": datetime.now(timezone.utc).isoformat(),
            "update_interval_months": update_interval_months,
            "is_retired": is_retired,
            "total_prize_latest": prize
        }
        
        if next_update_due_date:
            update_data["next_update_due_date"] = next_update_due_date
            
        response = await db.patch(f"api/horses/{horse_id}", update_data)
        logger.info(f"馬ID {horse_id} の情報を更新しました: {response}")
        
        return True
        
    except Exception as e:
        logger.error(f"馬ID {horse_id} の情報更新中にエラーが発生しました: {str(e)}", exc_info=True)
        return False

async def push_next_update_only(db: APIClient, horse: Dict, months: int = 3) -> bool:
    """賞金未登録想定の馬など、スクレイプを行わず次回更新日だけ先送りする。
    
    Args:
        db: APIクライアント
        horse: 馬情報（APIからの辞書）
        months: 先送りする月数
    Returns:
        bool
    """
    try:
        horse_id = horse.get('id')
        if not horse_id:
            return False
        payload = {
            "next_update_due_date": (datetime.now(timezone.utc) + relativedelta(months=months)).isoformat()
        }
        await db.patch(f"api/horses/{horse_id}", payload)
        logger.info(f"馬ID {horse_id} は未登録名（年次表記）のためスクレイプをスキップ。次回更新を{months}ヶ月後へ設定")
        return True
    except Exception as e:
        logger.error(f"馬ID {horse.get('id')} の次回更新日更新に失敗: {str(e)}")
        return False

async def process_horse(scraper, db: APIClient, horse: Dict) -> bool:
    """1頭の馬の賞金情報を更新"""
    try:
        horse_id = horse.get('id')
        horse_name = horse.get('name', '不明')
        # 検索用に馬名を正規化（例: 「〇〇の23/24」などの年次表記を除去）
        try:
            import re
            search_name = re.sub(r"の\d{2}$", "", horse_name).strip()
        except Exception:
            search_name = horse_name
        
        logger.info(f"馬ID {horse_id} ({horse_name}) の賞金情報を更新中...")

        # 「◯◯の23/24」などの未登録名はスキップして次回更新だけ先送り
        try:
            import re
            if re.search(r"の\d{2}$", horse_name):
                return await push_next_update_only(db, horse, months=3)
        except Exception:
            pass
        
        # スクレイピングで賞金情報を取得（実装版）
        # ヒット率向上のため、父母名・性別で絞り込まない（DBの表記ゆれ・ローマ字などで弾かれるため）
        father = ''
        mother = ''
        auction_date = horse.get('auction_date')
        gender = None

        horse_info = await scraper.get_horse_info(
            name=search_name,
            father=father,
            mother=mother,
            auction_date=auction_date,
            gender=gender
        )

        if not horse_info or horse_info.get('prize') is None:
            logger.warning(f"馬ID {horse_id} の賞金情報を取得できませんでした（name={horse_name}, father={father}, mother={mother}）")
            return False
        
        # 賞金が0円の場合は未出走・未入着として正常扱いし更新する
        if horse_info.get('prize') == 0:
            logger.info(f"馬ID {horse_id} の賞金は0円（未出走または未入着）。0円として更新します。")

        prize = int(horse_info.get('prize') or 0)
            
        # 賞金情報を更新
        success = await update_horse_prize(db, horse, prize)
        if success:
            logger.info(f"馬ID {horse_id} の賞金情報を更新しました: {prize:,}円")
        else:
            logger.warning(f"馬ID {horse_id} の賞金情報の更新に失敗しました")
            
        return success
        
    except Exception as e:
        logger.error(f"馬ID {horse.get('id', '不明')} の処理中にエラーが発生しました: {str(e)}", exc_info=True)
        return False
            
async def process_horses_async(batch_size=10):
    """馬の賞金情報を非同期で更新"""
    db: Optional[APIClient] = None
    try:
        logger.info("賞金情報の更新を開始します")
        
        # APIクライアントを初期化して認証
        db = APIClient()
        await db.authenticate()

        # APIがサポートしているメソッドを確認
        allowed_methods = await db.options("api/horses/1")
        logger.info(f"APIがサポートしているメソッド: {', '.join(allowed_methods) if allowed_methods else '不明'}")
        
        # スクレイパーを初期化（実装版を使用）
        from scripts.keibabook_scraper import KeibaBookScraper as RealKeibaBookScraper
        scraper_ctx = RealKeibaBookScraper(verify_ssl=False)
        
        # 更新対象の馬を取得
        horses = await get_horses_to_update(db, batch_size)
        
        if not horses:
            logger.info("更新対象の馬が見つかりませんでした")
            return True
            
        logger.info(f"更新対象の馬が {len(horses)} 件見つかりました")
        
        # 各馬の賞金情報を非同期で更新
        async with scraper_ctx as scraper:
            # 併行数を制限してレートリミット回避
            semaphore = asyncio.Semaphore(3)

            async def run_with_sem(h):
                async with semaphore:
                    return await process_horse(scraper, db, h)

            tasks = []
            for idx, h in enumerate(horses):
                # スタートを少しずつずらす
                await asyncio.sleep(0.2)
                tasks.append(asyncio.create_task(run_with_sem(h)))

            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果を集計
        success_count = sum(1 for r in results if r is True)
        failure_count = len(results) - success_count
        
        logger.info(f"賞金情報の更新が完了しました (成功: {success_count}件, 失敗: {failure_count}件)")
        
        return success_count > 0 and failure_count == 0
            
    except Exception as e:
        logger.error(f"賞金情報の更新中にエラーが発生しました: {str(e)}", exc_info=True)
        return False
    finally:
        # セッションをクローズ
        if db is not None and hasattr(db, '_session') and db._session:
            await db._session.close()

async def main_async():
    """非同期メイン関数"""
    try:
        # コマンドライン引数のパース
        parser = argparse.ArgumentParser(description='馬の賞金情報を更新するスクリプト')
        parser.add_argument('--batch-size', type=int, default=10, help='一度に処理する馬の数')
        args = parser.parse_args()
        
        # 非同期処理を実行
        return await process_horses_async(batch_size=args.batch_size)
        
    except KeyboardInterrupt:
        logger.info("処理を中断します")
        return 1
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {str(e)}", exc_info=True)
        return 1

def main():
    """同期メイン関数（エントリーポイント）"""
    result = asyncio.run(main_async())
    # main_async は True/False を返す想定のため、終了コードに変換する
    if isinstance(result, bool):
        return 0 if result else 1
    # それ以外（intなど）が返った場合はそのまま利用
    return result


if __name__ == "__main__":
    sys.exit(main())
