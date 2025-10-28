from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class Horse(Base):
    __tablename__ = "horses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    breed = Column(String)
    age = Column(Integer)
    is_unsold = Column(Boolean, default=False, nullable=False)
    bid_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, server_default='now()')
    latest_auction_id = Column(Integer, ForeignKey('auction_histories.id'), nullable=True)
    
    # リレーションシップは __init__.py で定義
