#!/usr/bin/env python3
"""
馬体重抽出メソッドの単体テスト用スクリプト
"""
import sys
import logging
from pathlib import Path
from bs4 import BeautifulSoup
import requests
import urllib3

# SSL警告を非表示に
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# プロジェクトのルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

# モジュールから抽出クラスをインポート
from scripts.components.horse_info_extractor import HorseInfoExtractor

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_weight_extractor.log', 'w', 'utf-8')
    ]
)
logger = logging.getLogger(__name__)

def test_extract_weight_from_html(html_content: str, source: str = "unknown") -> 'int | None':
    """HTMLコンテンツから馬体重を抽出して返す"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        extractor = HorseInfoExtractor()
        weight = extractor._extract_weight(soup)
        
        if weight is not None:
            logger.info(f"✅ 馬体重を抽出しました: {weight}kg (from {source})")
        else:
            logger.warning(f"⚠️ 馬体重を抽出できませんでした (from {source})")
            
            # デバッグ用にHTMLを保存
            with open('debug_weight.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info("デバッグ用にHTMLを保存しました: debug_weight.html")
            
        return weight
        
    except Exception as e:
        logger.error(f"❌ エラーが発生しました (from {source}): {str(e)}", exc_info=True)
        return None

def test_with_url(url: str):
    """URLからHTMLを取得してテスト"""
    try:
        logger.info(f"\n🔍 URLからテストを開始: {url}")
        
        # ヘッダーを設定してリクエスト
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # verify=False を追加してSSL証明書の検証をスキップ
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        response.encoding = 'utf-8'  # 明示的にエンコーディングを指定
        response.raise_for_status()
        
        # 抽出を実行
        weight = test_extract_weight_from_html(response.text, f"URL: {url}")
        return weight
        
    except Exception as e:
        logger.error(f"URLからの取得中にエラーが発生しました: {str(e)}", exc_info=True)
        return None

def test_with_file(file_path: str):
    """ファイルからHTMLを読み込んでテスト"""
    try:
        logger.info(f"\n📂 ファイルからテストを開始: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # 抽出を実行
        weight = test_extract_weight_from_html(html_content, f"File: {file_path}")
        return weight
        
    except Exception as e:
        logger.error(f"ファイルの読み込み中にエラーが発生しました: {str(e)}", exc_info=True)
        return None

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='馬体重抽出ツール')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--url', help='テストするURLを指定')
    group.add_argument('--file', help='テストするHTMLファイルを指定')
    
    args = parser.parse_args()
    
    if args.url:
        test_with_url(args.url)
    elif args.file:
        test_with_file(args.file)
    else:
        # デフォルトのテストケース（例）
        logger.info("テスト用のURLまたはファイルを指定してください。")
        logger.info("例1: python test_weight_extractor.py --url 'https://example.com/horse/123'")
        logger.info("例2: python test_weight_extractor.py --file 'path/to/horse_page.html'")

if __name__ == "__main__":
    main()
