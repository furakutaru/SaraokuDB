import { NextResponse } from 'next/server';

// バックエンドのベースURL
const BACKEND_URL = 'http://localhost:8001';

// バックエンドのAPIを呼び出す関数
async function fetchFromBackend(url: string) {
  console.log(`Fetching from backend: ${BACKEND_URL}${url}`);
  const response = await fetch(`${BACKEND_URL}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache'
    }
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    console.error('Backend API error:', {
      status: response.status,
      statusText: response.statusText,
      errorData
    });
    throw new Error(errorData.detail?.error || `Failed to fetch data from backend: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export async function GET() {
  try {
    console.log('Fetching horses from backend...');
    // バックエンドから馬の一覧を取得
    const data = await fetchFromBackend('/api/horses');
    console.log('Received data from backend:', {
      hasHorses: !!data.horses,
      horsesCount: data.horses?.length || 0,
      metadata: data.metadata
    });
    
    // バックエンドからのレスポンスをそのまま返す
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in GET /api/horses:', error);
    return NextResponse.json(
      { 
        error: 'Failed to fetch horses', 
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}

export const dynamic = 'force-dynamic';
