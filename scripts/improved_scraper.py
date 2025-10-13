#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
楽天競馬オークションのスクレイピングスクリプト

このスクリプトは、楽天競馬オークションのデータをスクレイピングし、構造化されたデータとして保存します。
"""

import argparse
import functools
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import time
import uuid
import traceback
import random
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, parse_qs, urlunparse

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 共通ユーティリティのインポート
try:
    from scripts.utils.common import (
        setup_logging,
        save_to_json,
        load_from_json,
        get_file_hash,
        ensure_directory
    )
    COMMON_UTILS_AVAILABLE = True
except ImportError:
    COMMON_UTILS_AVAILABLE = False
    
    # フォールバック用の簡易実装
    def setup_logging(*args, **kwargs):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def save_to_json(data, file_path, **kwargs):
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, **kwargs)
    
    def load_from_json(file_path):
        file_path = Path(file_path)
        if not file_path.exists():
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_file_hash(file_path):
        import hashlib
        file_path = Path(file_path)
        if not file_path.exists():
            return ""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def ensure_directory(directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

# バックエンドモジュールのインポート状態
BACKEND_AVAILABLE = False

# ロガーの設定
logger = logging.getLogger(__name__)

# 馬データを保存する関数
def save_horse(horse_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    馬データをJSONファイルに保存する
    
    Args:
        horse_data: 保存する馬データの辞書
        
    Returns:
        Dict: 保存結果を含む辞書
    """
    try:
        # 保存先ファイルパス
        json_file = Path('static-frontend/public/data/horses.json')
        
        # 必須フィールドが存在することを確認
        required_fields = ['id', 'name', 'sex', 'age', 'sire', 'dam', 'damsire', 'jbis_url']
        for field in required_fields:
            if field not in horse_data or not horse_data[field]:
                horse_data[field] = ''  # 必須フィールドがなければ空文字を設定
        
        # 既存のデータを読み込む（存在する場合）
        existing_data = []
        metadata = {}
        
        if json_file.exists():
            data = load_from_json(json_file)
            if isinstance(data, dict) and 'horses' in data:
                existing_data = data['horses']
                metadata = data.get('metadata', {})
            elif isinstance(data, list):
                existing_data = data
        
        # メタデータを更新
        metadata.update({
            'version': '1.0',
            'last_updated': datetime.now().isoformat(),
            'total_horses': len(existing_data) + (0 if horse_data.get('id') in 
                                [h.get('id') for h in existing_data if isinstance(h, dict)] else 1)
        })
        
        # 馬IDが指定されていない場合はエラー
        horse_id = horse_data.get('id')
        if not horse_id:
            error_msg = "馬IDが指定されていません。オークションページのIDを指定してください"
            logger.error(error_msg)
            return {'error': error_msg}
            
        # 数値IDに変換（文字列の場合は数値に、既に数値の場合はそのまま）
        try:
            horse_id = str(int(horse_id))  # 数値に変換してから文字列に
            horse_data['id'] = horse_id
        except (ValueError, TypeError) as e:
            error_msg = f"無効な馬ID形式です: {horse_id}"
            logger.error(error_msg, exc_info=True)
            return {'error': error_msg}
        
        # 既存の馬データを更新または新規追加
        updated = False
        for i, horse in enumerate(existing_data):
            if str(horse.get('id')) == str(horse_id):
                # 既存の馬データを更新（IDはそのまま）
                existing_data[i].update(horse_data)
                updated = True
                break
                
        if not updated:
            # 新しい馬データを追加
            existing_data.append(horse_data)
        
        # データを新しい形式で保存
        data_to_save = {
            'metadata': metadata,
            'horses': existing_data
        }
        
        # 一時ファイルに保存してからリネーム（アトミックな書き込みのため）
        temp_file = json_file.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        
        # アトミックなリネーム
        temp_file.replace(json_file)
        
        print(f"[INFO] 馬データを保存しました: {horse_data.get('name')} (ID: {horse_id})")
        return {'success': True, 'id': horse_id, 'action': 'updated' if updated else 'created'}
        
    except Exception as e:
        error_msg = f"馬データの保存中にエラーが発生しました: {str(e)}"
        print(f"[ERROR] {error_msg}")
        print(traceback.format_exc())
        return {'error': error_msg, 'traceback': traceback.format_exc()}

def save_auction_history(*args, **kwargs):
    print("バックエンドモジュールが利用できないため、オークション履歴は保存されません")
    return None

def load_json_file(*args, **kwargs):
    print("バックエンドモジュールが利用できないため、デフォルトのデータを返します")
    return {}

import requests
from bs4 import BeautifulSoup, Tag
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional

# スクリプトのルートディレクトリを取得
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent

# バックエンドモジュールのインポートを試みる
try:
    # バックエンドディレクトリをPythonパスに追加
    backend_dir = project_root / 'backend'
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    
    from backend.scrapers.data_helpers import (
        save_horse as backend_save_horse,
        save_auction_history as backend_save_auction_history,
        load_json_file as backend_load_json_file
    )
    
    # バックエンドの関数を使用
    save_horse = backend_save_horse
    save_auction_history = backend_save_auction_history
    load_json_file = backend_load_json_file
    
    BACKEND_AVAILABLE = True
    print("バックエンドモジュールのインポートに成功しました")
except ImportError as e:
    print(f"バックエンドモジュールのインポートに失敗しました: {e}")
    print("モック関数を使用します")
    BACKEND_AVAILABLE = False

# HTMLSaver のインポート
try:
    from core.utils.html_saver import HTMLSaver
except ImportError:
    # HTMLSaver が見つからない場合はダミークラスを定義
    class HTMLSaver:
        def __init__(self, *args, **kwargs):
            pass
        def save_html(self, *args, **kwargs):
            pass

try:
    from core.cache.cache_manager import CacheManager
except ImportError:
    # CacheManager が見つからない場合はダミークラスを定義
    class CacheManager:
        def __init__(self, *args, **kwargs):
            pass
        def get(self, *args, **kwargs):
            return None
        def set(self, *args, **kwargs):
            pass
        def start_session(self, *args, **kwargs):
            pass

from scripts.components.comment_extractor import CommentExtractor
from scripts.components.race_record_extractor import RaceRecordExtractor
from scripts.components.price_extractor import PriceExtractor
from scripts.components.horse_info_extractor import HorseInfoExtractor
from scripts.components.auction_date_extractor import AuctionDateExtractor
from scripts.components.horse_weight_extractor import HorseWeightExtractor
from scripts.components.seller_info_extractor import SellerInfoExtractor
from scripts.components.prize_info_extractor import PrizeInfoExtractor
from scripts.components.price_info_extractor import PriceInfoExtractor
from scripts.components.image_extractor import ImageExtractor

# BaseExtractor は components.image_extractor からインポートされます

# デフォルトの定数
DEFAULT_TIMEOUT = 30  # デフォルトのタイムアウト（秒）

# 健康状態のキーワード
HEALTH_KEYWORDS = [
    '喘鳴', '喘鳴症', '喉頭', '軟口蓋', '麻痺', '跛行', '屈腱炎', '骨折', '裂蹄',
    '骨瘤', '繋靭帯炎', 'ソエ', '管骨瘤', '飛節', '飛節炎', '球節', '球節炎',
    '屈腱', '屈腱部', '屈腱炎', '靭帯', '靭帯炎', '骨片', '骨瘤', '骨膜炎',
    '骨端症', '骨瘤', '骨瘤形成', '骨棘', '骨棘形成', '骨膜', '骨膜反応',
    '骨膜性骨化', '骨膜性反応', '骨膜性変化', '骨膜性増殖', '骨膜性肥厚',
    '骨膜性石灰化', '骨膜性硬化', '骨膜性骨化', '骨膜性反応', '骨膜性変化',
    '骨膜性増殖', '骨膜性肥厚', '骨膜性石灰化', '骨膜性硬化', '骨膜性骨化',
    '骨膜性反応', '骨膜性変化', '骨膜性増殖', '骨膜性肥厚', '骨膜性石灰化',
    '骨膜性硬化'
]
MAX_RETRIES = 3  # デフォルトの最大リトライ回数
BACKOFF_FACTOR = 0.5  # 指数バックオフの係数

# プロジェクトのルートディレクトリをパスに追加
project_root = Path(__file__).parent.parent
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(scripts_dir))

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
from scripts.core.utils.html_saver import HTMLSaver

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

# キャッシュ関連の設定
CACHE_DIR = config.cache.cache_dir
OUTPUT_DIR = config.output.output_dir

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
        'total_prize_start': 0,     # オークション時点の総賞金（円単位に統一）
        'is_breeding_mare': False   # 繁殖牝馬フラグ
    }
    
    try:
        from bs4 import BeautifulSoup
        import re
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. 繁殖牝馬のチェック
        title_tag = soup.find('title')
        if title_tag and '繁殖牝馬' in title_tag.get_text():
            result['is_breeding_mare'] = True
            logger.info(f"馬名 '{horse_name}' は繁殖牝馬のため賞金は0円です")
            return result

        # 2. 楽天のトップページから直接「総賞金」の値を取得
        # 例: <div class="auctionTableRow__price">
        #       <div class="label">総賞金</div>
        #       <div class="value">3980.2万円</div>
        #       <a href="..." target="_blank" class="netkeiba-link">🔍</a>
        #     </div>
        try:
            # トップページの「総賞金」を直接検索
            prize_divs = soup.find_all('div', class_='auctionTableRow__price')
            for div in prize_divs:
                label = div.find('div', class_='label')
                if label and '総賞金' in label.get_text(strip=True):
                    value_div = div.find('div', class_='value')
                    if value_div:
                        prize_text = value_div.get_text(strip=True)
                        # 数値部分を抽出（「3980.2万円」から「3980.2」を抽出）
                        match = re.search(r'([\d,]+(?:\.\d+)?)', prize_text)
                        if match:
                            try:
                                prize_man = float(match.group(1).replace(',', ''))
                                result['total_prize_start'] = int(prize_man * 10000)  # 万円→円に変換
                                logger.info(f"馬名 '{horse_name}' 総賞金(トップページ): {prize_man}万円 -> {result['total_prize_start']}円")
                                return result
                            except (ValueError, TypeError) as e:
                                logger.debug(f"賞金の数値変換に失敗: {prize_text}, エラー: {e}")
                                continue
        except Exception as e:
            logger.debug(f"トップページからの賞金抽出で例外: {e}")

        # 3. トップページで取得できなかった場合、詳細ページから取得を試みる
        # 3-0) まずは対象の馬カードを特定して、その内部のみを探索（他馬の値を拾わない）
        card_soup = None
        try:
            # よく使うカード候補のクラスを網羅的に探す
            card_candidates = soup.select('.auctionTableCard, .auctionList__item, .auctionCard, .auctionTableRow')
            for card in card_candidates:
                text = card.get_text(" ", strip=True)
                if horse_name and horse_name in text:
                    card_soup = card
                    break
        except Exception as e:
            logger.debug(f"カード特定中に例外: {e}")

        search_root = card_soup if card_soup is not None else soup

        # 3-1) 詳細ページの「中央獲得賞金」「地方獲得賞金」を合算
        try:
            full_text = (search_root or soup).get_text(' ', strip=True)
            # 例: 中央獲得賞金：3966.7万円　　　地方獲得賞金：13.5万円
            m_c = re.search(r'中央獲得賞金[：:\s]*([\d,]+(?:\.[\d]+)?)\s*万円', full_text)
            m_l = re.search(r'地方獲得賞金[：:\s]*([\d,]+(?:\.[\d]+)?)\s*万円', full_text)
            total_man = 0.0
            found_any = False
            if m_c:
                try:
                    total_man += float(m_c.group(1).replace(',', ''))
                    found_any = True
                except ValueError:
                    pass
            if m_l:
                try:
                    total_man += float(m_l.group(1).replace(',', ''))
                    found_any = True
                except ValueError:
                    pass
            if found_any and total_man > 0:
                result['total_prize_start'] = int(total_man * 10000)  # 万円→円
                logger.info(f"馬名 '{horse_name}' 総賞金(中央+地方): {total_man}万円 -> {result['total_prize_start']}円")
                return result
        except Exception as e:
            logger.debug(f"中央/地方 賞金合算抽出で例外: {e}")

        # 3-2) 詳細ページのその他の賞金情報を検索
        try:
            # 詳細ページの「総賞金」を検索
            prize_sections = search_root.find_all('div', class_=lambda c: c and 'prize' in (c or '').lower())
            for section in prize_sections:
                prize_text = section.get_text(' ', strip=True)
                # 「総賞金: 3980.2万円」のような形式を検索
                m = re.search(r'総賞金[：:\s]*([\d,]+(?:\.[\d]+)?)\s*万円', prize_text)
                if m:
                    try:
                        prize_man = float(m.group(1).replace(',', ''))
                        result['total_prize_start'] = int(prize_man * 10000)
                        logger.info(f"馬名 '{horse_name}' 総賞金(詳細ページ): {prize_man}万円 -> {result['total_prize_start']}円")
                        return result
                    except ValueError:
                        continue
                
                # 数値のみの場合はそれを使用
                m = re.search(r'([\d,]+(?:\.[\d]+)?)\s*万円', prize_text)
                if m:
                    try:
                        prize_man = float(m.group(1).replace(',', ''))
                        result['total_prize_start'] = int(prize_man * 10000)
                        logger.info(f"馬名 '{horse_name}' 総賞金(数値のみ): {prize_man}万円 -> {result['total_prize_start']}円")
                        return result
                    except ValueError:
                        continue
        except Exception as e:
            logger.debug(f"詳細ページからの賞金抽出で例外: {e}")
        
        logger.info(f"馬名 '{horse_name}' の賞金情報を抽出できませんでした: {result}")
        return result
        
    except Exception as e:
        logger.error(f"賞金情報の抽出中にエラーが発生しました（馬名: {horse_name}）: {str(e)}")
        logger.error(traceback.format_exc())
        return result

