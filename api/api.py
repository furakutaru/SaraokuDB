from fastapi import FastAPI
from .health import router as health_router
from .auth.login import router as auth_router

app = FastAPI()

# ルーターを登録
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth")

# ルートエンドポイント
@app.get("/")
async def root():
    return {"message": "Welcome to the API"}
