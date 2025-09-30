#!/usr/bin/env python3
"""
シンプルなキャッシュ機能のテスト
"""
import os
import sys
import logging
import hashlib
from pathlib import Path

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

class SimpleCache:
    """シンプルなキャッシュ実装"""
    
    def __init__(self, cache_dir: str = "simple_cache"):
        """初期化"""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"キャッシュディレクトリ: {self.cache_dir.absolute()}")
    
    def get(self, key: str) -> str:
        """キャッシュから値を取得"""
        cache_file = self.cache_dir / f"{key}.cache"
        if not cache_file.exists():
            return None
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"キャッシュの読み込みに失敗しました: {e}")
            return None
    
    def set(self, key: str, value: str) -> bool:
        """キャッシュに値を保存"""
        try:
            cache_file = self.cache_dir / f"{key}.cache"
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(value)
            logger.info(f"キャッシュを保存しました: {cache_file.name} ({len(value)} バイト)")
            return True
        except Exception as e:
            logger.error(f"キャッシュの保存に失敗しました: {e}")
            return False

def test_simple_cache():
    """シンプルなキャッシュのテストを実行"""
    try:
        logger.info("===== シンプルキャッシュテスト開始 =====")
        
        # テスト用のキャッシュディレクトリ
        test_dir = "test_simple_cache"
        
        # 既存のテストディレクトリがあれば削除
        if os.path.exists(test_dir):
            import shutil
            shutil.rmtree(test_dir)
        
        # キャッシュを初期化
        cache = SimpleCache(test_dir)
        
        # テストデータ
        test_key = "test_key"
        test_data = "This is a test data"
        
        # 1. キャッシュに保存
        logger.info("1. キャッシュにデータを保存中...")
        cache.set(test_key, test_data)
        
        # 2. キャッシュから読み込み
        logger.info("2. キャッシュからデータを読み込み中...")
        cached_data = cache.get(test_key)
        
        # 結果を検証
        if cached_data == test_data:
            logger.info("✅ テスト成功: キャッシュの保存と読み込みに成功しました")
        else:
            logger.error(f"❌ テスト失敗: 期待値='{test_data}', 実際の値='{cached_data}'")
        
        # キャッシュファイルの存在を確認
        cache_file = Path(test_dir) / f"{test_key}.cache"
        if cache_file.exists():
            logger.info(f"✅ キャッシュファイルが存在します: {cache_file}")
            logger.info(f"    サイズ: {os.path.getsize(cache_file)} バイト")
        else:
            logger.error(f"❌ キャッシュファイルが存在しません: {cache_file}")
        
        logger.info("===== シンプルキャッシュテスト完了 =====")
        return 0
        
    except Exception as e:
        logger.error(f"テスト中にエラーが発生しました: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(test_simple_cache())
