#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import logging
from bs4 import BeautifulSoup

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('seller_extraction_test.log')
    ]
)
logger = logging.getLogger(__name__)

def extract_seller_from_html(html_content, file_path):
    """HTMLから全馬の販売者情報を抽出する（リストページからのみ）"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []
        
        # 各馬のカードを取得
        horse_cards = soup.find_all('div', class_='auctionTableCard')
        
        if not horse_cards:
            logger.warning("馬のカードが見つかりませんでした")
            return []
            
        logger.info(f"{len(horse_cards)}頭の馬を検出しました")
        
        for i, card in enumerate(horse_cards, 1):
            # 馬名を取得
            name_span = card.find('span', class_='auctionTableCard__name')
            horse_name = name_span.get_text(strip=True) if name_span else f'不明な馬名 ({i})'
            
            # 販売者情報を取得
            seller_div = card.find('div', class_='auctionTableCard__seller')
            if seller_div:
                seller_span = seller_div.find('span', class_='value')
                if seller_span:
                    seller = seller_span.get_text(strip=True)
                    if seller:
                        results.append({
                            'index': i,
                            'name': horse_name,
                            'seller': seller,
                            'status': 'success'
                        })
                        logger.info(f"[{i:3d}] 成功: {horse_name} - 販売者: {seller}")
                        continue
            
            # 販売者情報が見つからなかった場合
            results.append({
                'index': i,
                'name': horse_name,
                'seller': None,
                'status': 'failed'
            })
            logger.warning(f"[{i:3d}] 失敗: {horse_name} - 販売者情報が見つかりませんでした")
        
        return results
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}\nファイル: {file_path}")
        return []
        
    except Exception as e:
        logger.error(f"[エラー] 販売者情報の抽出中にエラーが発生: {str(e)}\nファイル: {file_path}")
        return None

def test_seller_extraction(file_path):
    """指定したファイルから全馬の販売者情報を抽出してテストする"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        logger.info(f"\n{'='*80}")
        logger.info(f"ファイルを処理中: {file_path}")
        
        # 全馬の販売者情報を抽出
        results = extract_seller_from_html(html_content, file_path)
        
        if not results:
            logger.error("馬の情報を抽出できませんでした")
            return False
        
        # 結果を集計
        success_count = sum(1 for r in results if r['status'] == 'success')
        total = len(results)
        
        # サマリーを表示
        logger.info(f"\n{'='*80}")
        logger.info(f"抽出結果: {success_count}/{total} 頭の販売者情報を抽出しました (成功率: {success_count/total*100:.1f}%)")
        
        # 失敗した馬がいる場合は表示
        failed_horses = [r for r in results if r['status'] == 'failed']
        if failed_horses:
            logger.warning(f"\n販売者情報を抽出できなかった馬 ({len(failed_horses)}頭):")
            for horse in failed_horses:
                logger.warning(f"  - {horse['name']} (インデックス: {horse['index']})")
        
        return success_count > 0
        
    except FileNotFoundError:
        logger.error(f"ファイルが見つかりません: {file_path}")
        return False
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}\nファイル: {file_path}")
        return False

def main():
    if len(sys.argv) < 2:
        print("使用法: python test_seller_extraction_only.py <HTMLファイルのパス>")
        print("例: python test_seller_extraction_only.py /path/to/your/file.html")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # ディレクトリが指定された場合は、その中の全HTMLファイルを処理
    if os.path.isdir(file_path):
        logger.info(f"ディレクトリ内のHTMLファイルを処理します: {file_path}")
        html_files = [os.path.join(file_path, f) for f in os.listdir(file_path) 
                     if f.endswith('.html') and os.path.isfile(os.path.join(file_path, f))]
        
        if not html_files:
            logger.error(f"HTMLファイルが見つかりません: {file_path}")
            sys.exit(1)
            
        success_count = 0
        for html_file in html_files:
            if test_seller_extraction(html_file):
                success_count += 1
        
        logger.info(f"\n{'='*80}")
        logger.info(f"テスト結果: {success_count}/{len(html_files)} 件成功")
        
    # 単一ファイルが指定された場合
    elif os.path.isfile(file_path):
        if not file_path.endswith('.html'):
            logger.error("HTMLファイルを指定してください")
            sys.exit(1)
            
        success = test_seller_extraction(file_path)
        sys.exit(0 if success else 1)
        
    else:
        logger.error(f"ファイルまたはディレクトリが見つかりません: {file_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()
