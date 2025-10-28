from fastapi import APIRouter
from . import horses, auction_histories

# メインのルーターを作成
api_router = APIRouter()

# サブルーターをインポートしてマウント
api_router.include_router(horses.router, prefix="/horses", tags=["horses"])
api_router.include_router(auction_histories.router, prefix="/auction_histories", tags=["auction_histories"])
