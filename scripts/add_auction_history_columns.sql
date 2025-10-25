-- オークション履歴テーブルに新しいカラムを追加
ALTER TABLE auction_histories 
ADD COLUMN IF NOT EXISTS horse_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS sire_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS dam_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS damsire_name VARCHAR(255);

-- 検索パフォーマンス向上のためのインデックスを追加
CREATE INDEX IF NOT EXISTS idx_auction_histories_horse_info 
ON auction_histories (horse_name, sire_name, dam_name, damsire_name);

CREATE INDEX IF NOT EXISTS idx_auction_histories_auction_date 
ON auction_histories (auction_date);

-- インデックスの作成状況を確認
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'auction_histories' 
ORDER BY indexname;
