import { NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs';

// 開発環境と本番環境の両方で動作するようにパスを設定
const getDataPath = () => {
  // 開発環境の場合
  if (process.env.NODE_ENV === 'development') {
    const devPath = path.join(process.cwd(), 'public/data/horses_combined.json');
    if (fs.existsSync(devPath)) return devPath;
    
    // 別の可能性のあるパスをチェック
    const altPath = path.join(process.cwd(), '..', 'static-frontend', 'public', 'data', 'horses_combined.json');
    if (fs.existsSync(altPath)) return altPath;
  }
  
  // 本番環境用のパス
  return path.join(process.cwd(), 'public/data/horses_combined.json');
};

export async function GET() {
  try {
    const dataPath = getDataPath();
    console.log('馬データを読み込み中:', dataPath);
    
    // ファイルが存在するか確認
    if (!fs.existsSync(dataPath)) {
      console.error('馬データファイルが見つかりません:', dataPath);
      return NextResponse.json(
        { 
          error: '馬データファイルが見つかりません',
          path: dataPath,
          cwd: process.cwd(),
          files: fs.readdirSync(path.dirname(dataPath) || '.')
        },
        { status: 404 }
      );
    }
    
    // ファイルを読み込む
    const fileData = fs.readFileSync(dataPath, 'utf8');
    const data = JSON.parse(fileData);
    
    // デバッグ用にデータのサンプルをログ出力
    if (data.horses && data.horses.length > 0) {
      console.log('最初の馬データ（サンプル）:', {
        id: data.horses[0].id,
        name: data.horses[0].name,
        comment: data.horses[0].comment ? 'コメントあり' : 'コメントなし',
        weight: data.horses[0].weight,
        history_count: data.horses[0].history?.length || 0
      });
    }
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('馬データの読み込み中にエラーが発生しました:', error);
    return NextResponse.json(
      { 
        error: '馬データの読み込みに失敗しました',
        details: error instanceof Error ? error.message : '不明なエラー',
        stack: process.env.NODE_ENV === 'development' && error instanceof Error ? error.stack : undefined
      },
      { status: 500 }
    );
  }
}
