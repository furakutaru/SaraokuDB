-- インデックスを活用するための追加インデックス
-- 現在のインデックスではDISTINCT ONが最適化されないため

-- 1. nameのみのインデックスを追加（DISTINCT ON用）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_horses_name 
ON horses (name);

-- 2. sold_priceのインデックスを再作成（NULLS LAST対応）
DROP INDEX CONCURRENTLY IF EXISTS idx_horses_sold_price;
CREATE INDEX CONCURRENTLY idx_horses_sold_price 
ON horses (sold_price DESC NULLS LAST);

-- 3. 複合インデックスの再作成
DROP INDEX CONCURRENTLY IF EXISTS idx_horses_name_updated_at;
CREATE INDEX CONCURRENTLY idx_horses_name_updated_at 
ON horses (name, updated_at DESC NULLS LAST);

-- 4. 統計情報更新
ANALYZE horses;

-- 5. 実行計画の再確認
EXPLAIN (ANALYZE, BUFFERS) 
SELECT DISTINCT ON (name) id, name, updated_at
FROM horses
WHERE name IS NOT NULL
ORDER BY name, updated_at DESC;

-- 6. ソートクエリの確認
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, name, sold_price
FROM horses
WHERE id = ANY(ARRAY[1,2,3,4,5])
ORDER BY sold_price DESC NULLS LAST;
