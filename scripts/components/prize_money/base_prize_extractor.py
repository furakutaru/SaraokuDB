"""
賞金情報抽出の基底クラス
"""
from abc import ABC, abstractmethod
import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class BasePrizeExtractor(ABC):
    """賞金情報抽出の基底クラス"""
    
    PRIZE_PATTERN = r'([\d,]+(?:\.\d+)?)'
    
    @abstractmethod
    def extract(self, content: str, horse_name: str = '') -> Dict[str, any]:
        """賞金情報を抽出する
        
        Args:
            content: 抽出元のHTMLコンテンツ
            horse_name: 馬名（デバッグ用）
            
        Returns:
            抽出した賞金情報を含む辞書
        """
        pass
    
    def _extract_prize_value(self, text: str, horse_name: str = '') -> Optional[float]:
        """賞金の数値を抽出する
        
        Args:
            text: 抽出元のテキスト
            horse_name: 馬名（ログ出力用）
            
        Returns:
            抽出した賞金額（万円単位）、抽出できない場合はNone
        """
        if not text:
            return None
            
        try:
            # 数値部分を抽出（「1,234.0万円」→ 1,234.0）
            match = re.search(self.PRIZE_PATTERN, text.replace(',', ''))
            if match:
                return float(match.group(1))
            
            logger.warning(f"馬名 '{horse_name}': 賞金の数値が見つかりませんでした: {text}")
            return None
            
        except (ValueError, TypeError) as e:
            logger.error(f"馬名 '{horse_name}': 賞金の抽出中にエラーが発生しました: {e}")
            return None
