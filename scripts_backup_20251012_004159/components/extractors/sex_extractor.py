"""
性別抽出モジュール

このモジュールは、様々なソースから馬の性別（牡・牝・セ）を抽出するための機能を提供します。
"""

import re
from typing import Optional, Any, Dict, List, Union
from bs4 import BeautifulSoup, Tag
import logging

class SexExtractor:
    """性別抽出の責務を担当するクラス"""
    
    # 性別を表す正規表現パターン
    SEX_PATTERNS = {
        'stallion': r'牡',  # 牡馬
        'mare': r'牝',      # 牝馬
        'gelding': r'(セ|セン|せん)',   # せん馬（セ・セン・せんのいずれも可）
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初期化メソッド
        
        Args:
            logger: ロガーインスタンス。指定しない場合はルートロガーを使用
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def from_text(self, text: str) -> Optional[str]:
        """
        テキストから性別を抽出
        
        Args:
            text: 抽出元のテキスト
            
        Returns:
            Optional[str]: 抽出された性別（'牡', '牝', 'セ' のいずれか）。見つからない場合はNone
        """
        if not text:
            return None
            
        # 正規表現で性別を検索
        for sex_type, pattern in self.SEX_PATTERNS.items():
            if re.search(pattern, text):
                return self._get_sex_code(sex_type)
        
        return None
    
    def from_element(self, element: Union[BeautifulSoup, Tag, str]) -> Optional[str]:
        """
        HTML要素から性別を抽出
        
        Args:
            element: BeautifulSoup要素またはHTML文字列
            
        Returns:
            Optional[str]: 抽出された性別（'牡', '牝', 'セ' のいずれか）。見つからない場合はNone
        """
        if not element:
            return None
            
        # 文字列の場合はそのまま処理
        if isinstance(element, str):
            return self.from_text(element)
            
        # 要素からテキストを取得
        try:
            # 性別が含まれている可能性のある要素を検索
            info_elem = element.select_one('.horse-info, .sex, [class*="info"], [class*="sex"]')
            if info_elem:
                text = info_elem.get_text(strip=True)
                return self.from_text(text)
                
            # 要素全体のテキストからも検索
            text = element.get_text(strip=True)
            return self.from_text(text)
            
        except Exception as e:
            self.logger.debug(f'性別の抽出中にエラーが発生しました: {e}')
            return None
    
    def extract(self, source: Any, source_type: str = 'auto') -> Optional[str]:
        """
        ソースから性別を抽出
        
        Args:
            source: 抽出元（テキスト、BeautifulSoup要素、辞書など）
            source_type: ソースタイプ（'auto', 'text', 'element'）
            
        Returns:
            Optional[str]: 抽出された性別（'牡', '牝', 'セ' のいずれか）。見つからない場合はNone
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
    
    @staticmethod
    def _get_sex_code(sex_type: str) -> str:
        """性別タイプをコードに変換"""
        sex_map = {
            'stallion': '牡',
            'mare': '牝',
            'gelding': 'セ'
        }
        return sex_map.get(sex_type, '')
