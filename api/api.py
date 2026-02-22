import sys
import os
import logging
from pathlib import Path
from typing import List, Optional
import json

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# 環境変数の読み込み
load_dotenv()

# 認証関連の設定をインポート
from backend.config import SECRET_KEY, ALGORITHM
from backend.auth.jwt_auth import oauth2_scheme, get_current_user, User, get_user, fake_users_db

# データベース関連のインポート
from backend.database.models import get_db, Horse
from backend.services.horse_service import HorseService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # フロントエンドのURL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware to log requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise

# Import routers
from .health import router as health_router
from .auth.login import router as auth_router

# Include routers with prefixes
app.include_router(health_router, prefix="/api")
# auth_router を /api/auth にマウント
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the API"}

# ヘルスチェックエンドポイント
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# get_current_userは既にインポート済み

# 保護されたエンドポイント
@app.get("/api/users/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user

# データベースセッションの依存関係
def get_db_session():
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()

# 馬データを取得するエンドポイント
@app.get("/api/horses")
async def get_horses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)):
    """
    馬データの一覧をデータベースから取得します。
    
    Parameters:
    - skip: スキップするレコード数（ページネーション用）
    - limit: 取得する最大レコード数（ページネーション用）
    """
    def safe_json_parse(json_str, default=None):
        try:
            if json_str and isinstance(json_str, str):
                return json.loads(json_str)
            return default if default is not None else []
        except json.JSONDecodeError:
            return default if default is not None else []

    try:
        # デバッグ用にデータベース接続を確認
        logger.info("データベースから馬データを取得します...")
        
        # 直接クエリを実行してデータを取得
        horses = db.query(Horse).offset(skip).limit(limit).all()
        logger.info(f"取得した馬データの数: {len(horses)}")
        
        if not horses:
            logger.warning("データベースから馬データを取得できませんでした")
            return {"horses": []}
        
        # データベースの結果をシリアライズ
        serialized_horses = []
        for horse in horses:
            try:
                # 各フィールドの型をチェックして適切に処理
                def get_value(field_value, default=None):
                    if field_value is None:
                        return default
                    # 文字列の場合はJSONとしてパースを試みる
                    if isinstance(field_value, str):
                        try:
                            parsed = json.loads(field_value)
                            if isinstance(parsed, list):
                                return parsed[-1] if parsed else default
                            return parsed
                        except json.JSONDecodeError:
                            return field_value
                    # 数値やその他の型はそのまま返す
                    return field_value
                
                # 各フィールドの値を取得
                sex = get_value(horse.sex, "不明")
                age = get_value(horse.age)
                sold_price = get_value(horse.sold_price)
                comment = get_value(horse.comment, "")
                auction_date = get_value(horse.auction_date)
                seller = get_value(horse.seller, "不明")
                
                # デバッグ用に馬の基本情報をログに出力
                logger.debug(f"処理中の馬データ - ID: {horse.id}, 名前: {horse.name}")
                
                serialized_horse = {
                    "id": horse.id,
                    "auction_id": str(horse.auction_id) if horse.auction_id is not None else f"unknown_{horse.id}",
                    "name": horse.name or "未登録",
                    "sex": sex,
                    "age": age,
                    "sire": horse.sire or "不明",
                    "dam": horse.dam or "不明",
                    "damsire": horse.dam_sire or "不明",
                    "weight": horse.weight,
                    "total_prize_start": horse.total_prize_start,
                    "total_prize_latest": horse.total_prize_latest,
                    "sold_price": sold_price,
                    "auction_date": auction_date,
                    "seller": seller,
                    "comment": comment,
                    "image_url": horse.image_url or "",
                    "primary_image": horse.primary_image or "",
                    "jbis_url": horse.jbis_url or "",
                    "detail_url": horse.detail_url or "",
                    "unsold_count": horse.unsold_count or 0,
                    "created_at": horse.created_at.isoformat() if horse.created_at else None,
                    "updated_at": horse.updated_at.isoformat() if horse.updated_at else None
                }
                serialized_horses.append(serialized_horse)
                
            except Exception as e:
                logger.error(f"馬データのシリアライズ中にエラーが発生しました (ID: {getattr(horse, 'id', 'unknown')}): {str(e)}", exc_info=True)
                continue  # エラーが発生したレコードはスキップ
                
        logger.info(f"シリアライズされた馬データの数: {len(serialized_horses)}")
        
        if not serialized_horses:
            logger.warning("有効な馬データが見つかりませんでした")
            return {"horses": []}
            
        return {"horses": serialized_horses}
        
    except Exception as e:
        logger.error(f"馬データの取得中にエラーが発生しました: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"馬データの取得中にエラーが発生しました: {str(e)}"
        )

