from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from .jwt_auth import (
    authenticate_user,
    create_access_token,
    fake_users_db,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_active_user
)

router = APIRouter(tags=["auth"])

class Token(BaseModel):
    access_token: str
    token_type: str

from typing import Optional

class TokenData(BaseModel):
    username: Optional[str] = None

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"認証試行: username={form_data.username}")
    print(f"fake_users_db: {fake_users_db}")
    
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    print(f"認証結果: {user}")
    
    if not user:
        print("認証失敗: ユーザー名またはパスワードが正しくありません")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー名またはパスワードが正しくありません",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# テスト用のエンドポイント（認証が必要）
@router.get("/users/me/")
async def read_users_me(current_user: dict = Depends(get_current_active_user)):
    return {
        "username": current_user.username,
        "message": "認証に成功しました"
    }
