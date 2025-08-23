#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
シンプルな設定テストスクリプト
"""

import sys
import os
import logging
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def print_section(title):
    """セクション見出しを表示する"""
    print(f"\n{'='*50}")
    print(f"{title:^50}")
    print(f"{'='*50}")

def test_config_loading():
    """設定の読み込みをテストする"""
    try:
        print_section("設定システムのテストを開始します")
        
        # 設定モジュールを直接インポート
        logger.info("設定モジュールをインポート中...")
        from scripts.core.config import config
        logger.info("設定モジュールのインポートに成功しました")
        
        # 設定値の表示
        print_section("設定値の確認")
        logger.info("データベース設定: %s", config.database.__dict__)
        logger.info("ロギング設定: %s", config.logging.__dict__)
        logger.info("スクレイパー設定: %s", config.scraper.__dict__)
        logger.info("キャッシュ設定: %s", config.cache.__dict__)
        logger.info("出力設定: %s", config.output.__dict__)
        
        # ディレクトリの存在確認
        print_section("ディレクトリの確認")
        for name, path in [
            ("キャッシュディレクトリ", config.cache.cache_dir),
            ("出力ディレクトリ", config.output.output_dir),
            ("ログディレクトリ", config.logging.file.parent)
        ]:
            exists = "存在します" if path.exists() else "存在しません"
            logger.info("%s: %s (%s)", name, path, exists)
        
        # ディレクトリ作成テスト
        print_section("ディレクトリ作成テスト")
        test_dir = Path("test_directory")
        try:
            test_dir.mkdir(exist_ok=True)
            logger.info("テストディレクトリの作成に成功しました: %s", test_dir)
            test_dir.rmdir()
            logger.info("テストディレクトリを削除しました")
        except Exception as e:
            logger.error("ディレクトリ操作中にエラーが発生しました: %s", e)
        
        print_section("テストが正常に完了しました")
        return True
        
    except Exception as e:
        logger.error("テスト中にエラーが発生しました: %s", e, exc_info=True)
        return False

if __name__ == "__main__":
    success = test_config_loading()
    sys.exit(0 if success else 1)
