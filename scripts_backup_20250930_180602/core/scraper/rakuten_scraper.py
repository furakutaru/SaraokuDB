"""
楽天競馬オークションのスクレイピングを行うモジュール
"""
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper
from ..models.horse import Horse, Sex
from ..models.auction import Auction
from ..utils.html_parser import HTMLParser
from ..utils.data_validator import Validator, ValidationError

class RakutenScraper(BaseScraper):
    """楽天競馬オークションのスクレイピングクラス"""
    
    BASE_URL = "https://www.rakuten.co.jp/"
    
    def __init__(self, headers: Optional[Dict[str, str]] = None, max_retries: int = 3):
        """
        初期化
        
        Args:
            headers: HTTPヘッダー
            max_retries: 最大リトライ回数
        """
        super().__init__(self.BASE_URL, headers, max_retries)
        self.parser = HTMLParser()
        self.validator = Validator()
    
    def fetch_horse_list(self, url: str) -> List[Dict[str, str]]:
        """
        馬の一覧を取得する
        
        Args:
            url: 馬一覧ページのURL
            
        Returns:
            List[Dict[str, str]]: 馬の基本情報のリスト
        """
        try:
            response = self.request_get(url)
            soup = self.parser.parse_html(response.text)
            
            # 馬の行を取得（実際のHTML構造に合わせてセレクタを調整してください）
            rows = self.parser.find_elements(soup, 'tr.horse-row, tr.horse-item, tr[data-horse-id]')
            
            horses = []
            for row in rows:
                try:
                    horse = self._extract_horse_basic_info(row)
                    if horse:
                        horses.append(horse)
                except Exception as e:
                    self.logger.warning(f"馬情報の抽出中にエラーが発生しました: {str(e)}")
            
            return horses
            
        except Exception as e:
            self.logger.error(f"馬一覧の取得中にエラーが発生しました: {str(e)}")
            raise
    
    def fetch_horse_detail(self, url: str) -> Dict[str, Any]:
        """
        馬の詳細情報を取得する
        
        Args:
            url: 馬詳細ページのURL
            
        Returns:
            Dict[str, Any]: 馬の詳細情報
        """
        try:
            response = self.request_get(url)
            soup = self.parser.parse_html(response.text)
            
            # 馬の基本情報を抽出
            horse_info = self._extract_horse_info(soup)
            
            # オークション情報を抽出
            auction_info = self._extract_auction_info(soup)
            
            return {
                "horse": horse_info,
                "auction": auction_info
            }
            
        except Exception as e:
            self.logger.error(f"馬詳細情報の取得中にエラーが発生しました: {str(e)}")
            raise
    
    def _extract_horse_basic_info(self, row) -> Optional[Dict[str, str]]:
        """
        馬の基本情報を抽出する
        
        Args:
            row: 馬の行のBeautifulSoup要素
            
        Returns:
            Optional[Dict[str, str]]: 馬の基本情報、抽出できない場合はNone
        """
        try:
            # 馬名を取得（実際のHTML構造に合わせて調整してください）
            name_elem = self.parser.find_element(row, '.horse-name a')
            if not name_elem:
                return None
                
            name = self.parser.get_text(name_elem)
            detail_url = self.parser.get_attribute(name_elem, 'href')
            
            # 性別と年齢を取得（例: "牡3" → ("牡", 3)）
            sex_age_elem = self.parser.find_element(row, '.sex-age')
            sex, age = self._parse_sex_and_age(self.parser.get_text(sex_age_elem))
            
            # 父・母・母父を取得（実際のHTML構造に合わせて調整してください）
            sire = self.parser.get_text(self.parser.find_element(row, '.sire'))
            dam = self.parser.get_text(self.parser.find_element(row, '.dam'))
            damsire = self.parser.get_text(self.parser.find_element(row, '.damsire'))
            
            return {
                'name': name,
                'sex': sex,
                'age': age,
                'sire': sire,
                'dam': dam,
                'damsire': damsire,
                'detail_url': urljoin(self.BASE_URL, detail_url) if detail_url else ''
            }
            
        except Exception as e:
            self.logger.warning(f"馬の基本情報の抽出中にエラーが発生しました: {str(e)}")
            return None
    
    def _extract_horse_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        馬の詳細情報を抽出する
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            Dict[str, Any]: 馬の詳細情報
        """
        try:
            # 馬名
            name_elem = self.parser.find_element(soup, '.horse-name')
            name = self.parser.get_text(name_elem)
            
            # 性別と年齢
            sex_age_elem = self.parser.find_element(soup, '.sex-age')
            sex, age = self._parse_sex_and_age(self.parser.get_text(sex_age_elem))
            
            # 血統情報
            sire = self.parser.get_text(self.parser.find_element(soup, '.sire .name'))
            dam = self.parser.get_text(self.parser.find_element(soup, '.dam .name'))
            damsire = self.parser.get_text(self.parser.find_element(soup, '.damsire .name'))
            
            # 賞金情報（あれば）
            prize_elem = self.parser.find_element(soup, '.prize-money')
            total_prize = self._parse_prize(self.parser.get_text(prize_elem)) if prize_elem else None
            
            # コメント（あれば）
            comment_elem = self.parser.find_element(soup, '.horse-comment')
            comment = self.parser.get_text(comment_elem) if comment_elem else None
            
            return {
                'name': name,
                'sex': sex,
                'age': age,
                'sire': sire,
                'dam': dam,
                'damsire': damsire,
                'total_prize': total_prize,
                'comment': comment
            }
            
        except Exception as e:
            self.logger.error(f"馬の詳細情報の抽出中にエラーが発生しました: {str(e)}")
            raise
    
    def _extract_auction_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        オークション情報を抽出する
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            Dict[str, Any]: オークション情報
        """
        try:
            # オークションID（URLから抽出）
            auction_id = self._extract_auction_id(soup)
            
            # 馬ID（URLから抽出）
            horse_id = self._extract_horse_id(soup)
            
            # オークション日（実際のHTML構造に合わせて調整してください）
            date_elem = self.parser.find_element(soup, '.auction-date')
            auction_date = self.parser.get_text(date_elem)
            
            # 出品者・落札者・価格
            seller = self.parser.get_text(self.parser.find_element(soup, '.seller'))
            buyer = self.parser.get_text(self.parser.find_element(soup, '.buyer'))
            
            price_elem = self.parser.find_element(soup, '.price')
            price = self._parse_price(self.parser.get_text(price_elem)) if price_elem else None
            
            # 主取りフラグ
            is_unsold = 'unsold' in (price_elem.get('class', []) if price_elem else [])
            
            return {
                'auction_id': auction_id,
                'horse_id': horse_id,
                'auction_date': auction_date,
                'seller': seller,
                'buyer': buyer if not is_unsold else None,
                'price': price,
                'is_unsold': is_unsold
            }
            
        except Exception as e:
            self.logger.error(f"オークション情報の抽出中にエラーが発生しました: {str(e)}")
            raise
    
    def _parse_sex_and_age(self, text: str) -> Tuple[str, int]:
        """性別と年齢をパースする
        
        Args:
            text: 性別と年齢が含まれるテキスト（例: "牡3"）
            
        Returns:
            Tuple[str, int]: (性別, 年齢)のタプル
        """
        if not text:
            return '', 0
            
        # 性別を抽出
        sex = ''
        if '牡' in text:
            sex = '牡'
        elif '牝' in text:
            sex = '牝'
        elif 'セ' in text:
            sex = 'セ'
            
        # 年齢を抽出
        age_match = re.search(r'\d+', text)
        age = int(age_match.group()) if age_match else 0
        
        return sex, age
    
    def _parse_prize(self, text: str) -> float:
        """賞金をパースする
        
        Args:
            text: 賞金が含まれるテキスト（例: "1,234.5万円"）
            
        Returns:
            float: 賞金（万円単位）
        """
        if not text:
            return 0.0
            
        # 数字と小数点のみを抽出
        match = re.search(r'[\d,.]+', text.replace(',', ''))
        if match:
            try:
                return float(match.group())
            except (ValueError, TypeError):
                pass
                
        return 0.0
    
    def _parse_price(self, text: str) -> float:
        """価格をパースする
        
        Args:
            text: 価格が含まれるテキスト（例: "1,234.5万円"）
            
        Returns:
            float: 価格（万円単位）
        """
        if not text:
            return 0.0
            
        # 数字と小数点のみを抽出
        match = re.search(r'[\d,.]+', text.replace(',', ''))
        if match:
            try:
                return float(match.group())
            except (ValueError, TypeError):
                pass
                
        return 0.0
    
    def _extract_auction_id(self, soup: BeautifulSoup) -> str:
        """オークションIDを抽出する
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            str: オークションID
        """
        # 実際のHTML構造に合わせて実装してください
        # 例: URLや特定の要素からIDを抽出
        return ''
    
    def _extract_horse_id(self, soup: BeautifulSoup) -> str:
        """馬IDを抽出する
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            str: 馬ID
        """
        # 実際のHTML構造に合わせて実装してください
        # 例: URLや特定の要素からIDを抽出
        return ''
