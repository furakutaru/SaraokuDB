from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request, APIRouter
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi import status
from passlib.context import CryptContext
import os
import logging
import sys
from pathlib import Path
from pydantic import BaseModel

# パスワードのハッシュ化と検証のためのコンテキスト
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ルーターの定義
auth_router = APIRouter(prefix="/auth", tags=["auth"])
debug_router = APIRouter(prefix="/debug", tags=["debug"])
router = APIRouter()
router.include_router(auth_router)
router.include_router(debug_router)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# ルーターの定義
router = APIRouter()

# ロギングの設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 設定の読み込み
import os
from typing import Optional

# 環境変数から直接取得
SECRET_KEY: Optional[str] = os.getenv("SECRET_KEY")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# 環境変数が設定されていない場合は設定モジュールから読み込む
if not SECRET_KEY:
    try:
        # 本番環境用
        from backend.config import SECRET_KEY as BK_SECRET_KEY, \
                                 ALGORITHM as BK_ALGORITHM, \
                                 ACCESS_TOKEN_EXPIRE_MINUTES as BK_ACCESS_TOKEN_EXPIRE_MINUTES
        SECRET_KEY = BK_SECRET_KEY
        ALGORITHM = BK_ALGORITHM
        ACCESS_TOKEN_EXPIRE_MINUTES = BK_ACCESS_TOKEN_EXPIRE_MINUTES
        logger.info("Using backend.config for configuration")
    except ImportError:
        try:
            # ローカル開発環境用
            from config import SECRET_KEY as LOCAL_SECRET_KEY, \
                               ALGORITHM as LOCAL_ALGORITHM, \
                               ACCESS_TOKEN_EXPIRE_MINUTES as LOCAL_ACCESS_TOKEN_EXPIRE_MINUTES
            SECRET_KEY = LOCAL_SECRET_KEY
            ALGORITHM = LOCAL_ALGORITHM
            ACCESS_TOKEN_EXPIRE_MINUTES = LOCAL_ACCESS_TOKEN_EXPIRE_MINUTES
            logger.info("Using local config for configuration")
        except ImportError as e:
            logger.error("Failed to import configuration: %s", str(e))
            logger.warning("Using environment variables for configuration")

# 最終的な設定値をログに出力
logger.info("最終的な設定値:")
logger.info(f"SECRET_KEY: {'*' * 8}{SECRET_KEY[-4:] if SECRET_KEY else 'None'}")
logger.info(f"ALGORITHM: {ALGORITHM}")
logger.info(f"ACCESS_TOKEN_EXPIRE_MINUTES: {ACCESS_TOKEN_EXPIRE_MINUTES}")

# 必須パラメータの検証
if not SECRET_KEY:
    error_msg = "SECRET_KEYが設定されていません。環境変数または設定ファイルを確認してください。"
    logger.error(error_msg)
    raise ValueError(error_msg)

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

def get_environment_credentials():
    """環境変数から認証情報を取得する"""
    # ユーザー名は固定
    username = "furakutaru"
    password = os.getenv("PROD_API_PASSWORD", "")
    
    logger.info("=" * 50)
    logger.info("環境変数から認証情報を取得中...")
    logger.info(f"GitHub Actions環境: {os.getenv('GITHUB_ACTIONS') == 'true'}")
    logger.info(f"ユーザー名: {username}")
    logger.info(f"生のパスワード長: {len(password) if password else 0}")
    logger.info(f"トリム後パスワード長: {len(password.strip()) if password else 0}")
    logger.info(f"パスワード先頭5文字: {password[:5] if password else 'None'}")
    logger.info(f"パスワード末尾5文字: {password[-5:] if password and len(password) > 5 else 'None'}")
    logger.info("=" * 50)
    
    # 環境変数のデバッグ情報を出力
    logger.info("=" * 50)
    logger.info("認証情報の設定:")
    logger.info(f"ユーザー名: {username}")
    logger.info(f"PROD_API_PASSWORD の長さ: {len(password) if password else 0}")
    
    # 環境変数の一覧をデバッグ出力
    env_vars = [k for k in os.environ.keys() if "PASS" in k.upper() or "SECRET" in k.upper() or "TOKEN" in k.upper()]
    logger.info(f"環境変数一覧: {', '.join(env_vars)}")
    
    if not password:
        logger.warning("PROD_API_PASSWORD が設定されていません")
    else:
        logger.info("環境変数からパスワードを正常に取得しました")
    
    logger.info(f"環境情報: {env_info}")
    logger.info(f"ユーザー名: {username}")
    if password:
        logger.info(f"パスワードが設定されました: {'*' * 8} (長さ: {len(password)}文字)")
    else:
        logger.warning("パスワードが設定されていません")
    
    return username, password

# 認証情報を取得
username, password = get_environment_credentials()

