import os
import sys
from pathlib import Path

# Add the project root and backend directory to the Python path
project_root = Path(__file__).parent.parent
backend_dir = Path(__file__).parent

# Add both project root and backend directory to path
for path in [str(project_root), str(backend_dir)]:
    if path not in sys.path:
        sys.path.insert(0, path)

import uvicorn
import logging
from fastapi import FastAPI, Depends, HTTPException, status, Request
from contextlib import asynccontextmanager

# ロギングの設定（Railway では stdout に出力）
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# SQLAlchemyのログレベルを設定
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
logger = logging.getLogger(__name__)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import logging
from typing import Dict, Any, List, Optional, Union, Callable
from sqlalchemy.orm import Session
from sqlalchemy import text

# Import database and models
from database.models import Base, get_db, engine
from database.schemas import HorseResponse

# Import routers
from routers import horses
from routers.auction_histories import router as auction_histories_router
from health import router as health_router

# 認証コンポーネントを取得
auth_components = {}

def get_auth_components() -> Dict[str, Any]:
    """認証コンポーネントを遅延読み込み
    
    Returns:
        Dict[str, Any]: 認証に必要なコンポーネントの辞書
    """
    global auth_components
    if not auth_components:
        from auth import get_auth_components as _get_auth_components
        auth_components = _get_auth_components()
    return auth_components

# 認証ルーターをインポート
from auth import auth_router, debug_router

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

# CORSミドルウェアの設定
# 環境変数 CORS_ORIGINS があれば追加（カンマ区切り）、なければデフォルト
_cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://saraoku-db.vercel.app",
]
_cors_env = os.environ.get("CORS_ORIGINS", "")
if _cors_env:
    _cors_origins.extend(origin.strip() for origin in _cors_env.split(",") if origin.strip())

# Vercel の全サブドメインを許可（プレビューURL対応）
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "*",
        "Authorization",
        "Content-Type",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Methods"
    ],
    expose_headers=[
        "*",
        "Content-Disposition",
        "Content-Length",
        "Content-Type"
    ],
    max_age=86400  # 24時間
)

# Include routers
# ルーターをインポート
from routers.horses import router as horses_router
from routers.auction_histories import router as auction_histories_router

# 各ルーターをマウント
app.include_router(horses_router, prefix="/api/horses")
app.include_router(auction_histories_router, prefix="/api/auction_histories")

# その他のルーター
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(debug_router)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "サラブレッドオークションデータベースAPIへようこそ！"}

# ヘルスチェックエンドポイント
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Service is running"}

# テスト用のシンプルなエンドポイント
@app.get("/test")
async def test_endpoint():
    return {"message": "Test endpoint is working"}

# データベース接続テスト用エンドポイント
@app.get("/test-db")
async def test_db():
    from database.models import SessionLocal
    
    db = SessionLocal()
    try:
        # シンプルなクエリを実行
        result = db.execute(text("SELECT 1"))
        return {
            "message": "Database connection successful", 
            "result": result.scalar()
        }
    except Exception as e:
        return {
            "message": "Database connection failed", 
            "error": str(e)
        }
    finally:
        db.close()

# データベース接続を確認する関数
def check_db_connection():
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        print("データベースに接続されました")
        return True
    except Exception as e:
        print(f"データベース接続エラー: {str(e)}")
        return False

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
