"""
年齢抽出モジュール

このモジュールは、様々なソースから馬の年齢を抽出するための機能を提供します。
"""

import re
from typing import Optional, Any, Union
from bs4 import BeautifulSoup, Tag
import logging

class AgeExtractor:
    """年齢抽出の責務を担当するクラス"""
    
    # 年齢を表す正規表現パターン
    AGE_PATTERN = r'(\d+)[歳才]'
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初期化メソッド
        
        Args:
            logger: ロガーインスタンス。指定しない場合はルートロガーを使用
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def from_text(self, text: str) -> Optional[int]:
        """
        テキストから年齢を抽出
        
        Args:
            text: 抽出元のテキスト（例: "3歳", "2才"）
            
        Returns:
            Optional[int]: 抽出された年齢（数値）。見つからない場合はNone
        """
        if not text:
            return None
            
        # 正規表現で年齢を検索
        match = re.search(self.AGE_PATTERN, text)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError) as e:
                self.logger.debug(f'年齢の変換に失敗しました: {e}')
                return None
        return None
    
    def from_element(self, element: Union[BeautifulSoup, Tag, str]) -> Optional[int]:
        """
        HTML要素から年齢を抽出
        
        Args:
            element: BeautifulSoup要素またはHTML文字列
            
        Returns:
            Optional[int]: 抽出された年齢（数値）。見つからない場合はNone
        """
        if not element:
            return None
            
        # 文字列の場合はそのまま処理
        if isinstance(element, str):
            return self.from_text(element)
            
        # 要素からテキストを取得
        try:
            # 年齢が含まれている可能性のある要素を検索
            age_elem = element.select_one('.horseLabelWrapper__horseAge, .age, [class*="age"], [class*="Age"]')
            if age_elem:
                text = age_elem.get_text(strip=True)
                return self.from_text(text)
                
            # 要素全体のテキストからも検索
            text = element.get_text(strip=True)
            return self.from_text(text)
            
        except Exception as e:
            self.logger.debug(f'年齢の抽出中にエラーが発生しました: {e}')
            return None
    
    def extract(self, source: Any, source_type: str = 'auto') -> Optional[int]:
        """
        ソースから年齢を抽出
        
        Args:
            source: 抽出元（テキスト、BeautifulSoup要素、辞書など）
            source_type: ソースタイプ（'auto', 'text', 'element'）
            
        Returns:
            Optional[int]: 抽出された年齢（数値）。見つからない場合はNone
        """
        if not source:
            return None
            
        # 自動判定
        if source_type == 'auto':
            if isinstance(source, (BeautifulSoup, Tag)):
                return self.from_element(source)
            elif isinstance(source, str):
                return self.from_text(source)
            elif hasattr(source, 'get_text'):  # get_textメソッドを持つオブジェクト
                return self.from_text(source.get_text())
            else:
                return self.from_text(str(source))
        
        # 明示的にソースタイプが指定されている場合
        extractors = {
            'text': self.from_text,
            'element': self.from_element
        }
        
        extractor = extractors.get(source_type)
        return extractor(source) if extractor else None
