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
                - total_prize: 総賞金（円）
        """
        try:
            prize_info = {}
            
            # 1. オークション時点の賞金を抽出
            # まずはカード内の賞金情報を探す
            prize_elem = None
            
            # クラス名のバリエーションに対応
            for class_name in ['auctionTableCard__price', 'price', 'prize-money']:
                prize_elem = horse_element.find('div', class_=class_name)
                if prize_elem:
                    break
            
            if prize_elem:
                prize_text = prize_elem.get_text(strip=True)
                self.logger.debug(f'賞金テキストを発見: {prize_text}')
                
                # 賞金情報を抽出（例: "総賞金 4,433.5万円" または "1,234万円"）
                prize_match = re.search(r'(?:総賞金[：: ]*)?([\d,.]+)万?円', prize_text)
                if prize_match:
                    try:
                        # カンマを削除し、浮動小数点数に変換
                        prize_amount = float(prize_match.group(1).replace(',', ''))
                        # 万円単位を円に変換（小数点以下も考慮）
                        prize_money = int(prize_amount * 10000)
                        # 総賞金を設定（JBIS連携はコメントアウト）
                        result = {
                            'total_prize': prize_money,
                            # JBIS連携が可能になったらコメントを外す
                            # 'total_prize_latest': self._get_jbis_prize(horse_element) or prize_money
                        }
                        self.logger.debug(f'賞金を抽出しました: {prize_money}円 (元のテキスト: {prize_match.group(0)})')
                        return result, True
                    except (ValueError, TypeError) as e:
                        self.logger.error(f'賞金情報の数値変換に失敗しました: {e}')
            
            # 2. 詳細ページから賞金情報を取得
            detail_url = None
            if hasattr(horse_element, 'find'):
                link = horse_element.find('a', href=lambda x: x and '/item/' in x)
                if link:
                    detail_url = link.get('href')
                    if not detail_url.startswith('http'):
                        detail_url = f'https://auction.keiba.rakuten.co.jp{detail_url}'
            
            if detail_url:
                try:
                    # 詳細ページのHTMLを取得
                    import requests
                    from bs4 import BeautifulSoup
                    
                    response = requests.get(detail_url, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        # 詳細ページ内の賞金情報を探す
                        for elem in soup.find_all(['div', 'span'], class_=True):
                            if '賞金' in elem.get_text():
                                prize_match = re.search(r'(?:総賞金[：: ]*)?([\d,]+)万円', elem.get_text())
                                if prize_match:
                                    prize_money = int(prize_match.group(1).replace(',', '')) * 10000
                                    prize_info['total_prize'] = prize_money
                                    self.logger.debug(f'詳細ページから賞金を抽出しました: {prize_money}円')
                                    return prize_info, True
                except Exception as e:
                    self.logger.debug(f'詳細ページからの賞金取得に失敗しました: {e}')
            
            self.logger.debug('賞金情報を取得できませんでした')
            return None, False
                
        except Exception as e:
            self.logger.error(f'賞金情報の抽出中にエラーが発生しました: {e}', exc_info=True)
            return {}, False
            
    # JBISから最新の賞金情報を取得するメソッド（将来的に使用）
    def _get_jbis_prize(self, horse_element):
        """
        JBISから最新の賞金情報を取得する（将来的に実装）
        
        Args:
            horse_element: 馬情報を含むHTML要素
            
        Returns:
            Optional[int]: 最新の賞金（円）、取得できない場合はNone
        """
        # 将来的に実装
        # 例:
        # jbis_url = self._extract_jbis_url(horse_element)
        # if jbis_url:
        #     return self._scrape_jbis_prize(jbis_url)
        return None
    
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
