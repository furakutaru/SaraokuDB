import { NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs/promises';

// 動的ルートとして明示的に指定
export const dynamic = 'force-dynamic';

// 環境変数からAPIのベースURLを取得
const API_BASE_URL = process.env.API_BASE_URL || 
                    process.env.PROD_API_BASE_URL || 
                    process.env.NEXT_PUBLIC_API_URL || 
                    'http://localhost:8001';
const API_URL = `${API_BASE_URL}/api`;

// 静的ファイルから馬データを取得（フォールバック用）
async function getHorseDataFromStatic(horseId: string): Promise<any | null> {
  try {
    const projectRoot = process.cwd();
    const dataPath = path.join(projectRoot, 'public', 'data', 'horses.json');
    
    const fileContent = await fs.readFile(dataPath, 'utf-8');
    const horses = JSON.parse(fileContent);
    
    if (!Array.isArray(horses)) {
      console.error('無効なデータ形式です');
      return null;
    }
    
    const horse = horses.find((h: any) => h.id === horseId || String(h.id) === horseId);
    
    if (!horse) {
      console.error(`馬が見つかりません (ID: ${horseId})`);
      return null;
    }
    
    // static-frontendのデータ構造をfrontendが期待する形式に変換
    return {
      ...horse,
      // 必要なフィールドを追加・変換
      auction_history: horse.auction_history || [],
      race_records: horse.race_records || {},
      latest_auction: horse.latest_auction || null,
      metadata: {
        created_at: horse.created_at || new Date().toISOString(),
        updated_at: horse.updated_at || new Date().toISOString(),
        data_source: "static"
      }
    };
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
    console.log(`[API] API_URL: ${API_URL}`);
    console.log(`[API] NODE_ENV: ${process.env.NODE_ENV}`);
    console.log(`[API] 環境変数一覧:`, {
      API_BASE_URL: process.env.API_BASE_URL,
      PROD_API_BASE_URL: process.env.PROD_API_BASE_URL,
      NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
      VERCEL_URL: process.env.VERCEL_URL,
      VERCEL_ENV: process.env.VERCEL_ENV
    });
    
    let horseData = null;
    let dataSource = 'unknown';
    let lastError = null;

    // 1. バックエンドAPIから馬詳細データを取得
    if (!API_BASE_URL.includes('localhost')) {
      const backendUrl = `${API_URL}/horses/${encodeURIComponent(params.id)}`;
      console.log(`[API] バックエンドリクエスト: ${backendUrl}`);
      console.log(`[API] 完全なURL: ${backendUrl}`);
      
      try {
        let response;
        try {
          response = await fetch(backendUrl, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
            cache: 'no-store',
            signal: AbortSignal.timeout(10000), // 10秒タイムアウト
          });
          console.log(`[API] fetch成功: レスポンスオブジェクト取得`);
        } catch (fetchError) {
          console.error(`[API] fetchエラー:`, fetchError);
          throw fetchError;
        }

        console.log(`[API] バックエンドレスポンス: ${response.status} ${response.statusText}`);
        console.log(`[API] レスポンスヘッダー:`, Object.fromEntries(response.headers.entries()));

        if (response.ok) {
          let horseData;
          try {
            horseData = await response.json();
            console.log(`[API] JSONパース成功: ${horseData.name || '不明'}`);
            dataSource = 'backend';
          } catch (jsonError) {
            console.error(`[API] JSONパースエラー:`, jsonError);
            throw new Error('レスポンスのJSONパースに失敗しました');
          }
        } else {
          let errorText;
          try {
            errorText = await response.text();
            console.error(`[API] バックエンドエラーレスポンス: ${errorText}`);
          } catch (textError) {
            errorText = 'レスポンステキストの読み取りに失敗';
            console.error(`[API] レスポンステキスト読み取りエラー:`, textError);
          }
          
          lastError = new Error(`バックエンドエラー: ${response.status} - ${errorText}`);
        }
      } catch (error) {
        console.error(`[API] バックエンド接続エラー:`, error);
        lastError = error;
      }
    } else {
      console.log(`[API] localhostのためバックエンドAPIをスキップします`);
      lastError = new Error('バックエンドAPIがlocalhostに設定されています');
    }

    // 2. バックエンドから取得できなかった場合は静的ファイルから取得
    if (!horseData) {
      console.log(`[API] 静的ファイルから取得を試みます`);
      horseData = await getHorseDataFromStatic(params.id);
      
      if (horseData) {
        dataSource = 'static';
        console.log(`[API] 静的ファイルから取得成功: ${horseData.name || '不明'}`);
        lastError = null; // 静的ファイルから取得できた場合はエラーをクリア
      }
    }

    if (!horseData) {
      return NextResponse.json(
        { 
          error: '馬が見つかりません', 
          details: lastError instanceof Error ? lastError.message : String(lastError),
          dataSource: dataSource
        },
        { status: 404 }
      );
    }

    console.log(`[API] バックエンドから取得成功: ${horseData.name || '不明'} (ソース: ${dataSource})`);

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

    console.log(`[API] レスポンスデータ整形完了 (ソース: ${dataSource})`);
    return NextResponse.json(responseData);
  } catch (error) {
    console.error('[API] 馬データの取得中にエラーが発生しました:', error);
    console.error('[API] エラー詳細:', {
      name: error instanceof Error ? error.name : 'Unknown',
      message: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined,
      cause: error instanceof Error ? error.cause : undefined
    });
    
    // タイムアウトエラーの場合
    if (error instanceof Error && error.name === 'TimeoutError') {
      return NextResponse.json(
        { error: 'バックエンドAPIへの接続がタイムアウトしました', details: '10秒以内に応答がありませんでした' },
        { status: 504 }
      );
    }
    
    return NextResponse.json(
      { 
        error: `サーバーエラーが発生しました: ${error instanceof Error ? error.message : String(error)}`,
        details: error instanceof Error ? error.stack : String(error)
      },
      { status: 500 }
    );
  }
}
