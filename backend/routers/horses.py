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
from sqlalchemy import func, and_, or_

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

# サービスをインポート
from services.horses_list_mapper import map_horses_list

# ルーターの設定
router = APIRouter(tags=["horses"])

# 必要なモデルとスキーマのインポート
class DiseaseExtractionRequest(BaseModel):
    comment: str

# 疾病情報抽出モジュールを一時的に無効化
DiseaseInfoExtractor = None
logger.info("DiseaseInfoExtractor is temporarily disabled")

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
        
        # 1. 最新のオークション日を取得（horsesテーブルから直接取得）
        latest_date = db.query(
            func.max(Horse.auction_date)
        ).filter(
            Horse.auction_date.isnot(None)
        ).scalar()
        
        logger.info(f"Latest auction date from horses table: {latest_date}")
        
        # 念のため、AuctionHistoryテーブルからも最新日を取得して比較
        latest_from_auction = db.query(
            func.max(AuctionHistory.auction_date)
        ).scalar()
        
        logger.info(f"Latest auction date from auction_histories table: {latest_from_auction}")
        
        # より新しい日付を使用
        if latest_date is None or (latest_from_auction and latest_from_auction > latest_date):
            latest_date = latest_from_auction
            
        logger.info(f"Using latest auction date: {latest_date}")
        
        # 2. 馬の基本クエリを構築
        query = db.query(Horse)
        
        # 3. オークション日でフィルタリング
        if auction_date:
            query = query.filter(
                Horse.auction_date.like(f'%{auction_date}%')
            )
        
        # 4. 最新のオークション日でフィルタリング
        if latest_auction.lower() == 'true' and latest_date:
            # 最新のオークション日を直接指定してフィルタリング
            query = query.filter(
                or_(
                    Horse.auction_date == latest_date,
                    Horse.auction_date.like(f'%{latest_date}%')
                )
            )
            logger.info(f"Filtering by latest auction date: {latest_date} (exact or partial match)")
            
            # デバッグ用：フィルタリング対象の馬の数をログに出力
            count = query.count()
            logger.info(f"Found {count} horses with auction date matching: {latest_date}")
            
            # デバッグ用：実際の日付の一覧をログに出力
            dates = [r[0] for r in db.query(Horse.auction_date).distinct().all() if r[0]]
            logger.info(f"Distinct auction dates in database: {dates}")
        
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
            # race_record をパースして unified_race_records を設定
            is_unraced = False
            
            if horse.race_record:
                try:
                    # 文字列の場合はJSONとしてパース
                    if isinstance(horse.race_record, str):
                        if horse.race_record.strip() and horse.race_record.strip() != "未出走":
                            parsed_record = json.loads(horse.race_record)
                            
                            # 配列形式の場合は、配列の長さを総レース数として扱う
                            if isinstance(parsed_record, list):
                                total_races = len(parsed_record)
                                is_unraced = total_races == 0
                            # 辞書形式の場合は必要なフィールドを抽出
                            elif isinstance(parsed_record, dict):
                                # シンプル形式の場合はそのまま使用
                                if "formatted_record" in parsed_record:
                                    total_races = parsed_record.get("total_races", 0)
                                    is_unraced = total_races == 0
                                # 詳細形式の場合はシンプル形式に変換
                                elif "races" in parsed_record:
                                    total_races = parsed_record.get("races", 0)
                                    is_unraced = total_races == 0
                    # 文字列でない場合
                    elif isinstance(horse.race_record, dict):
                        record_dict = horse.race_record
                        if "formatted_record" in record_dict:
                            total_races = record_dict.get("total_races", 0)
                            is_unraced = total_races == 0
                        elif "races" in record_dict:
                            total_races = record_dict.get("races", 0)
                            is_unraced = total_races == 0
                except (json.JSONDecodeError, AttributeError, TypeError) as e:
                    logger.warning(f"Failed to parse race_record for horse {horse.id}: {e}")
                    is_unraced = False
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
                "unsold": horse.is_unsold if hasattr(horse, 'is_unsold') else False,
                "unified_race_records": is_unraced  # race_record に基づいて設定
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

