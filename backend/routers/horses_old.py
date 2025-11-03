import json
import logging
import os
import re
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any
from typing_extensions import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body, Path
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from typing import List

# ロガーの設定
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# データベース関連のインポート
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from database import get_db
from database.models import Horse, AuctionHistory, Horse as HorseModel
from database.schemas import HorseResponse, HorseCreate
from services.horse_serializer import serialize_horse, _parse_first_int
from services.horses_list_mapper import map_horses_list

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
router = APIRouter(tags=["horses"])

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

@router.get("/with_auction_histories", response_model=Dict[str, Any], tags=["horses"])
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

@router.get("", response_model=Dict[str, Any], tags=["horses"])
async def get_horses(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    sort: str = 'price_desc',  # デフォルトは価格の降順
    auction_date: Optional[str] = None,
    latest_auction: str = 'false',  # デフォルトですべての馬を表示
    include_latest_auction: str = 'true',  # 最新のオークション情報を含める
    db: Session = Depends(get_db)
):
    """馬の一覧を取得するエンドポイント
    
    Args:
        skip: スキップするレコード数
        limit: 取得する最大レコード数
        sort: 並べ替え方法
            - 'price_desc': 価格の高い順
            - 'price_asc': 価格の安い順
            - 'name_asc': 名前順 (A-Z)
            - 'name_desc': 名前順 (Z-A)
        auction_date: オークション日でフィルタリング（部分一致）
        latest_auction: 'true'の場合、最新のオークション日でフィルタリング
        include_latest_auction: 'true'の場合、最新のオークション情報を含める
        
    Returns:
        {
            "horses": List[Dict],  # 馬のリスト（重複なし、各馬の最新オークション情報）
            "metadata": {
                "total": int,     # 総レコード数
                "skip": int,      # スキップ数
                "limit": int,     # リミット数
                "last_updated": str  # 最終更新日時
        }
    """
    try:
        logger.info("\n=== Starting get_horses endpoint ===")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Query params: {request.query_params}")
        
        # 1. 最新のオークション日を取得
        latest_date = db.query(
            func.max(AuctionHistory.auction_date)
        ).scalar()
        
        # 1. ベースクエリを作成
        query = db.query(Horse)
        
        # 最新のオークション情報を取得するための辞書を初期化
        latest_auctions = {}
        if include_latest_auction.lower() == 'true':
            # 最新のオークション情報を一括で取得
            from sqlalchemy import func
            from database.models import AuctionHistory
            
            # 各馬の最新のオークションIDを取得
            subq = db.query(
                AuctionHistory.horse_id,
                func.max(AuctionHistory.id).label('max_id')
            ).group_by(AuctionHistory.horse_id).subquery()
            
            # 最新のオークション情報を取得
            latest_auction_records = db.query(AuctionHistory).join(
                subq,
                (AuctionHistory.horse_id == subq.c.horse_id) & 
                (AuctionHistory.id == subq.c.max_id)
            ).all()
            
            # 辞書に格納
            latest_auctions = {ah.horse_id: ah for ah in latest_auction_records}
        
        # 2. オークション日でフィルタリング
        if auction_date:
            query = query.filter(Horse.auction_date.contains(auction_date))
        
        # 4. 最新のオークション日でフィルタリング
        if latest_auction.lower() == 'true' and latest_date:
            query = query.filter(Horse.auction_date == latest_date)
        
        # 5. ソート順を適用
        if sort == 'price_desc':
            query = query.order_by(Horse.sold_price.desc())
        elif sort == 'price_asc':
            query = query.order_by(Horse.sold_price.asc())
        elif sort == 'name_asc':
            query = query.order_by(Horse.name.asc())
        elif sort == 'name_desc':
            query = query.order_by(Horse.name.desc())
        else:  # デフォルトは価格の降順
            query = query.order_by(Horse.sold_price.desc())
        
        # 6. 総レコード数を取得
        total = query.count()
        
        # 7. ページネーションを適用
        horses = query.offset(skip).limit(limit).all()
        
        # 8. シリアライズ
        horses_data = []
        if include_latest_auction.lower() == 'true':
            # 最新のオークション情報を含める場合
            for horse in horses:
                horse_dict = serialize_horse(horse)
                if hasattr(horse, 'id') and horse.id in latest_auctions:
                    ah = latest_auctions[horse.id]
                    horse_dict['latest_auction'] = {
                        'price': ah.price,
                        'auction_date': ah.auction_date.isoformat() if hasattr(ah.auction_date, 'isoformat') else ah.auction_date,
                        'seller': ah.seller,
                        'buyer': ah.buyer,
                        'auction_house': ah.auction_house,
                        'auction_name': ah.auction_name,
                        'lot_number': ah.lot_number,
                        'auction_url': ah.auction_url,
                        'is_unsold': getattr(ah, 'is_unsold', False)
                    }
                horses_data.append(horse_dict)
        else:
            # 最新のオークション情報を含めない場合
            horses_data = [serialize_horse(horse) for horse in horses]
        
        logger.info(f"Retrieved {len(horses_data)} horses (skip: {skip}, limit: {limit})")
        
        return {
            "horses": horses_data,
            "metadata": {
                "total": total,
                "skip": skip,
                "limit": limit,
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error in get_horses: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving horses: {str(e)}"
        )


@router.post("", response_model=HorseResponse, status_code=status.HTTP_201_CREATED, tags=["horses"])
async def create_horse(
    horse_data: dict,
    db: Session = Depends(get_db)
):
    """新しい馬を登録するエンドポイント"""
    try:
        # 馬の作成処理
        logger.info(f"Creating new horse with data: {horse_data}")
        
        # 必須フィールドのバリデーション
        required_fields = ["name", "sex", "color", "birth_date", "sire", "dam"]
        for field in required_fields:
            if field not in horse_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # 既存の馬をチェック
        existing_horse = db.query(HorseModel).filter(
            HorseModel.name == horse_data["name"],
            HorseModel.birth_date == horse_data["birth_date"]
        ).first()
        
        if existing_horse:
            # 既存の馬の情報を更新
            logger.info(f"Updating existing horse: {existing_horse.id}")
            for key, value in horse_data.items():
                setattr(existing_horse, key, value)
            db.commit()
            db.refresh(existing_horse)
            return existing_horse
        else:
            # 新しい馬を作成
            db_horse = HorseModel(**horse_data)
            db.add(db_horse)
            db.commit()
            db.refresh(db_horse)
            logger.info(f"Created new horse with id: {db_horse.id}")
            return db_horse
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating/updating horse: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating/updating horse: {str(e)}"
        )

