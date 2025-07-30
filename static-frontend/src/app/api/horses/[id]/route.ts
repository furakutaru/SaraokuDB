import { NextResponse } from 'next/server';
import { Horse, AuctionHistory } from '@/types/horse';
import path from 'path';
import fs from 'fs/promises';

// 馬データを取得
async function getHorseData(horseId: string): Promise<Horse | null> {
  try {
    const projectRoot = process.cwd();
    const dataPath = path.join(projectRoot, 'public', 'data', 'horses.json');
    
    const fileContent = await fs.readFile(dataPath, 'utf-8');
    const data = JSON.parse(fileContent);
    
    if (!data?.horses || !Array.isArray(data.horses)) {
      console.error('無効なデータ形式です');
      return null;
    }
    
    return data.horses.find((h: Horse) => h.id === horseId) || null;
  } catch (error) {
    console.error('馬データの読み込み中にエラーが発生しました:', error);
    return null;
  }
}

// オークション履歴を取得
async function getAuctionHistory(horseId: string): Promise<AuctionHistory[]> {
  try {
    const projectRoot = process.cwd();
    const dataPath = path.join(projectRoot, 'public', 'data', 'auction_history.json');
    
    const fileContent = await fs.readFile(dataPath, 'utf-8');
    const data = JSON.parse(fileContent);
    
    if (!data?.auction_history || !Array.isArray(data.auction_history)) {
      console.error('無効なオークションデータ形式です');
      return [];
    }
    
    return data.auction_history.filter((a: AuctionHistory) => a.horse_id === horseId)
      .sort((a: AuctionHistory, b: AuctionHistory) => 
        new Date(b.auction_date).getTime() - new Date(a.auction_date).getTime()
      );
  } catch (error) {
    console.error('オークションデータの読み込み中にエラーが発生しました:', error);
    return [];
  }
}

import { NextRequest } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const horseId = params.id;
    
    if (!horseId) {
      return NextResponse.json(
        { error: '馬IDが指定されていません' },
        { status: 400 }
      );
    }
    
    // 馬データとオークション履歴を並行して取得
    const [horse, auctionHistory] = await Promise.all([
      getHorseData(horseId),
      getAuctionHistory(horseId)
    ]);
    
    if (!horse) {
      return NextResponse.json(
        { error: '馬が見つかりません' },
        { status: 404 }
      );
    }
    
    // 馬データにオークション履歴を追加して返す
    return NextResponse.json({
      ...horse,
      auction_history: auctionHistory
    });
    
  } catch (error) {
    console.error('エラーが発生しました:', error);
    return NextResponse.json(
      { error: 'サーバーエラーが発生しました' },
      { status: 500 }
    );
  }
}
