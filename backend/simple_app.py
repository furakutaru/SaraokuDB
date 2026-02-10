#!/usr/bin/env python3
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# FastAPIアプリケーション
app = FastAPI(title="SaraokuDB API Debug")

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
    return {"message": "Hello World", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/horses")
async def get_horses():
    return {"horses": [], "total": 0}

@app.options("/api/horses")
async def options_horses():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
