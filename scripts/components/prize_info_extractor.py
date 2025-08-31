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
                辞書のキー:
                - total_prize_start: オークション時点の総賞金（円）
                - total_prize_latest: 最新の総賞金（円、JBISから取得）
        """
        try:
            prize_info = {}
            
            # 1. オークション時点の賞金を抽出
            prize_elem = horse_element.find('div', class_='prize-money')
            if prize_elem:
                prize_text = prize_elem.get_text(strip=True)
                if prize_text:
                    # 賞金情報を抽出（例: "総賞金: 1,234万円"）
                    prize_match = re.search(r'総賞金[：: ]*([\d,]+)万円', prize_text)
                    if prize_match:
                        try:
                            prize_money = int(prize_match.group(1).replace(',', '')) * 10000  # 万円単位を円に変換
                            prize_info['total_prize_start'] = prize_money
                            self.logger.debug(f'オークション時点の賞金を抽出しました: {prize_money}円')
                        except (ValueError, TypeError) as e:
                            self.logger.error(f'賞金情報の数値変換に失敗しました: {e}')
            
            # 2. JBISから最新の賞金情報を取得
            jbis_url = None
            if hasattr(horse_element, 'find'):
                jbis_link = horse_element.find('a', href=lambda x: x and 'jbis.or.jp' in x)
                if jbis_link:
                    jbis_url = jbis_link.get('href')
            
            if jbis_url:
                latest_prize = self.extract_from_jbis(jbis_url)
                if latest_prize is not None:
                    prize_info['total_prize_latest'] = latest_prize
                    self.logger.debug(f'最新の賞金を取得しました: {latest_prize}円')
            
            # どちらか一方でも取得できていれば成功とする
            if prize_info:
                return prize_info, True
            
            self.logger.debug('賞金情報を取得できませんでした')
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
            
            # URLを正規化（血統情報ページの場合は基本情報ページにリダイレクト）
            if '/pedigree/' in jbis_url or '/record/' in jbis_url:
                base_url = jbis_url.split('/horse/')[0]
                horse_id = jbis_url.split('/horse/')[-1].split('/')[0]
                jbis_url = f"{base_url}/horse/{horse_id}/"
                self.logger.debug(f'URLを正規化: {jbis_url}')
            
            # リクエストを送信してHTMLを取得
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(jbis_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # BeautifulSoupでHTMLをパース
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. dtタグで「総賞金」を探す（より確実な方法）
            prize_elem = None
            dt_elem = soup.find('dt', string=re.compile(r'^\s*総賞金\s*$'))
            if dt_elem and dt_elem.find_next_sibling('dd'):
                prize_elem = dt_elem.find_next_sibling('dd')
                self.logger.debug('dt/ddタグから賞金情報を検出')
            
            # 2. 従来通りの方法で探す
            if not prize_elem:
                prize_elem = soup.find('div', class_='dbdata_main_prize_money')
                if prize_elem:
                    self.logger.debug('div.dbdata_main_prize_moneyから賞金情報を検出')
            
            if not prize_elem:
                self.logger.debug('賞金情報の要素が見つかりませんでした')
                return None
                
            # テキストから賞金を抽出
            prize_text = ' '.join(prize_elem.stripped_strings)
            self.logger.debug(f'賞金テキスト: {prize_text}')
            
            # 正規表現で数値を抽出（例: "総賞金 1,234 万円" または "1,234万円"）
            match = re.search(r'総賞金\s*([\d,]+(?:\.[\d]+)?)\s*万円', prize_text) or \
                    re.search(r'([\d,]+(?:\.[\d]+)?)\s*万円', prize_text)
            if not match:
                self.logger.debug('賞金情報のパターンが一致しませんでした')
                return None
                
            # カンマを削除して数値に変換（万円単位を円に変換）
            try:
                prize_money = float(match.group(1).replace(',', '')) * 10000
                return int(prize_money)  # 整数に変換して返す
            except (ValueError, TypeError) as e:
                self.logger.error(f'賞金情報の数値変換に失敗しました: {e}')
                return None
                
        except requests.RequestException as e:
            self.logger.error(f'JBISへのリクエスト中にエラーが発生しました: {e}')
            return None
        except Exception as e:
            self.logger.error(f'JBISからの賞金情報取得中に予期せぬエラーが発生しました: {e}')
            return None
