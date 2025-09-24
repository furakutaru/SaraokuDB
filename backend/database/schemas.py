from pydantic import BaseModel
from typing import List, Optional, Union, Dict, Any
from datetime import datetime

class RaceRecordSummary(BaseModel):
    status: Optional[str] = None
    races: Optional[int] = None
    wins: Optional[int] = None
    first: Optional[int] = None
    second: Optional[int] = None
    third: Optional[int] = None
    other: Optional[int] = None
    summary: Optional[str] = None

class HorseBase(BaseModel):
    name: str
    auction_id: Optional[str] = None
    sex: Optional[str] = None
    age: Optional[int] = None
    sire: Optional[str] = None
    dam: Optional[str] = None
    dam_sire: Optional[str] = None
    race_record: Optional[Union[RaceRecordSummary, str]] = None
    weight: Optional[int] = None
    total_prize_start: Optional[float] = None
    total_prize_latest: Optional[float] = None
    sold_price: Optional[int] = None
    auction_date: Optional[str] = None
    seller: Optional[str] = None
    disease_tags: Optional[str] = None
    comment: Optional[str] = None
    image_url: Optional[str] = None

class HorseCreate(HorseBase):
    pass

class HorseUpdate(HorseBase):
    total_prize_latest: Optional[float] = None
    jbis_url: Optional[str] = None

class HorseResponse(HorseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class StatisticsResponse(BaseModel):
    total_horses: int
    average_price: int
    average_growth_rate: float
    horses_with_growth_data: int
