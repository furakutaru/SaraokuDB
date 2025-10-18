import os

# 認証関連の設定
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")  # 本番環境では必ず変更してください
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
