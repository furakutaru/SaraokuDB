# 認証関連のモジュールをエクスポート
# モジュールのインポートを遅延読み込みに変更
# 循環インポートを防ぐため、必要な時点で直接インポートする

# パブリックAPI
def get_auth_components():
    """認証コンポーネントを取得する"""
    from .jwt_auth import (
        SECRET_KEY,
        ALGORITHM,
        ACCESS_TOKEN_EXPIRE_MINUTES,
        authenticate_user,
        create_access_token,
        get_current_user,
        get_current_active_user,
        login_for_access_token,
    )
    
    return {
        'SECRET_KEY': SECRET_KEY,
        'ALGORITHM': ALGORITHM,
        'ACCESS_TOKEN_EXPIRE_MINUTES': ACCESS_TOKEN_EXPIRE_MINUTES,
        'authenticate_user': authenticate_user,
        'create_access_token': create_access_token,
        'get_current_user': get_current_user,
        'get_current_active_user': get_current_active_user,
        'login_for_access_token': login_for_access_token,
    }

from .auth import auth_router, debug_router, router

__all__ = [
    'get_auth_components',
    'User',
    'get_user',
    'fake_users_db',
    'authenticate_user',
    'create_access_token',
    'auth_router',
    'debug_router',
    'router'
]
