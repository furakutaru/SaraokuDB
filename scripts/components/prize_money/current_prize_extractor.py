"""
現在の賞金情報を抽出するクラス
"""
import logging
from typing import Dict, Any
from bs4 import BeautifulSoup
from .base_prize_extractor import BasePrizeExtractor

logger = logging.getLogger(__name__)

class CurrentPrizeExtractor(BasePrizeExtractor):
    """現在の賞金情報を抽出するクラス"""
    
    def extract(self, content: str, horse_name: str = '') -> Dict[str, Any]:
        """現在の賞金情報を抽出する
        
        Args:
            content: 抽出元のHTMLコンテンツ
            horse_name: 馬名（デバッグ用）
            
        Returns:
            抽出した賞金情報を含む辞書
        """
        result = {
            'current_prize': None,  # 万円単位
            'is_breeding_mare': False
        }
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # 賞金情報のセクションを探す
            prize_section = soup.find('div', class_='prize-info')
            if not prize_section:
                return result
                
            # 繁殖牝馬の場合はスキップ
            if any(k in prize_section.get_text() for k in ['繁殖牝馬', '繫殖牝馬']):
                result['is_breeding_mare'] = True
                return result
                
            # 現在の賞金を抽出
            current_prize_elem = prize_section.find('span', class_='current-prize')
            if current_prize_elem:
                prize_text = current_prize_elem.get_text(strip=True)
                result['current_prize'] = self._extract_prize_value(prize_text, horse_name)
                
            return result
            
        except Exception as e:
            logger.error(f"馬名 '{horse_name}': 現在の賞金情報の抽出中にエラーが発生しました: {e}")
            return result
