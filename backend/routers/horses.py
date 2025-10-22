from datetime import datetime
import json
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from database.models import Horse, get_db
from database.schemas import HorseResponse
from services.horse_serializer import serialize_horse
from services.horses_list_mapper import map_horses_list

# ルーターの設定
router = APIRouter(tags=["horses"])

from fastapi import Request
import logging

# ロガーの設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# デバッグ用に現在のモジュールのパスをログに出力
logger.info(f"Loading {__name__} module")

# デバッグ用に現在のファイルのパスを表示
import os
logger.info(f"Current file path: {os.path.abspath(__file__)}")
logger.info(f"Current working directory: {os.getcwd()}")

@router.get("/horses/latest", response_model=Dict[str, Any], tags=["horses"])
async def get_latest_horses(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """最新のオークションの馬一覧を取得するエンドポイント"""
    logger.info("Calling /horses/latest endpoint")
    return await get_horses(request, skip, limit, None, 'true', db)

@router.get("/horses", response_model=Dict[str, Any], tags=["horses"])
async def get_horses(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    auction_date: Optional[str] = None,
    latest_auction: str = 'false',
    db: Session = Depends(get_db)
):
    """馬の一覧を取得するエンドポイント
    
    Args:
        skip: スキップするレコード数
        limit: 取得する最大レコード数
        auction_date: オークション日でフィルタリング（部分一致）
        latest_auction: 'true'の場合、最新のオークション日でフィルタリング
    """
    try:
        logger.info("\n=== Starting get_horses endpoint ===")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Query params: {request.query_params}")
        logger.info(f"latest_auction: {latest_auction}, type: {type(latest_auction)}")
        
        latest_auction_bool = latest_auction.lower() == 'true' or request.query_params.get('latest_auction', '').lower() == 'true'
        
        # クエリオブジェクトの初期化
        query = db.query(Horse)
        print(f"Query object created: {query}")
        
        # 1. 最新のオークション日を取得（必要な場合）
        latest_date = None
        if latest_auction_bool:
            print("\n1.1 Getting latest auction date (parse JSON array strings)...")
            
            # 全レコードから auction_date テキストを取得
            raw_dates = db.query(Horse.auction_date).filter(Horse.auction_date.isnot(None)).all()
            print(f"Fetched {len(raw_dates)} auction_date entries")
            
            # テキストから 'YYYY-MM-DD' を抽出して最大日付を決定
            import re, json
            date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}")
            extracted_dates = []
            for (ad,) in raw_dates:
                if not ad:
                    continue
                try:
                    # JSON配列文字列の場合
                    if isinstance(ad, str) and ad.strip().startswith('['):
                        arr = json.loads(ad)
                        for item in arr:
                            if isinstance(item, str) and date_pattern.fullmatch(item):
                                extracted_dates.append(item)
                    else:
                        # 平文（単一日付）またはその他の文字列
                        m = date_pattern.search(str(ad))
                        if m:
                            extracted_dates.append(m.group(0))
                except Exception as e:
                    print(f"Error processing auction_date entry: {e} | value={ad}")
            
            if extracted_dates:
                latest_date = max(extracted_dates)
                print(f"Latest auction date resolved: {latest_date}")
                
                # 最新のオークション日を含むレコードにLIKEでフィルタ
                query = query.filter(Horse.auction_date.like(f"%{latest_date}%"))
                # 念のため、オークション日がNULLのレコードを除外
                query = query.filter(Horse.auction_date.isnot(None))
                
                # デバッグ用: フィルタリング後のクエリを表示
                print("\n=== Filtered Query (by latest_date LIKE) ===")
                print(str(query.statement.compile(compile_kwargs={"literal_binds": True})))
            else:
                print("Warning: No valid auction dates found in the database (after parsing)")
                return {"items": [], "total": 0}
        
        # 3. フィルタリング
        print("\n3. Applying filters...")
        if auction_date and not latest_auction_bool:
            print(f"- Filtering by auction_date: {auction_date}")
            # オークション日を部分一致で検索（JSON配列内のいずれかの要素と一致）
            query = query.filter(
                Horse.auction_date.like(f'%{auction_date}%')
            )
        
        # 4. 総レコード数の取得
        print("\n4. Getting total count...")
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
            print("\n=== 実行するSQLクエリ ===")
            print(str(query.statement.compile(compile_kwargs={"literal_binds": True})))
            
            horses = query.offset(skip).limit(limit).all()
            print(f"\n取得した馬の数: {len(horses)}頭")
            
            # 取得した馬の詳細を表示
            print("\n=== 取得した馬の一覧 ===")
            name_list = {}
            for i, horse in enumerate(horses, 1):
                name = horse.name
                name_list[name] = name_list.get(name, 0) + 1
                print("{0:3d}. ID: {1}, 馬名: {2}, 重複回数: {3}".format(
                    i, horse.id, name, name_list[name]))
            
            # 重複している馬名を表示
            final_duplicates = {name: count for name, count in name_list.items() if count > 1}
            if final_duplicates:
                print("\n!!! 最終結果に重複する馬名を検出 !!!")
                for name, count in final_duplicates.items():
                    print(f"- {name}: {count}回")
            else:
                print("\n最終結果に重複する馬名は見つかりませんでした。")
            # サービスでフロントエンド用の配列へ変換
            print("\n=== フロントエンド用データ変換前の馬一覧 ===")
            for i, horse in enumerate(horses, 1):
                print(f"{i:3d}. ID: {horse.id}, 馬名: {horse.name}, オークション日: {horse.auction_date}")
            
            # map_horses_listは (horses_data, auction_histories) のタプルを返す
            horses_data, auction_histories = map_horses_list(horses)
            
            print(f"\n=== フロントエンド用データ変換後 ===")
            print(f"変換された馬の数: {len(horses_data)}頭")
            print(f"オークション履歴の数: {len(auction_histories)}件")
            
            # 変換後のデータで重複をチェック
            if horses_data:
                converted_names = {}
                print("\n=== 変換後の馬一覧 ===")
                for i, horse in enumerate(horses_data, 1):
                    name = horse.get('name')
                    converted_names[name] = converted_names.get(name, 0) + 1
                    print("{0:3d}. ID: {1}, 馬名: {2}, 重複回数: {3}".format(
                        i, horse.get('id'), name, converted_names[name]))
                
                # 変換後の重複をチェック
                converted_duplicates = {name: count for name, count in converted_names.items() if count > 1}
                if converted_duplicates:
                    print("\n!!! 変換後のデータに重複する馬名を検出 !!!")
                    for name, count in converted_duplicates.items():
                        print(f"- {name}: {count}回")
                else:
                    print("\n変換後のデータに重複する馬名は見つかりませんでした。")
                
                # サンプルデータを表示
                print("\n=== サンプルデータ ===")
                sample = horses_data[0]
                print(f"  - ID: {sample.get('id')}")
                print(f"  - 馬名: {sample.get('name')}")
                print(f"  - 性別: {sample.get('sex')}")
                print(f"  - 父: {sample.get('sire')}")
                print(f"  - 母: {sample.get('dam')}")
                print(f"  - 母父: {sample.get('damsire')}")
                print(f"  - オークション日: {sample.get('auction_date')}")
                print(f"  - セール: {sample.get('auction')}")
                print(f"  - 落札価格: {sample.get('price')}")
                print(f"  - 馬主: {sample.get('owner')}")
                print(f"  - 調教師: {sample.get('trainer')}")
                print(f"  - 生産者: {sample.get('breeder')}")
        except Exception as e:
            print(f"Error fetching/processing horses: {str(e)}")
            import traceback
            print(traceback.format_exc())
            raise
        
        # 5. レスポンスの作成
        print("\n5. Creating response...")

        response = {
            "horses": horses_data,
            # 下位互換: camelCase と snake_case の両方を返す
            "auction_histories": auction_histories,
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
@router.get("/horses/{horse_id}", response_model=HorseResponse, deprecated=True)
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

    # 明示的に必要なフィールドをロード
    db.refresh(horse)
    
    # デバッグ用にレスポンスデータをログに出力
    import json
    logger.info(f"Horse data before serialization: {json.dumps({c.name: getattr(horse, c.name) for c in horse.__table__.columns}, default=str)}")
    
    # 正規化と辞書構築は専用サービスに委譲
    serialized = serialize_horse(horse)
    logger.info(f"Serialized horse data: {json.dumps(serialized, default=str)}")
    
    return serialized


# 新しい馬データを作成するためのモデル
class HorseCreate(BaseModel):
    name: str
    auction_id: str
    sex: Optional[str] = None
    age: Optional[int] = None
    sire: Optional[str] = None
    dam: Optional[str] = None
    damsire: Optional[str] = None
    weight: Optional[float] = None
    auction_date: Optional[str] = None
    seller: Optional[str] = None
    price: Optional[float] = None
    comment: Optional[str] = None
    disease_tags: Optional[str] = None
    detail_url: Optional[str] = None
    image_url: Optional[str] = None

@router.post("/horses", response_model=Dict[str, Any], status_code=201, tags=["horses"])
async def create_horse(
    horse: HorseCreate,
    db: Session = Depends(get_db)
):
    """新しい馬データを作成するエンドポイント"""
    try:
        logger.info(f"新しい馬データを作成します: {horse.name} (auction_id: {horse.auction_id})")
        
        # 既存の馬データを確認
        existing_horse = db.query(Horse).filter(
            Horse.auction_id == horse.auction_id
        ).first()
        
        if existing_horse:
            logger.info(f"既存の馬データが見つかりました: {horse.auction_id}")
            return {
                "status": "exists",
                "message": "既に存在する馬データです",
                "data": serialize_horse(existing_horse)
            }
        
        # 馬データの作成
        db_horse = Horse(
            name=horse.name,
            auction_id=horse.auction_id,
            sex=json.dumps([horse.sex]) if horse.sex else None,
            age=json.dumps([horse.age]) if horse.age is not None else None,
            sire=horse.sire,
            dam=horse.dam,
            dam_sire=getattr(horse, 'damsire', None),  # damsire が存在しない場合は None を設定
            weight=horse.weight,
            auction_date=json.dumps([horse.auction_date]) if horse.auction_date else None,
            seller=json.dumps([horse.seller]) if horse.seller else None,
            sold_price=json.dumps([horse.price]) if horse.price is not None else None,
            comment=json.dumps([horse.comment]) if horse.comment else None,
            disease_tags=horse.disease_tags,
            detail_url=horse.detail_url,
            image_url=horse.image_url,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_horse)
        db.commit()
        db.refresh(db_horse)
        
        logger.info(f"馬データを作成しました: {db_horse.id}")
        return {
            "status": "success",
            "message": "馬データを作成しました",
            "data": serialize_horse(db_horse)
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"馬データの作成中にエラーが発生しました: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"馬データの作成中にエラーが発生しました: {str(e)}"
        )
