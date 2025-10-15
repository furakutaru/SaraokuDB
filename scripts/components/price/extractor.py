"""
価格情報を抽出するモジュール
"""
import re
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
        """
        result = {
            'sold_price': None,
            'is_unsold': False
        }
        
        try:
            # 主取りチェック
            if '主取り' in html_content:
                result['is_unsold'] = True
                return result
                
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
                        
        except Exception as e:
            # エラーが発生した場合はデフォルト値を返す
            pass
            
        return result
