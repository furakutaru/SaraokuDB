import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# .env ファイルから環境変数を読み込む
load_dotenv()

# データベースURLを取得
DATABASE_URL = os.getenv("DATABASE_URL")

# 接続の設定
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# モデルをインポート（必ずBaseのインポート後に）
from .models import Base

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