# パスワードのデバッグ情報をログに出力
if password:
    logger.info(f"パスワードの先頭5文字: {password[:5]}")
    logger.info(f"パスワードの長さ: {len(password)}")
else:
    logger.warning("パスワードが設定されていません")

# ユーザーデータベース（簡易的な実装）
fake_users_db = {
    "furakutaru": {
        "username": "furakutaru",
        "hashed_password": pwd_context.hash(password[:72]) if password else "",
    }
}

# ユーザーをデータベースに登録
logger.info(f"ユーザーデータベースに登録されました: {list(fake_users_db.keys())}")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワードを検証する"""
    logger.debug(f"[DEBUG] パスワード検証開始: username=furakutaru")
    logger.debug(f"[DEBUG] 入力パスワード: {plain_password}")
    logger.debug(f"[DEBUG] ハッシュパスワード: {hashed_password[:10]}...")
    
    if not plain_password or not hashed_password:
        logger.error("パスワードまたはハッシュが空です")
        return False
        
    try:
        # パスワードを72バイトに制限して検証
        is_valid = pwd_context.verify(plain_password[:72], hashed_password)
        logger.debug(f"[DEBUG] パスワード検証結果: {is_valid}")
        
        if not is_valid:
            logger.error("パスワードが一致しません")
            # ハッシュの形式を確認
            logger.debug(f"[DEBUG] ハッシュの接頭辞: {hashed_password[:6]}")
            logger.debug(f"[DEBUG] 想定される接頭辞: $2b$12$")
            
        return is_valid
    except Exception as e:
        logger.error(f"パスワード検証エラー: {str(e)}")
        logger.exception("スタックトレース:")
        return False

def get_password_hash(password: str) -> str:
    """パスワードをハッシュ化する（72バイトに制限）"""
    return pwd_context.hash(password[:72] if password else "")

def get_user(db, username: str) -> Optional[User]:
    """データベースからユーザーを取得する"""
    logger.debug(f"[DEBUG] ユーザー取得開始: username={username}")
    from sqlalchemy.orm import Session
    from database.models import User as DBUser, SessionLocal
    
    try:
        db_session = SessionLocal()
        logger.debug("[DEBUG] データベースセッションを取得しました")
        
        # データベースからユーザーを取得
        db_user = db_session.query(DBUser).filter(DBUser.username == username).first()
        
        if db_user:
            logger.debug(f"[DEBUG] データベースからユーザーを取得: {db_user.username}, 有効: {db_user.is_active}")
            logger.debug(f"[DEBUG] ハッシュパスワードの長さ: {len(db_user.hashed_password) if db_user.hashed_password else 0}")
            return User(username=db_user.username, hashed_password=db_user.hashed_password)
        else:
            logger.debug(f"[DEBUG] ユーザーが見つかりません: {username}")
            return None
    except Exception as e:
        logger.error(f"[ERROR] ユーザー取得中にエラーが発生: {str(e)}")
        logger.exception("スタックトレース:")
        return None
    finally:
        if 'db_session' in locals():
            db_session.close()
            logger.debug("[DEBUG] データベースセッションをクローズしました")

def authenticate_user(fake_db, username: str, password: str):
    """ユーザーを認証する"""
    user = get_user(fake_db, username)
    if not user:
        logger.error(f"ユーザーが見つかりません: {username}")
        return False
    if not verify_password(password, user.hashed_password):
        logger.error(f"パスワードが一致しません: {username}")
        return False
    logger.info(f"認証成功: {username}")
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """JWTトークンを作成する"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# OAuth2パスワードベアラースキーム
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """現在のユーザーを取得する"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認証情報を検証できませんでした",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user(fake_users_db, username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """現在のアクティブなユーザーを取得する"""
    return current_user

@auth_router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """認証トークンを発行するエンドポイント
    
    Args:
        form_data: ユーザー名とパスワードを含むフォームデータ
        
    Returns:
        Token: アクセストークンとトークンタイプ
        
    Raises:
        HTTPException: 認証に失敗した場合
    """
    logger.info(f"Login attempt for user: {form_data.username}")
    
    # ユーザー認証
    user = authenticate_user({}, form_data.username, form_data.password)
    
    if not user:
        logger.warning(f"認証失敗: ユーザー名またはパスワードが正しくありません - {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー名またはパスワードが正しくありません",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # アクセストークンの有効期限を設定
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # アクセストークンを作成
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    logger.info(f"認証成功: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}

# デバッグ用のエンドポイント
@router.get("/debug")
async def debug_endpoint(current_user: User = Depends(get_current_active_user)):
    """デバッグ用のエンドポイント"""
    return {
        "message": "認証に成功しました",
        "username": current_user.username,
        "is_authenticated": True
    }