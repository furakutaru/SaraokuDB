FROM python:3.11-slim

WORKDIR /app

# まずFastAPIとuvicornをインストール
RUN pip install fastapi uvicorn

# アプリケーションファイルをコピー
COPY simple_app.py .

# ポートを公開
EXPOSE 8080

# アプリケーションを起動
CMD ["python", "-u", "simple_app.py"]
