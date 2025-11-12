from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class HorsePrizeHistory(Base):
    """馬の賞金履歴を管理するモデル"""
    __tablename__ = "horse_prize_histories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    horse_id = Column(Integer, ForeignKey("horses.id"), nullable=False, index=True)
    prize = Column(Integer, nullable=False, comment="賞金額（円）")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # リレーションシップ
    horse = relationship("Horse", back_populates="prize_histories")

    def __repr__(self):
        return f"<HorsePrizeHistory(horse_id={self.horse_id}, prize={self.prize}, created_at={self.created_at})>"

    @classmethod
    def create(cls, db, horse_id: int, prize: int):
        """新しい賞金履歴を作成"""
        history = cls(horse_id=horse_id, prize=prize)
        db.add(history)
        db.commit()
        db.refresh(history)
        return history

    @classmethod
    def get_latest_prize(cls, db, horse_id: int) -> int:
        """指定された馬の最新の賞金額を取得"""
        latest = db.query(cls).filter(
            cls.horse_id == horse_id
        ).order_by(
            cls.created_at.desc()
        ).first()
        
        return latest.prize if latest else 0
