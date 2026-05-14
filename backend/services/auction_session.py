"""
オークション当日モード（Auction Day Mode）用のセッション定義と日付パース。

セッションキー session_date は開催日を表す YYYY-MM-DD（API・URLで使用）。
JST でユーザーに見せる日付文字列と一致させる。

カタログ馬の包含ルール（いずれかを満たせばその session に属する候補）:
1) auction_histories に auction_date が session_date と一致する行が存在する
2) horses.auction_date の JSON 履歴文字列に session_date が部分一致で含まれる
   （ISO 形式のため通常は配列要素として含まれる）

優先ルール: 同一馬について auction_histories があればその日付を正とし、
一覧ではそのセッション日に対応する出品を1行として扱う（API 側で DISTINCT horse）。

落札前は sold_price が空または 0 に近く、落札後は履歴の最新値が入る。
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from typing import Any, List, Optional, Tuple

from sqlalchemy.orm import Session

from database.models import AuctionHistory, Horse

try:
    from zoneinfo import ZoneInfo

    JST = ZoneInfo("Asia/Tokyo")
except Exception:  # pragma: no cover
    JST = timezone(timedelta(hours=9))


def extract_latest_history_value(raw_value: Any) -> Any:
    """履歴カラム（JSON文字列/配列）から最新値を取得（horses ルータと同一仕様）。"""
    if raw_value is None:
        return None

    if isinstance(raw_value, list):
        return raw_value[-1] if raw_value else None

    if isinstance(raw_value, dict):
        return raw_value.get("auction_date") or raw_value.get("date") or raw_value.get("value")

    if isinstance(raw_value, str):
        stripped = raw_value.strip()
        if not stripped:
            return None
        if stripped.startswith("[") or stripped.startswith("{"):
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, list) and parsed:
                    return parsed[-1]
                if isinstance(parsed, dict):
                    return parsed.get("auction_date") or parsed.get("date") or parsed.get("value")
            except json.JSONDecodeError:
                return stripped
        return stripped

    return raw_value


def parse_latest_auction_date(raw_value: Any) -> Optional[date]:
    """auction_date の履歴から最新日付を datetime.date で返す。"""
    latest_value = extract_latest_history_value(raw_value)
    if not latest_value:
        return None

    if isinstance(latest_value, dict):
        latest_value = latest_value.get("auction_date") or latest_value.get("date")

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


def parse_session_date_param(session_date: str) -> date:
    """パスパラメータ session_date を date に変換。不正なら ValueError。"""
    s = (session_date or "").strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except ValueError:
            continue
    raise ValueError("session_date must be YYYY-MM-DD")


def list_session_dates_from_db(db: Session, limit: int = 40) -> List[str]:
    """auction_histories から直近の開催日一覧（降順、重複除去）。"""
    rows = (
        db.query(AuctionHistory.auction_date)
        .distinct()
        .order_by(AuctionHistory.auction_date.desc())
        .limit(limit * 2)
        .all()
    )
    seen = set()
    out: List[str] = []
    for (d,) in rows:
        if not d or d in seen:
            continue
        seen.add(d)
        out.append(str(d)[:10])
        if len(out) >= limit:
            break
    return out


def _next_weekday_from(base: date, weekday: int) -> date:
    """base より後の最初の weekday（月=0 … 日=6）。"""
    days_ahead = weekday - base.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return base + timedelta(days=days_ahead)


def suggest_upcoming_auction_dates(count: int = 2) -> List[dict]:
    """
    楽天サラオクの木・日開催に合わせ、直近の木曜・日曜候補日を返す。
    DB に無い「予定」行として UI に併記する用途。
    """
    today = datetime.now(JST).date()
    candidates: List[date] = []
    d = today
    for _ in range(21):
        if d.weekday() == 3:  # Thu
            candidates.append(d)
        if d.weekday() == 6:  # Sun
            candidates.append(d)
        d += timedelta(days=1)
    uniq: List[date] = []
    for c in sorted(set(candidates)):
        if c >= today and c not in uniq:
            uniq.append(c)
        if len(uniq) >= count:
            break
    if not uniq:
        thu = _next_weekday_from(today, 3)
        sun = _next_weekday_from(today, 6)
        uniq = sorted({thu, sun})[:count]
    return [
        {"session_date": d.isoformat(), "label": "開催予定（カレンダー）", "source": "calendar_suggestion"}
        for d in uniq[:count]
    ]


def horse_ids_for_session(db: Session, session_date: date) -> List[int]:
    """session_date に該当する馬 ID 一覧（重複なし）。"""
    ds = session_date.isoformat()
    from_ah = (
        db.query(AuctionHistory.horse_id)
        .filter(AuctionHistory.auction_date == ds)
        .distinct()
        .all()
    )
    ids_ah = {int(r[0]) for r in from_ah if r[0] is not None}

    like_pat = f"%{ds}%"
    from_horse_json = db.query(Horse.id).filter(Horse.auction_date.isnot(None), Horse.auction_date.like(like_pat)).distinct().all()
    ids_json = {int(r[0]) for r in from_horse_json if r[0] is not None}

    merged = sorted(ids_ah | ids_json)
    return merged


def count_horses_for_session(db: Session, session_date: date) -> int:
    return len(horse_ids_for_session(db, session_date))


def query_horses_for_session(
    db: Session, session_date: date, skip: int = 0, limit: int = 50
) -> Tuple[List[Horse], int]:
    """セッションに属する馬をページング取得。total は ID ユニーク件数。"""
    ids = horse_ids_for_session(db, session_date)
    total = len(ids)
    if skip >= total:
        return [], total
    page_ids = ids[skip : skip + limit]
    if not page_ids:
        return [], total
    horses = db.query(Horse).filter(Horse.id.in_(page_ids)).all()
    order = {hid: i for i, hid in enumerate(page_ids)}
    horses.sort(key=lambda h: order.get(h.id, 9999))
    return horses, total


def max_data_as_of_for_horses(horses: List[Horse]) -> Optional[datetime]:
    if not horses:
        return None
    times = [h.updated_at for h in horses if getattr(h, "updated_at", None)]
    return max(times) if times else None
