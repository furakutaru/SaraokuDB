from sqlalchemy import create_engine
from database.models import Base, Horse, DATABASE_URL
import os

# データベースディレクトリが存在するか確認し、なければ作成
db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

# データベースエンジンを作成
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# テーブルを作成
print("データベーステーブルを作成しています...")
Base.metadata.create_all(bind=engine)
print("データベースの初期化が完了しました。")
print(f"データベースの場所: {os.path.join(db_dir, 'horses.db')}")
