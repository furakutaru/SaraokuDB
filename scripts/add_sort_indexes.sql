-- 昇順ソート用インデックス追加
-- price_ascソートのパフォーマンス改善

-- 昇順ソート用インデックスを追加
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_horses_sold_price_asc 
ON horses (sold_price ASC NULLS LAST);

-- nameソート用インデックスも追加（念のため）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_horses_name_asc 
ON horses (name ASC NULLS LAST);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_horses_name_desc 
ON horses (name DESC NULLS LAST);

-- 統計情報更新
ANALYZE horses;

-- インデックス確認
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'horses' 
    AND indexname LIKE 'idx_%'
ORDER BY indexname;
