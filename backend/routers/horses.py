import json
import logging
import os
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any
from typing_extensions import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body, Path
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_

# ロガーの設定
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# データベース関連のインポート
from database import get_db
from database.models import Horse, AuctionHistory, Horse as HorseModel
from database.schemas import HorseResponse, HorseCreate

# ルーターの設定
router = APIRouter(tags=["horses"])

# 必要なモデルとスキーマのインポート
class DiseaseExtractionRequest(BaseModel):
    comment: str

@router.get("", response_model=Dict[str, Any], tags=["horses"])
async def get_horses(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    sort: str = 'price_desc',
    auction_date: Optional[str] = None,
    latest_auction: str = 'false',
    include_latest_auction: str = 'true',
    db: Session = Depends(get_db)
):
    """
    馬の一覧を取得するエンドポイント
    
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
        
        # 2. 馬の基本クエリを構築
        query = db.query(Horse)
        
        # 3. オークション日でフィルタリング
        if auction_date:
            query = query.filter(
                Horse.auction_date.like(f'%{auction_date}%')
            )
        
        # 4. 最新のオークション日でフィルタリング
        if latest_auction.lower() == 'true' and latest_date:
            query = query.filter(
                Horse.auction_date.like(f'%{latest_date}%')
            )
        
        # 5. ソートを適用
        if sort == 'price_desc':
            query = query.order_by(Horse.sold_price.desc())
        elif sort == 'price_asc':
            query = query.order_by(Horse.sold_price.asc())
        elif sort == 'name_asc':
            query = query.order_by(Horse.name.asc())
        elif sort == 'name_desc':
            query = query.order_by(Horse.name.desc())
        else:
            # デフォルトは価格の降順
            query = query.order_by(Horse.sold_price.desc())
        
        # 6. ページネーションを適用
        total = query.count()
        horses = query.offset(skip).limit(limit).all()
        
        # 7. 結果をシリアライズ
        horses_data = []
        for horse in horses:
            horse_data = {
                "id": horse.id,
                "name": horse.name,
                "sex": horse.sex,
                "age": horse.age,
                "sire": horse.sire,
                "dam": horse.dam,
                "dam_sire": horse.dam_sire,
                "race_record": horse.race_record or "未出走",
                "weight": horse.weight,
                "total_prize_start": horse.total_prize_start,
                "total_prize_latest": horse.total_prize_latest,
                "sold_price": horse.sold_price,
                "auction_date": horse.auction_date,
                "seller": horse.seller,
                "disease_tags": horse.disease_tags,
                "comment": horse.comment,
                "image_url": horse.image_url,
                "detail_url": horse.detail_url,
                "jbis_url": horse.jbis_url,
                "is_unsold": horse.is_unsold if hasattr(horse, 'is_unsold') else False,
                "unsold": horse.is_unsold if hasattr(horse, 'is_unsold') else False
            }
            horses_data.append(horse_data)
        
        logger.info(f"Retrieved {len(horses_data)} horses (skip: {skip}, limit: {limit})")
        
        # 8. 結果を返す
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting horses: {str(e)}"
        )

@router.post("", response_model=HorseResponse, status_code=status.HTTP_201_CREATED, tags=["horses"])
async def create_horse(
    horse_data: dict,
    db: Session = Depends(get_db)
):
    """新しい馬を登録するエンドポイント"""
    try:
        logger.info(f"Creating new horse with data: {horse_data}")
        
        # 必須フィールドのチェック
        required_fields = ["name", "sex", "color", "birth_date", "sire", "dam"]
        for field in required_fields:
            if field not in horse_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # 既存の馬をチェック（名前と誕生日で一意に特定）
        existing_horse = db.query(HorseModel).filter(
            HorseModel.name == horse_data["name"],
            HorseModel.birth_date == horse_data["birth_date"]
        ).first()
        
        if existing_horse:
            # 既存の馬を更新
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
                results.append({
                    "status": "success", 
                    "data": {
                        "id": result.id,
                        "name": result.name,
                        "birth_date": result.birth_date
                    }
                })
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

# 既存のエンドポイントをインポート
from .horses_old import (
    get_horse_by_id,
    get_latest_horses,
    get_horses_with_auction_histories,
    extract_disease_tags
)
