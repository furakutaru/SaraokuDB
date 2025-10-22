from typing import Any, Dict, List, Tuple


import logging
from typing import List, Any, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from database.models import get_db, AuctionHistory

def map_horses_list(horses: List[Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Convert a list of Horse ORM objects into two arrays:
    - horses_data: list of dictionaries with column values
    - auction_histories: list of auction history dictionaries expected by the FE

    Behavior matches the previous implementation in routers/horses.get_horses.
    """
    # ロガーの設定
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # コンソールにログを出力するハンドラーを追加
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    horses_data: List[Dict[str, Any]] = []
    auction_histories: List[Dict[str, Any]] = []

    # データベースセッションを取得
    db = next(get_db())
    logger.info(f"Starting to process {len(horses)} horses")

    for horse in horses:
        # Build dictionary of column values from ORM object
        horse_dict: Dict[str, Any] = {}
        for column in horse.__table__.columns:  # type: ignore[attr-defined]
            column_name = column.name
            horse_dict[column_name] = getattr(horse, column_name, None)
        
        # オークション履歴から最新の落札価格を取得
        logger.info(f"\nProcessing horse ID: {horse.id}, Name: {getattr(horse, 'name', 'N/A')}")
        
        # デバッグ用: 馬の現在のsold_priceを確認
        current_sold_price = getattr(horse, 'sold_price', None)
        logger.info(f"Current sold_price in Horse table: {current_sold_price}")
        
        # オークション履歴をクエリ
        query = db.query(AuctionHistory).filter(AuctionHistory.horse_id == horse.id)
        logger.info(f"Auction history query: {query.statement}")
        
        latest_auction = query.order_by(AuctionHistory.auction_date.desc()).first()
        logger.info(f"Latest auction record: {latest_auction}")
        
        # 最新のオークション履歴があれば、その価格を使用
        sold_price = None
        is_unsold = False
        
        if latest_auction:
            logger.info(f"Found auction history - Price: {latest_auction.price}, Date: {latest_auction.auction_date}")
            sold_price = latest_auction.price
            is_unsold = (horse_dict.get('unsold_count') or 0) > 0
            logger.info(f"Using auction history price: {sold_price}, is_unsold: {is_unsold}")
        else:
            # オークション履歴がない場合は、Horseテーブルのsold_priceを使用
            sold_price = horse_dict.get('sold_price')
            logger.info(f"Raw sold_price from DB: {sold_price} (type: {type(sold_price)})")
        
        # 性別の処理（記号をそのまま保持）
        if 'sex' in horse_dict and horse_dict['sex']:
            sex = str(horse_dict['sex']).strip()
            # 前後の空白と制御文字を削除
            sex = ''.join(c for c in sex if c not in ' \t\n\r\f\v')
            horse_dict['sex'] = sex
        
        # raw_sold_price に元の値を保持
        if sold_price is not None:
            horse_dict['raw_sold_price'] = sold_price
            
        # 未落札フラグを設定
        is_unsold = (horse_dict.get('unsold_count') or 0) > 0
        if not latest_auction:
            logger.warning(f"No auction history found for horse ID: {horse.id}. Using sold_price from Horse table: {sold_price} (type: {type(sold_price)}), is_unsold: {is_unsold}")
            
        # デバッグ用: オークションテーブルの存在確認
            from sqlalchemy import inspect, text
            inspector = inspect(db.get_bind())
            tables = inspector.get_table_names()
            logger.info(f"Available tables: {tables}")
            
            if 'auction_histories' in tables:
                logger.info("auction_histories table exists")
                # テーブルの構造を確認
                columns = [column['name'] for column in inspector.get_columns('auction_histories')]
                logger.info(f"auction_histories columns: {columns}")
                
                # サンプルデータを確認
                try:
                    sample = db.execute(text("SELECT * FROM auction_histories LIMIT 1")).fetchone()
                    logger.info(f"Sample auction_histories row: {sample}")
                except Exception as e:
                    logger.error(f"Error querying auction_histories: {str(e)}")
        
        # デバッグ用にログを出力
        print(f"Horse ID: {horse.id}, Name: {horse_dict.get('name')}, Sold Price: {sold_price}, Is Unsold: {is_unsold}")
        
        # オークション履歴エントリを作成
        auction_history = {
            'id': horse_dict.get('id'),
            'horse_id': horse_dict.get('id'),
            'auction_date': horse_dict.get('auction_date'),
            'sold_price': sold_price,
            'total_prize_start': horse_dict.get('total_prize_start'),
            'total_prize_latest': horse_dict.get('total_prize_latest'),
            'weight': horse_dict.get('weight'),
            'seller': horse_dict.get('seller'),
            'is_unsold': is_unsold,
            'comment': horse_dict.get('comment', ''),
            'created_at': horse_dict.get('created_at'),
        }
        auction_histories.append(auction_history)
        
        # 馬データにsold_priceとis_unsoldを設定
        horse_dict['sold_price'] = sold_price
        horse_dict['is_unsold'] = is_unsold
        
        # detail_url が存在するか確認してログに出力
        if 'detail_url' in horse_dict:
            logger.info(f"Horse ID {horse_dict.get('id')} has detail_url: {horse_dict.get('detail_url')}")
        else:
            logger.warning(f"Horse ID {horse_dict.get('id')} is missing detail_url")
        
        # Field alias for FE expectations: dam_sire -> damsire
        if 'dam_sire' in horse_dict:
            horse_dict['damsire'] = horse_dict.pop('dam_sire')
            
        # フロントエンドに必要なフィールドを確実に含める
        horse_data = {
            **horse_dict,
            # 既存のフィールドに加えて、detail_url を明示的に含める
            'detail_url': horse_dict.get('detail_url'),
            'auction_url': horse_dict.get('detail_url'),  # 互換性のため
        }
        
        horses_data.append(horse_data)

    return horses_data, auction_histories
