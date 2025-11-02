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
# main.py で /api/auction_histories プレフィックスを指定しているため、ここでは空にします
router = APIRouter(
    prefix="",
    tags=["auction_histories"],
    responses={404: {"description": "Not found"}},
)

@router.get("", response_model=List[AuctionHistorySchema])
async def read_auction_histories(
    skip: int = 0, 
    limit: int = 100,
    horse_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    オークション履歴を取得
    
    - horse_idが指定された場合は、その馬のオークション履歴のみを返す
    - 指定がない場合は全てのオークション履歴を返す
    """
    try:
        logger.info(f"Fetching auction histories with params: horse_id={horse_id}, skip={skip}, limit={limit}")
        
        query = db.query(AuctionHistory)
        
        if horse_id is not None:
            logger.info(f"Filtering by horse_id: {horse_id}")
            query = query.filter(AuctionHistory.horse_id == horse_id)
        
        # 日付の降順でソート
        query = query.order_by(AuctionHistory.auction_date.desc())
        
        # ページネーションを適用
        auction_histories = query.offset(skip).limit(limit).all()
        
        logger.info(f"Found {len(auction_histories)} auction histories")
        return auction_histories
    except Exception as e:
        logger.error(f"Error fetching auction histories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# このエンドポイントは read_auction_histories に統合されました
# 代わりに /api/auction_histories?horse_id={horse_id} を使用してください

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

@router.post("", response_model=AuctionHistorySchema, status_code=201)
async def create_auction_history(
    history: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """新しいオークション履歴を作成する"""
    try:
        # 必須フィールドのバリデーション
        required_fields = [
            'horse_id', 'horse_name', 'sire_name', 'dam_name', 'damsire_name',
            'auction_date', 'price'
        ]
        for field in required_fields:
            if field not in history:
                raise HTTPException(
                    status_code=400,
                    detail=f"必須フィールドが不足しています: {field}"
                )
        
        # 日付のバリデーション
        if isinstance(history['auction_date'], str):
            try:
                history['auction_date'] = datetime.strptime(history['auction_date'], "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="日付の形式が正しくありません。YYYY-MM-DD形式で指定してください。"
                )
        
        # 既存のレコードをチェック
        existing = db.query(AuctionHistory).filter(
            AuctionHistory.horse_name == history['horse_name'],
            AuctionHistory.sire_name == history['sire_name'],
            AuctionHistory.dam_name == history['dam_name'],
            AuctionHistory.damsire_name == history['damsire_name'],
            AuctionHistory.auction_date == history['auction_date']
        ).first()
        
        if existing:
            # 既存のレコードを更新
            for key, value in history.items():
                setattr(existing, key, value)
            db.commit()
            db.refresh(existing)
            return existing
        
        # 新しいレコードを作成
        db_history = AuctionHistory(**history)
        db.add(db_history)
        db.commit()
        db.refresh(db_history)
        return db_history
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"オークション履歴の作成中にエラーが発生しました: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"オークション履歴の作成中にエラーが発生しました: {str(e)}"
        )

# ルーターをエクスポート
__all__ = ["router"]
