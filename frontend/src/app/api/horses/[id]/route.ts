import { NextResponse } from 'next/server';

// 動的ルートとして明示的に指定
export const dynamic = 'force-dynamic';

// 環境変数からAPIのベースURLを取得
const API_BASE_URL = process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
const API_URL = `${API_BASE_URL}/api`;

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    console.log(`[API] 馬詳細データ取得開始: ID=${params.id}`);
    console.log(`[API] API_BASE_URL: ${API_BASE_URL}`);
    console.log(`[API] NODE_ENV: ${process.env.NODE_ENV}`);
    console.log(`[API] 環境変数一覧:`, {
      API_BASE_URL: process.env.API_BASE_URL,
      NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
      VERCEL_URL: process.env.VERCEL_URL,
      VERCEL_ENV: process.env.VERCEL_ENV
    });
    
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
      signal: AbortSignal.timeout(10000), // 10秒タイムアウト
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
        { error: `データの取得に失敗しました (${response.status})` },
        { status: response.status }
      );
    }

    const horseData = await response.json();
    console.log(`[API] バックエンドから取得成功: ${horseData.name || '不明'}`);

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
      metadata: {
        ...horseData.metadata,
        created_at: horseData.metadata?.created_at || new Date().toISOString(),
        updated_at: horseData.metadata?.updated_at || new Date().toISOString(),
        data_source: 'backend'
      }
    };

    return NextResponse.json(responseData);
  } catch (error) {
    console.error('[API] 馬データの取得中にエラーが発生しました:', error);
    console.error('[API] エラー詳細:', {
      name: error instanceof Error ? error.name : 'Unknown',
      message: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined
    });
    
    // タイムアウトエラーの場合
    if (error instanceof Error && error.name === 'TimeoutError') {
      return NextResponse.json(
        { error: 'バックエンドAPIへの接続がタイムアウトしました' },
        { status: 504 }
      );
    }
    
    return NextResponse.json(
      { error: `サーバーエラーが発生しました: ${error instanceof Error ? error.message : String(error)}` },
      { status: 500 }
    );
  }
}