@router.get("/latest", response_model=Dict[str, Any], tags=["horses"])
async def get_latest_horses(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    sort: str = 'price_desc',
    db: Session = Depends(get_db)
):
    """最新のオークションの馬一覧を取得するエンドポイント
    
    Args:
        skip: スキップするレコード数
        limit: 取得する最大レコード数
        sort: 並べ替え方法（'price_desc', 'price_asc', 'name_asc', 'name_desc'）
        
    Returns:
        最新のオークションに出品された馬の一覧
    """
    logger.info("Calling /horses/latest endpoint")
    return await get_horses(request, skip, limit, sort, None, 'true', db)

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

@router.post("", response_model=HorseResponse, status_code=status.HTTP_201_CREATED, tags=["horses"])
async def create_horse(
    horse_data: dict,
    db: Session = Depends(get_db)
):
    """新しい馬を登録するエンドポイント"""
    try:
        logger.info("=== Starting create_horse endpoint ===")
        logger.info(f"Request data: {json.dumps(horse_data, ensure_ascii=False, default=str)}")
        
        # 必須フィールドのチェック
        required_fields = ["name", "sex", "sire", "dam", "damsire"]
        missing_fields = [field for field in required_fields if field not in horse_data or not horse_data[field]]
        
        if missing_fields:
            error_msg = f"必須フィールドが不足しています: {', '.join(missing_fields)}"
            logger.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
            
        # フィールドの型チェック
        if not isinstance(horse_data.get("name"), str):
            error_msg = "nameは文字列である必要があります"
            logger.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # 既存の馬をチェック（名前で一意に特定）
        existing_horse = db.query(HorseModel).filter(
            HorseModel.name == horse_data["name"]
        ).first()
        
        if existing_horse:
            # 既存の馬を更新
            logger.info(f"Updating existing horse: {existing_horse.id}")
            for key, value in horse_data.items():
                setattr(existing_horse, key, value)
            existing_horse.scraped_at = datetime.utcnow()  # スクレイピング日時を更新
            db.commit()
            db.refresh(existing_horse)
            return existing_horse
        else:
            # 新しい馬を作成
            horse_data['scraped_at'] = datetime.utcnow()  # スクレイピング日時を設定
            db_horse = HorseModel(**horse_data)
            db.add(db_horse)
            db.commit()
            db.refresh(db_horse)
            logger.info(f"Created new horse with id: {db_horse.id}")
            return db_horse
            
    except HTTPException:
        raise
    except HTTPException as he:
        db.rollback()
        logger.error(f"HTTPエラーが発生しました: {str(he.detail)}", exc_info=True)
        raise he
    except Exception as e:
        db.rollback()
        error_msg = f"馬データの保存中に予期せぬエラーが発生しました: {str(e)}"
        logger.error(error_msg, exc_info=True)
        logger.error(f"エラーの種類: {type(e).__name__}")
        logger.error(f"エラーが発生したデータ: {json.dumps(horse_data, ensure_ascii=False, default=str)}")
        
        # データベースエラーの場合はより詳細な情報を提供
        if hasattr(e, 'orig') and hasattr(e.orig, 'pgerror'):
            error_msg += f"\nデータベースエラー: {e.orig.pgerror}"
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
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

# 既存のエンドポイントは既に統合済み

