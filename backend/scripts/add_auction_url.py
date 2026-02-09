import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# プロジェクトのルートをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.models import engine

def backup_database():
    """データベースのバックアップを作成"""
    import shutil
    from datetime import datetime
    
    # バックアップディレクトリがなければ作成
    backup_dir = os.path.join(project_root, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    # バックアップファイル名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'horses_backup_{timestamp}.db')
    
    # データベースファイルをコピー
    db_file = os.path.join(project_root, 'backend', 'data', 'horses.db')
    
    # データベースファイルが存在するか確認
    if not os.path.exists(db_file):
        print(f"エラー: データベースファイルが見つかりません: {db_file}")
        return None
        
    shutil.copy2(db_file, backup_file)
    print(f"データベースのバックアップを作成しました: {backup_file}")
    return backup_file

def add_auction_url_column():
    """horsesテーブルにauction_urlカラムを追加する"""
    try:
        print("=== マイグレーションを開始します ===")
        
        # バックアップを作成
        print("データベースのバックアップを作成中...")
        backup_file = backup_database()
        if backup_file is None:
            print("バックアップの作成に失敗しました。処理を中止します。")
            return
        
        with engine.connect() as conn:
            # トランザクションを開始
            with conn.begin():
                # カラムが既に存在するか確認
                result = conn.execute(
                    text("""
                    SELECT COUNT(*) as count 
                    FROM pragma_table_info('horses') 
                    WHERE name = 'auction_url'
                    """)
                ).fetchone()
                
                if result and result[0] == 0:
                    # auction_urlカラムを追加
                    print("horsesテーブルにauction_urlカラムを追加しています...")
                    conn.execute(text("""
                        ALTER TABLE horses 
                        ADD COLUMN auction_url TEXT
                    
```python
                    """))
                    print("auction_urlカラムを追加しました")
                else:
                    print("auction_urlカラムは既に存在します")
                    
        print("\n=== マイグレーションが正常に完了しました ===")
        print(f"バックアップファイル: {backup_file}")
        
    except Exception as e:
        print(f"\n=== エラーが発生しました ===\n{str(e)}\n")
        if 'backup_file' in locals() and backup_file:
            print("バックアップファイルから復元する場合は以下のコマンドを実行してください:")
            print(f"cp {backup_file} {os.path.join(project_root, 'backend', 'data', 'horses.db')}")
        sys.exit(1)

if __name__ == "__main__":
    add_auction_url_column()
