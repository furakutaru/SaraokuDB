#!/bin/bash

# バックエンドディレクトリに移動
cd "$(dirname "$0")/backend"

# バックエンドサーバーを起動
echo "バックエンドサーバーを起動しています..."
python3 -m uvicorn main:app --reload --port 3002 &
BACKEND_PID=$!

# フロントエンドディレクトリに移動
cd "../static-frontend"

# 依存関係をインストール（初回のみ）
if [ ! -d "node_modules" ]; then
    echo "依存関係をインストールしています..."
    npm install
fi

# フロントエンドサーバーを起動
echo "フロントエンドサーバーを起動しています..."
npm run dev &
FRONTEND_PID=$!

# 終了時の処理
trap "echo '\nサーバーを停止しています...'; kill $BACKEND_PID $FRONTEND_PID 2> /dev/null; exit 0" INT

echo -e "\n開発サーバーが起動しました！"
echo "- フロントエンド: http://localhost:3000"
echo "- バックエンドAPI: http://localhost:3002"
echo "\n終了するには Ctrl+C を押してください"

# プロセスが終了するのを待つ
wait $BACKEND_PID $FRONTEND_PID
