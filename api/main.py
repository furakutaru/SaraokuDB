from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# メインアプリケーションとして設定
app = FastAPI(
    title="SaraokuDB API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORSミドルウェアを追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なオリジンを指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# リクエストログ用のミドルウェア
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

# ルーターのインポート
import sys
from pathlib import Path

# プロジェクトのルートをパスに追加
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# ルーターをインポート
from api.health import router as health_router
from api.auth.login import router as auth_router
from api.protected import router as protected_router

# ルーターをマウント
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(protected_router, prefix="/api", tags=["protected"])

# ルートエンドポイント
@app.get("/")
async def root():
    return {
        "message": "Welcome to SaraokuDB API",
        "docs": "/docs",
        "health_check": "/api/health"
    }

# 404エラーハンドラ
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"detail": f"Not Found: {request.url}"}
    )

# グローバルエラーハンドラ
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )

# Vercel が app 変数を探すため、明示的に公開
app = app
