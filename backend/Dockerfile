FROM python:3.11-slim

WORKDIR /app

# 依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# Railwayは自動的にPORT環境変数を設定
# ポート8000でリッスン（Railwayの内部設定）
EXPOSE 8000

# ヘルスチェックとアプリケーション起動
CMD ["sh", "-c", "python -c \"import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=int(__import__('os').environ.get('PORT', 8000)), log_level='info')\""]
