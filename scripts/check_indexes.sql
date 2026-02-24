-- インデックス確認用クエリ
-- 修正版：正しい列名を使用

-- 1. 作成されたインデックスの確認
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'horses'
    AND indexname LIKE 'idx_%'
ORDER BY indexname;

-- 2. インデックス使用統計の確認
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename = 'horses'
    AND indexname LIKE 'idx_%'
ORDER BY indexname;

-- 3. テーブルの基本情報
SELECT 
    schemaname,
    tablename,
    tableowner,
    tablespace
FROM pg_tables 
WHERE tablename = 'horses';
