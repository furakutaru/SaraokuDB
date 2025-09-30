import os
import sys
import sqlite3
from datetime import datetime

def backup_database(db_path):
    """データベースのバックアップを作成"""
    backup_dir = os.path.join(os.path.dirname(db_path), '..', 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'horses_backup_{timestamp}.db')
    
    # データベースファイルをコピー
    with open(db_path, 'rb') as src, open(backup_file, 'wb') as dst:
        dst.write(src.read())
    
    print(f"データベースのバックアップを作成しました: {backup_file}")
    return backup_file

def add_auction_url_column():
    """horsesテーブルにauction_urlカラムを追加する"""
    try:
        print("=== マイグレーションを開始します ===")
        
        # データベースファイルのパス
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'horses.db')
        
        # データベースファイルが存在するか確認
        if not os.path.exists(db_path):
            print(f"エラー: データベースファイルが見つかりません: {db_path}")
            return False
            
        # バックアップを作成
        print("データベースのバックアップを作成中...")
        backup_file = backup_database(db_path)
        
        # データベースに接続
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # カラムが既に存在するか確認
            cursor.execute("PRAGMA table_info(horses)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'auction_url' not in columns:
                # auction_urlカラムを追加
                print("horsesテーブルにauction_urlカラムを追加しています...")
                cursor.execute("ALTER TABLE horses ADD COLUMN auction_url TEXT")
                conn.commit()
                print("auction_urlカラムを追加しました")
            else:
                print("auction_urlカラムは既に存在します")
                
            print("\n=== マイグレーションが正常に完了しました ===")
            print(f"バックアップファイル: {backup_file}")
            return True
            
        except Exception as e:
            print(f"\n=== エラーが発生しました ===\n{str(e)}\n")
            print("バックアップファイルから復元する場合は以下のコマンドを実行してください:")
            print(f"cp {backup_file} {db_path}")
            return False
            
        finally:
            conn.close()
            
    except Exception as e:
        print(f"\n=== 予期せぬエラーが発生しました ===\n{str(e)}\n")
        return False

if __name__ == "__main__":
    add_auction_url_column()
