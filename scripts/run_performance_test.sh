#!/bin/bash

# SaraokuDB APIパフォーマンス測定スクリプト（実行可能版）
# フェーズ2-3: パフォーマンス測定

# 実際のデプロイ先URLに設定（ユーザーが変更）
API_BASE_URL="https://saraoku-db.vercel.app"
RESULTS_FILE="performance_results_$(date +%Y%m%d_%H%M%S).csv"

echo "=== SaraokuDB API パフォーマンス測定 ==="
echo "測定開始時刻: $(date)"
echo "APIベースURL: $API_BASE_URL"
echo ""

# ヘッダー出力
echo "テストケース,レスポンスタイム(ms),ステータスコード,キャッシュヒット" > $RESULTS_FILE

# テストケース1: キャッシュなし（初回アクセス）
echo "1. キャッシュなしテスト（初回アクセス）"
for i in {1..3}; do
    echo "  計測中..."
    start_time=$(date +%s%3N)
    response=$(curl -s -w "%{http_code}" -o /dev/null "$API_BASE_URL/api/horses?limit=24&skip=0&sort=price_desc")
    end_time=$(date +%s%3N)
    response_time=$((end_time - start_time))
    echo "初回アクセス,$response_time,$response,false" >> $RESULTS_FILE
    echo "  試行 $i: ${response_time}ms (ステータス: $response)"
    sleep 1
done

echo ""

# テストケース2: キャッシュあり（2回目以降）
echo "2. キャッシュありテスト"
for i in {1..5}; do
    start_time=$(date +%s%3N)
    response=$(curl -s -w "%{http_code}" -o /dev/null "$API_BASE_URL/api/horses?limit=24&skip=0&sort=price_desc")
    end_time=$(date +%s%3N)
    response_time=$((end_time - start_time))
    echo "キャッシュヒット,$response_time,$response,true" >> $RESULTS_FILE
    echo "  キャッシュ $i: ${response_time}ms"
done

echo ""

# テストケース3: 異なるソート条件
echo "3. 異なるソート条件のテスト"
sort_types=("price_desc" "price_asc" "name_asc" "name_desc")
for sort in "${sort_types[@]}"; do
    echo "  ソート: $sort"
    for i in {1..2}; do
        start_time=$(date +%s%3N)
        response=$(curl -s -w "%{http_code}" -o /dev/null "$API_BASE_URL/api/horses?limit=24&skip=0&sort=$sort")
        end_time=$(date +%s%3N)
        response_time=$((end_time - start_time))
        echo "ソート_${sort},$response_time,$response,true" >> $RESULTS_FILE
        echo "    ${response_time}ms"
    done
done

echo ""

# テストケース4: ページネーションテスト
echo "4. ページネーションテスト"
for page in {0..2}; do
    skip=$((page * 24))
    echo "  ページ $page (skip=$skip)"
    for i in {1..2}; do
        start_time=$(date +%s%3N)
        response=$(curl -s -w "%{http_code}" -o /dev/null "$API_BASE_URL/api/horses?limit=24&skip=$skip&sort=price_desc")
        end_time=$(date +%s%3N)
        response_time=$((end_time - start_time))
        echo "ページ_${page},$response_time,$response,true" >> $RESULTS_FILE
        echo "    ${response_time}ms"
    done
done

echo ""
echo "=== 測定完了 ==="
echo "結果ファイル: $RESULTS_FILE"

# 平均値計算と表示
echo ""
echo "=== 結果サマリー ==="
first_avg=$(awk -F',' '/初回アクセス/ {sum+=$2; count++} END {if(count>0) printf "%.0f", sum/count; else print "N/A"}' $RESULTS_FILE)
cache_avg=$(awk -F',' '/キャッシュヒット/ {sum+=$2; count++} END {if(count>0) printf "%.0f", sum/count; else print "N/A"}' $RESULTS_FILE)

echo "初回アクセス平均: ${first_avg}ms"
echo "キャッシュヒット平均: ${cache_avg}ms"

if [[ "$first_avg" != "N/A" && "$cache_avg" != "N/A" ]]; then
    improvement=$(( (first_avg - cache_avg) * 100 / first_avg ))
    echo "改善率: ${improvement}%"
fi

# キャッシュ統計の取得
echo ""
echo "=== キャッシュ統計 ==="
curl -s "$API_BASE_URL/api/cache?action=stats" | jq '.' 2>/dev/null || echo "キャッシュ統情報の取得に失敗しました"
