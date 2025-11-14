from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, ForwardRef, TYPE_CHECKING

# 循環インポートを防ぐための型ヒント
if TYPE_CHECKING:
    from .auction_history import AuctionHistory

class HorseBase(BaseModel):
    name: str
    breed: Optional[str] = None
    age: Optional[int] = None
    disease_tags: Optional[List[str]] = None
    race_records: Optional[dict] = None

class HorseCreate(HorseBase):
    pass

class HorseUpdate(HorseBase):
    name: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[int] = None
    race_records: Optional[dict] = None

class HorseInDBBase(HorseBase):
    id: int
    latest_auction_id: Optional[int] = None
    created_at: datetime

    class Config:
        orm_mode = True

class Horse(HorseInDBBase):
    pass

# 前方参照を使用して循環インポートを解決
AuctionHistoryRef = ForwardRef('AuctionHistory')

class HorseWithAuction(Horse):
    latest_auction: Optional[AuctionHistoryRef] = None

class HorseInDB(HorseInDBBase):
    pass
