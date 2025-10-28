"""
落札価格を抽出するモジュール
"""
import logging
import re
from typing import Dict, Optional, Union
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class PriceExtractor:
    """落札価格の抽出を行うクラス"""
    
    @staticmethod
    def extract_price(html_content: str, horse_name: str = '') -> Dict[str, Union[int, bool, None]]:
        """HTMLから価格情報を抽出する
        
        Args:
            html_content: 抽出元のHTMLコンテンツ
            horse_name: 馬名（デバッグ用）
            
        Returns:
            抽出した価格情報を含む辞書
            {
                'sold_price': int or None,  # 落札価格（円、主取り時はNone）
                'is_unsold': bool          # 主取りフラグ（入札数0の場合にTrue）
            }
        """
        result = {
            'sold_price': None,
            'is_unsold': False
        }
        
        try:
            # 1. 入札数が0の場合は主取りと判定
            bid_count_match = re.search(r'入札数\s*:\s*(\d+)', html_content)
            if bid_count_match:
                bid_count = int(bid_count_match.group(1))
                if bid_count == 0:
                    result['sold_price'] = None  # 主取りの場合は価格をNoneに設定
                    result['is_unsold'] = True
                    logger.info(f"馬名 '{horse_name}': 入札数が0のため主取りと判定")
                    return result
            
            # 2. JavaScriptのデータから価格を抽出（最も信頼性が高い）
            bid_history_match = re.search(r'var\s+bid_history\s*=\s*(\[.*?\]);', html_content, re.DOTALL)
            if bid_history_match:
                import json
                try:
                    bid_history = json.loads(bid_history_match.group(1))
                    if bid_history and len(bid_history) > 0:
                        # 最終入札価格を取得
                        last_bid = bid_history[-1]
                        if 'price' in last_bid:
                            result['sold_price'] = int(last_bid['price'])
                            return result
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"馬名 '{horse_name}': 入札履歴の解析に失敗しました: {e}")
            
            # 3. 価格パターンマッチング
            price_patterns = [
                r'落札価格[：:](?:\s*)([\d,]+)(?:\s*)円',
                r'現在価格[：:](?:\s*)([\d,]+)(?:\s*)円',
                r'"current_price"\s*:\s*"?([\d,]+)"?'
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, html_content)
                if match:
                    try:
                        price_str = match.group(1).replace(',', '')
                        result['sold_price'] = int(price_str)
                        return result
                    except (ValueError, IndexError) as e:
                        continue
            
            # 4. HTML要素から価格を抽出（最終手段）
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 価格を含む可能性のある要素を検索
            price_elements = soup.find_all(['div', 'span', 'td', 'p'], class_=re.compile(r'(price|sold|bid|amount|value)', re.I))
            
            for elem in price_elements:
                price_text = elem.get_text(strip=True)
                # 数値のみの抽出を試みる
                match = re.search(r'([\d,]+)(?:\s*)円', price_text)
                if match:
                    try:
                        result['sold_price'] = int(match.group(1).replace(',', ''))
                        return result
                    except (ValueError, IndexError):
                        continue
            
            logger.warning(f"馬名 '{horse_name}': 価格要素が見つかりませんでした")
            return result
            
        except Exception as e:
            logger.error(f"馬名 '{horse_name}': 落札価格の抽出中にエラーが発生しました: {e}", exc_info=True)
            return result
