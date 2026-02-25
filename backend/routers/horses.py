import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from typing_extensions import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body, Path
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, cast
from sqlalchemy.types import Integer, Float

# ロガーの設定
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# データベース関連のインポート
from database import get_db
from database.models import Horse, AuctionHistory, HorsePrizeHistory, Horse as HorseModel
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

MIN_PRIZE_UPDATE_AGE_DAYS = 90
PRIZE_UPDATE_FETCH_MULTIPLIER = 5


def _extract_latest_history_value(raw_value):
    """履歴カラム（JSON文字列/配列）から最新値を取得"""
    if raw_value is None:
        return None

    if isinstance(raw_value, list):
        return raw_value[-1] if raw_value else None

    if isinstance(raw_value, dict):
        return raw_value.get('auction_date') or raw_value.get('date') or raw_value.get('value')

    if isinstance(raw_value, str):
        stripped = raw_value.strip()
        if not stripped:
            return None
        if stripped.startswith('[') or stripped.startswith('{'):
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, list) and parsed:
                    return parsed[-1]
                if isinstance(parsed, dict):
                    return parsed.get('auction_date') or parsed.get('date') or parsed.get('value')
            except json.JSONDecodeError:
                return stripped
        return stripped

    return raw_value


def _parse_latest_auction_date(raw_value):
    """auction_date の履歴から最新日付を datetime.date で返す"""
    latest_value = _extract_latest_history_value(raw_value)
    if not latest_value:
        return None

    if isinstance(latest_value, dict):
        latest_value = latest_value.get('auction_date') or latest_value.get('date')

    if latest_value is None:
        return None

    latest_str = str(latest_value).strip()
    if not latest_str:
        return None

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d"):
        try:
            return datetime.strptime(latest_str[:10], fmt).date()
        except ValueError:
            continue
    return None


def _is_next_update_due(horse, now_utc: datetime) -> bool:
    due = getattr(horse, "next_update_due_date", None)
    if due is None:
        return True
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)
    return due <= now_utc


def _should_include_in_prize_batch(horse, now_utc: datetime) -> bool:
    if getattr(horse, "is_retired", False):
        return False
    if not _is_next_update_due(horse, now_utc):
        return False

    latest_auction_date = _parse_latest_auction_date(getattr(horse, "auction_date", None))
    if latest_auction_date is None:
        return True

    min_date = now_utc.date() - timedelta(days=MIN_PRIZE_UPDATE_AGE_DAYS)
    return latest_auction_date <= min_date


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

