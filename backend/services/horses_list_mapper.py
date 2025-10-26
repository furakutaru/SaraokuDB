from typing import Any, Dict, List, Tuple
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database.models import get_db, AuctionHistory

def map_horses_list(horses: List[Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    馬のリストをフロントエンド用に変換する
    N+1問題を解消するため、オークション履歴を一括取得するように最適化
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # 重複したハンドラの追加を防ぐ
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    horses_data: List[Dict[str, Any]] = []
    auction_histories: List[Dict[str, Any]] = []
    db = next(get_db())

    try:
        # 馬IDのリストを取得
        horse_ids = [horse.id for horse in horses]
        logger.info(f"Processing {len(horse_ids)} horses")
        
        # 全馬の最新オークション履歴を1回のクエリで取得
        latest_auctions = {}
        if horse_ids:
            # サブクエリで各馬の最新オークションIDを取得
            subq = db.query(
                AuctionHistory.horse_id,
                func.max(AuctionHistory.auction_date).label('max_date')
            ).filter(
                AuctionHistory.horse_id.in_(horse_ids)
            ).group_by(
                AuctionHistory.horse_id
            ).subquery()

            # 最新のオークション履歴を取得
            latest_auction_records = db.query(AuctionHistory).join(
                subq,
                (AuctionHistory.horse_id == subq.c.horse_id) &
                (AuctionHistory.auction_date == subq.c.max_date)
            ).all()

            # 辞書に格納（horse_idをキーとして）
            latest_auctions = {auction.horse_id: auction for auction in latest_auction_records}
            logger.info(f"Fetched latest auction history for {len(latest_auctions)} horses")

        # 馬データを処理
        for horse in horses:
            # カラム情報を辞書に変換
            horse_dict = {column.name: getattr(horse, column.name, None) 
                         for column in horse.__table__.columns}
            
            # 最新のオークション履歴を取得
            latest_auction = latest_auctions.get(horse.id)
            
            # sold_price を取得（horses テーブルから直接取得）
            horse_dict['sold_price'] = getattr(horse, 'sold_price', None)
            
            # is_unsold を設定
            # 1. 馬レコードに明示的に is_unsold が設定されている場合はそれを使用
            # 2. 次に unsold_count が 1 以上の場合
            # 3. 最後に sold_price が None または 0 の場合
            horse_dict['is_unsold'] = getattr(horse, 'is_unsold', False) or \
                                   bool(getattr(horse, 'unsold_count', 0) > 0) or \
                                   (getattr(horse, 'sold_price', None) in (None, 0))
            
            # デバッグ用ログ
            logger.debug(f"Processing horse - ID: {horse.id}, Name: {getattr(horse, 'name', 'N/A')}, "
                       f"sold_price: {getattr(horse, 'sold_price', 'N/A')}, "
                       f"is_unsold: {getattr(horse, 'is_unsold', 'N/A')}, "
                       f"unsold_count: {getattr(horse, 'unsold_count', 0)}, "
                       f"final_is_unsold: {horse_dict['is_unsold']}")
            
            if latest_auction:
                # オークション履歴を追加
                auction_history = {
                    'id': latest_auction.id,
                    'horse_id': latest_auction.horse_id,
                    'auction_date': latest_auction.auction_date,
                    'price': latest_auction.price,
                    'sold_price': horse_dict['sold_price'],  # horses テーブルの sold_price を使用
                    'seller': latest_auction.seller,
                    'buyer': latest_auction.buyer,
                    'auction_house': latest_auction.auction_house,
                    'auction_name': latest_auction.auction_name,
                    'lot_number': latest_auction.lot_number,
                    'auction_url': latest_auction.auction_url,
                    'horse_name': latest_auction.horse_name,
                    'sire_name': latest_auction.sire_name,
                    'dam_name': latest_auction.dam_name,
                    'damsire_name': latest_auction.damsire_name,
                    'is_unsold': horse_dict['is_unsold'],
                    'unsold': horse_dict['is_unsold'],  # フロントエンドの互換性のため追加
                    'created_at': latest_auction.created_at,
                    'updated_at': latest_auction.updated_at,
                    'user_id': latest_auction.user_id
                }
                auction_histories.append(auction_history)
            else:
                logger.info(f"No auction history found for horse ID: {horse.id}")

            # 性別の処理
            if 'sex' in horse_dict and horse_dict['sex']:
                sex = str(horse_dict['sex']).strip()
                horse_dict['sex'] = ''.join(c for c in sex if c not in ' \t\n\r\f\v')
            
            # フロントエンド用にフィールド名を調整
            if 'dam_sire' in horse_dict:
                horse_dict['damsire'] = horse_dict.pop('dam_sire')
            
            # 詳細URLを設定
            if 'detail_url' not in horse_dict and hasattr(horse, 'detail_url'):
                horse_dict['detail_url'] = horse.detail_url
                horse_dict['auction_url'] = horse.detail_url

            horses_data.append(horse_dict)

        logger.info(f"Successfully processed {len(horses_data)} horses and {len(auction_histories)} auction histories")
            
    except Exception as e:
        logger.error(f"Error in map_horses_list: {str(e)}", exc_info=True)
        raise

    return horses_data, auction_histories
