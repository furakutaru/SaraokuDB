import os
import sys
import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# デバッグ：環境変数を表示
logger.info(f"DATABASE_URL: {'SET' if os.environ.get('DATABASE_URL') else 'NOT SET'}")
logger.info(f"PORT: {os.environ.get('PORT', 'NOT SET')}")

# シンプルなFastAPIアプリケーション
app = FastAPI(
    title="サラブレッドオークション データベース",
    version="1.0.0",
    docs_url="/docs"
)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400
)

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "サラブレッドオークション データベース API",
        "version": "1.0.0",
        "status": "running",
        "port": os.environ.get("PORT", "8000"),
        "database_url_set": bool(os.environ.get('DATABASE_URL'))
    }

@app.get("/health")
async def health():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy"}

@app.get("/api/horses")
async def get_horses():
    """馬データ取得エンドポイント"""
    return {
        "horses": [],
        "metadata": {
            "last_updated": "2026-02-12T03:41:00Z",
            "total_horses": 0,
            "total_auction_records": 0
        }
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    try:
        uvicorn.run("debug_main:app", host="0.0.0.0", port=port, reload=False)
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
