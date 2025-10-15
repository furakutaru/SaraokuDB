#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from scripts.improved_scraper import CacheManager, ScraperConfig

def test_cache():
    print("=== キャッシュのテストを開始します ===")
    
    # テスト用の設定を作成
    config = ScraperConfig(use_cache=True, cache_dir='test_cache')
    
    # キャッシュマネージャーを初期化
    cache_manager = CacheManager(config.cache_dir)
    
    # テスト用のURLとコンテンツ
    test_url = "https://example.com/test"
    test_content = "<html><body>テストコンテンツ</body></html>"
    
    # キャッシュに保存
    print(f"キャッシュに保存: {test_url}")
    cache_manager.set(test_url, test_content)
    
    # キャッシュから読み込み
    print("キャッシュから読み込み中...")
    cached_content = cache_manager.get(test_url)
    
    if cached_content == test_content:
        print("✅ キャッシュの保存と読み込みが正常に動作しています")
    else:
        print("❌ キャッシュの保存または読み込みに問題があります")
    
    # キャッシュファイルのパスを表示
    cache_path = cache_manager._get_cache_path(test_url)
    print(f"キャッシュファイルのパス: {cache_path}")
    print(f"キャッシュファイルの存在確認: {'あり' if cache_path.exists() else 'なし'}")
    
    # キャッシュディレクトリの内容を表示
    print("\nキャッシュディレクトリの内容:")
    for f in Path('test_cache').rglob('*'):
        if f.is_file():
            print(f"- {f.relative_to('test_cache')} ({f.stat().st_size} バイト)")
    
    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    test_cache()
