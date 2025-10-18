from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from passlib.context import CryptContext
import os

# 設定をインポート
from ..config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# パスワードのハッシュ化と検証のためのコンテキスト
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ユーザーモデル（簡易的な実装）
class User:
    def __init__(self, username: str, hashed_password: str):
        self.username = username
        self.hashed_password = hashed_password

# 環境変数から認証情報を取得
username = os.getenv("PROD_API_USERNAME")
password = os.getenv("PROD_API_PASSWORD")

if not username or not password:
    raise ValueError("PROD_API_USERNAME と PROD_API_PASSWORD の環境変数が設定されていません")

# パスワードの長さを72バイトに制限
if len(password.encode('utf-8')) > 72:
    password = password[:72]  # 72バイトを超える場合は切り詰める

# 環境変数から取得した認証情報を使用
hashed_password = pwd_context.hash(password)
fake_users_db = {
    username: User(
        username=username,
        hashed_password=hashed_password
    )
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

def get_user(db, username: str):
    if username in db:
        user = db[username]
        if isinstance(user, dict):
            return User(**user)
        return user  # Userオブジェクトをそのまま返す
    return None

def authenticate_user(fake_db, username: str, password: str):
    # パスワードの長さを72バイトに制限
    if len(password.encode('utf-8')) > 72:
        password = password[:72]  # 72バイトを超える場合は切り詰める
        
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認証情報が無効です",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user(fake_users_db, username=username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    # 必要に応じてユーザーのアクティブ状態をチェック
    return current_user

async def login_for_access_token(form_data: OAuth2PasswordRequestForm) -> Dict[str, str]:
    """
    OAuth2互換のトークンログイン
    """
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
