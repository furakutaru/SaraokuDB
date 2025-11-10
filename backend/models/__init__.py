# すべてのモデルをインポート
from .base import Base
from .user import User
from .horse import Horse
from .auction_history import AuctionHistory

# 循環インポートを避けるために、リレーションシップはここで設定
from sqlalchemy.orm import relationship, backref

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
            foreign_keys="[AuctionHistory.horse_id]",
            back_populates="auction_histories",
            viewonly=True  # 読み取り専用に設定
        )

# リレーションシップを設定
setup_relationships()

# リレーションシップが正しく設定されたか確認
if not hasattr(Horse, 'latest_auction'):
    raise RuntimeError("Failed to set up latest_auction relationship on Horse model")

# latest_horse リレーションシップは削除されたため、チェックを削除
