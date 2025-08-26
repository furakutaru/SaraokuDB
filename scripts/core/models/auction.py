from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class Auction:
    """オークション情報を表すデータクラス"""
    auction_id: str  # オークションID
    horse_id: str  # 馬ID
    auction_date: datetime  # オークション開催日
    seller: Optional[str] = None  # 出品者
    buyer: Optional[str] = None  # 落札者
    price: Optional[float] = None  # 落札価格（万円）
    is_unsold: bool = False  # 主取りフラグ
    comment: Optional[str] = None  # コメント
    metadata: Optional[Dict[str, Any]] = None  # その他のメタデータ
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "auction_id": self.auction_id,
            "horse_id": self.horse_id,
            "auction_date": self.auction_date.isoformat(),
            "seller": self.seller,
            "buyer": self.buyer,
            "price": self.price,
            "is_unsold": self.is_unsold,
            "comment": self.comment,
            "metadata": self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Auction':
        """辞書からインスタンスを生成"""
        return cls(
            auction_id=data["auction_id"],
            horse_id=data["horse_id"],
            auction_date=datetime.fromisoformat(data["auction_date"]),
            seller=data.get("seller"),
            buyer=data.get("buyer"),
            price=data.get("price"),
            is_unsold=data.get("is_unsold", False),
            comment=data.get("comment"),
            metadata=data.get("metadata")
        )
