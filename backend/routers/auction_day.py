"""
オークション当日モード API。

読み取り専用。JBIS 賞金一括更新はトリガーしない。
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from services.auction_session import (
    count_horses_for_session,
    extract_latest_history_value,
    list_session_dates_from_db,
    max_data_as_of_for_horses,
    parse_session_date_param,
    query_horses_for_session,
    suggest_upcoming_auction_dates,
)
from services.auction_price_prediction import (
    get_sire_ranks_cached,
    parse_sold_price_latest,
    predict_for_horse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auction-day", tags=["auction-day"])


@router.get("/sessions")
async def list_auction_sessions(
    db: Session = Depends(get_db),
    limit: int = Query(30, ge=1, le=80),
) -> Dict[str, Any]:
    """直近の開催日（DB）と、カレンダー由来の開催予定候補。"""
    from_db = list_session_dates_from_db(db, limit=limit)
    sessions: List[Dict[str, Any]] = []
    for d in from_db:
        cnt = count_horses_for_session(db, parse_session_date_param(d))
        sessions.append(
            {
                "session_date": d,
                "horse_count": cnt,
                "source": "database",
            }
        )
    suggestions = suggest_upcoming_auction_dates(count=2)
    return {
        "sessions": sessions,
        "upcoming_suggestions": suggestions,
    }


@router.get("/sessions/{session_date}/horses")
async def list_session_horses(
    session_date: str,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    include_valuation: bool = Query(False, description="査定ポイント文字列を含める（デバッグ用）"),
) -> Dict[str, Any]:
    try:
        sd = parse_session_date_param(session_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_date は YYYY-MM-DD 形式で指定してください",
        )

    horses, total = query_horses_for_session(db, sd, skip=skip, limit=limit)
    ds = sd.isoformat()
    sire_ranks = get_sire_ranks_cached(db)
    data_as_of = max_data_as_of_for_horses(horses)
    data_as_of_iso = data_as_of.isoformat() if data_as_of else None

    items: List[Dict[str, Any]] = []
    for h in horses:
        try:
            est_min, est_max, range_str, valuation = predict_for_horse(h, ds, sire_ranks)
        except Exception as e:
            logger.exception("predict_for_horse failed horse_id=%s", h.id)
            est_min, est_max, range_str, valuation = 0, 0, "", str(e)

        sold = parse_sold_price_latest(h)
        row: Dict[str, Any] = {
            "id": h.id,
            "name": h.name,
            "sex": extract_latest_history_value(h.sex),
            "age": extract_latest_history_value(h.age),
            "sire": h.sire,
            "dam": h.dam,
            "dam_sire": h.dam_sire,
            "weight": h.weight,
            "total_prize_start": float(h.total_prize_start) if h.total_prize_start is not None else None,
            "is_broodmare": bool(h.is_broodmare),
            "is_unsold": bool(h.is_unsold),
            "sold_price_latest": sold,
            "detail_url": h.detail_url,
            "jbis_url": h.jbis_url,
            "predicted_price_min": est_min,
            "predicted_price_max": est_max,
            "predicted_price_range_label": range_str,
            "data_as_of": data_as_of_iso,
        }
        if include_valuation:
            row["valuation"] = valuation
        items.append(row)

    return {
        "session_date": ds,
        "metadata": {
            "total": total,
            "skip": skip,
            "limit": limit,
            "returned": len(items),
            "data_as_of": data_as_of_iso,
        },
        "horses": items,
    }


@router.get("/sessions/{session_date}/meta")
async def session_meta(session_date: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    try:
        sd = parse_session_date_param(session_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_date は YYYY-MM-DD 形式で指定してください",
        )
    total = count_horses_for_session(db, sd)
    return {
        "session_date": sd.isoformat(),
        "horse_count": total,
    }