def _extract_prize_value(text: str, horse_name: str = '') -> Optional[float]:
    """
    テキストから賞金額を抽出する
    
    Args:
        text: 賞金情報を含むテキスト
        horse_name: 馬名（ログ出力用）
        
    Returns:
        抽出した賞金額（万円単位）、抽出できない場合はNone
    """
    if not text:
        return None
        
    try:
        # 数字とカンマ、小数点を抽出（例: 1,234.56万円 → 1234.56）
        import re
        match = re.search(r'([\d,]+(?:\.[\d,]+)?)', text.replace(',', ''))
        if match:
            return float(match.group(1).replace(',', ''))
            
        logger.debug(f"馬名 '{horse_name}': 賞金の数値が見つかりませんでした: {text}")
        return None
        
    except (ValueError, TypeError) as e:
        logger.error(f"馬名 '{horse_name}': 賞金の抽出中にエラーが発生しました: {e}")
        return None


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

# プロジェクトのルートディレクトリをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(project_root, 'backend')

# デバッグ用にパスを表示
print(f"プロジェクトルート: {project_root}")
print(f"バックエンドディレクトリ: {backend_dir}")
print(f"現在のPythonパス: {sys.path}")

# バックエンドディレクトリをパスに追加
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
    print(f"バックエンドディレクトリをパスに追加しました: {backend_dir}")

