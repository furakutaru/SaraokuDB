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
            
            # 1. 入札数をチェック
            bid_count_elem = horse_element.select_one('.topBidder__number--highLighted')
            if bid_count_elem:
                try:
                    bid_count = int(bid_count_elem.get_text(strip=True))
                    if bid_count == 0:
                        price_info['is_unsold'] = True
                        price_info['sold_price'] = None
                        self.logger.debug(f'入札数が0のため主取りと判定: 入札数={bid_count}')
                        return price_info, True
                except (ValueError, TypeError) as e:
                    self.logger.warning(f'入札数の取得に失敗しました: {e}')
            
            # 2. 落札価格の抽出
            price_span = horse_element.select_one('span[itemprop="price"]')
            if price_span:
                try:
                    price_text = price_span.get_text(strip=True).replace(',', '')
                    if price_text.isdigit():
                        price = int(price_text)
                        price_info['sold_price'] = price
                        price_info['is_unsold'] = False
                        self.logger.debug(f'落札価格を抽出しました: {price}円')
                        return price_info, True
                except (ValueError, TypeError) as e:
                    self.logger.warning(f'価格の取得に失敗しました: {e}')
            
            # 3. 価格情報が取得できなかった場合
            self.logger.warning('価格情報が見つかりませんでした')
            return None, False
            
        except Exception as e:
            self.logger.error(f'価格情報の抽出中に予期せぬエラーが発生しました: {e}', exc_info=True)
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
