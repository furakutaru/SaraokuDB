"""
JBIS（日本軽種馬協会）の情報をスクレイピングするモジュール
"""
import re
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper
from ..models.horse import Horse
from ..utils.html_parser import HTMLParser
from ..utils.data_validator import Validator, ValidationError

class JBISScraper(BaseScraper):
    """JBIS（日本軽種馬協会）のスクレイピングクラス"""
    
    BASE_URL = "https://www.jbis.or.jp/"
    
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
    
    def fetch_horse_info(self, horse_id: str) -> Dict[str, Any]:
        """
        馬の情報を取得する
        
        Args:
            horse_id: 馬ID
            
        Returns:
            Dict[str, Any]: 馬の情報
        """
        try:
            # 血統情報ページのURLを生成
            url = f"horse/{horse_id}/pedigree/"
            response = self.request_get(url)
            soup = self.parser.parse_html(response.text)
            
            # 馬の基本情報を抽出
            horse_info = self._extract_horse_info(soup, horse_id)
            
            # 賞金情報を取得（別ページ）
            prize_url = f"horse/{horse_id}/race/"
            prize_response = self.request_get(prize_url)
            prize_soup = self.parser.parse_html(prize_response.text)
            
            # 賞金情報を抽出
            prize_info = self._extract_prize_info(prize_soup)
            
            # 情報をマージ
            horse_info.update(prize_info)
            
            return horse_info
            
        except Exception as e:
            self.logger.error(f"馬情報の取得中にエラーが発生しました（馬ID: {horse_id}）: {str(e)}")
            raise
    
    def _extract_horse_info(self, soup: BeautifulSoup, horse_id: str) -> Dict[str, Any]:
        """
        馬の基本情報を抽出する
        
        Args:
            soup: BeautifulSoupオブジェクト
            horse_id: 馬ID
            
        Returns:
            Dict[str, Any]: 馬の基本情報
        """
        try:
            # 馬名を取得
            name_elem = self.parser.find_element(soup, '.main_ttl_blue')
            name = self.parser.get_text(name_elem).strip() if name_elem else ''
            
            # 性別と年齢を取得
            sex_age_elem = self.parser.find_element(soup, '.horse_title')
            sex, age = self._parse_sex_and_age(self.parser.get_text(sex_age_elem))
            
            # 血統情報を取得
            pedigree_table = self.parser.find_element(soup, '.tbl_pedigree')
            sire, dam, damsire = self._extract_pedigree(pedigree_table)
            
            return {
                'horse_id': horse_id,
                'name': name,
                'sex': sex,
                'age': age,
                'sire': sire,
                'dam': dam,
                'damsire': damsire
            }
            
        except Exception as e:
            self.logger.error(f"馬の基本情報の抽出中にエラーが発生しました: {str(e)}")
            raise
    
    def _extract_prize_info(self, soup: BeautifulSoup) -> Dict[str, float]:
        """
        賞金情報を抽出する
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            Dict[str, float]: 賞金情報
        """
        try:
            # 賞金情報のテーブルを探す
            prize_table = self.parser.find_element(soup, '.tbl_data')
            if not prize_table:
                return {'total_prize': 0.0}
            
            # 総賞金を探す（実際のHTML構造に合わせて調整が必要）
            rows = self.parser.find_elements(prize_table, 'tr')
            total_prize = 0.0
            
            for row in rows:
                cells = self.parser.find_elements(row, 'td')
                if len(cells) >= 2:
                    label = self.parser.get_text(cells[0]).strip()
                    if '総賞金' in label:
                        value_text = self.parser.get_text(cells[1]).strip()
                        total_prize = self._parse_prize(value_text)
                        break
            
            return {
                'total_prize': total_prize
            }
            
        except Exception as e:
            self.logger.warning(f"賞金情報の抽出中にエラーが発生しました: {str(e)}")
            return {'total_prize': 0.0}
    
    def _extract_pedigree(self, pedigree_table) -> Tuple[str, str, str]:
        """
        血統情報を抽出する
        
        Args:
            pedigree_table: 血統テーブルのBeautifulSoup要素
            
        Returns:
            Tuple[str, str, str]: (父, 母, 母父)のタプル
        """
        if not pedigree_table:
            return '', '', ''
            
        try:
            # 父を抽出
            sire_elem = self.parser.find_element(pedigree_table, '.sire .name')
            sire = self.parser.get_text(sire_elem).strip() if sire_elem else ''
            
            # 母を抽出
            dam_elem = self.parser.find_element(pedigree_table, '.dam .name')
            dam = self.parser.get_text(dam_elem).strip() if dam_elem else ''
            
            # 母父を抽出
            damsire_elem = self.parser.find_element(pedigree_table, '.damsire .name')
            damsire = self.parser.get_text(damsire_elem).strip() if damsire_elem else ''
            
            return sire, dam, damsire
            
        except Exception as e:
            self.logger.warning(f"血統情報の抽出中にエラーが発生しました: {str(e)}")
            return '', '', ''
    
    def _parse_sex_and_age(self, text: str) -> Tuple[str, int]:
        """性別と年齢をパースする
        
        Args:
            text: 性別と年齢が含まれるテキスト
            
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
