#!/bin/bash

# インデックス追加実行スクリプト
# 接続情報
HOST="ep-sweet-term-adm0rzzh-pooler.c-2.us-east-1.aws.neon.tech"
USER="neondb_owner"
DATABASE="neondb"
PORT="5432"

echo "=== データベース接続情報 ==="
echo "ホスト: $HOST"
echo "ユーザー: $USER"
echo "データベース: $DATABASE"
echo "ポート: $PORT"
echo ""

echo "=== インデックス追加を開始します ==="

# インデックス追加SQLを実行
psql -h "$HOST" -p "$PORT" -U "$USER" -d "$DATABASE" -f scripts/add_performance_indexes.sql

echo ""
echo "=== インデックス追加完了 ==="
