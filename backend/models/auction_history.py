from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class AuctionHistory(Base):
    __tablename__ = "auction_histories"

    id = Column(Integer, primary_key=True, index=True)
    horse_id = Column(Integer, ForeignKey('horses.id'), nullable=False)
    auction_date = Column(DateTime, nullable=False, index=True)
    price = Column(Numeric(12, 2), nullable=True)
    is_unsold = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default='now()')
    updated_at = Column(DateTime, server_default='now()', onupdate='now()')
    
    # リレーションシップは __init__.py で定義