class ScraperConfig:
    """スクレイパーの設定を管理するクラス"""
    
    # モバイルデバイス用のUser-Agentリスト
    MOBILE_USER_AGENTS = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Linux; Android 12; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.88 Mobile Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 15_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
    ]
    
    # 一般的なPC向けUser-Agentのリスト
    PC_USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.277'
    ]
    
    def __init__(
        self,
        max_workers: int = 5, 
        use_cache: bool = True, 
        cache_dir: Union[str, Path] = 'cache',
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        min_delay: float = 1.0,
        max_delay: float = 3.0,
        use_mobile: bool = True,  # デフォルトでモバイル版を使用
        log_level: str = 'INFO',
        log_file: Optional[Union[str, Path]] = None
    ):
        """
        初期化メソッド
        
        Args:
            max_workers: 並列処理の最大ワーカー数
            use_cache: キャッシュを使用するかどうか
            cache_dir: キャッシュディレクトリのパス
            timeout: リクエストのタイムアウト（秒）
            max_retries: 最大リトライ回数
            backoff_factor: リトライ間の待機時間の係数
            min_delay: リクエスト間の最小遅延（秒）
            max_delay: リクエスト間の最大遅延（秒）
            use_mobile: モバイル版のUser-Agentを使用するかどうか
            log_level: ログレベル（'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'）
            log_file: ログファイルのパス（Noneの場合はコンソールのみに出力）
        """
        self.max_workers = max_workers
        self.use_cache = use_cache
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.use_mobile = use_mobile
        self.log_level = log_level
        self.log_file = Path(log_file) if log_file else None
        self._current_ua_index = 0
        
        # ロギングの初期化
        self.logger = setup_logging(log_level=log_level, log_file=log_file)
        
        # キャッシュディレクトリの作成
        if self.use_cache and self.cache_dir:
            try:
                ensure_directory(self.cache_dir)
                self.logger.debug(f"キャッシュディレクトリを初期化しました: {self.cache_dir}")
            except Exception as e:
                self.logger.warning(f"キャッシュディレクトリの初期化に失敗しました: {e}")
                self.use_cache = False
        
    def get_random_user_agent(self) -> str:
        """ランダムなUser-Agentを取得（モバイル/PCを設定に応じて切り替え）"""
        if self.use_mobile:
            return random.choice(self.MOBILE_USER_AGENTS)
        return random.choice(self.PC_USER_AGENTS)
        
    def get_next_user_agent(self) -> str:
        """次のUser-Agentをローテーションして取得（モバイル/PCを設定に応じて切り替え）"""
        if self.use_mobile:
            self._current_ua_index = (self._current_ua_index + 1) % len(self.MOBILE_USER_AGENTS)
            return self.MOBILE_USER_AGENTS[self._current_ua_index]
        self._current_ua_index = (self._current_ua_index + 1) % len(self.PC_USER_AGENTS)
        return self.PC_USER_AGENTS[self._current_ua_index]
        
    def get_random_delay(self) -> float:
        """ランダムな遅延時間を取得"""
        return random.uniform(self.min_delay, self.max_delay)


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
    
    def __init__(
        self, 
        config: Optional[ScraperConfig] = None,
        **kwargs
    ):
        """
        初期化メソッド
        
        Args:
            config: スクレイパー設定（省略時はデフォルト設定を使用）
            **kwargs: 設定オーバーライド用のキーワード引数
        """
        # 設定の初期化
        self.config = config if config is not None else ScraperConfig(**kwargs)
        
        # ロガーの設定
        self.logger = self.config.logger
        
        # リクエストセッションの初期化
        self.session = requests.Session()
        
        # リトライ設定
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.backoff_factor,
            status_forcelist=[408, 429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        # アダプターの設定
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # ユーザーエージェントの設定
        self.session.headers.update({
            'User-Agent': self.config.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Connection': 'keep-alive',
        })
        
        # キャッシュの初期化
        self._setup_cache()
        
        # その他の初期化
        self.failed_horses = []  # 失敗した馬の記録用
        self.processed_count = 0  # 処理済みカウンタ
        
        self.logger.info("スクレイパーを初期化しました")
    
    def _handle_error(self, error: Exception, context: str = "", log_level: str = "error", 
                    reraise: bool = False, **kwargs) -> Optional[Dict]:
        """
        エラーハンドリングを統一するユーティリティメソッド
        
        Args:
            error: 発生した例外
            context: エラーのコンテキストを説明するメッセージ
            log_level: ログレベル ('debug', 'info', 'warning', 'error', 'critical')
            reraise: 例外を再送出するかどうか
            **kwargs: ログに記録する追加情報
            
        Returns:
            Optional[Dict]: エラー情報を含む辞書（エラー処理に使用可能）
        """
        error_info = {
            'error_type': error.__class__.__name__,
            'error_message': str(error),
            'context': context,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        
        # ログレベルの設定
        log_method = getattr(self.logger, log_level.lower(), self.logger.error)
        
        # ログメッセージの構築
        log_message = f"{context}: {error.__class__.__name__}: {str(error)}"
        if 'url' in kwargs:
            log_message = f"{log_message} (URL: {kwargs['url']})"
            
        log_method(log_message, exc_info=log_level.lower() in ['error', 'critical'])
        
        # 失敗した馬を記録
        if 'horse_id' in kwargs and hasattr(self, 'failed_horses'):
            self.failed_horses.append({
                'horse_id': kwargs['horse_id'],
                'error': error_info,
                'timestamp': datetime.now().isoformat()
            })
        
        # 例外を再送出する場合
        if reraise:
            raise error
            
        return error_info
    
    def _setup_cache(self) -> None:
        """キャッシュの設定を行う"""
        # キャッシュをデフォルトで無効化
        self.cache_manager = None
        self.use_cache = False
        
        # 設定でキャッシュが有効な場合のみ初期化
        if not hasattr(self, 'config') or not hasattr(self.config, 'use_cache'):
            self.logger.warning("設定が見つからないため、キャッシュを無効化します")
            return
            
        if self.config.use_cache and self.config.cache_dir:
            try:
                # キャッシュマネージャーの初期化
                self.cache_manager = CacheManager(base_dir=self.config.cache_dir)
                self.use_cache = True
                self.logger.info(f"キャッシュを有効化: {self.config.cache_dir}")
                
                # キャッシュセッションを開始
                if hasattr(self, 'start_cache_session') and not self.start_cache_session():
                    self.logger.warning("キャッシュセッションの開始に失敗しました")
                    
            except Exception as e:
                self.use_cache = False
                self.logger.warning(f"キャッシュの初期化に失敗しました: {e}")
                    
            except Exception as e:
                self._handle_error(
                    e,
                    context="キャッシュの初期化に失敗しました",
                    log_level="warning"
                )
                self.use_cache = False
        
        if not self.use_cache:
            self.logger.info("キャッシュは無効化されています")
    
    def _initialize_extractors(self):
        """抽出コンポーネントを初期化する"""
        extractors = {
            'horse_info_extractor': HorseInfoExtractor,
            'horse_weight_extractor': HorseWeightExtractor,
            # JBIS関連の抽出器を一時的に無効化（BOT判定回避のため）
            # 'jbis_link_extractor': JbisLinkExtractor,
            'prize_info_extractor': PrizeInfoExtractor,
            # 'current_prize_extractor': CurrentPrizeExtractor,
            'pedigree_extractor': PedigreeExtractor,
            'prize_extractor': PrizeExtractor,
            'comment_extractor': CommentExtractor,
            'auction_prize_extractor': AuctionPrizeExtractor,
            'price_extractor': PriceExtractor,
            'price_info_extractor': PriceInfoExtractor,
            'seller_info_extractor': SellerInfoExtractor,
            'race_record_extractor': RaceRecordExtractor,
            'image_extractor': ImageExtractor,
            'auction_date_extractor': AuctionDateExtractor,
        }
        
        # 各extractorを初期化してインスタンス変数に設定
        for name, extractor_class in extractors.items():
            try:
                setattr(self, name, extractor_class())
                self.logger.debug(f"{name} を初期化しました")
            except Exception as e:
                self.logger.error(f"{name} の初期化に失敗しました: {str(e)}")
                setattr(self, name, None)  # エラーが発生した場合はNoneを設定
                
        self.logger.debug("抽出コンポーネントの初期化が完了しました")

    def get_auction_date(self, html_content: str = None, url: str = None) -> Optional[str]:
        """
        オークションの開催日を取得する
        
        Args:
            html_content: オプションでHTMLコンテンツを直接指定
            url: オプションでURLを指定（html_contentが指定されていない場合に使用）
            
        Returns:
            str: オークション日（YYYY-MM-DD形式）、取得できない場合はNone
        """
        try:
            self.logger.info("=== オークション日取得処理を開始します ===")
            self.logger.info(f"URL: {url}")
            self.logger.info(f"HTMLコンテンツの長さ: {len(html_content) if html_content else 0} バイト")
            self.logger.info(f"HTMLコンテンツの先頭100文字: {html_content[:100] if html_content else 'None'}")
            self.logger.info("get_auction_dateメソッドが呼び出されました")
            
            # キャッシュキーを生成
            cache_key = f"auction_date_{url}" if url else "auction_date"
            self.logger.debug(f"キャッシュキー: {cache_key}")
            
            # キャッシュから取得を試みる
            if self.config.use_cache and hasattr(self, 'cache_manager') and self.cache_manager:
                cached_date = self.cache_manager.get(cache_key)
                if cached_date:
                    self.logger.info(f"キャッシュからオークション日を取得: {cached_date}")
                    self.logger.info(f"キャッシュから取得した値の型: {type(cached_date)}")
                    self.logger.info(f"キャッシュから取得した値の長さ: {len(str(cached_date))}")
                    self.logger.info(f"キャッシュから取得した値の先頭100文字: {str(cached_date)[:100]}")
                    return cached_date
                else:
                    self.logger.debug("キャッシュにオークション日が存在しません")
            
            # HTMLコンテンツが指定されていない場合はURLから取得
            if not html_content and url:
                self.logger.info(f"オークションページからHTMLを取得中: {url}")
                response = self.session.get(url)
                response.raise_for_status()
                html_content = response.text
                self.logger.debug(f"HTMLの取得に成功: {len(html_content)} バイト")
            
            if not html_content:
                self.logger.warning("HTMLコンテンツが指定されていません")
                return None
            
            # まずキャッシュメタデータから日付を取得を試みる
            self.logger.info("キャッシュメタデータからオークション日を抽出します")
            cache_meta_match = re.search(r'CACHE_METADATA=.*?"saved_at":"([^"]+)"', html_content)
            if cache_meta_match:
                saved_at = cache_meta_match.group(1)
                # 日付部分のみを抽出 (YYYY-MM-DD)
                auction_date = saved_at.split('T')[0]
                self.logger.info(f"キャッシュメタデータからオークション日を抽出しました: {auction_date}")
                self.logger.info(f"auction_dateの型: {type(auction_date)}")
                self.logger.info(f"auction_dateの内容: '{auction_date}'")
                # キャッシュに保存
                if hasattr(self, 'cache_manager') and self.cache_manager:
                    self.cache_manager.set(cache_key, auction_date, expire_seconds=86400)
                return auction_date
            
            # HTMLをBeautifulSoupでパース
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # オークション日を抽出（AuctionDateExtractorを使用）
            if hasattr(self, 'auction_date_extractor') and self.auction_date_extractor:
                self.logger.info("AuctionDateExtractorを使用してオークション日を抽出します")
                auction_date = self.auction_date_extractor.extract_from_html(html_content)
                if auction_date:
                    self.logger.info(f"オークション日を抽出しました (AuctionDateExtractor経由): {auction_date}")
                    # キャッシュに保存
                    if hasattr(self, 'cache_manager') and self.cache_manager:
                        self.cache_manager.set(cache_key, auction_date, expire_seconds=86400)
                    return auction_date
            
            # AuctionDateExtractorが使えない、または日付が抽出できなかった場合、直接HTMLから抽出を試みる
            self.logger.info("直接HTMLからオークション日を抽出します")
            
            # 日付パターンのリスト（複数の形式に対応）
            date_patterns = [
                r'(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日',  # 2023年10月15日
                r'(\d{4})[\\/\\-年](\d{1,2})[\\/\\-月](\d{1,2})日?',  # 2023/10/15 や 2023-10-15
                r'(\d{4})[\\/\\-](\d{1,2})[\\/\\-](\d{1,2})'  # 2023/10/15 や 2023-10-15 (日付のみ)
            ]
            
            # ページ内のテキストを取得
            text = soup.get_text()
            self.logger.debug(f"ページテキストの先頭500文字: {text[:500]}...")
            
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    year = match.group(1)
                    month = match.group(2).zfill(2)
                    day = match.group(3).zfill(2)
                    date_str = f"{year}-{month}-{day}"
                    self.logger.info(f"オークション日を抽出しました (正規表現経由): {date_str}")
                    
                    # キャッシュに保存
                    if hasattr(self, 'cache_manager') and self.cache_manager:
                        self.cache_manager.set(cache_key, date_str, expire_seconds=86400)
                    
                    return date_str
            
            # 日付が見つからなかった場合、HTML内の日付関連の要素を直接検索
            self.logger.info("日付関連の要素を直接検索します")
            
            # 日付が含まれていそうな要素を検索
            date_elements = soup.find_all(['span', 'div', 'td', 'p'], string=re.compile(r'\d{4}'))
            for elem in date_elements:
                elem_text = elem.get_text().strip()
                self.logger.debug(f"日付候補の要素テキスト: {elem_text[:100]}...")
                
                for pattern in date_patterns:
                    match = re.search(pattern, elem_text)
                    if match:
                        year = match.group(1)
                        month = match.group(2).zfill(2)
                        day = match.group(3).zfill(2)
                        date_str = f"{year}-{month}-{day}"
                        self.logger.info(f"要素からオークション日を抽出しました: {date_str}")
                        
                        # キャッシュに保存
                        if hasattr(self, 'cache_manager') and self.cache_manager:
                            self.cache_manager.set(cache_key, date_str, expire_seconds=86400)
                        
                        self.logger.info(f"要素からオークション日を抽出しました: {date_str}")
                        return date_str
            
            self.logger.warning("オークション日を抽出できませんでした")
            # デバッグ用: HTMLコンテンツが返されていないことを確認
            self.logger.warning(f"HTMLコンテンツの先頭100文字: {html_content[:100] if html_content else 'None'}")
            return None
            
        except Exception as e:
            self.logger.error(f"オークション日の取得中にエラーが発生しました: {e}", exc_info=True)
            return None

    def _setup_logger(self) -> logging.Logger:
        """ロガーを設定する
        
        Returns:
            logging.Logger: 設定済みのロガーインスタンス
        """
        # ロガーを取得
        logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        logger.setLevel(logging.DEBUG)
        
        # 既存のハンドラをクリア
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # コンソールハンドラ（INFOレベル）
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # ファイルハンドラ（DEBUGレベル）
        log_dir = Path('debug_logs')
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # フォーマッタ
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # ハンドラを追加
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
        
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
        self.base_url = "https://auction.keiba.rakuten.co.jp/"
        
        # テストモードの設定
        self.test_mode = isinstance(config, TestConfig)
        
        # ロガーを設定
        self.logger = self._setup_logger()
        
        # 失敗した馬を記録するためのリスト
        self.failed_horses = []
        
        # 並列処理の最大ワーカー数を設定
        self.max_workers = config.max_workers
        
        self.logger.info(f"スクレイパーを初期化します (max_workers={self.max_workers})")
        
        # キャッシュの設定
        self._setup_cache()
            
        # 抽出コンポーネントの初期化
        self.horse_info_extractor = HorseInfoExtractor(logger=self.logger.getChild('horse_info_extractor'))
        
        # セッションの初期化
        self.timeout = config.timeout  # timeoutをインスタンス変数として設定
        self.session = self._create_session(
            timeout=config.timeout,
            max_retries=config.max_retries,
            backoff_factor=config.backoff_factor
        )
        
        # 抽出コンポーネントの初期化
        self._initialize_extractors()
        
        # HTML保存用の初期化
        self.html_saver = None
        # デフォルトでHTML保存を有効化
        self.enable_html_saving(Path('html_dump'))
    
    def enable_html_saving(self, base_dir: Union[str, Path]) -> None:
        """HTML保存機能を有効化する
        
        Args:
            base_dir: HTMLを保存するベースディレクトリ（文字列またはPathオブジェクト）
        """
        if isinstance(base_dir, str):
            base_dir = Path(base_dir)
        base_dir.mkdir(parents=True, exist_ok=True)
        self.html_saver = HTMLSaver(base_dir)
        self.logger.info(f"HTML保存が有効化されました: {base_dir.absolute()}")
        self.logger.info(f"詳細ページは {base_dir.absolute()}/details/ に保存されます")
    
    def _fetch_html(self, url: str, use_cache: bool = True) -> Optional[str]:
        """HTMLを取得する
            
        Args:
            url: 取得するURL
            use_cache: キャッシュを使用するかどうか
                
        Returns:
            HTMLコンテンツ（取得失敗時はNone）
        """
        try:
            # キャッシュから取得を試みる
            if use_cache and self.cache_manager:
                cached_content = self.cache_manager.get(url)
                if cached_content:
                    self.logger.debug(f'キャッシュから取得: {url}')
                    return cached_content
            
            # リクエスト間のランダムな遅延を追加（1.0〜3.0秒）
            delay = self.config.get_random_delay()
            self.logger.debug(f'リクエスト前に {delay:.2f}秒待機します...')
            time.sleep(delay)
            
            # User-Agentをローテーション
            if hasattr(self, 'session'):
                new_ua = self.config.get_next_user_agent()
                self.session.headers.update({'User-Agent': new_ua})
                self.logger.debug(f'User-Agentを変更: {new_ua[:50]}...')
            
            # ウェブから取得
            self.logger.debug(f'ウェブから取得: {url}')
            response = self.session.get(
                url,
                timeout=self.config.timeout,
                headers={
                    'User-Agent': self.config.get_next_user_agent(),
                    'Referer': 'https://auction.keiba.rakuten.co.jp/'
                }
            )
            response.raise_for_status()
            
            # エンコーディングを設定
            response.encoding = 'utf-8'
            html_content = response.text
            
            # 成功時に少し待機（サーバー負荷軽減のため）
            time.sleep(random.uniform(0.5, 1.5))
            
            # HTMLを保存（デバッグ用）
            if self.html_saver is not None:
                self.html_saver.save(url, html_content)
            
            # キャッシュに保存
            if use_cache and self.cache_manager:
                self.cache_manager.set(url, html_content)
                
            return html_content
                
        except requests.RequestException as e:
            self.logger.error(f'リクエストエラー: {e}')
            return None
        except Exception as e:
            self.logger.error(f'HTMLの取得中にエラーが発生しました: {e}')
            return None
        
    def _setup_html_dirs(self, base_dir: Optional[Union[str, Path]] = None) -> Tuple[Path, Path]:
        """HTML保存用のディレクトリ構造をセットアップする
        
        注意: このメソッドは互換性のために残されていますが、HTMLSaverクラスを使用することを推奨します。
        
        Args:
            base_dir: ベースディレクトリ（Noneの場合はスクリプトディレクトリの親ディレクトリを使用）
            
        Returns:
            Tuple[Path, Path]: (日付ディレクトリのパス, 詳細ページ用ディレクトリのパス)
        """
        if base_dir is None:
            base_dir = Path(__file__).parent.parent
        else:
            base_dir = Path(base_dir)
            
        # 日付ベースのディレクトリを作成 (例: 20230825)
        date_str = datetime.now().strftime("%Y%m%d")
        date_dir = base_dir / 'html_dump' / date_str
        detail_dir = date_dir / 'detail'
        
        # ディレクトリが存在しない場合は作成
        date_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
        detail_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
        
        # HTMLSaverを有効化
        self.enable_html_saving(date_dir)
        
        self.logger.info(f"HTML保存先: {date_dir}")
        
        return date_dir, detail_dir
        
        # その他のコンポーネントの初期化（既存コードを維持）
        self.jbis_link_extractor = JbisLinkExtractor()
        self.pedigree_extractor = PedigreeExtractor()
        # 2回目の初期化を削除（既に初期化済み）
        self.prize_extractor = PrizeExtractor()
        self.comment_extractor = CommentExtractor()
        self.current_prize_extractor = CurrentPrizeExtractor()
        self.auction_prize_extractor = AuctionPrizeExtractor()
        self.price_extractor = PriceExtractor()
        
        # 出力ディレクトリの確認
        self.output_dir = Path(OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"出力先ディレクトリ: {self.output_dir}")
        
        # HTML保存機能の初期化（デフォルトでは無効）
        self.html_saver = None
        self.logger.info(f"出力先ディレクトリ: {self.output_dir}")
        
        # HTML保存用ディレクトリの設定
        self.date_dir, self.detail_dir = self._setup_html_dirs()
        
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = self.output_dir / f'scraped_horses_{self.session_id}.json'
            
    def start_cache_session(self):
        """キャッシュセッションを開始する
        
        Returns:
            bool: セッションの開始に成功した場合はTrue、失敗した場合はFalse
        """
        try:
            if not self.use_cache:
                self.logger.debug("キャッシュが無効化されています")
                return False
                
            if hasattr(self, 'cache_session') and self.cache_session is not None:
                self.logger.debug("既にキャッシュセッションが開始されています")
                return True
                
            self.logger.debug("キャッシュセッションを開始します")
            self.cache_session = datetime.now().strftime("%Y%m%d_%H%M%S")
            return True
        except Exception as e:
            self.logger.error(f"キャッシュセッションの開始中にエラーが発生しました: {e}")
            return False
    
    def _create_session(self, timeout: int = None, max_retries: int = None, 
                      backoff_factor: float = None) -> requests.Session:
        """HTTPセッションを作成します。
        
        Args:
            timeout: リクエストのタイムアウト（秒）
            max_retries: 最大リトライ回数
            backoff_factor: リトライ間の待機時間の係数
        
        Returns:
            requests.Session: 設定済みのセッションオブジェクト
            
        Example:
            >>> scraper = ImprovedRakutenScraper()
            >>> session = scraper._create_session(timeout=30, max_retries=3)
            >>> isinstance(session, requests.Session)
            True
        """
        # デフォルト値の設定
        timeout = timeout if timeout is not None else self.config.timeout
        max_retries = max_retries if max_retries is not None else self.config.max_retries
        backoff_factor = backoff_factor if backoff_factor is not None else self.config.backoff_factor
        
        self.logger.debug(
            f"セッションを作成します (timeout={timeout}, "
            f"max_retries={max_retries}, backoff_factor={backoff_factor})"
        )
        
        # セッションの作成
        session = requests.Session()
        
        # プロキシ設定（必要に応じて有効化）
        # proxies = {
        #     'http': 'http://223.135.156.183:8080',
        #     'https': 'http://223.135.156.183:8080'
        # }
        # session.proxies.update(proxies)
        # self.logger.info(f"プロキシを設定しました: {proxies}")
        session.proxies = {}
        self.logger.info("プロキシを無効化しました")
        
        # リクエスト/レスポンスのフックを設定
        def log_request(response, *args, **kwargs):
            self.logger.debug(f"Request: {response.request.method} {response.request.url}")
            self.logger.debug(f"Status: {response.status_code}")
            self.logger.debug(f"Using proxy: {response.request.url.split('//')[0] + '//' + response.request.url.split('//')[1].split('/')[0] if '//' in response.request.url else response.request.url}")
            return response

        session.hooks['response'] = [log_request]
        
        # リトライ戦略の設定
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[408, 413, 429, 500, 502, 503, 504, 521, 522, 524],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"],
            respect_retry_after_header=True,
            backoff_max=60,  # 最大60秒までバックオフ
            raise_on_status=False
        )

        # アダプターの設定
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=min(32, self.config.max_workers * 2),
            pool_maxsize=min(100, self.config.max_workers * 10),
            pool_block=False
        )
        
        # セッションにアダプターをマウント
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # ヘッダー設定
        headers = {
            'User-Agent': self.config.get_random_user_agent(),
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
            'Referer': self.base_url
        }
        
        # カスタムユーザーエージェントが指定されていれば使用
        if hasattr(self.config, 'user_agent') and self.config.user_agent:
            headers['User-Agent'] = self.config.user_agent
        
        # セッションのタイムアウト設定
        session.request = functools.partial(
            session.request,
            timeout=timeout,
            headers=headers
        )
        
        # セッションの設定をログに記録
        self.logger.debug(f"セッション設定: timeout={timeout}s, "
                         f"pool_connections={adapter._pool_connections}, "
                         f"pool_maxsize={adapter._pool_maxsize}")
        
        return session


