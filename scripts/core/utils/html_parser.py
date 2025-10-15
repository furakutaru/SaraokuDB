"""
HTML解析のためのユーティリティ関数を提供するモジュール
"""
from typing import Optional, List, Dict, Any, Union
import re
from bs4 import BeautifulSoup, Tag, ResultSet
from bs4.element import NavigableString

from ..utils.logger import get_logger

logger = get_logger(__name__)

class HTMLParser:
    """HTML解析のためのユーティリティクラス"""
    
    @staticmethod
    def parse_html(html_content: str, parser: str = 'html.parser') -> BeautifulSoup:
        """
        HTML文字列をBeautifulSoupオブジェクトにパースする
        
        Args:
            html_content: HTML文字列
            parser: パーサー（デフォルト: 'html.parser'）
            
        Returns:
            BeautifulSoup: パースされたBeautifulSoupオブジェクト
        """
        try:
            return BeautifulSoup(html_content, parser)
        except Exception as e:
            logger.error(f"HTMLのパースに失敗しました: {str(e)}")
            raise
    
    @staticmethod
    def find_element(soup: BeautifulSoup, selector: str, **kwargs) -> Optional[Tag]:
        """
        指定されたセレクタに一致する最初の要素を取得する
        
        Args:
            soup: BeautifulSoupオブジェクト
            selector: CSSセレクタ
            **kwargs: その他の引数（findメソッドに渡される）
            
        Returns:
            Optional[Tag]: 見つかった要素、見つからない場合はNone
        """
        try:
            return soup.select_one(selector, **kwargs)
        except Exception as e:
            logger.warning(f"要素の検索に失敗しました（セレクタ: {selector}）: {str(e)}")
            return None
    
    @staticmethod
    def find_elements(soup: BeautifulSoup, selector: str, **kwargs) -> List[Tag]:
        """
        指定されたセレクタに一致するすべての要素を取得する
        
        Args:
            soup: BeautifulSoupオブジェクト
            selector: CSSセレクタ
            **kwargs: その他の引数（find_allメソッドに渡される）
            
        Returns:
            List[Tag]: 見つかった要素のリスト、見つからない場合は空のリスト
        """
        try:
            return soup.select(selector, **kwargs)
        except Exception as e:
            logger.warning(f"要素の検索に失敗しました（セレクタ: {selector}）: {str(e)}")
            return []
    
    @staticmethod
    def get_text(element: Union[Tag, NavigableString, str], default: str = '') -> str:
        """
        要素からテキストを取得する
        
        Args:
            element: BeautifulSoupの要素
            default: 要素がNoneの場合のデフォルト値
            
        Returns:
            str: 抽出されたテキスト
        """
        if element is None:
            return default
        
        if isinstance(element, str):
            return element.strip()
            
        if hasattr(element, 'get_text'):
            return element.get_text(separator=' ', strip=True)
            
        return str(element).strip()
    
    @staticmethod
    def get_attribute(element: Optional[Tag], attribute: str, default: str = '') -> str:
        """
        要素の属性値を取得する
        
        Args:
            element: BeautifulSoupの要素
            attribute: 取得する属性名
            default: 属性が存在しない場合のデフォルト値
            
        Returns:
            str: 属性値、存在しない場合はデフォルト値
        """
        if element is None or not hasattr(element, 'get'):
            return default
            
        return element.get(attribute, default).strip()
    
    @staticmethod
    def extract_text_by_regex(text: str, pattern: str, group: int = 1, default: str = '') -> str:
        """
        正規表現を使用してテキストから値を抽出する
        
        Args:
            text: 検索対象のテキスト
            pattern: 正規表現パターン
            group: 取得するグループ番号（デフォルト: 1）
            default: マッチしない場合のデフォルト値
            
        Returns:
            str: 抽出された値、マッチしない場合はデフォルト値
        """
        if not text:
            return default
            
        match = re.search(pattern, text, re.DOTALL)
        if match and len(match.groups()) >= group:
            return match.group(group).strip()
            
        return default
