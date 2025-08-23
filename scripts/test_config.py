#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
設定システムのテストスクリプト

このスクリプトは、新しい設定システムが既存のコードと正しく連携することを確認するためのものです。
"""

import sys
import os
import logging
import traceback
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print(f"Python path: {sys.path}")

# 新しい設定システムをインポート
try:
    print("Configモジュールをインポート中...")
    from scripts.core.config import config
    print("Configモジュールのインポートに成功しました")
    
    print("Loggerモジュールをインポート中...")
    from scripts.core.utils.logger import get_logger
    print("Loggerモジュールのインポートに成功しました")
except ImportError as e:
    print(f"モジュールのインポート中にエラーが発生しました: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    traceback.print_exc()
    sys.exit(1)

# ロガーの設定
logger = get_logger(__name__)

def test_config_loading():
    """設定の読み込みをテストする"""
    try:
        # 設定値の表示
        print("=== 設定値の確認 ===")
        print(f"データベース設定: {config.database.__dict__}")
        print(f"ロギング設定: {config.logging.__dict__}")
        print(f"スクレイパー設定: {config.scraper.__dict__}")
        print(f"キャッシュ設定: {config.cache.__dict__}")
        print(f"出力設定: {config.output.__dict__}")
        
        # ログ出力のテスト
        logger.debug("これはデバッグメッセージです")
        logger.info("これは情報メッセージです")
        logger.warning("これは警告メッセージです")
        logger.error("これはエラーメッセージです")
        
        # ディレクトリの存在確認
        print("\n=== ディレクトリの確認 ===")
        for name, path in [
            ("キャッシュディレクトリ", config.cache.cache_dir),
            ("出力ディレクトリ", config.output.output_dir),
            ("ログディレクトリ", config.logging.file.parent)
        ]:
            exists = "存在します" if path.exists() else "存在しません"
            print(f"{name}: {path} ({exists})")
        
        return True
    except Exception as e:
        logger.exception("設定のテスト中にエラーが発生しました")
        return False

if __name__ == "__main__":
    print("設定システムのテストを開始します...\n")
    if test_config_loading():
        print("\n✅ 設定システムのテストが正常に完了しました")
    else:
        print("\n❌ 設定システムのテストに失敗しました")
        sys.exit(1)
