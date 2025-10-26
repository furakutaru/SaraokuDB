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

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
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
from api.health import router as health_router

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

# Create FastAPI app
app = FastAPI(
    title="サラブレッドオークション データベース",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None
)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # すべてのオリジンを許可（本番環境では適切に制限してください）
    allow_credentials=True,
    allow_methods=["*"],  # すべてのHTTPメソッドを許可
    allow_headers=["*"],  # すべてのヘッダーを許可
    expose_headers=["*"]  # すべてのレスポンスヘッダーを公開
)

# Include routers
# 各ルーターのprefixは各ファイルで設定されているため、ここでは指定しない
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(debug_router)
app.include_router(horses.router)
app.include_router(auction_histories_router)

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

# アプリケーション起動時にデータベース接続を確認
@app.on_event("startup")
async def startup_event():
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

# アプリケーション終了時に実行
@app.on_event("shutdown")
async def shutdown_event():
    print("アプリケーションを終了します")
    try:
        # データベース接続を閉じるなどのクリーンアップ処理
        if 'engine' in globals():
            engine.dispose()
    except Exception as e:
        print(f"シャットダウン中のエラー: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
