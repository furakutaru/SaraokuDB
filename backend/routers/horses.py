import json
import logging
import os
import re
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm import joinedload
from sqlalchemy import func, and_

# ロガーの初期化（最初に設定）
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# データベース関連のインポート
from backend.database import get_db
from backend.database.models import Horse, AuctionHistory
from backend.database.schemas import HorseResponse
from backend.services.horse_serializer import serialize_horse, _parse_first_int
from backend.services.horses_list_mapper import map_horses_list

# スクリプトのディレクトリをパスに追加
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
scripts_dir = os.path.join(project_root, 'scripts')
components_dir = os.path.join(project_root, 'scripts', 'components')
components_dir = os.path.join(scripts_dir, 'components')

# 必要なディレクトリをsys.pathに追加
for path in [project_root, scripts_dir, components_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)
        logger.info(f"Added to sys.path: {path}")

# 現在のPythonパスをログに出力
logger.info(f"Python path: {sys.path}")

# 疾病情報抽出モジュールを一時的に無効化
logger.info("DiseaseInfoExtractor is temporarily disabled")
DiseaseInfoExtractor = None

# ルーターの設定
# Vercelでは /api が自動的には付与されないため、完全なパスを指定する
router = APIRouter(prefix="/api", tags=["horses"])

class DiseaseExtractionRequest(BaseModel):
    comment: str

@router.post("/extract-disease-tags", tags=["horses"])
async def extract_disease_tags(
    request: Request,
    disease_request: DiseaseExtractionRequest,
    db: Session = Depends(get_db)
):
    """
    コメントから疾病タグを抽出するエンドポイント
    
    Args:
        disease_request: 抽出対象のコメントを含むリクエストボディ
        
    Returns:
        {
            "tags": List[str]  # 抽出された疾病タグのリスト
        }
    """
    if not DiseaseInfoExtractor:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DiseaseInfoExtractor could not be imported"
        )
    
    try:
        extractor = DiseaseInfoExtractor(logger=logger)
        result = extractor.extract(disease_request.comment)
        return {"tags": result.get("diseases", [])}
    except Exception as e:
        logger.error(f"Error extracting disease tags: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting disease tags: {str(e)}"
        )

