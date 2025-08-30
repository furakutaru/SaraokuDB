"""
馬の基本情報を抽出するためのコンポーネント（修正版）
"""
import re
import traceback
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup, Tag
import logging

class HorseInfoExtractor:
    """馬の基本情報を抽出するクラス"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初期化メソッド
        
        Args:
            logger: ロガーインスタンス（指定がない場合は新規作成）
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def _extract_pedigree(self, horse_element: Tag) -> Dict[str, str]:
        """
        血統情報を抽出する
        
        Args:
            horse_element: 馬情報を含むBeautifulSoup要素
            
        Returns:
            Dict[str, str]: 抽出した血統情報（sire, dam, damsire）を含む辞書
        """
        result = {}
        try:
            # 要素のテキストを取得
            text = horse_element.get_text(separator=' ', strip=True)
            
            # 正規表現で血統情報を抽出
            # 形式: 父：テスト父馬　母：テスト母馬　母の父：テスト母父馬
            pattern = r'父[：:]([^\s　]+?)\s*母[：:]([^\s　]+?)\s*母の?父[：:]([^\s　\d\n]+)'
            match = re.search(pattern, text)
            
            if match:
                result['sire'] = match.group(1).strip()  # 父
                result['dam'] = match.group(2).strip()    # 母
                result['damsire'] = match.group(3).strip()  # 母の父
                
                self.logger.debug(f'血統情報を抽出しました: sire={result["sire"]}, dam={result["dam"]}, damsire={result["damsire"]}')
            else:
                self.logger.warning('血統情報のパターンが一致しませんでした')
                self.logger.debug(f'抽出対象テキスト: {text[:200]}...')
                
        except Exception as e:
            self.logger.error(f'血統情報の抽出中にエラーが発生しました: {str(e)}')
            self.logger.debug(f'エラー詳細: {traceback.format_exc()}')
            
        return result
