from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric
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
    
    # リレーションシップは __init__.py で定義
