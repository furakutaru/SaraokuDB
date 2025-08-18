import os
import time
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
from pathlib import Path

# ログ設定
log_file = 'auction_download.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_cache_dir():
    """日付ベースのキャッシュディレクトリを取得する"""
    today = datetime.now().strftime('%Y%m%d')
    cache_base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / 'cache'
    cache_dir = cache_base_dir / today
    details_dir = cache_dir / 'details'
    
    # ディレクトリがなければ作成
    details_dir.mkdir(parents=True, exist_ok=True)
    return str(cache_dir), str(details_dir)

def download_auction_list():
    """オークション一覧をダウンロードする"""
    base_url = "https://auction.keiba.rakuten.co.jp/"
    cache_dir, details_dir = get_cache_dir()
    
    # セッションを開始
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
    })
    
    try:
        logging.info(f"オークション一覧ページにアクセス中: {base_url}")
        response = session.get(base_url, timeout=30)
        response.raise_for_status()
        
        # レスポンスを保存
        list_file = os.path.join(cache_dir, 'list.html')
        with open(list_file, 'wb') as f:
            f.write(response.content)
        
        logging.info(f"オークション一覧を保存しました: {list_file}")
        
        # メタデータを保存
        metadata = {
            'downloaded_at': datetime.now().isoformat(),
            'url': base_url,
            'status': 'success'
        }
        
        metadata_file = os.path.join(cache_dir, 'metadata.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return list_file
        
    except Exception as e:
        logging.error(f"オークション一覧のダウンロード中にエラーが発生しました: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    import json
    downloaded_file = download_auction_list()
    if downloaded_file:
        print(f"オークション一覧をダウンロードしました: {downloaded_file}")
    else:
        print("オークション一覧のダウンロードに失敗しました")
