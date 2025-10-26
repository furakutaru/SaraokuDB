from .horse import HorseBase, HorseCreate, HorseUpdate, HorseInDBBase, Horse, HorseWithAuction, HorseInDB
from .auction_history import (
    AuctionHistoryBase, 
    AuctionHistoryCreate, 
    AuctionHistoryUpdate, 
    AuctionHistoryInDBBase, 
    AuctionHistory,
    AuctionHistoryInDB
)

# 循環インポートを解決するために、型ヒントを後で更新
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .auction_history import AuctionHistory
    from .horse import Horse

# 循環参照を解決するために、後から型ヒントを更新
HorseWithAuction.update_forward_refs(AuctionHistory=AuctionHistory)
AuctionHistory.update_forward_refs(Horse=Horse)
