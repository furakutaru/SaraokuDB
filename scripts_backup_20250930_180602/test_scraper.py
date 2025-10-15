#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
楽天競馬オークションのテストスクリプト

このスクリプトは、楽天競馬オークションのスクレイピング機能をテストするためのユーティリティです。
"""

import os
import sys
import argparse
import logging
import re
import json
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Any, Optional, Tuple

# 親ディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TestScraper:
    """スクレイピング機能をテストするためのクラス"""
    
    def __init__(self, cache_dir: str = 'test_cache'):
        """テストスクレイパーの初期化"""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.base_url = "https://auction.keiba.rakuten.co.jp/"
    
    def clean_horse_name(self, raw_name: str) -> str:
        """馬名をクリーンアップする関数
        
        Args:
            raw_name (str): 生の馬名（例："ソリッドベーシス　　セン３歳　　※中央競馬　登録抹消"）
        
        Returns:
            str: クリーンアップされた馬名（例："ソリッドベーシス"）
        """
        if not raw_name:
            return ""
        # 最初の半角・全角スペース以降を削除
        name = re.split(r'[ 　]', raw_name, 1)[0]
        return name.strip()

    def extract_horse_info(self, file_path: str) -> Dict[str, Any]:
        """HTMLファイルから馬の情報を抽出する"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 基本情報の抽出
            result = {
                'file': str(file_path),
                'extracted_data': {},
                'html_structure': {}
            }
            
            # 1. 馬名の抽出
            # 馬名の抽出とクリーニング
            name_elem = soup.select_one('title')
            if name_elem:
                raw_name = name_elem.get_text(strip=True).split('|')[0]
                result['extracted_data']['name'] = self.clean_horse_name(raw_name)
            else:
                result['extracted_data']['name'] = '名前が見つかりませんでした'
            
            # 2. 基本情報のテーブルを探す
            info_table = soup.select_one('table')
            if info_table:
                # テーブル内のテキストを取得
                table_text = info_table.get_text(' ', strip=True)
                result['extracted_data']['table_text'] = table_text
                
                # 血統情報の抽出
                pedigree_match = re.search(r'父：([^\s]+)\s*母：([^\s]+)\s*母の父：([^\s]+)', table_text)
                if pedigree_match:
                    result['extracted_data']['sire'] = pedigree_match.group(1)
                    result['extracted_data']['dam'] = pedigree_match.group(2)
                    result['extracted_data']['damsire'] = pedigree_match.group(3)
                
                # 通算成績の抽出
                record_match = re.search(r'通算成績：([^\s]+)', table_text)
                if record_match:
                    result['extracted_data']['record'] = record_match.group(1)
                
                # 獲得賞金の抽出
                prize_match = re.search(r'中央獲得賞金：([\d,.]+)万円', table_text)
                if prize_match:
                    result['extracted_data']['prize_money'] = float(prize_match.group(1).replace(',', ''))
            
            # 3. 画像URLの抽出
            img_elem = soup.select_one('img[src*="/horse/"]')
            if img_elem:
                img_src = img_elem.get('src', '')
                result['extracted_data']['image_url'] = urljoin(self.base_url, img_src) if img_src else ''
            
            # 4. コメントの抽出（文字数制限なしで全文を取得）
            comment_elem = soup.find('div', class_=lambda x: x and 'comment' in x.lower())
            if comment_elem:
                result['extracted_data']['comment'] = comment_elem.get_text(' ', strip=True)  # 全文を取得
            
            # HTML構造の解析
            result['html_structure']['tables'] = len(soup.find_all('table'))
            result['html_structure']['images'] = len(soup.find_all('img'))
            result['html_structure']['links'] = len(soup.find_all('a'))
            
            # 主要な要素のクラスを記録
            result['html_structure']['common_classes'] = {}
            for elem in soup.find_all(class_=True):
                for cls in elem['class']:
                    result['html_structure']['common_classes'][cls] = result['html_structure']['common_classes'].get(cls, 0) + 1
            
            # 上位10個のクラスのみを保持
            result['html_structure']['common_classes'] = dict(
                sorted(result['html_structure']['common_classes'].items(), 
                      key=lambda x: x[1], reverse=True)[:10]
            )
            
            return result
            
        except Exception as e:
            logger.error(f"HTMLの解析中にエラーが発生しました: {e}")
            return {'error': str(e), 'file': str(file_path)}
    
    def analyze_html_structure(self, file_path: str) -> Dict[str, Any]:
        """HTMLの構造を分析する"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 主要な要素を抽出
            result = {
                'title': str(soup.title.string) if soup.title else 'No title',
                'tables': [],
                'metadata': {
                    'tables_count': len(soup.find_all('table')),
                    'images_count': len(soup.find_all('img')),
                    'links_count': len(soup.find_all('a')),
                    'divs_count': len(soup.find_all('div')),
                    'spans_count': len(soup.find_all('span')),
                },
                'common_classes': {}
            }
            
            # テーブルの構造を分析
            for i, table in enumerate(soup.find_all('table')[:3]):  # 最初の3つのテーブルのみ
                table_info = {
                    'index': i,
                    'rows': len(table.find_all('tr')),
                    'cells': len(table.find_all(['td', 'th'])),
                    'sample_text': table.get_text(' ', strip=True)[:200] + '...'  # 最初の200文字のみ
                }
                result['tables'].append(table_info)
            
            # 一般的なクラスをカウント
            for elem in soup.find_all(class_=True):
                for cls in elem['class']:
                    result['common_classes'][cls] = result['common_classes'].get(cls, 0) + 1
            
            # 上位10個のクラスのみを保持
            result['common_classes'] = dict(
                sorted(result['common_classes'].items(), 
                      key=lambda x: x[1], reverse=True)[:10]
            )
            
            return result
            
        except Exception as e:
            logger.error(f"HTML構造の分析中にエラーが発生しました: {e}")
            return {'error': str(e), 'file': str(file_path)}
    
    def extract_auction_info(self, file_path: str) -> Dict[str, Any]:
        """オークション情報を抽出する"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            result = {}
            
            # 価格情報の抽出
            price_elem = soup.select_one('.price')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                result['price_text'] = price_text
                
                # 数値の抽出
                price_match = re.search(r'(\d{1,3}(?:,\d{3})*)', price_text)
                if price_match:
                    result['price'] = int(price_match.group(1).replace(',', ''))
                
                # 未落札のチェック
                result['is_unsold'] = any(x in price_text.lower() for x in ['未落札', 'unsold', '不成立'])
            
            return result
            
        except Exception as e:
            logger.error(f"オークション情報の抽出中にエラーが発生しました: {e}")
            return {'error': str(e)}
            sex_elem = soup.select_one('.horseLabelWrapper__horseSex')
            age_elem = soup.select_one('.horseLabelWrapper__horseAge')
            
            sex = sex_elem.get_text(strip=True) if sex_elem else '性別不明'
            age = age_elem.get_text(strip=True) if age_elem else '年齢不明'
            
            # 販売者情報の抽出を試みる
            seller_elem = soup.select_one('.auctionTableCard__seller .value')
            seller = seller_elem.get_text(strip=True) if seller_elem else '販売者情報なし'
            
            # 賞金情報の抽出を試みる
            prize_elem = soup.select_one('.auctionTableCard__price .value')
            prize = prize_elem.get_text(strip=True) if prize_elem else '賞金情報なし'
            
            result = {
                'name': name,
                'sex': sex,
                'age': age,
                'seller': seller,
                'prize': prize,
                'debug': {
                    'name_element': bool(name_elem),
                    'sex_element': bool(sex_elem),
                    'age_element': bool(age_elem),
                    'seller_element': bool(seller_elem),
                    'prize_element': bool(prize_elem)
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"HTMLのパース中にエラーが発生しました: {str(e)}")
            return {}
    
    def run_tests(self, test_dir: str) -> Dict[str, Any]:
        """指定されたディレクトリ内のすべてのHTMLファイルをテストする"""
        test_dir = Path(test_dir)
        if not test_dir.exists():
            logger.error(f"テストディレクトリが見つかりません: {test_dir}")
            return {}
        
        results = {}
        html_files = list(test_dir.glob('**/*.html'))
        
        if not html_files:
            logger.warning(f"テスト用のHTMLファイルがありません: {test_dir}")
            return {}
        
        for html_file in html_files:
            logger.info(f"テスト中: {html_file.name}")
            result = self.test_parse_html(str(html_file))
            if result:
                results[html_file.name] = result
        
        return results

def main():
    """メインの実行関数"""
    parser = argparse.ArgumentParser(description='楽天競馬オークションのスクレイピングテスト')
    parser.add_argument('file', help='テストするHTMLファイルのパス')
    parser.add_argument('--cache-dir', default='test_cache', help='キャッシュディレクトリ')
    parser.add_argument('--mode', choices=['extract', 'analyze', 'auction'], default='extract',
                       help='実行モード: extract=情報抽出, analyze=HTML構造分析, auction=オークション情報抽出')
    args = parser.parse_args()
    
    scraper = TestScraper(cache_dir=args.cache_dir)
    
    if not os.path.exists(args.file):
        logger.error(f"ファイルが見つかりません: {args.file}")
        return 1
    
    logger.info(f"ファイルを解析中: {args.file}")
    
    if args.mode == 'extract':
        result = scraper.extract_horse_info(args.file)
        print("\n=== 抽出結果 ===")
        print(json.dumps(result['extracted_data'], ensure_ascii=False, indent=2))
        
    elif args.mode == 'analyze':
        result = scraper.analyze_html_structure(args.file)
        print("\n=== HTML構造分析結果 ===")
        print(f"タイトル: {result.get('title')}")
        print("\nメタデータ:")
        for k, v in result.get('metadata', {}).items():
            print(f"  {k}: {v}")
        
        print("\nテーブル情報:")
        for i, table in enumerate(result.get('tables', [])):
            print(f"  テーブル {i+1}: {table['rows']}行, {table['cells']}セル")
            print(f"  サンプル: {table['sample_text']}")
        
        print("\nよく使われるクラス:")
        for cls, count in result.get('common_classes', {}).items():
            print(f"  .{cls}: {count}回")
            
    elif args.mode == 'auction':
        result = scraper.extract_auction_info(args.file)
        print("\n=== オークション情報 ===")
        print(f"価格テキスト: {result.get('price_text', 'N/A')}")
        print(f"価格: {result.get('price', 'N/A'):,}円" if 'price' in result else "価格: N/A")
        print(f"未落札: {'はい' if result.get('is_unsold') else 'いいえ'}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
