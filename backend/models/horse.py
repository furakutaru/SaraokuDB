from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, JSON
from sqlalchemy.orm import relationship
from .base import Base

class Horse(Base):
    __tablename__ = "horses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    is_unsold = Column(Boolean, default=False, nullable=False)
    bid_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, server_default='now()')
    latest_auction_id = Column(Integer, ForeignKey('auction_histories.id'), nullable=True)
    total_prize_latest = Column(Numeric(12, 2), nullable=True, comment='最新の賞金（総額）')
    sire = Column(String, nullable=True, comment='父馬名')
    dam = Column(String, nullable=True, comment='母馬名')
    sex = Column(String, nullable=True, comment='性別')
    is_broodmare = Column(Boolean, default=False, comment='繁殖牝馬フラグ')
    
    # 賞金管理関連のフィールド
    last_prize_update = Column(DateTime(timezone=True), comment='最終賞金更新日時')
    next_update_due_date = Column(DateTime(timezone=True), comment='次回更新予定日')
    update_interval_months = Column(Integer, default=3, comment='更新間隔（月）')
    is_retired = Column(Boolean, default=False, comment='引退フラグ')
    race_records = Column(JSON, nullable=True, comment='レース記録（JSON形式）')
    
    # リレーションシップ
    prize_histories = relationship("HorsePrizeHistory", back_populates="horse", cascade="all, delete-orphan")
