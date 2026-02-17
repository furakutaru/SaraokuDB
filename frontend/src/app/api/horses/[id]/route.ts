import { NextResponse } from 'next/server';
import { neon } from '@neondatabase/serverless';

// データベース接続を設定
if (!process.env.DATABASE_URL) {
  throw new Error('DATABASE_URL environment variable is not defined');
}

const sql = neon(process.env.DATABASE_URL);

// DBから馬データを取得
async function getHorseData(horseId: string): Promise<any | null> {
  try {
    const idNum = parseInt(horseId, 10);
    console.log(`Fetching horse data for ID: ${horseId} (parsed as: ${idNum})`);

    // 馬の基本情報を取得
    const horseResult = await sql`SELECT 
        id,
        name,
        raw_name,
        sex,
        age,
        sire,
        dam,
        dam_sire,
        weight,
        is_broodmare,
        total_prize_start,
        total_prize_latest,
        sold_price,
        auction_date,
        seller,
        disease_tags,
        comment,
        image_url,
        detail_url,
        jbis_url,
        is_unsold,
        created_at,
        updated_at,
        race_records,
        unified_race_records
      FROM horses 
      WHERE id = ${idNum}`;

    console.log(`Query result for ID ${idNum}:`, horseResult?.length || 0, 'rows found');

    if (!horseResult || horseResult.length === 0) {
      console.error(`馬が見つかりません (ID: ${horseId})`);
      return null;
    }

    const horse = horseResult[0];
    const horseName = horse.name;

    console.log(`[API] Searching history for horse name: "${horseName}"`);

    // 同名の馬をすべて取得して履歴としてマージする
    const allSameNamedHorses = await sql`SELECT 
        id,
        auction_date,
        sold_price as price,
        is_unsold,
        seller,
        detail_url,
        comment,
        weight
      FROM horses 
      WHERE name = ${horseName}
      ORDER BY auction_date DESC`;

    console.log(`[API] allSameNamedHorses for "${horse.name}":`, allSameNamedHorses.length);

    // オークション履歴テーブル (auction_histories) からも取得
    const horseIds = allSameNamedHorses.map(h => h.id);
    const auctionHistoryResult = await sql`SELECT 
        auction_date,
        price,
        is_unsold,
        seller,
        auction_url as detail_url
      FROM auction_histories 
      WHERE horse_id = ANY(${horseIds})
      ORDER BY auction_date DESC`;

    console.log(`[API] auctionHistoryResult for horseIds [${horseIds.join(',')}]:`, auctionHistoryResult.length);

    // 全データを統合してマージ
    const mergedHistoryMap = new Map();

    // 1. horses テーブルからのデータを投入（数値変換含む）
    allSameNamedHorses.forEach(h => {
      const priceVal = h.price ? Number(h.price) : 0;
      const weightVal = h.weight ? Number(h.weight) : null;
      const key = `${h.auction_date}_${h.seller}_${priceVal}`;

      mergedHistoryMap.set(key, {
        auction_date: h.auction_date,
        price: priceVal,
        is_unsold: h.is_unsold,
        seller: h.seller,
        detail_url: h.detail_url,
        comment: h.comment || null,
        weight: weightVal
      });
    });

    // 2. auction_histories テーブルからのデータを投入（上書きまたは情報補完）
    auctionHistoryResult.forEach(h => {
      const priceVal = h.price ? Number(h.price) : 0;
      const weightVal = h.weight ? Number(h.weight) : null;
      const key = `${h.auction_date}_${h.seller}_${priceVal}`;

      const existing = mergedHistoryMap.get(key);
      mergedHistoryMap.set(key, {
        auction_date: h.auction_date,
        price: priceVal,
        is_unsold: h.is_unsold,
        seller: h.seller,
        detail_url: h.detail_url,
        // すでに horses から取得している場合は、足りない情報を保持
        comment: existing?.comment || h.comment || null,
        weight: existing?.weight || weightVal
      });
    });

    // 日付順にソートした配列に変換
    const finalAuctionHistoryArray = Array.from(mergedHistoryMap.values())
      .sort((a, b) => {
        const dateA = a.auction_date ? new Date(a.auction_date).getTime() : 0;
        const dateB = b.auction_date ? new Date(b.auction_date).getTime() : 0;
        return dateB - dateA;
      });

    // 最新のオークション情報を取得
    const latestAuction = finalAuctionHistoryArray.length > 0 ? finalAuctionHistoryArray[0] : null;

    return {
      ...horse,
      auction_histories: finalAuctionHistoryArray,
      latest_auction: latestAuction
    };
  } catch (error) {
    console.error('馬データの読み込み中にエラーが発生しました:', error);
    return null;
  }
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const horse = await getHorseData(id);

    if (!horse) {
      return NextResponse.json(
        { error: '馬が見つかりません' },
        { status: 404 }
      );
    }

    // フロントエンドが期待する形式でデータを整形
    const responseData = {
      ...horse,
      name: horse.name || '',
      sex: horse.sex || '',
      age: horse.age || 0,
      sire: horse.sire || '',
      dam: horse.dam || '',
      damsire: horse.dam_sire || horse.damsire || '',

      // auction_history フィールドとして返す
      auction_history: horse.auction_histories || [],

      // race_records は JSONB カラムから取得 (page.tsxが race_records を期待している)
      race_records: horse.race_records || { total_races: 0, wins: 0, total_prize_money: 0 },

      // 互換性のため
      race_record: horse.race_records || { total_races: 0, wins: 0, total_prize_money: 0 },

      metadata: {
        created_at: horse.created_at || new Date().toISOString(),
        updated_at: horse.updated_at || new Date().toISOString(),
        data_source: 'db'
      }
    };

    return NextResponse.json(responseData);
  } catch (error) {
    console.error('馬データの取得中にエラーが発生しました:', error);
    return NextResponse.json(
      { error: 'サーバーエラーが発生しました' },
      { status: 500 }
    );
  }
}
