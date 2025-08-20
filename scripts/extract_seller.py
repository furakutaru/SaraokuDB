"""
販売者情報を抽出するモジュール

このモジュールは、楽天競馬オークションの詳細ページから販売者情報を抽出する機能を提供します。
improved_scraper.py の _extract_seller メソッドと同様のロジックを実装しています。
"""

import re
import logging
from bs4 import BeautifulSoup
from typing import Optional

# ロギング設定
logger = logging.getLogger(__name__)

def clean_seller_name(seller: str) -> str:
    """販売者名をクリーンアップする。
    
    Args:
        seller: 抽出した販売者名
        
    Returns:
        str: クリーンアップされた販売者名
    """
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
    ]
    
    for pattern in patterns:
        seller = re.sub(pattern, ' ', seller)
    
    return seller.strip()

def extract_seller(soup: BeautifulSoup) -> str:
    """売主情報を抽出する。
    
    複数の方法で売主情報を抽出し、最初に一致したものを返します。
    1. 販売申込者パターンのチェック
    2. テーブルから販売者情報を抽出
    3. フッターやコピーライトから販売者情報を抽出
    4. キーワード（売主、販売者、出品者、セラー）を元に検索
    5. 生のHTMLテキストから正規表現で検索
    
    Args:
        soup: BeautifulSoupオブジェクト
        
    Returns:
        str: 抽出した販売者名。見つからない場合は空文字列
    """
    if not soup:
        logger.warning("BeautifulSoupオブジェクトが無効です")
        return ""

    logger.info("販売者情報の抽出を開始します")
    html_text = str(soup)
    
    # 0. 販売申込者パターンを最初にチェック
    try:
        logger.info("販売申込者パターンで検索を開始")
        seller_match = re.search(r'販売申込者[：:]([^<\n（]+)', html_text)
        if seller_match:
            raw_seller = seller_match.group(1).strip()
            logger.info(f"抽出した生の販売者情報: '{raw_seller}'")
            seller = clean_seller_name(raw_seller)
            logger.info(f"クリーニング後の販売者情報: '{seller}'")
            if seller:
                logger.info(f"販売申込者から販売者を抽出: {seller}")
                return seller
            else:
                logger.warning("クリーニング後の販売者情報が空です")
        else:
            logger.info("販売申込者パターンに一致する情報が見つかりませんでした")
    except Exception as e:
        logger.error(f"販売申込者からの抽出でエラー: {e}", exc_info=True)

    # 1. テーブルから販売者情報を抽出
    try:
        # テーブル内のセラー情報を検索
        seller_tables = soup.find_all('table', class_=lambda x: x and 'seller' in x.lower())
        for table in seller_tables:
            rows = table.find_all('tr')
            for row in rows:
                th = row.find('th')
                td = row.find('td')
                if th and td and any(keyword in th.get_text().strip() for keyword in ['売主', '販売者', '出品者', 'セラー']):
                    seller = clean_seller_name(td.get_text().strip())
                    if seller:
                        logger.info(f"テーブルから販売者を抽出: {seller}")
                        return seller
    except Exception as e:
        logger.debug(f"テーブルからの販売者抽出でエラー: {e}")

    # 2. フッターやコピーライトから抽出（コメントアウト）
    """
    # ユーザーの要望によりフッター検索は無効化
    try:
        footer = soup.find('footer') or soup.find('div', class_=lambda x: x and 'footer' in x.lower())
        if footer:
            seller_match = re.search(r'売主[：:]([^\n<]+)', footer.get_text())
            if seller_match:
                seller = clean_seller_name(seller_match.group(1))
                if seller:
                    logger.info(f"フッターから販売者を抽出: {seller}")
                    return seller
    except Exception as e:
        logger.debug(f"フッターからの販売者抽出でエラー: {e}")
    """
    try:
        footer = soup.find('footer') or soup.find('div', class_=lambda x: x and 'footer' in x.lower())
        if footer:
            seller_match = re.search(r'売主[：:]([^\n<]+)', footer.get_text())
            if seller_match:
                seller = clean_seller_name(seller_match.group(1))
                if seller:
                    logger.info(f"フッターから販売者を抽出: {seller}")
                    return seller
    except Exception as e:
        logger.debug(f"フッターからの販売者抽出でエラー: {e}")

    # 3. キーワードを元に検索（販売申込者も含める）
    keywords = ['売主', '販売者', '出品者', 'セラー', '販売申込者']
    keywords = ['売主', '販売者', '出品者', 'セラー']
    for keyword in keywords:
        try:
            elements = soup.find_all(string=re.compile(keyword))
            for elem in elements:
                text = elem.get_text().strip()
                if keyword in text:
                    seller_match = re.search(f'{keyword}[：:]([^\n<]+)', text)
                    if seller_match:
                        seller = clean_seller_name(seller_match.group(1))
                        if seller:
                            logger.info(f"キーワード「{keyword}」から販売者を抽出: {seller}")
                            return seller
        except Exception as e:
            logger.debug(f"キーワード「{keyword}」からの販売者抽出でエラー: {e}")

    # 4. 生のHTMLテキストから正規表現で検索（最後の手段）
    try:
        html_text = str(soup)
        seller_match = re.search(r'(?:売主|販売者|出品者|セラー)[：:]([^<\n]+)', html_text)
        if seller_match:
            seller = clean_seller_name(seller_match.group(1))
            if seller:
                logger.info(f"正規表現で販売者を抽出: {seller}")
                return seller
    except Exception as e:
        logger.debug(f"正規表現での販売者抽出でエラー: {e}")

    logger.warning("販売者情報が見つかりませんでした")
    return ""

# テスト用コード
if __name__ == "__main__":
    import sys
    from bs4 import BeautifulSoup
    
    # ロギング設定
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python extract_seller.py <html_file>")
        sys.exit(1)
    
    try:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            html = f.read()
        
        soup = BeautifulSoup(html, 'html.parser')
        seller = extract_seller(soup)
        
        if seller:
            print(f"抽出された販売者: {seller}")
        else:
            print("販売者情報が見つかりませんでした")
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        sys.exit(1)
