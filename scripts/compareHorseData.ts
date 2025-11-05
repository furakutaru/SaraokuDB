import { PrismaClient } from '@prisma/client';
import fs from 'fs';
import path from 'path';
import dotenv from 'dotenv';

// .envファイルから環境変数を読み込み
dotenv.config({ path: path.join(process.cwd(), '.env') });

// 型定義
interface JsonHorse {
  id: number | string;
  name: string;
  race_records?: {
    total_races: number;
    wins: number;
  };
  total_prize_start?: number;
  [key: string]: any;
}

interface RaceRecord {
  total_races: number;
  wins: number;
  record_format?: string;
  formatted_record?: string;
  [key: string]: any;
}

interface Mismatch {
  id?: number;
  name: string;
  field: string;
  dbValue: any;
  jsonValue: any;
  status: string;
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

// 結果を保存するディレクトリ
const OUTPUT_DIR = path.join(process.cwd(), 'comparison_results');

// 結果をCSVに保存する関数
const saveToCsv = (filename: string, data: any[]) => {
  if (data.length === 0) {
    log(`比較結果に差異は見つかりませんでした: ${filename}`);
    return;
  }

  // ヘッダー行を作成
  const headers = Object.keys(data[0]);
  const csvRows = [
    headers.join(','),
    ...data.map(row => 
      headers.map(fieldName => {
        const value = row[fieldName] ?? '';
        // カンマや改行が含まれる場合はダブルクォートで囲む
        if (typeof value === 'string' && (value.includes(',') || value.includes('\n'))) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
      }).join(',')
    )
  ];

  // 出力ディレクトリがなければ作成
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  const filePath = path.join(OUTPUT_DIR, filename);
  fs.writeFileSync(filePath, csvRows.join('\n'), 'utf8');
  log(`比較結果を保存しました: ${filePath}`);
};

// メインの比較処理
async function compareHorseData() {
  const prisma = new PrismaClient({
    log: ['query', 'info', 'warn', 'error'],
  });
  
  try {
    log('比較処理を開始します...');
    
    // JSONファイルからデータを読み込み
    const jsonPath = path.join(process.cwd(), 'static-frontend', 'public', 'data', 'horses.json');
    log(`JSONファイルを読み込み中: ${jsonPath}`);
    
    if (!fs.existsSync(jsonPath)) {
      throw new Error(`JSONファイルが見つかりません: ${jsonPath}`);
    }
    
    const jsonData = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
    log(`JSONデータを読み込みました。レコード数: ${jsonData.length}`);
    
    // 比較結果を格納する配列
    const mismatches: Mismatch[] = [];
    
    // データベースから全馬情報を取得
    log('データベースから馬情報を取得中...');
    const dbHorses = await prisma.$queryRaw<Array<{
      id: number;
      name: string;
      race_record: string | null;
      total_prize_start: number | null;
    }>>`
      SELECT id, name, race_record, total_prize_start
      FROM horses
    `;
    
    log(`データベースから${dbHorses.length}件のレコードを取得しました。`);
    
    // JSONデータを馬名でマップ化（小文字に統一）
    const jsonHorseMap = new Map<string, JsonHorse>(
      jsonData.map((horse: JsonHorse) => [horse.name.toLowerCase(), horse])
    );
    
    // データベースの各レコードとJSONを比較
    for (const dbHorse of dbHorses) {
      const jsonHorse = jsonHorseMap.get(dbHorse.name.toLowerCase());
      
      // JSONに存在しない馬はスキップ
      if (!jsonHorse) {
        log(`警告: データベースに存在しますが、JSONに存在しない馬が見つかりました (名前: ${dbHorse.name})`);
        mismatches.push({
          name: dbHorse.name,
          field: 'existence',
          dbValue: 'DBに存在',
          jsonValue: 'JSONに存在しない',
          status: 'DBにのみ存在'
        });
        continue;
      }

      // レースレコードの比較
      let dbRaceRecord: RaceRecord | null = null;
      if (dbHorse.race_record) {
        try {
          dbRaceRecord = typeof dbHorse.race_record === 'string' 
            ? JSON.parse(dbHorse.race_record) 
            : dbHorse.race_record;
        } catch (e) {
          log(`レコードのパースに失敗しました (名前: ${dbHorse.name}): ${dbHorse.race_record}`, e);
          continue;
        }
      }
      
      const jsonRaceRecord = jsonHorse.race_records;
      
      // 未出走馬の処理
      if (!jsonRaceRecord) {
        // JSONに戦績がない（未出走）場合
        if (dbRaceRecord && (dbRaceRecord.total_races !== 0 || dbRaceRecord.wins !== 0)) {
          mismatches.push({
            name: dbHorse.name,
            field: 'race_record',
            dbValue: dbRaceRecord.formatted_record || `${dbRaceRecord.total_races}戦${dbRaceRecord.wins}勝`,
            jsonValue: '0戦0勝',
            status: '未出走馬の戦績が0戦0勝ではありません'
          });
        }
        continue;
      }
      
      // 戦績の比較
      if (!dbRaceRecord) {
        mismatches.push({
          name: dbHorse.name,
          field: 'race_record',
          dbValue: '戦績なし',
          jsonValue: `${jsonRaceRecord.total_races}戦${jsonRaceRecord.wins}勝`,
          status: 'DBに戦績がありません'
        });
      } else if (dbRaceRecord.total_races !== jsonRaceRecord.total_races || 
                dbRaceRecord.wins !== jsonRaceRecord.wins) {
        mismatches.push({
          name: dbHorse.name,
          field: 'race_record',
          dbValue: dbRaceRecord.formatted_record || `${dbRaceRecord.total_races}戦${dbRaceRecord.wins}勝`,
          jsonValue: `${jsonRaceRecord.total_races}戦${jsonRaceRecord.wins}勝`,
          status: '戦績が異なります'
        });
      }
      
      // 賞金の比較（型を揃えて比較）
      const dbPrize = dbHorse.total_prize_start !== null ? Number(dbHorse.total_prize_start) : null;
      const jsonPrize = jsonHorse.total_prize_start !== undefined ? 
                       Number(jsonHorse.total_prize_start) : null;
      
      if (dbPrize !== jsonPrize) {
        mismatches.push({
          name: dbHorse.name,
          field: 'total_prize_start',
          dbValue: dbPrize,
          jsonValue: jsonPrize,
          status: dbPrize === null ? 'DBがNULL' : 
                 jsonPrize === null ? 'JSONがNULL' : '値が異なります'
        });
      }
    }
    
    // 比較結果をCSVに保存
    saveToCsv('horse_comparison_results.csv', mismatches);
    
    // 結果を要約
    const summary = {
      totalRecords: dbHorses.length,
      recordsInJson: jsonData.length,
      mismatchesFound: mismatches.length,
      fieldsCompared: ['race_record', 'total_prize_start'],
      timestamp: new Date().toISOString()
    };
    
    log('比較処理が完了しました。', { summary });
    
  } catch (error) {
    log('エラーが発生しました:', error);
    throw error;
  } finally {
    await prisma.$disconnect();
  }
}

// スクリプトを実行
compareHorseData().catch(error => {
  console.error('エラーが発生しました:', error);
  process.exit(1);
});
