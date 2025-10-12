"""賞金情報を抽出するモジュール"""
from typing import Dict, Optional, Tuple, Any, Union
import re
import logging
import sys
import requests
from bs4 import BeautifulSoup, Tag, NavigableString


class PrizeInfoExtractor:
    """賞金情報を抽出するクラス"""
    
    def __init__(self, logger: logging.Logger = None):
        """初期化メソッド
        
        Args:
            logger: ロガーインスタンス（Noneの場合は新規作成）
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def extract(self, horse_element: Union[BeautifulSoup, Tag, Any]) -> Tuple[Optional[Dict[str, Any]], bool]:
        """馬の要素から賞金情報を抽出する
        
        Args:
            horse_element: 馬情報を含むBeautifulSoup要素
            
        Returns:
            Tuple[Optional[Dict[str, int]], bool]: 
                (賞金情報を含む辞書, 成功したかどうか)
                辞書のキー:
                - total_prize: 総賞金（円）
        """
        import re  # メソッド内でreモジュールを使用するためインポート
        # デバッグ情報の出力
        self.logger.debug('=' * 50)
        self.logger.debug('賞金情報抽出を開始します')
        self.logger.debug(f'horse_element の型: {type(horse_element)}')
        
        # デバッグ用に要素の内容をログに出力（先頭500文字）
        element_str = str(horse_element)
        if len(element_str) > 500:
            element_str = element_str[:500] + '...'
        self.logger.debug(f'要素の内容（先頭）: {element_str}')
        
        try:
            prize_info = {}
            
            # 1. オークション時点の賞金を抽出
            # まずはカード内の賞金情報を探す
            prize_elem = None
            
            # horse_element が BeautifulSoup オブジェクトか確認
            if not hasattr(horse_element, 'find'):
                self.logger.warning('horse_element は find メソッドを持っていません')
                self.logger.debug(f'horse_element の内容（先頭500文字）: {str(horse_element)[:500]}')
                return None, False
                
            self.logger.debug('クラス名パターンで賞金要素を検索中...')
            # クラス名のバリエーションに対応
            class_patterns = [
                'auctionTableCard__price',  # 新しいバージョン
                'price',                    # 一般的なクラス名
                'prize-money',              # 別の一般的なクラス名
                'price-info',               # 追加のパターン
                'item-price',               # 追加のパターン
                'amount'                    # 追加のパターン
            ]
            
            for class_name in class_patterns:
                try:
                    # div, span, p, td, th など複数のタグをチェック
                    for tag in ['div', 'span', 'p', 'td', 'th']:
                        prize_elem = horse_element.find(tag, class_=class_name)
                        if prize_elem:
                            self.logger.debug(f'タグ <{tag} class="{class_name}"> で要素を発見')
                            break
                    if prize_elem:
                        break
                except Exception as e:
                    self.logger.warning(f'クラス {class_name} での検索中にエラー: {str(e)}', exc_info=True)
                    continue
            
            if prize_elem:
                try:
                    # テキストを取得（改行や余分な空白を削除）
                    prize_text = ' '.join(prize_elem.stripped_strings)
                    self.logger.debug(f'賞金テキストを発見: {prize_text}')
                    
                    # 賞金情報を抽出する正規表現パターン（複数パターン対応）
                    prize_patterns = [
                        # 日本語フォーマット（「987万6,543円」形式）
                        r'(?:総?賞金[：: ]*)?([\d,]+)万([\d,]+)円',
                        # 日本語表記（「1,234.5万円」形式）
                        r'(?:総?賞金[：: ]*)?([\d,.]+)万(?:円|\s*円)',
                        # 通常の数値表記（「5,678,900円」形式）
                        r'(?:総?賞金[：: ]*)?([\d,]+)(?:\s*円|円)',
                        # テキスト内の賞金表記
                        r'賞金[：: ]*([\d,.]+)(?:\s*万円?|円)',
                        # 数値 + 単位（「1,234万円」形式）
                        r'([\d,]+)(?:\s*万円?|円)'
                    ]
                    
                    for pattern in prize_patterns:
                        prize_match = re.search(pattern, prize_text)
                        if prize_match:
                            try:
                                # 日本語フォーマット（「987万6,543円」形式）の処理
                                if len(prize_match.groups()) >= 2 and prize_match.group(2):
                                    man_part = prize_match.group(1).replace(',', '')
                                    yen_part = prize_match.group(2).replace(',', '')
                                    prize_amount = int(man_part) * 10000 + int(yen_part)
                                else:
                                    # 通常の数値部分を抽出して正規化
                                    prize_value = prize_match.group(1).replace(',', '')
                                    
                                    # パターンに応じて処理を分岐
                                    if '万' in prize_match.group(0):
                                        # 小数点以下の処理（例：1,234.5万円 → 12,345,000円）
                                        if '.' in prize_value:
                                            prize_amount = int(float(prize_value) * 10000)
                                        else:
                                            prize_amount = int(prize_value) * 10000
                                    else:
                                        prize_amount = int(prize_value)
                                
                                # 明らかに小さい値（1万円未満）は無視
                                if prize_amount < 10000:
                                    self.logger.warning(f'賞金が1万円未満のため無視します: {prize_amount}円')
                                    continue
                                
                                result = {
                                    'total_prize': int(prize_amount),  # 整数値で返す
                                    'original_text': prize_match.group(0),  # デバッグ用に元のテキストも保持
                                    'pattern_used': pattern  # 使用したパターンを記録
                                }
                                
                                self.logger.info(f'賞金を抽出しました: {prize_amount:,}円 (パターン: {pattern})')
                                return result, True
                                
                            except (ValueError, TypeError) as e:
                                self.logger.warning(f'賞金情報の数値変換に失敗しました（パターン: {pattern}）: {e}')
                                continue
                    
                    self.logger.warning(f'どの賞金パターンにも一致しませんでした: {prize_text}')
                    
                except Exception as e:
                    self.logger.error(f'賞金テキストの処理中にエラーが発生しました: {e}', exc_info=True)
            
            # 2. テキスト全体から賞金情報を検索（クラス名での検索に失敗した場合）
            if not prize_elem and hasattr(horse_element, 'get_text'):
                self.logger.debug('クラス名での検索に失敗したため、テキスト全体から検索を試みます...')
                full_text = horse_element.get_text(separator=' ', strip=True)
                
                # テキスト内から賞金情報を検索
                text_patterns = [
                    # 日本語フォーマット（「987万6,543円」形式）
                    r'(?:総?賞金[：: ]*)?([\d,]+)万([\d,]+)円',
                    # 日本語表記（「1,234.5万円」形式）
                    r'(?:総?賞金[：: ]*)?([\d,.]+)万(?:円|\s*円)',
                    # 通常の数値表記（「5,678,900円」形式）
                    r'(?:総?賞金[：: ]*)?([\d,]+)(?:\s*円|円)',
                    # テキスト内の賞金表記
                    r'賞金[：: ]*([\d,.]+)(?:\s*万円?|円)',
                    # 数値 + 単位（「1,234万円」形式）
                    r'([\d,]+)(?:\s*万円?|円)'
                ]
                
                for pattern in text_patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        try:
                            # 日本語フォーマット（「987万6,543円」形式）の処理
                            if len(match.groups()) >= 2 and match.group(2):
                                man_part = match.group(1).replace(',', '')
                                yen_part = match.group(2).replace(',', '')
                                prize_amount = int(man_part) * 10000 + int(yen_part)
                            else:
                                # 通常の数値部分を抽出して正規化
                                prize_value = match.group(1).replace(',', '')
                                
                                # パターンに応じて処理を分岐
                                if '万' in match.group(0):
                                    if '.' in prize_value:
                                        prize_amount = int(float(prize_value) * 10000)
                                    else:
                                        prize_amount = int(prize_value) * 10000
                                else:
                                    prize_amount = int(prize_value)
                            
                            result = {
                                'total_prize': prize_amount,
                                'original_text': match.group(0),
                                'pattern_used': f'text_pattern: {pattern}'
                            }
                            
                            self.logger.info(f'テキスト内から賞金を抽出しました: {prize_amount:,}円 (パターン: {pattern})')
                            return result, True
                            
                        except (ValueError, TypeError) as e:
                            self.logger.warning(f'テキストからの賞金抽出中にエラーが発生しました: {e}')
                            continue
            
            # 3. 詳細ページから賞金情報を取得
            self.logger.debug('詳細ページから賞金情報を取得します...')
            detail_url = None
            try:
                if hasattr(horse_element, 'find'):
                    link = horse_element.find('a', href=lambda x: x and '/item/' in x)
                    if link and hasattr(link, 'get'):
                        detail_url = link.get('href')
                        if detail_url and not detail_url.startswith('http'):
                            detail_url = f'https://auction.keiba.rakuten.co.jp{detail_url}'
                        self.logger.debug(f'詳細ページURLを検出: {detail_url}')
            except Exception as e:
                self.logger.warning(f'詳細ページURLの取得中にエラーが発生しました: {e}')
            
            if detail_url:
                try:
                    self.logger.debug(f'詳細ページにアクセス中: {detail_url}')
                    # 詳細ページのHTMLを取得
                    import requests
                    from bs4 import BeautifulSoup
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    
                    response = requests.get(detail_url, headers=headers, timeout=15)
                    response.raise_for_status()
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        self.logger.debug('詳細ページのHTMLを正常に取得しました')
                        
                        # 詳細ページ内の賞金情報を探す
                        prize_elements = soup.find_all(['div', 'span', 'td', 'th'], class_=True)
                        self.logger.debug(f'検索対象要素数: {len(prize_elements)}')
                        
                        for elem in prize_elements:
                            try:
                                text = elem.get_text(strip=True)
                                if '賞金' in text:
                                    self.logger.debug(f'賞金関連の要素を発見: {text[:100]}...')
                                    # より寛容な正規表現パターン
                                    patterns = [
                                        r'(?:総賞金[：: ]*)?([\d,.]+)万円?',
                                        r'賞金[：: ]*([\d,.]+)万円?',
                                        r'([\d,.]+)万円?.*賞金'
                                    ]
                                    
                                    for pattern in patterns:
                                        prize_match = re.search(pattern, text)
                                        if prize_match:
                                            try:
                                                prize_money = int(float(prize_match.group(1).replace(',', '')) * 10000)
                                                prize_info['total_prize'] = prize_money
                                                self.logger.info(f'詳細ページから賞金を抽出しました: {prize_money}円 (パターン: {pattern})')
                                                return prize_info, True
                                            except (ValueError, TypeError) as ve:
                                                self.logger.warning(f'賞金の数値変換に失敗しました: {ve}', exc_info=True)
                                                continue
                            except Exception as elem_error:
                                self.logger.debug(f'要素処理中のエラー: {elem_error}')
                                continue
                                
                        self.logger.warning('詳細ページ内で賞金情報を見つけられませんでした')
                        
                except requests.RequestException as re:
                    self.logger.error(f'詳細ページへのリクエスト中にエラーが発生しました: {re}')
                except Exception as e:
                    self.logger.error(f'詳細ページの処理中に予期せぬエラーが発生しました: {e}', exc_info=True)
            
            self.logger.debug('賞金情報を取得できませんでした')
            return None, False
                
        except Exception as e:
            self.logger.error(f'賞金情報の抽出中にエラーが発生しました: {e}', exc_info=True)
            return None, False
            
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
