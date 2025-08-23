"""
コメント抽出コンポーネント

このモジュールは、BeautifulSoupオブジェクトから馬のコメントを抽出する機能を提供します。
"""

import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class CommentExtractor:
    """馬のコメントを抽出するクラス"""
    
    @staticmethod
    def extract(soup) -> Dict[str, str]:
        """BeautifulSoupオブジェクトからコメントを抽出する
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            Dict[str, str]: 抽出したコメント情報を含む辞書
        """
        result = {'comment': ''}
        
        try:
            # コメントセクションを探す（クラス名は実際のHTMLに合わせて調整が必要）
            comment_section = soup.find('div', class_=re.compile(r'comment|description|remarks', re.IGNORECASE))
            
            if not comment_section:
                # 別の一般的なコメントセレクタを試す
                comment_section = (
                    soup.find('p', class_=re.compile(r'comment|description|remarks', re.IGNORECASE)) or
                    soup.find('div', {'id': re.compile(r'comment|description|remarks', re.IGNORECASE)})
                )
            
            if comment_section:
                # コメントテキストを取得し、前後の空白を削除
                comment_text = comment_section.get_text(separator=' ', strip=True)
                
                # 不要な改行や空白を正規化
                comment_text = re.sub(r'\s+', ' ', comment_text).strip()
                
                # コメントをそのまま返す（文字数制限なし）
                result['comment'] = comment_text
                
            logger.debug(f"[COMMENT] 抽出したコメント: {result['comment']}")
            
        except Exception as e:
            logger.error(f"[COMMENT_ERROR] コメントの抽出中にエラーが発生しました: {str(e)}", exc_info=True)
        
        return result
