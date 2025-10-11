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
from typing import Dict, List, Optional, Any, Union

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

# バックエンドディレクトリをPythonのパスに追加
backend_dir = str(Path(project_root) / 'backend')
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# スクリプトディレクトリをPythonのパスに追加
scripts_dir = str(Path(project_root) / 'scripts')
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

# バックエンドモジュールをインポート
try:
    from scripts.improved_scraper import ImprovedRakutenScraper, ScraperConfig
    print("バックエンドモジュールのインポートに成功しました")
except ImportError as e:
    print(f"バックエンドモジュールのインポートに失敗しました: {e}")
    print(f"現在のPythonパス: {sys.path}")
    raise

def setup_logging():
    """ロギングの設定"""
    # ログディレクトリの作成
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # ログファイルの設定
    log_file = log_dir / 'cache_only_scraper.log'
    
    # ロギングの基本設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def main():
    """メイン処理"""
    # ロギングの設定
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 馬情報を格納するリストを初期化
    horses = []
    
    try:
        # キャッシュのみを使用する設定
        config = ScraperConfig(
            use_cache=True,  # キャッシュを使用
            max_retries=0,   # リトライなし（キャッシュのみ）
            max_workers=1,   # 並列処理を無効化
            timeout=10,      # タイムアウトを短く設定
            use_mobile=True  # モバイル版を使用
        )
        
        # スクレイパーを初期化
        scraper = ImprovedRakutenScraper(config=config)
        
        # オークションリストページのURL（実際のスクレイピングで使用されるURLに合わせて調整）
        auction_list_url = "https://auction.keiba.rakuten.co.jp/"
        cache_dir = Path('cache')
        cache_dir.mkdir(exist_ok=True, parents=True)
        cache_key = hashlib.md5(auction_list_url.encode('utf-8')).hexdigest()
        cache_file = cache_dir / f"{cache_key}.html"
        
        # 既存のキャッシュを確認
        if cache_file.exists() and os.path.getsize(cache_file) > 0:
            logger.info(f"既存のキャッシュファイルが見つかりました: {cache_file}")
        else:
            # Seleniumの設定
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            # WebDriverの初期化
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            try:
                logger.info(f"オークションリストページにアクセス中: {auction_list_url}")
                driver.get(auction_list_url)
                
                # ページが完全に読み込まれるまで待機（最大20秒）
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # 少し待機して動的コンテンツが読み込まれるのを待つ
                time.sleep(5)
                
                # ページソースを取得
                page_source = driver.page_source
                
                # ページソースが有効か確認
                if not page_source or len(page_source) < 1000:  # 適切な最小サイズに調整
                    logger.error("無効なページソースが返されました")
                    return
                    
                logger.info(f"ページソースのサイズ: {len(page_source)} バイト")
                
                try:
                    # 一時ファイルに保存
                    temp_file = cache_file.with_suffix('.tmp')
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        f.write(page_source)
                        
                    # ファイルが正しく保存されたか確認
                    if not temp_file.exists() or os.path.getsize(temp_file) == 0:
                        logger.error("一時ファイルの保存に失敗しました")
                        return
                        
                    # 一時ファイルを正式なキャッシュファイルに移動
                    temp_file.replace(cache_file)
                    
                    logger.info(f"オークションリストページをキャッシュに保存しました: {cache_file} (サイズ: {os.path.getsize(cache_file)} バイト)")
                    
                    # ファイルの最初の100文字をログに記録
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        first_100 = f.read(100)
                        logger.debug(f"キャッシュファイルの先頭100文字: {first_100}...")
                        
                except Exception as e:
                    logger.error(f"キャッシュファイルの保存中にエラーが発生しました: {e}")
                    return
                
                logger.info("オークションリストページの取得とキャッシュが完了しました")
                
            except Exception as e:
                logger.error(f"オークションリストページの取得中にエラーが発生しました: {e}")
                if not cache_file.exists():
                    logger.error("キャッシュファイルが存在しないため、処理を終了します")
                logger.warning("既存のキャッシュを使用して続行します")
                
            finally:
                # ブラウザを閉じる
                driver.quit()
                # キャッシュからHTMLを読み込む
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # JavaScriptから馬のデータを抽出
                import re
                
                # 正規表現で馬のデータを抽出
                pattern = r'getPickupHorse:.*?data:\{title:"[^"]+",body:"([^"]+)",startTime', re.DOTALL
                match = re.search(pattern, html_content)
                
                if not match:
                    logger.error("馬のデータが見つかりませんでした")
                    return
                
                # 馬の説明文を取得
                horse_descriptions = match.group(1).replace('\\r\\n', '\n').split('\n\n')
                
                # 馬のデータを抽出する正規表現
                horse_pattern = r'☆([^（]+)（([^）]+)・父([^）]+)）([\s\S]*?)(?=\n\n|$)'
                
                horses = []
                for desc in horse_descriptions:
                    match = re.search(horse_pattern, desc)
                    if match:
                        name = match.group(1).strip()
                        sex = match.group(2).strip()
                        sire = match.group(3).strip()
                        description = match.group(4).strip()
                        
                        horse_data = {
                            'name': name,
                            'sex': sex,
                            'sire': sire,
                            'description': description,
                            'detail_url': f"https://auction.keiba.rakuten.co.jp/detail/{len(horses) + 1}",
                            'id': str(len(horses) + 1)
                        }
                        horses.append(horse_data)
                
                if not horses:
                    logger.warning("馬のデータを抽出できませんでした")
                    return
                logger.info(f"{len(horses)}頭の馬情報を抽出しました")
                
            except Exception as e:
                logger.error(f"キャッシュからのデータ抽出中にエラーが発生しました: {e}")
                return
        
        # 結果をファイルに保存
        output_dir = Path('static-frontend/public/data')
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / 'horses.json'
        
        # 既存の馬データを読み込む
        existing_horses = {}
        if output_path.exists():
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    if isinstance(existing_data, list):
                        existing_horses = {h['id']: h for h in existing_data if 'id' in h}
                    elif isinstance(existing_data, dict) and 'horses' in existing_data:
                        existing_horses = {h['id']: h for h in existing_data['horses'] if 'id' in h}
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning(f"既存の馬データの読み込み中にエラーが発生しました: {e}")
            except Exception as e:
                logger.error(f"予期しないエラーが発生しました: {e}")
        
        # 新しいデータで既存のデータを更新
        for horse in horses:
            if 'id' in horse and horse['id']:
                existing_horses[horse['id']] = horse
        
        # 更新したデータを保存
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(list(existing_horses.values()), f, ensure_ascii=False, indent=2)
            logger.info(f"馬データを {output_path} に保存しました")
        except Exception as e:
            logger.error(f"馬データの保存に失敗しました: {e}")
        logger.info("スクレイピングが完了しました")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
