from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional

# ルーターの定義
auth_router = APIRouter(prefix="/auth", tags=["auth"])
debug_router = APIRouter(prefix="/debug", tags=["debug"])
router = APIRouter()
router.include_router(auth_router)
router.include_router(debug_router)

# JWT認証関連のインポート
from .jwt_auth import (
    authenticate_user,
    create_access_token,
    fake_users_db,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_active_user,
    login_for_access_token
)

class Token(BaseModel):
    access_token: str
    token_type: str

from typing import Optional

class TokenData(BaseModel):
    username: Optional[str] = None

@auth_router.post("/token", response_model=Token)
async def login_for_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    認証トークンを発行するエンドポイント
    
    Args:
        request: FastAPIのリクエストオブジェクト
        form_data: ユーザー名とパスワードを含むフォームデータ
        
    Returns:
        Token: アクセストークンとトークンタイプ
    """
    return await login_for_access_token(request, form_data)

# テスト用のエンドポイント（認証が必要）
@auth_router.get("/users/me/")
async def read_users_me(current_user: dict = Depends(get_current_active_user)):
    return {
        "username": current_user.username,
        "message": "認証に成功しました"
    }

# デバッグ用のエンドポイント（本番環境では無効化することを推奨）
@debug_router.get("/hash")
async def debug_hash(password: str):
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_context.hash(password)
    return {
        "hashed_password": hashed,
        "verification": pwd_context.verify(password, hashed)
    }