# 馬IDで検索するエンドポイント
@router.get("/{horse_id}", response_model=Dict[str, Any], tags=["horses"])
async def get_horse_by_id(
    horse_id: Annotated[int, Path(title="The ID of the horse to get", ge=1)],
    db: Session = Depends(get_db)
):
    """馬IDを指定して馬の詳細情報を取得するエンドポイント"""
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
        
        # race_record を取得してフォーマットを統一
        race_record = {
            "total_races": 0,
            "wins": 0,
            "record_format": "simple",
            "formatted_record": "未出走"
        }
        
        # race_records を取得（賞金情報など）
        race_records = {
            "total_prize_money": 0,
            "last_race_date": None,
            "last_prize_update": None
        }
        
        if hasattr(horse, 'race_record') and horse.race_record:
            try:
                # 文字列の場合はJSONとしてパース
                if isinstance(horse.race_record, str):
                    if horse.race_record.strip() and horse.race_record.strip() != "未出走":
                        parsed_record = json.loads(horse.race_record)
                        
                        # 配列形式の場合は、配列の長さを総レース数として扱う
                        if isinstance(parsed_record, list):
                            total_races = len(parsed_record)
                            wins = 0
                            
                            # 配列内の各レースから勝ち星をカウント
                            for race in parsed_record:
                                if isinstance(race, dict) and race.get('finish_position') == '1':
                                    wins += 1
                            
                            race_record = {
                                "total_races": total_races,
                                "wins": wins,
                                "record_format": "simple",
                                "formatted_record": f"{total_races}戦{wins}勝" if total_races > 0 else "未出走"
                            }
                        # 辞書形式の場合は必要なフィールドを抽出
                        elif isinstance(parsed_record, dict):
                            # シンプル形式の場合はそのまま使用
                            if "formatted_record" in parsed_record:
                                race_record = parsed_record
                            # 詳細形式の場合はシンプル形式に変換
                            elif "races" in parsed_record:
                                race_record = {
                                    "total_races": parsed_record.get("races", 0),
                                    "wins": parsed_record.get("wins", 0),
                                    "record_format": "simple",
                                    "formatted_record": f"{parsed_record.get('races', 0)}戦{parsed_record.get('wins', 0)}勝"
                                }
                # 文字列でない場合
                else:
                    record_dict = horse.race_record
                    if isinstance(record_dict, dict):
                        if "formatted_record" in record_dict:
                            race_record = record_dict
                        elif "races" in record_dict:
                            race_record = {
                                "total_races": record_dict.get("races", 0),
                                "wins": record_dict.get("wins", 0),
                                "record_format": "simple",
                                "formatted_record": f"{record_dict.get('races', 0)}戦{record_dict.get('wins', 0)}勝"
                            }
                            # 賞金情報があれば取得
                            if "total_prize_money" in record_dict:
                                race_records["total_prize_money"] = record_dict.get("total_prize_money", 0)
                            if "last_race_date" in record_dict:
                                race_records["last_race_date"] = record_dict.get("last_race_date")
                            if "last_prize_update" in record_dict:
                                race_records["last_prize_update"] = record_dict.get("last_prize_update")
            except (json.JSONDecodeError, AttributeError, TypeError) as e:
                logger.warning(f"Failed to parse race_record: {e}")
                race_record = {
                    "total_races": 0,
                    "wins": 0,
                    "record_format": "simple",
                    "formatted_record": "未出走"
                }
        
        # 未出走かどうかを示すフラグ
        # total_racesが0の場合はtrue、それ以外はfalse
        is_unraced = race_record.get("total_races", 0) == 0
        
        # 未出走フラグを設定（必ずboolean型で設定）
        unified_race_records = bool(is_unraced)
        
        # 馬の基本情報を返す
        response_data = {
            "id": horse.id,
            "name": horse.name,
            "sex": horse.sex,
            "age": horse.age,
            "sire": horse.sire,
            "dam": horse.dam,
            "dam_sire": horse.dam_sire,
            "weight": horse.weight,
            "total_prize_start": horse.total_prize_start,
            "total_prize_latest": horse.total_prize_latest,
            "sold_price": horse.sold_price,
            "auction_date": auction_date.isoformat() if hasattr(auction_date, 'isoformat') else auction_date,
            "seller": horse.seller,
            "disease_tags": horse.disease_tags,
            "comment": horse.comment,
            "image_url": horse.image_url,
            "detail_url": horse.detail_url,
            "jbis_url": horse.jbis_url,
            "is_unsold": getattr(horse, 'is_unsold', False),
            "race_record": race_record,  # 後方互換性のため残す
            "race_records": race_records,  # 後方互換性のため残す
            "unified_race_records": unified_race_records,  # 新しい統合形式
            "auction_histories": auction_histories_list,
            "latestAuction": latest_auction_dict
        }
        
        return response_data
    except Exception as e:
        db.rollback()
        logger.error(f"Error getting horse by ID: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting horse by ID: {str(e)}"
        )
