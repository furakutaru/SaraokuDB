"""
馬体重情報を抽出するモジュール
"""
import re
import logging
from typing import Dict, Optional, Union
from bs4 import BeautifulSoup, Tag

class HorseWeightExtractor:
    """馬体重情報を抽出するクラス"""
    
    # 馬体重を抽出する正規表現パターン
    WEIGHT_PATTERNS = [
        r'馬体重[：:]?\s*(\d+)\s*kg',  # 馬体重：454kg や 馬体重454kg などにマッチ
        r'馬体重は(\d+)kg',           # 馬体重は454kg にマッチ
        r'馬体重(\d+)kg'              # 馬体重454kg にマッチ
    ]
    
    def __init__(self, logger: logging.Logger = None):
        """
        初期化メソッド
        
        Args:
            logger: ロガーインスタンス（Noneの場合は新規作成）
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def extract(self, soup: Union[BeautifulSoup, str]) -> Dict[str, Optional[int]]:
        """
        HTMLから馬体重情報を抽出する
        
        Args:
            soup: BeautifulSoupオブジェクトまたはHTML文字列
            
        Returns:
            Dict[str, Optional[int]]: 抽出した馬体重情報（キー: 'weight_kg'）
        """
        result = {'weight_kg': None}
        
        try:
            # 文字列が渡された場合はBeautifulSoupオブジェクトに変換
            if isinstance(soup, str):
                soup = BeautifulSoup(soup, 'html.parser')
            
            # テキストを取得
            text = soup.get_text(' ', strip=True)
            
            # 正規表現で馬体重を抽出
            weight = None
            matched_pattern = None
            
            for pattern in self.WEIGHT_PATTERNS:
                match = re.search(pattern, text)
                if match:
                    weight = int(match.group(1))
                    matched_pattern = pattern
                    break
            
            if weight is not None:
                result['weight_kg'] = weight
                self.logger.info(f'馬体重を抽出しました: {weight}kg (パターン: "{matched_pattern}", テキスト: "{match.group(0).strip()}")')
            else:
                self.logger.warning('馬体重情報が見つかりませんでした。テキスト: %s', text[:100] + '...' if len(text) > 100 else text)
                
        except Exception as e:
            self.logger.error(f'馬体重の抽出中にエラーが発生しました: {e}', exc_info=True)
            
        return result