# RaceRecordExtractor は components.race_record_extractor からインポートされます

    def scrape_horse_list(self, url: str = None, use_cache: bool = False, max_pages: int = 0) -> List[Dict[str, Any]]:
        """馬の一覧をスクレイピングする
        
        Args:
            url: スクレイピング対象のURL（Noneの場合はベースURLを使用）
            use_cache: キャッシュを使用するかどうか
            max_pages: 取得する最大ページ数（0は無制限）
            
        Returns:
            List[Dict[str, Any]]: 馬情報のリスト
        """
        if self.test_mode:
            self.logger.info("テストモード: サンプルデータを返します")
            return [
                {
                    "id": "test1",
                    "name": "テスト馬1",
                    "sire": "テスト父",
                    "dam": "テスト母",
                    "damsire": "テスト母父",
                    "sex": "牡",
                    "age": 3,
                    "seller": "テスト牧場",
                    "auction_date": datetime.now().strftime("%Y-%m-%d"),
                    "detail_url": f"{self.base_url}detail/1"
                },
                {
                    "id": "test2",
                    "name": "テスト馬2",
                    "sire": "テスト父2",
                    "dam": "テスト母2",
                    "damsire": "テスト母父2",
                    "sex": "牝",
                    "age": 2,
                    "seller": "テスト牧場2",
                    "auction_date": datetime.now().strftime("%Y-%m-%d"),
                    "detail_url": f"{self.base_url}detail/2"
                },
                {
                    "id": "test3",
                    "name": "テスト馬3",
                    "sire": "テスト父3",
                    "dam": "テスト母3",
                    "damsire": "テスト母父3",
                    "sex": "セ",
                    "age": 4,
                    "seller": "テスト牧場3",
                    "auction_date": datetime.now().strftime("%Y-%m-%d"),
                    "detail_url": f"{self.base_url}detail/3"
                }
            ]
            
        # 実際のスクレイピング処理を呼び出す
        return self._scrape_horse_list(url=url, use_cache=use_cache)

    def _scrape_horse_list(self, url: Optional[str] = None, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        馬一覧ページから馬の情報をスクレイピングする
        
        Args:
            url (str, optional): スクレイピング対象のURL. デフォルトはNone.
            use_cache (bool, optional): キャッシュを使用するかどうか. デフォルトはTrue.
            
        Returns:
            List[Dict[str, Any]]: 馬情報のリスト
        """
        from bs4 import BeautifulSoup
        
        url = url or self.base_url
        self.logger.info(f"馬一覧のスクレイピングを開始します: {url}")
        
        try:
            # HTMLを取得
            html = self._fetch_html(url, use_cache=use_cache)
            if not html:
                self.logger.error("HTMLの取得に失敗しました")
                return []
            
            # BeautifulSoupでパース
            soup = BeautifulSoup(html, 'html.parser')
            
            # 馬のカード要素を取得
            horse_cards = soup.select('.auctionTableCard')
            total_horses = len(horse_cards)
            
            if total_horses == 0:
                self.logger.warning("馬のカードが見つかりませんでした")
                return []
            
            self.logger.info(f"馬のカードを {total_horses} 件見つけました")
            
            # 馬情報を格納するリスト
            horses = []
            success_count = 0
            failed_count = 0
            
            # 各馬カードを処理
            for i, card in enumerate(horse_cards, 1):
                try:
                    # 馬情報を抽出
                    horse_info = self._process_horse_info(card, i, total_horses)
                    if horse_info:
                        horses.append(horse_info)
                        success_count += 1
                    else:
                        failed_count += 1
                    
                    # 進捗をログに出力
                    self.logger.info(f"進捗: {i}/{total_horses}頭 (成功: {success_count}, 失敗: {failed_count})")
                    
                except Exception as e:
                    failed_count += 1
                    self.logger.error(f"馬情報の抽出中にエラーが発生しました (馬 {i}/{total_horses}): {e}", exc_info=True)
            
            # 結果をログに出力
            self.logger.info(f"完了: 成功 {success_count}頭, 失敗 {failed_count}頭")
            
            if failed_count > 0:
                self.logger.warning(f"{failed_count}頭の馬情報の抽出に失敗しました")
            
            return horses
                
        except Exception as e:
            self.logger.error(f"馬の一覧のスクレイピング中にエラーが発生しました: {e}", exc_info=True)
            if hasattr(self, 'test_mode') and self.test_mode:
                raise  # テストモードの場合は例外を再スロー
            return []

    def _clean_horse_name(self, name_elem) -> str:
        """馬名をクリーンアップする
        
        Args:
            name_elem: BeautifulSoupの要素オブジェクト
            
        Returns:
            str: クリーンアップされた馬名（余分な情報を削除）
        """
        if not name_elem:
            return ""
            
        # 1. 要素内のすべてのテキストを取得
        name = name_elem.get_text(' ', strip=True)
        
        # 2. 改行をスペースに変換
        name = name.replace('\n', ' ')
        
        # 3. 不要なパターンを削除
        patterns = [
            r'※.*$',  # ※以降の文字列
            r'登録抹消.*$',  # 登録抹消以降の文字列
            r'新馬.*$',  # 新馬以降の文字列
            r'未出走.*$',  # 未出走以降の文字列
            r'[0-9]+歳',  # 年齢（例：3歳）
            r'[牡牝セ]',  # 性別（牡、牝、セ）
            r'\(.*\)',  # 括弧内の文字列
            r'\[.*\]'  # 角括弧内の文字列
        ]
        
        for pattern in patterns:
            name = re.sub(pattern, '', name)
            
        # 4. スペースで分割して最後の要素が「セン」の場合は削除
        name_parts = name.split()
        if len(name_parts) > 1 and name_parts[-1] == 'セン':
            name = ' '.join(name_parts[:-1])
        # スペースがなく「セン」で終わる場合も削除
        elif name.endswith(' セン') or name.endswith('　セン'):
            name = name[:-2].strip()
            
        # 5. 前後の空白を削除
        name = name.strip()
        
        # 5. 空の場合は元のテキストを返す
        if not name:
            return name_elem.get_text(' ', strip=True)
            
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

    def _extract_detail_url(self, card) -> Optional[Tuple[str, str]]:
        """
        馬の詳細ページのURLと馬IDを抽出する
        
        Args:
            card: 馬情報を含むHTML要素（BeautifulSoupオブジェクト）
            
        Returns:
            Optional[Tuple[str, str]]: (詳細ページのURL, 馬ID)のタプル。抽出に失敗した場合はNone
        """
        try:
            # 馬名のリンクから相対URLを取得（複数のクラス名に対応）
            name_links = card.find_all('a')
            self.logger.debug(f"見つかったリンク数: {len(name_links)}")
            
            # デバッグ用にリンクのクラスをログに出力
            for i, link in enumerate(name_links):
                self.logger.debug(f"リンク {i+1} のクラス: {link.get('class', [])}  href: {link.get('href', 'N/A')}")
            
            # 馬名のリンクを検索（複数のクラス名に対応）
            name_link = card.find('a', class_=lambda c: c and ('horseName' in c or 'auctionTableCard__name' in c.split()))
            
            if name_link:
                self.logger.debug(f"馬名リンクのクラス: {name_link.get('class', [])}")
                if 'href' in name_link.attrs:
                    detail_path = name_link['href']
                    self.logger.debug(f"相対URLを検出: {detail_path}")
                    # 相対URLを絶対URLに変換
                    full_url = urljoin(self.base_url, detail_path)
                    self.logger.debug(f"絶対URLに変換: {full_url}")
                    
                    # URLから数値の馬IDを抽出（例: /item/12345 から 12345 を抽出）
                    import re
                    match = re.search(r'/(\d+)(?:/|$)', full_url)
                    if match:
                        horse_id = match.group(1)
                        self.logger.debug(f"抽出した馬ID: {horse_id}")
                        return (full_url, horse_id)
                    else:
                        self.logger.warning(f"URLから馬IDを抽出できませんでした: {full_url}")
                        return (full_url, None)
                else:
                    self.logger.warning("馬名リンクにhref属性がありません")
            else:
                self.logger.warning("馬名リンクが見つかりませんでした")
                
            return None
            
        except Exception as e:
            self.logger.error(f"詳細ページURLの抽出中にエラーが発生しました: {e}", exc_info=True)
            return None

    def _process_horse_info(self, card, index: int, total: int) -> Optional[Dict[str, Any]]:
        """
        馬の情報を抽出する（リストページからの情報抽出用）
        
        Args:
            card: 馬情報を含むHTML要素（BeautifulSoupオブジェクト）
            index: 処理中の馬のインデックス（1ベース）
            total: 総馬数
            
        Returns:
            Optional[Dict[str, Any]]: 抽出した馬情報の辞書。必須フィールドが不足している場合はNoneを返す
        """
        try:
            self.logger.info(f"[{index}/{total}] 馬情報の抽出を開始")
            
            # 1. 詳細ページのURLと馬IDを抽出
            detail_info = self._extract_detail_url(card)
            if not detail_info:
                self.logger.warning(f"詳細ページURLの抽出に失敗しました")
                return None
                
            detail_url, horse_id = detail_info
            self.logger.debug(f"抽出した馬ID: {horse_id}, 詳細URL: {detail_url}")
                
            # 2. 詳細ページのHTMLを取得
            detail_html = self._fetch_html(detail_url, use_cache=True)
            if not detail_html:
                self.logger.warning(f"詳細ページの取得に失敗しました: {detail_url}")
                return None
                
            # 3. 詳細ページから基本情報を抽出
            detail_soup = BeautifulSoup(detail_html, 'html.parser')
            
            # 馬名を抽出 (タイトルタグから取得)
            title_tag = detail_soup.find('title')
            if not title_tag:
                self.logger.warning("タイトルタグが見つかりませんでした")
                return None
                
            # タイトルから馬名部分を抽出（「|」で分割して最初の要素を取得）
            title_text = title_tag.get_text(strip=True)
            title_text = title_text.split('|')[0].strip() if '|' in title_text else title_text
            
            # 最初のスペース（全角・半角）までを馬名として抽出
            import re
            name_match = re.match(r'^([^ 　]+)', title_text)
            if not name_match:
                self.logger.warning("馬名の抽出に失敗しました")
                return None
                
            name = name_match.group(1).strip()
            self.logger.debug(f"抽出した馬名: {name} (元のテキスト: {title_text})")
                
            self.logger.debug(f"馬名を抽出: {name}")
            
            # 基本情報を辞書に格納
            horse_info = {
                'id': horse_id,  # データベース用のID（後で自動採番される）
                'auction_id': horse_id,  # オークションサイトの数値ID
                'name': name,
                'detail_url': detail_url,
                'scraped_at': datetime.now().isoformat()
            }
            
            # 基本情報テーブルから情報を抽出
            info_table = detail_soup.find('table', class_=lambda c: c and 'horse-info' in c.lower())
            if info_table:
                rows = info_table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        key = cols[0].get_text(strip=True).replace(':', '')
                        value = cols[1].get_text(strip=True)
                        horse_info[key] = value
            
            # 賞金情報を抽出
            try:
                prize_info = extract_prize_from_auction(detail_html, name)
                if prize_info:
                    horse_info.update(prize_info)
                    self.logger.debug(f'賞金情報を抽出しました: {prize_info}')
            except Exception as e:
                self.logger.warning(f'賞金情報の抽出中にエラーが発生しました: {e}')
            
            # 性別と年齢を抽出
            try:
                sex_age = self.horse_info_extractor._extract_sex_and_age(detail_soup)
                if sex_age:
                    horse_info.update(sex_age)
            except Exception as e:
                self.logger.warning(f"性別・年齢の抽出中にエラーが発生しました: {e}")
            
            # 血統情報を抽出
            try:
                pedigree = self.horse_info_extractor._extract_pedigree(detail_soup)
                if pedigree:
                    horse_info.update(pedigree)
            except Exception as e:
                self.logger.warning(f"血統情報の抽出中にエラーが発生しました: {e}")
                
            # オークション日を取得
            try:
                # 個別馬詳細ページにはオークション日が含まれていないため、リストページのURLを使用
                auction_date = self.get_auction_date(url=self.base_url)
                if auction_date:
                    horse_info['auction_date'] = auction_date
                    self.logger.info(f"オークション日を抽出しました: {auction_date}")
                    self.logger.info(f"auction_dateの型: {type(auction_date)}")
                    self.logger.info(f"auction_dateの長さ: {len(str(auction_date))}")
                else:
                    self.logger.warning("オークション日を抽出できませんでした")
            except Exception as e:
                self.logger.warning(f"オークション日の抽出中にエラーが発生しました: {e}")
            
            # 馬体重を抽出
            try:
                # 馬体重が含まれている可能性のある要素を検索
                weight_element = detail_soup.find(lambda tag: '馬体重' in tag.get_text() or '体重' in tag.get_text())
                if weight_element:
                    weight_kg = self.horse_info_extractor._extract_weight(weight_element)
                    if weight_kg is not None:
                        horse_info['weight'] = weight_kg
                        self.logger.info(f'馬体重を抽出: {weight_kg}kg (馬名: {name})')
                    else:
                        self.logger.debug(f'馬体重の抽出に失敗しました (馬名: {name})')
                else:
                    self.logger.debug(f'馬体重要素が見つかりませんでした (馬名: {name})')
            except Exception as e:
                self.logger.warning(f'馬体重の抽出中にエラーが発生しました: {str(e)} (馬名: {name})', exc_info=True)
            
            # 必須フィールドの確認
            required_fields = ['name', 'age', 'sex']
            missing_required = [f for f in required_fields if f not in horse_info or not horse_info.get(f)]
            
            # 血統情報フィールドの確認
            pedigree_fields = ['sire', 'dam', 'damsire']
            missing_pedigree = [f for f in pedigree_fields if f not in horse_info or not horse_info.get(f)]
            
            # 必須フィールドが不足している場合は処理を中断
            if missing_required:
                self.logger.warning(f"以下の必須フィールドが不足しているため、この馬の処理をスキップします: {missing_required}")
                return None
                
            # 血統情報が不足している場合は警告をログに記録
            if missing_pedigree:
                self.logger.warning(f"血統情報が不足しています: {missing_pedigree}")
            
            # デバッグ用に抽出した情報をログに出力
            self.logger.debug(f"抽出した馬情報: {horse_info}")
            
            # オークション日を取得
            self.logger.info("オークション日を取得します...")
            # 個別馬詳細ページにはオークション日が含まれていないため、リストページのURLを使用
            auction_date = self.get_auction_date(url=self.base_url)
            if auction_date:
                horse_info['auction_date'] = auction_date
                self.logger.info(f"オークション日を抽出しました: {auction_date}")
                self.logger.info(f"auction_dateの型: {type(auction_date)}")
                self.logger.info(f"auction_dateの長さ: {len(str(auction_date))}")
            else:
                self.logger.warning("オークション日を抽出できませんでした")
            
            # JBISリンクを抽出
            try:
                jbis_info = JbisLinkExtractor.extract(detail_soup, self.base_url)
                if jbis_info.get('jbis_url'):
                    horse_info.update(jbis_info)
                    self.logger.info(f"JBISリンクを抽出しました: {jbis_info['jbis_url']}")
            except Exception as e:
                self.logger.error(f"JBISリンクの抽出中にエラーが発生しました: {e}", exc_info=True)
            
            # オプションフィールドの抽出を実行
            extractors = [
                ('prize_money', 'prize_info_extractor', '賞金情報', True),
                ('price', 'price_info_extractor', '価格情報', True),
                ('seller', 'seller_info_extractor', '販売者情報', True),
                ('race_records', 'race_record_extractor', 'レース記録', True),
                ('image_url', 'image_extractor', '画像URL', True)
            ]
            
            # コメント抽出用の抽出器
            comment_extractor = getattr(self, 'comment_extractor', None)
            comment_data = None

            # 各抽出器を実行
            for field, extractor_name, display_name, _ in extractors:
                try:
                    # 抽出器が初期化されているか確認
                    extractor = getattr(self, extractor_name, None)
                    if extractor is None:
                        self.logger.warning(f"{display_name}の抽出器が初期化されていません")
                        continue
                    
                    # 抽出を実行
                    try:
                        # レコード抽出器の場合は文字列を渡す
                        if extractor_name == 'race_record_extractor':
                            result, success = extractor.extract(str(detail_html))
                        else:
                            result, success = extractor.extract(detail_soup)
                        
                        if success and result:
                            if field == 'price' and isinstance(result, dict):
                                # 価格情報の処理
                                horse_info.update(result)
                            else:
                                horse_info[field] = result
                                
                            self.logger.debug(f"{display_name}を抽出しました: {result}")
                        else:
                            self.logger.debug(f"{display_name}の抽出に失敗しました")
                            
                    except Exception as e:
                        self.logger.error(f"{display_name}の抽出中にエラーが発生しました: {e}", exc_info=True)
                        
                except Exception as e:
                    self.logger.error(f"{display_name}の抽出器の実行中にエラーが発生しました: {e}", exc_info=True)
            
            # 最後にコメントを抽出して追加
            if comment_extractor:
                try:
                    comment_data, success = comment_extractor.extract(detail_soup)
                    if success and comment_data:
                        # コメントを追加
                        horse_info.update(comment_data)
                        self.logger.debug("コメントを抽出しました")
                        
                        # コメントから疾病情報を抽出
                        if 'comment' in comment_data and comment_data['comment']:
                            disease_tags = _extract_disease_tags(comment_data['comment'])
                            if disease_tags != "なし":
                                horse_info['disease_tags'] = disease_tags.split(',')
                                self.logger.debug(f"疾病タグを抽出しました: {horse_info['disease_tags']}")
                    else:
                        self.logger.debug("コメントの抽出に失敗しました")
                except Exception as e:
                    self.logger.error(f"コメントの抽出中にエラーが発生しました: {e}", exc_info=True)
            
            # 馬の詳細情報を取得
            if 'id' in horse_info and horse_info['id']:
                try:
                    self.logger.info(f"馬の詳細情報を取得します: ID {horse_info['id']}")
                    detail_info = self.scrape_horse_details(horse_info['id'], use_cache=True)
                    if detail_info:
                        # 既存の情報を保持したまま詳細情報をマージ
                        horse_info.update(detail_info)
                        self.logger.info(f"馬の詳細情報を取得しました: {horse_info.get('name', '不明')}")
                    else:
                        self.logger.warning("馬の詳細情報の取得に失敗しました")
                except Exception as e:
                    self.logger.error(f"馬の詳細情報の取得中にエラーが発生しました: {e}", exc_info=True)
            
            # 馬名を先頭に移動するために新しい辞書を作成
            if 'name' in horse_info:
                name = horse_info.pop('name')
                horse_info = {'name': name, **horse_info}
            
            self.logger.info(f"[{index}/{total}] 馬情報の抽出が完了: {horse_info.get('name', '不明')}")
            return horse_info
            
        except Exception as e:
            self.logger.error(f"馬情報の抽出中にエラーが発生しました: {e}", exc_info=True)
            return None
            # データ保存処理
            if BACKEND_AVAILABLE:
                # 保存用のデータを準備
                save_data = result.copy()
                
                # 馬体重が数値の場合は文字列に変換
                if 'weight' in save_data and save_data['weight'] is not None:
                    if isinstance(save_data['weight'], (int, float)):
                        save_data['weight'] = str(save_data['weight'])
                    self.logger.info(f'馬体重を保存します: {save_data["weight"]}kg (馬名: {save_data.get("name", "不明")})')
                
                # 必須フィールドの確認
                required_fields = ['name', 'age', 'sex', 'sire', 'dam', 'damsire', 'seller', 'auction_date']
                missing_fields = [field for field in required_fields if not save_data.get(field)]
                
                if missing_fields:
                    self.logger.warning(f'必須フィールドが不足しています: {missing_fields} (馬名: {save_data.get("name", "不明")})')
                
                # データ保存を試行
                try:
                    self.logger.info('バックエンドにデータを保存します...')
                    save_result = save_horse(save_data)
                    
                    if save_result and 'error' in save_result:
                        self.logger.error(f'データの保存に失敗しました: {save_result["error"]} (馬名: {save_data.get("name", "不明")})')
                    else:
                        self.logger.info(f'データを正常に保存しました (馬名: {save_data.get("name", "不明")})')
                    
                    self.logger.debug(f'保存結果の詳細: {save_result}')
                    
                except Exception as e:
                    error_msg = f'データの保存中にエラーが発生しました: {str(e)} (馬名: {save_data.get("name", "不明")})'
                    self.logger.error(error_msg)
                    self.logger.error(traceback.format_exc())
                    
                    # エラー内容をファイルに保存（デバッグ用）
                    error_data = {
                        'error': str(e),
                        'traceback': traceback.format_exc(),
                        'data': save_data
                    }
                    error_file = Path('data_save_errors.json')
                    with open(error_file, 'a', encoding='utf-8') as f:
                        json.dump(error_data, f, ensure_ascii=False, indent=2)
                        f.write('\n')
                        return result

    def _extract_horse_info(self, horse_element, index: int = 0, total: int = 0) -> Optional[Dict[str, Any]]:
        """
        馬の情報を抽出する（更新版）
        
        Args:
            horse_element: 馬情報を含むHTML要素
            index: 現在のインデックス（0から開始）
            total: 総数（進捗表示用）
            
        Returns:
            抽出した馬情報の辞書。必須フィールドが不足している場合はNoneを返す
        """
        try:
            # 1. HorseInfoExtractorを使用して基本情報を抽出
            basic_info, detail_info = self.horse_info_extractor.extract(horse_element)
            
            # 2. 馬名が取得できなかった場合は致命的なエラー
            if not basic_info.get('name'):
                self.logger.error('馬名の抽出に失敗しました')
                return None
            
            # 3. 進捗表示
            progress_prefix = f'[{index+1}/{total}] ' if total > 0 else ''
            self.logger.info(f'{progress_prefix}馬情報を処理中: {basic_info["name"]}')
            
            # 4. 血統情報を抽出（HorseInfoExtractorのextractメソッドでは血統情報が抽出されないため、個別に抽出）
            if not all(field in basic_info for field in ['sire', 'dam', 'damsire']):
                try:
                    # 血統情報を抽出
                    pedigree_result = self.horse_info_extractor._extract_pedigree(horse_element)
                    if pedigree_result:
                        basic_info.update(pedigree_result)
                except Exception as e:
                    self.logger.warning(f'血統情報の抽出中にエラーが発生しました: {str(e)}')
            
            # 5. 馬体重を抽出
            if 'weight' not in basic_info:
                self.logger.debug(f'馬体重を抽出開始 (馬名: {basic_info.get("name", "不明")})')
                try:
                    # HorseInfoExtractorの_extract_weightメソッドを使用して馬体重を抽出
                    self.logger.debug('_extract_weightメソッドを呼び出します')
                    weight_kg = self.horse_info_extractor._extract_weight(horse_element)
                    self.logger.debug(f'_extract_weightメソッドの結果: {weight_kg}')
                    
                    if weight_kg is not None:
                        basic_info['weight'] = weight_kg
                        self.logger.info(f'馬体重を抽出: {basic_info["weight"]}kg (馬名: {basic_info["name"]})')
                    else:
                        self.logger.debug(f'馬体重の抽出に失敗しました (馬名: {basic_info["name"]})')
                        # デバッグ用にHTMLをログに出力
                        debug_html = str(horse_element)[:1000] + '...'  # 先頭1000文字のみ
                        self.logger.debug(f'デバッグ用HTML: {debug_html}')
                except Exception as e:
                    self.logger.error(f'馬体重の抽出中にエラーが発生しました: {str(e)} (馬名: {basic_info.get("name", "不明")})', exc_info=True)
                    # エラーが発生した場合もHTMLをログに出力
                    debug_html = str(horse_element)[:1000] + '...'  # 先頭1000文字のみ
                    self.logger.error(f'エラー発生時のHTML: {debug_html}')
            
            # 6. オークション日を抽出
            if 'auction_date' not in basic_info:
                self.logger.debug(f'オークション日を抽出開始 (馬名: {basic_info.get("name", "不明")})')
                try:
                    # horse_elementは個別の馬要素なので、HTML全文ではなくリストページのHTMLを使用
                    auction_date = self.get_auction_date(url=self.base_url)
                    if auction_date:
                        basic_info['auction_date'] = auction_date
                        self.logger.info(f'オークション日を抽出: {auction_date} (馬名: {basic_info["name"]})')
                        self.logger.info(f"auction_dateの型: {type(auction_date)}")
                        self.logger.info(f"auction_dateの長さ: {len(str(auction_date))}")
                    else:
                        self.logger.debug(f'オークション日の抽出に失敗しました (馬名: {basic_info["name"]})')
                except Exception as e:
                    self.logger.error(f'オークション日の抽出中にエラーが発生しました: {str(e)} (馬名: {basic_info.get("name", "不明")})')
                    self.logger.debug(f'エラー詳細: {traceback.format_exc()}')
            
            # 7. 必須フィールドの確認
            required_fields = ['name', 'age', 'sex', 'sire', 'dam']
            
            # 6. 必須フィールドの確認
            required_fields = ['name', 'age', 'sex', 'sire', 'dam']
            missing_required = [field for field in required_fields 
                             if field not in basic_info or basic_info[field] is None]
            
            # 7. 詳細情報があれば統合
            if detail_info:
                basic_info.update(detail_info)
            
            # 8. 不足している必須フィールドがあれば記録
            if missing_required:
                basic_info['_missing_fields'] = missing_required
                basic_info['_debug'] = {
                    'missing_fields': missing_required,
                    'source': 'improved_scraper.py',
                    'version': '2024-03-15'
                }
                
                self.logger.warning(
                    f'必須フィールドが不足しています: {missing_required} (馬名: {basic_info["name"]})'
                )
                
                # 必須フィールドが不足している場合はNoneを返す
                self.logger.error(
                    f'必須フィールドが不足しているため、馬の情報をスキップします: {missing_required} '
                    f'(馬名: {basic_info["name"]})'
                )
                return None
            
            return basic_info
            
        except Exception as e:
            self.logger.error(f'馬情報の抽出中に予期せぬエラーが発生しました: {str(e)}')
            self.logger.debug(f'エラー詳細: {traceback.format_exc()}')
            return None
        
        try:
            # HTMLをパース
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 馬のカードを取得
            horse_cards = soup.select('.auctionTableCard')
            if not horse_cards:
                self.logger.warning("馬のカードが見つかりませんでした")
                # デバッグ用にHTMLを保存
                debug_html_path = date_dir / 'debug_horse_list.html'
                try:
                    with open(debug_html_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    self.logger.warning(f"デバッグ用のHTMLを保存しました: {debug_html_path}")
                except Exception as e:
                    self.logger.error(f"デバッグ用HTMLの保存に失敗しました: {e}")
                return all_horse_info
                
            self.logger.info(f"{len(horse_cards)}頭の馬を検出しました")
            
            # 馬の情報を抽出
            for i, card in enumerate(horse_cards, 1):
                try:
                    horse_name = "不明な馬"
                    self.logger.debug(f"[{i}/{len(horse_cards)}] 馬情報の抽出を開始")
                    
                    # 馬情報の抽出（直接処理を行う）
                    horse_info = self._process_horse_info(card, i, len(horse_cards))
                    if not horse_info:
                        continue
                        
                    horse_name = horse_info.get('name', '不明な馬')
                    
                    # 詳細ページのURLを取得
                    detail_link = card.select_one('a[href*="detail"]')
                    if not detail_link:
                        self.logger.warning(f"詳細ページのリンクが見つかりません: {horse_name}")
                        continue
                        
                    detail_url = urljoin(self.base_url, detail_link.get('href', '').strip())
                    horse_info['detail_url'] = detail_url
                    
                    # 詳細ページのパスを設定
                    detail_path = detail_dir / f'detail_{i:03d}.html'
                    detail_html = None
                    
                    # 1. 既存のファイルから読み込みを試みる
                    if detail_path.exists():
                        try:
                            with open(detail_path, 'r', encoding='utf-8') as f:
                                detail_html = f.read()
                            self.logger.debug(f"既存の詳細ページを読み込みました: {detail_path}")
                        except Exception as e:
                            self.logger.warning(f"既存の詳細ページの読み込みに失敗しました: {e}")
                    
                    # 2. _fetch_htmlを使用してHTMLを取得（キャッシュを使用）
                    detail_html = self._fetch_html(detail_url, use_cache=self.use_cache)
                    
                    if not detail_html:
                        self.logger.error(f"詳細ページの取得に失敗しました: {detail_url}")
                        continue
                        
                    # 3. デバッグ用にHTMLをローカルに保存
                    debug_html_dir = Path('debug_html')
                    debug_html_dir.mkdir(exist_ok=True, mode=0o755)
                    
                    # ファイル名をURLから生成（安全なファイル名に変換）
                    safe_filename = re.sub(r'[^a-zA-Z0-9]', '_', detail_url)[:100] + '.html'
                    debug_file = debug_html_dir / safe_filename
                    
                    try:
                        with open(debug_file, 'w', encoding='utf-8') as f:
                            f.write(detail_html)
                        debug_file.chmod(0o644)  # 読み取り可能なパーミッションを設定
                        self.logger.info(f"デバッグ用HTMLを保存しました: {debug_file}")
                    except Exception as e:
                        self.logger.warning(f"デバッグ用HTMLの保存に失敗しました: {e}")
                    
                    # 4. 詳細ページをファイルに保存
                    if detail_html:
                        save_attempts = [
                            (detail_dir, f'detail_{i:03d}.html'),  # 優先パス
                            (Path.cwd(), f'detail_{i:03d}_{timestamp}.html')  # フォールバックパス
                        ]
                        
                        saved = False
                        for save_dir, filename in save_attempts:
                            save_path = save_dir / filename if isinstance(save_dir, Path) else Path(filename)
                            try:
                                # ディレクトリが存在することを確認
                                if isinstance(save_dir, Path):
                                    save_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
                                
                                # ファイルに書き込み
                                with open(save_path, 'w', encoding='utf-8') as f:
                                    f.write(detail_html)
                                
                                # パーミッション設定
                                save_path.chmod(0o644)
                                
                                self.logger.info(f"詳細ページを保存しました: {save_path}")
                                saved = True
                                break  # 保存に成功したらループを抜ける
                                
                            except Exception as e:
                                self.logger.warning(f"詳細ページの保存に失敗しました ({save_path}): {e}")
                        
                    # 馬情報をリストに追加
                    all_horse_info.append(horse_info)
                    self.logger.info(f"[{i}/{len(horse_cards)}] 馬情報を抽出しました: {horse_name}")
                    
                except Exception as e:
                    self.logger.error(f"[{i}/{len(horse_cards)}] 馬情報の抽出中にエラーが発生しました: {e}", exc_info=True)
                    
                    # 失敗した馬の情報を記録
                    if not hasattr(self, 'failed_horses'):
                        self.failed_horses = []
                        
                    self.failed_horses.append({
                        'index': i,
                        'error': str(e),
                        'horse_name': horse_name if 'horse_name' in locals() else '不明な馬'
                    })
                    
                    continue  # エラーが発生しても次の馬の処理を継続
                    
        except Exception as e:
            self.logger.error(f"スクレイピング中に予期しないエラーが発生しました: {e}", exc_info=True)
            
        finally:
            # 結果をJSONファイルに保存
            try:
                output_file = self.output_dir / f'scraped_horses_{timestamp}.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_horse_info, f, ensure_ascii=False, indent=2)
                self.logger.info(f"スクレイピング結果を保存しました: {output_file}")
            except Exception as e:
                self.logger.error(f"スクレイピング結果の保存に失敗しました: {e}")
                
            # 失敗した馬がいたらログに記録
            if hasattr(self, 'failed_horses') and self.failed_horses:
                failed_file = self.output_dir / f'failed_horses_{timestamp}.json'
                try:
                    with open(failed_file, 'w', encoding='utf-8') as f:
                        json.dump(self.failed_horses, f, ensure_ascii=False, indent=2)
                    self.logger.warning(f"{len(self.failed_horses)}頭の馬の処理に失敗しました。詳細: {failed_file}")
                except Exception as e:
                    self.logger.error(f"失敗した馬の情報の保存に失敗しました: {e}")
            
            # フロントエンド連携用にhorses_history.jsonにも保存
            try:
                output_file = self.output_dir / 'horses_history.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_horse_info, f, ensure_ascii=False, indent=2)
                self.logger.info(f"{len(all_horse_info)}頭の馬の情報を {output_file} に保存しました")
            except Exception as e:
                self.logger.error(f"horses_history.jsonの保存に失敗しました: {e}")
                
        return all_horse_info

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

    def scrape_horse_details(self, horse_id: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """馬IDを指定して詳細情報をスクレイピングする
        
        Args:
            horse_id: 馬のID
            use_cache: キャッシュを使用するかどうか
            
        Returns:
            Optional[Dict[str, Any]]: 馬の詳細情報（抽出に失敗した場合はNone）
        """
        self.logger.info(f"=== 馬の詳細情報取得を開始: 馬ID {horse_id} ===")
        self.logger.info(f"=== 馬の詳細情報取得を開始: 馬ID {horse_id} ===")
        try:
            # 詳細ページのURLを構築（正しいURL形式に修正）
            detail_url = f"{self.base_url}item/{horse_id}"
            self.logger.debug(f"詳細ページURL: {detail_url}")
            self.logger.info(f"馬の詳細ページを取得します: {detail_url}")
            
            # HTMLを取得
            html_content = self._fetch_html(detail_url, use_cache=use_cache)
            if not html_content:
                self.logger.error(f"馬の詳細ページの取得に失敗しました: {detail_url}")
                return None
                
            # BeautifulSoupオブジェクトを作成
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 馬の基本情報を抽出
            horse_info = {}
            
            # 馬IDを追加
            horse_info['id'] = horse_id
            
            # 馬名を取得
            name_elem = soup.find('h1', class_=lambda c: c and 'horse-name' in c.lower())
            if name_elem:
                horse_info['name'] = name_elem.get_text(strip=True)
            
            # 基本情報テーブルから情報を抽出
            info_table = soup.find('table', class_=lambda c: c and 'horse-info' in c.lower())
            if info_table:
                rows = info_table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        key = cols[0].get_text(strip=True).replace(':', '')
                        value = cols[1].get_text(strip=True)
                        horse_info[key] = value
            
            # レース記録を抽出
            race_record_data, race_success = self.race_record_extractor.extract(html_content)
            if race_success and race_record_data:
                # 抽出したデータをrace_recordsに保存（後でrace_recordにマッピングされる）
                horse_info['race_records'] = race_record_data
                self.logger.debug(f'抽出されたレース記録: {race_record_data}')
            else:
                self.logger.warning('レース記録の抽出に失敗しました')
                # 空の辞書で初期化（後でrace_recordにマッピングされる）
                horse_info['race_records'] = {}
                
            # オークション日は _process_horse_info で取得するため、ここでは取得しない
            
            # コメントを抽出（詳細ページのHTMLをそのまま渡す）
            comment, comment_success = self.comment_extractor.extract(soup)
            if comment_success and comment:
                horse_info['comment'] = comment
                self.logger.info(f'コメントを抽出しました（長さ: {len(comment)}文字）')
            else:
                # コメント抽出に失敗した場合、HTMLをファイルに保存してデバッグ用に残す
                debug_dir = Path('debug_html')
                debug_dir.mkdir(exist_ok=True)
                debug_file = debug_dir / f'comment_debug_{horse_id}.html'
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                self.logger.warning(f'コメントの抽出に失敗しました。デバッグ用HTMLを保存しました: {debug_file}')
            
            # 賞金情報を抽出（トップページ優先）
            try:
                name_for_log = horse_info.get('name') or ''
                top_html = self._fetch_html(self.base_url, use_cache=use_cache)
                top_prize = None
                if top_html:
                    top_prize = extract_prize_from_auction(top_html, name_for_log)
                    # total_prize_start が取れていれば反映
                    if isinstance(top_prize, dict) and int(top_prize.get('total_prize_start', 0)) > 0:
                        horse_info.update(top_prize)
                        # total_prize が未設定なら同値を設定（円）
                        if horse_info.get('total_prize') in [None, 0]:
                            horse_info['total_prize'] = int(top_prize['total_prize_start'])
                        self.logger.info(f"トップページから総賞金を抽出しました: {top_prize}")
                # フォールバック: 詳細ページから抽出
                if not isinstance(top_prize, dict) or int(top_prize.get('total_prize_start', 0)) == 0:
                    prize_info, prize_success = self.prize_info_extractor.extract(html_content)
                    if prize_success and prize_info and isinstance(prize_info, dict) and prize_info.get('total_prize') is not None:
                        horse_info.update(prize_info)
                        self.logger.info(f'詳細ページから賞金情報を抽出しました: {prize_info}')
                    else:
                        # いずれも取得できない場合の明示設定
                        horse_info['total_prize'] = None
                        if 'total_prize_start' not in horse_info:
                            horse_info['total_prize_start'] = 0
                        self.logger.warning('賞金情報の抽出に失敗したか、有効な賞金情報がありませんでした')
            except Exception as e:
                self.logger.warning(f'賞金情報の抽出処理でエラー: {e}', exc_info=True)
                # エラー時もキーを揃える
                horse_info.setdefault('total_prize', None)
                horse_info.setdefault('total_prize_start', 0)
            
            # 画像URLを抽出
            image_url, image_success = self.image_extractor.extract(html_content)
            if image_success and image_url:
                horse_info['image_url'] = image_url
            
            # オークション日は既に取得済み
            
            # 販売者情報を抽出
            seller_info, seller_success = self.seller_info_extractor.extract(soup)
            if seller_success and seller_info:
                horse_info.update(seller_info)
                self.logger.info(f'販売者情報を抽出しました: {seller_info}')
            else:
                self.logger.warning('販売者情報の抽出に失敗しました')
            
            self.logger.info(f"馬の詳細情報を抽出しました: {horse_info.get('name', '不明')}")
            return horse_info
            
        except Exception as e:
            self.logger.error(f"馬の詳細情報の抽出中にエラーが発生しました: {e}", exc_info=True)
            return None

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
            self.logger.error(f'エラーが発生しました: {e}', exc_info=True)
            return []


def setup_logging(debug=False, log_level=None, log_file=None):
    """ロギングの設定を行う
    
    Args:
        debug: デバッグモードの有効/無効
        log_level: ログレベル (logging.DEBUG, logging.INFO など)
        log_file: ログファイルのパス (Noneの場合はデフォルトのログファイルを使用)
    """
    # ログレベルの設定
    if log_level is None:
        log_level = logging.DEBUG if debug else logging.INFO
    
    # ログフォーマット
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(fmt=log_format, datefmt=date_format)
    console_handler.setFormatter(console_formatter)
    
    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # ルートは最も低いレベルに設定
    root_logger.handlers = []  # 既存のハンドラをクリア
    root_logger.addHandler(console_handler)
    
    # ファイルハンドラの設定
    if log_file is not None:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # ファイルには常にDEBUGレベルで出力
        file_formatter = logging.Formatter(fmt=log_format, datefmt=date_format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # 外部ライブラリのログレベルを制御
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('bs4').setLevel(logging.WARNING)
    
    # バックエンドモジュールのログを有効化
    if BACKEND_AVAILABLE:
        logging.getLogger('scrapers').setLevel(logging.DEBUG)
    
    return root_logger


def load_existing_horses(output_dir: Path) -> List[Dict[str, Any]]:
    """既存の馬データを読み込む"""
    output_path = output_dir / 'horses.json'
    if output_path.exists():
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    return []
                return existing_data
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []

def save_horses_to_file(horses: List[Dict[str, Any]], output_path: Path) -> bool:
    """
    馬データをファイルに保存する
    
    Args:
        horses: 保存する馬データのリスト
        output_path: 出力先のファイルパス
        
    Returns:
        bool: 保存が成功した場合はTrue、失敗した場合はFalse
    """
    try:
        # 必須フィールドを確認
        required_fields = ['id', 'name', 'sex', 'age', 'sire', 'dam', 'damsire', 'jbis_url']
        
        # 各馬のデータを検証して必須フィールドを追加
        validated_horses = []
        for horse in horses:
            # 馬IDがなければ新規生成
            if 'id' not in horse or not horse['id']:
                horse['id'] = str(uuid.uuid4())
            
            # 必須フィールドがなければ空文字を設定
            for field in required_fields:
                if field not in horse or not horse[field]:
                    horse[field] = ''
            
            # 日付フィールドを文字列に変換
            for date_field in ['auction_date', 'created_at', 'updated_at']:
                if date_field in horse and isinstance(horse[date_field], (datetime, date)):
                    horse[date_field] = horse[date_field].isoformat()
            
            validated_horses.append(horse)
        
        # ファイルに保存
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(validated_horses, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        logger.error(f'馬データの保存中にエラーが発生しました: {e}')
        return False

def update_horses_database(horses: List[Dict[str, Any]]) -> bool:
    """
    馬データをデータベースに保存する
    
    Args:
        horses: 保存する馬データのリスト
        
    Returns:
        bool: データベース更新が成功した場合はTrue、失敗した場合はFalse
    """
    try:
        # データベース更新スクリプトのパスを取得（絶対パスに変換）
        update_script_path = (Path(__file__).parent / 'update_database.py').resolve()
        
        # スクリプトが存在するか確認
        if not update_script_path.exists():
            logger.error(f"データベース更新スクリプトが見つかりません: {update_script_path}")
            return False
        
        # 一時ディレクトリのパスを絶対パスで設定
        temp_dir = (Path(__file__).parent / 'temp').resolve()
        temp_dir.mkdir(exist_ok=True, parents=True, mode=0o755)  # 適切なパーミッションを設定
        temp_json = temp_dir / 'temp_horses.json'
        
        logger.info(f"一時ファイルに馬データを保存します: {temp_json}")
        
        try:
            # 馬データを一時ファイルに保存
            with open(temp_json, 'w', encoding='utf-8') as f:
                json.dump(horses, f, ensure_ascii=False, indent=2)
            
            # スクリプトのフルパスを取得
            script_path = str(update_script_path)
            temp_json_path = str(temp_json)
            
            logger.info(f"データベース更新スクリプトを実行します: {script_path}")
            logger.info(f"一時ファイル: {temp_json_path}")
            logger.info(f"現在の作業ディレクトリ: {os.getcwd()}")
            
            # サブプロセスでデータベース更新スクリプトを実行
            result = subprocess.run(
                ['python3', script_path, '--input', temp_json_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent  # スクリプトのディレクトリをカレントディレクトリに設定
            )
            
            # 実行結果をログに出力
            if result.stdout:
                logger.info(f"スクリプト出力: {result.stdout}")
            if result.stderr:
                logger.error(f"スクリプトエラー: {result.stderr}")
            
            if result.returncode == 0:
                logger.info("データベースの更新に成功しました")
                return True
            else:
                logger.error(f"データベースの更新に失敗しました (終了コード: {result.returncode})")
                return False
                
        except Exception as e:
            logger.error(f"データベース更新スクリプトの実行中にエラーが発生しました: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        finally:
            # 一時ファイルを削除
            if temp_json.exists():
                try:
                    temp_json.unlink()
                    logger.debug(f"一時ファイルを削除しました: {temp_json}")
                except Exception as e:
                    logger.warning(f"一時ファイルの削除に失敗しました: {e}")
                
    except Exception as e:
        logger.error(f"データベース更新中に予期しないエラーが発生しました: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def save_horses(horses: List[Dict[str, Any]], output_path: Path) -> bool:
    """
    馬データをファイルとデータベースに保存する
    
    Args:
        horses: 保存する馬データのリスト
        output_path: 出力先のファイルパス
        
    Returns:
        bool: ファイルの保存とデータベースの更新の両方が成功した場合はTrue、それ以外はFalse
    """
    # ファイルに保存
    if not save_horses_to_file(horses, output_path):
        logger.error("ファイルの保存に失敗しました")
        return False
    
    # データベースを更新
    if not update_horses_database(horses):
        logger.error("データベースの更新に失敗しました")
        return False
    
    return True

def main():
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(description='楽天競馬オークションのスクレイピング')
    parser.add_argument('--debug', action='store_true', help='デバッグモードで実行')
    parser.add_argument('--no-cache', action='store_true', help='キャッシュを使用しない')
    parser.add_argument('--max-pages', type=int, default=0, help='最大取得ページ数（0は無制限）')
    parser.add_argument('--output', type=str, default='horses.json', help='出力ファイル名')
    parser.add_argument('--threads', type=int, default=5, help='並列スレッド数')
    parser.add_argument('--horse-id', type=str, help='特定の馬IDのみを処理する')
    args = parser.parse_args()
    
    # ログ設定
    logger = setup_logging(args.debug)
    logger.info('スクリプトを開始します')
    logger.info(f'バックエンドモジュール利用可能: {BACKEND_AVAILABLE}')
    
    try:
        # スクレイパーの初期化
        config = ScraperConfig(
            use_cache=not args.no_cache,
            max_workers=args.threads
        )
        
        # スクレイパーインスタンスを作成
        scraper = ImprovedRakutenScraper(config)
        
        # 出力ディレクトリを設定（フロントエンドのpublic/dataディレクトリに保存）
        script_dir = Path(__file__).parent.parent
        output_dir = script_dir / 'static-frontend' / 'public' / 'data'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / args.output
        
        # 既存の馬データを読み込む
        existing_horses = load_existing_horses(output_dir)
        existing_horses_map = {horse.get('id'): horse for horse in existing_horses if 'id' in horse}
        
        # 特定の馬IDが指定されている場合
        if args.horse_id:
            logger.info(f'馬ID {args.horse_id} の情報を取得します')
            horse_info = scraper.scrape_horse_details(args.horse_id)
            
            if horse_info:
                # 既存のデータを更新または追加（dictの場合は単一要素リストに正規化）
                horses_iterable = horse_info if isinstance(horse_info, list) else [horse_info]
                for horse in horses_iterable:
                    horse_id = horse.get('id')
                    if horse_id and horse_id in existing_horses_map:
                        # 既存のデータを更新
                        existing_horses_map[horse_id].update(horse)
                    else:
                        # 新しい馬を追加
                        if not horse_id:
                            horse_id = str(uuid.uuid4())
                            horse['id'] = horse_id
                        existing_horses_map[horse_id] = horse
                
                # 更新されたデータを保存
                updated_horses = list(existing_horses_map.values())
                if save_horses(updated_horses, output_path):
                    logger.info(f'馬情報を {output_path} に保存し、データベースを更新しました ({len(updated_horses)}頭)')
                else:
                    logger.error('馬情報の保存に失敗しました')
                    return 1
            else:
                logger.error('馬情報の取得に失敗しました')
                return 1
        else:
            # 馬一覧をスクレイピング
            logger.info('馬一覧のスクレイピングを開始します')
            results = scraper.scrape_horse_list(max_pages=args.max_pages, use_cache=not args.no_cache)
            
            if results:
                # 既存のデータを更新または追加
                for horse in results:
                    # 馬IDを抽出（detail_urlから）
                    detail_url = horse.get('detail_url', '')
                    horse_id = None
                    
                    # URLからIDを抽出（例: https://auction.keiba.rakuten.co.jp/item/14927 から 14927 を抽出）
                    if detail_url and '/item/' in detail_url:
                        horse_id = detail_url.split('/')[-1].strip()
                    
                    # IDがなければ新規生成
                    if not horse_id:
                        horse_id = str(uuid.uuid4())
                    
                    horse['id'] = horse_id
                    
                    # 既存のデータを更新または追加
                    if horse_id in existing_horses_map:
                        # 既存のデータを更新（新しいデータで上書き）
                        existing_horses_map[horse_id].update(horse)
                    else:
                        # 新しい馬を追加
                        existing_horses_map[horse_id] = horse
                
                # 更新されたデータを保存
                updated_horses = list(existing_horses_map.values())
                if save_horses(updated_horses, output_path):
                    logger.info(f'スクレイピング結果を {output_path.absolute()} に保存し、データベースを更新しました ({len(updated_horses)}頭)')
                else:
                    logger.error('スクレイピング結果の保存に失敗しました')
                    return 1
                
                # 失敗した馬がいる場合は分析
                if hasattr(scraper, 'failed_horses') and scraper.failed_horses:
                    logger.warning(f"{len(scraper.failed_horses)}頭の馬の処理に失敗しました")
                    analysis = scraper.analyze_failed_horses()
                    logger.warning(f"失敗の内訳: {analysis['reasons']}")
                    
                    if analysis['suggestions']:
                        logger.info("\n改善のための提案:")
                        for suggestion in analysis['suggestions']:
                            logger.info(f"- {suggestion}")
            else:
                logger.warning('スクレイピング結果が空です')
                return 1
        
        return 0
            
    except KeyboardInterrupt:
        logger.info('ユーザーによって中断されました')
        return 130  # SIGINTの終了コード
    except Exception as e:
        logger.error(f'スクリプトの実行中にエラーが発生しました: {e}', exc_info=True)
        return 1


if __name__ == "__main__":
    main()
