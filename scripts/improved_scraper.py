#!/usr/bin/env python3
"""
楽天競馬オークションのスクレイピングスクリプト

このスクリプトは、楽天競馬オークションのデータをスクレイピングし、構造化されたデータとして保存します。

主な機能:
- オークション一覧ページからの馬情報のスクレイピング
- 個別馬の詳細情報の取得（JBISサイトから）
- 賞金情報の取得と処理
- 取得データのJSON形式での保存
- オフラインでのテストを可能にするキャッシュ機能

データ構造 (horses.json):
{
  "metadata": {
    "last_updated": "YYYY-MM-DDTHH:MM:SS.ssssss",
    "total_horses": 0,
    "version": "1.0.0"
  },
  "horses": [
    {
      "id": "UUID",
      "name": "馬名",
      "age": 年齢,
      "sex": "性別（牡/牝/セ）",
      "sire": "父馬名",
      "dam": "母馬名",
      "damsire": "母父名",
      "total_prize_start": 0.0,
      "total_prize_latest": 0.0,
      "jbis_url": "JBISのURL",
      "auction_url": "オークションページのURL",
      "image_url": "画像URL",
      "disease_tags": ["タグ1", "タグ2"],
      "comment": "コメント",
      "race_record": "戦績",
      "weight": 体重,
      "seller": "出品者",
      "auction_date": "オークション日（YYYY-MM-DD）",
      "created_at": "作成日時（ISOフォーマット）",
      "updated_at": "更新日時（ISOフォーマット）"
    }
  ]
}
"""
import traceback

# スクレイピングルール
# 1. オークション一覧ページから基本情報を取得
#    - 馬名、性別、年齢、JBIS URL、画像URLなど
#    - 一覧ページから取得可能な賞金情報
#
# 2. 詳細ページ（JBIS）から追加情報を取得
#    - 血統情報（父馬、母馬、母父）
#    - 最新の賞金情報
#    - レース戦績
#
# 3. テストモード（test_mode=True）
#    - キャッシュを使用してオフラインでテスト可能
#    - 詳細ページがない馬はスキップ
#    - バリデーションをスキップしてデータを保存
#
# キャッシュの仕組み:
# - 取得したHTMLは'html_cache'ディレクトリに保存
# - ファイル名は'{タイムスタンプ}_{URLのMD5ハッシュ}.html'
# - テスト時はキャッシュがあればそれを使用し、なければスキップ
#
# 実行方法:
# 通常モード（本番用）: python improved_scraper.py
# テストモード（キャッシュ使用）: python improved_scraper.py --test
# キャッシュを強制更新して実行: python improved_scraper.py --force
#

import os
import sys
import requests
from bs4 import BeautifulSoup
import re
import json
import time
import uuid
import logging
import traceback
import functools
import concurrent.futures
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs
import hashlib
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm
from pathlib import Path

# キャッシュ管理用モジュール
from cache_manager import CacheManager

# ロギング設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraper.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# キャッシュディレクトリの設定
CACHE_DIR = Path('html_cache')
CACHE_DIR.mkdir(exist_ok=True)

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# バックエンドのモジュールをインポート
from backend.scrapers.data_helpers import (
    save_horse,
    save_auction_history,
    load_json_file
)

