from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, Dict, Any
import logging
from jose import JWTError, jwt
import os
from datetime import datetime, timedelta

# ロガーの設定
logger = logging.getLogger(__name__)

router = APIRouter()
# Use absolute path for OpenAPI/security scheme to match deployed routes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# 環境変数から設定を取得
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

async def verify_token(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    JWTトークンを検証し、ペイロードを返す
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認証情報が無効です",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # トークンの検証
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception

@router.get("/users/me")
async def read_current_user(payload: dict = Depends(verify_token)):
    """
    現在のユーザー情報を取得するエンドポイント
    """
    username = payload.get("sub")
    # 実際のプロジェクトでは、ここでデータベースからユーザー情報を取得します
    return {
        "username": username,
        "email": f"{username}@example.com",
        "is_active": True,
        "token_data": {
            "exp": payload.get("exp"),
            "iat": payload.get("iat")
        }
    }

@router.get("/api/protected-route")
async def protected_route(payload: dict = Depends(verify_token)):
    """
    保護されたエンドポイントの例
    """
    username = payload.get("sub")
    return {
        "message": f"こんにちは、{username}さん！",
        "status": "認証成功",
        "token_info": {
            "username": username,
            "expires_at": datetime.fromtimestamp(payload.get("exp")).isoformat(),
            "issued_at": datetime.fromtimestamp(payload.get("iat")).isoformat()
        }
    }
