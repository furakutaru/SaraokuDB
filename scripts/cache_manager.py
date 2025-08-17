"""
キャッシュ管理モジュール

スクレイピング結果を日時ベースのフォルダに保存・管理するためのユーティリティ
"""

from pathlib import Path
from datetime import datetime
import json
import re
from typing import Dict, List, Optional
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

class CacheManager:
    """スクレイピング結果のキャッシュを管理するクラス
    
    1回のスクレイピングセッションで取得したデータを、日時ベースのフォルダにまとめて保存します。
    例：
    cache/
    └── 202508122100/          # スクレイピング実行日時 (YYYYMMDDHHMM)
        ├── list.html          # 一覧ページ
        ├── metadata.json      # スクレイピングのメタデータ
        └── details/           # 詳細ページ
            ├── サトノダイヤモンド_12345.html
            └── キタサンブラック_67890.html
    """
    
    def __init__(self, base_dir: str = "cache"):
        """キャッシュマネージャーの初期化
        
        Args:
            base_dir: キャッシュのベースディレクトリパス
        """
        self.base_dir = Path(base_dir)
        self.current_session: Optional[Path] = None
        self.metadata: Dict = {}
        
    def start_new_session(self, session_id: str = None) -> str:
        """新しいスクレイピングセッションを開始
        
        Args:
            session_id: セッションID（未指定の場合は現在時刻から生成）
            
        Returns:
            str: セッションID
        """
        if session_id is None:
            session_id = datetime.now().strftime("%Y%m%d%H%M")
            
        self.current_session = self.base_dir / session_id
        self.current_session.mkdir(parents=True, exist_ok=True)
        (self.current_session / "details").mkdir(exist_ok=True)
        
        # メタデータの初期化
        self.metadata = {
            "session_id": session_id,
            "start_time": datetime.now().isoformat(),
            "list_page": "list.html",
            "details": []
        }
        self._save_metadata()
        
        logger.info(f"新しいセッションを開始しました: {session_id}")
        return session_id
        
    def save_list_page(self, content: str) -> str:
        """一覧ページを保存
        
        Args:
            content: 保存するHTMLコンテンツ
            
        Returns:
            str: 保存されたファイルのパス
            
        Raises:
            RuntimeError: セッションが開始されていない場合
        """
        if not self.current_session:
            self.start_new_session()
            
        list_path = self.current_session / "list.html"
        list_path.write_text(content, encoding='utf-8')
        
        # メタデータを更新
        self.metadata["list_page"] = str(list_path.name)
        self._save_metadata()
        
        logger.debug(f"一覧ページを保存しました: {list_path}")
        return str(list_path)
        
    def get_list_page(self, session_id: str = None) -> Optional[str]:
        """保存された一覧ページの内容を取得
        
        Args:
            session_id: 取得するセッションID（Noneの場合は現在のセッション）
            
        Returns:
            Optional[str]: 一覧ページの内容。見つからない場合はNone
        """
        if session_id is None:
            if not self.current_session:
                return None
            session_dir = self.current_session
        else:
            session_dir = self.base_dir / session_id
            
        # メタデータを読み込む
        metadata_path = session_dir / "metadata.json"
        if not metadata_path.exists():
            return None
            
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            list_page = metadata.get('list_page', 'list.html')
            list_path = session_dir / list_page
            
            if list_path.exists():
                return list_path.read_text(encoding='utf-8')
                
        except Exception as e:
            logger.error(f"一覧ページの読み込み中にエラーが発生しました: {e}")
            
        return None
        
    def save_detail_page(self, content: str, horse_name: str, item_id: str) -> str:
        """詳細ページを保存
        
        Args:
            content: 保存するHTMLコンテンツ
            horse_name: 互換性のための引数（使用しない）
            item_id: アイテムID（ファイル名に使用）
            
        Returns:
            str: 保存されたファイルのパス
            
        Raises:
            RuntimeError: セッションが開始されていない場合
        """
        if not self.current_session:
            raise RuntimeError("セッションが開始されていません。start_new_session() を呼び出してください。")
            
        # 詳細ページ用ディレクトリがなければ作成
        details_dir = self.current_session / "details"
        details_dir.mkdir(exist_ok=True)
        
        # ファイル名はIDのみを使用
        filename = f"{item_id}.html"
        detail_path = details_dir / filename
        
        # ファイルを保存
        detail_path.write_text(content, encoding='utf-8')
        
        # メタデータを更新
        self.metadata["details"].append({
            "id": item_id,
            "filename": f"details/{filename}",
            "saved_at": datetime.now().isoformat()
        })
        self._save_metadata()
        
        logger.debug(f"詳細ページを保存しました: {detail_path}")
        return str(detail_path)
        
    def _save_metadata(self):
        """メタデータを保存"""
        if not self.current_session:
            return
            
        metadata_path = self.current_session / "metadata.json"
        self.metadata["last_updated"] = datetime.now().isoformat()
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            
    def get_session_list(self) -> List[Dict]:
        """保存済みのセッション一覧を取得
        
        Returns:
            List[Dict]: セッション情報のリスト
        """
        sessions = []
        for session_dir in sorted(self.base_dir.glob("*/"), reverse=True):
            if not session_dir.is_dir():
                continue
                
            metadata_path = session_dir / "metadata.json"
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        sessions.append({
                            "id": session_dir.name,
                            "path": str(session_dir),
                            "details_count": len(metadata.get("details", [])),
                            "start_time": metadata.get("start_time")
                        })
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"メタデータの読み込みに失敗しました: {session_dir} - {e}")
                    continue
        return sessions
        
    def get_latest_session(self) -> Optional[Dict]:
        """最新のセッション情報を取得
        
        Returns:
            Optional[Dict]: 最新のセッション情報、見つからない場合はNone
        """
        sessions = self.get_session_list()
        return sessions[0] if sessions else None
        
    def load_session(self, session_id: str) -> bool:
        """既存のセッションを読み込む
        
        Args:
            session_id: 読み込むセッションID
            
        Returns:
            bool: 読み込みに成功したかどうか
        """
        session_dir = self.base_dir / session_id
        metadata_path = session_dir / "metadata.json"
        
        if not metadata_path.exists():
            logger.warning(f"セッションが見つかりません: {session_id}")
            return False
            
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
                self.current_session = session_dir
                logger.info(f"セッションを読み込みました: {session_id}")
                return True
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"セッションの読み込みに失敗しました: {session_id} - {e}")
            return False
