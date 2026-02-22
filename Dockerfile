FROM python:3.11-slim

WORKDIR /app

# 依存関係をインストール
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# アプリケーションコードをコピー（backend と api を含める）
COPY . /app

# Python が /app を参照できるようにする
ENV PYTHONPATH=/app

# Render は $PORT を割り当てる
EXPOSE 8000

# Uvicorn で FastAPI を起動
# 環境変数展開を行うため shell 形式で指定（JSON 形式だと ${PORT} が展開されません）
CMD uvicorn api.main:app --host 0.0.0.0 --port $PORT