class ImprovedRakutenScraper:
    def __init__(self, timeout=30, max_retries=3, backoff_factor=1, test_mode=False, cache_file=None, cache_dir="cache"):
        """楽天競馬オークションスクレイパーの初期化

        Args:
            timeout: リクエストのタイムアウト時間（秒）
            max_retries: 最大リトライ回数
            backoff_factor: リトライ間の待機時間の係数
            test_mode: テストモードかどうか
            cache_file: テスト用キャッシュファイルのパス
            cache_dir: キャッシュを保存するディレクトリ
        """
        self.base_url = "https://auction.keiba.rakuten.co.jp/"
        list_url = "https://auction.keiba.rakuten.co.jp/"
        self.timeout = timeout
        self.test_mode = test_mode  # テストモードフラグを追加
        self.cache_file = cache_file  # テスト用キャッシュファイルのパス（レガシー）
        self.cache_dir = cache_dir    # キャッシュディレクトリを保存

        # キャッシュディレクトリが存在しない場合は作成
        if self.cache_dir and not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
            logger.info(f"キャッシュディレクトリを作成しました: {self.cache_dir}")

        # キャッシュマネージャーの初期化
        self.cache_manager = CacheManager(base_dir=cache_dir)
        self.current_session_id = None

        # セッションの初期化
        self.session = requests.Session()

        # テストモードに応じたリトライ設定
        if test_mode:
            # テストモードの場合はリトライを無効化
            retry_strategy = Retry(total=0)
            # テストモードではデフォルトのログレベルをINFOに設定
            logging.getLogger().setLevel(logging.INFO)
            logger.info("テストモードで初期化: リトライ無効、ログレベルINFOに設定")
        else:
            # 本番モードの場合は指定されたリトライ設定を使用
            retry_strategy = Retry(
                total=max_retries,
                backoff_factor=backoff_factor,
                status_forcelist=[500, 502, 503, 504],
                allowed_methods=["GET", "POST"]
            )

        # アダプタの設定
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,  # コネクションプールのサイズを最適化
            pool_maxsize=10
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # セッションのタイムアウト設定
        self.session.request = functools.partial(
            self.session.request,
            timeout=timeout if not test_mode else 5  # テストモードではタイムアウトを短縮
        )

        # ヘッダー設定 - より自然なブラウザリクエストを模倣
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="125"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }

    def _save_html_to_cache(self, url: str, content: str) -> Path:
        """HTMLをキャッシュに保存する（CacheManagerを使用）

        Args:
            url: キャッシュするURL
            content: 保存するHTMLコンテンツ

        Returns:
            Path: 保存されたキャッシュファイルのパス
        """
        try:
            # 一覧ページの場合はlist.htmlとして保存
            if "list.cgi" in url or "list/" in url:
                # 相対パスに変換するため、詳細ページへのリンクを更新
                soup = BeautifulSoup(content, 'html.parser')
                for a in soup.find_all('a', href=True):
                    if '/item/' in a['href']:
                        item_id = a['href'].split('/')[-1]
                        a['href'] = f'details/{item_id}.html'
                content = str(soup)
                self.cache_manager.save_list_page(content)
                return Path(self.cache_manager.current_session) / "list.html"

            # 詳細ページの場合はIDを抽出して保存
            if "/item/" in url:
                # URLからアイテムIDを抽出 (例: /item/14687 -> 14687)
                item_id = url.rstrip('/').split('/')[-1]
                if item_id.isdigit():
                    return Path(self.cache_manager.save_detail_page(content, "", item_id))

            # その他のURLは従来の方法で保存
            url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{url_hash}.html"
            filepath = CACHE_DIR / filename

            # ファイルに保存
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.debug(f"HTMLをキャッシュに保存しました: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"キャッシュの保存中にエラーが発生しました: {str(e)}")
            raise

    def _get_cache_key(self, url: str) -> str:
        """URLからキャッシュキーを生成する。"""
        import hashlib
        import re

        # URLを安全なファイル名に変換
        clean_url = re.sub(r'[^a-zA-Z0-9]', '_', url)
        # ハッシュを追加して一意性を確保
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:8]
        return f"{clean_url[:50]}_{url_hash}"

    def _load_test_cache(self, url: str) -> Optional[str]:
        """テスト用キャッシュからHTMLを読み込む。

        Args:
            url: 読み込むキャッシュのURL

        Returns:
            キャッシュされたHTMLコンテンツ、または見つからない場合はNone
        """
        if not self.test_mode:
            logger.debug("テストモードではないため、キャッシュを読み込みません")
            return None

        # キャッシュファイルが直接指定されている場合
        if self.cache_file and os.path.isfile(self.cache_file):
            logger.info(f"指定されたキャッシュファイルを読み込みます: {self.cache_file}")
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    logger.info(f"キャッシュファイルから {len(content)} バイトを読み込みました")
                    return content
            except Exception as e:
                logger.error(f"キャッシュファイルの読み込み中にエラーが発生しました: {e}")
                return None

        # 通常のキャッシュディレクトリからの読み込み
        if not self.cache_dir:
            logger.debug("キャッシュディレクトリが設定されていません")
            return None

        # キャッシュキーを生成
        cache_key = self._get_cache_key(url)
        logger.debug(f"キャッシュ検索 - URL: {url}")
        logger.debug(f"生成されたキャッシュキー: {cache_key}")

        try:
            # キャッシュディレクトリの絶対パスを取得
            cache_dir = os.path.abspath(self.cache_dir)
            logger.debug(f"キャッシュディレクトリ (絶対パス): {cache_dir}")

            # キャッシュディレクトリの存在確認
            if not os.path.exists(cache_dir):
                logger.error(f"キャッシュディレクトリが存在しません: {cache_dir}")
                return None

            # キャッシュディレクトリの内容を取得（存在確認付き）
            try:
                cache_files = os.listdir(cache_dir)
                logger.debug(f"キャッシュディレクトリの内容 ({cache_dir}): {cache_files}")

                # デバッグ用: 各ファイルのフルパスとサイズをログに出力
                for f in cache_files:
                    try:
                        file_path = os.path.join(cache_dir, f)
                        file_size = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
                        logger.debug(f"  - {f} ({file_size} bytes)")
                    except Exception as e:
                        logger.error(f"ファイル情報の取得に失敗しました {f}: {e}")

            except Exception as e:
                logger.error(f"キャッシュディレクトリの読み込みに失敗しました: {e}", exc_info=True)
                return None

            if not cache_files:
                logger.error("キャッシュディレクトリにファイルがありません")
                return None

            # キャッシュキーのハッシュ部分を取得
            hash_part = cache_key.split('_')[-1]
            logger.debug(f"キャッシュ検索 - ハッシュ部分: {hash_part}")

            # 1. キャッシュキーに完全に一致するファイルを探す（拡張子付き）
            target_file = f"{cache_key}.html"
            if target_file in cache_files:
                cache_file = os.path.join(cache_dir, target_file)
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        logger.info(f"キャッシュファイル {target_file} から {len(content)} バイトを読み込みました")
                        return content
                        logger.info(f"テストモード: 完全一致キャッシュから読み込みました: {target_file}")
                        return content
                except Exception as e:
                    logger.error(f"キャッシュファイルの読み込みに失敗しました {target_file}: {e}")

            # 2. ファイル名にハッシュ部分が含まれるファイルを検索
            matching_files = [f for f in cache_files if f.endswith('.html') and hash_part in f]
            if matching_files:
                for filename in matching_files:
                    cache_file = os.path.join(cache_dir, filename)
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            logger.info(f"テストモード: ハッシュ一致キャッシュから読み込みました: {filename}")
                            return content
                    except Exception as e:
                        logger.error(f"キャッシュファイルの読み込みに失敗しました {filename}: {e}")
                        continue

            # 3. URLのパス部分で検索
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            path = parsed_url.path.strip('/')

            if path:
                path_parts = [p for p in path.split('/') if p]
                logger.debug(f"URLパス部分で検索: {path_parts}")

                # パスの最後の部分（通常はID）を優先的に検索
                if path_parts:
                    last_part = path_parts[-1]
                    matching_files = [f for f in cache_files if f.endswith('.html') and last_part in f]
                    if matching_files:
                        for filename in matching_files:
                            cache_file = os.path.join(cache_dir, filename)
                            try:
                                with open(cache_file, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    logger.info(f"テストモード: パス最終部分一致キャッシュから読み込みました: {filename}")
                                    return content
                            except Exception as e:
                                logger.error(f"キャッシュファイルの読み込みに失敗しました {filename}: {e}")
                                continue

                # パスのいずれかの部分が含まれるファイルを検索
                for part in path_parts:
                    matching_files = [f for f in cache_files if f.endswith('.html') and part in f]
                    if matching_files:
                        for filename in matching_files:
                            cache_file = os.path.join(cache_dir, filename)
                            try:
                                with open(cache_file, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    logger.info(f"テストモード: パス部分一致キャッシュから読み込みました: {filename}")
                                    return content
                            except Exception as e:
                                logger.error(f"キャッシュファイルの読み込みに失敗しました {filename}: {e}")
                                continue

        except Exception as e:
            logger.error(f"キャッシュの検索中にエラーが発生: {e}", exc_info=True)

        logger.warning(f"テストモードでキャッシュが見つかりませんでした: {url}")
        logger.warning(f"検索したキャッシュキー: {cache_key}")
        logger.warning(f"キャッシュディレクトリ: {os.path.abspath(self.cache_dir)}")
        logger.warning(f"ディレクトリの内容: {os.listdir(self.cache_dir) if os.path.exists(self.cache_dir) else 'ディレクトリが存在しません'}")
        return None

    def _save_test_cache(self, url: str, content: str) -> None:
        """テスト用キャッシュにHTMLを保存する。"""
        if not self.test_mode or not hasattr(self, 'cache_dir') or not self.cache_dir:
            return

        os.makedirs(self.cache_dir, exist_ok=True)
        cache_key = self._get_cache_key(url)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.html")

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"テストモード: キャッシュを保存しました: {cache_file}")
        except Exception as e:
            logger.error(f"キャッシュの保存中にエラーが発生: {e}")

    def _make_request(self, url: str, method: str = 'GET',
                     save_html: bool = False, use_cache_on_error: bool = False,
                     is_detail_page: bool = False, horse_name: str = None, horse_id: str = None, **kwargs):
        """HTTPリクエストを送信し、必要に応じてキャッシュを使用する

        Args:
            url: リクエスト先のURL
            method: HTTPメソッド（デフォルト: 'GET'）
            save_html: レスポンスのHTMLをキャッシュに保存するかどうか
            use_cache_on_error: エラー時にキャッシュを使用するかどうか
            is_detail_page: 詳細ページかどうか（キャッシュ保存時に使用）
            horse_name: 馬名（詳細ページのキャッシュ保存時に使用）
            horse_id: 馬ID（詳細ページのキャッシュ保存時に使用）
            **kwargs: requests.request() に渡す追加引数

        Returns:
            Optional[requests.Response]: レスポンスオブジェクト
        """
        # テストモードの場合はキャッシュを優先
        if self.test_mode:
            # まずキャッシュを確認
            cache_content = self._load_test_cache(url)
            if cache_content is not None:
                response = requests.Response()
                response._content = cache_content.encode('utf-8')
                response.status_code = 200
                response.url = url  # 元のURLを保持
                response.encoding = 'utf-8'
                response.headers = {'Content-Type': 'text/html; charset=utf-8'}
                logger.info(f"テストモード: キャッシュから読み込みました: {url}")
                return response
            logger.warning(f"テストモード: キャッシュが見つかりません: {url}")
            logger.warning(f"キャッシュディレクトリ: {self.cache_dir}")
            logger.warning(f"キャッシュキー: {self._get_cache_key(url)}.html")
            return None

        # 本番モード - 常に新しいリクエストを実行
        try:
            logger.info(f"本番モードでリクエストを送信: {url}")
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            response.encoding = 'utf-8'  # 明示的にエンコーディングを指定
            response.raise_for_status()

            # レスポンスをキャッシュに保存（明示的にsave_html=Trueが指定された場合のみ）
            if save_html and response.status_code == 200 and 'text/html' in response.headers.get('content-type', ''):
                content = response.text

                # 一覧ページか詳細ページかで保存方法を分岐
                if 'auction.keiba.rakuten.co.jp' in url and ('list.cgi' in url or 'list/' in url):
                    # 一覧ページの場合
                    try:
                        self.cache_manager.save_list_page(content)
                        logger.debug(f"一覧ページをキャッシュに保存: {url}")
                    except Exception as e:
                        logger.error(f"一覧ページのキャッシュ保存に失敗: {e}")
                elif is_detail_page and horse_id:
                    # 詳細ページの場合 - horse_idを優先
                    try:
                        self.cache_manager.save_detail_page(content, horse_name or "", horse_id)
                        logger.debug(f"詳細ページをキャッシュに保存: {horse_id}")
                    except Exception as e:
                        logger.error(f"詳細ページのキャッシュ保存に失敗: {e}")
                elif "/item/" in url:
                    # URLからアイテムIDを抽出して詳細ページとして保存
                    item_id = url.rstrip('/').split('/')[-1]
                    if item_id.isdigit():
                        try:
                            self.cache_manager.save_detail_page(content, horse_name or "", item_id)
                            logger.debug(f"詳細ページをキャッシュに保存（URL解析）: {item_id}")
                        except Exception as e:
                            logger.error(f"詳細ページのキャッシュ保存に失敗（URL解析）: {e}")
                else:
                    # その他のページはレガシーな方法で保存
                    self._save_html_to_cache(url, content)
                    logger.debug(f"キャッシュを保存しました: {url}")

            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"リクエストエラー ({e.__class__.__name__}): {e}")

            # エラー時にキャッシュがあればそれを使用（明示的に許可されている場合のみ）
            if use_cache_on_error:
                cache_files = list(CACHE_DIR.glob(f'*_{hashlib.md5(url.encode()).hexdigest()}.html'))
                if cache_files:
                    latest_cache = max(cache_files, key=os.path.getmtime)
                    with open(latest_cache, 'r', encoding='utf-8') as f:
                        content = f.read()
                        logger.warning(f"エラーが発生したため、キャッシュから読み込みます: {latest_cache}")
                        response = requests.Response()
                        response._content = content.encode('utf-8')
                        response.status_code = 200
                        response.headers = {'Content-Type': 'text/html; charset=utf-8'}
                        return response
            logger.error(f"リクエストに失敗し、キャッシュからの復旧も無効化されています: {url}")

            logger.error(f"キャッシュも見つかりません: {url}")
            raise

    def get_auction_date(self) -> str:
        # ページから開催日を取得
        response = self._make_request(self.base_url)
        if not response:
            logger.warning("オークション日の取得に失敗しました。現在の日付を使用します。")
            return datetime.now().strftime("%Y-%m-%d")

        try:
            soup = BeautifulSoup(response.content, 'html.parser')

            # 開催日を探す（例: "2023年11月15日(水)"）
            date_pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日(?:\([月火水木金土日]\))?'
            date_match = re.search(date_pattern, soup.get_text())

            if date_match:
                # マッチした部分から年月日を抽出
                year = int(date_match.group(1))
                month = int(date_match.group(2))
                day = int(date_match.group(3))

                # 日付オブジェクトを作成してフォーマット
                date_obj = datetime(year, month, day)
                return date_obj.strftime('%Y-%m-%d')
        except Exception as e:
            logger.error(f"オークション日の解析中にエラーが発生しました: {str(e)}")

        # 日付が見つからないかエラーが発生した場合は現在の日付を使用
        return datetime.now().strftime('%Y-%m-%d')

    def _extract_prize_from_text(self, text: str) -> float:
        # テキストから賞金を抽出するヘルパーメソッド
        # Args:
        #   text: 抽出元のテキスト
        # Returns:
        #   float: 抽出した賞金（万円単位）。見つからない場合は0.0
        if not text:
            return 0.0

        # パターン1: 「447.2万円」形式
        match = re.search(r'([\d,.]+)\s*万円', text)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except (ValueError, AttributeError):
                pass

        # パターン2: 「総賞金 447.2万円」形式
        match = re.search(r'総賞金\s*([\d,.]+)\s*万円', text)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except (ValueError, AttributeError):
                pass

        return 0.0

    def scrape_horse_list(self, use_cache: bool = False) -> List[Dict[str, Any]]:
        """
        馬の一覧ページから馬の基本情報をスクレイピングします。

        Args:
            use_cache: キャッシュを使用するかどうか（デフォルト: False）
                      テスト時や開発時のみ明示的にTrueを指定してください

        Returns:
            List[Dict[str, Any]]: 馬の基本情報のリスト
        """
        logger.info(f"馬の一覧ページのスクレイピングを開始します (use_cache={use_cache}, test_mode={getattr(self, 'test_mode', False)})")

        try:
            # 一覧ページのURL
            list_url = f"{self.base_url}"
            logger.debug(f"一覧ページURL: {list_url}")

            # キャッシュの初期化
            soup = None
            is_from_cache = False

            # キャッシュから取得を試みる
            if use_cache:
                try:
                    cached_list = self.cache_manager.get_list_page(self.current_session_id)
                    if cached_list:
                        logger.info("キャッシュから一覧ページを読み込みました")
                        soup = BeautifulSoup(cached_list, 'html.parser')
                        is_from_cache = True
                except Exception as e:
                    logger.error(f"キャッシュの取得中にエラーが発生しました: {e}", exc_info=True)
                    if self.test_mode:
                        return []

            # キャッシュが無効またはキャッシュがない場合はリクエストを実行
            if not is_from_cache:
                if self.test_mode and use_cache:
                    logger.warning("テストモードでキャッシュが見つかりませんでした")
                    return []

                response = self._make_request(
                    list_url,
                    save_html=True,
                    use_cache_on_error=True,
                    is_detail_page=False
                )

                if not response or not hasattr(response, 'ok') or not response.ok:
                    status_code = getattr(response, 'status_code', 'No response')
                    logger.error(f"一覧ページの取得に失敗しました: {status_code}")
                    return []

                html = response.text
                soup = BeautifulSoup(html, 'html.parser')

                # キャッシュに保存
                try:
                    self.cache_manager.save_list_page(html)
                    logger.debug(f"一覧ページをキャッシュに保存しました: {list_url}")
                except Exception as e:
                    logger.error(f"キャッシュの保存中にエラーが発生しました: {e}", exc_info=True)

            # HTMLのパースに失敗した場合はエラー
            if soup is None:
                logger.error("HTMLのパースに失敗しました")
                return []

            # 馬の情報を格納するリスト
            horses = []

            # 馬の行を抽出（実際のHTML構造に合わせたセレクタ）
            selectors = [
                '.auctionTableCard',  # カード型レイアウトのメインコンテナ
                '.auctionTableCard__horseInfo',  # 馬情報を含むコンテナ
                '.auctionTableCard__name',  # 馬名を含む要素
                'div[class*="auctionTableCard"]'  # より広範なマッチング
            ]

            # セレクタで行を抽出
            rows = []
            for selector in selectors:
                rows = soup.select(selector)
                if rows:
                    logger.info(f"セレクタ '{selector}' で {len(rows)}件の要素を検出")
                    break

            if not rows:
                logger.warning("馬の行が見つかりませんでした")
                return []

            # 各行から情報を抽出
            for row in rows:
                try:
                    horse_info = {}

                    # 馬名と詳細URLを抽出
                    name_elem = row.select_one('a[href*="horse"], a[href*="detail"], .auctionTableCard__name a')
                    if not name_elem:
                        # 別のパターンを試す
                        name_elem = row.select_one('a[href*="/horse/"]')

                    if name_elem:
                        horse_name = name_elem.get_text(strip=True)
                        detail_url = urljoin(self.base_url, name_elem.get('href', ''))

                        if horse_name and detail_url:
                            # 馬IDを抽出
                            horse_id = self._extract_horse_id(detail_url)

                            horse_info.update({
                                'name': horse_name,
                                'url': detail_url,
                                'horse_id': horse_id,
                                'auction_date': self.get_auction_date() or datetime.now().strftime('%Y-%m-%d')
                            })

                            logger.debug(f"馬情報を抽出: {horse_name} (ID: {horse_id})")

                            # 行全体のテキストから追加情報を抽出
                            row_text = row.get_text(' ', strip=True)

                            # 性別と年齢を抽出（horseLabelWrapperから取得）
                            label_wrapper = row.select_one('.horseLabelWrapper')
                            if label_wrapper:
                                label_text = label_wrapper.get_text(strip=True)
                                # 性別を抽出
                                sex_match = re.search(r'([牡牝セ]|せん|めす)', label_text)
                                if sex_match:
                                    sex = sex_match.group(1)
                                    if sex == 'せん': sex = 'セ'
                                    elif sex == 'めす': sex = '牝'
                                    horse_info['sex'] = sex

                                # 年齢を抽出
                                age_match = re.search(r'(\d+)', label_text)
                                if age_match:
                                    try:
                                        horse_info['age'] = int(age_match.group(1))
                                    except (ValueError, TypeError):
                                        pass  # 年齢の取得に失敗した場合はスキップ

                            # 馬の情報をリストに追加
                            horses.append(horse_info)

                except Exception as e:
                    logger.error(f"馬情報の抽出中にエラーが発生しました: {str(e)}")
                    logger.error(traceback.format_exc())
                    continue

            logger.info(f"{len(horses)}頭の馬を発見しました")
            return horses

        except Exception as e:
            logger.error(f"馬一覧のスクレイピング中にエラーが発生しました: {str(e)}")
            logger.error(traceback.format_exc())
            return []

    def _process_horse_rows(self, soup):
        """
        馬の行を処理するヘルパーメソッド

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            list: 抽出した馬の行のリスト
        """
        try:
            # 1. まずはauctionTableCardクラスを持つ要素を探す（キャッシュ用）
            rows = soup.select('.auctionTableCard')

            if not rows:
                # 2. 他の一般的なセレクタも試す
                selectors = [
                    'tr.horse-row',
                    'tr.horse-item',
                    'tr[data-horse-id]',
                    '.horse-row',
                    '.horse-item',
                    '[data-horse-id]'
                ]

                for selector in selectors:
                    try:
                        found = soup.select(selector)
                        if found:
                            logger.debug(f"セレクタ '{selector}' で {len(found)} 件の要素を検出")
                            rows = found
                            break
                    except Exception as e:
                        logger.debug(f"セレクタ '{selector}' でエラー: {e}")

            if rows:
                logger.info(f"合計 {len(rows)} 件の馬の行を検出しました")
            else:
                logger.warning("馬の行を検出できませんでした")

            return rows

        except Exception as e:
            logger.error(f"馬の行の処理中にエラーが発生しました: {e}")
            logger.error(traceback.format_exc())
            return []

    def _extract_horse_info_from_row(self, row, base_url=None):
        """
        馬の行から馬の情報を抽出する

        Args:
            row: 馬の行を表すBeautifulSoup要素
            base_url: 詳細ページのベースURL（オプション）

        Returns:
            dict: 抽出した馬の情報
        """
        horse_info = {}
        try:
            # 馬名の抽出
            name_elem = row.select_one('div.auctionTableCard__name a.auctionTableCard__name--link')
            if name_elem and name_elem.text.strip():
                horse_name = name_elem.text.strip()
                horse_info['name'] = horse_name
                logger.debug(f"馬名を抽出: {horse_name}")

                # 詳細ページのURLを取得
                detail_url = name_elem.get('href')
                if detail_url and base_url:
                    # 相対URLの場合はベースURLと結合
                    if not detail_url.startswith(('http://', 'https://')):
                        detail_url = f"{base_url.rstrip('/')}/{detail_url.lstrip('/')}"
                    horse_info['detail_url'] = detail_url

                    # 詳細ページから追加情報を取得
                    detail_info = self._extract_horse_detail_info(detail_url)
                    if detail_info:
                        horse_info.update(detail_info)
            else:
                logger.warning("馬名の抽出に失敗しました")
                # デバッグ用にHTMLをログに出力
                name_container = row.select_one('div.auctionTableCard__horseInfo')
                if name_container:
                    logger.debug(f"抽出対象のHTML: {name_container}")

            # 性別の抽出
            sex_age_elem = row.select_one('div.horseLabelWrapper')
            if sex_age_elem:
                sex_age_text = sex_age_elem.get_text(strip=True)
                logger.debug(f"性別・年齢テキスト: {sex_age_text}")

                # 性別の抽出
                if '牡' in sex_age_text:
                    horse_info['sex'] = '牡'
                elif '牝' in sex_age_text:
                    horse_info['sex'] = '牝'
                elif 'せん' in sex_age_text:
                    horse_info['sex'] = 'せん'

                # 年齢の抽出
                age_match = re.search(r'(\d+)歳', sex_age_text)
                if age_match:
                    horse_info['age'] = int(age_match.group(1))

            # 販売者の抽出
            seller_elem = row.find(string=re.compile('販売申込者'))
            if seller_elem:
                # 次の要素が販売者名の場合
                next_sibling = seller_elem.find_next_sibling()
                if next_sibling and next_sibling.name == 'span':
                    seller = next_sibling.text.strip()
                    # 末尾の...を削除
                    if seller.endswith('...'):
                        seller = seller[:-3]
                    horse_info['seller'] = seller
                    logger.debug(f"販売者を抽出: {seller}")

            # 賞金の抽出
            prize_elem = row.find(string=re.compile('総賞金'))
            if prize_elem:
                # 次の要素が賞金の場合
                next_sibling = prize_elem.find_parent().find_next_sibling()
                if next_sibling and next_sibling.name == 'div' and 'value' in next_sibling.get('class', []):
                    prize_text = next_sibling.text.strip()
                    logger.debug(f"賞金テキスト: {prize_text}")

                    # 賞金を数値に変換
                    if '未出走' not in prize_text and '万' in prize_text:
                        try:
                            # 「1,234.5万円」のような形式を1234.5に変換
                            prize = float(prize_text.replace('万円', '').replace(',', ''))
                            horse_info['total_prize_start'] = prize
                            horse_info['total_prize_latest'] = prize
                            logger.debug(f"賞金を抽出: {prize}万円")
                        except (ValueError, AttributeError):
                            logger.warning(f"賞金のパースに失敗しました: {prize_text}")

            # スクレイプ日時を記録
            horse_info['scraped_at'] = datetime.now().isoformat()

            logger.debug(f"抽出した馬情報: {horse_info}")
            return horse_info

        except Exception as e:
            logger.error(f"馬情報の抽出中にエラーが発生しました: {e}")
            logger.debug(f"エラーが発生した行のHTML: {row}")
            return {}

    def _extract_horse_detail_info(self, detail_url):
        """
        馬の詳細ページから追加情報を抽出する

        Args:
            detail_url: 詳細ページのURL

        Returns:
            dict: 抽出した馬の詳細情報
        """
        detail_info = {}
        try:
            # キャッシュから詳細ページを取得
            cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'test_cache')
            detail_file = os.path.join(cache_dir, os.path.basename(detail_url))

            if os.path.exists(detail_file):
                with open(detail_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                soup = BeautifulSoup(content, 'html.parser')

                # 基本情報を抽出
                title = soup.title.text if soup.title else ''

                # タイトルから情報を抽出
                if '|' in title:
                    title_parts = title.split('|')
                    if len(title_parts) > 0:
                        # 馬名、性別、年齢、毛色、生年月日を抽出
                        horse_info = title_parts[0].strip()
                        detail_info['full_name'] = horse_info

                        # 性別と年齢
                        if '牡' in horse_info:
                            detail_info['sex'] = '牡'
                        elif '牝' in horse_info:
                            detail_info['sex'] = '牝'
                        elif 'せん' in horse_info:
                            detail_info['sex'] = 'せん'

                        # 年齢
                        age_match = re.search(r'(\d+)歳', horse_info)
                        if age_match:
                            detail_info['age'] = int(age_match.group(1))

                        # 毛色
                        color_match = re.search(r'[\u4e00-\u9fff]+毛', horse_info)
                        if color_match:
                            detail_info['color'] = color_match.group(0)

                        # 生年月日
                        birth_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', horse_info)
                        if birth_match:
                            detail_info['birth_date'] = f"{birth_match.group(1)}-{birth_match.group(2).zfill(2)}-{birth_match.group(3).zfill(2)}"

                # 血統情報を抽出
                table_rows = soup.select('table tr')
                for row in table_rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        key = cols[0].get_text(strip=True)
                        value = cols[1].get_text(' ', strip=True)

                        if '父' in key:
                            detail_info['sire'] = value
                        elif '母' in key and '父' not in key:  # 母の父と区別
                            detail_info['dam'] = value
                        elif '母の父' in key or '母父' in key:
                            detail_info['damsire'] = value
                        elif '馬主' in key:
                            detail_info['owner'] = value
                        elif '生産者' in key:
                            detail_info['breeder'] = value

                # 馬体重を抽出
                weight_match = re.search(r'馬体重[：:]([\d.]+)kg', content)
                if weight_match:
                    try:
                        detail_info['weight'] = float(weight_match.group(1))
                    except (ValueError, AttributeError):
                        pass

                # 落札価格を抽出（入札履歴から最新の価格を取得）
                bid_rows = soup.select('table tr')
                for row in bid_rows:
                    cols = row.find_all('td')
                    if len(cols) >= 4:  # 入札履歴の行
                        try:
                            price_text = cols[3].get_text(strip=True)
                            if '円' in price_text:
                                price = int(price_text.replace('円', '').replace(',', ''))
                                detail_info['winning_bid'] = price
                                break  # 最新の入札価格を取得
                        except (ValueError, IndexError):
                            continue

                # コメントを抽出
                comments = []
                comment_sections = soup.select('div.comment, div.description, p.comment')
                for section in comment_sections:
                    comment = section.get_text(' ', strip=True)
                    if comment and len(comment) > 10:  # 短いテキストは無視
                        comments.append(comment)

                if comments:
                    detail_info['comments'] = comments

                # 疾病情報を抽出
                health_issues = []
                health_sections = soup.find_all(string=re.compile(r'疾病|怪我|治療|異常'))
                for section in health_sections:
                    parent = section.parent
                    if parent:
                        health_text = parent.get_text(' ', strip=True)
                        if health_text and len(health_text) > 10:  # 短いテキストは無視
                            health_issues.append(health_text)

                if health_issues:
                    detail_info['health_issues'] = health_issues

                logger.debug(f"詳細情報を抽出: {detail_info}")
                return detail_info

            return {}

        except Exception as e:
            logger.error(f"詳細情報の抽出中にエラーが発生しました: {e}")
            return {}

    def _extract_sex_and_age(self, row, horse_info):
        """性別と年齢を抽出するヘルパーメソッド"""
        try:
            # 性別と年齢を抽出（horseLabelWrapperから取得）
            label_wrapper = row.select_one('.horseLabelWrapper')
            if label_wrapper:
                label_text = label_wrapper.get_text(strip=True)
                # 性別を抽出
                sex_match = re.search(r'([牡牝セ]|せん|めす)', label_text)
                if sex_match:
                    sex = sex_match.group(1)
                    if sex == 'せん': sex = 'セ'
                    elif sex == 'めす': sex = '牝'
                    horse_info['sex'] = sex

                # 年齢を抽出
                age_match = re.search(r'(\d+)', label_text)
                if age_match:
                    try:
                        horse_info['age'] = int(age_match.group(1))
                    except (ValueError, TypeError):
                        pass  # 年齢の取得に失敗した場合はスキップ

        except Exception as e:
            logger.error(f"性別・年齢の抽出中にエラーが発生しました: {str(e)}")

    def _extract_additional_info(self, row, horse_info):
        """その他の情報を抽出するヘルパーメソッド"""
        try:
            # 行全体のテキストから追加情報を抽出
            row_text = row.get_text(' ', strip=True)

            # ここにその他の情報抽出ロジックを追加
            # 例: 販売価格、生産者、調教師など
            pass

        except Exception as e:
            logger.error(f"追加情報の抽出中にエラーが発生しました: {str(e)}")
            logger.debug(traceback.format_exc())

    def _process_horse_info(self, row):
        """
        馬の行から情報を抽出して辞書を返すヘルパーメソッド

        Args:
            row: BeautifulSoupオブジェクト（馬1頭分の行）

        Returns:
            dict: 抽出した馬の情報
        """
        try:
            # 馬の情報を抽出
            horse_info = self._extract_horse_info_from_row(row)

            if not horse_info:
                logger.warning("馬の情報を抽出できませんでした")
                return None

            # デバッグ用に抽出した情報をログ出力
            logger.debug(f"抽出した馬情報: {horse_info}")

            # 性別と年齢が抽出されていない場合は再度試みる
            if 'sex' not in horse_info or 'age' not in horse_info:
                self._extract_sex_and_age(row, horse_info)

            # その他の情報を抽出
            self._extract_additional_info(row, horse_info)

            # 必要なフィールドが存在することを確認
            required_fields = ['name', 'url', 'horse_id']
            for field in required_fields:
                if field not in horse_info or not horse_info[field]:
                    logger.warning(f"必須フィールド '{field}' が不足しています: {horse_info}")

            return horse_info

        except Exception as e:
            logger.error(f"馬情報の処理中にエラーが発生しました: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    def _clean_seller_name(self, seller_name: str) -> str:
        """販売者名をクリーニングする。

        Args:
            seller_name: クリーニング前の販売者名

        Returns:
            str: クリーニング済みの販売者名
        """
        if not seller_name:
            return ""

        # 不要な接頭辞・接尾辞を削除
        seller = seller_name.strip()
        seller = re.sub(r'^[（(].*?[)）]', '', seller)  # 先頭の括弧内テキストを削除
        seller = re.sub(r'[（(].*?[)）]$', '', seller)  # 末尾の括弧内テキストを削除
        seller = re.sub(r'[\[\]【】]', '', seller)  # 角括弧・鉤括弧を削除

        # 不要な接頭辞を削除
        seller = re.sub(r'^(?:販売(?:申込)?[者人]|出品者|セラー|売主)[：:]*\s*', '', seller, flags=re.IGNORECASE)

        # インボイス登録情報を削除
        seller = re.sub(r'\s*(?:[(（]?インボイス登録(?:あり)?[)）]?|[(（]?登録販売者[)）]?)\s*', '', seller, flags=re.IGNORECASE)

        # 連続するスペースを1つに統一
        seller = re.sub(r'\s+', ' ', seller).strip()

        return seller

    def _extract_seller(self, soup: BeautifulSoup) -> str:
        """売主情報を抽出する。

        複数の方法で売主情報を抽出し、最初に一致したものを返します。
        1. テーブルから販売者情報を抽出
        2. フッターやコピーライトから販売者情報を抽出
        3. キーワード（売主、販売者、出品者、セラー）を元に検索
        4. 生のHTMLテキストから正規表現で検索

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            str: 抽出した販売者名。見つからない場合は空文字列
        """
        if not soup:
            logger.warning("BeautifulSoupオブジェクトが無効です")
            return ""

        logger.debug("販売者情報の抽出を開始します")

        # 1. テーブルから販売者情報を抽出
        try:
            # テーブル内のセラー情報を検索
            seller_tables = soup.find_all('table', class_=lambda x: x and 'seller' in x.lower())
            for table in seller_tables:
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    if th and td and any(keyword in th.get_text().strip() for keyword in ['売主', '販売者', '出品者', 'セラー']):
                        seller = self._clean_seller_name(td.get_text().strip())
                        if seller:
                            logger.info(f"テーブルから販売者を抽出: {seller}")
                            return seller
        except Exception as e:
            logger.debug(f"テーブルからの販売者抽出でエラー: {e}")

        # 2. フッターやコピーライトから抽出
        try:
            footer = soup.find('footer') or soup.find('div', class_=lambda x: x and 'footer' in x.lower())
            if footer:
                seller_match = re.search(r'売主[：:]([^\n<]+)', footer.get_text())
                if seller_match:
                    seller = self._clean_seller_name(seller_match.group(1))
                    if seller:
                        logger.info(f"フッターから販売者を抽出: {seller}")
                        return seller
        except Exception as e:
            logger.debug(f"フッターからの販売者抽出でエラー: {e}")

        # 3. キーワードを元に検索
        keywords = ['売主', '販売者', '出品者', 'セラー']
        for keyword in keywords:
            try:
                elements = soup.find_all(string=re.compile(keyword))
                for elem in elements:
                    text = elem.get_text().strip()
                    if keyword in text:
                        seller_match = re.search(f'{keyword}[：:]([^\n<]+)', text)
                        if seller_match:
                            seller = self._clean_seller_name(seller_match.group(1))
                            if seller:
                                logger.info(f"キーワード「{keyword}」から販売者を抽出: {seller}")
                                return seller
            except Exception as e:
                logger.debug(f"キーワード「{keyword}」からの販売者抽出でエラー: {e}")

        # 4. 生のHTMLテキストから正規表現で検索（最後の手段）
        try:
            html_text = str(soup)
            seller_match = re.search(r'(?:売主|販売者|出品者|セラー)[：:]([^<\n]+)', html_text)
            if seller_match:
                seller = self._clean_seller_name(seller_match.group(1))
                if seller:
                    logger.info(f"正規表現で販売者を抽出: {seller}")
                    return seller
        except Exception as e:
            logger.debug(f"正規表現での販売者抽出でエラー: {e}")

        logger.warning("販売者情報が見つかりませんでした")
        return ""

    def _extract_sold_price(self, soup: BeautifulSoup) -> Optional[int]:
        # 落札価格を抽出する
        #
        # Args:
        #     soup: BeautifulSoupオブジェクト
        #
        # Returns:
        #     Optional[int]: 落札価格（円）。見つからない場合はNone
        try:
            # 1. itemprop="price" 属性を持つ要素を直接探す（最も確実な方法）
            price_element = soup.find(itemprop="price")
            if price_element:
                try:
                    price_text = price_element.get_text(strip=True)
                    price = int(price_text.replace(',', ''))
                    logger.debug(f"itemprop='price' から落札価格を抽出: {price}円")
                    return price
                except (ValueError, AttributeError) as e:
                    logger.debug(f"itemprop='price' からの価格抽出に失敗: {e}")

            # 2. 現在価格を表示する要素を探す
            current_price_elements = soup.find_all(string=re.compile(r'現在価格'))
            for elem in current_price_elements:
                parent = elem.parent
                # 親要素内で価格を探す
                price_text = parent.find(string=re.compile(r'[\d,]+'))
                if price_text:
                    try:
                        price = int(price_text.replace(',', ''))
                        logger.debug(f"現在価格から落札価格を抽出: {price}円")
                        return price
                    except (ValueError, AttributeError):
                        continue

            # 3. 価格ボックスを探す
            price_box = soup.find(class_=re.compile(r'priceBox|price-box|price_box'))
            if price_box:
                # 価格ボックス内の数値を探す
                price_matches = re.findall(r'([\d,]+)', price_box.get_text())
                if price_matches:
                    try:
                        # 最も大きい数値を落札価格とみなす
                        prices = [int(p.replace(',', '')) for p in price_matches]
                        price = max(prices)  # 最大値を採用
                        logger.debug(f"価格ボックスから最大値を落札価格として抽出: {price}円")
                        return price
                    except (ValueError, IndexError):
                        pass

            # 4. テキスト全体から正規表現で探す（最終手段）
            price_patterns = [
                # 「落札価格」の後に数値が続くパターン
                r'落札価格[^\d]*([\d,]+)',
                # 「123,456円」形式
                r'([\d,]+)\s*円',
                # 「123,456万円」形式
                r'([\d,]+)\s*万円',
            ]

            text = soup.get_text()
            for pattern in price_patterns:
                match = re.search(pattern, text)
                if match:
                    try:
                        # 単純に数値のみを抽出（単位「kg」は含めない）
                        price = int(match.group(1).replace(',', ''))
                        logger.debug(f"正規表現で落札価格を抽出: {price} (パターン: {pattern})")
                        return price
                    except (ValueError, IndexError):
                        continue

            logger.warning("落札価格を見つけることができませんでした")
            return None

        except Exception as e:
            logger.error(f"落札価格の抽出中にエラーが発生しました: {e}")
            logger.error(traceback.format_exc())

        return None

    def _extract_horse_id(self, url: str) -> str:
        """馬の詳細ページURLから馬IDを抽出します。

        Args:
            url: 馬の詳細ページのURL

        Returns:
            抽出した馬ID。見つからない場合は空文字列を返す
        """
        try:
            if not url:
                return ""

            logger.debug(f"馬ID抽出対象URL: {url}")

            # 複数のパターンで馬IDを抽出
            patterns = [
                r'(?:/|id=)(\d+)(?:$|&|/)',  # 標準的なパターン
                r'/item/(\d+)',  # /item/12345 形式
                r'/horse/(\d+)',  # /horse/12345 形式
                r'(\d{4,})',  # 4桁以上の数字（最後の手段）
            ]

            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    horse_id = match.group(1)
                    logger.debug(f"馬IDを抽出: {horse_id} (パターン: {pattern})")
                    return horse_id

            logger.warning(f"馬IDを抽出できませんでした: {url}")
            return ""

        except Exception as e:
            logger.error(f"馬IDの抽出中にエラーが発生: {str(e)}")
            return ""

    def _extract_name_sex_age(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """馬名、性別、年齢を抽出します。

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            Dict[str, Any]: 抽出した情報（name, sex, age）
        """
        result = {
            'name': '',
            'sex': '',
            'age': None
        }

        try:
            # 1. 馬名を抽出（クラス名を指定）
            name_elem = soup.find('h1', class_='horse-name')
            if name_elem:
                result['name'] = name_elem.get_text(strip=True)
                logger.debug(f"馬名を抽出: {result['name']}")

            # 2. 性別と年齢の抽出
            sex = ""
            age = None

            # 2.1 通常の性別・年齢要素を検索
            sex_age_element = soup.find(class_="horseLabelWrapper")
            if sex_age_element:
                # 性別を抽出
                sex_element = sex_age_element.find(class_=["horseLabelWrapper__horseSex", "horseSex"])
                if sex_element:
                    sex = sex_element.get_text(strip=True)
                    logger.debug(f"性別を抽出 (horseLabelWrapper): {sex}")

                # 年齢を抽出
                age_element = sex_age_element.find(class_=["horseLabelWrapper__horseAge", "horseAge"])
                if age_element:
                    age_text = age_element.get_text(strip=True)
                    age_match = re.search(r'(\d+)', age_text)
                    if age_match:
                        try:
                            age = int(age_match.group(1))
                            logger.debug(f"年齢を抽出 (horseLabelWrapper): {age}")
                        except (ValueError, TypeError) as e:
                            logger.warning(f"年齢の数値変換に失敗: {age_match.group(1)} - {e}")

            # 2.2 性別・年齢が取得できていない場合は、代替方法で試す
            if not sex or age is None:
                # ページ内のテキストから正規表現で抽出を試みる
                page_text = soup.get_text()

                # 性別の抽出（牡/牝/セ/騸）
                if not sex:
                    sex_match = re.search(r'[牡牝セ騸]', page_text)
                    if sex_match:
                        sex = sex_match.group(0)
                        logger.debug(f"性別を抽出 (フォールバック): {sex}")

                # 年齢の抽出（数字+歳 or 数字）
                if age is None:
                    age_match = re.search(r'(\d+)[歳才]?', page_text)
                    if age_match:
                        try:
                            age = int(age_match.group(1))
                            logger.debug(f"年齢を抽出 (フォールバック): {age}")
                        except (ValueError, TypeError) as e:
                            logger.warning(f"年齢の抽出に失敗 (フォールバック): {e}")

            # 結果を格納
            result['sex'] = sex
            result['age'] = age

            logger.info(f"馬名・性別・年齢の抽出完了: {result}")
            return result

        except Exception as e:
            logger.error(f"馬名・性別・年齢の抽出中にエラーが発生: {str(e)}")
            logger.debug(traceback.format_exc())
            return result

    def _extract_pedigree(self, soup: BeautifulSoup) -> Dict[str, str]:
        """ページから血統情報（父、母、母父）を抽出する

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            dict: 抽出した血統情報（sire, dam, damsire をキーに持つ辞書）
        """
        result = {
            'sire': '不明',
            'dam': '不明',
            'damsire': '不明'
        }

        try:
            # ページ全体のテキストを取得
            page_text = soup.get_text(separator=' ', strip=True)

            # 父、母、母父のパターンにマッチするか試みる
            patterns = [
                # 一般的なパターン（日本語）
                r'父[：:]([^\s　]+)[\s　]+母[：:]([^\s　]+)[\s　]+母の父[：:]([^\s　(（]+)',
                # 英語表記のパターン
                r'Sire[：:]([^\n]+)Dam[：:]([^\n]+)Broodmare\s*Sire[：:]([^\n]+)',
                # シンプルなパターン
                r'父[：:]([^\s　]+)',
                r'母[：:]([^\s　]+)',
                r'母の父[：:]([^\s　(（]+)'
            ]

            for pattern in patterns:
                try:
                    matches = list(re.finditer(pattern, page_text))
                    for match in matches:
                        groups = match.groups()
                        if len(groups) >= 1 and '父' in pattern and result['sire'] == '不明':
                            result['sire'] = groups[0].strip()
                            logger.debug(f"父を抽出: {result['sire']}")

                        if len(groups) >= 2 and '母' in pattern and '母の父' not in pattern and result['dam'] == '不明':
                            result['dam'] = groups[1].strip()
                            logger.debug(f"母を抽出: {result['dam']}")

                        if len(groups) >= 3 and '母の父' in pattern and result['damsire'] == '不明':
                            result['damsire'] = groups[2].strip()
                            logger.debug(f"母父を抽出: {result['damsire']}")

                        # 英語表記のパターン
                        if 'Sire' in pattern and len(groups) >= 3 and result['damsire'] == '不明':
                            result.update({
                                'sire': groups[0].strip(),
                                'dam': groups[1].strip(),
                                'damsire': groups[2].strip()
                            })
                            logger.debug(f"英語表記から血統情報を抽出: {result}")

                except Exception as e:
                    logger.warning(f"パターン '{pattern}' のマッチング中にエラーが発生: {str(e)}")
                    continue

            # 母父がまだ見つかっていない場合、別の方法で試す
            if result['damsire'] == '不明':
                try:
                    # 母の父を別の方法で検索
                    damsire_pattern = r'母の父[：:]([^\s　(（]+)'
                    damsire_match = re.search(damsire_pattern, page_text)
                    if damsire_match:
                        result['damsire'] = damsire_match.group(1).strip()
                        logger.debug(f"代替方法で母父を抽出: {result['damsire']}")
                except Exception as e:
                    logger.warning(f"代替方法での母父抽出中にエラーが発生: {str(e)}")

            # 結果を返す前に不要な空白や改行を削除
            for key in result:
                if result[key] and result[key] != '不明':
                    result[key] = re.sub(r'\s+', ' ', result[key]).strip()

            # 結果をログに記録
            logger.info(f"抽出した血統情報: 父={result['sire']}, 母={result['dam']}, 母父={result['damsire']}")
            logger.debug(f"血統情報を抽出: {result}")
            return result

        except Exception as e:
            logger.error(f"血統情報の抽出中にエラーが発生: {str(e)}")
            logger.debug(traceback.format_exc())
            return result

    def _parse_horse_info(self, page_text: str, detail_url: str, prize_money: float = None) -> Dict[str, Any]:
        """馬の詳細情報をパースします。

        Args:
            page_text: 馬の詳細ページのHTMLテキスト
            detail_url: 詳細ページのURL
            prize_money: 賞金情報（オプション）

        Returns:
            Dict: 馬の詳細情報を含む辞書
        """
        result = {
            'id': str(uuid.uuid4()),
            'auction_url': detail_url,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'sire': '不明',
            'dam': '不明',
            'damsire': '不明',
            'disease_tags': [],
            'race_record': '',
            'weight': None,
            'comment': '',
            'seller': '',
            'total_prize_start': 0.0,
            'total_prize_latest': 0.0,
            'image_url': '',
            'jbis_url': ''
        }

        try:
            soup = BeautifulSoup(page_text, 'html.parser')

            # 1. 血統情報の抽出
            try:
                pedigree = self._extract_pedigree(soup)
                result.update(pedigree)
                logger.debug(f"血統情報を抽出: {pedigree}")
            except Exception as e:
                logger.error(f"血統情報の抽出に失敗: {str(e)}")
                logger.debug(traceback.format_exc())

            # 2. レース戦績の抽出
            try:
                race_record = self._extract_race_record(soup)
                result['race_record'] = race_record
                logger.debug(f"レース戦績を抽出: {race_record}")
            except Exception as e:
                logger.error(f"レース戦績の抽出に失敗: {str(e)}")
                logger.debug(traceback.format_exc())

            # 3. 馬体重の抽出
            try:
                # 例: 最終出走馬体重：468kg
                weight_match = re.search(r'最終出走馬体重[：:](\d+)kg', page_text)
                if weight_match:
                    result['weight'] = int(weight_match.group(1))
                    logger.debug(f"馬体重を抽出: {result['weight']}kg")
            except Exception as e:
                logger.error(f"馬体重の抽出に失敗: {str(e)}")
                logger.debug(traceback.format_exc())

            # 4. 賞金情報の抽出
            try:
                jbis_url = self._extract_jbis_url(soup)
                prize_money = self._extract_prize_money(
                    page_text=page_text,
                    jbis_url=jbis_url,
                    race_record=result.get('race_record', '')
                )
                result.update(prize_money)
                logger.debug(f"賞金情報を抽出: {prize_money}")
            except Exception as e:
                logger.error(f"賞金情報の抽出に失敗: {str(e)}")
                logger.debug(traceback.format_exc())

            # 5. その他の情報
            try:
                other_info = {
                    'primary_image': self._extract_primary_image(soup),
                    'jbis_url': jbis_url,  # 既に取得済みの値を使用
                    'comment': self._extract_comment(page_text),
                    'seller': self._extract_seller(soup=soup)
                }
                result.update(other_info)

                # コメントから病気タグを抽出
                if 'comment' in result and result['comment']:
                    try:
                        result['disease_tags'] = self._extract_disease_tags(result['comment'])
                        logger.debug(f"病気タグを抽出: {result['disease_tags']}")
                    except Exception as e:
                        logger.error(f"病気タグの抽出中にエラーが発生: {str(e)}")
                        logger.debug(traceback.format_exc())
                        result['disease_tags'] = []
                else:
                    result['disease_tags'] = []

            except Exception as e:
                logger.error(f"その他の情報の抽出中にエラーが発生: {str(e)}")
                logger.debug(traceback.format_exc())

            return result

        except Exception as e:
            logger.error(f"馬情報の抽出中に予期せぬエラーが発生: {str(e)}")
            logger.error(traceback.format_exc())
            if not result.get('name'):
                raise ValueError("馬情報の抽出に失敗しました") from e
            # 一部の情報が取得できている場合は、取得できた情報を返す
            logger.warning("一部の情報が取得できませんでしたが、取得できた情報を返します")
            return result

    def scrape_horse_detail(self, detail_url: str, horse_name: str = None, horse_id: str = None,
                       prize_money: float = None, save_html: bool = False) -> Optional[Dict]:
        """馬の詳細情報をスクレイピングします。

        Args:
            detail_url: 馬の詳細ページのURL
            horse_name: 馬名（オプション）
            horse_id: 馬ID（オプション）
            prize_money: 賞金情報（オプション）
            save_html: HTMLをキャッシュに保存するかどうか

        Returns:
            Dict: 馬の詳細情報を含む辞書。エラー時はNoneを返す
        """
        try:
            # horse_idが指定されていない場合はURLから抽出
            if not horse_id:
                horse_id = self._extract_horse_id(detail_url)
                if horse_id:
                    logger.debug(f"URLから馬IDを抽出: {horse_id}")
                else:
                    logger.warning(f"URLから馬IDを抽出できませんでした: {detail_url}")

            # リクエストを送信してHTMLを取得
            response = self._make_request(
                detail_url,
                save_html=save_html,
                is_detail_page=True,
                horse_name=horse_name,
                horse_id=horse_id
            )

            if not response:
                logger.error(f"詳細ページの取得に失敗しました: {detail_url}")
                return None

            return self._parse_horse_info(response.text, detail_url, prize_money)

        except Exception as e:
            logger.error(f"馬の詳細情報の取得中にエラーが発生しました: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    def _extract_race_record(self, soup: BeautifulSoup) -> str:
        """レース戦績を抽出します。

        以下のパターンに対応:
        - レース成績（例: "24戦4勝［4-6-2-12］"）
        - 未出走の場合は「未出走」
        - 成績が見つからない場合は空文字列

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            str: 抽出されたレース成績の文字列
        """
        try:
            # ページ全体のテキストを取得（改行をスペースに置換して正規化）
            page_text = ' '.join(soup.stripped_strings)

            # デバッグ用: ページテキストの先頭をログに記録
            logger.debug(f"レース戦績抽出対象テキスト: {page_text[:500]}...")

            # 1. 完全なレース成績パターンを探す（例: "24戦4勝［4-6-2-12］"）
            # 全角・半角の括弧、空白の有無、様々なハイフン/ダッシュに対応
            record_patterns = [
                # 標準的な形式
                r'(\d+戦\d+勝\s*[\[［]\s*\d+\s*-\s*\d+\s*-\s*\d+\s*-\s*\d+\s*[\]］])',
                # 括弧内の区切り文字が異なるパターン
                r'(\d+戦\d+勝\s*[\[［]\s*\d+\s*[・,、]\s*\d+\s*[・,、]\s*\d+\s*[・,、]\s*\d+\s*[\]］])',
                # 括弧内の数値のみのパターン
                r'(\d+戦\d+勝\s*[\[［]\s*\d+\s+\d+\s+\d+\s+\d+\s*[\]］])',
                # 括弧なしのシンプルなパターン
                r'(\d+戦\d+勝)'
            ]

            for pattern in record_patterns:
                record_match = re.search(pattern, page_text)
                if record_match:
                    result = record_match.group(1).strip()
                    # 正規化: 全角スペース・タブ・改行を削除
                    result = re.sub(r'[\s　\t\n\r]+', '', result)
                    # 括弧を半角に統一
                    result = result.replace('［', '[').replace('］', ']')
                    # ハイフン・ダッシュを統一
                    result = re.sub(r'[－−—]', '-', result)
                    # カンマや中黒をハイフンに統一
                    result = re.sub(r'[・,、]', '-', result)

                    logger.debug(f"レース戦績を抽出: {result} (パターン: {pattern})")
                    return result

            # 2. 明示的に未出走と記載がある場合
            if re.search(r'未[ 　]*出[ 　]*走|出走前|デビュー前|未出走馬', page_text, re.IGNORECASE):
                logger.debug("未出走馬として検出")
                return "未出走"

            # 3. 競走馬登録番号が発行されていない場合も未出走とみなす
            if re.search(r'競走馬登録番号\s*[:：]?\s*なし|未登録|登録前', page_text, re.IGNORECASE):
                logger.debug("未登録・未出走馬として検出")
                return "未出走"

            # 4. 競走馬登録番号が記載されているが、レース成績の記載がない場合は「未出走」とみなす
            if re.search(r'競走馬登録番号\s*[:：]\s*\d+', page_text, re.IGNORECASE):
                # レース成績の記述が全くない場合
                if not re.search(r'\d+戦', page_text):
                    logger.debug("競走馬登録番号はあるがレース成績の記載がないため、未出走とみなします")
                    return "未出走"

            # 5. 成績が見つからない場合は空文字列を返す
            logger.debug("レース戦績が見つかりませんでした")
            return ""

        except Exception as e:
            logger.error(f"レース戦績の抽出中にエラーが発生: {e}")
            logger.error(traceback.format_exc())
            return ""  # エラー時は空文字列を返す

    def _extract_prize_money(self, page_text: str, jbis_url: Optional[str] = None, race_record: Optional[str] = None) -> Dict[str, float]:
        """賞金情報を抽出します。

        以下の情報源から優先順に賞金情報を抽出します：
        1. ページ内のdt/ddタグから総賞金を抽出
        2. 正規表現で総賞金を直接検索
        3. JBISのURLが指定されている場合はJBISから最新情報を取得

        未出走馬の場合は常に0.0を返します。

        Args:
            page_text: ページのHTMLテキスト
            jbis_url: JBISのURL（オプション、指定した場合は最新の賞金情報を取得）
            race_record: レース戦績（オプション、未指定の場合は自動で抽出）

        Returns:
            賞金情報を含む辞書（total_prize_start, total_prize_latest）
        """
        # デフォルト値の設定
        result = {
            'total_prize_start': 0.0,
            'total_prize_latest': 0.0
        }

        if not page_text or not isinstance(page_text, str):
            logger.warning("無効なページテキストが指定されました")
            return result

        try:
            logger.debug("賞金情報の抽出を開始")
            soup = BeautifulSoup(page_text, 'html.parser')

            # レース戦績を確認（未指定の場合は自動で抽出）
            if race_record is None:
                race_record = self._extract_race_record(soup)

            # 未出走馬の場合は0.0を返す
            if race_record == "未出走":
                logger.debug("未出走馬のため賞金を0.0に設定")
                return result

            # 1. dt/ddタグから取得を試みる（最も信頼性の高い方法）
            prize_found = False
            dt_tag = soup.find('dt', string=re.compile(r'^\s*総賞金\s*$'))

            if dt_tag and dt_tag.find_next_sibling('dd'):
                prize_text = dt_tag.find_next_sibling('dd').get_text(strip=True)
                prize_match = re.search(r'([\d,.]+)', prize_text)

                if prize_match:
                    try:
                        total_prize = float(prize_match.group(1).replace(',', ''))
                        result['total_prize_start'] = total_prize
                        result['total_prize_latest'] = total_prize
                        logger.debug(f"dt/ddタグから賞金を抽出: {total_prize}万円")
                        prize_found = True
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"賞金の数値変換に失敗: {e}")

            # 2. 正規表現で直接検索（フォールバック）
            if not prize_found:
                text_content = ' '.join(soup.stripped_strings)  # 正規化されたテキスト

                # 複数のパターンを試す
                patterns = [
                    r'総賞金[\s:：]+([\d,.]+)',  # 標準的な形式
                    r'賞金合計[\s:：]+([\d,.]+)',  # 代替形式
                    r'([\d,]+)(?:\s*万円|円)'  # 数値のみ（最後の手段）
                ]

                for pattern in patterns:
                    total_prize_match = re.search(pattern, text_content)
                    if total_prize_match:
                        try:
                            prize_str = total_prize_match.group(1).replace(',', '')
                            total_prize = float(prize_str)

                            # 円表記の場合は万円に変換
                            if '円' in text_content[total_prize_match.start():total_prize_match.end()]:
                                total_prize = total_prize / 10000

                            result['total_prize_start'] = total_prize
                            result['total_prize_latest'] = total_prize
                            logger.debug(f"正規表現で賞金を抽出: {total_prize}万円 (パターン: {pattern})")
                            prize_found = True
                            break
                        except (ValueError, AttributeError) as e:
                            continue

            # 3. JBISから最新情報を取得（可能な場合）
            if jbis_url and jbis_url.startswith('http'):
                try:
                    logger.debug(f"JBISから最新の賞金情報を取得: {jbis_url}")
                    latest_prize = self._extract_jbis_prize_money(jbis_url)

                    if latest_prize > 0:
                        # ページ内で賞金が見つからなかった場合のみ更新
                        if not prize_found:
                            result['total_prize_start'] = latest_prize
                        result['total_prize_latest'] = latest_prize
                        logger.debug(f"JBISから最新の賞金を取得: {latest_prize}万円")
                except Exception as e:
                    logger.warning(f"JBISからの賞金情報取得中にエラーが発生: {e}")

            # デバッグ用ログ
            if not prize_found and not (jbis_url and result['total_prize_latest'] > 0):
                logger.warning("賞金情報が見つかりませんでした")
                logger.debug(f"検索対象テキスト: {text_content[:300]}..." if 'text_content' in locals() else "")

            return result

        except Exception as e:
            logger.error(f"賞金情報の抽出中にエラーが発生しました: {e}")
            logger.error(traceback.format_exc())
            return result

    def _extract_comment(self, page_text: str) -> str:
        """コメント欄を抽出する。

        「本馬について」の見出しの直後の<pre>タグ内のテキストを取得する。

        Args:
            page_text: 抽出元のHTMLテキスト

        Returns:
            str: 抽出されたコメントテキスト。見つからない場合は空文字列。
        """
        try:
            # デバッグ用にHTMLをBeautifulSoupでパース
            soup = BeautifulSoup(page_text, 'html.parser')

            # デバッグ用にHTML全体をログに保存（必要に応じてコメントアウト）
            # with open('debug_comment_page.html', 'w', encoding='utf-8') as f:
            #     f.write(str(soup))

            # 「本馬について」の見出しを探す（大文字小文字を区別しない）
            about_heading = None
            for tag in soup.find_all(['b', 'strong', 'h3', 'h4', 'div', 'span']):
                if tag.text.strip() == '本馬について':
                    about_heading = tag
                    break

            if not about_heading:
                logger.warning("「本馬について」の見出しが見つかりませんでした")
                # ページ内の全テキストを確認
                all_text = soup.get_text()
                logger.debug(f"ページの先頭500文字: {all_text[:500]}...")
                return ""

            logger.debug(f"「本馬について」見出しを発見: {about_heading}")

            # 見出しの直後のhrタグを探す
            hr_tag = about_heading.find_next('hr')
            if not hr_tag:
                logger.warning("hrタグが見つかりませんでした")
                # hrタグがなくても、次の要素を探してみる
                next_element = about_heading.find_next()
                logger.debug(f"見出しの次にある要素: {next_element}")

                # 次の要素がテキストを含む場合、それを返す
                if next_element and next_element.text.strip():
                    return next_element.text.strip()
                return ""

            # hrタグの直後のpreタグを探す
            pre_tag = hr_tag.find_next('pre')
            if not pre_tag:
                logger.warning("preタグが見つかりませんでした")
                # preタグがなければ、hrタグ以降のテキストを取得してみる
                next_siblings = []
                current = hr_tag.next_sibling
                while current and len(next_siblings) < 10:  # 最大10要素まで
                    if hasattr(current, 'name') and current.name:
                        next_siblings.append(str(current))
                    current = current.next_sibling

                logger.debug(f"hrタグの後の要素: {' | '.join(next_siblings[:3])}...")

                # 次の要素がテキストを含む場合、それを返す
                next_element = hr_tag.find_next()
                if next_element and next_element.text.strip():
                    return next_element.text.strip()
                return ""

            # preタグ内のテキストを取得して返す
            comment = pre_tag.get_text(separator='\n', strip=True)
            logger.debug(f"コメントを抽出しました（長さ: {len(comment)}文字）")

            # 余分な空白や改行を削除して整形
            comment = ' '.join(comment.split())
            return comment

        except Exception as e:
            logger.error(f"コメントの抽出中にエラーが発生: {e}")
            logger.error(traceback.format_exc())
            return ""

    def _extract_disease_tags(self, comment: str) -> str:
        # 疾病タグを抽出します。
        # Args:
        #   comment: 抽出元のコメントテキスト
        # Returns:
        #   カンマ区切りの疾病タグ文字列。見つからない場合は「なし」を返します。
        if not comment:
            return "なし"

        try:
            disease_keywords = [
                '喉頭片麻痺', '喘鳴症', '脚部不安', '関節炎', '腱炎',
                '骨折', '脱臼', '筋肉痛', '腰痛', '腹痛', '球節炎', 'さく癖'
            ]

            found_diseases = []
            for disease in disease_keywords:
                if disease in comment:
                    found_diseases.append(disease)

            return ','.join(found_diseases) if found_diseases else "なし"
        except Exception as e:
            logger.error(f"疾病タグの抽出中にエラーが発生しました: {e}")
            logger.error(traceback.format_exc())
            return "なし"

    def _extract_primary_image(self, soup: BeautifulSoup) -> str:
        # 馬体画像のURLを抽出します。
        # Args:
        #   soup: BeautifulSoupオブジェクト
        # Returns:
        #   抽出した画像URL。見つからない場合は空文字列。
        try:
            # 画像要素を探す
            image_elements = soup.find_all('img')
            for img in image_elements:
                src = img.get('src', '')
                if (src and isinstance(src, str) and
                    'horse' in src.lower() and
                    any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png'])):
                    return src

            return ""
        except Exception as e:
            logger.error(f"馬体画像の抽出に失敗: {e}")
            logger.error(traceback.format_exc())
            return ""

    # 削除（上記の統一メソッドに統合）

    def _normalize_jbis_url(self, jbis_url: str) -> str:
        """JBISのURLを正規化する

        血統情報ページ(/pedigree/)や競走成績ページ(/record/)を基本情報ページに変換します。
        """
        if not jbis_url or not jbis_url.startswith('http'):
            return jbis_url

        # URLの正規化
        normalized_url = jbis_url

        # 血統情報ページや競走成績ページを基本情報ページに変換
        if '/pedigree/' in normalized_url or '/record/' in normalized_url:
            normalized_url = re.sub(r'(/pedigree/|/record/).*$', '/', normalized_url)

        # 末尾のスラッシュを確保
        if not normalized_url.endswith('/'):
            normalized_url += '/'

        return normalized_url

    def _extract_jbis_prize_money(self, jbis_url: str) -> float:
        """JBISのページから総賞金を取得する

        Args:
            jbis_url: JBISの馬基本情報ページのURL

        Returns:
            賞金額（万円単位）。取得に失敗した場合は0.0
        """
        if not jbis_url or not jbis_url.startswith('http'):
            logger.warning(f"無効なJBIS URL: {jbis_url}")
            return 0.0

        try:
            # URLを正規化
            normalized_url = self._normalize_jbis_url(jbis_url)
            if normalized_url != jbis_url:
                logger.debug(f"JBIS URLを正規化: {jbis_url} -> {normalized_url}")

            # 最大3回リトライ
            for attempt in range(3):
                try:
                    response = self.session.get(normalized_url, timeout=30)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # 方法1: dtタグから総賞金を取得（最も確実）
                    total_prize_dt = soup.find('dt', string=re.compile(r'^\s*総賞金\s*$'))
                    if total_prize_dt:
                        dd = total_prize_dt.find_next_sibling('dd')
                        if dd:
                            prize_text = dd.get_text(strip=True)
                            prize_match = re.search(r'([\d,.]+)', prize_text)
                            if prize_match:
                                prize_value = float(prize_match.group(1).replace(',', ''))
                                logger.debug(f"JBISから賞金を取得: {prize_value}万円 (dtタグから)")
                                return prize_value

                    # 方法2: フォールバック - 正規表現で直接検索
                    prize_match = re.search(r'総賞金[\s:：]*([\d,.]+)', soup.get_text())
                    if prize_match:
                        prize_value = float(prize_match.group(1).replace(',', ''))
                        logger.debug(f"JBISから賞金を取得: {prize_value}万円 (正規表現から)")
                        return prize_value

                except (requests.RequestException, ValueError) as e:
                    if attempt == 2:  # 最終リトライ
                        logger.warning(f"JBISからの賞金取得に失敗 (試行 {attempt + 1}/3): {e}")
                    time.sleep(1)  # 1秒待機してリトライ
                    continue

            logger.warning(f"JBISから賞金を取得できませんでした: {normalized_url}")
            return 0.0

        except Exception as e:
            logger.error(f"JBIS賞金取得中にエラーが発生: {e}")
            logger.error(traceback.format_exc())
            return 0.0

    def _extract_jbis_url(self, soup) -> str:
        # JBIS URLを抽出し、基本情報ページのURLに正規化して返す
        try:
            # 1. まず「基本情報」というテキストを含むリンクを探す
            info_links = []
            for link in soup.find_all('a', href=True):
                if '基本情報' in link.get_text():
                    info_links.append(link.get('href', ''))

            # 2. 基本情報リンクからJBISのURLを抽出
            for href in info_links:
                if 'jbis.or.jp' in href and 'horse' in href:
                    normalized_url = self._normalize_jbis_url(href)
                    print(f"基本情報ページからJBIS URLを抽出: {normalized_url}")
                    return normalized_url

            # 3. 基本情報リンクが見つからない場合は、直接JBISリンクを探す
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if 'jbis.or.jp' in href and 'horse' in href:
                    normalized_url = self._normalize_jbis_url(href)
                    print(f"直接JBISリンクから抽出: {normalized_url}")
                    return normalized_url

            print("警告: JBISの基本情報ページへのリンクが見つかりませんでした")
            return ""

        except Exception as e:
            print(f"JBIS URLの抽出に失敗: {e}")
            return ""

    def _normalize_jbis_url(self, jbis_url: str) -> str:
        # JBIS URLを基本情報ページのURLに正規化する
        #
        # Args:
        #     jbis_url: 正規化するJBISのURL
        #
        # Returns:
        #     str: 正規化された基本情報ページのURL（例: https://www.jbis.or.jp/horse/0001378353/）
        if not jbis_url:
            return ""

        # 相対URLの場合はベースURLを追加
        if jbis_url.startswith('//'):
            jbis_url = 'https:' + jbis_url
        elif not jbis_url.startswith('http'):
            jbis_url = 'https://www.jbis.or.jp' + ('' if jbis_url.startswith('/') else '/') + jbis_url

        # クエリパラメータを除去
        jbis_url = jbis_url.split('?')[0]

        # 馬IDを抽出（例: /horse/0001378353/ から 0001378353 を抽出）
        horse_id_match = re.search(r'/horse/(\d+)', jbis_url)
        if not horse_id_match:
            return ""

        horse_id = horse_id_match.group(1)

        # 基本情報ページのURLを構築
        return f"https://www.jbis.or.jp/horse/{horse_id}/"

    def _process_horse_detail(self, link: Dict[str, Any], auction_date: str, save_html: bool = False) -> Optional[Dict]:
        """個別の馬の詳細情報を処理するヘルパーメソッド

        Args:
            link: 馬の基本情報を含む辞書（url, prize_money, name など）
            auction_date: オークション日
            save_html: HTMLをキャッシュに保存するかどうか

        Returns:
            処理済みの馬情報（エラーの場合はNone）
        """
        try:
            detail_url = link['url']
            prize_money = link.get('prize_money')
            horse_name = link.get('name', '不明')
            horse_id = link.get('horse_id') or self._extract_horse_id(detail_url)

            logger.info(f"馬の詳細を取得中: {horse_name} - {detail_url}")
            if horse_id:
                logger.debug(f"馬ID: {horse_id}")

            # 詳細情報を取得
            detail_data = self.scrape_horse_detail(
                detail_url,
                horse_name=horse_name,
                horse_id=horse_id,
                prize_money=prize_money,
                save_html=save_html
            )

            if not detail_data:
                logger.warning(f"詳細情報が空です: {horse_name}")
                return None

            # オークション日を設定
            detail_data['auction_date'] = auction_date

            # 必須フィールドのチェック
            required_fields = ['name', 'sex', 'age', 'seller', 'sire', 'dam', 'damsire', 'auction_date']
            missing_fields = [field for field in required_fields
                           if field not in detail_data or not detail_data[field]]

            if missing_fields:
                logger.warning(f"必須フィールドが不足しています: {missing_fields} - {horse_name}")

            # デバッグ情報を出力
            logger.debug(f"馬の詳細を取得: {horse_name} - 賞金: {prize_money}万円")
            for field in required_fields:
                logger.debug(f"  {field}: {detail_data.get(field, 'N/A')}")

            return detail_data

        except Exception as e:
            logger.error(f"馬の詳細取得中にエラーが発生しました ({horse_name}): {str(e)}")
            logger.debug(traceback.format_exc())

            # テストモードの場合はエラーを再スロー
            if self.test_mode:
                raise

            return None

    def scrape_all_horses(self, auction_date: str = None, save_html: bool = True,
                         max_workers: int = 4) -> List[Dict]:
        """全馬の情報を並列で取得します。

        Args:
            auction_date: オークション日（指定がない場合は自動取得）
            save_html: HTMLをキャッシュに保存するかどうか
            max_workers: 並列処理の最大スレッド数（テストモードでは1に設定）

        Returns:
            List[Dict]: 各馬の詳細情報のリスト
        """
        if not auction_date:
            auction_date = self.get_auction_date()

        # キャッシュセッションを開始
        if save_html:
            try:
                self.current_session_id = self.cache_manager.start_new_session()
                logger.info(f"キャッシュセッションを開始しました: {self.current_session_id}")
            except Exception as e:
                logger.error(f"キャッシュセッションの開始に失敗: {e}")

        # テストモードの場合はシングルスレッドで実行
        if self.test_mode:
            max_workers = 1
            logger.info("テストモードのため、シングルスレッドで実行します")

        logger.info(f"オークション日: {auction_date}")

        # 馬の一覧を取得（賞金情報付き）
        horse_links = self.scrape_horse_list()
        logger.info(f"{len(horse_links)}頭の馬を発見しました。")

        # デバッグ用：馬一覧を出力
        logger.debug("\n=== 馬一覧 ===")
        for i, horse in enumerate(horse_links, 1):
            logger.debug(f"{i}. {horse.get('name')} - {horse.get('url')}")
        logger.debug("==============")

        horses = []

        # 並列処理で各馬の詳細情報を取得
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 各馬の処理をスケジュール
            future_to_horse = {
                executor.submit(
                    self._process_horse_detail,
                    link,
                    auction_date,
                    save_html
                ): link.get('name', '不明')
                for link in horse_links
            }

            # 進捗表示用
            futures = tqdm(
                concurrent.futures.as_completed(future_to_horse),
                total=len(future_to_horse),
                desc="馬の詳細を取得中",
                unit="頭"
            )

            # 結果を収集
            for future in futures:
                try:
                    result = future.result()
                    if result:
                        horses.append(result)
                except Exception as e:
                    logger.error(f"馬の詳細取得中にエラーが発生しました: {str(e)}")
                    if self.test_mode:
                        raise

        logger.info(f"{len(horses)}/{len(horse_links)}頭の馬の詳細を取得しました。")
        return horses

def save_scraped_data(horse_data: Dict[str, Any], data_dir: str = 'static-frontend/public/data', test_mode: bool = False) -> Tuple[bool, str]:
    # スクレイピングしたデータをhorses.jsonとauction_history.jsonに保存します。
    #
    # この関数は以下の処理を行います：
    # 1. テストモードでない場合、必須フィールドのバリデーションを実行
    # 2. 馬の基本情報を準備し、データベースに保存
    # 3. オークション履歴情報を準備し、データベースに保存
    #
    # データ構造（horses.json）:
    # - id: 自動生成されるユニークID
    # - name: 馬名（必須）
    # - sex: 性別（牡・牝・セ）（必須）
    # - age: 年齢（必須）
    # - sire: 父馬名（必須）
    # - dam: 母馬名（必須）
    # - damsire: 母父名（空文字列の場合あり）
    # - image_url: 馬の画像URL
    # - jbis_url: JBISの詳細ページURL
    # - auction_url: オークションの詳細ページURL
    # - disease_tags: 疾病情報のタグ配列
    try:
        # テストモードでない場合のみバリデーションを実行
        if not test_mode:
            # 必須フィールドのバリデーション
            print("\n[デバッグ] 必須フィールドのバリデーションを開始します...")
            required_fields = ['name', 'sex', 'age', 'sire', 'dam', 'seller', 'auction_date']
            missing_fields = [field for field in required_fields if not horse_data.get(field)]

            # 各フィールドの値をデバッグ出力
            print("[デバッグ] 現在のフィールド値:")
            for field in required_fields + ['damsire']:
                print(f"  - {field}: '{horse_data.get(field, 'N/A')}' (型: {type(horse_data.get(field))})")

            # 販売者情報の確認（空または「不明」はエラー）
            seller = horse_data.get('seller', '').strip()
            if not seller or seller == '不明':
                return False, f"{horse_data['name']} - 販売者情報が正しく取得できませんでした"

            if missing_fields:
                return False, f"必須フィールドが不足しています: {', '.join(missing_fields)}"
        else:
            print("\n[デバッグ] テストモード: バリデーションをスキップします")

        # damsireが存在しない場合は空文字を設定
        if 'damsire' not in horse_data or not horse_data['damsire']:
            horse_data['damsire'] = ''
            horse_data['dam_sire'] = ''  # 互換性のため

        # 馬情報を準備
        print(f"\n[デバッグ] 馬情報を準備中: {horse_data.get('name', 'N/A')}")
        print(f"[デバッグ] disease_tags の型: {type(horse_data.get('disease_tags'))}, 値: {horse_data.get('disease_tags')}")

        # disease_tags が文字列の場合はリストに変換
        disease_tags = horse_data.get('disease_tags', [])
        if isinstance(disease_tags, str):
            print(f"[警告] disease_tags が文字列です。リストに変換します: {disease_tags}")
            # カンマ区切りの文字列をリストに変換
            disease_tags = [tag.strip() for tag in disease_tags.split(',') if tag.strip()]

        # 馬の基本情報を準備（テストモードではNoneを許容）
        horse_info = {
            'name': horse_data.get('name', ''),
            'sex': horse_data.get('sex', ''),
            'age': int(horse_data['age']) if horse_data.get('age') is not None else 0,
            'sire': horse_data.get('sire', ''),
            'dam': horse_data.get('dam', ''),
            'damsire': horse_data.get('damsire', ''),
            'image_url': horse_data.get('primary_image', ''),
            'jbis_url': horse_data.get('jbis_url', ''),
            'auction_url': horse_data.get('auction_url', horse_data.get('detail_url', '')),  # auction_urlがなければdetail_urlを使用
            'disease_tags': disease_tags,
            'weight': horse_data.get('weight', ''),
            'race_record': horse_data.get('race_record', ''),
            'comment': horse_data.get('comment', ''),
            'seller': horse_data.get('seller', ''),  # 販売者情報は必須（空の場合はエラー）
            'auction_date': horse_data.get('auction_date', ''),
            'total_prize_start': float(horse_data.get('total_prize_start', 0)) if horse_data.get('total_prize_start') else 0.0,
            'total_prize_latest': float(horse_data.get('total_prize_latest', 0)) if horse_data.get('total_prize_latest') else 0.0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        print(f"[デバッグ] 保存する馬情報: {json.dumps(horse_info, ensure_ascii=False, indent=2)}")

        # 馬情報を保存
        horse_id = save_horse(horse_info, data_dir)

        # オークション履歴を準備
        auction_info = {
            'horse_id': horse_id,
            'auction_date': horse_data['auction_date'],
            'sold_price': float(horse_data.get('sold_price', 0)) if horse_data.get('sold_price') else None,
            'total_prize_start': float(horse_data.get('total_prize_start', 0)) if horse_data.get('total_prize_start') else 0.0,
            'total_prize_latest': float(horse_data.get('total_prize_latest', 0)) if horse_data.get('total_prize_latest') else 0.0,
            'weight': float(horse_data.get('weight', 0)) if horse_data.get('weight') else None,
            'seller': horse_data['seller'],
            'is_unsold': bool(horse_data.get('is_unsold', False)),
            'comment': horse_data.get('comment', '')
        }

        # オークション履歴を保存
        save_auction_history(auction_info, data_dir)

        return True, f"{horse_data['name']} のデータを保存しました"
    except Exception as e:
        return False, f"データの保存中にエラーが発生しました: {str(e)}"

    print("\n===== スクレイピング結果 =====")
    print(f"成功: {success_count}件")
    print(f"失敗: {failed_count}件")
    print("===========================\n")

def main():
    # メイン実行関数
    import argparse

    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(description='楽天競馬オークション スクレイパー')
    parser.add_argument('--test', action='store_true', help='テストモードで実行（保存されたHTMLファイルを使用）')
    parser.add_argument('--cache-file', type=str, help='テストモードで使用するキャッシュファイルのパス')
    parser.add_argument('--save-html', action='store_true', help='HTMLをキャッシュに保存する')
    parser.add_argument('--no-save-html', action='store_false', dest='save_html', help='HTMLをキャッシュに保存しない')
    parser.set_defaults(save_html=True)
    args = parser.parse_args()

    # キャッシュファイルが指定されている場合はテストモードを有効にする
    if args.cache_file and not args.test:
        args.test = True

    scraper = None
    exit_code = 1  # デフォルトはエラー終了

    try:
        logger.info("楽天競馬オークション スクレイピングを開始します...")

        # データディレクトリのパスを設定
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              'static-frontend', 'public', 'data')
        os.makedirs(data_dir, exist_ok=True)

        # スクレイパーを初期化（タイムアウト30秒、最大3回リトライ）
        scraper = ImprovedRakutenScraper(
            timeout=30,
            max_retries=3,
            test_mode=args.test,
            cache_file=args.cache_file if hasattr(args, 'cache_file') else None
        )

        # オークション日を取得
        logger.info("オークション情報を取得中...")
        auction_date = scraper.get_auction_date()
        if not auction_date:
            logger.error("オークション日を取得できませんでした")
            return 1

        logger.info(f"オークション日: {auction_date}")

        # 全馬の情報を取得（キャッシュ保存の有無を指定）
        logger.info("馬の情報を取得中...")
        logger.info(f"キャッシュ保存: {'有効' if args.save_html else '無効'}")
        horses = scraper.scrape_all_horses(auction_date, save_html=args.save_html)

        if not horses:
            logger.error("馬の情報を取得できませんでした")
            return 1

        logger.info(f"\n===== スクレイピング結果 =====")
        logger.info(f"取得した馬の数: {len(horses)}")

        success_count = 0
        fail_count = 0

        # 各馬の情報を保存（進捗表示付き）
        for horse in tqdm(horses, desc="データを保存中", unit="件"):
            horse_name = horse.get('name', 'N/A')
            logger.debug(f"処理中: {horse_name}")

            try:
                # テストモードを渡して保存を試みる
                success, message = save_scraped_data(horse, data_dir, test_mode=args.test)
                if success:
                    success_count += 1
                    logger.debug(f"保存成功: {horse_name}")
                else:
                    fail_count += 1
                    logger.warning(f"保存失敗: {horse_name} - {message}")

                # サーバーに優しくするために少し待機
                time.sleep(0.5)

            except Exception as e:
                fail_count += 1
                logger.error(f"保存中にエラーが発生しました ({horse_name}): {str(e)}")
                continue

        # 結果をログに記録
        logger.info("\n===== 処理完了 =====")
        logger.info(f"成功: {success_count}件")
        logger.info(f"失敗: {fail_count}件")

        # 成功した場合のみ0を返す
        exit_code = 0 if success_count > 0 else 1

    except KeyboardInterrupt:
        logger.warning("\nユーザーによって処理が中断されました")
        exit_code = 130  # SIGINTの終了コード
    except Exception as e:
        logger.error(f"\n予期しないエラーが発生しました: {str(e)}", exc_info=True)
        exit_code = 1
    finally:
        # リソースのクリーンアップ
        if scraper and hasattr(scraper, 'session'):
            try:
                scraper.session.close()
                logger.info("セッションをクローズしました")
            except Exception as e:
                logger.error(f"セッションのクローズ中にエラーが発生しました: {str(e)}")

        logger.info("スクリプトを終了します")

        if args.test and exit_code == 0:
            logger.info("テストモードが正常に完了しました")
        elif args.test:
            logger.warning("テストモードでエラーが発生しました")

        return exit_code

if __name__ == "__main__":
    import sys
    sys.exit(main())
