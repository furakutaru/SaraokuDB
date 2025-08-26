"""
通算成績を抽出するモジュール
"""
import re
import logging
from typing import Dict, Optional, Any, Tuple


class RaceRecordExtractor:
    """通算成績を抽出するクラス"""
    
    def __init__(self, logger: logging.Logger = None):
        """初期化メソッド
        
        Args:
            logger: ロガーインスタンス（Noneの場合は新規作成）
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def extract(self, element) -> Tuple[Optional[Dict[str, str]], bool]:
        """通算成績を抽出する
        
        Args:
            element: BeautifulSoup要素
            
        Returns:
            Tuple[Optional[Dict[str, str]], bool]: 
                (通算成績情報を含む辞書, 成功したかどうか)
        """
        try:
            # テーブル内のテキストを取得
            table_text = element.get_text(' ', strip=True)
            
            # 通算成績の抽出
            record_match = re.search(r'通算成績[：:]([^\s]+)', table_text)
            if record_match:
                record = record_match.group(1).strip()
                if record:
                    self.logger.debug(f'通算成績を抽出しました: {record}')
                    return {'record': record}, True
                
            self.logger.debug('通算成績のパターンが一致しませんでした')
            return None, False
                
        except Exception as e:
            self.logger.error(f'通算成績の抽出中にエラーが発生しました: {e}', exc_info=True)
            return None, False
