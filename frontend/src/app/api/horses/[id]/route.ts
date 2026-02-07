import { NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs/promises';

// 動的ルートとして明示的に指定
export const dynamic = 'force-dynamic';

// 環境変数からAPIのベースURLを取得
const API_BASE_URL = process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
const API_URL = `${API_BASE_URL}/api`;

// 静的ファイルから馬データを取得（フォールバック用）
async function getHorseDataFromStatic(horseId: string): Promise<any | null> {
  try {
    const projectRoot = process.cwd();
    const dataPath = path.join(projectRoot, 'public', 'data', 'horses_combined.json');
    
    const fileContent = await fs.readFile(dataPath, 'utf-8');
    const data = JSON.parse(fileContent);
    
    if (!data?.horses || !Array.isArray(data.horses)) {
      console.error('無効なデータ形式です');
      return null;
    }
    
    const horse = data.horses.find((h: any) => h.id === horseId || String(h.id) === horseId);
    
    if (!horse) {
      console.error(`馬が見つかりません (ID: ${horseId})`);
      return null;
    }
    
    return horse;
  } catch (error) {
    console.error('静的ファイルからの馬データ読み込み中にエラーが発生しました:', error);
    return null;
  }
}

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    console.log(`[API] 馬詳細データ取得開始: ID=${params.id}`);
    console.log(`[API] API_BASE_URL: ${API_BASE_URL}`);
    
    let horseData = null;
    let dataSource = 'unknown';

    // 1. バックエンドAPIから馬詳細データを取得
    try {
      const backendUrl = `${API_URL}/horses/${encodeURIComponent(params.id)}`;
      console.log(`[API] バックエンドリクエスト: ${backendUrl}`);
      
      const response = await fetch(backendUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        cache: 'no-store',
        signal: AbortSignal.timeout(5000), // 5秒タイムアウト
      });

      console.log(`[API] バックエンドレスポンス: ${response.status} ${response.statusText}`);

      if (response.ok) {
        horseData = await response.json();
        dataSource = 'backend';
        console.log(`[API] バックエンドから取得成功: ${horseData.name || '不明'}`);
      } else {
        const errorText = await response.text();
        console.error(`[API] バックエンドエラー: ${response.status} - ${errorText}`);
      }
    } catch (fetchError) {
      console.error(`[API] バックエンド接続エラー:`, fetchError);
    }

    // 2. バックエンドから取得できなかった場合は静的ファイルから取得
    if (!horseData) {
      console.log(`[API] 静的ファイルから取得を試みます`);
      horseData = await getHorseDataFromStatic(params.id);
      dataSource = 'static';
      
      if (horseData) {
        console.log(`[API] 静的ファイルから取得成功: ${horseData.name || '不明'}`);
      }
    }

    if (!horseData) {
      return NextResponse.json(
        { error: '馬が見つかりません' },
        { status: 404 }
      );
    }

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
        data_source: dataSource
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
