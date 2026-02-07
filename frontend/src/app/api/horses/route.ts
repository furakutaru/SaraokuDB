import { NextResponse } from 'next/server'
import path from 'path';
import fs from 'fs/promises';

// 環境変数からAPIのベースURLを取得
const API_BASE_URL = process.env.API_BASE_URL || 
                    process.env.PROD_API_BASE_URL || 
                    process.env.NEXT_PUBLIC_API_URL || 
                    'http://localhost:8001';
const API_URL = `${API_BASE_URL}/api`;  // /api パスを追加

// 動的ルートとして明示的に指定
export const dynamic = 'force-dynamic';

// 静的ファイルから馬データを取得（フォールバック用）
async function getHorsesFromStatic(): Promise<any | null> {
  try {
    const projectRoot = process.cwd();
    const dataPath = path.join(projectRoot, 'public', 'data', 'horses_combined.json');
    
    const fileContent = await fs.readFile(dataPath, 'utf-8');
    const data = JSON.parse(fileContent);
    
    if (!data?.horses || !Array.isArray(data.horses)) {
      console.error('無効なデータ形式です');
      return null;
    }
    
    return data;
  } catch (error) {
    console.error('静的ファイルからの馬データ読み込み中にエラーが発生しました:', error);
    return null;
  }
}

// デバッグログ
console.log('API Configuration:', {
  API_BASE_URL,
  API_URL,
  NODE_ENV: process.env.NODE_ENV
});

export async function GET(request: Request) {
  try {
    // クエリパラメータを取得 - Next.js 13+の方法で安全に処理
    const { searchParams } = new URL(request.url || `http://${process.env.VERCEL_URL || 'localhost:3000'}`);
    const sort = searchParams.get('sort') || 'price_desc';
    
    console.log(`[API] 馬一覧データ取得開始: sort=${sort}`);
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
    
    let data = null;
    let dataSource = 'unknown';
    let lastError = null;

    // 1. バックエンドAPIから馬データを取得
    if (!API_BASE_URL.includes('localhost')) {
      const requestUrl = `${API_URL}/horses?sort=${sort}`;
      console.log(`[API] バックエンドリクエスト: ${requestUrl}`);
      
      try {
        const response = await fetch(requestUrl, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          cache: 'no-store', // キャッシュを無効化
          signal: AbortSignal.timeout(10000), // 10秒タイムアウト
        });

        console.log(`[API] バックエンドレスポンス: ${response.status} ${response.statusText}`);

        if (response.ok) {
          const responseText = await response.text();
          console.log(`[API] レスポンステキスト長: ${responseText.length}`);
          
          try {
            data = JSON.parse(responseText);
            console.log(`[API] JSONパース成功: ${data.horses?.length || 0}件`);
            dataSource = 'backend';
          } catch (parseError) {
            console.error(`[API] JSONパースエラー:`, parseError);
            throw new Error('レスポンスのJSONパースに失敗しました');
          }
        } else {
          const errorText = await response.text();
          console.error(`[API] バックエンドエラー: ${response.status} - ${errorText}`);
          lastError = new Error(`バックエンドエラー: ${response.status} - ${errorText}`);
        }
      } catch (fetchError) {
        console.error(`[API] バックエンド接続エラー:`, fetchError);
        lastError = fetchError;
      }
    } else {
      console.log(`[API] localhostのためバックエンドAPIをスキップします`);
      lastError = new Error('バックエンドAPIがlocalhostに設定されています');
    }

    // 2. バックエンドから取得できなかった場合は静的ファイルから取得
    if (!data) {
      console.log(`[API] 静的ファイルから取得を試みます`);
      data = await getHorsesFromStatic();
      
      if (data) {
        dataSource = 'static';
        console.log(`[API] 静的ファイルから取得成功: ${data.horses?.length || 0}件`);
        lastError = null; // 静的ファイルから取得できた場合はエラーをクリア
      }
    }

    if (!data) {
      return NextResponse.json(
        { 
          error: '馬データが見つかりません', 
          details: lastError instanceof Error ? lastError.message : String(lastError),
          dataSource: dataSource
        },
        { status: 404 }
      );
    }

    console.log(`[API] 馬一覧取得成功: ${data.horses?.length || 0}件 (ソース: ${dataSource})`);

    // 成功レスポンスを返す
    return new NextResponse(JSON.stringify(data), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    })
  } catch (error) {
    console.error('[API] 馬一覧データの取得中にエラーが発生しました:', error);
    console.error('[API] エラー詳細:', {
      name: error instanceof Error ? error.name : 'Unknown',
      message: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined
    });
    
    return NextResponse.json(
      { 
        error: 'Service Unavailable',
        message: 'バックエンドサーバーとの通信に失敗しました。ネットワーク接続を確認してください。',
        details: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    )
  }
}
