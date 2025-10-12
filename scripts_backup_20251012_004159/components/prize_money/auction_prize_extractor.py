"""
オークション時の賞金情報を抽出するクラス
"""
import logging
from typing import Dict, Any
from bs4 import BeautifulSoup
from .base_prize_extractor import BasePrizeExtractor

logger = logging.getLogger(__name__)

class AuctionPrizeExtractor(BasePrizeExtractor):
    """オークション時の賞金情報を抽出するクラス"""
    
    def extract(self, content: str, horse_name: str = '') -> Dict[str, Any]:
        """オークション時の賞金情報を抽出する
        
        Args:
            content: 抽出元のHTMLコンテンツ
            horse_name: 馬名（デバッグ用）
            
        Returns:
            抽出した賞金情報を含む辞書
        """
        result = {
            'auction_prize': None  # 万円単位
        }
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # オークション情報のセクションを探す
            auction_section = soup.find('div', class_='auction-info')
            if not auction_section:
                return result
                
            # オークション時の賞金を抽出
            auction_prize_elem = auction_section.find('span', class_='auction-prize')
            if auction_prize_elem:
                prize_text = auction_prize_elem.get_text(strip=True)
                prize_value = self._extract_prize_value(prize_text, horse_name)
                if prize_value is not None:
                    result['auction_prize'] = prize_value
                        
            return result
            
        except Exception as e:
            logger.error(f"馬名 '{horse_name}': オークション賞金情報の抽出中にエラーが発生しました: {e}")
            return result
