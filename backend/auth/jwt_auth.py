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

# 環境情報をログに出力
logger.info(f"環境情報: {env_info}")
logger.info(f"ユーザー名: {username}")
logger.info(f"パスワード長: {len(password) if password else 0}文字")

# 開発環境でのみ警告を表示
if env_info["is_dev"] and (not os.getenv("PROD_API_USERNAME") or not os.getenv("PROD_API_PASSWORD")):
    logger.warning("本番環境では必ず PROD_API_USERNAME と PROD_API_PASSWORD を設定してください")

# パスワードの長さを72バイトに制限
if password and len(password.encode('utf-8')) > 72:
    password = password[:72]  # 72バイトを超える場合は切り詰める
    logger.warning(f"パスワードが72バイトを超えたため、切り詰めました: {len(password)}文字")

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

# ユーザー情報をログに出力（パスワードのハッシュは一部のみ表示）
logger.info(f"ユーザー名: {username}")
logger.info(f"パスワードハッシュ: {hashed_password[:10]}...")

# ユーザーデータベースを初期化
fake_users_db = {
    username: User(
        username=username,
        hashed_password=hashed_password
    )
}

# データベースの内容をログに出力
logger.info(f"ユーザーデータベースに登録されました: {list(fake_users_db.keys())}")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

def get_user(db, username: str):
    """データベースからユーザーを取得する
    
    Args:
        db: ユーザーデータベース
        username: 検索するユーザー名
        
    Returns:
        User: 見つかったユーザーオブジェクト、見つからない場合はNone
    """
    logger.debug(f"[get_user] ユーザー検索: username={username}")
    logger.debug(f"[get_user] データベースキー: {list(db.keys())}")
    
    if username in db:
        user = db[username]
        logger.debug(f"[get_user] ユーザーが見つかりました: {username}")
        
        if isinstance(user, dict):
            logger.debug("[get_user] 辞書からUserオブジェクトを作成")
            return User(**user)
            
        logger.debug("[get_user] 既存のUserオブジェクトを返却")
        return user  # Userオブジェクトをそのまま返す
    
    logger.warning(f"[get_user] ユーザーが見つかりません: {username}")
    return None

def authenticate_user(fake_db, username: str, password: str):
    """ユーザー認証を行う
    
    Args:
        fake_db: ユーザーデータベース
        username: ユーザー名
        password: パスワード
        
    Returns:
        User: 認証に成功した場合はユーザーオブジェクト、失敗した場合はNone
    """
    logger.debug(f"[authenticate_user] 認証開始: username={username}")
    
    # パスワードの長さを72バイトに制限（UTF-8エンコードを考慮）
    safe_password = truncate_utf8(password, 72)
    logger.debug(f"[authenticate_user] パスワードを切り詰め: {len(safe_password)}文字")
    
    # ユーザーを取得
    user = get_user(fake_db, username)
    if not user:
        logger.warning(f"[authenticate_user] ユーザーが見つかりません: {username}")
        return None
    
    # パスワード検証
    logger.debug(f"[authenticate_user] パスワードを検証: user.hashed_password={user.hashed_password}")
    is_valid = verify_password(safe_password, user.hashed_password)
    
    if not is_valid:
        logger.warning(f"[authenticate_user] パスワードが一致しません: username={username}")
        return None
    
    logger.debug(f"[authenticate_user] 認証成功: {username}")
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
    logger.setLevel(logging.DEBUG)  # デバッグログを有効化
    logger.debug("=" * 50)
    logger.debug("認証処理を開始します")
    logger.debug(f"リクエストURL: {request.url}")
    logger.debug(f"HTTPメソッド: {request.method}")
    logger.debug(f"リクエストヘッダー: {dict(request.headers)}")
    logger.debug(f"フォームデータ: username={form_data.username}, password={'*' * len(form_data.password) if form_data.password else 'None'}")
    logger.debug(f"環境変数 USERNAME: {os.getenv('PROD_API_USERNAME', 'Not Set')}")
    logger.debug(f"環境変数 PASSWORD 長さ: {len(os.getenv('PROD_API_PASSWORD', '')) if os.getenv('PROD_API_PASSWORD') else 'Not Set'}")
    logger.debug(f"SECRET_KEY: {os.getenv('SECRET_KEY', 'Not Set')}")
    logger.debug(f"ALGORITHM: {ALGORITHM}")
    logger.debug(f"ACCESS_TOKEN_EXPIRE_MINUTES: {ACCESS_TOKEN_EXPIRE_MINUTES}")
    logger.debug(f"fake_users_db キー: {list(fake_users_db.keys())}")
    logger.debug(f"fake_users_db 値: {fake_users_db}")
    
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
