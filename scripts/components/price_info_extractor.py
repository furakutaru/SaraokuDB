"""価格情報を抽出するモジュール"""
from typing import Dict, Optional, Tuple, Any
import re
import logging
from bs4 import BeautifulSoup


class PriceInfoExtractor:
    """価格情報を抽出するクラス"""
    
    def __init__(self, logger: logging.Logger = None):
        """初期化メソッド
        
        Args:
            logger: ロガーインスタンス（Noneの場合は新規作成）
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def extract(self, horse_element) -> Tuple[Optional[Dict[str, Any]], bool]:
        """馬の要素から価格情報を抽出する
        
        Args:
            horse_element: 馬情報を含むBeautifulSoup要素
            
        Returns:
            Tuple[Optional[Dict[str, Any]], bool]: 
                (価格情報を含む辞書, 成功したかどうか)
        """
        try:
            price_info = {}
            
            # 落札価格を抽出
            # itemprop="price"属性を持つ要素を直接検索
            sold_price_elem = horse_element.select_one('div.price span[itemprop="price"]')
            if sold_price_elem:
                try:
                    price_text = sold_price_elem.get_text(strip=True)
                    price = int(price_text.replace(',', ''))
                    price_info['sold_price'] = price
                    price_info['is_unsold'] = False
                    self.logger.debug(f'落札価格を抽出しました: {price}円')
                except (ValueError, TypeError) as e:
                    self.logger.warning(f'価格の数値変換に失敗しました: {e}')
            else:
                self.logger.debug('落札価格要素が見つかりませんでした')
                # 主取りの可能性をチェック
                if '主取り' in str(horse_element):
                    price_info['is_unsold'] = True
                    self.logger.debug('主取りを検出しました')
            
            # 開始価格を抽出（オプション）
            start_price_elem = horse_element.select_one('.start-price, .opening-bid')
            if start_price_elem:
                start_price_text = start_price_elem.get_text(strip=True)
                start_price_match = re.search(r'[\d,]+', start_price_text)
                if start_price_match:
                    try:
                        start_price = int(start_price_match.group().replace(',', ''))
                        price_info['starting_price'] = start_price
                    except (ValueError, TypeError) as e:
                        self.logger.debug(f'開始価格の数値変換に失敗しました: {e}')
            
            # 価格情報が1つも見つからなかった場合
            if not price_info:
                self.logger.debug('価格情報が見つかりませんでした')
                return None, False
            
            self.logger.debug(f'価格情報を抽出しました: {price_info}')
            return price_info, True
            
        except Exception as e:
            self.logger.error(f'価格情報の抽出中にエラーが発生しました: {e}', exc_info=True)
            return None, False
    
    def _is_unsold(self, price_text: str) -> bool:
        """価格テキストから未落札かどうかを判定する
        
        Args:
            price_text: 価格テキスト
            
        Returns:
            bool: 未落札の場合はTrue、それ以外はFalse
        """
        if not price_text:
            return False
            
        # 未落札を示す可能性のあるキーワード
        unsold_keywords = [
            '未落札', '売れ残り', '不成立', 'キャンセル',
            'unsold', 'not sold', 'cancelled', 'no bid'
        ]
        
        # 大文字小文字を区別せずにチェック
        price_text_lower = price_text.lower()
        return any(keyword.lower() in price_text_lower for keyword in unsold_keywords)
