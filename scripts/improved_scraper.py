#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
楽天競馬オークションのスクレイピングスクリプト

このスクリプトは、楽天競馬オークションのデータをスクレイピングし、構造化されたデータとして保存します。
"""

import argparse
import concurrent.futures
import functools
import hashlib
import json
import logging
import os
import re
import sys
import time
import traceback
import urllib.parse
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from urllib.parse import urljoin, urlparse, parse_qs

# デフォルトの定数
DEFAULT_TIMEOUT = 30  # デフォルトのタイムアウト（秒）
MAX_RETRIES = 3  # デフォルトの最大リトライ回数
BACKOFF_FACTOR = 0.5  # 指数バックオフの係数

# プロジェクトのルートディレクトリをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 設定モジュールのインポート
from scripts.core.config import config
from scripts.core.utils.logger import get_logger

# カスタムコンポーネントのインポート
from scripts.components.horse_basic_info_extractor import HorseBasicInfoExtractor
from scripts.components.jbis_link_extractor import JbisLinkExtractor
from scripts.components.pedigree_extractor import PedigreeExtractor
from scripts.components.race_record_extractor import RaceRecordExtractor
from scripts.components.prize_extractor import PrizeExtractor
from scripts.components.comment_extractor import CommentExtractor
from scripts.components.prize_money import CurrentPrizeExtractor, AuctionPrizeExtractor
from scripts.components.price_extractor import PriceExtractor

# バックエンドモジュールのインポート
try:
    from backend.scrapers.data_helpers import save_horse, save_auction_history
except ImportError as e:
    print(f"バックエンドモジュールのインポートに失敗しました: {e}")
    print("テストモードで実行します...")
    save_horse = lambda *args, **kwargs: print(f"[TEST] save_horse called with {args}, {kwargs}")
    save_auction_history = lambda *args, **kwargs: print(f"[TEST] save_auction_history called with {args}, {kwargs}")

# サードパーティのライブラリ
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util.retry import Retry

# ロガーの設定
logger = get_logger(__name__)

# 定数の設定
CACHE_DIR = config.cache.cache_dir
OUTPUT_DIR = config.output.output_dir

# スクレイパー設定
BASE_URL = config.scraper.base_url
TIMEOUT = config.scraper.timeout
MAX_RETRIES = config.scraper.max_retries
BACKOFF_FACTOR = config.scraper.backoff_factor
MAX_WORKERS = config.scraper.max_workers
USER_AGENT = config.scraper.user_agent

# 健康関連のキーワード
HEALTH_KEYWORDS = [
    '手術歴', '骨折', '皮膚病', '屈腱炎', '腫れ', '咽頭虚脱', '脱臼', '跛行', '打撲'
]

class CacheManager:
    """HTMLキャッシュを管理するクラス"""
    
    def __init__(self, base_dir: Path = None):
        """
        キャッシュマネージャーを初期化します。
        
        Args:
            base_dir: キャッシュディレクトリのパス（指定しない場合は設定値を使用）
        """
        self.base_dir = base_dir if base_dir is not None else config.cache.cache_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.cache = {}
        self._load_cache()
        logger.info(f"キャッシュディレクトリ: {self.base_dir}")
        
    def _get_cache_path(self, url: str) -> Path:
        """
        URLからキャッシュファイルのパスを生成します。
        
        Args:
            url: キャッシュするURL
            
        Returns:
            Path: キャッシュファイルのパス
        """
        # URLをハッシュ化してファイル名を生成
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        cache_dir = self.base_dir / "details"
        cache_dir.mkdir(exist_ok=True, parents=True)
        return cache_dir / f"{url_hash}.html"
    
    def load_html(self, url: str) -> Optional[str]:
        """
        URLに対応するキャッシュされたHTMLを読み込みます。
        
        Args:
            url: 読み込むHTMLのURL
            
        Returns:
            str: キャッシュされたHTMLコンテンツ。見つからない場合はNone
        """
        cache_path = self._get_cache_path(url)
        if not cache_path.exists():
            return None
            
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"キャッシュの読み込みに失敗しました: {cache_path} - {e}")
            return None
            
    def save_html(self, url: str, content: str) -> bool:
        """
        HTMLコンテンツをキャッシュに保存します。
        
        Args:
            url: キャッシュするHTMLのURL
            content: 保存するHTMLコンテンツ
            
        Returns:
            bool: 保存に成功した場合はTrue、失敗した場合はFalse
        """
        try:
            cache_path = self._get_cache_path(url)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.debug(f"HTMLをキャッシュに保存しました: {cache_path}")
            return True
            
        except Exception as e:
            logger.error(f"キャッシュの保存に失敗しました: {url} - {e}")
            return False
            
    def _load_cache(self) -> None:
        """既存のキャッシュをメモリに読み込みます。"""
        if not self.base_dir.exists():
            logger.warning(f"キャッシュディレクトリが存在しません: {self.base_dir}")
            return
            
        cache_dir = self.base_dir / "details"
        if not cache_dir.exists():
            logger.warning(f"詳細キャッシュディレクトリが存在しません: {cache_dir}")
            return
            
        for file in cache_dir.glob('*.html'):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    self.cache[file.stem] = f.read()
            except Exception as e:
                logger.error(f"キャッシュファイルの読み込み中にエラーが発生しました: {file} - {e}")
        
        logger.info(f"キャッシュを読み込みました: {len(self.cache)} 件")
    
    def get(self, url: str) -> Optional[str]:
        """
        キャッシュからHTMLを取得します。
        
        Args:
            url: 取得するURL
            
        Returns:
            str: キャッシュされたHTMLコンテンツ、またはNone
        """
        if not config.cache.enabled:
            return None
            
        cache_file = self._get_cache_path(url)
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    logger.debug(f"キャッシュから読み込み: {url} -> {cache_file}")
                    return f.read()
            except Exception as e:
                logger.error(f"キャッシュの読み込み中にエラーが発生しました: {cache_file} - {e}")
        return None
    
    def set(self, url: str, content: str) -> None:
        """
        HTMLをキャッシュに保存します。
        
        Args:
            url: キャッシュするURL
            content: キャッシュするHTMLコンテンツ
        """
        if not config.cache.enabled:
            return
            
        cache_file = self._get_cache_path(url)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(content)
            self.cache[cache_file.stem] = content
            logger.debug(f"キャッシュに保存: {url} -> {cache_file}")
        except Exception as e:
            logger.error(f"キャッシュの保存中にエラーが発生しました: {cache_file} - {e}")
    
    def clear_expired(self, expire_days: int = 30) -> int:
        """
        有効期限が切れたキャッシュを削除します。
        
        Args:
            expire_days: 有効期限（日数）
            
        Returns:
            int: 削除したキャッシュファイルの数
        """
        if not self.base_dir.exists():
            return 0
            
        cache_dir = self.base_dir / "details"
        if not cache_dir.exists():
            return 0
            
        expired_time = time.time() - (expire_days * 24 * 60 * 60)
        deleted_count = 0
        
        for file in cache_dir.glob('*.html'):
            try:
                if file.stat().st_mtime < expired_time:
                    file.unlink()
                    deleted_count += 1
                    if file.stem in self.cache:
                        del self.cache[file.stem]
            except Exception as e:
                logger.error(f"キャッシュの削除中にエラーが発生しました: {file} - {e}")
        
        logger.info(f"有効期限切れのキャッシュを削除しました: {deleted_count} 件")
        return deleted_count

def extract_prize_from_auction(html_content: str, horse_name: str) -> Dict[str, any]:
    """
    オークションリストページから賞金情報を抽出する
    
    Args:
        html_content (str): オークションリストページのHTML
        horse_name (str): 馬名（デバッグ用）
        
    Returns:
        Dict[str, any]: 抽出した賞金情報を含む辞書
    """
    result = {
        'current_prize': 0.0,  # 万円単位
        'auction_prize': 0.0,  # 万円単位
        'is_breeding_mare': False,
        'is_unraced': False
    }
    
    try:
        # 現在の賞金情報を抽出
        current_extractor = CurrentPrizeExtractor()
        current_result = current_extractor.extract(html_content, horse_name)
        result.update(current_result)
        
        # オークション時の賞金情報を抽出
        auction_extractor = AuctionPrizeExtractor()
        auction_result = auction_extractor.extract(html_content, horse_name)
        result.update(auction_result)
        
        # 未出走馬のチェック
        if '未出走' in html_content:
            result['is_unraced'] = True
            logger.info(f"馬名 '{horse_name}' は未出走のため賞金は0円です")
        
        logger.info(f"馬名 '{horse_name}' の賞金情報を抽出: {result}")
        return result
        
    except Exception as e:
        logger.error(f"賞金情報の抽出中にエラーが発生しました（馬名: {horse_name}）: {str(e)}")
        logger.error(traceback.format_exc())
        return result

def _extract_disease_tags(comment: str) -> str:
    """
    コメントから病気タグを抽出する
    
    Args:
        comment (str): 抽出元のコメントテキスト
        
    Returns:
        str: カンマ区切りの病気タグ。見つからない場合は「なし」を返します。
    """
    if not comment:
        return "なし"
    
    found_tags = [kw for kw in HEALTH_KEYWORDS if kw in comment]
    return ",".join(dict.fromkeys(found_tags)) if found_tags else "なし"

def _extract_comment(html_content: str) -> str:
    """
    馬の詳細ページからコメントを抽出する
    
    Args:
        html_content (str): 馬の詳細ページのHTML
        
    Returns:
        str: 抽出されたコメントテキスト。見つからない場合は空文字列。
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        return CommentExtractor.extract(soup).get('comment', '')
    except Exception as e:
        logger.error(f"コメントの抽出中にエラーが発生しました: {str(e)}")
        return ""

