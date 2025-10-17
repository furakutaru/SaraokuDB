from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/token")
async def get_token():
    return {"access_token": "test-token", "token_type": "bearer"}
