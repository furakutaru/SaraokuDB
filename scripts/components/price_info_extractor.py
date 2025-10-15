"""価格情報を抽出するモジュール"""
from typing import Dict, Optional, Tuple, Any
import re
import logging
from bs4 import BeautifulSoup


class PriceInfoExtractor:
    """価格情報を抽出するクラス"""
    
    def __init__(self, logger: logging.Logger = None):
        """初期化メソッド
        
        Args:
            logger: ロガーインスタンス（Noneの場合は新規作成）
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def extract(self, html_content) -> Tuple[Optional[Dict[str, Any]], bool]:
        """HTMLから価格情報を抽出する
        
        Args:
            html_content: 抽出元のHTMLコンテンツ（文字列またはBeautifulSoupオブジェクト）
            
        Returns:
            Tuple[Optional[Dict[str, Any]], bool]: 
                (価格情報を含む辞書, 成功したかどうか)
        """
        try:
            # HTML文字列の場合はBeautifulSoupオブジェクトに変換
            if isinstance(html_content, str):
                soup = BeautifulSoup(html_content, 'html.parser')
            else:
                soup = html_content
                
            price_info = {}
            
            # 1. 入札数をチェック
            bid_count_elem = soup.select_one('.topBidder__number--highLighted')
            if bid_count_elem:
                try:
                    bid_count = int(bid_count_elem.get_text(strip=True))
                    if bid_count == 0:
                        price_info['is_unsold'] = True
                        price_info['sold_price'] = None
                        self.logger.debug(f'入札数が0のため主取りと判定: 入札数={bid_count}')
                        return price_info, True
                except (ValueError, TypeError) as e:
                    self.logger.warning(f'入札数の取得に失敗しました: {e}')
            
            # 2. 落札価格の抽出（ユーザー提供のHTML構造に合わせて更新）
            self.logger.debug('価格情報の抽出を開始します...')
            
            # デバッグ用にHTMLの一部をログに出力
            html_sample = str(soup)[:1000]  # 最初の1000文字をログに出力
            self.logger.debug(f'HTMLの先頭1000文字: {html_sample}')
            
            # 価格要素を検索
            price_elems = soup.find_all('span', {'itemprop': 'price'})
            self.logger.debug(f'見つかった価格要素の数: {len(price_elems)}')
            
            # すべての価格要素をログに出力
            for i, elem in enumerate(price_elems, 1):
                self.logger.debug(f'価格要素 {i}: {elem}')
            
            # 最初の価格要素を取得
            price_elem = soup.select_one('span[itemprop="price"]')
            
            if price_elem:
                try:
                    price_text = price_elem.get_text(strip=True)
                    self.logger.debug(f'抽出した価格テキスト: "{price_text}"')
                    
                    # 数字とカンマ以外を削除
                    price_text = re.sub(r'[^\d,]', '', price_text)
                    self.logger.debug(f'クリーニング後の価格テキスト: "{price_text}"')
                    
                    if price_text:
                        price = int(price_text.replace(',', ''))
                        if price > 0:  # 有効な価格の場合のみ採用
                            price_info['sold_price'] = price
                            price_info['is_unsold'] = False
                            self.logger.debug(f'落札価格を抽出しました: {price}円')
                            return price_info, True
                        else:
                            self.logger.debug(f'無効な価格: {price} (0以下です)')
                    else:
                        self.logger.debug('価格テキストが空です')
                except (ValueError, TypeError, AttributeError) as e:
                    self.logger.error(f'価格の抽出中にエラーが発生しました: {e}', exc_info=True)
            
            # 3. オークション終了チェック
            auction_ended = soup.select_one('div.priceBox.auctionBid p')
            if auction_ended and '終了しました' in auction_ended.get_text():
                self.logger.debug('オークションは終了しています')
                # 終了しているが価格が取得できなかった場合は、主取りとみなす
                price_info['is_unsold'] = True
                price_info['sold_price'] = None
                return price_info, True
            
            # 3. 価格情報が取得できなかった場合
            self.logger.warning('価格情報が見つかりませんでした')
            return None, False
            
        except Exception as e:
            self.logger.error(f'価格情報の抽出中に予期せぬエラーが発生しました: {e}', exc_info=True)
            return None, False
    
    def _is_unsold(self, price_text: str) -> bool:
        """価格テキストから未落札かどうかを判定する
        
        Args:
            price_text: 価格テキスト
            
        Returns:
            bool: 未落札の場合はTrue、それ以外はFalse
        """
        if not price_text:
            return False
            
        # 未落札を示す可能性のあるキーワード
        unsold_keywords = [
            '未落札', '売れ残り', '不成立', 'キャンセル',
            'unsold', 'not sold', 'cancelled', 'no bid'
        ]
        
        # 大文字小文字を区別せずにチェック
        price_text_lower = price_text.lower()
        return any(keyword.lower() in price_text_lower for keyword in unsold_keywords)
