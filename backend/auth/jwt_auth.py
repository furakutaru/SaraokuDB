from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from passlib.context import CryptContext
import os
import logging

# ロギングの設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 設定をインポート
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# パスワードのハッシュ化と検証のためのコンテキスト
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ユーザーモデル（簡易的な実装）
class User:
    def __init__(self, username: str, hashed_password: str):
        self.username = username
        self.hashed_password = hashed_password

# 環境変数から認証情報を取得（デフォルト値付き）
username = os.getenv("PROD_API_USERNAME", "admin")
password = os.getenv("PROD_API_PASSWORD", "admin123")

# デバッグ用ログ
print(f"[DEBUG] Username: {username}")
print(f"[DEBUG] Password: {'*' * len(password) if password else 'None'}")

def truncate_utf8(text: str, max_bytes: int = 72) -> str:
    """UTF-8エンコード時のバイト数を考慮して文字列を切り詰める"""
    if not text:
        return text
    
    # パスワードの長さを72バイトに制限
    encoded = text.encode('utf-8') 
    if len(encoded) > max_bytes:
        encoded = encoded[:max_bytes]
    return encoded.decode('utf-8', errors='ignore').rstrip('\x00')

# 環境変数から取得した認証情報を使用
# パスワードをUTF-8エンコードして72バイトに制限
safe_password = truncate_utf8(password, 72)
hashed_password = pwd_context.hash(safe_password)

# ユーザーデータベースの初期化
fake_users_db = {
    username: User(
        username=username,
        hashed_password=hashed_password
    )
}

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
    # パスワードの長さを72バイトに制限（UTF-8エンコードを考慮）
    safe_password = truncate_utf8(password, 72)
    
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(safe_password, user.hashed_password):
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

async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()) -> Dict[str, str]:
    """
    OAuth2互換のトークンログイン
    """
    logger.debug(f"認証リクエスト受信: {request.method} {request.url}")
    logger.debug(f"リクエストヘッダー: {dict(request.headers)}")
    logger.debug(f"認証試行: username={form_data.username}")
    logger.debug(f"環境変数 USERNAME: {os.getenv('PROD_API_USERNAME')}")
    logger.debug(f"環境変数 PASSWORD 長さ: {len(os.getenv('PROD_API_PASSWORD', '')) if os.getenv('PROD_API_PASSWORD') else '未設定'}")
    
    try:
        logger.debug(f"fake_users_db キー: {list(fake_users_db.keys())}")
        
        # ユーザー認証
        user = authenticate_user(fake_users_db, form_data.username, form_data.password)
        logger.debug(f"認証結果: {user is not None}")
        
        if not user:
            logger.warning(f"認証失敗: ユーザー名またはパスワードが正しくありません (username: {form_data.username})")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="ユーザー名またはパスワードが正しくありません",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # トークン発行
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        logger.info(f"認証成功: {user.username}")
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        logger.error(f"認証処理中にエラーが発生しました: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"認証処理中にエラーが発生しました: {str(e)}"
        )
    
    return {"access_token": access_token, "token_type": "bearer"}
