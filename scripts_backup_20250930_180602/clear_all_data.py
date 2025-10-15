#!/usr/bin/env python3
"""
JSONファイルとデータベースの両方をクリアするスクリプト
"""

import os
import sys
import shutil
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# プロジェクトのルートパス
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def clear_json_data(backup=True):
    """JSONファイルをクリアする"""
    json_path = os.path.join(PROJECT_ROOT, "static-frontend", "public", "data", "horses.json")
    backup_path = os.path.join(PROJECT_ROOT, "static-frontend", "public", "data", "horses.json.bak")
    
    if not os.path.exists(json_path):
        print("✅ JSONファイルは存在しません")
        return True
    
    try:
        if backup:
            # バックアップを作成
            shutil.copy2(json_path, backup_path)
            print(f"✅ JSONファイルをバックアップしました: {backup_path}")
        
        # 空のJSONファイルを作成
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({"horses": []}, f, ensure_ascii=False, indent=2)
        
        print(f"✅ JSONファイルをクリアしました: {json_path}")
        return True
    except Exception as e:
        print(f"❌ JSONファイルのクリア中にエラーが発生しました: {str(e)}")
        return False

def clear_database(drop_all=False):
    """データベースをクリアする"""
    db_path = os.path.join(PROJECT_ROOT, "backend", "data", "horses.db")
    db_uri = f'sqlite:///{db_path}'
    
    if not os.path.exists(db_path):
        print("✅ データベースファイルは存在しません")
        return True
    
    try:
        # プロジェクトのルートをパスに追加
        sys.path.append(PROJECT_ROOT)
        
        # データベースモデルを動的にインポート
        from backend.database.models import Base, Horse, SessionLocal
        
        # エンジンを作成
        engine = create_engine(db_uri)
        
        if drop_all:
            # すべてのテーブルを削除
            Base.metadata.drop_all(engine)
            # テーブルを再作成
            Base.metadata.create_all(engine)
            print("✅ データベースのすべてのテーブルを削除して再作成しました")
        else:
            # テーブルの内容をクリア
            session = SessionLocal()
            try:
                deleted_count = session.query(Horse).delete()
                session.commit()
                print(f"✅ データベースから {deleted_count} 件の馬データを削除しました")
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
                
        return True
    except Exception as e:
        print(f"❌ データベースのクリア中にエラーが発生しました: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='JSONファイルとデータベースをクリアします')
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='バックアップを作成しません'
    )
    parser.add_argument(
        '--drop-db',
        action='store_true',
        help='データベースのテーブルをすべて削除します（完全な初期化）'
    )
    
    args = parser.parse_args()
    
    print("\n=== データクリア処理を開始します ===\n")
    
    # JSONファイルをクリア
    print("1. JSONファイルを処理中...")
    if not clear_json_data(backup=not args.no_backup):
        print("❌ JSONファイルのクリアに失敗しました")
        sys.exit(1)
    
    # データベースをクリア
    print("\n2. データベースを処理中...")
    if not clear_database(drop_all=args.drop_db):
        print("❌ データベースのクリアに失敗しました")
        sys.exit(1)
    
    print("\n✅ すべてのデータのクリアが完了しました")
    sys.exit(0)

if __name__ == "__main__":
    main()
