import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション
app = FastAPI(title="SaraokuDB API")

# CORS設定 - すべてのオリジンを許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(__import__('os').environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
