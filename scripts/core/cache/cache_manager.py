"""
HTMLキャッシュを管理するモジュール
"""
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Dict, Optional, List

class CacheManager:
    """HTMLキャッシュを管理するクラス"""
    
    def __init__(self, base_dir: Path = None):
        """
        キャッシュマネージャーを初期化します。
        
        Args:
            base_dir: キャッシュディレクトリのパス（指定しない場合は設定値を使用）
        """
        self.base_dir = base_dir if base_dir is not None else Path('cache')
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.cache = {}
        self._load_cache()
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"キャッシュディレクトリ: {self.base_dir}")
    
    def _get_cache_path(self, url: str) -> Path:
        """
        URLからキャッシュファイルのパスを生成します。
        
        Args:
            url: キャッシュするURL
            
        Returns:
            Path: キャッシュファイルのパス
        """
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        return self.base_dir / f"{url_hash}.html"
    
    def load_html(self, url: str) -> Optional[str]:
        """
        URLに対応するキャッシュされたHTMLを読み込みます。
        
        Args:
            url: 読み込むHTMLのURL
            
        Returns:
            str: キャッシュされたHTMLコンテンツ。見つからない場合はNone
        """
        cache_path = self._get_cache_path(url)
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                self.logger.error(f"キャッシュの読み込みに失敗しました: {e}")
        return None
    
    def save_html(self, url: str, content: str) -> bool:
        """
        HTMLコンテンツをキャッシュに保存します。
        
        Args:
            url: キャッシュするHTMLのURL
            content: 保存するHTMLコンテンツ
            
        Returns:
            bool: 保存に成功した場合はTrue、失敗した場合はFalse
        """
        try:
            cache_path = self._get_cache_path(url)
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            self.logger.error(f"キャッシュの保存に失敗しました: {e}")
            return False
    
    def _load_cache(self) -> None:
        """既存のキャッシュをメモリに読み込みます。"""
        cache_index = self.base_dir / 'cache_index.json'
        if cache_index.exists():
            try:
                with open(cache_index, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except Exception as e:
                self.logger.error(f"キャッシュインデックスの読み込みに失敗しました: {e}")
                self.cache = {}
    
    def get(self, url: str) -> Optional[str]:
        """
        キャッシュからHTMLを取得します。
        
        Args:
            url: 取得するURL
            
        Returns:
            str: キャッシュされたHTMLコンテンツ、またはNone
        """
        return self.load_html(url)
    
    def set(self, url: str, content: str) -> None:
        """
        HTMLをキャッシュに保存します。
        
        Args:
            url: キャッシュするURL
            content: キャッシュするHTMLコンテンツ
        """
        self.save_html(url, content)
    
    def clear_expired(self, expire_days: int = 30) -> int:
        """
        有効期限が切れたキャッシュを削除します。
        
        Args:
            expire_days: 有効期限（日数）
            
        Returns:
            int: 削除したキャッシュファイルの数
        """
        if not self.base_dir.exists():
            return 0
            
        cache_dir = self.base_dir
        if not cache_dir.exists():
            return 0
            
        expired_time = time.time() - (expire_days * 24 * 60 * 60)
        deleted_count = 0
        
        for file in cache_dir.glob('*.html'):
            try:
                if file.stat().st_mtime < expired_time:
                    file.unlink()
                    deleted_count += 1
            except Exception as e:
                self.logger.error(f"キャッシュの削除に失敗しました: {file} - {e}")
        
        return deleted_count
