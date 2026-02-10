#!/usr/bin/env python3
import os
import sys
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ロギング設定
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

try:
    # FastAPIアプリケーション
    app = FastAPI(title="SaraokuDB API Debug")
    logger.info("FastAPI app created successfully")
except Exception as e:
    logger.error(f"Failed to create FastAPI app: {e}")
    sys.exit(1)

try:
    # CORS設定 - すべてのオリジンを許可
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS middleware configured successfully")
except Exception as e:
    logger.error(f"Failed to configure CORS: {e}")
    sys.exit(1)

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Hello World", "status": "running"}

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "healthy"}

@app.get("/api/horses")
async def get_horses():
    logger.info("Horses endpoint accessed")
    return {"horses": [], "total": 0}

@app.options("/api/horses")
async def options_horses():
    logger.info("OPTIONS horses endpoint accessed")
    return {"status": "ok"}

if __name__ == "__main__":
    try:
        import uvicorn
        port = int(os.environ.get("PORT", 8080))
        logger.info(f"Starting server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
