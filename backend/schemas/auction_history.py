from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from .horse import Horse

class AuctionHistoryBase(BaseModel):
    horse_id: int
    auction_date: datetime
    price: Optional[float] = None
    is_unsold: bool = False
    comment: Optional[str] = None

class AuctionHistoryCreate(AuctionHistoryBase):
    pass

class AuctionHistoryUpdate(BaseModel):
    price: Optional[float] = None
    is_unsold: Optional[bool] = None
    comment: Optional[str] = None

class AuctionHistoryInDBBase(AuctionHistoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class AuctionHistory(AuctionHistoryInDBBase):
    horse: Optional[Horse] = None

class AuctionHistoryInDB(AuctionHistoryInDBBase):
    pass
