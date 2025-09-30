"""販売者情報を抽出するモジュール"""
from typing import Dict, Optional, Tuple
import re
import logging
from bs4 import BeautifulSoup


class SellerInfoExtractor:
    """販売者情報を抽出するクラス"""
    
    def __init__(self, logger: logging.Logger = None):
        """初期化メソッド
        
        Args:
            logger: ロガーインスタンス（Noneの場合は新規作成）
        """
        self.logger = logger or logging.getLogger(__name__)
        
    def extract(self, card) -> Tuple[Optional[Dict[str, str]], bool]:
        """馬のカードから販売者情報を抽出する
        
        Args:
            card: 馬のカード要素 (BeautifulSoupオブジェクト)
            
        Returns:
            Tuple[Optional[Dict[str, str]], bool]: 
                (販売者情報を含む辞書, 成功したかどうか)
        """
        try:
            # 販売者情報の要素を探す
            seller_elem = card.find('div', class_='seller')
            if not seller_elem:
                self.logger.debug('販売者情報の要素が見つかりませんでした')
                return None, False
                
            # 販売者名を抽出してクリーンアップ
            seller_text = self._get_text_from_element(seller_elem)
            seller_name = self._clean_seller_name(seller_text)
            
            if not seller_name:
                self.logger.debug('販売者名の抽出に失敗しました')
                return None, False
                
            seller_info = {
                'seller': seller_name
            }
            
            # URLがあれば取得
            seller_link = seller_elem.find('a', href=True)
            if seller_link and seller_link.get('href'):
                seller_info['seller_url'] = seller_link['href']
            
            self.logger.debug(f'販売者情報を抽出しました: {seller_info}')
            return seller_info, True
            
        except Exception as e:
            self.logger.error(f'販売者情報の抽出中にエラーが発生しました: {e}', exc_info=True)
            return None, False
    
    def _clean_seller_name(self, seller: str) -> str:
        """販売者名をクリーンアップする
        
        Args:
            seller: クリーンアップ前の販売者名
            
        Returns:
            str: クリーンアップされた販売者名
        """
        if not seller:
            return ""
            
        # 不要な空白と改行を削除
        seller = ' '.join(seller.split())
        
        # 販売者名から不要なテキストを削除
        patterns = [
            r'^[\s\u3000]*(出品者|販売者|セラー|売主)[\s\u3000]*[:：]?[\s\u3000]*',  # 接頭辞
            r'[\s\u3000]*$',  # 末尾の空白
            r'[\r\n\t]+',  # 改行やタブ
            r'\s{2,}',  # 連続する空白
            r'^\s+|\s+$'  # 先頭と末尾の空白
        ]
        
        for pattern in patterns:
            seller = re.sub(pattern, ' ', seller)
            
        return seller.strip()
        
    def _get_text_from_element(self, element) -> str:
        """要素からテキストを取得し、正規化する"""
        if not element:
            return ""
            
        # テキストを取得し、正規化
        text = element.get_text(' ', strip=True)
        return ' '.join(text.split())