# ロギング設定
log_dir = Path('debug_logs')
try:
    log_dir.mkdir(exist_ok=True, mode=0o755)  # 読み取り/実行権限を明示的に設定
    log_file = log_dir / f'scraper_debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    
    # ログファイルのパスを絶対パスで表示
    log_file = log_file.absolute()
    print(f"[DEBUG] ログファイルパス: {log_file}")
    
    # ログファイルが存在するか確認
    if log_file.exists():
        print(f"[DEBUG] ログファイルが既に存在します: {log_file}")
    else:
        print(f"[DEBUG] 新しいログファイルを作成します: {log_file}")
        log_file.touch(mode=0o644)  # 読み取り/書き込み権限を明示的に設定
        
except Exception as e:
    print(f"[ERROR] ログディレクトリ/ファイルの作成に失敗しました: {e}")
    log_file = Path('scraper_debug.log')  # フォールバック

# ルートロガーの設定
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# 既存のハンドラをクリア
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# ファイルハンドラの設定
file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# コンソールハンドラの設定
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # コンソールにはINFO以上のみ表示
console_formatter = logging.Formatter('%(message)s')
console_handler.setFormatter(console_formatter)

# ハンドラを追加
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# モジュールごとのロガーを取得
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 不要なライブラリのログを無効化
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('bs4').setLevel(logging.WARNING)