# 部分更新用のPATCHエンドポイント（PUTと同等のallowed_fieldsで部分更新）
@router.patch("/{horse_id}", tags=["horses"])
async def patch_horse(
    horse_id: Annotated[int, Path(title="The ID of the horse to update", ge=1)],
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """馬の情報を部分更新するエンドポイント（PATCH）

    許可されたフィールドのみ更新します。
    """
    try:
        horse = db.query(Horse).filter(Horse.id == horse_id).first()
        if not horse:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Horse not found")

        allowed_fields = {
            "current_prize",
            "last_prize_update",
            "update_interval_months",
            "is_retired",
            "raw_name",
            "is_broodmare",
            "next_update_due_date",
            "total_prize_latest",
        }

        updated = False
        for key, value in payload.items():
            if key in allowed_fields:
                setattr(horse, key, value)
                updated = True

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="更新可能なフィールドが含まれていません"
            )

        db.commit()
        db.refresh(horse)

        return {
            "id": horse.id,
            "raw_name": getattr(horse, "raw_name", None),
            "current_prize": getattr(horse, "current_prize", None),
            "last_prize_update": getattr(horse, "last_prize_update", None),
            "update_interval_months": getattr(horse, "update_interval_months", None),
            "is_retired": getattr(horse, "is_retired", None),
            "is_broodmare": getattr(horse, "is_broodmare", None),
            "next_update_due_date": getattr(horse, "next_update_due_date", None),
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error patching horse: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error patching horse: {str(e)}"
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
    id: Optional[int] = None,
    q: Optional[str] = None,
    sex: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    min_weight: Optional[int] = None,
    max_weight: Optional[int] = None,
    min_roi: Optional[float] = None,
    max_roi: Optional[float] = None,
    needs_prize_update: bool = False,
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
        
        needs_prize_update_flag = bool(needs_prize_update)
        now_utc = datetime.now(timezone.utc)

        # 3. オークション日でフィルタリング
        if auction_date:
            query = query.filter(
                Horse.auction_date.like(f'%{auction_date}%')
            )
        
        # 3.5 IDでフィルタリング（完全一致）
        if id is not None:
            query = query.filter(Horse.id == id)

        # 3.6 クイック検索（部分一致: name/sire/dam/dam_sire）
        if q:
            like = f"%{q}%"
            query = query.filter(
                or_(
                    Horse.name.like(like),
                    Horse.sire.like(like),
                    Horse.dam.like(like),
                    Horse.dam_sire.like(like)
                )
            )

        # 3.7 性別フィルタ（カンマ区切りで複数指定可。例: sex=牡,牝,セ）
        if sex:
            try:
                sexes = [s.strip() for s in sex.split(',') if s.strip()]
                if sexes:
                    query = query.filter(Horse.sex.in_(sexes))
            except Exception:
                pass

        # 3.8 年齢レンジ
        # 年齢は文字列空値が含まれる可能性があるため空文字をNULL化してからCAST
        age_num = cast(func.nullif(Horse.age, ''), Integer)
        if min_age is not None:
            query = query.filter(age_num >= int(min_age))
        if max_age is not None:
            query = query.filter(age_num <= int(max_age))

        # 3.9 価格レンジ
        # 価格も空文字があり得るためNULL化してからCAST
        price_num = cast(func.nullif(Horse.sold_price, ''), Float)
        if min_price is not None:
            query = query.filter(price_num >= float(min_price))
        if max_price is not None:
            query = query.filter(price_num <= float(max_price))

        # 3.10 体重レンジ
        # 体重も空文字をNULL化
        weight_num = cast(func.nullif(Horse.weight, ''), Float)
        if min_weight is not None:
            query = query.filter(weight_num >= float(min_weight))
        if max_weight is not None:
            query = query.filter(weight_num <= float(max_weight))

        # 3.11 ROIレンジ（(total_prize_latest - total_prize_start) * 10000 / sold_price）
        if min_roi is not None or max_roi is not None:
            earned = (cast(Horse.total_prize_latest, Float) - cast(Horse.total_prize_start, Float))
            pricef = cast(Horse.sold_price, Float)
            query = query.filter(pricef.isnot(None), pricef > 0)
            if min_roi is not None:
                query = query.filter((earned * 10000.0) / pricef >= float(min_roi))
            if max_roi is not None:
                query = query.filter((earned * 10000.0) / pricef <= float(max_roi))

        if needs_prize_update_flag:
            query = query.filter(
                Horse.is_retired.is_(False),
                or_(
                    Horse.next_update_due_date.is_(None),
                    Horse.next_update_due_date <= now_utc
                )
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
        
        # 6. 重複（同一馬名）の除去をDB側で実施（高速化）
        #    フィルタ適用後の集合に対して、nameでパーティションし、updated_atの新しい行のみ採用
        filtered_subq = query.with_entities(
            Horse.id.label('id'),
            Horse.name.label('name'),
            Horse.updated_at.label('updated_at')
        ).subquery()

        ranked_subq = db.query(
            filtered_subq.c.id.label('id'),
            filtered_subq.c.name.label('name'),
            func.row_number().over(
                partition_by=filtered_subq.c.name,
                order_by=filtered_subq.c.updated_at.desc()
            ).label('rn')
        ).subquery()

        rep_ids_subq = db.query(ranked_subq.c.id).filter(ranked_subq.c.rn == 1).subquery()

        final_query = db.query(Horse).filter(Horse.id.in_(rep_ids_subq))

        # 並べ替えを適用（DB側でソート）
        if needs_prize_update_flag:
            final_query = final_query.order_by(
                Horse.next_update_due_date.asc(),
                Horse.id.asc()
            )
        elif sort == 'price_desc':
            final_query = final_query.order_by(Horse.sold_price.desc())
        elif sort == 'price_asc':
            final_query = final_query.order_by(Horse.sold_price.asc())
        elif sort == 'name_asc':
            final_query = final_query.order_by(Horse.name.asc())
        elif sort == 'name_desc':
            final_query = final_query.order_by(Horse.name.desc())
        else:
            final_query = final_query.order_by(Horse.sold_price.desc())

        # ページネーション
        total = final_query.count()
        horses = final_query.offset(skip).limit(limit).all()

        # 7. 結果をシリアライズ
        horses_data = []
        for horse in horses:
            # race_record をパースして unified_race_records を設定
            is_unraced = False
            normalized_race_record = None
            
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
                                normalized_race_record = {
                                    "total_races": total_races,
                                    "wins": 0,
                                    "record_format": "simple",
                                    "formatted_record": f"{total_races}戦0勝" if total_races > 0 else "未出走"
                                }
                            # 辞書形式の場合は必要なフィールドを抽出
                            elif isinstance(parsed_record, dict):
                                # シンプル形式の場合はそのまま使用
                                if "formatted_record" in parsed_record:
                                    total_races = parsed_record.get("total_races", 0)
                                    is_unraced = total_races == 0
                                    normalized_race_record = parsed_record
                                # 詳細形式の場合はシンプル形式に変換
                                elif "races" in parsed_record:
                                    total_races = parsed_record.get("races", 0)
                                    is_unraced = total_races == 0
                                    normalized_race_record = {
                                        "total_races": parsed_record.get("races", 0),
                                        "wins": parsed_record.get("wins", 0),
                                        "record_format": "simple",
                                        "formatted_record": f"{parsed_record.get('races', 0)}戦{parsed_record.get('wins', 0)}勝"
                                    }
                    # 文字列でない場合
                    elif isinstance(horse.race_record, dict):
                        record_dict = horse.race_record
                        if "formatted_record" in record_dict:
                            total_races = record_dict.get("total_races", 0)
                            is_unraced = total_races == 0
                            normalized_race_record = record_dict
                        elif "races" in record_dict:
                            total_races = record_dict.get("races", 0)
                            is_unraced = total_races == 0
                            normalized_race_record = {
                                "total_races": record_dict.get("races", 0),
                                "wins": record_dict.get("wins", 0),
                                "record_format": "simple",
                                "formatted_record": f"{record_dict.get('races', 0)}戦{record_dict.get('wins', 0)}勝"
                            }
                        
                except (json.JSONDecodeError, AttributeError, TypeError) as e:
                    logger.warning(f"Failed to parse race_record for horse {horse.id}: {e}")
                    is_unraced = False
            
            # race_records (JSONB) カラムがある場合はそちらを優先または補完
            db_race_records = getattr(horse, 'race_records', None)
            if db_race_records and isinstance(db_race_records, (list, dict)):
                if not normalized_race_record:
                    normalized_race_record = {
                        "total_races": 0,
                        "wins": 0,
                        "record_format": "simple",
                        "formatted_record": "未出走"
                    }
                
                if isinstance(db_race_records, list):
                    total_races = len(db_race_records)
                    wins = 0
                    for r in db_race_records:
                        if isinstance(r, dict) and (r.get('finish_position') == '1' or r.get('order') == 1):
                            wins += 1
                    
                    normalized_race_record["total_races"] = max(normalized_race_record["total_races"], total_races)
                    normalized_race_record["wins"] = max(normalized_race_record["wins"], wins)
                    normalized_race_record["formatted_record"] = f"{normalized_race_record['total_races']}戦{normalized_race_record['wins']}勝"
                    is_unraced = normalized_race_record["total_races"] == 0
                elif isinstance(db_race_records, dict):
                    # 既に集約済みのデータが入っている場合
                    if "total_races" in db_race_records:
                        normalized_race_record["total_races"] = max(normalized_race_record["total_races"], db_race_records.get("total_races", 0))
                    if "wins" in db_race_records:
                        normalized_race_record["wins"] = max(normalized_race_record["wins"], db_race_records.get("wins", 0))
                    if normalized_race_record["total_races"] > 0:
                        normalized_race_record["formatted_record"] = f"{normalized_race_record['total_races']}戦{normalized_race_record['wins']}勝"
                    is_unraced = normalized_race_record["total_races"] == 0
            # race_recordから賞金情報のフォールバックを抽出
            fallback_total_prize_start = None
            fallback_total_prize_latest = None
            try:
                if horse.race_record:
                    if isinstance(horse.race_record, str):
                        parsed = json.loads(horse.race_record)
                    else:
                        parsed = horse.race_record
                    if isinstance(parsed, dict):
                        # start候補: total_prize_money/totalPrizeMoney（サラオク由来、固定）
                        for k in ['total_prize_money', 'totalPrizeMoney']:
                            if k in parsed and parsed[k] is not None:
                                fallback_total_prize_start = parsed[k]
                                break
                        # latest候補: total_prize_latest/current_prize/totalPrizeLatest（最新系のみ）
                        for k in ['total_prize_latest', 'current_prize', 'totalPrizeLatest']:
                            if k in parsed and parsed[k] is not None:
                                fallback_total_prize_latest = parsed[k]
                                break
            except (json.JSONDecodeError, TypeError, AttributeError):
                fallback_total_prize_start = None
                fallback_total_prize_latest = None

            horse_data = {
                "id": horse.id,
                "raw_name": getattr(horse, "raw_name", None),
                "name": horse.name,
                "sex": _extract_latest_history_value(horse.sex),
                "age": _extract_latest_history_value(horse.age),
                "sire": horse.sire,
                "dam": horse.dam,
                "dam_sire": horse.dam_sire,
                "race_record": normalized_race_record or horse.race_record or "未出走",
                "weight": horse.weight,
                "total_prize_start": horse.total_prize_start if horse.total_prize_start is not None else fallback_total_prize_start,
                # DB未設定時は race_record 内の total_prize_money 等をフォールバック
                "total_prize_latest": horse.total_prize_latest if horse.total_prize_latest is not None else fallback_total_prize_latest,
                "current_prize": getattr(horse, "current_prize", None),
                "last_prize_update": horse.last_prize_update.isoformat() if getattr(horse, "last_prize_update", None) else None,
                "next_update_due_date": horse.next_update_due_date.isoformat() if getattr(horse, "next_update_due_date", None) else None,
                "update_interval_months": getattr(horse, "update_interval_months", None),
                "is_retired": getattr(horse, "is_retired", None),
                "is_broodmare": getattr(horse, "is_broodmare", None),
                "sold_price": _extract_latest_history_value(horse.sold_price),
                "auction_date": _extract_latest_history_value(horse.auction_date),
                "seller": _extract_latest_history_value(horse.seller),
                "disease_tags": horse.disease_tags,
                "comment": _extract_latest_history_value(horse.comment),
                "image_url": horse.image_url,
                # 画像のフォールバック: primary_image が未設定なら image_url を使用
                "primary_image": getattr(horse, 'primary_image', None) or horse.image_url,
                "detail_url": horse.detail_url,
                "jbis_url": horse.jbis_url,
                "is_unsold": horse.is_unsold if hasattr(horse, 'is_unsold') else False,
                "unsold": horse.is_unsold if hasattr(horse, 'is_unsold') else False,
                "unified_race_records": normalized_race_record or {
                    "total_races": 0,
                    "wins": 0,
                    "record_format": "simple",
                    "formatted_record": "未出走"
                }
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
    return await get_horses(
        request=request,
        skip=skip,
        limit=limit,
        sort=sort,
        auction_date=None,
        latest_auction='true',
        include_latest_auction='true',
        db=db
    )

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
        
        # race_records を race_record に変換
        if 'race_records' in horse_data and horse_data['race_records'] is not None:
            if not isinstance(horse_data['race_records'], str):
                # 辞書やリストの場合はJSON文字列に変換して race_record に設定
                horse_data['race_record'] = json.dumps(horse_data['race_records'], ensure_ascii=False)
            else:
                horse_data['race_record'] = horse_data['race_records']
            # 元の race_records は削除
            del horse_data['race_records']
        # race_record が存在しない場合は空のJSONオブジェクトを設定
        elif 'race_record' not in horse_data or horse_data['race_record'] is None:
            horse_data['race_record'] = '{}'  # 空のJSONオブジェクトを表す文字列
        
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
        
        # 同一個体は「同名のみ」で集約（父母一致は考慮せず）
        # 表記ゆれ対策のため、半角/全角スペース・中黒を除去して一致判定
        def _norm_name(n: str) -> str:
            try:
                return (n or '').replace(' ', '').replace('　', '').replace('・', '').strip()
            except Exception:
                return n or ''

        norm_target = _norm_name(horse.name)
        normalized_horse_name = func.replace(func.replace(func.replace(Horse.name, ' ', ''), '　', ''), '・', '')
        candidate_query = db.query(Horse).filter(normalized_horse_name == norm_target)
        siblings = candidate_query.all()
        sibling_ids = [h.id for h in siblings] if siblings else [horse_id]

        # 兄弟馬をIDでマップ化（高速参照用）
        siblings_map = {h.id: h for h in siblings} if siblings else {horse_id: horse}

        # 同名だが別horse_idに紐づく履歴も拾う（名前の揺れで結合できないケースを補完）
        normalized_ah_name = func.replace(func.replace(func.replace(AuctionHistory.horse_name, ' ', ''), '　', ''), '・', '')
        auction_histories = db.query(AuctionHistory).filter(
            or_(
                AuctionHistory.horse_id.in_(sibling_ids),
                normalized_ah_name == norm_target
            )
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
            
            # 対応する馬の情報を取得してtotal_prize_startを取得
            related_horse = siblings_map.get(ah.horse_id)
            total_prize_start = getattr(related_horse, 'total_prize_start', None) if related_horse else None
                
            return {
                'id': getattr(ah, 'id', None),
                'horse_id': getattr(ah, 'horse_id', None),
                'horse_name': getattr(ah, 'horse_name', None),
                'sire_name': getattr(ah, 'sire_name', None),
                'dam_name': getattr(ah, 'dam_name', None),
                'damsire_name': getattr(ah, 'damsire_name', None),
                'auction_date': safe_isoformat(getattr(ah, 'auction_date', None)),
                'price': getattr(ah, 'price', None),
                'total_prize_start': total_prize_start, # 追加
                'race_record': getattr(related_horse, 'race_record', None) if related_horse else None, # 追加: 戦績情報
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
        
        # オークション履歴をシリアライズし、IDベースで重複除去（安全最小限）
        raw_histories = [serialize_auction_history(ah) for ah in auction_histories]
        seen_ids = set()
        auction_histories_list = []
        for ah in raw_histories:
            hid = ah.get('id')
            if hid in seen_ids:
                continue
            seen_ids.add(hid)
            auction_histories_list.append(ah)

        # 最新のオークション情報を取得（存在する場合）
        latest_auction_dict = auction_histories_list[0] if auction_histories_list else None

        # もし履歴が1件以下しか見つからない場合は、同名の Horse 行から履歴相当の情報を補完
        if len(auction_histories_list) <= 1 and siblings:
            def parse_first_date(value):
                try:
                    if isinstance(value, str):
                        parsed = json.loads(value)
                        if isinstance(parsed, list) and parsed:
                            return parsed[0]
                        return value
                    return value
                except Exception:
                    return value
 
            for sib in siblings:
                try:
                    item = {
                        'id': None,
                        'horse_id': sib.id,
                        'horse_name': getattr(sib, 'name', None),
                        'sire_name': getattr(sib, 'sire', None),
                        'dam_name': getattr(sib, 'dam', None),
                        'damsire_name': getattr(sib, 'dam_sire', None),
                        'auction_date': parse_first_date(getattr(sib, 'auction_date', None)),
                        'price': None,
                        'total_prize_start': getattr(sib, 'total_prize_start', None), # 追加
                        'race_record': getattr(sib, 'race_record', None), # 追加: 戦績情報
                        'seller': getattr(sib, 'seller', None),
                        'buyer': None,
                        'auction_house': None,
                        'auction_name': None,
                        'lot_number': None,
                        'auction_url': getattr(sib, 'detail_url', None),
                        'is_unsold': getattr(sib, 'is_unsold', False),
                        'created_at': getattr(sib, 'created_at', None).isoformat() if getattr(sib, 'created_at', None) else None,
                        'updated_at': getattr(sib, 'updated_at', None).isoformat() if getattr(sib, 'updated_at', None) else None,
                        'scraped_at': getattr(sib, 'scraped_at', None).isoformat() if getattr(sib, 'scraped_at', None) else None,
                        'user_id': None
                    }
                    # sold_price が履歴配列文字列の場合は最新要素を使う
                    sp = getattr(sib, 'sold_price', None)
                    try:
                        if isinstance(sp, str):
                            # 先頭と末尾の空白を除去
                            sp_stripped = sp.strip()
                            if sp_stripped.startswith('[') and sp_stripped.endswith(']'):
                                # 配列形式の場合
                                parsed_sp = json.loads(sp_stripped)
                                if isinstance(parsed_sp, list) and parsed_sp:
                                    item['price'] = parsed_sp[-1]
                                else:
                                    item['price'] = None
                            else:
                                # 単一の数値形式の場合
                                try:
                                    item['price'] = int(float(sp_stripped))
                                except ValueError:
                                    item['price'] = None
                        else:
                            item['price'] = sp
                    except Exception:
                        item['price'] = None

                    auction_histories_list.append(item)
                except Exception:
                    continue

            # auction_date の降順で再ソート
            def _key_date(x):
                d = x.get('auction_date')
                try:
                    return d.isoformat() if hasattr(d, 'isoformat') else str(d)
                except Exception:
                    return str(d)
            auction_histories_list.sort(key=_key_date, reverse=True)
            latest_auction_dict = auction_histories_list[0] if auction_histories_list else latest_auction_dict

        
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
                            else:
                                pass
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
                        else:
                            pass
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
        
        # race_records (JSONB) カラムがある場合はそちらを優先または補完
        db_race_records = getattr(horse, 'race_records', None)
        if db_race_records and isinstance(db_race_records, (list, dict)):
            if isinstance(db_race_records, list):
                # 配列形式の場合は詳細なレース履歴
                total_races = len(db_race_records)
                wins = 0
                for r in db_race_records:
                    if isinstance(r, dict):
                        # '1' (string) または 1 (int) を考慮。キー名もいくつか想定
                        pos = r.get('finish_position') or r.get('order') or r.get('result')
                        if str(pos) == '1':
                            wins += 1
                
                race_record["total_races"] = max(race_record["total_races"], total_races)
                race_record["wins"] = max(race_record["wins"], wins)
                race_record["formatted_record"] = f"{race_record['total_races']}戦{race_record['wins']}勝"
            elif isinstance(db_race_records, dict):
                # 既にサマリーが入っている場合
                if "total_races" in db_race_records:
                    race_record["total_races"] = max(race_record["total_races"], db_race_records.get("total_races", 0))
                if "wins" in db_race_records:
                    race_record["wins"] = max(race_record["wins"], db_race_records.get("wins", 0))
                if race_record["total_races"] > 0:
                    race_record["formatted_record"] = f"{race_record['total_races']}戦{race_record['wins']}勝"

        # フロントエンドが期待する race_records オブジェクトに勝敗情報を集約
        race_records["total_races"] = race_record["total_races"]
        race_records["wins"] = race_record["wins"]
        race_records["formatted_record"] = race_record["formatted_record"]
        
        # 未出走フラグを設定
        is_unraced = race_record.get("total_races", 0) == 0
        
        # 統合されたレコードオブジェクトを作成
        unified_race_records_obj = {
            "total_races": race_record["total_races"],
            "wins": race_record["wins"],
            "formatted_record": race_record["formatted_record"],
            "total_prize_money": race_records.get("total_prize_money", 0),
            "last_race_date": race_records.get("last_race_date"),
            "last_prize_update": race_records.get("last_prize_update")
        }
        
        # 馬の基本情報を返す
        # 詳細APIでも start/latest のフォールバックを用意
        fallback_total_prize_start = None
        fallback_total_prize_latest = None
        try:
            if hasattr(horse, 'race_record') and horse.race_record:
                if isinstance(horse.race_record, str):
                    parsed_rr = json.loads(horse.race_record)
                else:
                    parsed_rr = horse.race_record
                if isinstance(parsed_rr, dict):
                    # start候補: total_prize_money/totalPrizeMoney
                    for k in ['total_prize_money', 'totalPrizeMoney']:
                        if k in parsed_rr and parsed_rr[k] is not None:
                            fallback_total_prize_start = parsed_rr[k]
                            break
                    # latest候補: total_prize_latest/current_prize/totalPrizeLatest
                    for k in ['total_prize_latest', 'current_prize', 'totalPrizeLatest']:
                        if k in parsed_rr and parsed_rr[k] is not None:
                            fallback_total_prize_latest = parsed_rr[k]
                            break
        except (json.JSONDecodeError, TypeError, AttributeError):
            fallback_total_prize_start = None
            fallback_total_prize_latest = None

        response_data = {
            "id": horse.id,
            "name": horse.name,
            "raw_name": getattr(horse, "raw_name", None),
            "sex": horse.sex,
            "age": horse.age,
            "sire": horse.sire,
            "dam": horse.dam,
            "dam_sire": horse.dam_sire,
            "weight": horse.weight,
            "is_broodmare": getattr(horse, "is_broodmare", False),
            "total_prize_start": horse.total_prize_start if horse.total_prize_start is not None else fallback_total_prize_start,
            # DB未設定時は race_record 内の total_prize_money 等をフォールバック
            "total_prize_latest": horse.total_prize_latest if horse.total_prize_latest is not None else fallback_total_prize_latest,
            "sold_price": horse.sold_price,
            "auction_date": auction_date.isoformat() if hasattr(auction_date, 'isoformat') else auction_date,
            "seller": horse.seller,
            "disease_tags": horse.disease_tags,
            "comment": horse.comment,
            "image_url": horse.image_url,
            # 画像のフォールバック: primary_image が未設定なら image_url を使用
            "primary_image": getattr(horse, 'primary_image', None) or horse.image_url,
            "detail_url": horse.detail_url,
            "jbis_url": horse.jbis_url,
            "is_unsold": getattr(horse, 'is_unsold', False),
            "race_record": race_record,  # 後方互換性のため残す
            "race_records": race_records,  # 後方互換性のため残す
            "unified_race_records": unified_race_records_obj,  # 新しい統合形式
            "auction_histories": auction_histories_list,
            "latest_auction": latest_auction_dict,
        }
        
        return response_data
    except Exception as e:
        db.rollback()
        logger.error(f"Error getting horse by ID: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting horse by ID: {str(e)}"
        )


@router.post("/{horse_id}/prize-history", tags=["horses"])
async def create_horse_prize_history(
    horse_id: Annotated[int, Path(title="The ID of the horse to add prize history for", ge=1)],
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """指定された馬の賞金履歴を追加するエンドポイント"""
    try:
        prize = payload.get("prize")
        if prize is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'prize' フィールドは必須です"
            )

        horse = db.query(Horse).filter(Horse.id == horse_id).first()
        if not horse:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Horse not found")

        history = HorsePrizeHistory(horse_id=horse_id, prize=prize)
        db.add(history)
        db.commit()
        db.refresh(history)

        return {
            "id": history.id,
            "horse_id": history.horse_id,
            "prize": history.prize,
            "created_at": history.created_at.isoformat() if history.created_at else None,
            "updated_at": history.updated_at.isoformat() if history.updated_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating horse prize history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating horse prize history: {str(e)}"
        )


@router.put("/{horse_id}", tags=["horses"])
async def update_horse(
    horse_id: Annotated[int, Path(title="The ID of the horse to update", ge=1)],
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """馬の情報を部分更新するエンドポイント

    主に賞金関連フィールド（current_prize, last_prize_update など）を更新することを想定
    """
    try:
        horse = db.query(Horse).filter(Horse.id == horse_id).first()
        if not horse:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Horse not found")

        # 許可するフィールドのみ更新
        allowed_fields = {
            "current_prize",
            "last_prize_update",
            "update_interval_months",
            "is_retired",
            "raw_name",
            "is_broodmare",
            "next_update_due_date",
            "total_prize_latest",
        }

        updated = False
        for key, value in payload.items():
            if key in allowed_fields:
                setattr(horse, key, value)
                updated = True

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="更新可能なフィールドが含まれていません"
            )

        db.commit()
        db.refresh(horse)

        return {
            "id": horse.id,
            "raw_name": getattr(horse, "raw_name", None),
            "current_prize": getattr(horse, "current_prize", None),
            "last_prize_update": getattr(horse, "last_prize_update", None),
            "update_interval_months": getattr(horse, "update_interval_months", None),
            "is_retired": getattr(horse, "is_retired", None),
            "is_broodmare": getattr(horse, "is_broodmare", None),
            "next_update_due_date": getattr(horse, "next_update_due_date", None),
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating horse: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating horse: {str(e)}"
        )