# 馬データを新規作成するエンドポイント
@app.post("/api/horses")
@app.post("/api/horses/")
async def create_horse_endpoint(
    payload: dict,
    db: Session = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    try:
        service = HorseService()
        created = service.create_horse(db, payload)
        return {
            "id": created.id,
            "auction_id": getattr(created, "auction_id", None),
            "name": getattr(created, "name", None),
            "is_unsold": getattr(created, "is_unsold", None),
            "sold_price": getattr(created, "sold_price", None),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating horse: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

# 単一の馬データを取得するエンドポイント
@app.get("/api/horses/{horse_id}")
async def get_horse_by_id(horse_id: int, db: Session = Depends(get_db_session)):
    try:
        horse = db.query(Horse).filter(Horse.id == horse_id).first()
        if not horse:
            raise HTTPException(status_code=404, detail="Horse not found")

        def safe_json_parse(json_str, default=None):
            try:
                if json_str and isinstance(json_str, str):
                    parsed = json.loads(json_str)
                    if isinstance(parsed, list):
                        return parsed[-1] if parsed else default
                    return parsed
                return json_str
            except json.JSONDecodeError:
                return json_str

        return {
            "id": horse.id,
            "name": horse.name or "未登録",
            "current_prize": getattr(horse, "current_prize", None),
            "last_prize_update": getattr(horse, "last_prize_update", None),
            "update_interval_months": getattr(horse, "update_interval_months", None),
            "is_retired": getattr(horse, "is_retired", None),
            "next_update_due_date": getattr(horse, "next_update_due_date", None),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching horse {horse_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

# 馬の情報を部分更新（PATCH）
@app.patch("/api/horses/{horse_id}")
async def patch_horse(
    horse_id: int,
    payload: dict,
    db: Session = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    try:
        horse = db.query(Horse).filter(Horse.id == horse_id).first()
        if not horse:
            raise HTTPException(status_code=404, detail="Horse not found")

        allowed_fields = {
            "current_prize",
            "last_prize_update",
            "update_interval_months",
            "is_retired",
            "next_update_due_date",
        }

        updated = False
        for key, value in payload.items():
            if key in allowed_fields:
                setattr(horse, key, value)
                updated = True

        if not updated:
            raise HTTPException(status_code=400, detail="更新可能なフィールドが含まれていません")

        db.commit()
        db.refresh(horse)

        return {
            "id": horse.id,
            "current_prize": getattr(horse, "current_prize", None),
            "last_prize_update": getattr(horse, "last_prize_update", None),
            "update_interval_months": getattr(horse, "update_interval_months", None),
            "is_retired": getattr(horse, "is_retired", None),
            "next_update_due_date": getattr(horse, "next_update_due_date", None),
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error patching horse {horse_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

# 馬の情報を更新（PUT）
@app.put("/api/horses/{horse_id}")
async def put_horse(
    horse_id: int,
    payload: dict,
    db: Session = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    try:
        horse = db.query(Horse).filter(Horse.id == horse_id).first()
        if not horse:
            raise HTTPException(status_code=404, detail="Horse not found")

        allowed_fields = {
            "current_prize",
            "last_prize_update",
            "update_interval_months",
            "is_retired",
            "next_update_due_date",
        }

        updated = False
        for key, value in payload.items():
            if key in allowed_fields:
                setattr(horse, key, value)
                updated = True

        if not updated:
            raise HTTPException(status_code=400, detail="更新可能なフィールドが含まれていません")

        db.commit()
        db.refresh(horse)

        return {
            "id": horse.id,
            "current_prize": getattr(horse, "current_prize", None),
            "last_prize_update": getattr(horse, "last_prize_update", None),
            "update_interval_months": getattr(horse, "update_interval_months", None),
            "is_retired": getattr(horse, "is_retired", None),
            "next_update_due_date": getattr(horse, "next_update_due_date", None),
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error putting horse {horse_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

# オークション履歴を取得するエンドポイント
@app.get("/api/auction_histories")
async def get_auction_histories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)):
    """
    オークション履歴の一覧をデータベースから取得します。
    
    Parameters:
    - skip: スキップするレコード数（ページネーション用）
    - limit: 取得する最大レコード数（ページネーション用）
    """
    def safe_json_parse(json_str, default=None):
        try:
            if json_str and isinstance(json_str, str):
                return json.loads(json_str)
            return default if default is not None else []
        except json.JSONDecodeError:
            return default if default is not None else []

    try:
        # オークション履歴を取得（馬テーブルから生成）
        horses = db.query(Horse).filter(Horse.auction_date.isnot(None)).offset(skip).limit(limit).all()
        
        auction_histories = []
        for horse in horses:
            try:
                # 安全にJSONをパース
                auction_dates = safe_json_parse(horse.auction_date, [])
                prices = safe_json_parse(horse.sold_price, [])
                sellers = safe_json_parse(horse.seller, [])
                
                # 各履歴エントリを生成
                for i, (auction_date, price, seller) in enumerate(zip(auction_dates, prices, sellers)):
                    auction_histories.append({
                        "id": f"{horse.id}_{i}",
                        "horse_id": horse.id,
                        "horse_name": horse.name or "不明",
                        "auction_date": auction_date,
                        "price": price,
                        "seller": seller or "不明",
                        "is_unsold": price == 0 or price is None
                    })
                    
            except Exception as e:
                logger.error(f"オークション履歴の処理中にエラーが発生しました (馬ID: {getattr(horse, 'id', 'unknown')}): {str(e)}")
                continue  # エラーが発生したレコードはスキップ
        
        return {"auction_histories": auction_histories}
        
    except Exception as e:
        logger.error(f"オークション履歴の取得中にエラーが発生しました: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"オークション履歴の取得中にエラーが発生しました: {str(e)}"
        )

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    logger.warning(f"404 Not Found: {request.method} {request.url}")
    return JSONResponse(
        status_code=404,
        content={"detail": "Not Found"}
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc: Exception):
    logger.error(f"500 Internal Server Error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )
