from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# 認証関連の設定をインポート
from backend.config import SECRET_KEY, ALGORITHM
from backend.auth.jwt_auth import oauth2_scheme, get_current_user, User, get_user, fake_users_db

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
