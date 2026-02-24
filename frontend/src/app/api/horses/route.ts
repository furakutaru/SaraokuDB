import { NextResponse } from 'next/server';
import { neon } from '@neondatabase/serverless';
import { apiCache, generateCacheKey } from '@/lib/cache';

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

        // キャッシュキーの生成
        const cacheKey = generateCacheKey('/api/horses', {
            skip,
            limit,
            sort,
            latestAuctionOnly
        });

        // キャッシュチェック
        const cachedResponse = apiCache.get(cacheKey);
        if (cachedResponse) {
            console.log(`[API/Horses] Cache hit for ${cacheKey}`);
            return NextResponse.json(cachedResponse);
        }

        console.log(`[API/Horses] Cache miss, fetching from DB: skip=${skip}, limit=${limit}, sort=${sort}, latest=${latestAuctionOnly}`);

        // 2. 重複（同名）を除去するための代表的なIDを取得（DISTINCT ONで最適化）
        let repIdsResult: any[];
        if (latestAuctionOnly) {
            // 最新のオークション日を取得
            const latestDateResult = await sql`SELECT MAX(auction_date) as max_date FROM horses WHERE auction_date IS NOT NULL`;
            const latestDate = latestDateResult[0]?.max_date;

            if (!latestDate) {
                repIdsResult = [];
            } else {
                repIdsResult = await sql`
                    SELECT DISTINCT ON (name) id, name, updated_at
                    FROM horses
                    WHERE name IS NOT NULL AND auction_date = ${latestDate}
                    ORDER BY name, updated_at DESC
                `;
            }
        } else {
            repIdsResult = await sql`
                SELECT DISTINCT ON (name) id, name, updated_at
                FROM horses
                WHERE name IS NOT NULL
                ORDER BY name, updated_at DESC
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

        // 3. ページネーション適用（メモリ内でスライス）
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

        // インデックスを活用したソート
        if (sort === 'price_asc') {
            horsesResult = await sql`SELECT ${selectFields} FROM horses WHERE id = ANY(${paginatedIds}) ORDER BY sold_price ASC NULLS LAST`;
        } else if (sort === 'name_asc') {
            horsesResult = await sql`SELECT ${selectFields} FROM horses WHERE id = ANY(${paginatedIds}) ORDER BY name ASC NULLS LAST`;
        } else if (sort === 'name_desc') {
            horsesResult = await sql`SELECT ${selectFields} FROM horses WHERE id = ANY(${paginatedIds}) ORDER BY name DESC NULLS LAST`;
        } else {
            // Default: price_desc
            horsesResult = await sql`SELECT ${selectFields} FROM horses WHERE id = ANY(${paginatedIds}) ORDER BY sold_price DESC NULLS LAST`;
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

        const responseData = {
            horses: horsesData,
            metadata: {
                total: totalCount,
                skip,
                limit,
                last_updated: new Date().toISOString()
            }
        };

        // キャッシュに保存（TTL: 5分）
        apiCache.set(cacheKey, responseData, 5 * 60 * 1000);
        console.log(`[API/Horses] Cached response for ${cacheKey}`);

        return NextResponse.json(responseData);

    } catch (error) {
        console.error('[API/Horses] Error:', error);
        return NextResponse.json(
            { error: 'サーバーエラーが発生しました' },
            { status: 500 }
        );
    }
}
