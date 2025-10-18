from fastapi import FastAPI
from .api import app as api_router

# メインアプリケーションとして設定
app = FastAPI()

# ルーターをマウント
app.include_router(api_router, prefix="/api")

# ルートエンドポイント
@app.get("/")
async def root():
    return {"message": "Welcome to the API"}

# Vercel が app 変数を探すため、明示的に公開
app = app
