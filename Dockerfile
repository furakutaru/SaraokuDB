FROM python:3.11-slim

WORKDIR /app

# 依存関係をインストール
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY backend/ .

# ヘルスチェックを無効化（一時的な対策）
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#   CMD curl -f http://localhost:8000/ || exit 1

EXPOSE 8000

# デバッグ情報を表示してから起動
CMD ["sh", "-c", "echo 'Starting app...' && echo 'PORT:' $PORT && python main.py"]
