#!/usr/bin/env python3
"""
データクリアスクリプト
開発途中で発生した意図していない状態のデータをクリアし、
クリーンな状態からスクレイピングを再実行するためのスクリプト
"""

import os
import json
import shutil
from pathlib import Path

def clear_data_files():
    """主要なデータファイルをクリアする"""

    # バックアップディレクトリ
    backup_dir = Path("data_backups")
    backup_dir.mkdir(exist_ok=True)
    timestamp = "20250926_192000"

    # クリアするファイルのリスト
    files_to_clear = [
        # ルートディレクトリ
        "extracted_horses.json",
        "scraped_horses.json",
        "scraping_results.json",
        "horse_name_analysis.json",
        "price_extraction_results.json",
        "test_output.json",
        "test_scraping_result.json",
        "output.json",
        "auction_data_20250830_122409.json",
        "auction_data_20250830_122756.json",
        "auction_data_20250830_122856.json",
        "auction_data_20250830_123033.json",
        "auction_data_20250830_123135.json",
        "auction_data_20250830_124907.json",

        # バックエンドデータ
        "backend/data/horses.json",
        "backend/data/auction_history.json",
        "backend/data/horses.db",

        # フロントエンドデータ
        "frontend/public/data/horses.json",
        "frontend/public/data/horses_combined.json",
        "frontend/public/data/horses_history.json",
    ]

    # バックアップを作成してからクリア
    for file_path in files_to_clear:
        if os.path.exists(file_path):
            # バックアップファイル名を作成
            backup_path = backup_dir / f"{Path(file_path).name}.backup_{timestamp}"
            print(f"Backing up {file_path} -> {backup_path}")
            shutil.copy2(file_path, backup_path)

            # ファイルをクリア（空のJSONオブジェクトで上書き）
            if file_path.endswith('.json'):
                print(f"Clearing {file_path}")
                with open(file_path, 'w', encoding='utf-8') as f:
                    if 'horses' in file_path or 'auction_history' in file_path:
                        # 馬データとオークション履歴は空の配列で初期化
                        json.dump([], f, ensure_ascii=False, indent=2)
                    else:
                        # その他のJSONファイルは空のオブジェクトで初期化
                        json.dump({}, f, ensure_ascii=False, indent=2)
            elif file_path.endswith('.db'):
                print(f"Removing database {file_path}")
                os.remove(file_path)

    print(f"Data clearing completed. Backups saved in {backup_dir}")

def clear_cache_directories():
    """キャッシュディレクトリをクリアする"""

    cache_dirs = [
        "cache",
        "html_cache",
        "test_cache_output",
        "test_simple_cache"
    ]

    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            print(f"Clearing cache directory: {cache_dir}")
            shutil.rmtree(cache_dir)
            os.makedirs(cache_dir)
            print(f"Recreated empty cache directory: {cache_dir}")

if __name__ == "__main__":
    print("Starting data clearing process...")
    clear_data_files()
    clear_cache_directories()
    print("Data clearing completed successfully!")
    print("You can now run the scraping scripts to regenerate clean data.")
