"""
賞金情報を抽出するモジュール
"""
import re
import logging
from typing import Dict, Optional

# ロガーの設定
logger = logging.getLogger(__name__)

class PrizeExtractor:
    """賞金情報を抽出するクラス"""
    
    def extract(self, element) -> Optional[Dict[str, float]]:
        """賞金情報を抽出する
        
        Args:
            element: BeautifulSoup要素
            
        Returns:
            Dict[str, float]: 賞金情報を含む辞書
        """
        try:
            # テーブル内のテキストを取得
            table_text = element.get_text(' ', strip=True)
            
            # 獲得賞金の抽出
            prize_match = re.search(r'中央獲得賞金：([\d,.]+)万円', table_text)
            if prize_match:
                prize_money = float(prize_match.group(1).replace(',', ''))
                return {'prize_money': prize_money}
                
        except Exception as e:
            logger.error(f"賞金情報の抽出中にエラーが発生しました: {e}", exc_info=True)
            
        return None
