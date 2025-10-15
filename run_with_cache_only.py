#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
キャッシュのみを使用してスクレイピングを実行するスクリプト
"""
import json
import os
import sys
import logging
import hashlib
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime

# Selenium関連のインポート
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# プロジェクトのルートディレクトリをPythonのパスに追加
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# バックエンドモジュールをインポート
try:
    from scripts.improved_scraper import ImprovedRakutenScraper, ScraperConfig
    from scripts.utils.common import setup_logging, ensure_directory, save_to_json, load_from_json
    BACKEND_AVAILABLE = True
except ImportError as e:
    print(f"バックエンドモジュールのインポートに失敗しました: {e}")
    print(f"現在のPythonパス: {sys.path}")
    BACKEND_AVAILABLE = False

# デフォルト設定
DEFAULT_CONFIG = {
    'use_cache': True,
    'cache_dir': 'cache',
    'log_level': 'INFO',
    'log_file': 'logs/cache_scraper.log',
    'output_dir': 'output',
    'max_retries': 0,
    'timeout': 30,
    'use_mobile': True
}

class CacheScraperConfig(ScraperConfig):
    """キャッシュ専用スクレイパーの設定クラス"""
    
    def __init__(self, **kwargs):
        # デフォルト設定で初期化
        config = {**DEFAULT_CONFIG, **kwargs}
        
        # 親クラスの初期化
        super().__init__(
            use_cache=config['use_cache'],
            cache_dir=config['cache_dir'],
            max_retries=config['max_retries'],
            timeout=config['timeout'],
            use_mobile=config['use_mobile'],
            log_level=config['log_level'],
            log_file=config['log_file']
        )
        
        # 出力ディレクトリの設定
        self.output_dir = Path(config['output_dir'])
        ensure_directory(self.output_dir)
        
        # ログディレクトリの作成
        if 'log_file' in config and config['log_file']:
            log_dir = Path(config['log_file']).parent
            ensure_directory(log_dir)


def setup_selenium_driver() -> Optional[webdriver.Chrome]:
    """Selenium WebDriverをセットアップする"""
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        logging.error(f"WebDriverの初期化に失敗しました: {e}")
        return None


def fetch_auction_page(url: str, cache_dir: Path, logger: logging.Logger) -> Optional[str]:
    """オークションページを取得してキャッシュに保存する"""
    cache_key = hashlib.md5(url.encode('utf-8')).hexdigest()
    cache_file = cache_dir / f"{cache_key}.html"
    
    # 既存のキャッシュがあれば返す
    if cache_file.exists() and cache_file.stat().st_size > 0:
        logger.info(f"既存のキャッシュを使用します: {cache_file}")
        return cache_file.read_text(encoding='utf-8')
    
    # Seleniumでページを取得
    driver = setup_selenium_driver()
    if not driver:
        return None
    
    try:
        logger.info(f"オークションページにアクセス中: {url}")
        driver.get(url)
        
        # ページの読み込みを待機
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(5)  # 動的コンテンツの読み込みを待機
        
        page_source = driver.page_source
        if not page_source or len(page_source) < 1000:
            logger.error("無効なページソースが返されました")
            return None
            
        # キャッシュに保存
        temp_file = cache_file.with_suffix('.tmp')
        temp_file.write_text(page_source, encoding='utf-8')
        
        if temp_file.stat().st_size > 0:
            temp_file.replace(cache_file)
            logger.info(f"キャッシュを保存しました: {cache_file} (サイズ: {cache_file.stat().st_size} バイト)")
            return page_source
        
        logger.error("キャッシュの保存に失敗しました")
        return None
        
    except Exception as e:
        logger.error(f"ページの取得中にエラーが発生しました: {e}")
        
    finally:
        driver.quit()


def fetch_horse_detail(url: str, cache_dir: Path, logger: logging.Logger) -> Optional[str]:
    """馬の詳細ページを取得する"""
    try:
        # キャッシュキーを生成
        cache_key = hashlib.md5(url.encode('utf-8')).hexdigest()
        cache_file = cache_dir / "details" / f"{cache_key}.html"
        
        # キャッシュディレクトリがなければ作成
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        # キャッシュが存在する場合は読み込む
        if cache_file.exists() and cache_file.stat().st_size > 0:
            logger.debug(f"既存のキャッシュを使用します: {cache_file}")
            return cache_file.read_text(encoding='utf-8')
        
        # Seleniumでページを取得
        driver = setup_selenium_driver()
        if not driver:
            return None
            
        try:
            logger.info(f"馬の詳細ページにアクセス中: {url}")
            driver.get(url)
            
            # ページの読み込みを待機
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)  # 動的コンテンツの読み込みを待機
            
            page_source = driver.page_source
            if not page_source or len(page_source) < 1000:
                logger.error("無効なページソースが返されました")
                return None
                
            # キャッシュに保存
            temp_file = cache_file.with_suffix('.tmp')
            temp_file.write_text(page_source, encoding='utf-8')
            
            if temp_file.stat().st_size > 0:
                temp_file.replace(cache_file)
                logger.info(f"キャッシュを保存しました: {cache_file} (サイズ: {cache_file.stat().st_size} バイト)")
                return page_source
            
            logger.error("キャッシュの保存に失敗しました")
            return None
            
        except Exception as e:
            logger.error(f"ページの取得中にエラーが発生しました: {e}")
            return None
            
        finally:
            driver.quit()
            
    except Exception as e:
        logger.error(f"馬の詳細ページの取得中にエラーが発生しました: {e}")
        return None

def extract_seller_from_detail(html_content: str, logger: logging.Logger) -> str:
    """詳細ページのHTMLから販売者情報を抽出する"""
    try:
        # BeautifulSoupを使用してHTMLをパース
        from bs4 import BeautifulSoup
        
        # まずは生のHTMLから直接検索を試みる（コメントアウトされている部分も含めて検索）
        raw_seller_match = re.search(r'販売申込者[：:]([^<\n（]+)', html_content)
        if raw_seller_match:
            seller = raw_seller_match.group(1).strip()
            # 不要な空白や改行を削除
            seller = ' '.join(seller.split())
            logger.info(f"生HTMLから販売者を抽出: {seller}")
            return seller
        
        # BeautifulSoupでパースして検索
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. コメント内を検索
        for comment in soup.find_all(string=lambda text: isinstance(text, str) and '販売申込者' in text):
            match = re.search(r'販売申込者[：:]([^<\n（]+)', comment)
            if match:
                seller = match.group(1).strip()
                seller = ' '.join(seller.split())
                logger.info(f"コメントから販売者を抽出: {seller}")
                return seller
        
        # 2. 通常の要素を検索
        seller_elements = soup.find_all(['div', 'span', 'p', 'td', 'pre'], string=re.compile(r'販売申込者[:：]'))
        
        for element in seller_elements:
            seller_text = element.get_text(strip=True)
            # 「販売申込者：」の後ろのテキストを抽出
            match = re.search(r'販売申込者[:：]\s*([^\n<（]+)', seller_text)
            if match:
                seller = match.group(1).strip()
                seller = ' '.join(seller.split())
                logger.info(f"要素から販売者を抽出: {seller}")
                return seller
        
        # 3. preタグ内を検索（整形済みテキスト用）
        pre_elements = soup.find_all('pre')
        for pre in pre_elements:
            pre_text = pre.get_text()
            match = re.search(r'販売申込者[：:]([^\n<（]+)', pre_text)
            if match:
                seller = match.group(1).strip()
                seller = ' '.join(seller.split())
                logger.info(f"preタグから販売者を抽出: {seller}")
                return seller
        
        # 4. 最終手段として生HTML全体を正規表現で検索
        seller_patterns = [
            r'販売申込者[:：]\s*([^<\n（]+)',  # カッコ前までを取得
            r'<[^>]*>販売申込者[:：][\s\S]*?>([^<]+)<',
            r'販売者[:：]\s*([^<\n（]+)'
        ]
        
        for pattern in seller_patterns:
            match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
            if match:
                seller = match.group(1).strip()
                seller = ' '.join(seller.split())
                logger.info(f"正規表現で販売者を抽出: {seller}")
                return seller
                
        logger.warning("販売者情報が見つかりませんでした")
        return "販売者情報なし"
        
    except Exception as e:
        logger.error(f"販売者情報の抽出中にエラーが発生しました: {e}", exc_info=True)
        return "抽出エラー"
        return "販売者情報取得エラー"

def parse_horse_descriptions(html_content: str, cache_dir: Path, logger: logging.Logger) -> List[Dict[str, str]]:
    """HTMLから馬の説明文をパースする"""
    try:
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        horses = []
        
        # 馬のリストを取得
        horse_items = soup.select('.auctionList__item')
        
        if not horse_items:
            logger.error("馬のリストが見つかりませんでした")
            return []
            
        logger.info(f"{len(horse_items)}頭の馬を検出しました")
        
        for i, item in enumerate(horse_items, 1):
            try:
                # 馬名を取得
                name_elem = item.select_one('.auctionList__name')
                if not name_elem:
                    logger.warning(f"馬名が見つかりません (馬 {i})")
                    continue
                    
                name = name_elem.get_text(strip=True)
                
                # 性別と父名を取得
                info_elem = item.select_one('.auctionList__info')
                if not info_elem:
                    logger.warning(f"馬の情報が見つかりません: {name}")
                    continue
                    
                info_text = info_elem.get_text(strip=True)
                sex_match = re.search(r'性別[:：]\s*([^\s]+)', info_text)
                sire_match = re.search(r'父[:：]\s*([^\s]+)', info_text)
                
                sex = sex_match.group(1) if sex_match else "不明"
                sire = sire_match.group(1) if sire_match else "不明"
                
                # 詳細ページのURLを取得
                detail_link = item.find('a', href=True)
                if not detail_link:
                    logger.warning(f"詳細ページのリンクが見つかりません: {name}")
                    continue
                    
                detail_url = detail_link['href']
                if not detail_url.startswith('http'):
                    detail_url = f"https://auction.keiba.rakuten.co.jp{detail_url}"
                
                horse_data = {
                    'name': name,
                    'sex': sex,
                    'sire': sire,
                    'description': "",  # 詳細ページから取得する
                    'seller': '販売者情報取得中...',
                    'id': str(i),
                    'detail_url': detail_url
                }
                
                # 詳細ページを取得
                detail_html = fetch_horse_detail(detail_url, cache_dir, logger)
                if detail_html:
                    # 販売者情報を抽出
                    seller = extract_seller_from_detail(detail_html, logger)
                    horse_data['seller'] = seller
                    
                    # 説明文を抽出（必要な場合）
                    description_elem = BeautifulSoup(detail_html, 'html.parser').select_one('.horseDescription')
                    if description_elem:
                        horse_data['description'] = description_elem.get_text(strip=True)
                
                horses.append(horse_data)
                logger.info(f"馬情報を抽出しました: {name} (性別: {sex}, 父: {sire}, 販売者: {horse_data['seller']})")
                
            except Exception as e:
                logger.error(f"馬情報の抽出中にエラーが発生しました (馬 {i}): {e}")
        
        logger.info(f"合計 {len(horses)}頭の馬情報を抽出しました")
        return horses
        
    except Exception as e:
        logger.error(f"馬のデータのパース中にエラーが発生しました: {e}")
        return []

def save_results(horses: List[Dict[str, Any]], output_dir: Path, logger: logging.Logger) -> None:
    """結果を保存する"""
    if not horses:
        logger.warning("保存するデータがありません")
        return
    
    try:
        # 出力ディレクトリの作成
        ensure_directory(output_dir)
        
        # タイムスタンプ付きのファイル名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f'horses_{timestamp}.json'
        
        # 結果を保存
        result = {
            'metadata': {
                'version': '1.0',
                'generated_at': datetime.now().isoformat(),
                'total_horses': len(horses)
            },
            'horses': horses
        }
        
        save_to_json(result, output_file, indent=2)
        logger.info(f"結果を保存しました: {output_file} (馬数: {len(horses)}頭)")
        
    except Exception as e:
        logger.error(f"結果の保存中にエラーが発生しました: {e}")


def extract_seller_info(html_content: str, file_path: Path, logger: logging.Logger) -> Dict[str, str]:
    """HTMLから販売者情報を抽出する"""
    try:
        # ファイル名から馬IDを取得
        horse_id = file_path.stem
        
        # 販売者情報を抽出
        seller = extract_seller_from_detail(html_content, logger)
        
        # 馬名を抽出（オプション）
        horse_name = ""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 馬名が含まれる可能性のある要素を検索
            name_elements = soup.find_all(['h1', 'h2', 'h3', 'div', 'span', 'p'], 
                                        string=re.compile(r'[\u4e00-\u9fff]+'))
            
            for elem in name_elements:
                text = elem.get_text(strip=True)
                # 適当な長さでフィルタ（2文字以上20文字以下）
                if 2 <= len(text) <= 20 and '販売' not in text and '申込' not in text:
                    horse_name = text
                    break
                    
        except Exception as e:
            logger.debug(f"馬名の抽出に失敗しました: {e}")
        
        return {
            'id': horse_id,
            'name': horse_name,
            'seller': seller,
            'source_file': str(file_path),
            'extracted_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"販売者情報の抽出中にエラーが発生しました: {e}", exc_info=True)
        return {}

def process_cache_files(cache_dir: Path, output_dir: Path, logger: logging.Logger, extract_type: str = 'seller') -> None:
    """キャッシュディレクトリ内のファイルを処理する
    
    Args:
        cache_dir: キャッシュディレクトリのパス
        output_dir: 出力ディレクトリのパス
        logger: ロガー
        extract_type: 抽出する情報の種類 ('seller' または 'all')
    """
    try:
        # キャッシュディレクトリ内のHTMLファイルを検索
        cache_files = list(cache_dir.glob('**/*.html'))
        
        if not cache_files:
            logger.warning(f"キャッシュファイルがありません: {cache_dir}")
            return
            
        logger.info(f"{len(cache_files)}個のキャッシュファイルを処理します (抽出タイプ: {extract_type})")
        
        results = []
        
        for i, cache_file in enumerate(cache_files, 1):
            try:
                logger.info(f"処理中: {cache_file} ({i}/{len(cache_files)})")
                
                # キャッシュファイルを読み込み
                with open(cache_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # 指定されたタイプの情報を抽出
                if extract_type == 'seller':
                    result = extract_seller_info(html_content, cache_file, logger)
                else:
                    # デフォルトは馬情報を抽出
                    result = extract_horse_from_detail(html_content, logger)
                    if result:
                        result['source_file'] = str(cache_file)
                
                if result:
                    results.append(result)
                    logger.info(f"抽出完了: {result.get('name', '不明')} - 販売者: {result.get('seller', '不明')}")
                
            except Exception as e:
                logger.error(f"キャッシュファイルの処理中にエラーが発生しました ({cache_file}): {e}")
        
        # 結果を保存
        if results:
            output_file = output_dir / f"extracted_{extract_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"抽出結果を保存しました: {output_file} (レコード数: {len(results)}件)")
        else:
            logger.warning("抽出された情報がありません")
            
    except Exception as e:
        logger.error(f"キャッシュファイルの処理中にエラーが発生しました: {e}", exc_info=True)

def extract_horse_from_detail(html_content: str, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """詳細ページのHTMLから馬情報を抽出する"""
    try:
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 馬名を取得
        name_elem = soup.select_one('.horseName')
        if not name_elem:
            logger.warning("馬名が見つかりませんでした")
            return None
            
        name = name_elem.get_text(strip=True)
        
        # 性別と年齢を取得
        info_text = ''
        info_elem = soup.select_one('.horseInfo')
        if info_elem:
            info_text = info_elem.get_text(strip=True)
            
        sex_match = re.search(r'性別[:：]\s*([^\s]+)', info_text)
        age_match = re.search(r'([0-9]+)歳', info_text)
        sire_match = re.search(r'父[:：]\s*([^\s]+)', info_text)
        
        # 販売者情報を抽出
        seller = extract_seller_from_detail(html_content, logger)
        
        # 説明文を取得
        description = ''
        desc_elem = soup.select_one('.horseDescription')
        if desc_elem:
            description = desc_elem.get_text(strip=True)
        
        return {
            'name': name,
            'sex': sex_match.group(1) if sex_match else "不明",
            'age': int(age_match.group(1)) if age_match else 0,
            'sire': sire_match.group(1) if sire_match else "不明",
            'seller': seller,
            'description': description,
            'source': 'cache',
            'extracted_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"馬情報の抽出中にエラーが発生しました: {e}", exc_info=True)
        return None

def get_available_methods():
    """利用可能なメソッドの一覧を返す"""
    from scripts.improved_scraper import ImprovedRakutenScraper
    
    # メインスクレイパーのインスタンスを作成
    scraper = ImprovedRakutenScraper()
    
    # メソッド一覧を取得（プライベートメソッドと特殊メソッドを除外）
    methods = [
        method for method in dir(scraper) 
        if callable(getattr(scraper, method)) 
        and not method.startswith('_')
    ]
    
    # コンポーネントのメソッドも追加
    components = ['horse_info_extractor', 'race_record_extractor', 'price_extractor']
    for comp in components:
        try:
            comp_obj = getattr(scraper, comp, None)
            if comp_obj:
                comp_methods = [
                    f"{comp}.{m}" for m in dir(comp_obj) 
                    if callable(getattr(comp_obj, m)) 
                    and not m.startswith('_')
                ]
                methods.extend(comp_methods)
        except Exception as e:
            print(f"Warning: Could not load methods from {comp}: {e}")
    
    return sorted(methods)

def execute_method(scraper, method_path, html_content, logger):
    """指定されたメソッドを実行して結果を返す"""
    try:
        # コンポーネントのメソッドかどうかをチェック
        if '.' in method_path:
            comp_name, method_name = method_path.split('.')
            comp = getattr(scraper, comp_name, None)
            if not comp:
                raise ValueError(f"Component {comp_name} not found")
            method = getattr(comp, method_name, None)
        else:
            method = getattr(scraper, method_path, None)
        
        if not method:
            raise ValueError(f"Method {method_path} not found")
        
        # メソッドを実行
        logger.info(f"Executing method: {method_path}")
        
        # メソッドの引数に応じて適切な引数を渡す
        import inspect
        sig = inspect.signature(method)
        params = sig.parameters
        
        args = []
        kwargs = {}
        
        # 引数に応じて適切な値を渡す
        for name, param in params.items():
            if name == 'self':
                continue
            elif name in ['horse_element', 'html_content']:
                # horse_element または html_content パラメータには HTML コンテンツを渡す
                kwargs[name] = html_content
            elif name == 'logger':
                kwargs[name] = logger
            elif param.default != inspect.Parameter.empty:
                kwargs[name] = param.default
            else:
                # デフォルト値がない必須の引数にはNoneを渡す
                kwargs[name] = None
        
        # メソッドを実行
        result = method(*args, **kwargs)
        return result
        
    except Exception as e:
        logger.error(f"Error executing method {method_path}: {e}", exc_info=True)
        return None

def main():
    """メイン処理"""
    import argparse
    from scripts.improved_scraper import ImprovedRakutenScraper, ScraperConfig
    
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(description='楽天競馬オークションのスクレイピングツール')
    
    # 基本オプション
    parser.add_argument('--cache-dir', type=str, help='処理するキャッシュディレクトリを指定')
    parser.add_argument('--output-dir', type=str, default='output', help='出力ディレクトリを指定')
    parser.add_argument('--log-level', type=str, default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='ログレベルを指定')
    
    # メソッド実行オプション
    method_group = parser.add_argument_group('メソッド実行オプション')
    method_group.add_argument('--list-methods', action='store_true',
                            help='利用可能なメソッドの一覧を表示して終了')
    method_group.add_argument('--method', type=str, default='horse_info_extractor.extract',
                            help='実行するメソッドを指定 (例: horse_info_extractor.extract)')
    method_group.add_argument('--method-args', type=str, nargs='*',
                            help='メソッドに渡す引数 (key=value 形式)')
    
    # 旧オプション（互換性のため）
    parser.add_argument('--extract', type=str, default=None,
                       choices=['seller', 'all'],
                       help='互換性のためのオプション（非推奨）')
    
    args = parser.parse_args()
    
    # 設定の初期化
    config = CacheScraperConfig(log_level=args.log_level)
    
    # ロガーの設定
    logger = setup_logging(
        log_level=config.log_level,
        log_file=config.log_file
    )
    
    logger.info("キャッシュ専用スクレイパーを開始します")
    
    # メソッド一覧を表示して終了
    if args.list_methods:
        print("\n利用可能なメソッド:")
        for method in get_available_methods():
            print(f"  - {method}")
        print("\n例: python run_with_cache_only.py --cache-dir cache/20231011 --method horse_info_extractor.extract\n")
        return
    
    # メインスクレイパーのインスタンスを作成
    scraper = ImprovedRakutenScraper()
    
    try:
        # 出力ディレクトリを準備
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # キャッシュディレクトリが指定されている場合
        if args.cache_dir:
            cache_dir = Path(args.cache_dir)
            if not cache_dir.exists() or not cache_dir.is_dir():
                logger.error(f"指定されたキャッシュディレクトリが見つかりません: {cache_dir}")
                return
            
            logger.info(f"キャッシュディレクトリを処理します: {cache_dir}")
            
            # 互換性のための旧オプション処理
            if args.extract:
                logger.warning("--extract オプションは非推奨です。--method オプションを使用してください。")
                if args.extract == 'seller':
                    args.method = 'horse_info_extractor._extract_seller_info'
            
            # キャッシュファイルを処理
            results = []
            cache_files = list(cache_dir.glob('**/*.html'))
            
            if not cache_files:
                logger.warning(f"キャッシュファイルがありません: {cache_dir}")
                return
                
            logger.info(f"{len(cache_files)}個のキャッシュファイルを処理します")
            
            for i, cache_file in enumerate(cache_files, 1):
                try:
                    logger.info(f"処理中: {cache_file} ({i}/{len(cache_files)})")
                    
                    # キャッシュファイルを読み込み
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    # メソッドを実行
                    result = execute_method(scraper, args.method, html_content, logger)
                    
                    if result is not None:
                        # 結果にファイル情報を追加
                        if isinstance(result, dict):
                            result['source_file'] = str(cache_file)
                            result['extracted_at'] = datetime.now().isoformat()
                        results.append(result)
                        logger.info(f"抽出完了: {str(result)[:100]}...")
                
                except Exception as e:
                    logger.error(f"{cache_file} の処理中にエラーが発生しました: {e}")
            
            # 結果を保存
            if results:
                # 出力ファイル名を生成
                method_name = args.method.replace('.', '_')
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = output_dir / f"extracted_{method_name}_{timestamp}.json"
                
                # 結果を保存
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                logger.info(f"抽出結果を保存しました: {output_file} (レコード数: {len(results)}件)")
            else:
                logger.warning("抽出された情報がありません")
            
            return
        
        # 通常のスクレイピング処理（キャッシュディレクトリが指定されていない場合）
        logger.info("通常モードで実行します")
        
        # オークションページのURL（オークション一覧ページを直接指定）
        auction_url = "https://auction.keiba.rakuten.co.jp/auction/list/"
        
        # キャッシュディレクトリの準備
        cache_dir = Path(config.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # ページの取得
        html_content = fetch_auction_page(auction_url, cache_dir, logger)
        if not html_content:
            logger.error("ページの取得に失敗しました")
            return
        
        # メソッドを実行
        result = execute_method(scraper, args.method, html_content, logger)
        
        # 結果を保存
        if result is not None:
            output_file = output_dir / f"result_{args.method.replace('.', '_')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info(f"結果を保存しました: {output_file}")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
    finally:
        logger.info("処理が完了しました")
    return 0

if __name__ == "__main__":
    main()