@router.get("/latest", response_model=Dict[str, Any], tags=["horses"])
async def get_latest_horses(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """最新のオークションの馬一覧を取得するエンドポイント"""
    logger.info("Calling /horses/latest endpoint")
    return await get_horses(request, skip, limit, None, 'true', db)

@router.get("/horses/with_auction_histories", response_model=Dict[str, Any], tags=["horses"])
async def get_horses_with_auction_histories(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    馬の一覧をオークション履歴と一緒に取得するエンドポイント
    N+1問題を解消するために、オークション履歴を一括で取得する
    
    Args:
        skip: スキップするレコード数
        limit: 取得する最大レコード数
        
    Returns:
        {
            "horses": List[Dict],  # 馬のリスト
            "auction_histories": List[Dict],  # オークション履歴のリスト
            "metadata": {
                "total": int,     # 総レコード数
                "skip": int,      # スキップ数
                "limit": int      # リミット数
            }
        }
    """
    try:
        logger.info("\n=== Starting get_horses_with_auction_histories endpoint ===")
        
        # 総レコード数を取得
        total = db.query(Horse).count()
        
        # 馬データを取得（ページネーション適用）
        horses = db.query(Horse).order_by(Horse.id).offset(skip).limit(limit).all()
        
        # マッパー関数でデータを変換
        horses_data, auction_histories = map_horses_list(horses)
        
        logger.info(f"Processed {len(horses_data)} horses and {len(auction_histories)} auction histories")
        
        return {
            "horses": horses_data,
            "auction_histories": auction_histories,
            "metadata": {
                "total": total,
                "skip": skip,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_horses_with_auction_histories: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/horses", response_model=Dict[str, Any], tags=["horses"])
async def get_horses(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    auction_date: Optional[str] = None,
    latest_auction: str = 'false',  # デフォルトですべての馬を表示
    include_latest_auction: str = 'true',  # 最新のオークション情報を含める
    db: Session = Depends(get_db)
):
    """馬の一覧を取得するエンドポイント
    
    Args:
        skip: スキップするレコード数
        limit: 取得する最大レコード数
        auction_date: オークション日でフィルタリング（部分一致）
        latest_auction: 'true'の場合、最新のオークション日でフィルタリング
        include_latest_auction: 'true'の場合、最新のオークション情報を含める
        
    Returns:
        {
            "horses": List[Dict],  # 馬のリスト
            "metadata": {
                "total": int,     # 総レコード数
                "skip": int,      # スキップ数
                "limit": int      # リミット数
            }
        }
    """
    try:
        logger.info("\n=== Starting get_horses endpoint ===")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Query params: {request.query_params}")
        logger.info(f"latest_auction: {latest_auction}, type: {type(latest_auction)}")
        
        # Horse モデルの属性を確認
        logger.info(f"Horse model attributes: {dir(Horse)}")
        logger.info(f"Horse model __table__: {Horse.__table__.columns.keys() if hasattr(Horse, '__table__') else 'No __table__ attribute'}")
        if hasattr(Horse, 'latest_auction'):
            logger.info("Horse model has 'latest_auction' attribute")
        else:
            logger.error("Horse model does NOT have 'latest_auction' attribute")
        
        latest_auction_bool = latest_auction.lower() == 'true' or request.query_params.get('latest_auction', '').lower() == 'true'
        
        # クエリオブジェクトの初期化
        try:
            # まずリレーションが存在するか確認
            if hasattr(Horse, 'latest_auction'):
                query = db.query(Horse).options(
                    joinedload(Horse.latest_auction)
                )
                logger.info("Query created with latest_auction relation")
            else:
                query = db.query(Horse)
                logger.info("Query created without latest_auction relation")
                
            # リレーションが正しくロードされているか確認
            logger.info(f"Horse model attributes: {dir(Horse)}")
            logger.info(f"Horse model relationships: {Horse.__mapper__.relationships.keys()}")
                
        except Exception as e:
            logger.error(f"Error creating query: {str(e)}")
            # エラーが発生した場合はリレーションをロードせずにクエリを作成
            query = db.query(Horse)
            logger.info("Created fallback query without relations")
        
        # 1. 最新のオークション日を取得（必要な場合）
        latest_date = None
        if latest_auction_bool:
            logger.info("Getting latest auction date from auction_histories table...")
            
            # 最新のオークション日を直接取得
            latest_date_result = db.query(
                func.max(AuctionHistory.auction_date)
            ).scalar()
            
            if latest_date_result:
                latest_date = latest_date_result
                logger.info(f"Latest auction date from auction_histories: {latest_date}")
                
                # 最新のオークション日を含む馬を取得
                query = query.join(
                    AuctionHistory, 
                    Horse.id == AuctionHistory.horse_id
                ).filter(
                    AuctionHistory.auction_date == latest_date
                ).distinct()
                
                logger.info(f"Query after filtering by latest auction date: {query}")
            else:
                logger.warning("No auction dates found in auction_histories table")
                return {"horses": [], "metadata": {"total": 0, "skip": skip, "limit": limit}}
        
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
            # 最新のオークション情報を含める場合
            if include_latest_auction.lower() == 'true':
                query = query.options(
                    joinedload(Horse.latest_auction)
                )
            
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
                
                # 最新のオークション情報を表示（デバッグ用）
                if hasattr(horse, 'latest_auction') and horse.latest_auction:
                    auction = horse.latest_auction
                    print(f"    最新オークション: 日付={auction.auction_date}, 価格={auction.price}, 未売れ={auction.is_unsold}")
            
            # 重複している馬名を表示
            final_duplicates = {name: count for name, count in name_list.items() if count > 1}
            if final_duplicates:
                print("\n!!! 最終結果に重複する馬名を検出 !!!")
                for name, count in final_duplicates.items():
                    print(f"- {name}: {count}回")
            else:
                print("\n最終結果に重複する馬名は見つかりませんでした。")
                
            # フロントエンド用データ変換
            print("\n=== フロントエンド用データ変換前の馬一覧 ===")
            for i, horse in enumerate(horses, 1):
                print(f"{i:3d}. ID: {horse.id}, 馬名: {horse.name}")
            
            # 最新のオークション情報を含めてシリアライズ
            include_auction = include_latest_auction.lower() == 'true'
            horses_data = []
            for horse in horses:
                # 明示的にリレーションをロード
                if hasattr(horse, 'latest_auction') and horse.latest_auction is not None:
                    # リレーションが既にロードされていることを確認
                    _ = horse.latest_auction.id
                horses_data.append(serialize_horse(horse, include_auction=include_auction))
            auction_histories = []  # 互換性のため空のリストを設定
                
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
        
        # フロントエンドが期待する形式に合わせてレスポンスを整形
        response = {
            "horses": horses_data if 'horses_data' in locals() else [],
            "auction_histories": auction_histories if 'auction_histories' in locals() else [],
            "metadata": {
                "total": total_count if 'total_count' in locals() else 0,
                "skip": skip,
                "limit": limit,
                "last_updated": datetime.utcnow().isoformat()
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
    
    # disease_tags のデバッグログ
    logger.info(f"Horse disease_tags raw: {getattr(horse, 'disease_tags', None)}")
    
    # 正規化と辞書構築は専用サービスに委譲
    serialized = serialize_horse(horse)
    
    # シリアライズ後の disease_tags をログに出力
    logger.info(f"Serialized horse data with disease_tags: {json.dumps(serialized.get('disease_tags'), default=str)}")
    logger.info(f"Full serialized horse data: {json.dumps(serialized, default=str, ensure_ascii=False, indent=2)}")
    
    return serialized


# 新しい馬データを作成するためのモデル
class RaceRecord(BaseModel):
    race_name: Optional[str] = None
    race_date: Optional[str] = None
    course: Optional[str] = None
    distance: Optional[str] = None
    track_condition: Optional[str] = None
    finish_position: Optional[str] = None
    margin: Optional[str] = None
    jockey: Optional[str] = None
    weight: Optional[str] = None
    finish_time: Optional[str] = None
    odds: Optional[str] = None
    favorite: Optional[str] = None
    race_class: Optional[str] = None
    race_condition: Optional[str] = None
    prize_money: Optional[str] = None

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
    race_records: List[RaceRecord] = []

@router.post("/horses", response_model=HorseResponse, status_code=status.HTTP_201_CREATED)
async def create_horse(
    request: Request,
    horse: HorseCreate,
    db: Session = Depends(get_db)
):
    """新しい馬データを作成するエンドポイント"""
    try:
        # リクエスト情報をログに出力
        client_host = request.client.host if request.client else "unknown"
        logger.info(f"新しい馬データのリクエストを受け付けました (クライアント: {client_host})")
        logger.info(f"馬名: {horse.name}, オークションID: {horse.auction_id}")
        
        # リクエストボディをデバッグログに出力
        logger.debug(f"リクエストヘッダー: {dict(request.headers)}")
        logger.debug(f"リクエストボディ: {json.dumps(horse.dict(), ensure_ascii=False, indent=2)}")
        
        # 必須フィールドのバリデーション
        if not horse.name or not horse.auction_id:
            error_msg = "必須フィールドが不足しています: name と auction_id は必須です"
            logger.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
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
