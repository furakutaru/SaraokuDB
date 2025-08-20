#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import logging
from bs4 import BeautifulSoup

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_seller(html_content):
    """HTMLから販売者情報を抽出する"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 販売者情報を保持する変数
        seller = None
        
        # 1. テーブルから販売者情報を抽出
        seller_tables = soup.find_all('table', class_=lambda x: x and 'seller' in (x or '').lower())
        for table in seller_tables:
            rows = table.find_all('tr')
            for row in rows:
                th = row.find('th')
                td = row.find('td')
                if th and td and any(keyword in th.get_text().strip() for keyword in ['売主', '販売者', '出品者', 'セラー']):
                    seller = td.get_text().strip()
                    if seller:
                        logger.info(f"テーブルから販売者を抽出: {seller}")
                        return seller
        
        # 2. フッターやコピーライトから抽出
        footer = soup.find('footer') or soup.find('div', class_=lambda x: x and 'footer' in (x or '').lower())
        if footer:
            seller_match = re.search(r'売主[：:]([^\n<]+)', footer.get_text())
            if seller_match:
                seller = seller_match.group(1).strip()
                if seller:
                    logger.info(f"フッターから販売者を抽出: {seller}")
                    return seller
        
        # 3. キーワードを元に検索
        keywords = ['売主', '販売者', '出品者', 'セラー']
        for keyword in keywords:
            elements = soup.find_all(string=re.compile(keyword))
            for element in elements:
                text = element.get_text()
                match = re.search(rf'{keyword}[：:]([^\n<]+)', text)
                if match:
                    seller = match.group(1).strip()
                    if seller:
                        logger.info(f"キーワード '{keyword}' から販売者を抽出: {seller}")
                        return seller
        
        # 4. 生のHTMLテキストから正規表現で検索
        text_matches = re.findall(r'売主[：:]([^<\n]+)', html_content)
        if text_matches:
            seller = text_matches[0].strip()
            if seller:
                logger.info(f"生HTMLから販売者を抽出: {seller}")
                return seller
        
        # 5. 最終手段: フッター付近のテキストから抽出
        footer_text = str(soup.find('footer') or '')
        if not footer_text:
            footer_text = html_content[-2000:]  # 最後の2000文字を取得
            
        seller_match = re.search(r'売主[：:]([^<\n]+)', footer_text)
        if seller_match:
            seller = seller_match.group(1).strip()
            if seller:
                logger.info(f"フッター付近から販売者を抽出: {seller}")
                return seller
        
        logger.warning("販売者情報が見つかりませんでした")
        return None
        
    except Exception as e:
        logger.error(f"販売者情報の抽出中にエラーが発生: {str(e)}")
        return None

def clean_seller_name(seller):
    """販売者名をクリーンアップする"""
    if not seller:
        return ""
        
    # 不要な空白と改行を削除
    seller = ' '.join(seller.split())
    
    # 不要な文字列を削除
    patterns = [
        r'^[：:]+\s*',  # 先頭の記号とスペース
        r'\s*[：:]+$',  # 末尾の記号とスペース
        r'^[\s　]+',    # 先頭の全角・半角スペース
        r'[\s　]+$',    # 末尾の全角・半角スペース
        r'\s+',         # 連続するスペースを1つに
        r'※.*$',        # コメントを削除
        r'（株）',       # 法人表記を正規化
        r'\(有\)',     # 有効表記を正規化
    ]
    
    for pattern in patterns:
        seller = re.sub(pattern, ' ', seller)
    
    return seller.strip()

def main():
    # テスト対象のHTMLファイルを読み込む
    html_file = "/Users/yum.ishii/SaraokuDB/cache/20250818/list.html"
    
    if not os.path.exists(html_file):
        logger.error(f"ファイルが見つかりません: {html_file}")
        return 1
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        logger.info(f"ファイルを読み込みました: {html_file}")
        
        # 販売者情報を抽出
        seller = extract_seller(html_content)
        
        if seller:
            # 販売者名をクリーンアップ
            cleaned_seller = clean_seller_name(seller)
            print(f"\n===== 抽出結果 =====")
            print(f"抽出した販売者: {seller}")
            print(f"クリーンアップ後: {cleaned_seller}")
        else:
            print("販売者情報を抽出できませんでした")
            
            # デバッグ用にHTMLの一部を表示
            print("\n===== HTMLの一部 =====")
            print(html_content[:1000] + "...")
            
        return 0
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
