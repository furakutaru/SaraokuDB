import { NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs/promises';

// 馬データを取得（horses_combined.jsonから取得）
async function getHorseData(horseId: string): Promise<any | null> {
  try {
    const projectRoot = process.cwd();
    const dataPath = path.join(projectRoot, 'public', 'data', 'horses_combined.json');
    
    const fileContent = await fs.readFile(dataPath, 'utf-8');
    const data = JSON.parse(fileContent);
    
    if (!data?.horses || !Array.isArray(data.horses)) {
      console.error('無効なデータ形式です');
      return null;
    }
    
    // 馬をIDで検索
    const horse = data.horses.find((h: any) => h.id === horseId);
    
    if (!horse) {
      console.error(`馬が見つかりません (ID: ${horseId})`);
      return null;
    }
    
    return horse;
  } catch (error) {
    console.error('馬データの読み込み中にエラーが発生しました:', error);
    return null;
  }
}

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const horse = await getHorseData(params.id);
    
    if (!horse) {
      return NextResponse.json(
        { error: '馬が見つかりません' },
        { status: 404 }
      );
    }

    // オークション履歴を取得
    const auctionHistory = horse.auction_history || [];

    // フロントエンドが期待する形式でデータを整形
    const responseData = {
      ...horse,
      name: horse.name || '',
      sex: horse.sex || '',
      age: horse.age || 0,
      sire: horse.sire || '',
      dam: horse.dam || '',
      damsire: horse.damsire || '',
      auction_history: auctionHistory,
      race_records: horse.race_records || { total_prize_money: 0 },
      latest_auction: horse.latest_auction || null,
      metadata: horse.metadata || {
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        data_source: 'jbis'
      }
    };

    return NextResponse.json(responseData);
  } catch (error) {
    console.error('馬データの取得中にエラーが発生しました:', error);
    return NextResponse.json(
      { error: 'サーバーエラーが発生しました' },
      { status: 500 }
    );
  }
}
