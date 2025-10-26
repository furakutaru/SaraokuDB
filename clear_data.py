#!/usr/bin/env python3
"""
データクリアスクリプト
開発途中で発生した意図していない状態のデータをクリアし、
クリーンな状態からスクレイピングを再実行するためのスクリプト
"""

import os
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def get_db_connection():
    """データベース接続を取得する"""
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("エラー: DATABASE_URL が設定されていません。.env ファイルを確認してください。")
        sys.exit(1)
    
    engine = create_engine(DATABASE_URL)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()

def clear_database():
    """データベースのデータをクリアする"""
    print("\n=== データベースのクリアを開始します ===")
    
    # 確認
    confirm = input("データベースの全データを削除します。よろしいですか？ (y/n): ")
    if confirm.lower() not in ['y', 'yes']:
        print("データベースのクリアをキャンセルしました。")
        return
    
    db = get_db_connection()
    try:
        # 外部キー制約を無効にせずに、CASCADE を使用してテーブルを削除
        # 外部キー制約を持つテーブルから順に削除
        tables = [
            'auction_histories',  # 外部キー制約を持つテーブルを先に削除
            'horses',
            # 他に関連テーブルがあれば追加
        ]
        
        for table in tables:
            print(f"テーブルをクリア中: {table}")
            # CASCADE を使用して外部キー制約を無視して削除
            db.execute(text(f'TRUNCATE TABLE {table} CASCADE;'))
        
        # シーケンスのリセット
        print("シーケンスをリセット中...")
        db.execute(text('ALTER SEQUENCE IF EXISTS horses_id_seq RESTART WITH 1;'))
        db.execute(text('ALTER SEQUENCE IF EXISTS auction_histories_id_seq RESTART WITH 1;'))
        
        # コミット
        db.commit()
        print("データベースのクリアが完了しました。")
        
    except Exception as e:
        db.rollback()
        print(f"エラーが発生しました: {e}")
        print("\nヒント: データベースの権限に問題がある可能性があります。")
        print("以下のいずれかの方法をお試しください：")
        print("1. データベースの管理者に連絡して、TRUNCATE 権限を付与してもらう")
        print("2. または、手動でテーブルを削除する")
        print("3. 別の方法でデータをクリアする")
        
        # 代替案として、DELETE文でデータを削除する方法を提案
        try:
            print("\n代替方法でデータを削除しますか？ (y/n): ", end='')
            if input().lower() in ['y', 'yes']:
                print("代替方法でデータを削除します...")
                for table in reversed(tables):  # 外部キー制約の関係で逆順に削除
                    print(f"テーブルからデータを削除中: {table}")
                    db.execute(text(f'DELETE FROM {table};'))
                db.commit()
                print("データの削除が完了しました。")
        except Exception as e2:
            db.rollback()
            print(f"代替方法でもエラーが発生しました: {e2}")
        
        raise
    finally:
        db.close()

def clear_data_files():
    """主要なデータファイルをクリアする"""
    print("\n=== データファイルのクリアを開始します ===")
    
    # バックアップディレクトリ
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"data_backups/backup_{timestamp}")
    backup_dir.mkdir(parents=True, exist_ok=True)

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

def main():
    print("=== データクリアツール ===")
    print("このツールは以下の操作を行います:")
    print("1. データベースの全データを削除")
    print("2. データファイルをバックアップしてクリア")
    print("3. キャッシュディレクトリをクリア\n")
    
    try:
        # データベースをクリア
        clear_database()
        
        # データファイルをクリア
        confirm = input("\nデータファイルをバックアップしてクリアしますか？ (y/n): ")
        if confirm.lower() in ['y', 'yes']:
            clear_data_files()
        
        # キャッシュをクリア
        confirm = input("\nキャッシュディレクトリをクリアしますか？ (y/n): ")
        if confirm.lower() in ['y', 'yes']:
            clear_cache_directories()
        
        print("\n=== クリーンアップが完了しました ===")
        print("以下のコマンドでスクレイピングを再開できます:")
        print("python run_scraper.py")
        
    except KeyboardInterrupt:
        print("\n処理を中断しました。")
        sys.exit(1)
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
