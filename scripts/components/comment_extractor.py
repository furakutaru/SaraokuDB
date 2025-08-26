"""
コメント抽出コンポーネント

このモジュールは、BeautifulSoupオブジェクトから馬のコメントを抽出する機能を提供します。
"""

import re
import logging
from typing import Dict, Optional, Any, Tuple


class CommentExtractor:
    """馬のコメントを抽出するクラス"""
    
    def __init__(self, logger: logging.Logger = None):
        """初期化メソッド
        
        Args:
            logger: ロガーインスタンス（Noneの場合は新規作成）
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def extract(self, element) -> Tuple[Optional[Dict[str, str]], bool]:
        """BeautifulSoup要素からコメントを抽出する
        
        以下のような構造からコメントを抽出します:
        <table bgcolor="#fff7bc">
            <tbody>
                <tr>
                    <td>
                        <b>本馬について</b>
                        <hr>
                        <pre>コメント本文</pre>
                    </td>
                </tr>
            </tbody>
        </table>
        
        Args:
            element: BeautifulSoup要素
            
        Returns:
            Tuple[Optional[Dict[str, str]], bool]: 
                (抽出したコメント情報を含む辞書, 成功したかどうか)
        """
        try:
            # テーブル内のpreタグからコメントを抽出
            pre_tag = element.find('pre')
            
            if pre_tag and pre_tag.get_text(strip=True):
                # preタグ内のテキストを取得し、前後の空白を削除
                comment_text = pre_tag.get_text(separator='\n', strip=True)
                
                # 連続する改行を1つにまとめる
                comment_text = re.sub(r'\n{3,}', '\n\n', comment_text)
                
                if comment_text:
                    self.logger.debug(f'コメントを抽出しました: {comment_text[:50]}...')
                    return {'comment': comment_text}, True
            
            self.logger.debug('コメントが見つかりませんでした')
            return None, False
            
        except Exception as e:
            self.logger.error(f'コメントの抽出中にエラーが発生しました: {e}', exc_info=True)
            return None, False
