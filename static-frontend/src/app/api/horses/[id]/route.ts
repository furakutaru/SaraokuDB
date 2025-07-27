import { NextResponse } from 'next/server';
import { Horse } from '@/types/horse';
import path from 'path';
import fs from 'fs/promises';

// 開発環境ではファイルシステムから直接データを読み込む
async function getHorseData(horseId: number): Promise<Horse | null> {
  try {
    // プロジェクトルートを取得
    const projectRoot = process.cwd();
    // データファイルのパスを構築
    const dataPath = path.join(projectRoot, 'public', 'data', 'horses_history.json');
    
    // ファイルを非同期で読み込む
    const fileContent = await fs.readFile(dataPath, 'utf-8');
    const data = JSON.parse(fileContent);
    
    if (!data?.horses || !Array.isArray(data.horses)) {
      console.error('無効なデータ形式です');
      return null;
    }
    
    const horse = data.horses.find((h: Horse) => h.id === horseId);
    return horse || null;
  } catch (error) {
    console.error('ファイルの読み込み中にエラーが発生しました:', error);
    return null;
  }
}

import { NextRequest } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const horseId = parseInt(params.id, 10);
    
    if (isNaN(horseId) || horseId <= 0) {
      return NextResponse.json(
        { error: '無効な馬IDです' },
        { status: 400 }
      );
    }
    
    const horse = await getHorseData(horseId);
    
    if (!horse) {
      return NextResponse.json(
        { error: '馬が見つかりませんでした' },
        { status: 404 }
      );
    }
    
    return NextResponse.json({ horse });
  } catch (error) {
    console.error('エラーが発生しました:', error);
    return NextResponse.json(
      { error: 'サーバーエラーが発生しました' },
      { status: 500 }
    );
  }
}
