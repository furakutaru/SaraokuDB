from pydantic import BaseModel, ConfigDict
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
    
    # 後方互換性のためのプロパティ
    @property
    def damsire(self):
        return self.dam_sire
        
    @damsire.setter
    def damsire(self, value):
        self.dam_sire = value

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
    jbis_url: Optional[str] = None
    detail_url: Optional[str] = None
    rakuten_url: Optional[str] = None
    auction_url: Optional[str] = None
    color: Optional[str] = None  # 毛色（オプション）
    bid_count: Optional[int] = None  # 入札数

class HorseCreate(HorseBase):
    pass

class HorseUpdate(HorseBase):
    total_prize_latest: Optional[float] = None

class AuctionHistoryBase(BaseModel):
    horse_id: int
    horse_name: Optional[str] = None
    sire_name: Optional[str] = None
    dam_name: Optional[str] = None
    damsire_name: Optional[str] = None
    auction_date: str
    price: int
    seller: Optional[str] = None
    buyer: Optional[str] = None
    auction_house: Optional[str] = None
    auction_name: Optional[str] = None
    lot_number: Optional[str] = None
    auction_url: Optional[str] = None

class AuctionHistoryCreate(AuctionHistoryBase):
    pass

class AuctionHistory(AuctionHistoryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    scraped_at: Optional[datetime] = None  # スクレイピング日時
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class HorseResponse(HorseBase):
    id: int
    created_at: datetime
    updated_at: datetime
    scraped_at: Optional[datetime] = None  # スクレイピング日時

    # Pydantic v2: enable ORM mode equivalent
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    # プロパティをモデルフィールドとして認識させる
    is_unsold: bool = False
    
    # オークション履歴
    auction_histories: List[AuctionHistory] = []


class StatisticsResponse(BaseModel):
    total_horses: int
    average_price: int
    average_growth_rate: float
    horses_with_growth_data: int
