from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from passlib.context import CryptContext
import os
import logging

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 設定をインポート
from ..config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# パスワードのハッシュ化と検証のためのコンテキスト
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ユーザーモデル（簡易的な実装）
class User:
    def __init__(self, username: str, hashed_password: str):
        self.username = username
        self.hashed_password = hashed_password

def get_environment_info():
    """環境情報を取得するヘルパー関数"""
    env = os.getenv("ENV", "development").lower()
    is_prod = env == "production"
    is_ci = os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"
    return {
        "env": env,
        "is_prod": is_prod,
        "is_ci": is_ci,
        "is_dev": not is_prod and not is_ci
    }

# 環境情報を取得
env_info = get_environment_info()

# 環境変数から認証情報を取得（環境に応じてデフォルト値を設定）
def get_env_var(name: str, default: str = None, required: bool = False) -> str:
    """環境変数を取得し、必要に応じてデフォルト値を設定"""
    value = os.getenv(name, default)
    if required and not value and env_info["is_prod"]:
        raise ValueError(f"必須の環境変数 {name} が設定されていません")
    return value

# 認証情報の取得
username = get_env_var("PROD_API_USERNAME", "dev_user", required=env_info["is_prod"] or env_info["is_ci"])
password = get_env_var("PROD_API_PASSWORD", "dev_password", required=env_info["is_prod"] or env_info["is_ci"])

# 開発環境でのみ警告を表示
if env_info["is_dev"] and (not os.getenv("PROD_API_USERNAME") or not os.getenv("PROD_API_PASSWORD")):
    logger.warning("本番環境では必ず PROD_API_USERNAME と PROD_API_PASSWORD を設定してください")

# パスワードの長さを72バイトに制限
if password and len(password.encode('utf-8')) > 72:
    password = password[:72]  # 72バイトを超える場合は切り詰める

def truncate_utf8(text: str, max_bytes: int = 72) -> str:
    """UTF-8エンコード時のバイト数を考慮して文字列を切り詰める"""
    if not text:
        return text
    
    encoded = text.encode('utf-8')[:max_bytes]
    return encoded.decode('utf-8', errors='ignore').rstrip('\x00')

# 環境変数から取得した認証情報を使用
# パスワードをUTF-8エンコードして72バイトに制限
safe_password = truncate_utf8(password, 72)
hashed_password = pwd_context.hash(safe_password)
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

async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Dict[str, str]:
    """
    OAuth2互換のトークンログイン
    
    Args:
        request: FastAPIのリクエストオブジェクト
        form_data: ユーザー名とパスワードを含むフォームデータ
        
    Returns:
        Dict[str, str]: アクセストークンとトークンタイプを含む辞書
        
    Raises:
        HTTPException: 認証に失敗した場合
    """
    # デバッグ情報のロギング
    if env_info["is_dev"]:
        logger.debug(f"認証試行: username={form_data.username}")
        logger.debug(f"環境: {env_info}")
    
    try:
        # 認証処理
        user = authenticate_user(fake_users_db, form_data.username, form_data.password)
        
        if not user:
            error_msg = "認証に失敗しました: ユーザー名またはパスワードが正しくありません"
            if env_info["is_dev"]:
                error_msg = f"{error_msg} (username: {form_data.username})"
            
            logger.warning(error_msg)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_msg,
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # トークン発行
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        
        logger.info(f"認証成功: {user.username}")
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        error_msg = f"認証処理中にエラーが発生しました: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 本番環境では詳細なエラーを表示しない
        if not env_info["is_prod"]:
            detail = error_msg
        else:
            detail = "認証処理中にエラーが発生しました"
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )
