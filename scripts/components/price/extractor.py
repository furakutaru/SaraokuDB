"""
価格情報を抽出するモジュール
"""
import re
import traceback
from typing import Dict, Any

class PriceExtractor:
    """価格情報を抽出するクラス"""
    
    def extract(self, html_content: str) -> Dict[str, Any]:
        """
        HTMLから価格情報を抽出する
        
        Args:
            html_content (str): 抽出元のHTML
            
        Returns:
            Dict[str, Any]: 抽出した価格情報
                - sold_price (float or None): 落札価格（万円単位）
                - is_unsold (bool): 主取りフラグ
                - bid_count (int): 入札数
        """
        result = {
            'sold_price': None,
            'is_unsold': False,
            'bid_count': 0
        }
        
        try:
            # 入札数の抽出
            bid_count_match = re.search(r'class="topBidder__number[^"]*">\s*<a[^>]*>(\d+)</a>', html_content)
            if bid_count_match:
                try:
                    result['bid_count'] = int(bid_count_match.group(1))
                    # 入札数が0の場合は主取りと判定
                    if result['bid_count'] == 0:
                        result['is_unsold'] = True
                        return result
                except (ValueError, TypeError):
                    pass
            
            # 価格の正規表現パターン
            price_patterns = [
                r'([\d,]+)万円',  # 通常の価格表記
                r'￥([\d,]+)万円', # 通貨記号付き
                r'([\d,]+)万'      # 「万円」の省略形
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, html_content)
                if match:
                    price_str = match.group(1).replace(',', '')
                    try:
                        result['sold_price'] = float(price_str)
                        break
                    except (ValueError, TypeError):
                        continue
                        
            # 価格が取得できず、入札数も0の場合は主取りと判定
            if result['sold_price'] is None and result['bid_count'] == 0:
                result['is_unsold'] = True
                        
        except Exception as e:
            # エラーが発生した場合は主取りとみなす
            result['is_unsold'] = True
            import logging
            logging.error(f"価格情報の抽出中にエラーが発生しました: {e}")
            logging.error(f"エラー詳細: {str(e)}\n{traceback.format_exc()}")
            
        return result
