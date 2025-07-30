import os
import shutil
from datetime import datetime
from pathlib import Path

def backup_database():
    # バックアップディレクトリのパス
    backup_dir = Path("data/backups")
    backup_dir.mkdir(exist_ok=True, parents=True)
    
    # 現在の日時をバックアップファイル名に使用
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"horses_backup_{timestamp}.db"
    
    # データベースファイルをバックアップ
    source = Path("data/horses.db")
    if source.exists():
        shutil.copy2(source, backup_file)
        print(f"データベースをバックアップしました: {backup_file}")
    else:
        print("警告: バックアップ元のデータベースファイルが見つかりませんでした。")

if __name__ == "__main__":
    backup_database()
