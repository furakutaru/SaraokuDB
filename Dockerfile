FROM python:3.11-slim

WORKDIR /app

# backendディレクトリに移動
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# backendディレクトリからすべてのコードをコピー
COPY backend/ .

# Railwayは自動的にPORT環境変数を設定
EXPOSE 8000

# 直接Pythonを実行
CMD ["python", "main.py"]
