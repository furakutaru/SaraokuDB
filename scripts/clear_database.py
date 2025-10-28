#!/usr/bin/env python3
"""
データベースの全データを削除するスクリプト

このスクリプトは、データベース内の全テーブルのデータを削除します。
本番環境では十分に注意して使用してください。
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# プロジェクトのルートディレクトリを追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 環境変数の読み込み
load_dotenv(os.path.join(project_root, '.env'))

def get_db_engine():
    """データベースエンジンを取得する"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL 環境変数が設定されていません")
    return create_engine(DATABASE_URL)

def clear_database():
    """データベースの全データを削除する"""
    engine = get_db_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("警告: この操作はデータベースの全データを削除します。")
        print("重要なデータは必ずバックアップを取ってから実行してください。")
        confirm = input("本当に続行しますか？ (y/N): ")
        
        if confirm.lower() != 'y':
            print("操作をキャンセルしました。")
            return
        
        print("テーブルデータを削除しています...")
        
        # 外部キー制約を解除するために、horsesテーブルの外部キーをNULLに設定
        print("外部キー制約を解除しています...")
        session.execute(text("UPDATE horses SET latest_auction_id = NULL;"))
        
        # 外部キー制約を持つテーブルから先に削除
        print("オークション履歴を削除しています...")
        session.execute(text("DELETE FROM auction_histories;"))
        
        # 最後にhorsesテーブルを削除
        print("馬データを削除しています...")
        session.execute(text("DELETE FROM horses;"))
        
        # 変更をコミット
        session.commit()
        print("データベースの全データを削除しました。")
        
    except Exception as e:
        session.rollback()
        print(f"エラーが発生しました: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    try:
        clear_database()
    except Exception as e:
        print(f"エラー: {str(e)}")
        sys.exit(1)
