from sqlalchemy import Column, Integer, String, Float, Text, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Horse(Base):
    __tablename__ = 'horses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)  # 馬名（カタカナのみ）
    sex = Column(String(10))  # 性別（牡、牝、セ）
    age = Column(Integer)  # 年齢（例: 3）
    sire = Column(String(100))  # 父
    dam = Column(String(100))  # 母
    dam_sire = Column(String(100))  # 母父
    race_record = Column(String(200))  # 通算成績（例: 2戦0勝［0-0-0-2］）
    weight = Column(Integer)  # 最終出走馬体重
    total_prize_start = Column(Float)  # 出品時の地方賞金（万円）
    total_prize_latest = Column(Float)  # 最新の地方賞金（万円、netkeibaより取得）
    sold_price = Column(Integer)  # 落札価格（円）
    auction_date = Column(String(20))  # 開催日（YYYY-MM-DD）
    seller = Column(String(200))  # 販売申込者
    disease_tags = Column(Text)  # 疾病カテゴリ（カンマ区切り）
    comment = Column(Text)  # 本馬についてのコメント全文
    netkeiba_url = Column(String(500))  # netkeibaの個体URL
    image_url = Column(String(500))  # 馬画像URL（将来的に取得）
    primary_image = Column(String(500))  # 馬体写真1枚目のURL
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# データベース設定
DATABASE_URL = "sqlite:///./data/horses.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 