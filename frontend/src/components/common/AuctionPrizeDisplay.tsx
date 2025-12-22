import React from 'react';

export interface RaceRecordInfo {
  total_races?: number;
  wins?: number;
  record_format?: string;
  formatted_record?: string;
  unified_race_records?: boolean;
  race_record?: {
    unified_race_records?: boolean;
    [key: string]: any;
  };
  [key: string]: any; // その他の動的プロパティ用
}

interface AuctionPrizeDisplayProps {
  raceRecord?: RaceRecordInfo | string | null;
  totalPrizeStart?: number | null;
  isUnsold?: boolean;
  formatPrizeMan: (
    amount: number | string | null | undefined, 
    raceRecords?: RaceRecordInfo | null
  ) => string;
}

/**
 * 落札時賞金を表示する共通コンポーネント
 * レース記録が0戦の場合は「未出走」と表示
 */
const AuctionPrizeDisplay: React.FC<AuctionPrizeDisplayProps> = ({
  raceRecord,
  totalPrizeStart,
  isUnsold,
  formatPrizeMan,
}) => {
  console.log('AuctionPrizeDisplay - raceRecord:', raceRecord);
  console.log('AuctionPrizeDisplay - totalPrizeStart:', totalPrizeStart);
  
  // raceRecordが文字列の場合は安全にパースする
  const parsedRaceRecord = (() => {
    if (typeof raceRecord !== 'string') return raceRecord || {};
    try {
      return JSON.parse(raceRecord);
    } catch (e) {
      console.warn('AuctionPrizeDisplay: failed to parse raceRecord string. Fallback to {}. value=', raceRecord, e);
      return {} as Record<string, any>;
    }
  })();
  
  // デバッグ用: raceRecordの構造を確認
  console.log('AuctionPrizeDisplay - parsedRaceRecord:', parsedRaceRecord);
  
  // 未出走チェック: total_races が 0 の場合に未出走とみなす
  const isUnraced = parsedRaceRecord.total_races === 0;
  
  // デバッグ用: 未出走判定のログを出力
  console.log('AuctionPrizeDisplay - isUnraced:', isUnraced);

  // 未出走の場合は「未出走」を表示
  if (isUnraced) {
    return <span>未出走</span>;
  }

  // 落札時賞金を表示
  const prizeDisplay = formatPrizeMan(totalPrizeStart, {
    ...parsedRaceRecord,
    total_prize_money: totalPrizeStart || 0,
    is_unsold: isUnsold
  });

  return <span>{prizeDisplay}</span>;
};

export default AuctionPrizeDisplay;
