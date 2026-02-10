import os
import sys
import uvicorn
import logging
from fastapi import FastAPI, Depends, HTTPException, status, Request
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from typing import Dict, Any, List, Optional, Union, Callable
from sqlalchemy.orm import Session
from sqlalchemy import text

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# SQLAlchemyのログレベルを設定
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
logger = logging.getLogger(__name__)

# Import database and models
try:
    from database.models import Base, get_db, engine
    from database.schemas import HorseResponse
    logger.info("Database imports successful")
except ImportError as e:
    logger.error(f"Database import error: {e}")
    sys.exit(1)

# Import routers
try:
    from routers import horses
    from routers.auction_histories import router as auction_histories_router
    from health import router as health_router
    logger.info("Router imports successful")
except ImportError as e:
    logger.error(f"Router import error: {e}")
    sys.exit(1)

# 認証コンポーネントを取得
auth_components = {}

def get_auth_components() -> Dict[str, Any]:
    """認証コンポーネントを遅延読み込み"""
    if not auth_components:
        try:
            from auth.jwt_auth import get_current_user, get_password_hash
            from auth.auth import authenticate_user, create_access_token
            auth_components.update({
                'get_current_user': get_current_user,
                'get_password_hash': get_password_hash,
                'authenticate_user': authenticate_user,
                'create_access_token': create_access_token
            })
            logger.info("認証コンポーネントの読み込みに成功しました")
        except ImportError as e:
            logger.warning(f"認証コンポーネントの読み込みに失敗しました: {e}")
    return auth_components

def check_db_connection() -> bool:
    """データベース接続をチェック"""
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        print("データベースに接続されました")
        return True
    except Exception as e:
        print(f"データベース接続エラー: {str(e)}")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # アプリケーション起動時の処理
    if not check_db_connection():
        print("警告: データベースに接続できませんでした")
    else:
        print("データベース接続が正常に確立されました")
    
    print("\n=== アプリケーション起動中 ===")
    try:
        # テーブルが存在しない場合は作成を試みる
        Base.metadata.create_all(bind=engine)
        print("テーブルの確認が完了しました")
    except Exception as e:
        print(f"テーブル作成中にエラーが発生しました: {str(e)}")
    
    yield
    
    # アプリケーション終了時の処理
    print("\n=== アプリケーション終了中 ===")
    try:
        # データベース接続をクリーンアップ
        engine.dispose()
        print("データベース接続をクリーンアップしました")
    except Exception as e:
        print(f"シャットダウン中のエラー: {e}")

# Create FastAPI app
app = FastAPI(
    title="サラブレッドオークション データベース",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan
)

# CORSミドルウェアの設定 - すべてのオリジンを許可（開発用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # すべてのオリジンを許可
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],  # すべてのヘッダーを許可
    expose_headers=["*"],
    max_age=86400  # 24時間
)

# Include routers
# ルーターをインポート
from routers.horses import router as horses_router
from routers.auction_histories import router as auction_histories_router

# 各ルーターをマウント
app.include_router(horses_router, prefix="/api/horses")
app.include_router(auction_histories_router, prefix="/api/auction_histories")

# ヘルスチェックエンドポイント
app.include_router(health_router)

# 静的ファイルの配信
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    logger.warning("Static files directory not found, skipping static file serving")

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "サラブレッドオークション データベース API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

# エラーハンドラ
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"detail": "エンドポイントが見つかりません"}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "内部サーバーエラーが発生しました"}
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Railwayのデフォルトポート
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
