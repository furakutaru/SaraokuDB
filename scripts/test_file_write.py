#!/usr/bin/env python3
"""
ファイル書き込みのテストスクリプト
"""
import os
import sys
import logging
from pathlib import Path

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def test_file_write():
    """ファイル書き込みのテストを実行"""
    try:
        # テスト用ディレクトリ
        test_dir = Path("test_output")
        test_dir.mkdir(exist_ok=True)
        
        # テストファイルのパス
        test_file = test_dir / "test.txt"
        
        # ファイルに書き込み
        test_content = "This is a test file."
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # ファイルの存在確認
        if test_file.exists():
            logger.info(f"✅ ファイルの作成に成功しました: {test_file}")
            logger.info(f"    サイズ: {os.path.getsize(test_file)} バイト")
            
            # ファイルの読み込み確認
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if content == test_content:
                    logger.info("✅ ファイルの読み書きが正常に動作しています")
                else:
                    logger.error(f"❌ ファイルの内容が一致しません。期待: '{test_content}', 実際: '{content}'")
            
            # ファイルを削除
            test_file.unlink()
            logger.info(f"テストファイルを削除しました: {test_file}")
        else:
            logger.error(f"❌ ファイルの作成に失敗しました: {test_file}")
        
        # カレントディレクトリの権限確認
        cwd = Path.cwd()
        logger.info(f"現在の作業ディレクトリ: {cwd}")
        logger.info(f"読み取り可能: {os.access(cwd, os.R_OK)}")
        logger.info(f"書き込み可能: {os.access(cwd, os.W_OK)}")
        logger.info(f"実行可能: {os.access(cwd, os.X_OK)}")
        
        # テスト用ディレクトリの権限確認
        logger.info(f"テストディレクトリ: {test_dir}")
        logger.info(f"存在: {test_dir.exists()}")
        logger.info(f"読み取り可能: {os.access(test_dir, os.R_OK)}")
        logger.info(f"書き込み可能: {os.access(test_dir, os.W_OK)}")
        logger.info(f"実行可能: {os.access(test_dir, os.X_OK)}")
        
        # テスト用ディレクトリを削除
        test_dir.rmdir()
        logger.info(f"テストディレクトリを削除しました: {test_dir}")
        
        return 0
        
    except Exception as e:
        logger.error(f"テスト中にエラーが発生しました: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(test_file_write())
