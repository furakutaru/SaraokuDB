#!/bin/bash

# DATABASE_URLを分解するスクリプト
# 使用方法: ./parse_db_url.sh "postgresql://user:pass@host:5432/dbname?sslmode=require"

if [ $# -eq 0 ]; then
    echo "使用方法: $0 \"DATABASE_URL\""
    echo "例: $0 \"postgresql://user:pass@host:5432/dbname?sslmode=require\""
    exit 1
fi

DB_URL="$1"

# URLから各部分を抽出
USER=$(echo "$DB_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
PASSWORD=$(echo "$DB_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
HOST=$(echo "$DB_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
PORT=$(echo "$DB_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DATABASE=$(echo "$DB_URL" | sed -n 's/.*\/\([^?]*\)?.*/\1/p')

echo "=== データベース接続情報 ==="
echo "ホスト: $HOST"
echo "ユーザー: $USER"
echo "パスワード: $PASSWORD"
echo "ポート: $PORT"
echo "データベース: $DATABASE"
echo ""
echo "=== psql接続コマンド ==="
echo "psql -h $HOST -p $PORT -U $USER -d $DATABASE"
echo ""
echo "=== pg_dumpバックアップコマンド ==="
echo "pg_dump -h $HOST -p $PORT -U $USER -d $DATABASE > backup_\$(date +%Y%m%d_%H%M%S).sql"
echo ""
echo "=== インデックス追加実行コマンド ==="
echo "psql -h $HOST -p $PORT -U $USER -d $DATABASE -f scripts/add_performance_indexes.sql"
