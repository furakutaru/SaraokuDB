"""
HorseInfoExtractorの統合テストスクリプト

実際のWebページを使用してHorseInfoExtractorの動作を検証します。
"""
import sys
import os
import logging
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# モジュールのインポート
from scripts.components.horse_info_extractor import HorseInfoExtractor

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_horse_info_extractor.log')
    ]
)
logger = logging.getLogger(__name__)

# テスト用の詳細ページURL（実際のオークションの馬詳細ページ）
TEST_URLS = [
    "https://www.rakuba-kyotei.jp/keiba/auction/2025/20250831/01/01.html",
    "https://www.rakuba-kyotei.jp/keiba/auction/2025/20250831/01/02.html",
    "https://www.rakuba-kyotei.jp/keiba/auction/2025/20250831/01/03.html"
]

def fetch_html(url):
    """指定されたURLからHTMLを取得する"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None

def test_extractor():
    """HorseInfoExtractorのテストを実行"""
    extractor = HorseInfoExtractor()
    
    for url in TEST_URLS:
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing URL: {url}")
        logger.info("="*80)
        
        # HTMLを取得
        html = fetch_html(url)
        if not html:
            logger.error(f"Failed to fetch HTML from {url}")
            continue
            
        # BeautifulSoupでパース
        soup = BeautifulSoup(html, 'html.parser')
        
        # 馬情報を抽出
        result = extractor.extract_from_detail_page(html)
        
        # 結果を表示
        logger.info("\nExtraction Results:")
        for key, value in result.items():
            logger.info(f"{key}: {value}")
        
        # 必須フィールドのチェック
        required_fields = ['name', 'sex', 'age', 'sire', 'dam', 'damsire', 'seller']
        missing_fields = [field for field in required_fields if not result.get(field)]
        
        if missing_fields:
            logger.warning(f"Missing required fields: {', '.join(missing_fields)}")
        else:
            logger.info("All required fields were successfully extracted!")

if __name__ == "__main__":
    test_extractor()
