from alembic.config import Config
from alembic import command
import os
import sys

# プロジェクトのルートディレクトリを設定
project_root = "/Users/yum.ishii/SaraokuDB"
alembic_cfg = os.path.join(project_root, "alembic.ini")

# Pythonのパスにプロジェクトルートを追加
sys.path.insert(0, project_root)

def run_migrations():
    # 設定を読み込む
    config = Config(alembic_cfg)
    
    # マイグレーションファイルを生成
    print("Generating migration...")
    command.revision(
        config=config,
        autogenerate=True,
        message="Add is_unsold column to auction_histories table"
    )
    
    # マイグレーションを適用
    print("Applying migrations...")
    command.upgrade(config, "head")
    print("Migration completed successfully!")

if __name__ == "__main__":
    run_migrations()
