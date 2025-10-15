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

# カスタムコンポーネントのインポート
from components.horse_basic_info_extractor import HorseBasicInfoExtractor
from components.jbis_link_extractor import JbisLinkExtractor
from components.pedigree_extractor import PedigreeExtractor
from components.comment_extractor import CommentExtractor
from components.prize_money import CurrentPrizeExtractor, AuctionPrizeExtractor
from components.price_extractor import PriceExtractor
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.scrapers.data_helpers import save_horse, save_auction_history

# サードパーティのライブラリ
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util.retry import Retry

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraper.log')
    ]
)
logger = logging.getLogger(__name__)

# 定数
BASE_URL = "https://auction.keiba.rakuten.co.jp/"
CACHE_DIR = "html_cache"
OUTPUT_DIR = "data"
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
BACKOFF_FACTOR = 1
MAX_WORKERS = 4

# 健康関連のキーワード
HEALTH_KEYWORDS = [
    '手術歴', '骨折', '皮膚病', '屈腱炎', '腫れ', '咽頭虚脱', '脱臼', '跛行', '打撲'
]

class CacheManager:
    """HTMLキャッシュを管理するクラス"""
    
    def __init__(self, base_dir: str = CACHE_DIR):
        """キャッシュマネージャーの初期化"""
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_cache_dir = self.base_dir / self.session_id
        self.current_cache_dir.mkdir(exist_ok=True)
        (self.current_cache_dir / "details").mkdir(exist_ok=True)
        
    def get_cache_path(self, url: str, is_detail: bool = False) -> Path:
        """URLに対応するキャッシュファイルのパスを取得"""
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        if is_detail:
            return self.current_cache_dir / "details" / f"{url_hash}.html"
        return self.current_cache_dir / f"{url_hash}.html"
    
    def save_html(self, url: str, content: str, is_detail: bool = False) -> Path:
        """HTMLをキャッシュに保存"""
        cache_path = self.get_cache_path(url, is_detail)
        cache_path.write_text(content, encoding='utf-8')
        return cache_path
    
    def load_html(self, url: str, is_detail: bool = False) -> Optional[str]:
        """キャッシュからHTMLを読み込み"""
        cache_path = self.get_cache_path(url, is_detail)
        if cache_path.exists():
            return cache_path.read_text(encoding='utf-8')
        return None

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
        self.config = config
        self.max_workers = config.max_workers
        self.use_cache = config.use_cache
        self.cache_dir = config.cache_dir
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        # HTTPセッションの設定
        self.session = self._create_session(
            timeout=config.timeout,
            max_retries=config.max_retries,
            backoff_factor=config.backoff_factor
        )
        
        self.base_url = BASE_URL
        
        # キャッシュマネージャーの初期化
        self.cache_manager = CacheManager(self.cache_dir) if self.use_cache else None
        
        # 失敗した馬を追跡するリスト
        self.failed_horses = []
        
        # ロガーの設定
        self._setup_logging()
        
        # 出力ディレクトリの作成
        self.output_dir = Path(OUTPUT_DIR)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # セッションIDの生成
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

    def _create_session(self, timeout, max_retries, backoff_factor):
        """HTTPセッションを作成する
        
        Args:
            timeout: リクエストのタイムアウト（秒）
            max_retries: 最大リトライ回数
            backoff_factor: リトライ間の待機時間の係数
            
        Returns:
            requests.Session: 設定済みのセッションオブジェクト
        """
        session = requests.Session()
        
        # リトライ戦略の設定
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            respect_retry_after_header=True
        )
        
        logger.debug(f"セッション設定: {max_retries}回リトライ、バックオフ係数{backoff_factor}, タイムアウト{timeout}秒")
        
        # アダプタの設定
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )
        
        # プロトコルに応じてアダプタをマウント
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # デスクトップ向けのユーザーエージェントを設定
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br'
        })
        
        # セッションのタイムアウト設定
        session.request = functools.partial(session.request, timeout=timeout)
        
        return session
        
    def scrape_horse_list(self, url: str = None, use_cache: bool = False) -> List[Dict[str, Any]]:
        """馬の一覧をスクレイピングする
        
        Args:
            url: スクレイピング対象のURL（Noneの場合はベースURLを使用）
            use_cache: キャッシュを使用するかどうか
            
        Returns:
            List[Dict[str, Any]]: 馬の情報のリスト
        """
        try:
            if url is None:
                url = self.base_url

            html_content = None
            if use_cache and hasattr(self, 'cache_manager'):
                html_content = self.cache_manager.load_html(url)

            if not html_content:
                try:
                    response = self.session.get(url, timeout=self.timeout)
                    response.raise_for_status()
                    html_content = response.text
                        
                    # キャッシュに保存
                    if hasattr(self, 'cache_manager') and use_cache:
                        self.cache_manager.save_html(url, html_content)
                except requests.exceptions.RequestException as e:
                    logger.error(f"リクエストに失敗しました: {e}")
                    return []
                        
            # HTMLをパース
            soup = BeautifulSoup(html_content, 'html.parser')
                
            # 馬の行を取得
            horse_rows = []
            # 馬のカードを取得
            horse_cards = soup.select('.auctionTableCard')
            total_horses = len(horse_cards)
            
            if not horse_cards:
                # デバッグ用HTML保存処理
                debug_html = "debug_horse_list.html"
                with open(debug_html, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.warning(f"馬のカードが見つかりませんでした。デバッグ用にHTMLを保存しました: {debug_html}")
                return []
                
            logger.info(f"{total_horses}頭の馬を検出しました")

            # 馬の情報を抽出
            horses = []
            failed_count = 0
            
            for i, card in enumerate(horse_cards, 1):
                try:
                    horse_info = self._extract_horse_info(card, i, total_horses)
                    if horse_info:
                        # 詳細ページへのURLを設定
                        detail_link = card.select_one('a[href*="detail"]')
                        if detail_link:
                            horse_info['detail_url'] = urljoin(self.base_url, detail_link.get('href', '').strip())
                        horses.append(horse_info)
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"[{i}/{total_horses}] 馬情報の抽出中にエラーが発生しました: {e}", exc_info=True)
                    failed_count += 1
                            
            # 成功・失敗の集計
            success_count = len(horses)
            
            logger.info("\n=== スクレイピング結果 ===")
            logger.info(f"総数: {total_horses}頭")
            logger.info(f"成功: {success_count}頭")
            logger.info(f"失敗: {failed_count}頭")
            
            if failed_count > 0:
                logger.warning(f"{failed_count}頭の馬情報の抽出に失敗しました")
            
            return horses
                
        except Exception as e:
            logger.error(f"馬の一覧のスクレイピング中にエラーが発生しました: {e}", exc_info=True)
            if self.test_mode:
                raise  # テストモードの場合は例外を再スロー
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
        """馬名をクリーンアップする"""
        # テキストノードを直接取得して、不要な子要素のテキストを除外
        text_nodes = [text for text in name_elem.find_all(text=True, recursive=True) 
                     if text.parent.name not in ['script', 'style']]
        
        # 1. まず、要素内のすべてのテキストを取得
        name = name_elem.get_text(' ', strip=True)
        
        # 2. テキストノードから直接名前を抽出
        if text_nodes:
            first_text = text_nodes[0].strip()
            if len(first_text) > 2 and (not name or len(first_text) < len(name)):
                name = first_text
        
        # 3. タイトル属性を確認
        title = name_elem.get('title', '').strip()
        if not title and name_elem.get('data-original-title'):
            title = name_elem.get('data-original-title', '').strip()
        
        # 4. タイトル属性からも名前を抽出
        if title and (not name or len(title) > len(name)):
            name = title
        
        # 5. 親要素のテキストを確認
        if name_elem.parent:
            parent_text = name_elem.parent.get_text(' ', strip=True)
            if (parent_text and len(parent_text) > len(name) and 
                len(re.findall(r'[0-9]', parent_text)) < 3):
                name = parent_text
        
        # 6. 馬名のクリーンアップ
        # 改行やタブをスペースに置換
        name = re.sub(r'[\n\r\t]+', ' ', name)
        
        # 7. 最初の馬名部分を抽出
        name_match = re.search(r'^([^\s\(\[\{\n\r\t]+(?:\s+[^\s\(\[\{\n\r\t]+)*)', name)
        if name_match:
            name = name_match.group(1).strip()
        
        # 8. 不要な接尾辞を削除
        name = re.sub(r'\s*[\[\]\(\)\{\}]\s*', ' ', name)  # 括弧類を削除
        name = re.sub(r'\s+', ' ', name).strip()  # 連続するスペースを1つに
        
        # 9. 不要な接頭辞・接尾辞を削除
        name = re.sub(r'^[\s\-\*\+\=\~_…]+', '', name)  # 先頭の記号
        name = re.sub(r'[\-\*\+\=\~_…]+$', '', name)  # 末尾の記号
        
        return name

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
            card: BeautifulSoupのカード要素
            
        Returns:
            Tuple[Optional[Dict[str, str]], bool]: 
                - 抽出した販売者情報の辞書（失敗時はNone）
                - 成功可否（True: 成功, False: 失敗）
        """
        try:
            # 販売者情報を取得
            seller_elem = card.select_one('.auctionTableCard__farm, .seller-info, [data-testid="seller"]')
            if not seller_elem:
                return None, False
                
            # 販売者名を取得
            seller = seller_elem.get_text(strip=True)
            
            # 不要なテキストを削除
            seller = self._clean_seller_name(seller)
            
            return {
                'seller': seller
            }, True
            
        except Exception as e:
            logger.error(f"販売者情報の抽出中にエラーが発生しました: {e}", exc_info=True)
            return None, False
    
    def _clean_seller_name(self, seller: str) -> str:
        """販売者名をクリーンアップする"""
        if not seller:
            return ""
        
        # 不要なテキストを削除
        seller = re.sub(r'\s*[\[\]\(\)\{\}]\s*', ' ', seller)  # 括弧類を削除
        seller = re.sub(r'\s+', ' ', seller).strip()  # 連続するスペースを1つに
        
        # 不要な接頭辞・接尾辞を削除
        seller = re.sub(r'^[\s\-\*\+\=\~_…]+', '', seller)  # 先頭の記号
        seller = re.sub(r'[\-\*\+\=\~_…]+$', '', seller)  # 末尾の記号
        
        return seller

    def _extract_horse_info(self, card, index: int, total: int) -> Optional[Dict[str, Any]]:
        """馬のカードから情報を抽出する
        
        Args:
            card: BeautifulSoupのカード要素
            index: 現在の馬のインデックス
            total: 総馬数
            
        Returns:
            Optional[Dict[str, Any]]: 抽出した馬の情報、抽出に失敗した場合はNone
        """
        try:
            # 基本情報を抽出
            basic_info, success = self._extract_name_sex_age(card)
            if not success:
                logger.warning(f"[WARNING] Could not extract basic info for horse {index+1}/{total}")
                return None
                
            name = basic_info['name']
            sex = basic_info['sex']
            age = basic_info['age']
            
            logger.debug(f"[DEBUG] Extracted basic info - Name: '{name}', Sex: '{sex}', Age: '{age}'")
            
            # 馬名要素を取得（詳細ページURLの取得に使用）
            name_elem = card.select_one('.auctionTableCard__name, .horse-name, [data-testid="horse-name"]')
            detail_url = name_elem.get('href', '') if name_elem else ''
            
            # 販売者情報を抽出
            seller_info, seller_success = self._extract_seller_info(card)
            seller = seller_info['seller'] if seller_success else ''
            
            # 前後の空白を削除
            seller = seller.strip()
            
            # 販売者名が短すぎる場合は無視
            if len(seller) <= 1:
                seller = ""
            else:
                # 販売者名が長すぎる場合は最初の15文字までに制限（「...」を追加）
                if len(seller) > 15:
                    seller = seller[:15].strip() + "..."
            
            logger.debug(f"[DEBUG] Extracted seller: '{seller}'")
            
            # 生年月日を取得
            birthday_elem = card.select_one('.auctionTableCard__birthday .value')
            birthday = birthday_elem.get_text(strip=True) if birthday_elem else ''
            
            # 詳細ページのURLを取得
            # 価格情報を抽出
            price_elem = row.find('td', class_='price')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'(\d+)', price_text)
                if price_match:
                    horse_info['sold_price'] = int(price_match.group(1))
                else:
                    horse_info['sold_price'] = None
            else:
                horse_info['sold_price'] = None
            horse_info['is_unsold'] = False
            # 馬の基本情報を辞書に格納
            horse_info = {
                'name': name,
                'sex': sex,
                'age': int(age) if age and age.isdigit() else None,
                'seller': seller,
                'birthday': birthday,
                'detail_url': urljoin(self.base_url, detail_url) if detail_url else '',
                'scraped_at': datetime.now().isoformat(),
                'auction_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            logger.debug(f"[{index}/{total}] 馬情報を抽出: {horse_info['name']} (性別: {horse_info['sex']}, 年齢: {horse_info['age']})")
            return horse_info
            
        except Exception as e:
            logger.error(f"馬情報の抽出中にエラーが発生しました: {e}", exc_info=True)
            return None

    def _extract_price(self, row: BeautifulSoup) -> Dict[str, Any]:
        """行から価格情報を抽出する
        
        Args:
            row: 抽出対象の行要素
            
        Returns:
            抽出した価格情報を含む辞書:
            {
                'sold_price': float or None,  # 落札価格（万円）
                'is_unsold': bool            # 主取りフラグ
            }
        """
        price_elem = row.find('td', class_='price')
        if not price_elem:
            return {'sold_price': None, 'is_unsold': False}
            
        # PriceExtractorを使用して価格情報を抽出
        return PriceExtractor.extract_price(str(price_elem))

    def scrape_horses(self) -> List[Dict[str, Any]]:
        """馬の一覧をスクレイピングする
        
        Returns:
            List[Dict[str, Any]]: 馬の情報のリスト
        """
        logger.info("馬の一覧をスクレイピングを開始します")
        
        # 馬の一覧を取得
        horses = self.scrape_horse_list()
        
        if not horses:
            logger.warning("馬の一覧を取得できませんでした")
            return []
            
        logger.info(f"{len(horses)}頭の馬の情報を取得しました")
        
        # 結果をJSONファイルに保存（フロントエンド連携のためhorses_history.jsonで保存）
        output_file = self.output_dir / 'horses_history.json'
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(horses, f, ensure_ascii=False, indent=2)
            logger.info(f"{len(horses)}頭の馬の情報を {output_file} に保存しました")
        except Exception as e:
            logger.error(f"ファイルの保存中にエラーが発生しました: {e}", exc_info=True)
        
        return horses

    def scrape_horse_detail(self, url: str) -> Dict[str, Any]:
        """馬の詳細ページから情報をスクレイピングする
        
        Args:
            url: 詳細ページのURL
            
        Returns:
            Dict[str, Any]: 抽出した馬の詳細情報
        """
        if not url:
            logger.warning("URLが指定されていません")
            return {}
        
        detail_info = {}
        soup = None
        current_horse = ""
        
        try:
            # キャッシュから読み込みを試みる
            if self.use_cache and self.cache_manager:
                cached_html = self.cache_manager.load_html(url, is_detail=True)
                if cached_html:
                    soup = BeautifulSoup(cached_html, 'html.parser')
            
            # キャッシュになければリクエストを実行
            if not soup:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # キャッシュに保存
                if self.use_cache and self.cache_manager:
                    self.cache_manager.save_html(url, response.text, is_detail=True)
            
            # 馬の基本情報を抽出
            basic_info = HorseBasicInfoExtractor.extract(soup)
            detail_info.update(basic_info)
            current_horse = basic_info.get('name', '')
            
            # 血統情報を抽出
            if current_horse:  # 馬名が取得できている場合のみ血統情報を抽出
                pedigree_info = PedigreeExtractor.extract(soup)
                detail_info.update(pedigree_info)
                
                # JBISリンクを抽出
                jbis_info = JbisLinkExtractor.extract(soup, self.base_url)
                detail_info.update(jbis_info)
            
            # デバッグ用のターゲット馬リスト
            target_horses = ["テスト馬", "デバッグ"]  # デバッグ対象の馬名をここに追加
            
            # デバッグ情報を出力
            print(f"\n[DEBUG] 現在処理中の馬: {current_horse}", file=sys.stderr)
            print(f"[DEBUG] 抽出した血統情報 - sire: {detail_info.get('sire', 'N/A')}, dam: {detail_info.get('dam', 'N/A')}, damsire: {detail_info.get('damsire', 'N/A')}", file=sys.stderr)
            
            # デバッグ対象の馬かどうかチェック
            is_target_horse = any(horse in current_horse for horse in target_horses)
            missing_pedigree = not all(detail_info.get(field) for field in ['sire', 'dam', 'damsire'])
            
            # デバッグファイルを作成する条件:
            # 1. 対象馬であるか、または血統情報が欠落している場合
            # 2. 現在処理中の馬が空でない場合
            if (is_target_horse or missing_pedigree) and current_horse:
                print("[DEBUG] デバッグファイルを作成します...", file=sys.stderr)
                print(f"[DEBUG] 現在の作業ディレクトリ: {os.getcwd()}", file=sys.stderr)
                print(f"[DEBUG] スクリプトの場所: {os.path.abspath(__file__)}", file=sys.stderr)
                
                # エラー情報を取得
                import traceback
                error_info = traceback.format_exc()
                
                # デバッグ情報を保存
                self._save_debug_info(current_horse, url, str(soup) if soup else "No HTML content", error_info)
            
            return detail_info
                
        except Exception as e:
            error_message = f"馬の詳細情報のスクレイピング中に予期せぬエラーが発生しました: {url} - {str(e)}"
            logger.error(error_message, exc_info=True)
            print(f"[DEBUG] エラー発生: {error_message}", file=sys.stderr)
            
            # エラーが発生してもデバッグ情報を保存
            if not current_horse:
                current_horse = f"error_{int(time.time())}"
                
            self._save_debug_info(current_horse, url, str(soup) if soup else "No HTML content", str(e))
            return None
            
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
                        if match:
                            current_horse['name'] = match.group(1).strip()
                    elif 'Error:' in line and current_horse:
                        current_horse['error'] = line.split('Error:')[-1].strip()
            
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
    parser = argparse.ArgumentParser(description='楽天競馬オークションのスクレイピングを実行します')
    parser.add_argument('--test', action='store_true', help='テストモードで実行')
    parser.add_argument('--workers', type=int, default=5, help='並列処理のワーカー数')
    parser.add_argument('--use-cache', action='store_true', help='キャッシュを使用')
    parser.add_argument('--cache-dir', default='cache', help='キャッシュディレクトリのパス')
    args = parser.parse_args()

    try:
        # スクレイパーの初期化
        scraper = ImprovedRakutenScraper(
            test_mode=args.test,
            max_workers=args.workers,
            use_cache=args.use_cache,
            cache_dir=args.cache_dir
        )

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


if __name__ == "__main__":
    import sys
    sys.exit(main())
