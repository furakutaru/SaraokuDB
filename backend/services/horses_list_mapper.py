from typing import Any, Dict, List, Tuple


def map_horses_list(horses: List[Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Convert a list of Horse ORM objects into two arrays:
    - horses_data: list of dictionaries with column values
    - auction_histories: list of auction history dictionaries expected by the FE

    Behavior matches the previous implementation in routers/horses.get_horses.
    """
    horses_data: List[Dict[str, Any]] = []
    auction_histories: List[Dict[str, Any]] = []

    for horse in horses:
        # Build dictionary of column values from ORM object
        horse_dict: Dict[str, Any] = {}
        for column in horse.__table__.columns:  # type: ignore[attr-defined]
            column_name = column.name
            horse_dict[column_name] = getattr(horse, column_name, None)
        horses_data.append(horse_dict)

        # Create auction history entry mirroring previous logic
        auction_history = {
            'id': horse_dict.get('id'),
            'horse_id': horse_dict.get('id'),
            'auction_date': horse_dict.get('auction_date'),
            'sold_price': horse_dict.get('sold_price'),
            'total_prize_start': horse_dict.get('total_prize_start'),
            'total_prize_latest': horse_dict.get('total_prize_latest'),
            'weight': horse_dict.get('weight'),
            'seller': horse_dict.get('seller'),
            'is_unsold': (horse_dict.get('unsold_count') or 0) > 0,
            'comment': horse_dict.get('comment', ''),
            'created_at': horse_dict.get('created_at'),
        }
        auction_histories.append(auction_history)

        # Field alias for FE expectations: dam_sire -> damsire
        if 'dam_sire' in horse_dict:
            horse_dict['damsire'] = horse_dict.pop('dam_sire')

    return horses_data, auction_histories
