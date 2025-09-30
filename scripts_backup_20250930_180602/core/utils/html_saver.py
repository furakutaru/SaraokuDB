"""
HTML保存ユーティリティ

このモジュールは、スクレイピングしたHTMLをファイルに保存する機能を提供します。
デバッグや分析目的で使用します。
"""

import logging
import time
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class HTMLSaver:
    """HTMLコンテンツをファイルに保存するためのクラス"""
    
    def __init__(self, base_dir: Path):
        """
        HTMLSaverの初期化
        
        Args:
            base_dir: HTMLを保存するベースディレクトリ
        """
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"HTML保存先: {self.base_dir}")
        
    def save(self, url: str, content: str) -> Optional[Path]:
        """
        HTMLコンテンツをURLに基づいて適切なパスに保存する
        
        Args:
            url: 取得元のURL
            content: 保存するHTMLコンテンツ
            
        Returns:
            保存されたファイルのPath、またはエラー時はNone
        """
        try:
            parsed_url = urlparse(url)
            path_parts = [p for p in parsed_url.path.split('/') if p]
            is_detail = any(x in path_parts for x in ['item', 'detail', 'horse'])
            
            # 保存先ディレクトリとファイル名を決定
            if is_detail:
                filename = f"{path_parts[-1]}.html" if path_parts else f"detail_{int(time.time())}.html"
                save_dir = self.base_dir / 'details'
            else:
                filename = "index.html"
                save_dir = self.base_dir
            
            # ディレクトリが存在しない場合は作成
            save_dir.mkdir(exist_ok=True, parents=True)
            filepath = save_dir / filename
            
            # ファイルに保存
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.debug(f"HTMLを保存しました: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"HTMLの保存に失敗しました: {e}", exc_info=True)
            return None
    
    @staticmethod
    def create_dated_dirs(base_path: Path) -> Tuple[Path, Path]:
        """
        日付ベースのディレクトリを作成する
        
        Args:
            base_path: ベースとなるパス
            
        Returns:
            (date_dir, detail_dir) のタプル
        """
        from datetime import datetime
        
        # 日付ベースのディレクトリ名を作成 (YYYYMMDD_HHMMSS)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        date_dir = base_path / timestamp
        detail_dir = date_dir / 'details'
        
        # ディレクトリが存在しない場合は作成
        date_dir.mkdir(parents=True, exist_ok=True)
        detail_dir.mkdir(exist_ok=True)
        
        logger.info(f"HTML保存先: {date_dir}")
        return date_dir, detail_dir
