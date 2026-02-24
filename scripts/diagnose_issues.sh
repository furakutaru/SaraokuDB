#!/bin/bash

# 問題解決のための診断スクリプト

API_BASE_URL="https://saraoku-db.vercel.app"

echo "=== 問題診断 ==="
echo "1. URLリダイレクトの確認"
echo "元URL: $API_BASE_URL/api/horses"
response=$(curl -s -I "$API_BASE_URL/api/horses?limit=24&skip=0&sort=price_desc")
echo "レスポンスヘッダー:"
echo "$response"
echo ""

echo "2. リダイレクト先の確認"
redirect_url=$(echo "$response" | grep -i location | cut -d' ' -f2 | tr -d '\r')
if [[ -n "$redirect_url" ]]; then
    echo "リダイレクト先: $redirect_url"
    echo "リダイレクト先のステータス:"
    curl -s -I "$redirect_url" | head -1
else
    echo "リダイレクトは検出されませんでした"
fi

echo ""
echo "3. キャッシュエンドポイントの確認"
cache_response=$(curl -s -I "$API_BASE_URL/api/cache?action=stats")
echo "キャッシュAPIステータス:"
echo "$cache_response"

echo ""
echo "4. Vercel関数の直接テスト"
echo "関数URL: https://saraoku-db.vercel.app/api/horses"
direct_response=$(curl -s -w "Status: %{http_code}, Time: %{time_total}s\n" -o /dev/null "$API_BASE_URL/api/horses?limit=5")
echo "$direct_response"
