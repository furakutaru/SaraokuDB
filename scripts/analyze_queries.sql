-- クエリ最適化分析と改善案
-- フェーズ2-2: クエリ最適化

-- 1. 現在のクエリ実行計画を確認
EXPLAIN (ANALYZE, BUFFERS) 
WITH RankedHorses AS (
    SELECT id, name, updated_at,
           ROW_NUMBER() OVER(PARTITION BY name ORDER BY updated_at DESC) as rn
    FROM horses
    WHERE name IS NOT NULL
)
SELECT id FROM RankedHorses WHERE rn = 1;

-- 2. 最適化版クエリ（インデックス活用）
EXPLAIN (ANALYZE, BUFFERS)
SELECT DISTINCT ON (name) id, name, updated_at
FROM horses
WHERE name IS NOT NULL
ORDER BY name, updated_at DESC;

-- 3. ページネーション最適化
-- 現在の方法：全件取得後にスライス
EXPLAIN (ANALYZE, BUFFERS)
WITH RankedHorses AS (
    SELECT id, name, updated_at,
           ROW_NUMBER() OVER(PARTITION BY name ORDER BY updated_at DESC) as rn
    FROM horses
    WHERE name IS NOT NULL
),
PaginatedHorses AS (
    SELECT id
    FROM RankedHorses 
    WHERE rn = 1
    ORDER BY updated_at DESC
    LIMIT 24 OFFSET 0
)
SELECT h.id, h.name, h.sold_price
FROM horses h
JOIN PaginatedHorses ph ON h.id = ph.id
ORDER BY h.sold_price DESC;

-- 4. 改善版：直接ページネーション
EXPLAIN (ANALYZE, BUFFERS)
WITH RankedHorses AS (
    SELECT id, name, updated_at, sold_price,
           ROW_NUMBER() OVER(PARTITION BY name ORDER BY updated_at DESC) as rn
    FROM horses
    WHERE name IS NOT NULL
),
PaginatedHorses AS (
    SELECT id, sold_price
    FROM RankedHorses 
    WHERE rn = 1
    ORDER BY sold_price DESC
    LIMIT 24 OFFSET 0
)
SELECT h.id, h.name, h.sold_price
FROM horses h
JOIN PaginatedHorses ph ON h.id = ph.id
ORDER BY h.sold_price DESC;

-- 5. ソートインデックスの有効性確認
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, name, sold_price
FROM horses
WHERE id = ANY(ARRAY[1,2,3,4,5])  -- サンプルID配列
ORDER BY sold_price DESC;

-- 6. 統計情報の更新（重要）
ANALYZE horses;

-- 7. テーブル統計情報の確認
SELECT 
    schemaname,
    tablename,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables 
WHERE tablename = 'horses';
