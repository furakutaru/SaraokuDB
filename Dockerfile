FROM python:3.11-slim

WORKDIR /app

# 依存関係をインストール
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY backend/ .

# RenderはPORT環境変数を自動設定
EXPOSE $PORT

# デバッグ版で起動して環境変数を確認
CMD ["python", "debug_main.py"]