# キャッシュディレクトリの設定
CACHE_DIR = Path('html_cache')
CACHE_DIR.mkdir(exist_ok=True)

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# バックエンドのモジュールをインポート
try:
    from backend.scrapers.data_helpers import (
        save_horse,
        save_auction_history,
        load_json_file
    )
except ImportError:
    # テスト用のモック関数
    def save_horse(*args, **kwargs):
        pass
    
    def save_auction_history(*args, **kwargs):
        pass
    
    def load_json_file(*args, **kwargs):
        return {}

class ScraperConfig:
    """スクレイパーの設定を管理するクラス"""
    
    def __init__(self, 
                 max_workers: int = 5, 
                 use_cache: bool = True, 
                 cache_dir: str = 'cache',
                 timeout: int = DEFAULT_TIMEOUT,
                 max_retries: int = MAX_RETRIES,
                 backoff_factor: float = BACKOFF_FACTOR):
        """
        初期化メソッド
        
        Args:
            max_workers: 並列処理の最大ワーカー数
            use_cache: キャッシュを使用するかどうか
            cache_dir: キャッシュディレクトリのパス
            timeout: リクエストのタイムアウト（秒）
            max_retries: 最大リトライ回数
            backoff_factor: リトライ間の待機時間の係数
        """
        self.max_workers = max_workers
        self.use_cache = use_cache
        self.cache_dir = Path(cache_dir)
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor


class TestConfig(ScraperConfig):
    """テスト用の設定クラス"""
    
    def __init__(self, **kwargs):
        """テスト用のデフォルト設定で初期化"""
        super().__init__(
            max_workers=1,  # テスト時は並列処理を無効化
            use_cache=kwargs.get('use_cache', True),
            cache_dir=kwargs.get('cache_dir', 'test_cache'),
            timeout=5,  # テスト時はタイムアウトを短く
            max_retries=0,  # テスト時はリトライを無効化
            backoff_factor=0  # バックオフを無効化
        )


