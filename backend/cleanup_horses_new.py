import os
import sys
import json
from sqlalchemy import create_engine, desc, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# データベースモデルをインポート
from database.models import Horse, engine, SessionLocal

def cleanup_old_horses():
    """最新の5頭を除くすべての馬を削除する"""
    db = SessionLocal()
    try:
        # 最新の5頭のIDを取得（idの降順でソート）
        latest_horses = db.query(Horse.id)\
            .order_by(desc(Horse.id))\
            .limit(5)\
            .all()
        
        latest_ids = [h[0] for h in latest_horses if h[0] is not None]
        
        if not latest_ids:
            print("削除する馬のデータはありません。")
            return
            
        # 最新の5頭以外の馬を削除
        result = db.query(Horse)\
            .filter(Horse.id.notin_(latest_ids))\
            .delete(synchronize_session=False)
        
        db.commit()
        print(f"{result}件の古い馬のデータを削除しました。")
        print(f"最新の馬ID: {', '.join(map(str, latest_ids))}")
        
    except Exception as e:
        db.rollback()
        print(f"エラーが発生しました: {e}")
        raise
    finally:
        db.close()

def check_database():
    """データベースの接続とテーブルを確認する"""
    db = SessionLocal()
    try:
        # テーブルが存在するか確認
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='horses'"))
        table_exists = result.fetchone() is not None
        
        if not table_exists:
            print("エラー: horses テーブルが存在しません。")
            return False
            
        # 馬の総数を確認
        count = db.query(Horse).count()
        print(f"現在の馬の総数: {count}頭")
        
        # 最新の5頭を表示
        latest_horses = db.query(Horse.id, Horse.name)\
            .order_by(desc(Horse.id))\
            .limit(5)\
            .all()
            
        print("\n最新の5頭の馬:")
        for i, (horse_id, name) in enumerate(latest_horses, 1):
            print(f"{i}. {name} (ID: {horse_id})")
            
        return True
        
    except Exception as e:
        print(f"データベースの確認中にエラーが発生しました: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=== 馬データベース管理ツール ===")
    print("1. 古い馬のデータを削除（最新5頭を除く）")
    print("2. データベースの状態を確認")
    print("3. 終了")
    
    choice = input("\n実行する操作を選択してください (1-3): ")
    
    if choice == "1":
        print("\n=== 古い馬のデータを削除します ===")
        if check_database():
            confirm = input("\n本当に最新の5頭以外の馬を削除しますか？ (y/N): ")
            if confirm.lower() == 'y':
                cleanup_old_horses()
    elif choice == "2":
        print("\n=== データベースの状態を確認します ===")
        check_database()
    else:
        print("終了します。")
