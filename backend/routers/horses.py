from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from database.models import Horse, get_db
from database.schemas import HorseResponse
from services.horse_serializer import serialize_horse
from services.horses_list_mapper import map_horses_list

router = APIRouter(prefix="/api", tags=["horses"])

@router.get("/horses", response_model=Dict[str, Any])
async def get_horses(
    skip: int = 0,
    limit: int = 100,
    auction_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """馬の一覧を取得するエンドポイント"""
    try:
        print("=== Starting get_horses endpoint ===")
        print(f"Parameters - skip: {skip}, limit: {limit}, auction_date: {auction_date}")
        
        # 1. Queryオブジェクトの作成
        print("\n1. Creating query object...")
        query = db.query(Horse)
        print(f"Query object created: {query}")
        
        # 2. フィルタリング
        if auction_date:
            print(f"\n2. Applying auction_date filter: {auction_date}")
            from sqlalchemy import text
            query = query.filter(Horse.auction_date.like(f'%{auction_date}%'))
            print(f"Filter applied. Query: {query}")
        
        # 3. 総レコード数の取得
        print("\n3. Getting total count...")
        try:
            total_count = query.count()
            print(f"Total count: {total_count}")
        except Exception as e:
            print(f"Error getting count: {str(e)}")
            raise
        
        # 4. データの取得と辞書への変換
        print("\n4. Fetching and processing data...")
        try:
            # データベースから取得
            horses = query.offset(skip).limit(limit).all()
            print(f"Retrieved {len(horses)} horses")
            # サービスでフロントエンド用の配列へ変換
            horses_data, auction_histories = map_horses_list(horses)

            if horses_data:
                print("\nSample horse data:")
                sample = horses_data[0]
                print(f"  - ID: {sample.get('id')}")
                print(f"  - Name: {sample.get('name')}")
                print(f"  - Sex: {sample.get('sex')}")
                print(f"  - Sire: {sample.get('sire')}")
                print(f"  - Dam: {sample.get('dam')}")
                print(f"  - Auction Date: {sample.get('auction_date')}")
        except Exception as e:
            print(f"Error fetching/processing horses: {str(e)}")
            import traceback
            print(traceback.format_exc())
            raise
        
        # 5. レスポンスの作成
        print("\n5. Creating response...")

        response = {
            "horses": horses_data,
            "auctionHistories": auction_histories,
            "metadata": {
                "last_updated": datetime.utcnow().isoformat(),
                "total_horses": total_count,
                "total_auction_records": len(auction_histories)
            }
        }
        print("Response created successfully")
        return response
        
    except Exception as e:
        print(f"\n!!! ERROR in get_horses: {str(e)}")
        import traceback
        error_trace = traceback.format_exc()
        print("Full traceback:")
        print(error_trace)
        raise HTTPException(
            status_code=500,
            detail={
                "message": "An error occurred while fetching horses",
                "error": str(e)
                # 本番環境ではスタックトレースを返さない方が安全です
                # "traceback": error_trace
            }
        )

@router.get("/horses/{horse_id}", response_model=HorseResponse)
async def get_horse(horse_id: str, db: Session = Depends(get_db)):
    """馬IDで馬データを取得
    
    検索順:
    1. 内部ID (horse_idが数値の場合)
    2. auction_id で検索
    3. detail_url に含まれる数値IDで検索
    """
    horse = None
    # 1) 数値として内部ID検索
    try:
        num_id = int(horse_id)
        horse = db.query(Horse).filter(Horse.id == num_id).first()
    except Exception:
        pass
        
    # 2) 見つからなければ auction_id で検索（文字列一致）
    if not horse:
        horse = db.query(Horse).filter(Horse.auction_id == horse_id).first()
        
    # 3) まだ見つからなければ、auction_id で部分一致検索
    if not horse and horse_id.isdigit():
        horse = db.query(Horse).filter(
            Horse.auction_id.like(f'%{horse_id}%')
        ).first()
        
    if not horse:
        # 利用可能な馬の一覧を取得（IDと名前）
        available_horses = db.query(Horse.id, Horse.name).order_by(Horse.id.desc()).limit(10).all()
        raise HTTPException(
            status_code=404, 
            detail={
                "error": f"馬が見つかりません (ID: {horse_id})",
                "available_horses": [
                    {"id": str(h.id), "name": h.name} 
                    for h in available_horses
                ]
            }
        )

    # 正規化と辞書構築は専用サービスに委譲
    return serialize_horse(horse)
