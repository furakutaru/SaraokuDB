from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from database.models import Horse, get_db
from database.schemas import HorseResponse

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
            
            # Horseオブジェクトを辞書に変換
            horses_data = []
            for horse in horses:
                horse_dict = {}
                for column in horse.__table__.columns:
                    # カラム名を取得して、その値を辞書に追加
                    column_name = column.name
                    horse_dict[column_name] = getattr(horse, column_name, None)
                horses_data.append(horse_dict)
            
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
        
        # フロントエンドの期待する形式に変換
        auction_histories = []
        for horse in horses_data:
            # オークション履歴の作成
            auction_history = {
                'id': horse.get('id'),
                'horse_id': horse.get('id'),
                'auction_date': horse.get('auction_date'),
                'sold_price': horse.get('sold_price'),
                'total_prize_start': horse.get('total_prize_start'),
                'total_prize_latest': horse.get('total_prize_latest'),
                'weight': horse.get('weight'),
                'seller': horse.get('seller'),
                'is_unsold': horse.get('unsold_count', 0) > 0,
                'comment': horse.get('comment', ''),
                'created_at': horse.get('created_at')
            }
            auction_histories.append(auction_history)
            
            # 馬データのフィールド名を調整
            horse['damsire'] = horse.pop('dam_sire', None)
            
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
async def get_horse(horse_id: int, db: Session = Depends(get_db)):
    """馬IDで馬データを取得"""
    horse = db.query(Horse).filter(Horse.id == horse_id).first()
    if not horse:
        raise HTTPException(status_code=404, detail="Horse not found")
    return horse