@router.post("/batch", status_code=status.HTTP_201_CREATED, tags=["horses"])
async def create_horses_batch(
    horses_data: List[dict],
    db: Session = Depends(get_db)
):
    """複数の馬を一括で登録・更新するエンドポイント"""
    try:
        results = []
        for horse_data in horses_data:
            try:
                # 個別の馬を登録・更新
                result = await create_horse(horse_data, db)
                results.append({"status": "success", "data": result})
            except Exception as e:
                results.append({
                    "status": "error",
                    "error": str(e),
                    "data": horse_data
                })
        
        return {
            "total": len(horses_data),
            "success": sum(1 for r in results if r["status"] == "success"),
            "errors": sum(1 for r in results if r["status"] == "error"),
            "results": results
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in batch create: {str(e)}"
        )

def convert_auction_history_to_dict(ah):
    """AuctionHistoryオブジェクトを辞書に変換するヘルパー関数"""
    if not ah:
        return None
    return {
        'id': ah.id,
        'horse_id': ah.horse_id,
        'horse_name': ah.horse_name,
        'sire_name': ah.sire_name,
        'dam_name': ah.dam_name,
        'damsire_name': ah.damsire_name,
        'auction_date': ah.auction_date.isoformat() if ah.auction_date else None,
        'price': ah.price,
        'seller': ah.seller,
        'buyer': ah.buyer,
        'auction_house': ah.auction_house,
        'auction_name': ah.auction_name,
        'lot_number': ah.lot_number,
        'auction_url': ah.auction_url,
        'is_unsold': ah.is_unsold,
        'created_at': ah.created_at.isoformat() if ah.created_at else None,
        'updated_at': ah.updated_at.isoformat() if ah.updated_at else None,
        'scraped_at': ah.scraped_at.isoformat() if ah.scraped_at else None,
        'user_id': ah.user_id
    }

