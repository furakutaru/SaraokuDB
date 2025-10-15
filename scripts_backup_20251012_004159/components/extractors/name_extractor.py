"""
馬名抽出モジュール

このモジュールは、様々なソースから馬名を抽出するための機能を提供します。
リストページ、詳細ページのタイトル、itemTitle要素など、異なるソースから
一貫した方法で馬名を抽出できます。
"""

import re
from typing import Optional, Any, Dict, List, Union
from bs4 import BeautifulSoup, Tag
import logging

class NameExtractor:
    """馬名抽出の責務を担当するクラス"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初期化メソッド
        
        Args:
            logger: ロガーインスタンス。指定しない場合はルートロガーを使用
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # 馬名抽出用の正規表現パターン
        self.patterns = {
            'list_page': r'^(.+?)(?:\s*※|$)',  # リストページ用（※以降を除去）
            'detail_title': r'^(.+?)(?:\s*[牡牝セ]\s*\d+歳|※|$)',  # 詳細ページタイトル用
            'item_title': r'^(.+?)(?:\s*[牡牝セ]\s*\d+歳|※|$)'  # itemTitle要素用（詳細ページ内）
        }
    
    def from_list_page(self, element: Union[BeautifulSoup, Tag, str]) -> Optional[str]:
        """
        リストページから馬名を抽出
        
        Args:
            element: BeautifulSoup要素またはHTML文字列
            
        Returns:
            Optional[str]: 抽出された馬名。抽出できない場合はNone
        """
        try:
            if isinstance(element, (BeautifulSoup, Tag)):
                name_elem = element.select_one('.horse-name')
                name_text = name_elem.get_text(strip=True) if name_elem else ''
            else:
                name_text = str(element).strip()
            
            return self._clean_name(name_text, 'list_page')
        except Exception as e:
            self.logger.debug(f'リストページからの馬名抽出に失敗しました: {e}')
            return None
    
    def from_detail_title(self, title_text: str) -> Optional[str]:
        """
        詳細ページのタイトルから馬名を抽出
        
        Args:
            title_text: タイトルテキスト
            
        Returns:
            Optional[str]: 抽出された馬名。抽出できない場合はNone
        """
        try:
            return self._clean_name(title_text, 'detail_title')
        except Exception as e:
            self.logger.debug(f'詳細ページタイトルからの馬名抽出に失敗しました: {e}')
            return None
    
    def from_item_title(self, item_title: Union[BeautifulSoup, Tag, str]) -> Optional[str]:
        """
        詳細ページのitemTitle要素から馬名を抽出
        
        Args:
            item_title: itemTitle要素（BeautifulSoup、Tag、または文字列）
            
        Returns:
            Optional[str]: 抽出された馬名。抽出できない場合はNone
        """
        try:
            if isinstance(item_title, (BeautifulSoup, Tag)):
                name_elem = item_title.select_one('[itemprop="name"]')
                name_text = name_elem.get_text(strip=True) if name_elem else ''
            else:
                name_text = str(item_title).strip()
            
            return self._clean_name(name_text, 'item_title')
        except Exception as e:
            self.logger.debug(f'itemTitleからの馬名抽出に失敗しました: {e}')
            return None
    
    def _clean_name(self, name: str, source_type: str) -> Optional[str]:
        """
        抽出された馬名をクリーンアップ
        
        Args:
            name: 抽出された馬名
            source_type: ソースタイプ（'list_page', 'detail_title', 'item_title'）
            
        Returns:
            Optional[str]: クリーンアップされた馬名
        """
        if not name:
            return None
            
        # ソースタイプに応じたパターンでマッチング
        pattern = self.patterns.get(source_type, self.patterns['list_page'])
        match = re.match(pattern, name.strip())
        
        if not match:
            return None
            
        cleaned = match.group(1).strip()
        
        # 不要な文字を削除
        for char in ['※', '登録抹消', '新馬', '未出走', '　']:
            cleaned = cleaned.replace(char, '')
        
        # 連続するスペースを1つに
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned if cleaned else None
    
    def extract(self, source: Any, source_type: str = 'auto') -> Optional[str]:
        """
        ソースに応じた適切な方法で馬名を抽出
        
        Args:
            source: 抽出元（BeautifulSoup要素、文字列など）
            source_type: ソースタイプ（'auto', 'list_page', 'detail_title', 'item_title'）
            
        Returns:
            Optional[str]: 抽出された馬名。抽出できない場合はNone
        """
        if not source:
            return None
        
        # 自動判定
        if source_type == 'auto':
            if isinstance(source, (BeautifulSoup, Tag)):
                # itemTitle要素を優先して検索
                item_title = source.select_one('#itemTitle')
                if item_title:
                    return self.from_item_title(item_title)
                
                # リストページの要素を検索
                return self.from_list_page(source)
            
            # 文字列の場合は詳細ページのタイトルと仮定
            return self.from_detail_title(str(source))
        
        # 明示的にソースタイプが指定されている場合
        extractors = {
            'list_page': self.from_list_page,
            'detail_title': self.from_detail_title,
            'item_title': self.from_item_title
        }
        
        extractor = extractors.get(source_type)
        return extractor(source) if extractor else None
