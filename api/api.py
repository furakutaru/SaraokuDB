from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
import sys
from pathlib import Path

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
app.include_router(auth_router, prefix="/api/auth")

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the API"}

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
