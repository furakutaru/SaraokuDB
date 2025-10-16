import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    const res = await fetch(`${apiUrl}/api/horses`, {
      next: { revalidate: 60 } // 60秒間キャッシュ
    });
    
    if (!res.ok) {
      throw new Error('バックエンドからのデータ取得に失敗しました');
    }
    
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('APIルートエラー:', error);
    return NextResponse.json(
      { error: 'データの取得に失敗しました' },
      { status: 500 }
    );
  }
}
