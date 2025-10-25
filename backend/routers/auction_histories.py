from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging
from database import get_db
from database.models import AuctionHistory
from database.schemas import AuctionHistory as AuctionHistorySchema

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ルーターの作成
router = APIRouter(
    prefix="/api/auction_histories",  # /api/auction_histories でアクセスできるようにする
    tags=["auction_histories"],
    responses={404: {"description": "Not found"}},
)

@router.get("", response_model=List[AuctionHistorySchema])  # スラッシュを削除
async def read_auction_histories(
    skip: int = 0, 
    limit: int = 100,
    horse_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """オークション履歴を取得"""
    try:
        query = db.query(AuctionHistory)
        
        if horse_id is not None:
            query = query.filter(AuctionHistory.horse_id == horse_id)
            
        auction_histories = query.offset(skip).limit(limit).all()
        return auction_histories
    except Exception as e:
        logger.error(f"Error fetching auction histories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/horses/{horse_id}", response_model=List[AuctionHistorySchema])
async def read_auction_histories_by_horse_id(
    horse_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """馬IDでオークション履歴を取得"""
    try:
        auction_histories = db.query(AuctionHistory)\
            .filter(AuctionHistory.horse_id == horse_id)\
            .order_by(AuctionHistory.auction_date.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
            
        if not auction_histories:
            logger.info(f"No auction histories found for horse_id: {horse_id}")
            return []
            
        logger.info(f"Found {len(auction_histories)} auction histories for horse_id: {horse_id}")
        return auction_histories
    except Exception as e:
        logger.error(f"Error fetching auction histories for horse {horse_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ルーターをエクスポート
__all__ = ["router"]
