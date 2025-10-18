from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import app as api_router

# メインアプリケーションとして設定
app = FastAPI(title="SaraokuDB API", version="1.0.0")

# CORSミドルウェアを追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なオリジンを指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターをマウント
app.include_router(api_router, prefix="/api")

# ルートエンドポイント
@app.get("/")
async def root():
    return {
        "message": "Welcome to SaraokuDB API",
        "docs": "/docs",
        "health_check": "/api/health"
    }

# Vercel が app 変数を探すため、明示的に公開
app = app
