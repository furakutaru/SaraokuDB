"""
オークション情報を抽出するモジュール
"""
import re
import logging
from typing import Dict, Optional, Union, List
from bs4 import BeautifulSoup, Tag

class AuctionInfoExtractor:
    """オークション情報を抽出するクラス"""
    
    # 日付を抽出する正規表現パターン
    DATE_PATTERN = r'(\d{4})[年/](\d{1,2})[月/](\d{1,2})日'
    
    def __init__(self, logger: logging.Logger = None):
        """
        初期化メソッド
        
        Args:
            logger: ロガーインスタンス（Noneの場合は新規作成）
        """
        self.logger = logger or logging.getLogger(__name__)
        self.detail_url = None  # オークション詳細ページのURLを保持
    
    def extract_date(self, soup: Union[BeautifulSoup, str]) -> Dict[str, Optional[str]]:
        """
        HTMLからオークション日を抽出する
        
        Args:
            soup: BeautifulSoupオブジェクトまたはHTML文字列
            
        Returns:
            Dict[str, Optional[str]]: 抽出したオークション日（キー: 'auction_date'）
        """
        result = {'auction_date': None}
        
        try:
            # 文字列が渡された場合はBeautifulSoupオブジェクトに変換して保持
            if isinstance(soup, str):
                soup = BeautifulSoup(soup, 'html.parser')
            
            # 後でget_infoで使えるようにsoupを保持
            self.soup = soup
            
            # 開始時間を含む要素を検索
            time_element = soup.select_one('.subData__startTime .subData__value')
            
            if time_element:
                date_text = time_element.get_text(strip=True)
                # 日付部分のみを抽出（「2025年08月24日 12:00」→「2025-08-24」）
                match = re.search(self.DATE_PATTERN, date_text)
                if match:
                    year, month, day = match.groups()
                    # YYYY-MM-DD形式に整形
                    result['auction_date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    self.logger.debug(f'オークション日を抽出しました: {result["auction_date"]}')
            else:
                self.logger.debug('オークション日が見つかりませんでした')
                
        except Exception as e:
            self.logger.error(f'オークション日の抽出中にエラーが発生しました: {e}', exc_info=True)
            
        return result
    
    def set_detail_url(self, url: str) -> None:
        """
        オークション詳細ページのURLを設定する
        
        Args:
            url: オークション詳細ページのURL
        """
        self.detail_url = url
        self.logger.debug(f'オークション詳細ページのURLを設定しました: {url}')
    
    def get_info(self) -> Dict[str, Optional[str]]:
        """
        抽出したオークション情報を取得する
        
        Returns:
            Dict[str, Optional[str]]: オークション情報（日付とURL）
        """
        return {
            'auction_date': self.extract_date(self.soup)['auction_date'] if hasattr(self, 'soup') else None,
            'auction_url': self.detail_url
        }
