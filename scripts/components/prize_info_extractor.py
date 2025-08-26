"""賞金情報を抽出するモジュール"""
from typing import Dict, Optional, Tuple
import re
import logging
from bs4 import BeautifulSoup


class PrizeInfoExtractor:
    """賞金情報を抽出するクラス"""
    
    def __init__(self, logger: logging.Logger = None):
        """初期化メソッド
        
        Args:
            logger: ロガーインスタンス（Noneの場合は新規作成）
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def extract(self, horse_element) -> Tuple[Optional[Dict[str, int]], bool]:
        """馬の要素から賞金情報を抽出する
        
        Args:
            horse_element: 馬情報を含むBeautifulSoup要素
            
        Returns:
            Tuple[Optional[Dict[str, int]], bool]: 
                (賞金情報を含む辞書, 成功したかどうか)
        """
        try:
            # 賞金情報の要素を探す
            prize_elem = horse_element.find('div', class_='prize-money')
            if not prize_elem:
                self.logger.debug('賞金情報の要素が見つかりませんでした')
                return None, False
                
            prize_text = prize_elem.get_text(strip=True)
            if not prize_text:
                self.logger.debug('賞金情報のテキストが空です')
                return None, False
                
            # 賞金情報を抽出（例: "総賞金: 1,234万円"）
            prize_match = re.search(r'総賞金[：: ]*([\d,]+)万円', prize_text)
            if not prize_match:
                self.logger.debug('賞金情報のパターンが一致しませんでした')
                return None, False
                
            # カンマを削除して数値に変換
            try:
                prize_money = int(prize_match.group(1).replace(',', '')) * 10000  # 万円単位を円に変換
                prize_info = {
                    'prize_money': prize_money
                }
                
                self.logger.debug(f'賞金情報を抽出しました: {prize_info}')
                return prize_info, True
                
            except (ValueError, TypeError) as e:
                self.logger.error(f'賞金情報の数値変換に失敗しました: {e}')
                return None, False
                
        except Exception as e:
            self.logger.error(f'賞金情報の抽出中にエラーが発生しました: {e}', exc_info=True)
            return None, False
    
    def extract_from_jbis(self, jbis_url: str) -> Optional[int]:
        """JBISのページから賞金情報を抽出する
        
        Args:
            jbis_url: JBISのURL
            
        Returns:
            Optional[int]: 賞金（円）、抽出に失敗した場合はNone
        """
        if not jbis_url:
            self.logger.debug('URLが空です')
            return None
            
        try:
            # 動的にインポートしてモック化を可能にする
            import requests
            
            # リクエストを送信してHTMLを取得
            response = requests.get(jbis_url)
            response.raise_for_status()
            
            # BeautifulSoupでHTMLをパース
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 賞金情報を含む要素を検索
            prize_elem = soup.find('div', class_='dbdata_main_prize_money')
            if not prize_elem:
                self.logger.debug('賞金情報の要素が見つかりませんでした')
                return None
                
            # テキストから賞金を抽出
            prize_text = ' '.join(prize_elem.stripped_strings)
            
            # 正規表現で数値を抽出（例: "総賞金 1,234 万円"）
            match = re.search(r'([\d,]+)\s*万円', prize_text)
            if not match:
                self.logger.debug(f'賞金情報のパターンが一致しませんでした: {prize_text}')
                return None
                
            # カンマを削除して数値に変換
            try:
                prize_money = int(match.group(1).replace(',', '')) * 10000  # 万円単位を円に変換
                self.logger.debug(f'JBISから賞金情報を抽出しました: {prize_money}円')
                return prize_money
                
            except (ValueError, TypeError) as e:
                self.logger.error(f'賞金情報の数値変換に失敗しました: {e}')
                return None
            
        except requests.RequestException as e:
            self.logger.error(f'JBISへのリクエスト中にエラーが発生しました: {e}')
            return None
            
        except Exception as e:
            self.logger.error(f'JBISからの賞金情報取得中にエラーが発生しました: {e}', exc_info=True)
            return None
