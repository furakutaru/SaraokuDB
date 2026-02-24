#!/bin/bash

# SaraokuDB APIパフォーマンス測定スクリプト
# フェーズ2-3: パフォーマンス測定

API_BASE_URL="https://your-domain.vercel.app"  # 実際のドメインに置き換え
RESULTS_FILE="performance_results_$(date +%Y%m%d_%H%M%S).csv"

echo "=== SaraokuDB API パフォーマンス測定 ==="
echo "測定開始時刻: $(date)"
echo ""

# ヘッダー出力
echo "テストケース,レスポンスタイム(ms),ステータスコード,キャッシュヒット" > $RESULTS_FILE

# テストケース1: キャッシュなし（初回アクセス）
echo "1. キャッシュなしテスト（初回アクセス）"
for i in {1..5}; do
    start_time=$(date +%s%3N)
    response=$(curl -s -w "%{http_code}" -o /dev/null "$API_BASE_URL/api/horses?limit=24&skip=0&sort=price_desc")
    end_time=$(date +%s%3N)
    response_time=$((end_time - start_time))
    echo "初回アクセス,$response_time,$response,false" >> $RESULTS_FILE
    echo "  試行 $i: ${response_time}ms"
done

echo ""

# テストケース2: キャッシュあり（2回目以降）
echo "2. キャッシュありテスト"
for i in {1..10}; do
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
    for i in {1..3}; do
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
    for i in {1..3}; do
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

# 平均値計算
echo ""
echo "=== 結果サマリー ==="
echo "初回アクセス平均:" $(awk -F',' '/初回アクセス/ {sum+=$2; count++} END {if(count>0) print int(sum/count); else print "N/A"}' $RESULTS_FILE) "ms"
echo "キャッシュヒット平均:" $(awk -F',' '/キャッシュヒット/ {sum+=$2; count++} END {if(count>0) print int(sum/count); else print "N/A"}' $RESULTS_FILE) "ms"
