import { NextResponse } from 'next/server';
import { neon } from '@neondatabase/serverless';

// データベース接続を設定
if (!process.env.DATABASE_URL) {
    throw new Error('DATABASE_URL environment variable is not defined');
}

const sql = neon(process.env.DATABASE_URL);

/**
 * 馬の一覧を取得するAPI
 */
export async function GET(request: Request) {
    try {
        const { searchParams } = new URL(request.url);
        const skip = parseInt(searchParams.get('skip') || '0', 10);
        const limit = parseInt(searchParams.get('limit') || '24', 10);
        const sort = searchParams.get('sort') || 'price_desc';
        const latestAuctionOnly = searchParams.get('latest_auction') === 'true';

        console.log(`[API/Horses] Fetching horses: skip=${skip}, limit=${limit}, sort=${sort}, latest=${latestAuctionOnly}`);

        // 2. 重複（同名）を除去するための代表的なIDを取得（最新の updated_at を優先）
        let repIdsResult: any[];
        if (latestAuctionOnly) {
            // 最新のオークション日を取得
            const latestDateResult = await sql`SELECT MAX(auction_date) as max_date FROM horses WHERE auction_date IS NOT NULL`;
            const latestDate = latestDateResult[0]?.max_date;

            if (!latestDate) {
                repIdsResult = [];
            } else {
                repIdsResult = await sql`
                    WITH RankedHorses AS (
                        SELECT id, name, updated_at,
                               ROW_NUMBER() OVER(PARTITION BY name ORDER BY updated_at DESC) as rn
                        FROM horses
                        WHERE name IS NOT NULL AND auction_date = ${latestDate}
                    )
                    SELECT id FROM RankedHorses WHERE rn = 1
                `;
            }
        } else {
            repIdsResult = await sql`
                WITH RankedHorses AS (
                    SELECT id, name, updated_at,
                           ROW_NUMBER() OVER(PARTITION BY name ORDER BY updated_at DESC) as rn
                    FROM horses
                    WHERE name IS NOT NULL
                )
                SELECT id FROM RankedHorses WHERE rn = 1
            `;
        }

        const repIds = repIdsResult.map(r => r.id);
        const totalCount = repIds.length;

        if (totalCount === 0) {
            return NextResponse.json({
                horses: [],
                metadata: { total: 0, skip, limit }
            });
        }

        // 3. ページネーション適用
        const paginatedIds = repIds.slice(skip, skip + limit);

        if (paginatedIds.length === 0) {
            return NextResponse.json({
                horses: [],
                metadata: { total: totalCount, skip, limit }
            });
        }

        // 4. 詳細データを取得（ソート順に応じてクエリを選択）
        let horsesResult;
        const selectFields = sql`id, name, sex, age, sire, dam, dam_sire, sold_price, auction_date, seller, weight, image_url, is_unsold, race_records, total_prize_start, total_prize_latest, disease_tags, detail_url, jbis_url, is_broodmare`;

        if (sort === 'price_asc') {
            horsesResult = await sql`SELECT ${selectFields} FROM horses WHERE id = ANY(${paginatedIds}) ORDER BY sold_price ASC`;
        } else if (sort === 'name_asc') {
            horsesResult = await sql`SELECT ${selectFields} FROM horses WHERE id = ANY(${paginatedIds}) ORDER BY name ASC`;
        } else if (sort === 'name_desc') {
            horsesResult = await sql`SELECT ${selectFields} FROM horses WHERE id = ANY(${paginatedIds}) ORDER BY name DESC`;
        } else {
            // Default: price_desc
            horsesResult = await sql`SELECT ${selectFields} FROM horses WHERE id = ANY(${paginatedIds}) ORDER BY sold_price DESC`;
        }

        // 5. フロントエンド形式に整形
        const horsesData = horsesResult.map(h => ({
            ...h,
            // ページによって damsire と dam_sire が混在している場合への対応
            damsire: h.dam_sire,
            // ページによって auction_url と detail_url が混在している場合への対応
            auction_url: h.detail_url,
            race_records: h.race_records || { total_prize_money: 0 },
            auction_history: [],
        }));

        return NextResponse.json({
            horses: horsesData,
            metadata: {
                total: totalCount,
                skip,
                limit,
                last_updated: new Date().toISOString()
            }
        });

    } catch (error) {
        console.error('[API/Horses] Error:', error);
        return NextResponse.json(
            { error: 'サーバーエラーが発生しました' },
            { status: 500 }
        );
    }
}
