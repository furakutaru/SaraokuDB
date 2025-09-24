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
async def get_horse(horse_id: str, db: Session = Depends(get_db)):
    """馬IDで馬データを取得"""
    # horse_id が数値なら内部ID検索、そうでなければ auction_id で検索
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
    if not horse:
        raise HTTPException(status_code=404, detail="Horse not found")

    # NOTE: DB上は一部フィールドが JSON 配列文字列(例: "[3]", "[8500000]") として保存されている。
    # HorseResponse は age(int), sold_price(int) を期待するため、適切に正規化して返す。
    import json

    def parse_first_int(value):
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            s = value.strip()
            # JSON 配列文字列 [8500000] など
            if s.startswith('[') and s.endswith(']'):
                try:
                    arr = json.loads(s)
                    if isinstance(arr, list) and len(arr) > 0:
                        # 直近(最後)を優先
                        last = arr[-1]
                        return int(last) if isinstance(last, (int, float, str)) and str(last).strip('"').isdigit() else None
                except Exception:
                    pass
            # 数字文字列
            num = s.strip('"')
            if num.isdigit():
                return int(num)
        return None

    def parse_first_str(value):
        if value is None:
            return None
        if isinstance(value, str):
            s = value.strip()
            if s.startswith('[') and s.endswith(']'):
                try:
                    arr = json.loads(s)
                    if isinstance(arr, list) and len(arr) > 0:
                        # 先頭要素を採用
                        return str(arr[0])
                except Exception:
                    pass
            # そのまま
            return value
        return str(value)

    # 正規化
    age_norm = parse_first_int(horse.age)
    sold_price_norm = parse_first_int(horse.sold_price)
    auction_date_norm = parse_first_str(horse.auction_date)
    seller_norm = parse_first_str(horse.seller)
    sex_norm = parse_first_str(horse.sex)
    comment_norm = parse_first_str(horse.comment)

    # dam_sire -> スキーマは dam_sire 名で受けるのでそのまま

    # レスポンス辞書を手動構築（Pydantic が期待するプリミティブ型に合わせる）
    response = {
        "id": horse.id,
        "name": horse.name,
        "auction_id": horse.auction_id,
        "sex": sex_norm,
        "age": age_norm,
        "sire": horse.sire,
        "dam": horse.dam,
        "dam_sire": horse.dam_sire,
        "race_record": horse.race_record,
        "weight": horse.weight,
        "total_prize_start": horse.total_prize_start,
        "total_prize_latest": horse.total_prize_latest,
        "sold_price": sold_price_norm,
        "auction_date": auction_date_norm,
        "seller": seller_norm,
        "disease_tags": horse.disease_tags,
        "comment": comment_norm,
        "image_url": horse.image_url,
        "created_at": horse.created_at,
        "updated_at": horse.updated_at,
    }

    return response
