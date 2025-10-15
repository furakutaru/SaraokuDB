"""
HTMLキャッシュを管理するモジュール

キャッシュの保存先構造:
cache/
  YYYYMMDD/          # 日付ごとのディレクトリ
    index.html       # リストページ
    details/         # 詳細ページ用ディレクトリ
      [horse_id].html  # 馬ごとの詳細ページ
"""
import hashlib
import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from urllib.parse import urlparse, parse_qs

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
    
    def _get_cache_path(self, url: str) -> Tuple[Path, str]:
        """
        URLからキャッシュファイルのパスを生成します。
        
        Args:
            url: キャッシュするURL
            
        Returns:
            Tuple[Path, str]: (キャッシュファイルのパス, ファイル名)
        """
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        # 日付ディレクトリの作成 (YYYYMMDD形式)
        date_dir = datetime.now().strftime('%Y%m%d')
        
        # リストページの場合
        if 'auction.keiba.rakuten.co.jp' in url and not any(p.isdigit() for p in path_parts):
            cache_dir = self.base_dir / date_dir
            cache_dir.mkdir(parents=True, exist_ok=True)
            return cache_dir / 'index.html', 'index.html'
            
        # 詳細ページの場合 (URLに数字が含まれる)
        if any(p.isdigit() for p in path_parts):
            # 馬IDを抽出 (URLの最後の数値部分)
            horse_id = next((p for p in reversed(path_parts) if p.isdigit()), None)
            if horse_id:
                details_dir = self.base_dir / date_dir / 'details'
                details_dir.mkdir(parents=True, exist_ok=True)
                return details_dir / f"{horse_id}.html", f"{horse_id}.html"
        
        # その他のURLはハッシュ化して保存
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        cache_dir = self.base_dir / date_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / f"{url_hash}.html", f"{url_hash}.html"
    
    def load_html(self, url: str) -> Optional[str]:
        """
        URLに対応するキャッシュされたHTMLを読み込みます。
        
        Args:
            url: 読み込むHTMLのURL
            
        Returns:
            str: キャッシュされたHTMLコンテンツ。見つからない場合はNone
        """
        try:
            # まず正確なURLで検索
            cache_path, _ = self._get_cache_path(url)
            if cache_path.exists():
                return self._read_cached_file(cache_path)
                
            # 見つからない場合は、日付ディレクトリを検索
            if 'auction.keiba.rakuten.co.jp' in url:
                date_dir = datetime.now().strftime('%Y%m%d')
                cache_dir = self.base_dir / date_dir
                
                # リストページの場合
                if not any(p.isdigit() for p in urlparse(url).path.strip('/').split('/')):
                    index_path = cache_dir / 'index.html'
                    if index_path.exists():
                        return self._read_cached_file(index_path)
                
                # 詳細ページの場合
                else:
                    # 馬IDを抽出して検索
                    horse_id = next((p for p in reversed(urlparse(url).path.strip('/').split('/')) if p.isdigit()), None)
                    if horse_id:
                        detail_path = cache_dir / 'details' / f"{horse_id}.html"
                        if detail_path.exists():
                            return self._read_cached_file(detail_path)
                            
        except Exception as e:
            self.logger.error(f"キャッシュの読み込み中にエラーが発生しました: {e}", exc_info=True)
            
        return None
        
    def _read_cached_file(self, path: Path) -> Optional[str]:
        """キャッシュファイルを読み込み、メタデータを除いたコンテンツを返します
        
        Returns:
            読み込んだコンテンツ（前後の不要な空白や改行を削除）
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # メタデータを除去
            if content.startswith('<!--\nCACHE_METADATA='):
                meta_end = content.find('\n-->\n')
                if meta_end != -1:
                    content = content[meta_end + 5:]  # メタデータの後の改行も含めてスキップ
            
            # 前後の不要な空白や改行を削除
            if content:
                content = content.strip()
                # 前後のクォーテーションや括弧を削除（コメントデータ用）
                content = re.sub(r'^[\s\{\}\[\]"\'\\,]+', '', content)
                content = re.sub(r'[\s\{\}\[\]"\'\\,]+$', '', content)
            
            return content if content else None
            
        except Exception as e:
            self.logger.error(f"キャッシュファイルの読み込みに失敗しました ({path}): {e}", exc_info=True)
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
            cache_path, filename = self._get_cache_path(url)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            # メタデータを保存
            metadata = {
                'url': url,
                'saved_at': datetime.now().isoformat(),
                'filename': filename
            }
            
            # HTMLにメタデータを埋め込む
            content_with_meta = f"""<!--
CACHE_METADATA={json.dumps(metadata, ensure_ascii=False)}
-->
{content}"""
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(content_with_meta)
                
            self.logger.debug(f"キャッシュを保存しました: {cache_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"キャッシュの保存に失敗しました: {e}", exc_info=True)
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
    
    def get(self, key: str) -> Optional[str]:
        """
        キャッシュから値を取得します。
        
        Args:
            key: 取得するキーまたはURL
            
        Returns:
            str: キャッシュされた値、またはNone
        """
        # URLの場合はHTMLキャッシュとして扱う
        if key.startswith('http'):
            return self.load_html(key)
        else:
            # 一般のキーと値のキャッシュ
            return self._get_key_value(key)
    
    def set(self, key: str, value: str, expire_seconds: int = None) -> None:
        """
        キーと値をキャッシュに保存します。
        
        Args:
            key: キャッシュキー
            value: キャッシュする値
            expire_seconds: 有効期限（秒）
        """
        # URLの場合はHTMLキャッシュとして扱う
        if key.startswith('http'):
            self.save_html(key, value)
        else:
            # 一般のキーと値のキャッシュ
            self._save_key_value(key, value, expire_seconds)
    
    def _save_key_value(self, key: str, value: str, expire_seconds: int = None) -> None:
        """
        キーと値をメモリキャッシュに保存します。
        
        Args:
            key: キャッシュキー
            value: キャッシュする値
            expire_seconds: 有効期限（秒）
        """
        expire_time = None
        if expire_seconds:
            expire_time = time.time() + expire_seconds
        
        self.cache[key] = {
            'value': value,
            'expire_time': expire_time
        }
        
        # キャッシュインデックスを保存
        self._save_cache_index()
    
    def _get_key_value(self, key: str) -> Optional[str]:
        """
        メモリキャッシュから値を取得します。
        
        Args:
            key: キャッシュキー
            
        Returns:
            str: キャッシュされた値、またはNone
        """
        if key not in self.cache:
            return None
        
        cached_item = self.cache[key]
        
        # 有効期限をチェック
        if cached_item.get('expire_time') and time.time() > cached_item['expire_time']:
            del self.cache[key]
            self._save_cache_index()
            return None
        
        return cached_item['value']
    
    def _save_cache_index(self) -> None:
        """キャッシュインデックスをファイルに保存します。"""
        cache_index = self.base_dir / 'cache_index.json'
        try:
            with open(cache_index, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"キャッシュインデックスの保存に失敗しました: {e}")
    
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