@router.get("/{horse_id}", response_model=Dict[str, Any], tags=["horses"])
async def get_horse_by_id(
    horse_id: Annotated[int, Path(title="The ID of the horse to get", ge=1)],
    db: Session = Depends(get_db)
):
    logger.info(f"\n=== Starting get_horse_by_id endpoint for horse_id: {horse_id} ===")
    
    try:
        # 馬の基本情報を取得
        horse = db.query(Horse).filter(Horse.id == horse_id).first()
        if not horse:
            raise HTTPException(status_code=404, detail="Horse not found")
        
        # オークション履歴を取得（最新のものから順に）
        auction_histories = db.query(AuctionHistory).filter(
            AuctionHistory.horse_id == horse_id
        ).order_by(AuctionHistory.auction_date.desc()).all()
        
        # オークション履歴を辞書に変換するヘルパー関数
        def serialize_auction_history(ah):
            if ah is None:
                return None
                
            # 日付フィールドをISOフォーマットに変換するヘルパー関数
            def safe_isoformat(dt):
                if dt is None:
                    return None
                if hasattr(dt, 'isoformat'):
                    return dt.isoformat()
                return str(dt) if dt else None
                
            return {
                'id': getattr(ah, 'id', None),
                'horse_id': getattr(ah, 'horse_id', None),
                'horse_name': getattr(ah, 'horse_name', None),
                'sire_name': getattr(ah, 'sire_name', None),
                'dam_name': getattr(ah, 'dam_name', None),
                'damsire_name': getattr(ah, 'damsire_name', None),
                'auction_date': safe_isoformat(getattr(ah, 'auction_date', None)),
                'price': getattr(ah, 'price', None),
                'seller': getattr(ah, 'seller', None),
                'buyer': getattr(ah, 'buyer', None),
                'auction_house': getattr(ah, 'auction_house', None),
                'auction_name': getattr(ah, 'auction_name', None),
                'lot_number': getattr(ah, 'lot_number', None),
                'auction_url': getattr(ah, 'auction_url', None),
                'is_unsold': getattr(ah, 'is_unsold', False),
                'created_at': safe_isoformat(getattr(ah, 'created_at', None)),
                'updated_at': safe_isoformat(getattr(ah, 'updated_at', None)),
                'scraped_at': safe_isoformat(getattr(ah, 'scraped_at', None)),
                'user_id': getattr(ah, 'user_id', None)
            }
        
        # オークション履歴をシリアライズ
        auction_histories_list = [serialize_auction_history(ah) for ah in auction_histories]
        
        # 最新のオークション情報を取得（存在する場合）
        latest_auction_dict = auction_histories_list[0] if auction_histories_list else None
        
        # auction_date をパース
        auction_date = None
        if hasattr(horse, 'auction_date') and horse.auction_date:
            try:
                if isinstance(horse.auction_date, str):
                    parsed_dates = json.loads(horse.auction_date)
                    if isinstance(parsed_dates, list) and len(parsed_dates) > 0:
                        auction_date = parsed_dates[0]  # 最初の日付を取得
                else:
                    auction_date = horse.auction_date
            except (json.JSONDecodeError, TypeError, AttributeError) as e:
                logger.warning(f"Failed to parse auction_date: {e}")
                auction_date = horse.auction_date
        
        # 日付フィールドをISOフォーマットに変換するヘルパー関数
        def safe_isoformat(dt):
            if dt is None:
                return None
            if hasattr(dt, 'isoformat'):
                return dt.isoformat()
            return str(dt) if dt else None
        
        # race_record を取得
        race_record = "未出走"
        if hasattr(horse, 'race_record') and horse.race_record:
            try:
                if isinstance(horse.race_record, str):
                    if horse.race_record.strip().startswith('{') or horse.race_record.strip().startswith('['):
                        race_record = json.loads(horse.race_record)
                    else:
                        race_record = horse.race_record
                else:
                    race_record = horse.race_record
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"Failed to parse race_record: {e}")
                race_record = str(horse.race_record) if horse.race_record else "未出走"
                
        # 日付フィールドをISOフォーマットに変換するヘルパー関数
        def safe_isoformat(dt):
            if dt is None:
                return None
            if hasattr(dt, 'isoformat'):
                return dt.isoformat()
            return str(dt) if dt else None
            
        # レスポンスを構築
        response = {
            "id": horse.id,
            "name": horse.name,
            "sex": getattr(horse, 'sex', None),
            "age": getattr(horse, 'age', None),
            "sire": getattr(horse, 'sire', None),
            "dam": getattr(horse, 'dam', None),
            "dam_sire": getattr(horse, 'dam_sire', None),
            "race_record": race_record,
            "weight": getattr(horse, 'weight', None),
            "total_prize_start": getattr(horse, 'total_prize_start', None),
            "total_prize_latest": getattr(horse, 'total_prize_latest', None),
            "prize_money": getattr(horse, 'prize_money', None),
            "sold_price": getattr(horse, 'sold_price', None),
            "auction_date": safe_isoformat(auction_date) if auction_date else None,
            "disease_tags": getattr(horse, 'disease_tags', None),
            "seller": getattr(horse, 'seller', None),
            "comment": getattr(horse, 'comment', None),
            "image_url": getattr(horse, 'image_url', None),
            "primary_image": getattr(horse, 'primary_image', None),
            "jbis_url": getattr(horse, 'jbis_url', None),
            "detail_url": getattr(horse, 'detail_url', None),
            "unsold_count": getattr(horse, 'unsold_count', 0),
            "bid_count": getattr(horse, 'bid_count', 0),
            "created_at": safe_isoformat(getattr(horse, 'created_at', None)),
            "updated_at": safe_isoformat(getattr(horse, 'updated_at', None)),
            "scraped_at": safe_isoformat(getattr(horse, 'scraped_at', None)),
            "is_unsold": getattr(horse, 'is_unsold', False),
            "auction_histories": auction_histories_list,
            "latest_auction": latest_auction_dict,
            "latest_auction_id": getattr(horse, 'latest_auction_id', None),
            "owner_id": getattr(horse, 'owner_id', None)
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in batch create: {str(e)}"
        )
