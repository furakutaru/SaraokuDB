import { NextResponse } from 'next/server';

// バックエンドのベースURL
const BACKEND_URL = 'http://localhost:8000';

// バックエンドのAPIを呼び出す関数
async function fetchFromBackend(url: string) {
  const response = await fetch(`${BACKEND_URL}${url}`);
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail?.error || 'Failed to fetch data from backend');
  }
  return response.json();
}

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    // バックエンドから馬のデータを取得
    const horse = await fetchFromBackend(`/api/horses/${params.id}`);
    return NextResponse.json(horse);
  } catch (error) {
    console.error('Error fetching horse data:', error);
    return NextResponse.json(
      { error: 'Failed to fetch horse data', details: error instanceof Error ? error.message : String(error) },
      { status: 404 }
    );
  }
}

export const dynamic = 'force-dynamic';
