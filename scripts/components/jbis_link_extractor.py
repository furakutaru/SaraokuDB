"""
JBISリンク抽出コンポーネント

このモジュールは、BeautifulSoupオブジェクトからJBISのリンクを抽出する機能を提供します。
"""

import re
import logging
from urllib.parse import urljoin
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class JbisLinkExtractor:
    """JBISリンクを抽出するクラス"""
    
    @staticmethod
    def extract(soup, base_url: str = '') -> Dict[str, str]:
        """BeautifulSoupオブジェクトからJBISリンクを抽出する
        
        Args:
            soup: BeautifulSoupオブジェクト
            base_url: 相対URLを解決するためのベースURL
            
        Returns:
            Dict[str, str]: 抽出したJBISリンクを含む辞書
        """
        result = {'jbis_url': ''}
        
        try:
            # JBISへのリンクを探す（一般的なパターン）
            jbis_links = soup.find_all('a', href=True, string=re.compile(r'JBIS|血統|競走馬|競走成績'))
            
            # 見つからない場合は、hrefに'jbis'が含まれるリンクを探す
            if not jbis_links:
                jbis_links = soup.find_all('a', href=re.compile(r'jbis', re.IGNORECASE))
            
            # 適切なリンクを選択
            for link in jbis_links:
                href = link.get('href', '').strip()
                if 'jbis' in href.lower() and 'horse' in href.lower():
                    # 相対URLの場合はベースURLと結合
                    if not href.startswith(('http://', 'https://')) and base_url:
                        href = urljoin(base_url, href)
                    result['jbis_url'] = href
                    break
            
            logger.info(f"[JBIS_LINK] 抽出したJBISリンク: {result['jbis_url']}")
            
        except Exception as e:
            logger.error(f"[JBIS_LINK_ERROR] JBISリンクの抽出中にエラーが発生しました: {str(e)}", exc_info=True)
        
        return result
