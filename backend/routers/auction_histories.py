from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import logging
from database import get_db
from database.models import AuctionHistory
from database.schemas import AuctionHistory as AuctionHistorySchema, AuctionHistoryCreate

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

@router.get("/by_horse/{horse_id}", response_model=List[AuctionHistorySchema])
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

@router.post("/check_duplicate", response_model=Dict[str, bool])
async def check_duplicate_auction_history(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """同じ馬（名前・血統）で同じ日付のオークション履歴が存在するかチェックする"""
    try:
        # リクエストからパラメータを取得
        horse_name = request.get('horse_name')
        sire_name = request.get('sire_name')
        dam_name = request.get('dam_name')
        damsire_name = request.get('damsire_name')
        auction_date = request.get('auction_date')
        
        # バリデーション
        if not all([horse_name, sire_name, dam_name, damsire_name, auction_date]):
            raise HTTPException(
                status_code=400,
                detail="必須パラメータが不足しています"
            )
        
        # 日付のバリデーション
        try:
            auction_date_obj = datetime.strptime(auction_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="日付の形式が正しくありません。YYYY-MM-DD形式で指定してください。"
            )
        
        # 同じ馬（名前・血統）で同じ日付のオークション履歴を検索
        existing = db.query(AuctionHistory).filter(
            AuctionHistory.horse_name == horse_name,
            AuctionHistory.sire_name == sire_name,
            AuctionHistory.dam_name == dam_name,
            AuctionHistory.damsire_name == damsire_name,
            AuctionHistory.auction_date == auction_date_obj
        ).first()
        
        return {"exists": existing is not None}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"オークション履歴の重複チェック中にエラーが発生しました: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="オークション履歴の重複チェック中にエラーが発生しました"
        )

# ルーターをエクスポート
__all__ = ["router"]
