FROM python:3.11-slim

WORKDIR /app

# FastAPIとuvicornをインストール
RUN pip install fastapi uvicorn

# アプリケーションファイルをコピー
COPY simple_app.py main.py

# ポートを公開
EXPOSE 8080

# アプリケーションを起動
CMD ["python", "-u", "main.py"]
