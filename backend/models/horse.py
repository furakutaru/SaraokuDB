from sqlalchemy import Column, Integer, String, DateTime
from .base import Base

class Horse(Base):
    __tablename__ = "horses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    breed = Column(String)
    age = Column(Integer)
    created_at = Column(DateTime, server_default='now()')
