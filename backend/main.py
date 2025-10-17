import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

# Import database and models
from database.models import Base, get_db, engine
from database.schemas import HorseResponse

# Import routers
from routers import horses
from auth.auth import router as auth_router
from api.health import router as health_router

# Create FastAPI app
app = FastAPI(
    title="サラブレッドオークション データベース",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None
)

# Include routers
app.include_router(health_router, prefix="/api")
app.include_router(horses.router, prefix="/api")
app.include_router(auth_router, prefix="/api", tags=["auth"])

# CORS settings
origins = [
    "http://localhost:3000",  # Next.js 開発サーバー
    "http://127.0.0.1:3000",  # ローカルホストの別表記
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
