import { PrismaClient } from '@prisma/client';
import fs from 'fs';
import path from 'path';
import dotenv from 'dotenv';

// .envファイルから環境変数を読み込み
dotenv.config({ path: path.join(process.cwd(), '.env') });

// Prisma Clientを初期化
const prisma = new PrismaClient({
  log: ['query', 'info', 'warn', 'error']
});

// 型定義
interface JsonHorse {
  id: number | string;
  name: string;
  race_records?: {
    total_races: number;
    wins: number;
    record_format: string;
    formatted_record: string;
  };
  [key: string]: any;
}

interface DbHorse {
  id: number;
  name: string;
  raceRecord: string | null;  // マッピング用にキャメルケースのまま
}

// ログ出力用の関数
const log = (message: string, data?: any) => {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] ${message}`;
  console.log(logMessage);
  
  if (data) {
    console.log(JSON.stringify(data, null, 2));
  }
};

async function updateRaceRecords(dryRun: boolean = false) {
  try {
    log('戦績の更新を開始します...');
    
    // JSONファイルからデータを読み込み
    const jsonPath = path.join(process.cwd(), 'static-frontend', 'public', 'data', 'horses.json');
    log(`JSONファイルを読み込み中: ${jsonPath}`);
    
    if (!fs.existsSync(jsonPath)) {
      throw new Error(`JSONファイルが見つかりません: ${jsonPath}`);
    }
    
    const jsonData = JSON.parse(fs.readFileSync(jsonPath, 'utf-8')) as JsonHorse[];
    log(`JSONデータを読み込みました。レコード数: ${jsonData.length}`);
    
    // 更新対象の馬名と戦績をマップ化
    const raceRecordMap = new Map<string, { total_races: number; wins: number }>();
    
    jsonData.forEach(horse => {
      if (horse.race_records) {
        raceRecordMap.set(horse.name, {
          total_races: horse.race_records.total_races,
          wins: horse.race_records.wins
        });
      }
    });
    
    // データベースから全馬情報を取得
    log('データベースから馬情報を取得中...');
    const dbHorses = await prisma.$queryRaw<DbHorse[]>`
      SELECT id, name, race_record as "raceRecord"
      FROM horses
    `;
    
    log(`データベースから${dbHorses.length}件のレコードを取得しました。`);
    
    // 更新対象のレコードを特定
    const updates = [];
    
    for (const dbHorse of dbHorses) {
      const jsonRecord = raceRecordMap.get(dbHorse.name);
      
      if (!jsonRecord) {
        log(`警告: JSONに戦績が見つかりませんでした (名前: ${dbHorse.name})`);
        continue;
      }
      
      // 現在のレコードをパース
      let currentRecord = { total_races: 0, wins: 0 };
      if (dbHorse.raceRecord) {
        try {
          currentRecord = JSON.parse(dbHorse.raceRecord);
        } catch (e) {
          log(`警告: レコードのパースに失敗しました (名前: ${dbHorse.name}): ${dbHorse.raceRecord}`);
          continue;
        }
      }
      
      // 戦績が異なる場合に更新
      if (currentRecord.total_races !== jsonRecord.total_races || 
          currentRecord.wins !== jsonRecord.wins) {
        
        const updatedRecord = {
          total_races: jsonRecord.total_races,
          wins: jsonRecord.wins,
          record_format: 'simple',
          formatted_record: `${jsonRecord.total_races}戦${jsonRecord.wins}勝`
        };
        
        updates.push(
          prisma.$executeRaw`
            UPDATE horses
            SET race_record = ${JSON.stringify(updatedRecord)}::jsonb
            WHERE id = ${dbHorse.id}
          `
        );
        
        log(`更新予定: ${dbHorse.name} - ${currentRecord.total_races}戦${currentRecord.wins}勝 → ${jsonRecord.total_races}戦${jsonRecord.wins}勝`);
      }
    }
    
    // 更新を実行
    if (updates.length > 0) {
      if (dryRun) {
        log(`[ドライラン] ${updates.length}件のレコードが更新されます。`);
        log('実際の更新を行うには dryRun を false に設定してください。');
      } else {
        log(`${updates.length}件のレコードを更新します...`);
        await prisma.$transaction(updates);
        log('更新が完了しました。');
      }
    } else {
      log('更新対象のレコードはありませんでした。');
    }
    
  } catch (error) {
    log('エラーが発生しました:', error);
    throw error;
  } finally {
    // グローバルなprismaインスタンスはクローズしない
    await prisma.$disconnect();
  }
}

// スクリプトを実行（実際に更新を実行）
updateRaceRecords(false).catch(error => {
  console.error('エラーが発生しました:', error);
  process.exit(1);
});
