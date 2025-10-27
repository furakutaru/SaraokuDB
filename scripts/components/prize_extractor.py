"""
賞金情報を抽出するモジュール
"""
import re
import logging
from typing import Dict, Optional, Union
from bs4 import BeautifulSoup, Tag

# ロガーの設定
logger = logging.getLogger(__name__)

class PrizeExtractor:
    """賞金情報を抽出するクラス"""
    
    def extract(self, element) -> Dict[str, Union[int, str, Dict]]:
        """賞金情報を抽出する
        
        Args:
            element: BeautifulSoup要素
            
        Returns:
            Dict: 賞金情報を含む辞書
            {
                'total_prize': int,  # 総賞金（円）
                'original_text': str,  # 元のテキスト
                'pattern_used': str    # 使用されたパターン
            }
        """
        default_return = {
            'total_prize': 0,
            'original_text': '賞金なし',
            'pattern_used': 'デフォルト（0円）'
        }
        
        try:
            # トップページの賞金表示パターン
            if hasattr(element, 'find_all'):
                # トップページの賞金表示を探す
                prize_divs = element.find_all('div', class_='auctionTableRow__price')
                for div in prize_divs:
                    label = div.find('div', class_='label')
                    value = div.find('div', class_='value')
                    
                    if label and value and '総賞金' in label.get_text():
                        prize_text = value.get_text(strip=True)
                        # 「万円」を除去して数値に変換
                        try:
                            prize_value = float(prize_text.replace('万円', '').replace(',', '').strip())
                            return {
                                'total_prize': int(prize_value * 10000),  # 万円から円に変換
                                'original_text': prize_text,
                                'pattern_used': 'トップページ総賞金'
                            }
                        except (ValueError, AttributeError):
                            logger.warning(f"賞金の数値変換に失敗しました: {prize_text}")
                            continue
            
            # テキストベースの抽出（旧方式）
            text = element.get_text(' ', strip=True) if hasattr(element, 'get_text') else str(element)
            
            # 賞金パターン
            prize_patterns = [
                (r'総賞金[：: ]*([\d,.]+)(?:\s*万円)?', '総賞金パターン'),
                (r'獲得賞金[：: ]*([\d,.]+)(?:\s*万円)?', '獲得賞金パターン'),
                (r'([\d,.]+)\s*万円', '単純な万円パターン')
            ]
            
            for pattern, pattern_name in prize_patterns:
                match = re.search(pattern, text)
                if match:
                    try:
                        prize_str = match.group(1).replace(',', '').strip()
                        prize_value = float(prize_str)
                        return {
                            'total_prize': int(prize_value * 10000),  # 万円から円に変換
                            'original_text': match.group(0).strip(),
                            'pattern_used': pattern_name
                        }
                    except (ValueError, IndexError) as e:
                        logger.debug(f"賞金の数値変換に失敗しました: {e}")
                        continue
            
            return default_return
                
        except Exception as e:
            logger.error(f"賞金情報の抽出中にエラーが発生しました: {e}", exc_info=True)
            return default_return
