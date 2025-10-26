# すべてのモデルをインポート
from .base import Base
from .user import User
from .horse import Horse
from .auction_history import AuctionHistory

# 循環インポートを避けるために、リレーションシップはここで設定
from sqlalchemy.orm import relationship

def setup_relationships():
    """モデル間のリレーションシップを設定する"""
    # 1. Horse モデルのリレーションシップ
    if not hasattr(Horse, 'auction_histories'):
        Horse.auction_histories = relationship(
            "AuctionHistory", 
            back_populates="horse",
            order_by="AuctionHistory.auction_date.desc()",
            foreign_keys="[AuctionHistory.horse_id]"
        )
    
    if not hasattr(Horse, 'latest_auction'):
        Horse.latest_auction = relationship(
            "AuctionHistory",
            primaryjoin="Horse.latest_auction_id == AuctionHistory.id",
            foreign_keys="[Horse.latest_auction_id]",
            uselist=False,
            post_update=True,
            lazy='joined',  # 常に結合してロード
            viewonly=False
        )
    
    # 2. AuctionHistory モデルのリレーションシップ
    if not hasattr(AuctionHistory, 'horse'):
        AuctionHistory.horse = relationship(
            "Horse",
            back_populates="auction_histories",
            foreign_keys="[AuctionHistory.horse_id]"
        )
    
    if not hasattr(AuctionHistory, 'latest_horse'):
        AuctionHistory.latest_horse = relationship(
            "Horse",
            back_populates="latest_auction",
            foreign_keys="[AuctionHistory.id]",
            post_update=True,
            uselist=False,
            viewonly=False
        )

# リレーションシップを設定
setup_relationships()

# リレーションシップが正しく設定されたか確認
if not hasattr(Horse, 'latest_auction'):
    raise RuntimeError("Failed to set up latest_auction relationship on Horse model")

if not hasattr(AuctionHistory, 'latest_horse'):
    raise RuntimeError("Failed to set up latest_horse relationship on AuctionHistory model")

# リレーションシップが正しく設定されたか確認
if not hasattr(Horse, 'latest_auction'):
    raise RuntimeError("Failed to set up latest_auction relationship on Horse model")

if not hasattr(AuctionHistory, 'latest_horse'):
    raise RuntimeError("Failed to set up latest_horse relationship on AuctionHistory model")
