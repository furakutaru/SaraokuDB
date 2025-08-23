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
    def extract_price(html_content: str, horse_name: str = '') -> Dict[str, Union[float, bool, None]]:
        """HTMLから落札価格と主取りフラグを抽出する
        
        Args:
            html_content: 抽出元のHTMLコンテンツ
            horse_name: 馬名（デバッグ用）
            
        Returns:
            抽出した価格情報を含む辞書
            {
                'sold_price': float or None,  # 落札価格（万円）
                'is_unsold': bool            # 主取りフラグ
            }
        """
        result = {
            'sold_price': None,
            'is_unsold': False
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 主取りチェック
            unsold_elem = soup.find('div', class_='unsold')
            if unsold_elem and '主取り' in unsold_elem.get_text():
                result['is_unsold'] = True
                return result
            
            # 落札価格の抽出
            price_elem = soup.find('div', class_='sold-price')
            if not price_elem:
                return result
                
            price_text = price_elem.get_text(strip=True)
            
            # 価格の数値部分を抽出（「1,234万円」→ 1234.0）
            price_match = re.search(r'[\d,]+', price_text.replace('\u3000', '').replace(' ', ''))
            if price_match:
                price_str = price_match.group().replace(',', '')
                try:
                    result['sold_price'] = float(price_str) / 10000  # 万円に変換
                except (ValueError, TypeError) as e:
                    logger.warning(f"馬名 '{horse_name}': 価格の数値変換に失敗しました: {price_text}")
            
            return result
            
        except Exception as e:
            logger.error(f"馬名 '{horse_name}': 落札価格の抽出中にエラーが発生しました: {e}")
            return result
