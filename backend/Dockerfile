FROM python:3.11-slim

WORKDIR /app

# 依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# Railwayは自動的にPORT環境変数を設定
EXPOSE 8000

# 直接Pythonを実行してuvicornのimportエラーを回避
CMD ["python", "main.py"]
