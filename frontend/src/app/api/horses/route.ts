import { NextResponse } from 'next/server'

// 環境変数からAPIのベースURLを取得
const API_BASE_URL = process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
const API_URL = `${API_BASE_URL}/api`;  // /api パスを追加

// 動的ルートとして明示的に指定
export const dynamic = 'force-dynamic';

// デバッグログ
console.log('API Configuration:', {
  API_BASE_URL,
  API_URL,
  NODE_ENV: process.env.NODE_ENV
});

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
    
    const requestUrl = `${API_URL}/horses?sort=${sort}`;
    console.log('Fetching horses from backend...', { 
      apiUrl: requestUrl,
      sortParam: sort
    });
    
    // バックエンドAPIからデータを取得
    const response = await fetch(requestUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      cache: 'no-store', // キャッシュを無効化
    })

    console.log('Backend response status:', response.status, response.statusText)
    
    // レスポンスのテキストを取得（デバッグ用）
    const responseText = await response.text()
    console.log('Raw response text:', responseText)
    
    // レスポンスが空でないことを確認
    if (!response.ok) {
      console.error('Error response status:', response.status, response.statusText);
      console.error('Response headers:', Object.fromEntries(response.headers.entries()));
      
      let errorText = '';
      try {
        errorText = await response.text();
        console.error('Error response body:', errorText);
        // JSONとしてパースを試みる
        try {
          const errorJson = JSON.parse(errorText);
          console.error('Parsed error response:', errorJson);
        } catch (e) {
          // JSONパースに失敗した場合は無視
        }
      } catch (e) {
        console.error('Failed to read error response:', e);
      }
      
      throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}\n${errorText}`);
    }
    
    // レスポンスボディをJSONとしてパース
    let data;
    try {
      data = JSON.parse(responseText);
      console.log('Successfully parsed response data');
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('Failed to parse response as JSON:', error);
      console.error('Response text:', responseText);
      throw new Error(`Failed to parse response as JSON: ${errorMessage}`, { cause: error });
    }
    
    // 成功レスポンスを返す
    return new NextResponse(JSON.stringify(data), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    })
  } catch (error) {
    console.error('Error in API route:', error);
    
    // より詳細なエラー情報を収集
    let errorDetails = 'Unknown error';
    let errorMessage = 'Failed to fetch horses';
    let statusCode = 500;
    
    if (error instanceof Error) {
      errorMessage = error.message;
      errorDetails = error.stack || error.message;
      
      // ECONNREFUSED エラーの場合
      if (errorMessage.includes('ECONNREFUSED')) {
        errorMessage = 'バックエンドサーバーに接続できません。サーバーが起動しているか確認してください。';
        statusCode = 503; // Service Unavailable
      }
      
      // ネットワークエラーの場合
      if (errorMessage.includes('fetch failed') || errorMessage.includes('Failed to fetch')) {
        errorMessage = 'バックエンドサーバーとの通信に失敗しました。ネットワーク接続を確認してください。';
        statusCode = 503; // Service Unavailable
      }
    } else if (typeof error === 'string') {
      errorDetails = error;
      errorMessage = error;
    } else if (error && typeof error === 'object') {
      errorDetails = JSON.stringify(error, null, 2);
      errorMessage = 'Unknown error occurred';
    }
    
    console.error('Error details:', {
      error,
      errorMessage,
      errorDetails,
      timestamp: new Date().toISOString(),
      apiUrl: API_BASE_URL
    });

    // エラーレスポンスを返す
    return new NextResponse(
      JSON.stringify({
        error: statusCode === 503 ? 'Service Unavailable' : 'Internal Server Error',
        message: errorMessage,
        details: errorDetails,
        timestamp: new Date().toISOString(),
        apiUrl: API_BASE_URL
      }, null, 2),
      {
        status: 500,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );
  }
}
