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
from typing import List, Dict, Optional, Any, Tuple, Union, Match, Pattern, Set, Callable
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm
from pathlib import Path
import hashlib

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
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
    def __init__(self, timeout=30, max_retries=3, backoff_factor=1, test_mode=False, cache_file=None):
        self.base_url = "https://auction.keiba.rakuten.co.jp/"
        self.timeout = timeout
        self.test_mode = test_mode  # テストモードフラグを追加
        self.cache_file = cache_file  # テスト用キャッシュファイルのパス
        
        # セッションの初期化
        self.session = requests.Session()
        
        # リトライ設定
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        # アダプタの設定
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
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
        # キャッシュファイルにHTMLを保存
        # 引数:
        #   url: キャッシュするURL
        #   content: 保存するHTMLコンテンツ
        # 戻り値:
        #   Path: 保存されたキャッシュファイルのパス
        
        # URLから一意のファイル名を生成
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{url_hash}.html"
        filepath = CACHE_DIR / filename
        
        # ファイルに保存
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.debug(f"HTMLをキャッシュに保存しました: {filepath}")
        return filepath
        
    def _make_request(self, url: str, method: str = 'GET', 
                     save_html: bool = False, use_cache_on_error: bool = False, **kwargs) -> Optional[Union[requests.Response, str]]:
        # HTTPリクエストを送信し、必要に応じてキャッシュを使用する
        # 引数:
        #   url: リクエスト先のURL
        #   method: HTTPメソッド（デフォルト: 'GET'）
        #   save_html: レスポンスのHTMLをキャッシュに保存するかどうか
        #   use_cache_on_error: エラー時にキャッシュを使用するかどうか
        #   **kwargs: requests.request() に渡す追加引数
        # 戻り値:
        #   requests.Response: 成功時
        #   str: キャッシュ使用時またはエラー時のHTML文字列
        #   None: エラーでキャッシュも利用できない場合
        # テストモードまたはオフラインモードの場合はキャッシュを確認
        if self.test_mode or os.environ.get('SCRAPER_OFFLINE', '').lower() == 'true':
            logger.info(f"テスト/オフラインモードでリクエストを処理中: {url}")
            # キャッシュファイルが指定されている場合はそれを使用
            if self.cache_file and os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    logger.info(f"テストモード: 指定されたキャッシュファイルから読み込みました: {self.cache_file}")
                    # テスト用のResponseオブジェクトを返す
                    response = requests.Response()
                    response._content = content.encode('utf-8')
                    response.status_code = 200
                    response.headers = {'Content-Type': 'text/html; charset=utf-8'}
                    return response
            
            # テストモード用のファイル名を生成 (例: debug_horse_38.html など)
            test_file = None
            if 'horse_no=' in url:
                horse_no = url.split('horse_no=')[1].split('&')[0]
                test_file = f"debug_horse_{horse_no}.html"
            elif 'pedigree' in url and 'horse_id=' in url:
                horse_id = url.split('horse_id=')[1].split('&')[0]
                test_file = "debug_pedigree_page.html"
            elif 'auction.keiba.rakuten.co.jp' in url or 'horse_list' in url:
                # 馬リストページのテスト用ファイル - 新しいテストファイルを使用
                test_file = "test_horse_list.html"
                logger.info(f"テストモード: 馬リストページのテストファイルを使用: {test_file}")
            
            # テスト用ファイルが存在する場合はそれを使用
            if test_file and os.path.exists(test_file):
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    logger.info(f"テストモード: ローカルファイルから読み込みました: {test_file}")
                    # テスト用のResponseオブジェクトを返す
                    response = requests.Response()
                    response._content = content.encode('utf-8')
                    response.status_code = 200
                    response.headers = {'Content-Type': 'text/html; charset=utf-8'}
                    return response
            
            # テスト用ファイルがなければキャッシュを確認
            cache_files = list(CACHE_DIR.glob(f'*_{hashlib.md5(url.encode()).hexdigest()}.html'))
            if cache_files:
                # 最新のキャッシュを取得
                latest_cache = max(cache_files, key=os.path.getmtime)
                with open(latest_cache, 'r', encoding='utf-8') as f:
                    content = f.read()
                    logger.info(f"オフラインモード: キャッシュから読み込みました: {latest_cache}")
                    # テスト用のResponseオブジェクトを返す
                    response = requests.Response()
                    response._content = content.encode('utf-8')
                    response.status_code = 200
                    response.headers = {'Content-Type': 'text/html; charset=utf-8'}
                    return response
            
            logger.warning(f"テスト/オフラインモード: キャッシュが見つかりません: {url}")
            return None
        
        # 本番モード - 常に新しいリクエストを実行
        try:
            logger.info(f"本番モードでリクエストを送信: {url}")
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            
            # レスポンスをキャッシュに保存（明示的にsave_html=Trueが指定された場合のみ）
            if save_html and response.status_code == 200 and 'text/html' in response.headers.get('content-type', ''):
                self._save_html_to_cache(url, response.text)
                logger.debug(f"キャッシュを保存しました: {url}")
            elif not save_html:
                logger.debug(f"キャッシュ保存は無効化されています: {url}")
            
            return response
            
        except Exception as e:
            logger.error(f"リクエストエラー: {e}")
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

    def scrape_horse_list(self) -> List[Dict]:
        # トップページから馬のリストを取得
        # Returns:
        #   List[Dict]: 馬の基本情報（name, url, prize_money）のリスト
        logger.info("馬リストの取得を開始します...")
        
        response = self._make_request(self.base_url)
        if not response:
            logger.error("トップページの取得に失敗しました")
            return []
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 馬の情報を格納するリスト
        horse_links = []
        
        # 新しいHTML構造に対応したセレクタで馬の要素を取得
        horse_cards = soup.select('.auctionTableCard')
        
        for card in horse_cards:
            try:
                # 馬名を含む要素を取得
                name_elem = card.select_one('.auctionTableCard__name a')
                if not name_elem:
                    logger.debug("馬名要素が見つかりませんでした")
                    continue
                    
                # 馬の詳細ページURLを取得
                href = name_elem.get('href', '')
                if not href:
                    logger.debug(f"URLが見つかりません: {name_elem.get_text(strip=True)}")
                    continue
                    
                if not href.startswith('http'):
                    href = self.base_url + href.lstrip('/')
                
                # 馬名を取得（余分な空白を削除）
                name = name_elem.get_text(strip=True)
                if not name:  # 空の名前は無視
                    logger.debug("空の馬名をスキップします")
                    continue
                
                # 賞金情報を抽出
                prize_money = 0.0
                price_elem = card.select_one('.auctionTableCard__price .value')
                
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    logger.debug(f"賞金テキストを抽出: {price_text}")
                    
                    # 未出走馬の判定
                    if '未出走' in price_text:
                        prize_money = 0.0
                        logger.debug(f"未出走馬を検出: {name}")
                    else:
                        # 数値部分を抽出（例：「447.2万円」→「447.2」）
                        match = re.search(r'([\d,.]+)', price_text)
                        if match:
                            try:
                                prize_money = float(match.group(1).replace(',', ''))
                                logger.debug(f"賞金を抽出: {prize_money}万円")
                            except (ValueError, AttributeError) as e:
                                logger.warning(f"賞金の抽出に失敗しました: {e}")
                
                # 馬の情報を辞書に格納
                horse_info = {
                    'name': name,
                    'url': href,
                    'prize_money': prize_money
                }
                
                horse_links.append(horse_info)
                logger.debug(f"馬情報を追加: {name} - 賞金: {prize_money}万円 - URL: {href}")
                
            except Exception as e:
                logger.error(f"馬情報の抽出中にエラーが発生しました: {e}")
                continue
        
        logger.info(f"馬リストの取得が完了しました。{len(horse_links)}頭の馬を取得しました。")
        return horse_links
    
    def _extract_seller(self, soup: BeautifulSoup) -> str:
        # 販売者情報を抽出する
        # 
        # Args:
        #     soup: BeautifulSoupオブジェクト
        #     
        # Returns:
        #     str: 販売者名。見つからない場合は空文字列
        try:
            # preタグ内のテキストを取得
            pre_tag = soup.find('pre', style=re.compile(r'white-space: pre-wrap;'))
            if not pre_tag:
                logger.warning("コメントを含むpreタグが見つかりませんでした")
                return ""
                
            comment_text = pre_tag.get_text()
            
            # 「販売申込人：」または「販売申込者：」のパターンにマッチ
            seller_match = re.search(r'販売申込[者人][：:]([^\n（(]+)', comment_text)
            if seller_match:
                seller = seller_match.group(1).strip()
                logger.debug(f"抽出した販売者情報: {seller}")
                return seller
                
            logger.warning("販売者情報が見つかりませんでした")
            return ""
            
        except Exception as e:
            logger.error(f"販売者情報の抽出中にエラーが発生しました: {e}")
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
                r'落札価格[^\d]*([\d,]+)',  # 「落札価格」の後に数値が続くパターン
                r'([\d,]+)\s*円',           # 「123,456円」形式
                r'([\d,]+)\s*万円',         # 「123,456万円」形式
            ]
            
            text = soup.get_text()
            for pattern in price_patterns:
                match = re.search(pattern, text)
                if match:
                    try:
                        # 単純に数値のみを抽出（単位変換は行わない）
                        price = int(match.group(1).replace(',', ''))
                        logger.debug(f"正規表現で落札価格を抽出: {price} (パターン: {pattern})")
                        return price
                    except (ValueError, IndexError):
                        continue
            
            logger.warning("落札価格を見つけることができませんでした")
            return None
            
        except Exception as e:
            logger.error(f"落札価格の抽出中にエラーが発生しました: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
            
    def _extract_name_sex_age(self, page_text: str) -> Dict[str, Any]:
        # 馬名、性別、年齢を抽出する
        # 
        # フォーマット例:
        # - "アイドルフェスタ　　牝３歳　　※中央競馬　登録抹消"
        # - "馬名　牡5歳　コメント"
        # - "馬名　セン馬　3歳"
        # 
        # Args:
        #     page_text: 抽出元のページのテキスト
        #     
        # Returns:
        #     Dict[str, Any]: 抽出した情報（name, sex, age）
        result = {
            'name': '',
            'sex': '',
            'age': None
        }
        
        try:
            # デバッグ用: 入力テキストの先頭200文字をログに出力
            logger.debug(f"抽出対象テキスト: {page_text[:200]}...")
            
            # パターン1: 性別と年齢が続いている場合（例: "馬名　牡5歳"）
            pattern1 = r'([^\s　]+?)\s*([牡牝セ])(\d+)歳'
            match1 = re.search(pattern1, page_text)
            
            if match1:
                result['name'] = match1.group(1).strip()
                result['sex'] = match1.group(2).strip()
                result['age'] = int(match1.group(3))
                logger.debug(f"パターン1にマッチ: name={result['name']}, sex={result['sex']}, age={result['age']}")
                return result
            
            # パターン2: 性別と年齢が分かれている場合（例: "馬名　牡　5歳"）
            pattern2 = r'([^\n\r\t]+?)\s+([牡牝セ])\s*(\d+)歳'
            match2 = re.search(pattern2, page_text)
            
            if match2:
                result['name'] = match2.group(1).strip()
                result['sex'] = match2.group(2).strip()
                result['age'] = int(match2.group(3))
                logger.debug(f"パターン2にマッチ: name={result['name']}, sex={result['sex']}, age={result['age']}")
                return result
            
            # パターン3: セン馬の場合（例: "馬名　セン馬　3歳"）
            pattern3 = r'([^\s　]+?)\s*セン[馬\s]*(\d+)歳'
            match3 = re.search(pattern3, page_text)
            
            if match3:
                result['name'] = match3.group(1).strip()
                result['sex'] = 'セ'  # セン馬は「セ」として扱う
                result['age'] = int(match3.group(2))
                logger.debug(f"パターン3（セン馬）にマッチ: name={result['name']}, sex={result['sex']}, age={result['age']}")
                return result
            
            # デバッグ用にマッチしなかったテキストをログに出力
            logger.warning(f"性別・年齢のパターンにマッチしませんでした。テキスト: {page_text[:200]}...")
            
            # マッチしなかった場合のフォールバック処理
            # 例: 「馬名　3歳」のような形式を想定
            fallback_pattern = r'([^\s　]+?)\s*(\d+)歳'
            fallback_match = re.search(fallback_pattern, page_text)
            
            if fallback_match:
                result['name'] = fallback_match.group(1).strip()
                # 性別は空文字のまま（デフォルト値は設定しない）
                result['age'] = int(fallback_match.group(2))
                logger.warning(f"フォールバックパターンにマッチ（性別不明）: name={result['name']}, age={result['age']}")
        
        except Exception as e:
            logger.error(f"馬名・性別・年齢の抽出中にエラーが発生しました: {e}")
            logger.error(traceback.format_exc())
        
        return result
    
    def scrape_horse_detail(self, detail_url: str, prize_money: float = None, save_html: bool = False) -> Optional[Dict]:
        # 個別ページから詳細情報を取得
        # 
        # Args:
        #     detail_url: 詳細ページのURL
        #     prize_money: 一覧ページから取得した賞金情報（オプション）
        #     save_html: HTMLをキャッシュに保存するかどうか
        # 
        # Returns:
        #     Optional[Dict]: 抽出した詳細情報。エラーの場合はNone
        try:
            # リクエストを送信
            response = self._make_request(detail_url, save_html=save_html)
            if not response:
                logger.error(f"リクエストに失敗しました: {detail_url}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text()
            
            # 基本情報を取得
            detail_data = self._extract_name_sex_age(page_text)
            
            # 血統情報を取得 (page_textを渡す)
            pedigree_data = self._extract_pedigree(page_text)
            detail_data.update(pedigree_data)
            
            # オークション時の賞金はリストページの値を使用（必ず設定）
            auction_prize = float(prize_money) if prize_money is not None else 0.0
            
            # 現在の賞金は一旦0.0で初期化（後でJBISから取得）
            current_prize = 0.0
            
            # JBIS URLが存在する場合は最新の賞金情報を取得
            jbis_url = self._extract_jbis_url(soup)
            if jbis_url:
                try:
                    current_prize = self._extract_jbis_prize_money(jbis_url)
                    logger.debug(f"JBISから最新の賞金を取得: {current_prize}万円")
                except Exception as e:
                    logger.warning(f"JBISからの賞金取得中にエラーが発生しました: {str(e)}")
            
            # その他の情報を取得
            detail_data.update({
                'sold_price': self._extract_sold_price(soup),
                'weight': self._extract_weight(page_text),
                'race_record': self._extract_race_record(page_text),
                'comment': self._extract_comment(page_text),
                'disease_tags': self._extract_disease_tags(detail_data.get('comment', '')),
                'primary_image': self._extract_primary_image(soup),
                'seller': self._extract_seller(page_text),
                'jbis_url': jbis_url,
                'detail_url': detail_url,  # 詳細ページのURLを保存
                'total_prize_start': auction_prize,  # オークション時の賞金（リストページから）
                'total_prize_latest': current_prize  # 現在の賞金（JBISから）
            })
            
            # オークション日を設定
            detail_data['auction_date'] = self.get_auction_date() or datetime.now().strftime('%Y-%m-%d')
            
            # デバッグ情報をログに出力
            logger.debug(f"抽出した詳細情報: {json.dumps(detail_data, ensure_ascii=False, indent=2)}")
            
            return detail_data
            
        except Exception as e:
            logger.error(f"詳細情報の抽出中にエラーが発生しました ({detail_url}): {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _clean_horse_name(self, name: str) -> str:
        # 馬名をクリーンアップするヘルパー関数
        # 
        # Args:
        #     name: クリーンアップする馬名（「父：サクラバクシンオー 母：**」のような形式）
        #     
        # Returns:
        #     クリーンアップされた馬名（省略なし）
        if not name:
            return ''
            
        original_name = name
        
        # 不要な空白と改行を削除
        name = re.sub(r'\s+', ' ', name.strip())
        
        # 「父：」や「母：」で始まる場合はその部分を削除
        name = re.sub(r'^[父母]\s*[：:]\s*', '', name)
        
        # 先頭の全角スペースを削除
        name = name.lstrip('　')
        
        # 括弧内の文字列を削除（例：アラバスター（JPN）→ アラバスター）
        name = re.sub(r'\s*[（(].*?[)）]', '', name)
        
        # 不要な記号を削除
        name = re.sub(r'[\[\]()（）【】]', '', name)
        
        # 不要な接頭語を削除
        name = re.sub(r'^[\s　]*(?:父|母|母父|母の父)[\s　]*[：:][\s　]*', '', name)
        
        # 通算成績や賞金情報が含まれる場合（例：「オレハマッテルゼ 通算成績：5戦0勝」）
        name = re.split(r'\s+通算成績|\s+獲得賞金|\s+最終出走|\s+競走成績|\s*[0-9]+戦[0-9]+勝', name)[0]
        
        # 先頭と末尾の空白を削除
        name = name.strip()
        
        # 馬名が1文字以下の場合は空文字を返す
        if len(name) <= 1:
            return ''
            
        # 7. 元の名前に「...」が含まれていて、処理後に消えている場合は元に戻す
        if '...' in original_name and '...' not in name:
            name = original_name
        
        # デバッグ用に変更前後の名前を出力
        if name != original_name.strip():
            print(f"[デバッグ] 名前を正規化: '{original_name}' -> '{name}'")
            
        return name

    def _extract_pedigree(self, page_text: str) -> Dict:
        # 血統情報を抽出・正規化
        # 
        # Args:
        #     page_text: 抽出元のHTMLテキスト
        #     
        # Returns:
        #     Dict: 抽出した血統情報（sire, dam, damsire, dam_sire を含む）
        result = {
            'sire': '',
            'dam': '',
            'damsire': '',
            'dam_sire': ''
        }
        
        try:
            logger.debug("=== 血統情報抽出開始 ===")
            
            # まずBeautifulSoupでパース
            soup = BeautifulSoup(page_text, 'html.parser')
            
            # 1. 血統情報が含まれている可能性のある要素を検索
            possible_elements = []
            
            # preタグを検索
            pre_tags = soup.find_all('pre')
            for pre in pre_tags:
                text = pre.get_text(strip=False)
                if any(keyword in text for keyword in ['父：', '母：', '母の父：', '父:', '母:', '母の父:']):
                    possible_elements.append(('pre', text))
            
            # div.horse-info を検索
            horse_info = soup.find('div', class_='horse-info')
            if horse_info:
                possible_elements.append(('div.horse-info', horse_info.get_text(strip=False)))
            
            # テーブル内の血統情報を検索
            tables = soup.find_all('table')
            for i, table in enumerate(tables):
                table_text = table.get_text(strip=True)
                if any(keyword in table_text for keyword in ['父：', '母：', '母の父：', '父:', '母:', '母の父:']):
                    possible_elements.append((f'table-{i}', table_text))
            
            # 見つかった要素から血統情報を抽出
            for elem_type, text in possible_elements:
                logger.debug(f"[{elem_type}] 血統情報候補テキスト: {text[:200]}...")
                
                # テキストを正規化
                normalized_text = re.sub(r'[\s　]+', ' ', text.strip())
                
                # 血統情報の抽出を試みる
                self._extract_from_text(normalized_text, result)
                
                # すべての情報が取得できた場合は終了
                if result.get('sire') and result.get('dam') and result.get('damsire'):
                    break
            
            # それでも取得できない場合、ページ全体から抽出を試みる
            if not result.get('sire') or not result.get('dam') or not result.get('damsire'):
                logger.debug("通常の抽出方法では不十分なため、ページ全体から抽出を試みます")
                full_text = soup.get_text(strip=False)
                normalized_full_text = re.sub(r'[\s　]+', ' ', full_text.strip())
                self._extract_from_text(normalized_full_text, result)
            
            # 互換性のため dam_sire にも damsire と同じ値を設定
            if result.get('damsire') and not result.get('dam_sire'):
                result['dam_sire'] = result['damsire']
            
            logger.info(f"抽出された血統情報: sire='{result.get('sire', '')}', dam='{result.get('dam', '')}', damsire='{result.get('damsire', '')}'")
            
        except Exception as e:
            logger.error(f"血統情報の抽出中にエラーが発生しました: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return result
    
    def _extract_from_text(self, text: str, result: Dict) -> None:
        # テキストから血統情報を抽出して結果辞書を更新
        # 
        # Args:
        #     text: 抽出元のテキスト
        #     result: 結果を格納する辞書
        try:
            # テキストをログに出力して確認
            logger.debug(f"[血統抽出] 抽出対象テキスト: {text}")
            
            # テキストを正規化（全角スペースを半角に変換、連続するスペースを1つに）
            normalized_text = re.sub(r'[\s　]+', ' ', text.strip())
            logger.debug(f"[血統抽出] 正規化済みテキスト: {normalized_text}")
            
            # 1. まず「父：～ 母：～ 母の父：～」の形式で全体を取得
            # 全角・半角の区切り文字に対応し、馬名に全角スペースが含まれる場合も対応
            full_patterns = [
                r'父[：:]([^\s　]+(?:[\s　]+[^\s　]+)*?)\s+母[：:]([^\s　]+(?:[\s　]+[^\s　]+)*?)(?:\s+(?:母の?父|母父)[：:]([^\s　]+(?:[\s　]+[^\s　]+)*))?',
                r'父[：:]([^\s　]+(?:[\s　]+[^\s　]+)*?)[\s　]+母[：:]([^\s　]+(?:[\s　]+[^\s　]+)*?)(?:[\s　]+(?:母の?父|母父)[：:]([^\s　]+(?:[\s　]+[^\s　]+)*))?',
                r'父[：:]([^\s　]+(?:[\s　]+[^\s　]+)*?)[\s　]*母[：:]([^\s　]+(?:[\s　]+[^\s　]+)*?)(?:[\s　]*(?:母の?父|母父)[：:]([^\s　]+(?:[\s　]+[^\s　]+)*))?'
            ]
            
            for pattern in full_patterns:
                match = re.search(pattern, normalized_text)
                if match:
                    result['sire'] = self._clean_horse_name(match.group(1)) if match.group(1) else ''
                    result['dam'] = self._clean_horse_name(match.group(2)) if match.group(2) else ''
                    result['damsire'] = self._clean_horse_name(match.group(3)) if match.group(3) else ''
                    result['dam_sire'] = result['damsire']  # 互換性のため
                    
                    # 馬名が1文字の場合は無効とみなす
                    if len(result['sire']) < 2:
                        result['sire'] = ''
                    if len(result['dam']) < 2:
                        result['dam'] = ''
                    if len(result['damsire']) < 2:
                        result['damsire'] = ''
                        result['dam_sire'] = ''
                    
                    logger.info(f"完全な血統情報を抽出: sire='{result['sire']}', dam='{result['dam']}', damsire='{result['damsire']}'")
                    return
            
            # 2. 完全な形式で取得できない場合、個別に抽出を試みる
            logger.debug("完全な血統情報の取得に失敗、個別に抽出を試みます")
            
            # 父馬の抽出
            if not result.get('sire'):
                sire_match = re.search(r'父[：:]([^\s　]+(?:[\s　]+[^\s　]+)*)', normalized_text)
                if sire_match:
                    result['sire'] = self._clean_horse_name(sire_match.group(1))
                    if len(result['sire']) < 2:
                        result['sire'] = ''
                    else:
                        logger.info(f"個別に父馬を抽出: {result['sire']}")
            
            # 母馬の抽出
            if not result.get('dam'):
                dam_match = re.search(r'母[：:]([^\s　]+(?:[\s　]+[^\s　]+)*)', normalized_text)
                if dam_match:
                    result['dam'] = self._clean_horse_name(dam_match.group(1))
                    if len(result['dam']) < 2:
                        result['dam'] = ''
                    else:
                        logger.info(f"個別に母馬を抽出: {result['dam']}")
            
            # 母父馬の抽出
            if not result.get('damsire'):
                # テキストを改行で分割して1行ずつ処理
                for line in text.split('\n'):
                    line = line.strip()
                    # 母の父を含む行を探す
                    if '母の父' in line or '母父' in line:
                        # パターン1: 「母の父：馬名」の形式
                        match = re.search(r'(?:母の?父|母父)[：:]([^\s　\[（(]+)', line)
                        if match:
                            damsire_name = match.group(1).strip()
                            # 不要な文字を除去
                            damsire_name = re.sub(r'[\[\]()（）【】]', '', damsire_name)
                            # 馬名として有効な文字列か確認
                            if len(damsire_name) >= 2 and not any(c in damsire_name for c in ['通算', '成績', '獲得', '賞金']):
                                result['damsire'] = self._clean_horse_name(damsire_name)
                                result['dam_sire'] = result['damsire']
                                logger.info(f"母父馬を抽出: '{result['damsire']}'")
                                break
                        
                        # パターン2: 母の父の後に改行がある場合
                        next_line = text[text.find(line) + len(line):].strip().split('\n')[0].strip()
                        if next_line and not any(c in next_line for c in ['：', ':', '通算', '成績']):
                            result['damsire'] = self._clean_horse_name(next_line.split()[0])
                            result['dam_sire'] = result['damsire']
                            logger.info(f"母父馬を抽出（改行後）: '{result['damsire']}'")
                            break
                
                # それでも見つからない場合は空文字を設定
                if 'damsire' not in result or not result['damsire']:
                    logger.warning(f"母父馬の抽出に失敗しました: {normalized_text[:100]}...")
                    result['damsire'] = ''
                    result['dam_sire'] = ''
            
            # 互換性のため dam_sire にも damsire と同じ値を設定
            if not result.get('dam_sire') and result.get('damsire'):
                result['dam_sire'] = result['damsire']
                
        except Exception as e:
            logger.error(f"血統情報の抽出中にエラーが発生しました: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        if match:
            groups = match.groups()
            logger.debug(f"血統情報を検出: {groups}")
            
            # 父馬の抽出
            if not result['sire'] and groups[0]:
                result['sire'] = self._clean_horse_name(groups[0].strip())
                logger.debug(f"父馬を抽出: {result['sire']}")
            
            # 母馬の抽出
            if not result['dam'] and len(groups) > 1 and groups[1]:
                result['dam'] = self._clean_horse_name(groups[1].strip())
                logger.debug(f"母馬を抽出: {result['dam']}")
            
            # 母父馬の抽出
            if not result['damsire'] and len(groups) > 2 and groups[2]:
                result['damsire'] = self._clean_horse_name(groups[2].strip())
                logger.debug(f"母父馬を抽出: {result['damsire']}")
        else:
            # 全体マッチしなかった場合、個別に抽出を試みる
            logger.debug("完全な血統情報の取得に失敗、個別に抽出を試みます")
            
            # 父馬の抽出
            if not result['sire']:
                sire_match = re.search(r'父[：:]([^\s　\n]+)', text)
                if sire_match:
                    result['sire'] = self._clean_horse_name(sire_match.group(1).strip())
                    logger.debug(f"個別に父馬を抽出: {result['sire']}")
            
            # 母馬の抽出
            if not result['dam']:
                dam_match = re.search(r'母[：:]([^\s　\n]+)', text)
                if dam_match:
                    result['dam'] = self._clean_horse_name(dam_match.group(1).strip())
                    logger.debug(f"個別に母馬を抽出: {result['dam']}")
            
            # 母父馬の抽出
            if not result['damsire']:
                damsire_match = re.search(r'(?:母の?父|母父)[：:]([^\s　\n]+)', text)
                if damsire_match:
                    result['damsire'] = self._clean_horse_name(damsire_match.group(1).strip())
                    logger.debug(f"個別に母父馬を抽出: {result['damsire']}")
        
        # 互換性のため dam_sire にも damsire と同じ値を設定
        if result['damsire'] and not result['dam_sire']:
            result['dam_sire'] = result['damsire']
        
        # 互換性のため dam_sire にも damsire と同じ値を設定
        if result['damsire'] and not result['dam_sire']:
            result['dam_sire'] = result['damsire']
    
    def _extract_weight(self, page_text: str) -> Optional[int]:
        # ページテキストから馬体重を抽出します。
        # 
        # 以下のパターンに対応します:
        # - 「最終出走馬体重：XXXkg」形式
        # - 「馬体重：XXXkg」形式
        # - 数値部分のみを返す（単位「kg」は含めない）
        # 
        # Args:
        #     page_text (str): 抽出元のHTMLテキスト
        #     
        # Returns:
        #     Optional[int]: 抽出された馬体重（kg）。見つからない場合はNoneを返します。
        #     
        # Note:
        #     正規表現を使用して馬体重情報を抽出します。
        #     数値が不正な場合は警告を出力し、Noneを返します。
        # "最終出走馬体重：XXXkg" を探す
        patterns = [
            r'最終出走馬体重[：:]\s*(\d+)kg',
            r'馬体重[：:]\s*(\d+)kg',
            r'(?:馬体重|体重)[：:](?:\s*<[^>]+>)*\s*(\d+)\s*kg'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_text)
            if match:
                try:
                    weight = int(match.group(1))
                    if 300 <= weight <= 600:  # 馬の体重として妥当な範囲かチェック
                        return weight
                    else:
                        logger.warning(f'Invalid weight value detected: {weight}kg')
                except (ValueError, IndexError) as e:
                    logger.warning(f'Error parsing weight: {e}')
                    continue
        
        # どのパターンにもマッチしなかった場合
        return None
        
    def _extract_race_record(self, page_text: str) -> str:
        # 馬の戦績を抽出します。
        # 
        # 「通算成績：5戦0勝［0-0-0-5］」形式の戦績を抽出します。
        # 前後に他の情報が続く場合も含めて抽出可能です。
        # 
        # Args:
        #     page_text (str): 抽出元のHTMLテキスト
        #     
        # Returns:
        #     str: 戦績文字列（例: "5戦0勝[0-0-0-5]"）。抽出できない場合は空文字列を返します。
        if not page_text or not isinstance(page_text, str):
            logger.warning("[戦績抽出] ページテキストが空または無効です")
            return ""
            
        try:
            logger.debug("[戦績抽出] 戦績抽出を開始します")
            
            # テキストを正規化（改行をスペースに置換、連続する空白を1つに）
            normalized_text = re.sub(r'\s+', ' ', page_text.replace('\n', ' ').replace('\r', ' '))
            
            # 戦績パターン（「通算成績：X戦Y勝［W-P-L-F］」形式）
            pattern = r'通算成績[：:](?:\s|　)*(\d+戦\d+勝)\s*［([\d\-]+)］'
            
            # パターンマッチを試行
            match = re.search(pattern, normalized_text)
            if match:
                # マッチしたグループを取得（グループ1: 戦績、グループ2: 内訳）
                record = match.group(1).strip()
                details = match.group(2).strip()
                
                # 内訳の形式を正規化（全角ハイフンや全角数字を半角に）
                details = details.replace('－', '-').replace('ー', '-')
                details = re.sub(r'[^0-9\-]', '', details)  # 数字とハイフン以外を除去
                
                # 結果を整形（例：「5戦0勝[0-0-0-5]」）
                result = f"{record}[{details}]"
                
                # デバッグログ
                start = max(0, match.start() - 30)
                end = min(len(normalized_text), match.end() + 30)
                context = normalized_text[start:end]
                logger.debug(f"[戦績抽出] 戦績を検出: '{result}' 前後のテキスト: ...{context}...")
                
                return result
            
            # デバッグ用：キーワード周辺のテキストをログ出力
            for keyword in ['通算成績', '戦', '勝']:
                idx = normalized_text.find(keyword)
                if idx >= 0:
                    start_idx = max(0, idx - 30)
                    end_idx = min(len(normalized_text), idx + 50)
                    logger.debug(f"[戦績抽出] キーワード '{keyword}' 周辺のテキスト: ...{normalized_text[start_idx:end_idx]}...")
            
            logger.debug("[戦績抽出] 戦績情報を検出できませんでした")
            return ""
            
        except Exception as e:
            error_msg = f"[戦績抽出] エラーが発生しました: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return ""

    def _extract_prize_money(self, page_text: str, jbis_url: Optional[str] = None) -> Dict[str, float]:
        # 賞金情報を抽出します。
        # 
        # Args:
        #     page_text: 抽出元のHTMLテキスト
        #     jbis_url: JBISのURL（指定すると最新の賞金情報を取得）
        #     
        # Returns:
        #     賞金情報を含む辞書。キーは'total_prize_start'と'total_prize_latest'。
        result = {
            'total_prize_start': 0.0,
            'total_prize_latest': 0.0
        }
        
        if not page_text:
            logger.warning("ページテキストが空です")
            return result
            
        try:
            logger.debug("賞金情報の抽出を開始")
            
            # 中央・地方・総獲得賞金のパターンを検索（必ず「万円」表記を要求）
            central_prize_match = re.search(r'中央獲得賞金[：:](?:\s|　)*([\d,.]+)(?:\s|　)*万円', page_text)
            local_prize_match = re.search(r'地方獲得賞金[：:](?:\s|　)*([\d,.]+)(?:\s|　)*万円', page_text)
            total_prize_match = re.search(r'総獲得賞金[：:](?:\s|　)*([\d,.]+)(?:\s|　)*万円', page_text)
            
            # デバッグ情報
            debug_info = {
                '中央賞金': central_prize_match.group(1) if central_prize_match else 'なし',
                '地方賞金': local_prize_match.group(1) if local_prize_match else 'なし',
                '総獲得賞金': total_prize_match.group(1) if total_prize_match else 'なし'
            }
            logger.debug(f"賞金情報マッチ: {debug_info}")
            
            # 総賞金を設定
            if total_prize_match:
                prize_value = total_prize_match.group(1).replace(',', '')
                result['total_prize_start'] = float(prize_value)
                logger.debug(f"総賞金を検出: {prize_value}万円")
            elif central_prize_match or local_prize_match:
                logger.debug("総賞金のマッチに失敗。中央・地方賞金から計算します。")
                central = float(central_prize_match.group(1).replace(',', '')) if central_prize_match else 0.0
                local = float(local_prize_match.group(1).replace(',', '')) if local_prize_match else 0.0
                result['total_prize_start'] = central + local
                logger.debug(
                    f"中央賞金: {central}万円, "
                    f"地方賞金: {local}万円, "
                    f"合計: {result['total_prize_start']}万円"
                )
            else:
                logger.warning("有効な賞金情報が見つかりませんでした")
            
            # JBISから最新の賞金情報を取得
            if jbis_url:
                logger.debug(f"JBISから最新の賞金情報を取得: {jbis_url}")
                try:
                    latest_prize = self._extract_jbis_prize_money(jbis_url)
                    result['total_prize_latest'] = latest_prize if latest_prize > 0 else result['total_prize_start']
                    logger.debug(f"JBISから取得した最新賞金: {latest_prize}万円")
                except Exception as e:
                    logger.warning(f"JBISからの賞金取得に失敗: {e}")
                    result['total_prize_latest'] = result['total_prize_start']
            else:
                result['total_prize_latest'] = result['total_prize_start']
            
            logger.debug(
                f"賞金情報 - オークション時: {result['total_prize_start']}万円, "
                f"最新: {result['total_prize_latest']}万円"
            )
            
        except Exception as e:
            logger.error(f"賞金情報の抽出に失敗: {e}")
            logger.error(traceback.format_exc())
        
        return result
    
    def _extract_comment(self, page_text: str) -> str:
        # コメントを抽出します。
        # Args:
        #   page_text: 抽出元のHTMLテキスト
        # Returns:
        #   抽出したコメントテキスト。見つからない場合は空文字列。
        try:
            # "本馬について" の後のテキストを探す
            comment_match = re.search(r'本馬について(.+?)(?=\n\n|\n販売申込者|$)', 
                                   page_text, re.DOTALL)
            if comment_match:
                return comment_match.group(1).strip()
            return ""
        except Exception as e:
            logger.error(f"コメントの抽出中にエラーが発生しました: {e}")
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
    
    def _extract_seller(self, page_text: str) -> str:
        # 販売申込者を抽出
        # 
        # Returns:
        #     str: 販売者名（「インボイス登録あり」のテキストは削除）
        seller_match = re.search(r'販売申込者[：:]\s*([^\n]+)', page_text)
        if seller_match:
            seller = seller_match.group(1).strip()
            # 「（インボイス登録あり）」を削除
            seller = re.sub(r'\s*[(（]インボイス登録あり[)）]', '', seller)
            return seller.strip()
        return ""
    
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

    def scrape_all_horses(self, auction_date: str = None, save_html: bool = False) -> List[Dict]:
        # 全馬の情報を取得
        # 
        # Args:
        #     auction_date: オークション日（指定がない場合は自動取得）
        #     save_html: HTMLをキャッシュに保存するかどうか
        #     
        # Returns:
        #     List[Dict]: 各馬の詳細情報のリスト
        if not auction_date:
            auction_date = self.get_auction_date()
        
        print(f"オークション日: {auction_date}")
        
        # 馬の一覧を取得（賞金情報付き）
        horse_links = self.scrape_horse_list()
        print(f"{len(horse_links)}頭の馬を発見しました。")
        
        horses = []
        
        # 進行状況を表示するための設定
        with tqdm(total=len(horse_links), desc="馬の詳細を取得中", unit="頭") as pbar:
            for link in horse_links:
                try:
                    try:
                        # 一覧ページから取得した賞金情報を渡して詳細情報を取得
                        detail_url = link['url']
                        prize_money = link.get('prize_money')
                        
                        # 詳細情報を取得
                        detail_data = self.scrape_horse_detail(detail_url, prize_money=prize_money, save_html=save_html)
                        
                        if detail_data:
                            # オークション日を設定
                            detail_data['auction_date'] = auction_date
                            
                            # テストモードの場合は必須フィールドのチェックをスキップ
                            if self.test_mode and not all(key in detail_data for key in ['name', 'sex', 'age', 'seller']):
                                logger.warning(f"テストモード: 必須フィールドが不足していますが、スキップします - {detail_url}")
                                continue
                                
                            horses.append(detail_data)
                            
                            # デバッグ情報を出力
                            logger.debug(f"馬の詳細を取得: {detail_data.get('name')} - 賞金: {prize_money}万円")
                        
                    except Exception as e:
                        if self.test_mode:
                            logger.warning(f"テストモード: 詳細ページの取得に失敗しましたが、スキップします - {link.get('url', 'URL不明')}: {str(e)}")
                            continue
                        else:
                            raise
                    
                except Exception as e:
                    logger.error(f"馬の詳細取得中にエラーが発生しました ({link.get('text', '不明')}): {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                # 進捗を更新
                pbar.update(1)
                
                # サーバーに負荷をかけないように少し待機
                time.sleep(1)
        
        print(f"\n{len(horses)}頭の馬の詳細を取得しました。")
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
            'auction_url': horse_data.get('detail_url', ''),
            'disease_tags': disease_tags,
            'weight': horse_data.get('weight', ''),
            'race_record': horse_data.get('race_record', ''),
            'comment': horse_data.get('comment', ''),
            'seller': horse_data.get('seller', ''),
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
    parser.add_argument('--save-html', action='store_true', help='HTMLをキャッシュに保存する（デフォルト: 保存しない）')
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