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
    WEIGHT_PATTERN = r'最終出走馬体重[：:](\d+)kg'
    
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
            match = re.search(self.WEIGHT_PATTERN, text)
            if match:
                weight = int(match.group(1))
                result['weight_kg'] = weight
                self.logger.debug(f'馬体重を抽出しました: {weight}kg')
            else:
                self.logger.debug('馬体重情報が見つかりませんでした')
                
        except Exception as e:
            self.logger.error(f'馬体重の抽出中にエラーが発生しました: {e}', exc_info=True)
            
        return result
