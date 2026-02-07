import { NextResponse } from 'next/server';

// 動的ルートとして明示的に指定
export const dynamic = 'force-dynamic';

// 環境変数からAPIのベースURLを取得
const API_BASE_URL = 'http://localhost:8001';
const API_URL = `${API_BASE_URL}/api`;

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    console.log(`[API] 馬詳細データ取得開始: ID=${params.id}`);
    
    // バックエンドAPIから馬詳細データを取得
    const backendUrl = `${API_URL}/horses/${encodeURIComponent(params.id)}`;
    console.log(`[API] バックエンドリクエスト: ${backendUrl}`);
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      cache: 'no-store',
    });

    console.log(`[API] バックエンドレスポンス: ${response.status} ${response.statusText}`);

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[API] バックエンドエラー: ${response.status} - ${errorText}`);
      
      if (response.status === 404) {
        return NextResponse.json(
          { error: '馬が見つかりません' },
          { status: 404 }
        );
      }
      
      return NextResponse.json(
        { error: 'データの取得に失敗しました' },
        { status: response.status }
      );
    }

    const horseData = await response.json();
    console.log(`[API] 取得成功: ${horseData.name || '不明'}`);

    // フロントエンドが期待する形式でデータを整形
    const responseData = {
      ...horseData,
      name: horseData.name || '',
      sex: horseData.sex || '',
      age: horseData.age || 0,
      sire: horseData.sire || '',
      dam: horseData.dam || '',
      damsire: horseData.damsire || horseData.dam_sire || '',
      auction_history: horseData.auction_history || horseData.auction_histories || [],
      race_records: horseData.race_records || { total_prize_money: 0 },
      latest_auction: horseData.latest_auction || null,
      metadata: horseData.metadata || {
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        data_source: 'backend'
      }
    };

    return NextResponse.json(responseData);
  } catch (error) {
    console.error('[API] 馬データの取得中にエラーが発生しました:', error);
    return NextResponse.json(
      { error: 'サーバーエラーが発生しました' },
      { status: 500 }
    );
  }
}
