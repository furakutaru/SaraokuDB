import { UnifiedRaceRecords } from '../types/horse';

/**
 * レコードを統合された形式に変換します
 */
export function toUnifiedRaceRecords(
  race_record?: { 
    total_races: number; 
    wins: number; 
    record_format?: string; 
    formatted_record?: string 
  },
  race_records?: { 
    total_prize_money: number; 
    last_race_date?: string; 
    last_prize_update?: string;
    [key: string]: any;
  }
): UnifiedRaceRecords | undefined {
  // 両方のレコードが存在しない場合はundefinedを返す
  if (!race_record && !race_records) {
    return undefined;
  }

  return {
    // race_record から取得
    total_races: race_record?.total_races || 0,
    wins: race_record?.wins || 0,
    record_format: race_record?.record_format,
    formatted_record: race_record?.formatted_record,
    
    // race_records から取得
    total_prize_money: race_records?.total_prize_money || 0,
    last_race_date: race_records?.last_race_date,
    last_prize_update: race_records?.last_prize_update
  };
}

/**
 * 馬のオブジェクトから統合されたレコードを取得します
 */
export function getUnifiedRaceRecords(horse: {
  race_record?: { 
    total_races: number; 
    wins: number; 
    record_format?: string; 
    formatted_record?: string 
  };
  race_records?: { 
    total_prize_money: number; 
    last_race_date?: string; 
    last_prize_update?: string;
    [key: string]: any;
  };
  unified_race_records?: UnifiedRaceRecords;
}): UnifiedRaceRecords | undefined {
  // すでに統合済みのレコードがある場合はそれを返す
  if (horse.unified_race_records) {
    return horse.unified_race_records;
  }

  // 統合されていない場合は、古い形式から変換する
  if (horse.race_record || horse.race_records) {
    return toUnifiedRaceRecords(horse.race_record, horse.race_records);
  }

  // どちらの形式も利用できない場合はundefinedを返す
  return undefined;
}

/**
 * 馬のオブジェクトに統合されたレコードを設定します
 */
export function withUnifiedRaceRecords<T extends {
  race_record?: any;
  race_records?: any;
  unified_race_records?: UnifiedRaceRecords;
}>(horse: T): T & { unified_race_records?: UnifiedRaceRecords } {
  const unified = getUnifiedRaceRecords(horse);
  return {
    ...horse,
    unified_race_records: unified
  };
}