class ImprovedRakutenScraper:
    """楽天競馬オークションのスクレイパークラス"""
    
    def __init__(self, config: Optional[ScraperConfig] = None, **kwargs):
        """
        初期化メソッド
        
        Args:
            config: スクレイパーの設定（Noneの場合はデフォルト設定を使用）
            **kwargs: 後方互換性のための引数（非推奨）
        """
        # 後方互換性のための処理
        if config is None:
            # 古い引数形式で渡された場合は警告を出して新しい形式に変換
            if any(k in kwargs for k in ['test_mode', 'max_workers', 'use_cache', 'cache_dir']):
                logger.warning("古い引数形式は非推奨です。ScraperConfigクラスを使用してください。")
                
                # テストモードの設定
                if kwargs.get('test_mode', False):
                    config = TestConfig(
                        use_cache=kwargs.get('use_cache', True),
                        cache_dir=kwargs.get('cache_dir', 'test_cache')
                    )
                else:
                    config = ScraperConfig(
                        max_workers=kwargs.get('max_workers', 5),
                        use_cache=kwargs.get('use_cache', True),
                        cache_dir=kwargs.get('cache_dir', 'cache')
                    )
            else:
                # 引数が指定されていない場合はデフォルト設定を使用
                config = ScraperConfig()
        
        # 設定を適用
        self.use_cache = config.use_cache
        self.max_workers = config.max_workers
        self.base_url = "https://auction.keiba.rakuten.co.jp/"  # ベースURLを追加
        
        # ロガーの設定
        self.logger = get_logger(__name__)
        self.logger.info(f"スクレイパーを初期化します (use_cache={self.use_cache}, max_workers={self.max_workers})")
        
        # キャッシュマネージャーの初期化
        self.cache_manager = CacheManager(config.cache_dir) if self.use_cache else None
        if self.use_cache:
            self.logger.info(f"キャッシュを有効化: {config.cache_dir}")
        else:
            self.logger.warning("キャッシュが無効化されています")
            
        # セッションの初期化
        self.session = self._create_session(
            timeout=config.timeout,
            max_retries=config.max_retries,
            backoff_factor=config.backoff_factor
        )
        
        # 抽出コンポーネントの初期化
        self.horse_info_extractor = HorseBasicInfoExtractor()
        self.jbis_link_extractor = JbisLinkExtractor()
        self.pedigree_extractor = PedigreeExtractor()
        self.race_record_extractor = RaceRecordExtractor()
        self.prize_extractor = PrizeExtractor()
        self.comment_extractor = CommentExtractor()
        self.current_prize_extractor = CurrentPrizeExtractor()
        self.auction_prize_extractor = AuctionPrizeExtractor()
        self.price_extractor = PriceExtractor()
        
        # 出力ディレクトリの確認
        self.output_dir = Path(OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"出力先ディレクトリ: {self.output_dir}")
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = self.output_dir / f'scraped_horses_{self.session_id}.json'
            
    def start_cache_session(self):
        """キャッシュセッションを開始する"""
        try:
            if not self.use_cache:
                logger.debug("キャッシュが無効化されています")
                return False
                
            if self.cache_session is not None:
                logger.debug("既にキャッシュセッションが開始されています")
                return True
                
            logger.debug("キャッシュセッションを開始します")
            self.cache_session = self.cache_manager.start_session()
            return True
            
        except Exception as e:
            logger.error(f"キャッシュセッションの開始に失敗: {e}")
            logger.error(traceback.format_exc())
            return False

    def _create_session(self, timeout: int = None, max_retries: int = None, backoff_factor: float = None) -> requests.Session:
        """HTTPセッションを作成します。
        
        Args:
            timeout: リクエストのタイムアウト（秒）
            max_retries: 最大リトライ回数
            backoff_factor: リトライ間の待機時間の係数
            
        Returns:
            requests.Session: 設定済みのセッションオブジェクト
        """
        # デフォルト値の設定
        timeout = timeout if timeout is not None else config.scraper.timeout
        max_retries = max_retries if max_retries is not None else config.scraper.max_retries
        backoff_factor = backoff_factor if backoff_factor is not None else config.scraper.backoff_factor
        
        self.logger.debug(f"セッションを作成します (timeout={timeout}, max_retries={max_retries}, backoff_factor={backoff_factor})")
        
        session = requests.Session()
        
        # リトライ設定
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[500, 502, 503, 504, 429],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            respect_retry_after_header=True
        )
        
        # アダプターの設定
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=config.scraper.max_workers * 2,
            pool_maxsize=config.scraper.max_workers * 2,
            pool_block=False
        )
        
        # セッションにアダプターをマウント
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # ヘッダー設定
        session.headers.update({
            'User-Agent': config.scraper.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'max-age=0',
            'Accept-Encoding': 'gzip, deflate, br'
        })
        
        # セッションのタイムアウト設定
        session.request = functools.partial(session.request, timeout=timeout)
        
        return session
        
    def scrape_horse_list(self, url: str = None, use_cache: bool = None) -> List[Dict[str, Any]]:
        """馬の一覧をスクレイピングする
        
        Args:
            url: スクレイピング対象のURL（Noneの場合はベースURLを使用）
            use_cache: キャッシュを使用するかどうか（Noneの場合は設定ファイルの値を使用）
            
        Returns:
            List[Dict[str, Any]]: 馬の情報のリスト
        """
        # 設定の取得
        use_cache = use_cache if use_cache is not None else config.scraper.use_cache
        max_retries = config.scraper.max_retries
        backoff_factor = config.scraper.backoff_factor
        
        try:
            # URLの設定
            target_url = url if url else self.base_url
            self.logger.debug(f"スクレイピングを開始します: {target_url}")
            
            # キャッシュから読み込み
            html_content = None
            if use_cache and hasattr(self, 'cache_manager'):
                self.logger.debug("キャッシュから読み込みを試みます")
                html_content = self.cache_manager.load_html(target_url)
                if html_content:
                    self.logger.debug("キャッシュからHTMLを読み込みました")
            
            # キャッシュがない、またはキャッシュを使用しない場合はリクエストを実行
            if not html_content:
                self.logger.debug("キャッシュがありません。リクエストを実行します")
                for attempt in range(max_retries + 1):
                    try:
                        response = self.session.get(
                            target_url, 
                            timeout=config.scraper.timeout
                        )
                        response.raise_for_status()
                        html_content = response.text
                        
                        # キャッシュに保存
                        if use_cache and hasattr(self, 'cache_manager'):
                            self.cache_manager.save_html(target_url, html_content)
                            self.logger.debug("HTMLをキャッシュに保存しました")
                        break
                            
                    except requests.exceptions.RequestException as e:
                        if attempt == max_retries:
                            self.logger.error(f"リクエストが{max_retries}回連続で失敗しました: {e}")
                            return []
                        
                        wait_time = backoff_factor * (2 ** attempt)
                        self.logger.warning(
                            f"リクエストに失敗しました。{wait_time:.1f}秒後に再試行します... "
                            f"({attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait_time)
            
            # HTMLをパース
            try:
                soup = BeautifulSoup(html_content, 'html.parser')
            except Exception as e:
                self.logger.error(f"HTMLのパースに失敗しました: {e}")
                return []
            
            # 馬のカードを取得
            horse_cards = soup.select('.auctionTableCard')
            total_horses = len(horse_cards)
            
            if not horse_cards:
                debug_html = os.path.join("debug", "debug_horse_list.html")
                os.makedirs(os.path.dirname(debug_html), exist_ok=True)
                with open(debug_html, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                self.logger.warning(f"馬のカードが見つかりませんでした。デバッグ用にHTMLを保存しました: {debug_html}")
                return []
                
            self.logger.info(f"{total_horses}頭の馬を検出しました")

            # 馬の情報を抽出
            horses = []
            failed_count = 0
            
            for i, card in enumerate(horse_cards, 1):
                try:
                    self.logger.debug(f"[{i}/{total_horses}] 馬情報の抽出を開始")
                    
                    # 馬情報の抽出
                    horse_info = self._extract_horse_info(card, i, total_horses)
                    if not horse_info:
                        self.logger.warning(f"[{i}/{total_horses}] 馬情報の抽出に失敗しました")
                        failed_count += 1
                        continue
                    
                    # 詳細ページのURLを追加
                    detail_link = card.select_one('a[href*="detail"]')
                    if detail_link:
                        detail_url = urljoin(self.base_url, detail_link.get('href', '').strip())
                        horse_info['detail_url'] = detail_url
                        self.logger.debug(f"詳細ページURL: {detail_url}")
                    
                    horses.append(horse_info)
                    self.logger.debug(f"[{i}/{total_horses}] 馬情報の抽出が完了: {horse_info.get('name', '不明')}")
                    
                except Exception as e:
                    self.logger.error(f"[{i}/{total_horses}] 馬情報の抽出中にエラーが発生しました: {e}", exc_info=True)
                    failed_count += 1
                    
                    # デバッグモードの場合はエラー詳細をログに出力
                    if config.scraper.debug_mode:
                        debug_info = {
                            'card_html': str(card)[:500] + '...',
                            'error': str(e),
                            'traceback': traceback.format_exc()
                        }
                        self.logger.debug(f"デバッグ情報: {json.dumps(debug_info, ensure_ascii=False, indent=2)}")
            
            # 結果の集計とログ出力
            success_count = len(horses)
            result_summary = {
                'total': total_horses,
                'success': success_count,
                'failed': failed_count,
                'success_rate': f"{(success_count / total_horses * 100):.1f}%" if total_horses > 0 else "0.0%"
            }
            
            self.logger.info("\n=== スクレイピング結果 ===")
            self.logger.info(f"総数: {result_summary['total']}頭")
            self.logger.info(f"成功: {result_summary['success']}頭 ({result_summary['success_rate']})")
            self.logger.info(f"失敗: {result_summary['failed']}頭")
            
            if failed_count > 0:
                self.logger.warning(f"{failed_count}頭の馬情報の抽出に失敗しました")
            
            return horses
                
        except Exception as e:
            self.logger.error(f"馬の一覧のスクレイピング中に予期せぬエラーが発生しました: {e}", exc_info=True)
            if hasattr(self, 'test_mode') and self.test_mode:
                raise  # テストモードの場合は例外を再スロー
            return []
        return []

    def _extract_name_sex_age(self, card) -> Tuple[Optional[Dict[str, str]], bool]:
        """馬のカードから基本情報（馬名、性別、年齢）を抽出する
        
        Args:
            card: BeautifulSoupのカード要素
            
        Returns:
            Tuple[Optional[Dict[str, str]], bool]: 
                - 抽出した基本情報の辞書（失敗時はNone）
                - 成功可否（True: 成功, False: 失敗）
        """
        try:
            # 馬名を抽出
            name_elem = card.select_one('.auctionTableCard__name, .horse-name, [data-testid="horse-name"]')
            if not name_elem:
                return None, False
                
            # 馬名のクリーンアップ処理
            name = self._clean_horse_name(name_elem)
            
            # 性別と年齢を取得
            sex_elem = card.select_one('.horseLabelWrapper__horseSex')
            age_elem = card.select_one('.horseLabelWrapper__horseAge')
            
            sex = sex_elem.get_text(strip=True) if sex_elem else ''
            age = self._extract_age(age_elem, card) if age_elem else ''
            
            return {
                'name': name,
                'sex': sex,
                'age': age
            }, True
            
        except Exception as e:
            logger.error(f"馬の基本情報抽出中にエラーが発生しました: {e}", exc_info=True)
            return None, False

    def _clean_horse_name(self, name_elem) -> str:
        """馬名をクリーンアップする
        
        Args:
            name_elem: BeautifulSoupの要素オブジェクト
            
        Returns:
            str: クリーンアップされた馬名
        """
        if not name_elem:
            return ""
            
        # 1. まず、要素内のすべてのテキストを取得
        name = name_elem.get_text(' ', strip=True)
        
        # 2. 最初の半角・全角スペース以降を削除
        name = re.split(r'[ 　]', name, 1)[0]
        
        # 3. 不要な文字列を削除
        for s in ["※", "登録抹消", "新馬", "未出走"]:
            name = name.replace(s, "")
            
        return name.strip()

    def _extract_age(self, age_elem, card):
        """年齢を抽出する
        
        Args:
            age_elem: 年齢要素
            card: カード要素（バックアップ用）
            
        Returns:
            Optional[int]: 抽出された年齢（失敗時はNone）
        """
        # 1. 年齢要素から直接抽出を試みる
        if age_elem:
            age_text = age_elem.get_text(strip=True)
            age_match = re.search(r'(\d+)', age_text)
            if age_match:
                return int(age_match.group(1))
        
        if not card:
            return None
            
        # 2. カード全体から年齢を検索（バックアップ）
        card_text = card.get_text(' ', strip=True)
        
        # パターン1: 「○歳」の形式
        age_match = re.search(r'(\d+)\s*歳', card_text)
        if age_match:
            return int(age_match.group(1))
            
        # パターン2: 年齢が数字のみで表記されている場合
        age_match = re.search(r'(?:年齢|Age|年令)[:：]?\s*(\d+)', card_text)
        if age_match:
            return int(age_match.group(1))
        
        # パターン3: 生年月日から計算
        birth_year_match = re.search(r'(\d{4})年\s*\d{1,2}月\s*\d{1,2}日', card_text)
        if birth_year_match:
            from datetime import datetime
            birth_year = int(birth_year_match.group(1))
            current_year = datetime.now().year
            return current_year - birth_year
        
        # 3. タイトルから年齢を抽出（最終手段）
        title_elem = card.find_previous('title')
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            age_match = re.search(r'(\d+)歳', title_text)
            if age_match:
                return int(age_match.group(1))
        
        return None

    def _extract_seller_info(self, card) -> Tuple[Optional[Dict[str, str]], bool]:
        """馬のカードから販売者情報を抽出する
        
        Args:
            card: 馬のカード要素 (BeautifulSoupオブジェクト)
            
        Returns:
            Tuple[Optional[Dict[str, str]], bool]: (販売者情報を含む辞書, 成功したかどうか)
        """
        try:
            # 販売者情報を含む要素を探す
            # 実際のセレクタはHTMLの構造に合わせて調整が必要
            seller_elem = card.select_one('.seller-info, .owner-info, .trader')
            if not seller_elem:
                return {}, True  # 販売者情報がなくてもエラーとはしない
                
            # 販売者名を抽出
            seller_name = seller_elem.get_text(strip=True)
            if not seller_name:
                return {}, True
                
            # 販売者名をクリーンアップ
            seller_name = self._clean_seller_name(seller_name)
            
            # 販売者URLがあれば取得
            seller_url = None
            seller_link = seller_elem.find('a', href=True)
            if seller_link:
                seller_url = urljoin(self.base_url, seller_link['href'])
            
            # 結果を返す
            result = {
                'seller': seller_name
            }
            
            if seller_url:
                result['seller_url'] = seller_url
                
            return result, True
            
        except Exception as e:
            self.logger.error(f"販売者情報の抽出中にエラーが発生しました: {e}", exc_info=True)
            return None, False
    
    def _clean_seller_name(self, seller: str) -> str:
        """販売者名をクリーンアップする
        
        Args:
            seller: クリーンアップ前の販売者名
            
        Returns:
            str: クリーンアップされた販売者名
        """
        if not seller:
            return ""
            
        try:
            # 不要な空白と改行を削除
            seller = ' '.join(seller.split())
            
            # 不要な接頭辞・接尾辞を削除
            seller = re.sub(r'^[\s\-\*\+=\~_…]+', '', seller)  # 先頭の記号
            seller = re.sub(r'[\s\-\*\+=\~_…]+$', '', seller)  # 末尾の記号
            
            # 括弧内の不要な情報を削除
            seller = re.sub(r'\s*\([^)]*\)', '', seller)
            seller = re.sub(r'\s*\[[^]]*\]', '', seller)
            seller = re.sub(r'\s*\{[^}]*\}', '', seller)
            
            # 連続するスペースを1つに
            seller = ' '.join(seller.split())
            
            return seller.strip()
            
        except Exception as e:
            self.logger.error(f"販売者名のクリーンアップ中にエラーが発生しました: {e}", exc_info=True)
            return seller  # エラーが発生した場合は元の値を返す

    def get_jbis_prize(self, jbis_url: str) -> Optional[float]:
        """JBISのページから総賞金を取得する
        
        Args:
            jbis_url (str): JBISの馬詳細ページURL
            
        Returns:
            Optional[float]: 賞金（万円単位）、取得できない場合はNone
        """
        if not jbis_url or not jbis_url.startswith('http'):
            return None
        
        retries = 3
        for attempt in range(retries):
            try:
                response = self.session.get(jbis_url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')

                # 方法1: dtタグから総賞金を取得（最も確実）
                total_prize_dt = soup.find('dt', string=re.compile(r'^\s*総賞金\s*$'))
                if total_prize_dt:
                    dd = total_prize_dt.find_next_sibling('dd')
                    if dd:
                        prize_text = dd.get_text(strip=True)
                        # 数値を抽出（例: "9077.9万円" -> 9077.9）
                        import re
                        prize_match = re.search(r'([\d,.]+)', prize_text)
                        if prize_match:
                            return float(prize_match.group(1).replace(',', ''))
                
                # 方法2: テーブルから総賞金を取得
                prize_table = soup.find('table', class_='tbl-data-01')
                if prize_table:
                    # テーブルから総賞金を抽出する処理を追加
                    pass
                
                return None
                
            except Exception as e:
                self.logger.warning(f"JBIS賞金取得に失敗しました (試行 {attempt + 1}/{retries}): {e}")
                if attempt == retries - 1:
                    self.logger.error(f"JBIS賞金の取得に失敗しました: {e}", exc_info=True)
                    return None
                time.sleep(1)  # 少し待ってからリトライ
    
    def _extract_price_info(self, element) -> Dict[str, Any]:
        """価格情報を抽出する
        
        Returns:
            Dict[str, Any]: 価格情報を含む辞書
            {
                'starting_price': int,      # スタート価格（円）
                'sold_price': int or None,  # 落札価格（円、主取り時はNone）
                'is_unsold': bool          # 主取りフラグ（入札数0の場合にTrue）
            }
        """
        from .components.price_extractor import PriceExtractor
        
        try:
            # PriceExtractorを使用して価格情報を抽出
            if hasattr(element, 'prettify'):
                html_content = str(element.prettify())
            else:
                html_content = str(element)
                
            price_info = PriceExtractor.extract_price(html_content)
            
            # 古い形式との互換性のため、priceフィールドも設定
            price_info['price'] = price_info['sold_price'] if not price_info.get('is_unsold', False) else None
            
            return price_info
            
        except Exception as e:
            self.logger.error(f"価格情報の抽出中にエラーが発生しました: {e}", exc_info=True)
            return {
                'starting_price': None,
                'sold_price': None,
                'is_unsold': False,
                'price': None  # 互換性のため
            }
    
    def _extract_horse_info(self, horse_element, index: int, total: int) -> Optional[Dict[str, Any]]:
        """馬の基本情報を抽出するメソッド"""
        try:
            horse_info = {}
            
            # 通算成績を抽出
            record_info = self.race_record_extractor.extract(horse_element)
            if record_info:
                horse_info['record'] = record_info.get('record', '')
            
            # 価格情報を初期化（詳細ページから取得するため、ここではデフォルト値）
            horse_info.update({
                'starting_price': None,
                'sold_price': None,
                'is_unsold': False
            })
            
            # 賞金情報を抽出
            prize_info = self.prize_extractor.extract(horse_element)
            if prize_info and 'prize_money' in prize_info:
                horse_info['prize_money'] = prize_info['prize_money']
            
            # 画像URLを抽出
            img_elem = horse_element.select_one('img[src*="/horse/"]')
            if img_elem and 'src' in img_elem.attrs:
                horse_info['image_url'] = urljoin(self.base_url, img_elem['src'])
            
            # 詳細ページURLを抽出
            detail_link = horse_element.select_one('a[href*="/horse/"]')
            if detail_link and 'href' in detail_link.attrs:
                detail_url = urljoin(self.base_url, detail_link['href'])
                horse_info['auction_url'] = detail_url
                
                # JBIS URLがまだ取得できていない場合は、詳細ページから取得を試みる
                if 'jbis_url' not in horse_info or not horse_info['jbis_url']:
                    jbis_url = self.jbis_link_extractor.extract(horse_element)
                    if jbis_url:
                        horse_info['jbis_url'] = jbis_url
            
            # JBISから賞金情報を取得（フォールバック）
            if 'jbis_url' in horse_info and horse_info['jbis_url'] and 'prize_money' not in horse_info:
                prize_money = self.get_jbis_prize(horse_info['jbis_url'])
                if prize_money is not None:
                    horse_info['prize_money'] = prize_money
            
            # コメントを抽出
            comment_info = self.comment_extractor.extract(horse_element)
            if comment_info and 'comment' in comment_info:
                horse_info['comment'] = comment_info['comment']
                horse_info['disease_tags'] = self._extract_disease_tags(comment_info['comment'])
            
            # 落札価格を抽出
            price_info = self.price_extractor.extract(horse_element)
            if price_info and 'sold_price' in price_info:
                horse_info['sold_price'] = price_info['sold_price']
            
            # オークション日付を抽出（例として実装）
            # 実際の実装では、適切なセレクタを使用して日付を抽出してください
            # date_elem = horse_element.select_one('.auction-date')
            # if date_elem:
            #     horse_info['auction_date'] = date_elem.get_text(strip=True)
            
            # 販売者情報を抽出
            seller_info, _ = self._extract_seller_info(horse_element)
            if seller_info and 'seller' in seller_info:
                horse_info['seller'] = seller_info['seller']
            
            return horse_info
            
        except Exception as e:
            self.logger.error(f"馬情報の抽出中にエラーが発生しました: {e}", exc_info=True)
            return None

    def scrape_horses(self) -> List[Dict[str, Any]]:
        """馬の一覧をスクレイピングする
        
        Returns:
            List[Dict[str, Any]]: 馬の情報のリスト
        """
        self.logger.info("馬の一覧をスクレイピングを開始します")
        
        # 馬の一覧を取得
        horses = self.scrape_horse_list()
        
        if not horses:
            self.logger.warning("馬の一覧を取得できませんでした")
            return []
            
        self.logger.info(f"{len(horses)}頭の馬の情報を取得しました")
        
        # 結果をJSONファイルに保存（フロントエンド連携のためhorses_history.jsonで保存）
        output_file = self.output_dir / 'horses_history.json'
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(horses, f, ensure_ascii=False, indent=2)
            self.logger.info(f"{len(horses)}頭の馬の情報を {output_file} に保存しました")
        except Exception as e:
            self.logger.error(f"ファイルの保存中にエラーが発生しました: {e}", exc_info=True)
        
        return horses

            
    def _setup_logging(self):
        """ロギングの設定を行う"""
        # ログレベルの設定
        log_level = logging.DEBUG if isinstance(self.config, TestConfig) else logging.INFO
        
        # ルートロガーを取得
        logger = logging.getLogger()
        
        # ルートロガーの設定
        logger.setLevel(log_level)
        
        # コンソールハンドラの設定
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # フォーマッタの設定
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        # 既存のハンドラをクリアして新しいハンドラを追加
        logger.handlers = [console_handler]
        
        # デバッグログ用のファイルハンドラを設定
        try:
            log_dir = Path('debug_logs')
            log_dir.mkdir(exist_ok=True, mode=0o755)
            log_file = log_dir / f'scraper_debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            logger.debug(f"デバッグログを {log_file.absolute()} に出力します")
            
        except Exception as e:
            logger.warning(f"デバッグログファイルの作成に失敗しました: {e}")
        
        # 他モジュールのログレベルを設定
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('selenium').setLevel(logging.WARNING)
        logging.getLogger('bs4').setLevel(logging.WARNING)
        
        # テストモードの場合は追加のログを出力
        if isinstance(self.config, TestConfig):
            logger.info("テストモードで初期化しました")
            logger.info(f"キャッシュディレクトリ: {self.cache_dir.absolute()}")
            logger.info(f"並列処理: {self.max_workers} ワーカー")

    def analyze_failed_horses(self):
        """失敗した馬の情報を分析する
        
        Returns:
            Dict: 分析結果の辞書
        """
        analysis = {
            'total_failed': len(self.failed_horses),
            'reasons': {},
            'suggestions': []
        }
        
        if not self.failed_horses:
            analysis['message'] = "失敗した馬はありません"
            return analysis
            
        # エラーの種類ごとにカウント
        for horse in self.failed_horses:
            error_type = horse.get('error_type', 'unknown')
            analysis['reasons'][error_type] = analysis['reasons'].get(error_type, 0) + 1
            
        # 提案を追加
        if 'connection_error' in analysis['reasons']:
            analysis['suggestions'].append(
                "接続エラーが発生しています。ネットワーク接続を確認してください。"
            )
            
        if 'timeout' in analysis['reasons']:
            analysis['suggestions'].append(
                "タイムアウトが発生しています。リトライ間隔を長くするか、タイムアウト時間を延長してください。"
            )
            
        if 'parse_error' in analysis['reasons']:
            analysis['suggestions'].append(
                "HTMLのパースエラーが発生しています。ウェブサイトの構造が変更された可能性があります。"
            )
            
        return analysis

    def analyze_logs(self):
        """ログファイルを分析して失敗した馬の情報を取得する
        
        Returns:
            List[Dict]: 失敗した馬の情報のリスト
        """
        try:
            log_dir = Path('logs')
            if not log_dir.exists():
                logger.warning("ログディレクトリが見つかりません")
                return []
            
            log_files = sorted(log_dir.glob('scraper_*.log'), reverse=True)
            if not log_files:
                logger.warning("ログファイルが見つかりません")
                return []
            
            latest_log = log_files[0]
            logger.info(f"最新のログファイルを分析中: {latest_log.name}")
            
            failed_horses = []
            current_horse = {}
            
            with open(latest_log, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'Failed to process horse' in line:
                        if current_horse:
                            failed_horses.append(current_horse)
                            current_horse = {}
                        # 馬名を抽出
                        match = re.search(r'Failed to process horse: (.+?)(?: - |$)', line)
            
            # 最後の馬を追加
            if current_horse:
                failed_horses.append(current_horse)
                
            return failed_horses
            
        except Exception as e:
            logger.error(f"ログファイルの分析中にエラーが発生しました: {e}")
            logger.debug(traceback.format_exc())
            return []


def main():
    """メインの実行関数"""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='楽天競馬オークションのスクレイピングを実行します')
    parser.add_argument('--test', action='store_true', help='テストモードで実行')
    parser.add_argument('--workers', type=int, default=5, help='並列処理のワーカー数')
    parser.add_argument('--no-cache', action='store_false', dest='use_cache', 
                       help='キャッシュを使用しない（デフォルト: 有効）')
    parser.add_argument('--cache-dir', default='cache', help='キャッシュディレクトリのパス')
    args = parser.parse_args()

    try:
        # 設定の初期化（キャッシュをデフォルトで有効化）
        config = ScraperConfig(
            max_workers=args.workers,
            use_cache=args.use_cache,
            cache_dir=args.cache_dir
        )
        
        # スクレイパーの初期化
        if args.test:
            scraper = ImprovedRakutenScraper(TestConfig(use_cache=args.use_cache, cache_dir=args.cache_dir))
        else:
            scraper = ImprovedRakutenScraper(config)

        # 馬の一覧をスクレイピング
        logger.info("馬の一覧をスクレイピングを開始します")
        horses = scraper.scrape_horses()
        
        if not horses:
            logger.warning("馬の一覧を取得できませんでした")
            return
            
        logger.info(f"{len(horses)}頭の馬の情報を取得しました")
        
        # 馬の情報を保存
        saved_count = 0
        for horse in horses:
            try:
                horse_id = save_horse(horse)
                if horse_id:
                    saved_count += 1
                    logger.debug(f"馬情報を保存しました: {horse.get('name')} (ID: {horse_id})")
                else:
                    logger.warning(f"馬情報の保存に失敗しました: {horse.get('name')}")
            except Exception as e:
                logger.error(f"馬情報の保存中にエラーが発生しました: {horse.get('name')} - {str(e)}")
        
        logger.info(f"{saved_count}頭の馬情報を保存しました")
        
        # 失敗した馬がいる場合は分析
        if scraper.failed_horses:
            logger.warning(f"{len(scraper.failed_horses)}頭の馬の処理に失敗しました")
            analysis = scraper.analyze_failed_horses()
            logger.warning(f"失敗の内訳: {analysis['reasons']}")
            
            if analysis['suggestions']:
                logger.info("\n改善のための提案:")
                for suggestion in analysis['suggestions']:
                    logger.info(f"- {suggestion}")
        
    except KeyboardInterrupt:
        logger.info("\nユーザーによって中断されました")
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {e}")
        logger.debug(traceback.format_exc())


class RakutenAuctionScraper(ImprovedRakutenScraper):
    """
    後方互換性のためのラッパークラス。
    improved_scraper.py の ImprovedRakutenScraper を RakutenAuctionScraper として利用可能にします。
    """
    def __init__(self, data_dir: str = 'static-frontend/public/data'):
        # 親クラスの初期化
        config = ScraperConfig()
        super().__init__(config)
        
        # データディレクトリの設定
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 互換性のための設定
        self.base_url = "https://auction.keiba.rakuten.co.jp/"
        
    def scrape_all_horses(self, auction_date: str = None) -> List[Dict]:
        """
        互換性のためのメソッド。
        ImprovedRakutenScraper の scrape_horses メソッドを呼び出します。
        """
        return self.scrape_horses()
        
    # 必要に応じて他の互換性メソッドを追加


if __name__ == "__main__":
    import sys
    sys.exit(main())
