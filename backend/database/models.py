from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

# sex, seller, sold_price, commentを履歴（配列/JSON文字列）で保存
class Horse(Base):
    __tablename__ = 'horses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    auction_id = Column(String(20), unique=True, index=True, nullable=True)  # オークションサイトの数値ID
    name = Column(String(100), nullable=False)  # 馬名（カタカナのみ）
    sex = Column(Text)  # 性別履歴（JSON配列文字列: ["牡", "牝", ...]）
    age = Column(Text)  # 年齢履歴（JSON配列文字列: [3, 4, ...]）
    sire = Column(String(100))  # 父
    dam = Column(String(100))  # 母
    dam_sire = Column(String(100))  # 母父
    race_record = Column(Text)  # 通算成績 (JSON形式で保存)
    weight = Column(Integer)  # 最終出走馬体重
    total_prize_start = Column(Float)  # 出品時の地方賞金
    total_prize_latest = Column(Float)  # 最新の地方賞金
    sold_price = Column(Text)  # 落札価格履歴（JSON配列文字列: [10000000, ...]）
    auction_date = Column(Text)  # 開催日履歴（JSON配列文字列: ["YYYY-MM-DD", ...]）
    seller = Column(Text)  # 販売申込者（JSON配列文字列: ["社台", ...]）
    disease_tags = Column(Text)  # 疾病カテゴリ
    comment = Column(Text)  # コメント履歴（JSON配列文字列: ["1回目コメント", ...]）
    image_url = Column(String(500))  # 馬画像URL
    primary_image = Column(String(500))  # 馬体写真1枚目のURL
    jbis_url = Column(String(500))  # JBISの馬情報ページURL
    detail_url = Column(String(500))  # 楽天競馬オークションの詳細ページURL
    unsold_count = Column(Integer, default=0)  # 主取り回数
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    auction_histories = relationship("AuctionHistory", back_populates="horse")


class AuctionHistory(Base):
    __tablename__ = 'auction_histories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    horse_id = Column(Integer, ForeignKey('horses.id'), nullable=False)
    auction_date = Column(String(10), nullable=False)  # YYYY-MM-DD形式
    price = Column(Integer, nullable=False)  # 落札価格
    seller = Column(String(100))  # 販売者
    buyer = Column(String(100))   # 落札者
    auction_house = Column(String(100))  # 市場名
    auction_name = Column(String(200))   # セール名
    lot_number = Column(String(20))      # ロット番号
    auction_url = Column(String(500))    # オークションURL
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    horse = relationship("Horse", back_populates="auction_histories")

# データベース設定
# プロジェクトルートの絶対パスを取得
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'horses.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection():
    db = None
    try:
        db = next(get_db())
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        print("データベースに接続されました")
        return True
    except Exception as e:
        print(f"データベース接続エラー: {str(e)}")
        return False
    finally:
        if db:
            db.close()