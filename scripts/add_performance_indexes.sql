-- パフォーマンス最適化のためのインデックス追加
-- フェーズ2: DB最適化 - インデックス追加

-- 1. horsesテーブルのインデックス
-- 重複除去クエリ（PARTITION BY name ORDER BY updated_at DESC）の最適化
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_horses_name_updated_at 
ON horses (name, updated_at DESC);

-- 価格ソートの最適化
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_horses_sold_price 
ON horses (sold_price DESC);

-- 2. auctionsテーブルのインデックス（存在する場合）
-- オークション履歴検索の最適化
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auctions_horse_id_auction_date 
-- ON auctions (horse_id, auction_date DESC);

-- 3. auction_historiesテーブルのインデックス（既存の確認と追加）
-- 既に存在する場合はスキップ
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auction_histories_horse_id 
-- ON auction_histories (horse_id);

-- インデックス作成状況の確認
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename IN ('horses', 'auctions', 'auction_histories')
    AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

-- インデックス使用統計の確認
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename IN ('horses', 'auctions', 'auction_histories')
    AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;
