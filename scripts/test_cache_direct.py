#!/usr/bin/env python3
"""
キャッシュマネージャーの直接テスト
"""
import os
import sys
import logging
import hashlib
from pathlib import Path
from scripts.cache_manager import CacheManager

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def test_cache_basic():
    """キャッシュの基本機能をテスト"""
    try:
        logger.info("===== キャッシュ基本テストを開始 =====")
        
        # テスト用のキャッシュディレクトリ
        test_dir = "test_cache_dir"
        
        # 既存のテストディレクトリがあれば削除
        if os.path.exists(test_dir):
            import shutil
            shutil.rmtree(test_dir)
        
        # キャッシュマネージャーを初期化
        cache = CacheManager(test_dir)
        
        # テスト用のデータ
        test_key = "test_key"
        test_data = "This is a test data"
        
        # データをキャッシュに保存
        logger.info("データをキャッシュに保存中...")
        cache.set(test_key, test_data)
        
        # キャッシュからデータを読み込み
        logger.info("キャッシュからデータを読み込み中...")
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
        
        # テスト用ディレクトリを削除
        if os.path.exists(test_dir):
            import shutil
            shutil.rmtree(test_dir)
            logger.info(f"テスト用ディレクトリを削除しました: {test_dir}")
        
        logger.info("===== キャッシュ基本テスト完了 =====")
        return 0
        
    except Exception as e:
        logger.error(f"テスト中にエラーが発生しました: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(test_cache_basic())
