"""
JBISリンクを抽出するモジュール
"""
import re
import logging
from typing import Optional, Tuple
from urllib.parse import urljoin

# ロガー設定
logger = logging.getLogger(__name__)

def extract_jbis_link(card) -> Tuple[Optional[str], bool]:
    """
    馬のカードからJBISリンクを抽出する
    
    Args:
        card: BeautifulSoupのカード要素
        
    Returns:
        Tuple[Optional[str], bool]: 
            - 抽出したJBISリンク（相対URLの場合は絶対URLに変換）
            - 成功可否（True: 成功, False: 失敗）
    """
    try:
        # JBISリンクを検索
        jbis_link = None
        
        # 1. data-jbis-href 属性を確認
        jbis_elem = card.select_one('[data-jbis-href]')
        if jbis_elem and jbis_elem.get('data-jbis-href'):
            jbis_link = jbis_elem['data-jbis-href']
        
        # 2. JBISリンクがまだ見つからなければ、aタグのhrefを確認
        if not jbis_link:
            jbis_links = card.select('a[href*="jbis.or.jp"]')
            if jbis_links:
                jbis_link = jbis_links[0]['href']
        
        # 3. 相対URLの場合は絶対URLに変換
        if jbis_link and jbis_link.startswith('/'):
            jbis_link = urljoin('https://www.jbis.or.jp', jbis_link)
        
        # 4. 有効なJBIS URLか確認
        if jbis_link and not _is_valid_jbis_url(jbis_link):
            return None, False
            
        return jbis_link, bool(jbis_link)
        
    except Exception as e:
        logger.warning(f'JBISリンクの抽出に失敗しました: {e}')
        return None, False

def _is_valid_jbis_url(url: str) -> bool:
    """有効なJBISのURLかどうかを検証する"""
    if not url:
        return False
        
    # JBISのドメインを含むか確認
    if 'jbis.or.jp' not in url:
        return False
    
    # 有効な馬の詳細ページかチェック
    if not re.search(r'/horse/\d+', url):
        return False
        
    return True
