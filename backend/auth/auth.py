from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from .jwt_auth import (
    authenticate_user,
    create_access_token,
    fake_users_db,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_active_user,
    login_for_access_token
)

router = APIRouter(tags=["auth"])

class Token(BaseModel):
    access_token: str
    token_type: str

from typing import Optional

class TokenData(BaseModel):
    username: Optional[str] = None

@router.post("/token", response_model=Token)
async def login_for_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    return await login_for_access_token(request, form_data)

# テスト用のエンドポイント（認証が必要）
@router.get("/users/me/")
async def read_users_me(current_user: dict = Depends(get_current_active_user)):
    return {
        "username": current_user.username,
        "message": "認証に成功しました"
    }
