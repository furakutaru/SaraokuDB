import json
from typing import Any, Dict, Optional
from datetime import datetime

# Utilities to normalize DB fields that might be stored as JSON-like strings (e.g., "[3]")

def _parse_first_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value if value != 0 else None
    if isinstance(value, float):
        return int(value) if value != 0 else None
    if isinstance(value, str):
        s = value.strip()
        # Handle empty string
        if not s:
            return None
            
        # Try to parse as JSON array first
        if s.startswith("[") and s.endswith("]"):
            try:
                arr = json.loads(s)
                if isinstance(arr, list) and len(arr) > 0:
                    first = arr[0]
                    if first is not None:
                        if isinstance(first, str):
                            # Handle comma-separated numbers in array
                            num = int(first.replace(',', ''))
                            return num if num != 0 else None
                        num = int(first)
                        return num if num != 0 else None
                return None
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        
        # Try to parse as plain string (e.g., "1,000,000" or "1000000")
        try:
            # Remove any commas and try to convert to int
            num = int(s.replace(',', ''))
            return num if num != 0 else None
        except (ValueError, TypeError):
            pass
    
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


def _parse_last_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                arr = json.loads(s)
                if isinstance(arr, list) and len(arr) > 0:
                    return str(arr[-1])  # 最後の要素を返す
            except Exception:
                return None
        return value
    return str(value)


def serialize_horse(horse: Any, include_auction: bool = False) -> Dict[str, Any]:
    """
    Convert a Horse ORM object into a response dict matching HorseResponse
    with normalized primitives for age/sold_price/etc.
    
    Args:
        horse: Horse ORM object or dict
        include_auction: Whether to include latest auction information
    """
    if not horse:
        return None
        
    # Handle SQLAlchemy model or dict-like object
    if hasattr(horse, '__dict__'):
        data = horse.__dict__.copy()
        # Remove SQLAlchemy internal attributes
        data.pop('_sa_instance_state', None)
    else:
        data = dict(horse)
    
    # Normalize fields that might be stored as JSON-like strings
    data['age'] = _parse_first_int(data.get('age'))
    data['sold_price'] = _parse_first_int(data.get('sold_price'))
    data['is_unsold'] = data.get('is_unsold', False)
    
    # 最新のオークション情報を取得
    latest_auction = None
    if include_auction and hasattr(horse, 'latest_auction') and horse.latest_auction:
        auction = horse.latest_auction
        latest_auction = {
            'id': auction.id,
            'auction_date': auction.auction_date.isoformat() if hasattr(auction, 'auction_date') and auction.auction_date else None,
            'price': float(auction.price) if hasattr(auction, 'price') and auction.price is not None else None,
            'is_unsold': auction.is_unsold if hasattr(auction, 'is_unsold') else False,
            'comment': auction.comment if hasattr(auction, 'comment') else None,
            'created_at': auction.created_at.isoformat() if hasattr(auction, 'created_at') and auction.created_at else None,
            'updated_at': auction.updated_at.isoformat() if hasattr(auction, 'updated_at') and auction.updated_at else None
        }
    
    # 日付フィールドの処理用ヘルパー
    def safe_isoformat(dt):
        if hasattr(dt, 'isoformat'):
            return dt.isoformat()
        return dt.isoformat() if hasattr(dt, 'isoformat') else None
    
    # 結果の辞書を作成
    result = {
        'id': data.get('id'),
        'name': data.get('name'),
        'breed': data.get('breed'),
        'age': data.get('age'),
        'sold_price': data.get('sold_price'),
        'is_unsold': data.get('is_unsold', False),
        'created_at': safe_isoformat(data.get('created_at')) if data.get('created_at') else None,
        'updated_at': safe_isoformat(data.get('updated_at')) if data.get('updated_at') else None,
        'auction_date': safe_isoformat(data.get('auction_date')) if data.get('auction_date') else None,
        'auction_id': data.get('auction_id'),
        'sex': data.get('sex'),
        'sire': data.get('sire'),
        'dam': data.get('dam'),
        'dam_sire': data.get('dam_sire'),
        'weight': data.get('weight'),
        'seller': data.get('seller'),
        'comment': data.get('comment'),
        'disease_tags': data.get('disease_tags'),
        'detail_url': data.get('detail_url'),
        'image_url': data.get('image_url'),
        'jbis_url': data.get('jbis_url', ''),
        'rakuten_url': data.get('rakuten_url', ''),
        'auction_url': data.get('auction_url', ''),
        'race_record': data.get('race_record', '{}'),  # race_record をそのまま返す
        'pedigree': data.get('pedigree'),
        'latest_auction': latest_auction
    }
    
    return result
