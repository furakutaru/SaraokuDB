import json
from typing import Any, Dict, Optional
from datetime import datetime

# Utilities to normalize DB fields that might be stored as JSON-like strings (e.g., "[3]")

def _parse_first_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        s = value.strip()
        # JSON array string, e.g. "[8500000]"
        if s.startswith("[") and s.endswith("]"):
            try:
                arr = json.loads(s)
                if isinstance(arr, list) and len(arr) > 0:
                    last = arr[-1]
                    try:
                        return int(str(last).strip().strip('"'))
                    except Exception:
                        return None
            except Exception:
                return None
        # plain number string
        num = s.strip('"')
        if num.isdigit():
            return int(num)
    return None


def _parse_first_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                arr = json.loads(s)
                if isinstance(arr, list) and len(arr) > 0:
                    return str(arr[0])
            except Exception:
                return None
        return value
    return str(value)


def serialize_horse(horse: Any) -> Dict[str, Any]:
    """
    Convert a Horse ORM object into a response dict matching HorseResponse
    with normalized primitives for age/sold_price/etc.
    """
    age_norm = _parse_first_int(getattr(horse, 'age', None))
    sold_price_norm = _parse_first_int(getattr(horse, 'sold_price', None))
    auction_date_norm = _parse_first_str(getattr(horse, 'auction_date', None))
    seller_norm = _parse_first_str(getattr(horse, 'seller', None))
    sex_norm = _parse_first_str(getattr(horse, 'sex', None))
    comment_norm = _parse_first_str(getattr(horse, 'comment', None))

    return {
        "id": getattr(horse, 'id', None),
        "name": getattr(horse, 'name', None),
        "auction_id": getattr(horse, 'auction_id', None),
        "sex": sex_norm,
        "age": age_norm,
        "sire": getattr(horse, 'sire', None),
        "dam": getattr(horse, 'dam', None),
        "dam_sire": getattr(horse, 'dam_sire', None),
        "race_record": getattr(horse, 'race_record', None),
        "weight": getattr(horse, 'weight', None),
        "total_prize_start": getattr(horse, 'total_prize_start', None),
        "total_prize_latest": getattr(horse, 'total_prize_latest', None),
        "sold_price": sold_price_norm,
        "auction_date": auction_date_norm,
        "seller": seller_norm,
        "disease_tags": getattr(horse, 'disease_tags', None),
        "comment": comment_norm,
        "image_url": getattr(horse, 'image_url', None),
        "jbis_url": getattr(horse, 'jbis_url', ''),
        "detail_url": getattr(horse, 'detail_url', ''),
        "rakuten_url": getattr(horse, 'rakuten_url', ''),
        "auction_url": getattr(horse, 'auction_url', ''),
        "created_at": getattr(horse, 'created_at', None) or datetime.utcnow().isoformat(),
        "updated_at": getattr(horse, 'updated_at', None) or datetime.utcnow().isoformat(),
    }
