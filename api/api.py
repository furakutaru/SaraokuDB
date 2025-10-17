from fastapi import FastAPI
from .health import router as health_router
from .auth.login import router as login_router
from .auth.token import router as token_router

app = FastAPI()

# ルーターを登録
app.include_router(health_router, prefix="/api")
app.include_router(login_router, prefix="/api")
app.include_router(token_router, prefix="/api")

# ルートエンドポイント
@app.get("/")
async def root():
    return {"message": "Welcome to the API"}
