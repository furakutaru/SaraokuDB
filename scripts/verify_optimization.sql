-- 統計情報更新と最適化確認
-- フェーズ2-2完了後の確認

-- 1. 統計情報を更新（重要）
ANALYZE horses;

-- 2. 最適化後のクエリ実行計画を確認
EXPLAIN (ANALYZE, BUFFERS) 
SELECT DISTINCT ON (name) id, name, updated_at
FROM horses
WHERE name IS NOT NULL
ORDER BY name, updated_at DESC;

-- 3. ソートクエリの最適化確認
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, name, sold_price
FROM horses
WHERE id = ANY(ARRAY[1,2,3,4,5])  -- サンプルID
ORDER BY sold_price DESC NULLS LAST;

-- 4. インデックス使用状況の確認
SELECT 
    indexrelname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan
FROM pg_stat_user_indexes 
WHERE schemaname = 'public' 
    AND relname = 'horses'
    AND indexrelname LIKE 'idx_%';

-- 5. テーブル統計情報の確認
SELECT 
    n_live_tup as "行数",
    n_dead_tup as "不要行数",
    last_vacuum as "最後のVACUUM",
    last_autovacuum as "最後の自動VACUUM",
    last_analyze as "最後のANALYZE",
    last_autoanalyze as "最後の自動ANALYZE"
FROM pg_stat_user_tables 
WHERE tablename = 'horses';
