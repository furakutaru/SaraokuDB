#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
落札価格抽出モジュール

このモジュールは、楽天競馬オークションのHTMLから落札価格を抽出する機能を提供します。
"""

import re
import logging
from typing import Optional, Union
from bs4 import BeautifulSoup

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def extract_sold_price(html_content: str) -> Optional[Union[int, str]]:
    """HTMLコンテンツから落札価格を抽出する
    
    Args:
        html_content (str): 抽出元のHTMLコンテンツ
        
    Returns:
        Optional[Union[int, str]]: 落札価格（円単位）または「主取り」の文字列。見つからない場合はNone
    """
    try:
        # BeautifulSoupでHTMLをパース
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. 主取りのチェック
        # 主取りを示す可能性のあるテキストを検索
        unsold_keywords = ['主取り', '不成立', '落札不成立', '売却不成立']
        for keyword in unsold_keywords:
            if keyword in html_content:
                logger.info(f"主取りを検出: {keyword}")
                return "主取り"
        
        # 2. 通常の価格抽出
        # itemprop="price"属性を持つ要素を検索
        price_element = soup.find(attrs={"itemprop": "price"})
        
        if price_element:
            # 価格テキストを取得し、数値のみを抽出
            price_text = price_element.get_text(strip=True)
            price_str = re.sub(r'[^\d]', '', price_text)
            if price_str:  # 数値が抽出できた場合のみ変換
                return int(price_str)
        
        # 3. 価格が見つからない場合
        logger.warning("価格要素が見つかりませんでした")
        return None
        
    except Exception as e:
        logger.error(f"価格の抽出中にエラーが発生しました: {str(e)}")
        return None

def main():
    """コマンドラインからの実行用"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python extract_sold_price.py <html_file>")
        sys.exit(1)
    
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    price = extract_sold_price(html_content)
    if price is not None:
        print(f"落札価格: {price}円")
    else:
        print("落札価格の抽出に失敗しました")

if __name__ == "__main__":
    main()
