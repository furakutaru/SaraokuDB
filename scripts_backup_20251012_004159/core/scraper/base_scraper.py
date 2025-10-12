import logging
import time
from typing import Optional, Dict, Any, Tuple, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from core.utils.logger import setup_logger

class BaseScraper:
    """
    スクレイピングの基本クラス
    共通の機能を提供する
    """
    
    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None, max_retries: int = 3):
        """
        初期化
        
        Args:
            base_url: ベースURL
            headers: HTTPヘッダー
            max_retries: 最大リトライ回数
        """
        self.base_url = base_url
        self.session = self._create_session(headers, max_retries)
        self.logger = setup_logger(self.__class__.__name__)
    
    def _create_session(self, headers: Optional[Dict[str, str]] = None, max_retries: int = 3) -> requests.Session:
        """
        HTTPセッションを作成
        
        Args:
            headers: HTTPヘッダー
            max_retries: 最大リトライ回数
            
        Returns:
            requests.Session: 設定済みのセッション
        """
        session = requests.Session()
        
        # デフォルトヘッダー
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        # ヘッダーをマージ
        if headers:
            default_headers.update(headers)
        session.headers.update(default_headers)
        
        # リトライ設定
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def request_get(self, url: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> requests.Response:
        """
        GETリクエストを送信
        
        Args:
            url: リクエストURL
            params: クエリパラメータ
            **kwargs: その他の引数（requests.getにそのまま渡される）
            
        Returns:
            requests.Response: レスポンスオブジェクト
        """
        try:
            response = self.session.get(url, params=params, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"リクエストに失敗しました: {url}, エラー: {str(e)}")
            raise
    
    def request_post(self, url: str, data: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None, **kwargs) -> requests.Response:
        """
        POSTリクエストを送信
        
        Args:
            url: リクエストURL
            data: フォームデータ
            json_data: JSONデータ
            **kwargs: その他の引数（requests.postにそのまま渡される）
            
        Returns:
            requests.Response: レスポンスオブジェクト
        """
        try:
            response = self.session.post(url, data=data, json=json_data, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"リクエストに失敗しました: {url}, エラー: {str(e)}")
            raise
    
    def close(self):
        """セッションを閉じる"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
