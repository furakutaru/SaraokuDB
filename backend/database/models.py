from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, create_engine
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql.expression import text
from datetime import datetime
import os
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

Base = declarative_base()

# 共通のカラムミックスイン
class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

# ユーザーモデル
class User(Base, TimestampMixin):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'public'}
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # リレーションシップを明示的に指定
    auction_histories = relationship(
        "AuctionHistory", 
        back_populates="user",
        foreign_keys="[AuctionHistory.user_id]",
        primaryjoin="User.id == foreign(AuctionHistory.user_id)",
        remote_side="[AuctionHistory.user_id]"
    )
    horses = relationship(
        "Horse", 
        back_populates="owner",
        foreign_keys="[Horse.owner_id]",
        primaryjoin="User.id == foreign(Horse.owner_id)",
        remote_side="[Horse.owner_id]"
    )

# sex, seller, sold_price, commentを履歴（配列/JSON文字列）で保存
class Horse(Base):
    __tablename__ = 'horses'
    __table_args__ = {'schema': 'public'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    auction_id = Column(String(20), unique=True, index=True, nullable=True)  # オークションサイトの数値ID
    name = Column(String(100), nullable=False)  # 馬名（カタカナのみ）
    sex = Column(Text)  # 性別履歴（JSON配列文字列: ["牡", "牝", ...]）
    age = Column(Text)  # 年齢履歴（JSON配列文字列: [3, 4, ...]）
    sire = Column(String(100))  # 父
    dam = Column(String(100))  # 母
    dam_sire = Column(String(100))  # 母父
    
    # 後方互換性のためのプロパティ
    @property
    def damsire(self):
        return self.dam_sire
        
    @damsire.setter
    def damsire(self, value):
        self.dam_sire = value
    race_record = Column(Text)  # 通算成績 (JSON形式で保存)
    weight = Column(Integer)  # 最終出走馬体重
    total_prize_start = Column(Float)  # 出品時の地方賞金
    total_prize_latest = Column(Float)  # 最新の地方賞金
    prize_money = Column(Float, nullable=True)  # 賞金（スクレイピング用の一時的なフィールド）
    sold_price = Column(Text)  # 落札価格履歴（JSON配列文字列: [10000000, ...]）
    auction_date = Column(Text)  # 開催日履歴（JSON配列文字列: ["YYYY-MM-DD", ...]）
    disease_tags = Column(Text)  # 疾病タグ（JSON配列文字列: ["跛行", ...]）
    seller = Column(Text)  # 販売申込者（JSON配列文字列: ["社台", ...]）
    comment = Column(Text)  # コメント履歴（JSON配列文字列: ["1回目コメント", ...]）
    image_url = Column(String(500))  # 馬画像URL
    primary_image = Column(String(500))  # 馬体写真1枚目のURL
    jbis_url = Column(String(500))  # JBISの馬情報ページURL
    detail_url = Column(String(500))  # 楽天競馬オークションの詳細ページURL
    unsold_count = Column(Integer, default=0)  # 主取り回数
    bid_count = Column(Integer, nullable=True, comment='入札数')  # 入札数
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    scraped_at = Column(DateTime, nullable=True)  # スクレイピング日時
    
    # 統合されたレース記録
    unified_race_records = Column(JSON, nullable=True, comment='統合されたレース記録（JSON形式）')
    
    # リレーションシップ
    auction_histories = relationship(
        "AuctionHistory", 
        back_populates="horse",
        foreign_keys="[AuctionHistory.horse_id]",
        primaryjoin="Horse.id == foreign(AuctionHistory.horse_id)",
        remote_side="[AuctionHistory.horse_id]"
    )
    latest_auction_id = Column(Integer, ForeignKey('public.auction_histories.id', name='fk_horses_latest_auction_id_auction_histories'), nullable=True)
    latest_auction = relationship(
        "AuctionHistory",
        primaryjoin="Horse.latest_auction_id == AuctionHistory.id",
        foreign_keys=[latest_auction_id],
        uselist=False,
        post_update=True,
        lazy='joined',  # 常に結合してロード
        overlaps="latest_horse"  # 双方向リレーションシップの競合を解決
    )
    owner_id = Column(Integer, ForeignKey('public.users.id', name='fk_horses_owner_id_users'), nullable=True)
    owner = relationship(
        "User", 
        back_populates="horses",
        foreign_keys=[owner_id],
        primaryjoin="Horse.owner_id == User.id",
        remote_side="[User.id]"
    )
    
    is_unsold = Column(Boolean, default=False, nullable=False, comment='最新のオークション情報から自動設定される主取りフラグ')
    
    @property
    def is_unsold_property(self):
        """互換性のためのプロパティ（必要に応じて使用）"""
        if self.latest_auction:
            return self.latest_auction.is_unsold
        return self.is_unsold


class AuctionHistory(Base):
    __tablename__ = 'auction_histories'
    __table_args__ = {'schema': 'public'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    horse_id = Column(Integer, ForeignKey('public.horses.id', name='fk_auction_histories_horse_id_horses'), nullable=False)
    horse_name = Column(String(255))  # 馬名
    sire_name = Column(String(255))   # 父名
    dam_name = Column(String(255))    # 母名
    damsire_name = Column(String(255)) # 母父名
    auction_date = Column(String(10), nullable=False)  # YYYY-MM-DD形式
    price = Column(Integer, nullable=False)  # 落札価格
    seller = Column(String(100))  # 販売者
    buyer = Column(String(100))   # 落札者
    auction_house = Column(String(100))  # 市場名
    auction_name = Column(String(200))   # セール名
    lot_number = Column(String(20))      # ロット番号
    auction_url = Column(String(500))    # オークションURL
    is_unsold = Column(Boolean, default=False, nullable=False, comment='主取りフラグ')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    scraped_at = Column(DateTime, nullable=True)  # スクレイピング日時
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # AuctionHistoryが作成・更新されたら、関連するHorseのis_unsoldも更新
        if self.horse:
            self.horse.is_unsold = self.is_unsold
    
    # リレーションシップ
    horse = relationship(
        "Horse", 
        back_populates="auction_histories",
        foreign_keys=[horse_id],
        primaryjoin="AuctionHistory.horse_id == Horse.id",
        remote_side="[Horse.id]"
    )
    latest_horse = relationship(
        "Horse",
        primaryjoin="AuctionHistory.id == Horse.latest_auction_id",
        foreign_keys="[Horse.latest_auction_id]",
        uselist=False,
        post_update=True,
        overlaps="latest_auction"  # 双方向リレーションシップの競合を解決
    )
    user_id = Column(
        Integer,
        ForeignKey('public.users.id', name='fk_auction_histories_user_id_users'),
        nullable=True
    )
    user = relationship(
        "User", 
        back_populates="auction_histories",
        foreign_keys=[user_id],
        primaryjoin="AuctionHistory.user_id == User.id",
        remote_side="[User.id]"
    )

# データベース設定
# Neon PostgreSQL接続URLを環境変数から取得
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# SSLモードを設定（Neonでは必須）
if DATABASE_URL.startswith('postgres') and 'sslmode=' not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

# エンジン設定
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

# セッションファクトリ
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection():
    """データベース接続を確認する関数"""
    db = None
    try:
        db = next(get_db())
        # PostgreSQL用の接続チェック
        db.execute(text("SELECT 1"))
        print("✅ データベースに正常に接続されました")
        
        # テーブルが存在するか確認
        table_exists = db.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'horses'
                )
                """
            )
        ).scalar()
        
        if table_exists:
            print("✅ horses テーブルが存在します")
            # レコード数を取得
            count = db.execute(text("SELECT COUNT(*) FROM horses")).scalar()
            print(f"✅ レコード数: {count}件")
        else:
            print("⚠️ horses テーブルが存在しません。マイグレーションが必要です。")
        
        return True
    except Exception as e:
        print(f"❌ データベース接続エラー: {str(e)}")
        print(f"接続URL: {DATABASE_URL}")
        return False
    finally:
        if db:
            db.close()