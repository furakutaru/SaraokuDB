import json
import logging
import os
import re
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
logger.addHandler(handler)

# データベース関連のインポート
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from database import get_db
from database.models import Horse, AuctionHistory
from database.schemas import HorseResponse
from services.horse_serializer import serialize_horse, _parse_first_int
from services.horses_list_mapper import map_horses_list

# スクリプトのディレクトリをパスに追加
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
scripts_dir = os.path.join(project_root, 'scripts')
components_dir = os.path.join(project_root, 'scripts', 'components')
components_dir = os.path.join(scripts_dir, 'components')

# 必要なディレクトリをsys.pathに追加
for path in [project_root, scripts_dir, components_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)
        logger.info(f"Added to sys.path: {path}")

# 現在のPythonパスをログに出力
logger.info(f"Python path: {sys.path}")

# 疾病情報抽出モジュールを一時的に無効化
logger.info("DiseaseInfoExtractor is temporarily disabled")
DiseaseInfoExtractor = None

# ルーターの設定
router = APIRouter(tags=["horses"])

class DiseaseExtractionRequest(BaseModel):
    comment: str

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

@router.get("/latest", response_model=Dict[str, Any], tags=["horses"])
async def get_latest_horses(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """最新のオークションの馬一覧を取得するエンドポイント"""
    logger.info("Calling /horses/latest endpoint")
    return await get_horses(request, skip, limit, None, 'true', db)

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

@router.get("", response_model=Dict[str, Any], tags=["horses"])
async def get_horses(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    sort: str = 'price_desc',  # デフォルトは価格の降順
    auction_date: Optional[str] = None,
    latest_auction: str = 'false',  # デフォルトですべての馬を表示
    include_latest_auction: str = 'true',  # 最新のオークション情報を含める
    db: Session = Depends(get_db)
):
    """馬の一覧を取得するエンドポイント
    
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
        
        # 2. 馬の基本クエリを構築（LEFT OUTER JOINを使用して、オークション履歴のない馬も含める）
        query = db.query(Horse)
        
        # 3. オークション日でフィルタリング
        if auction_date:
            # オークション日を部分一致で検索（JSON配列内のいずれかの要素と一致）
            query = query.filter(
                Horse.auction_date.like(f'%{auction_date}%')
            )
        
        # 4. 最新のオークション日でフィルタリング
        latest_auction_bool = latest_auction.lower() == 'true' or request.query_params.get('latest_auction', '').lower() == 'true'
        if latest_auction_bool and latest_date:
            # 最新のオークション日を含む馬をフィルタリング
            query = query.filter(
                Horse.auction_date.like(f'%{latest_date}%')
            )
        
        # 5. ソートに必要なフィールドを決定
        if sort in ['price_desc', 'price_asc']:
            # 価格でのソートの場合は、オークション情報をサブクエリで取得
            latest_auction_subq = (
                db.query(
                    AuctionHistory.horse_id,
                    func.max(AuctionHistory.id).label('latest_auction_id')
                )
                .group_by(AuctionHistory.horse_id)
                .subquery()
            )
            
            # 価格情報を含むサブクエリ
            auction_with_prices = (
                db.query(
                    AuctionHistory.horse_id,
                    AuctionHistory.id.label('auction_id'),
                    AuctionHistory.price,
                    AuctionHistory.is_unsold
                )
                .join(
                    latest_auction_subq,
                    and_(
                        AuctionHistory.horse_id == latest_auction_subq.c.horse_id,
                        AuctionHistory.id == latest_auction_subq.c.latest_auction_id
                    )
                )
                .subquery()
            )
            
            # メインクエリと結合
            query = query.outerjoin(
                auction_with_prices,
                Horse.id == auction_with_prices.c.horse_id
            )
            
            # ソート順を適用
            logger.info(f"Applying sort: {sort}")
            
            if sort == 'price_desc':
                # 価格の降順（高い順）でソート（未落札は最後）
                logger.info("Sorting by price_desc")
                query = query.order_by(
                    auction_with_prices.c.is_unsold.asc(),
                    auction_with_prices.c.price.desc().nulls_last(),
                    Horse.id.asc()
                )
                logger.info(f"SQL: {str(query)}")
            
            elif sort == 'price_asc':
                # 価格の昇順（安い順）でソート（未落札は最後）
                logger.info("Sorting by price_asc")
                query = query.order_by(
                    auction_with_prices.c.is_unsold.asc(),
                    auction_with_prices.c.price.asc().nulls_last(),
                    Horse.id.asc()
                )
                logger.info(f"SQL: {str(query)}")

        # 価格以外のソート条件
        elif sort == 'name_asc':
            # 名前の昇順（A-Z）でソート
            logger.info("Sorting by name_asc")
            query = query.order_by(
                Horse.name.asc(),
                Horse.id.asc()
            )
            logger.info(f"SQL: {str(query)}")
            
        elif sort == 'name_desc':
            # 名前の降順（Z-A）でソート
            logger.info("Sorting by name_desc")
            query = query.order_by(
                Horse.name.desc(),
                Horse.id.asc()
            )
            logger.info(f"SQL: {str(query)}")
            
        elif sort == 'date_desc':
            # 日付の降順（最新を先頭に）
            logger.info("Sorting by date_desc (default)")
            query = query.order_by(Horse.id.desc())
            logger.info(f"SQL: {str(query)}")
            
        else:
            # デフォルトはIDの降順（最新の馬を先頭に）
            logger.info(f"Unknown sort parameter: {sort}, using default sort (id desc)")
            query = query.order_by(Horse.id.desc())
            logger.info(f"SQL: {str(query)}")
        
        # 6. 総レコード数を取得
        total_count = query.count()
        
        # 7. ページネーションを適用して馬のIDを取得（ソート順を保持）
        # ソート順を保持するために、必要なフィールドも含めて取得
        if sort in ['price_desc', 'price_asc']:
            # 価格でのソートの場合は、必要なフィールドを取得
            horses_with_order = query.with_entities(
                Horse.id,
                auction_with_prices.c.price,
                auction_with_prices.c.is_unsold
            )
            
            # ソート順を適用
            if sort == 'price_desc':
                # 未落札を最後に、価格の降順、IDの昇順でソート
                horses_with_order = horses_with_order.order_by(
                    auction_with_prices.c.is_unsold.asc(),  # 未落札を最後に
                    auction_with_prices.c.price.desc().nulls_last(),  # 価格の降順（NULLは最後）
                    Horse.id.asc()  # 同点の場合はIDでソート
                )
            else:  # price_asc
                # 未落札を最後に、価格の昇順、IDの昇順でソート
                horses_with_order = horses_with_order.order_by(
                    auction_with_prices.c.is_unsold.asc(),  # 未落札を最後に
                    auction_with_prices.c.price.asc().nulls_last(),  # 価格の昇順（NULLは最後）
                    Horse.id.asc()  # 同点の場合はIDでソート
                )
            
            # ページネーションを適用
            horses_with_order = horses_with_order.offset(skip).limit(limit).all()
            horse_ids = [horse.id for horse in horses_with_order]
        else:
            # その他のソートの場合はIDのみを取得
            horses_with_order = query.with_entities(Horse.id).offset(skip).limit(limit).all()
            horse_ids = [horse.id for horse in horses_with_order]
        
        # ソート順を保持するためのインデックスマップを作成
        horse_id_to_index = {horse_id: idx for idx, horse_id in enumerate(horse_ids)}
        
        # 10. 最終的な馬のデータを取得
        if horse_ids:
            # 馬の基本情報を取得
            horses = db.query(Horse).filter(Horse.id.in_(horse_ids)).all()
            
            # 各馬の最新オークション情報を取得
            horse_auction_subq = (
                db.query(
                    AuctionHistory.horse_id,
                    func.max(AuctionHistory.id).label('latest_auction_id')
                )
                .group_by(AuctionHistory.horse_id)
                .subquery()
            )
            
            latest_auctions = (
                db.query(
                    AuctionHistory
                )
                .join(
                    horse_auction_subq,
                    and_(
                        AuctionHistory.horse_id == horse_auction_subq.c.horse_id,
                        AuctionHistory.id == horse_auction_subq.c.latest_auction_id
                    )
                )
                .filter(AuctionHistory.horse_id.in_(horse_ids))
                .all()
            )
            
            # 馬IDをキーにした辞書を作成
            auction_dict = {auction.horse_id: auction for auction in latest_auctions}
            
            # 馬のデータにオークション情報を追加
            for horse in horses:
                if horse.id in auction_dict:
                    auction = auction_dict[horse.id]
                    # auction_dateが文字列の場合はそのまま、datetimeの場合はisoformat()を適用
                    auction_date = auction.auction_date
                    if hasattr(auction_date, 'isoformat'):
                        auction_date = auction_date.isoformat()
                    elif auction_date is not None and not isinstance(auction_date, str):
                        auction_date = str(auction_date)
                    
                    # 辞書を直接代入する代わりに、新しいオブジェクトを作成してから代入
                    latest_auction_data = {
                        'price': auction.price,
                        'auction_date': auction_date,
                        'location': auction.auction_house or None,
                        'name': auction.auction_name or auction.horse_name or None
                    }
                    
                    # 既存のlatest_auctionが存在する場合は更新、存在しない場合は新規作成
                    if hasattr(horse, 'latest_auction') and horse.latest_auction is not None:
                        for key, value in latest_auction_data.items():
                            setattr(horse.latest_auction, key, value)
                    else:
                        # 新しいオブジェクトを作成して代入
                        class LatestAuction:
                            def __init__(self, data):
                                self.__dict__.update(data)
                        
                        horse.latest_auction = LatestAuction(latest_auction_data)
            # ソート順を保持するために、元の順序で並べ替え
            horse_dict = {horse.id: horse for horse in horses}
            # horse_idsの順序でソート（存在するIDのみをフィルタリング）
            horses = [horse_dict[horse_id] for horse_id in horse_ids if horse_id in horse_dict]
            # ソート順を保持するために、horse_id_to_indexに基づいてソート
            horses.sort(key=lambda x: horse_id_to_index.get(x.id, float('inf')))
        else:
            horses = []
        
        # 7. 馬IDのリストを取得
        horse_ids = [horse.id for horse in horses]
        
        # 8. 馬IDに紐づく最新のオークション情報を一括取得
        latest_auctions = {}
        if horse_ids:
            # 各馬の最新のオークションIDを取得するサブクエリ
            latest_auction_subq = db.query(
                AuctionHistory.horse_id,
                func.max(AuctionHistory.id).label('latest_auction_id')
            ).filter(
                AuctionHistory.horse_id.in_(horse_ids)
            ).group_by(
                AuctionHistory.horse_id
            ).subquery()
            
            # 最新のオークション情報を取得
            latest_auctions_result = db.query(AuctionHistory).join(
                latest_auction_subq,
                and_(
                    AuctionHistory.id == latest_auction_subq.c.latest_auction_id,
                    AuctionHistory.horse_id == latest_auction_subq.c.horse_id
                )
            ).all()
            
            # 辞書に変換
            latest_auctions = {auction.horse_id: auction for auction in latest_auctions_result}
        
        # 9. 馬データに最新のオークション情報をマージ
        result_horses = []
        for horse in horses:
            try:
                # 馬の基本情報を取得
                latest_auction_unsold = getattr(horse.latest_auction, 'is_unsold', False) if hasattr(horse, 'latest_auction') and horse.latest_auction else False
                
                # デバッグログ（必要に応じてコメントアウト）
                # logger.info(f"Horse {horse.id} - Name: {horse.name}, Latest Auction ID: {getattr(horse.latest_auction, 'id', 'N/A')}, is_unsold: {latest_auction_unsold}")
                
                horse_data = {
                    'id': horse.id,
                    'name': horse.name,
                    'sex': horse.sex,
                    'age': horse.age,
                    'sire': horse.sire,
                    'dam': horse.dam,
                    'dam_sire': horse.dam_sire,
                    'weight': horse.weight,
                    'total_prize_start': horse.total_prize_start,
                    'total_prize_latest': horse.total_prize_latest,
                    'sold_price': horse.sold_price,
                    'auction_date': horse.auction_date,
                    'seller': horse.seller,
                    'disease_tags': horse.disease_tags,
                    'comment': horse.comment,
                    'image_url': horse.image_url,
                    'detail_url': horse.detail_url,
                    'jbis_url': horse.jbis_url,  # jbis_urlを追加
                    'is_unsold': latest_auction_unsold,  # latest_auctionから取得
                    'unsold': latest_auction_unsold  # エイリアス
                }
                
                # 最新のオークション情報があればマージ
                if horse.id in latest_auctions:
                    auction = latest_auctions[horse.id]
                    # オークション情報をマージ
                    auction_data = {
                        'auction_date': auction.auction_date,
                        'price': auction.price,
                        'sold_price': auction.price,  # sold_price の代わりに price を使用
                        'seller': getattr(auction, 'seller', ''),  # seller の存在を確認
                        'comment': getattr(auction, 'comment', ''),  # comment の存在を確認
                        'disease_tags': getattr(horse, 'disease_tags', []),  # horseオブジェクトからdisease_tagsを取得
                        'is_unsold': getattr(auction, 'is_unsold', False)  # is_unsold の存在を確認
                    }
                    horse_data.update(auction_data)
                
                # 初回出品の馬の場合、horsesテーブルの情報を優先
                if horse_data['sold_price'] is None and 'price' in horse_data:
                    horse_data['sold_price'] = horse_data['price']
                
                # オークション情報から主取りフラグを更新
                if horse.id in latest_auctions:
                    auction = latest_auctions[horse.id]
                    horse_data['is_unsold'] = getattr(auction, 'is_unsold', False)
                    horse_data['unsold'] = horse_data['is_unsold']
                    
                    # デバッグログ
                    logger.info(f"Updated horse {horse.id} - is_unsold: {horse_data['is_unsold']} from auction {auction.id}")
                
                # デバッグログ（必要に応じてコメントアウト）
                # logger.info(f"Final horse data for {horse.id} - is_unsold: {horse_data['is_unsold']}, sold_price: {horse_data.get('sold_price')}")
                
                # 結果に追加
                result_horses.append(horse_data)
                
            except Exception as e:
                logger.error(f"Error processing horse {getattr(horse, 'id', 'unknown')}: {str(e)}", exc_info=True)
                continue  # エラーが発生した馬はスキップ
        
        # 10. 結果を返す
        return {
            "horses": result_horses,
            "metadata": {
                "total": total_count,
                "skip": skip,
                "limit": limit,
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error in get_horses: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your request: {str(e)}"
        )

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
        
        # 最新のオークション情報を取得
        latest_auction = db.query(AuctionHistory).filter(
            AuctionHistory.horse_id == horse_id
        ).order_by(AuctionHistory.id.desc()).first()
        
        # auction_date をパース
        auction_date = None
        if horse.auction_date:
            try:
                import json
                parsed_dates = json.loads(horse.auction_date)
                if isinstance(parsed_dates, list) and len(parsed_dates) > 0:
                    auction_date = parsed_dates[0]  # 最初の日付を取得
            except (json.JSONDecodeError, TypeError):
                auction_date = horse.auction_date
        
        # race_record を取得
        race_record = None
        if hasattr(horse, 'race_record') and horse.race_record:
            try:
                # race_record がJSON文字列の場合はパースする
                if isinstance(horse.race_record, str) and horse.race_record.strip().startswith('{'):
                    race_record = json.loads(horse.race_record)
                else:
                    race_record = horse.race_record
            except json.JSONDecodeError:
                race_record = horse.race_record
        else:
            race_record = "未出走"
        
        return {
            "id": horse.id,
            "name": horse.name,
            "sex": horse.sex,
            "age": horse.age,
            "sire": horse.sire,
            "dam": horse.dam,
            "dam_sire": horse.dam_sire,
            "race_record": race_record,  # race_record を追加
            "weight": horse.weight,
            "total_prize_start": horse.total_prize_start,
            "total_prize_latest": horse.total_prize_latest,
            "sold_price": horse.sold_price,
            "auction_date": auction_date,
            "seller": horse.seller,
            "disease_tags": horse.disease_tags,
            "comment": horse.comment,
            "image_url": horse.image_url,
            "detail_url": horse.detail_url,
            "jbis_url": horse.jbis_url,
            "is_unsold": latest_auction.is_unsold if latest_auction else False,
            "unsold": latest_auction.is_unsold if latest_auction else False
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting horse {horse_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting horse: {str(e)}"
        )
