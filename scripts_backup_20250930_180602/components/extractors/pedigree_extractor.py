"""
血統情報抽出モジュール

このモジュールは、馬の血統情報（父・母・母父）を抽出するための機能を提供します。
"""

import re
from typing import Optional, Dict, Any, Union, Tuple
from bs4 import BeautifulSoup, Tag
import logging

class PedigreeExtractor:
    """血統情報抽出の責務を担当するクラス"""
    
    # 血統情報を抽出する正規表現パターン
    PEDIGREE_PATTERN = r'父[：:]([^\s　]+?)(?:\s|　|$).*?母[：:]([^\s　]+?)(?:\s|　|$)(?:母の父[：:]([^\s　]+(?:\s+[^\s　]+)*))?'
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初期化メソッド
        
        Args:
            logger: ロガーインスタンス。指定しない場合はルートロガーを使用
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def _clean_text(self, text: Optional[str]) -> Optional[str]:
        """抽出したテキストをクリーニング"""
        if not text:
            return None
            
        # 改行と不要な空白を削除
        text = ' '.join(text.split())
        # 先頭・末尾の空白と改行を削除
        text = text.strip('\n\r\t 　')
        # 連続する空白を1つにまとめる
        text = re.sub(r'\s+', ' ', text)
        
        # 不要な情報を削除（例：通算成績、賞金情報など）
        text = re.sub(r'\s*(通算成績|獲得賞金|最終出走|馬体重|賞金)[:：].*?\d', '', text)
        text = re.sub(r'\s*\[.*?\]', '', text)  # カッコ内の情報を削除
        text = re.sub(r'\s*\(.*?\)', '', text)  # 丸カッコ内の情報を削除
        text = re.sub(r'[\[\]()【】]', '', text)  # その他の括弧を削除
        
        # 不要な記号や空白を削除
        text = text.replace('\u3000', ' ')  # 全角スペースを半角に
        text = text.strip(' 　,.')
        
        # 通算成績などの不要な単語を削除
        text = re.sub(r'\s*(?:通算成績|獲得賞金|馬体重|賞金|戦|勝|負|着|人気|着差|kg|kg|万円|円|:|：|\|).*$', '', text)
        
        return text.strip() or None
    
    def _extract_from_text(self, text: str) -> Dict[str, Optional[str]]:
        """
        テキストから血統情報を抽出
        
        Args:
            text: 抽出元のテキスト
            
        Returns:
            Dict[str, Optional[str]]: 血統情報を含む辞書（'sire', 'dam', 'damsire' のキーを持つ）
        """
        result = {
            'sire': None,    # 父
            'dam': None,     # 母
            'damsire': None  # 母父
        }
        
        if not text:
            return result
        
        # 正規表現パターンを柔軟に
        patterns = [
            # パターン1: 完全な形式「父：XXX 母：YYY 母の父：ZZZ」
            r'父[:：]\s*([^\s　:：]+(?:\s+[^\s　:：]+)*)(?:\s|　|$).*?母[:：]\s*([^\s　:：]+(?:\s+[^\s　:：]+)*)(?:\s|　|$)(?:母の父[:：]\s*([^\s　:：]+(?:\s+[^\s　:：]+)*))?',
            # パターン2: 父と母のみ「父：XXX 母：YYY」
            r'父[:：]\s*([^\s　:：]+(?:\s+[^\s　:：]+)*)(?:\s|　|$).*?母[:：]\s*([^\s　:：]+(?:\s+[^\s　:：]+)*)(?:\s|$|\b)',
            # パターン3: 父のみ（母の記述がない場合）
            r'(?:^|[\s　])父[:：]\s*([^\s　:：]+(?:\s+[^\s　:：]+)*)(?=\s|　|$)(?![\s\S]*母[:：])',
            # パターン4: 改行区切り
            r'父[:：]\s*([^\n]+?)(?:\n|$).*?母[:：]\s*([^\n]+?)(?:\n|$)(?:母の父[:：]\s*([^\n]+))?',
            # パターン5: スペース区切り（例：父:キングカメハメハ 母:トーセンレーヴ）
            r'父[:：]([^\s　:：]+(?:\s+[^\s　:：]+)*)(?:\s|$).*?母[:：]([^\s　:：]+(?:\s+[^\s　:：]+)*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                # グループの存在を確認しながら抽出
                if match.lastindex >= 1 and match.group(1):
                    result['sire'] = self._clean_text(match.group(1))
                
                if match.lastindex >= 2 and match.group(2):
                    result['dam'] = self._clean_text(match.group(2))
                
                if match.lastindex >= 3 and match.group(3):
                    result['damsire'] = self._clean_text(match.group(3))
                
                # 少なくとも1つ有効な情報があれば終了
                if any(result.values()):
                    break
        
        return result
    
    def extract(self, source: Union[str, BeautifulSoup, Tag]) -> Dict[str, Optional[str]]:
        """
        ソースから血統情報を抽出
        
        Args:
            source: 抽出元（テキストまたはBeautifulSoup要素）
            
        Returns:
            Dict[str, Optional[str]]: 血統情報を含む辞書（'sire', 'dam', 'damsire' のキーを持つ）
        """
        if not source:
            return {'sire': None, 'dam': None, 'damsire': None}
            
        # 文字列の場合はそのまま処理
        if isinstance(source, str):
            return self._extract_from_text(source)
            
        # BeautifulSoup要素の場合はテキストを取得して処理
        try:
            # 詳細ページの情報が含まれている可能性のある要素を検索
            details_elem = source.select_one('#itemDetails')
            if details_elem:
                text = details_elem.get_text(' ', strip=True)
                return self._extract_from_text(text)
                
            # 要素全体のテキストからも検索
            text = source.get_text(' ', strip=True)
            return self._extract_from_text(text)
            
        except Exception as e:
            self.logger.debug(f'血統情報の抽出中にエラーが発生しました: {e}')
            return {'sire': None, 'dam': None, 'damsire': None}
    
    def extract_sire(self, source: Union[str, BeautifulSoup, Tag]) -> Optional[str]:
        """父馬名のみを抽出"""
        return self.extract(source).get('sire')
    
    def extract_dam(self, source: Union[str, BeautifulSoup, Tag]) -> Optional[str]:
        """母馬名のみを抽出"""
        return self.extract(source).get('dam')
    
    def extract_damsire(self, source: Union[str, BeautifulSoup, Tag]) -> Optional[str]:
        """母父名のみを抽出"""
        return self.extract(source).get('damsire')
