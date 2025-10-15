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

            # 1) 楽天の実DOMに合わせた抽出: label/value ペアから「総賞金」を取得
            # 例: <div class="auctionTableRow__price"><div class="label">総賞金</div><div class="value">3980.2万円</div></div>
            try:
                price_rows = soup.select('div.auctionTableRow__price')
                for row in price_rows:
                    label = row.find(class_='label')
                    value = row.find(class_='value')
                    if not label or not value:
                        continue
                    if '総賞金' in label.get_text(strip=True):
                        prize_text = value.get_text(strip=True)
                        prize_value = self._extract_prize_value(prize_text, horse_name)
                        if prize_value is not None:
                            result['auction_prize'] = prize_value  # 万円単位
                            return result
            except Exception as e:
                logger.debug(f"label/value 方式での抽出中にエラー: {e}")

            # 2) 既存のフォールバック: 独自セクション/クラス名にも対応
            auction_section = soup.find('div', class_='auction-info')
            if auction_section:
                auction_prize_elem = auction_section.find('span', class_='auction-prize')
                if auction_prize_elem:
                    prize_text = auction_prize_elem.get_text(strip=True)
                    prize_value = self._extract_prize_value(prize_text, horse_name)
                    if prize_value is not None:
                        result['auction_prize'] = prize_value  # 万円単位
                        return result

            # 3) テキスト走査のフォールバック: 「総賞金」近傍の値を正規表現で抽出
            full_text = soup.get_text(" ", strip=True)
            # パターン例: 総賞金 3980.2万円 / 総賞金：3980.2 万円
            import re
            m = re.search(r'総賞金[：:\s]*([\d,]+(?:\.\d+)?)\s*万円', full_text)
            if m:
                try:
                    prize_value = float(m.group(1).replace(',', ''))
                    result['auction_prize'] = prize_value  # 万円単位
                    return result
                except ValueError:
                    pass

            return result
            
        except Exception as e:
            logger.error(f"馬名 '{horse_name}': オークション賞金情報の抽出中にエラーが発生しました: {e}")
            return result
