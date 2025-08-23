"""
通算成績を抽出するモジュール
"""
import re
import logging
from typing import Dict, Optional

# ロガーの設定
logger = logging.getLogger(__name__)

class RaceRecordExtractor:
    """通算成績を抽出するクラス"""
    
    def extract(self, element) -> Optional[Dict[str, str]]:
        """通算成績を抽出する
        
        Args:
            element: BeautifulSoup要素
            
        Returns:
            Dict[str, str]: 通算成績情報を含む辞書
        """
        try:
            # テーブル内のテキストを取得
            table_text = element.get_text(' ', strip=True)
            
            # 通算成績の抽出
            record_match = re.search(r'通算成績：([^\s]+)', table_text)
            if record_match:
                return {'record': record_match.group(1)}
                
        except Exception as e:
            logger.error(f"通算成績の抽出中にエラーが発生しました: {e}", exc_info=True)
            
        return None
