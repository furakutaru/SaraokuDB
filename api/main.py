from fastapi import FastAPI
from .api import app

# メインアプリケーションとして設定
api = FastAPI()

# ルーターをマウント
api.mount("/api", app)

# ルートエンドポイント
@api.get("/")
async def root():
    return {"message": "Welcome to the API"}

# Vercel が api 変数を探すため、明示的に公開
__all__ = ['api']
