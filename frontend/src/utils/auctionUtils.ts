import { AuctionHistory } from '../types/horse';

export interface GroupedAuctionHistory {
  [key: string]: AuctionHistory[];
}

export const groupAuctionHistory = (histories: any[]): GroupedAuctionHistory => {
  const result: GroupedAuctionHistory = {};

  for (const history of histories) {
    if (!history || typeof history !== 'object') continue;

    // 馬IDを取得（horse_id または id を試みる）
    const horseId = String(history.horse_id ?? history.id ?? '');
    if (!horseId) continue;

    if (!result[horseId]) {
      result[horseId] = [];
    }
    result[horseId].push(history);
  }

  return result;
};

// デバッグ用ログ
export const debugAuctionHistory = (histories: any[]) => {
  console.log('=== オークション履歴デバッグ情報 ===');
  console.log('合計件数:', histories.length);
  if (histories.length > 0) {
    console.log('最初のアイテム:', histories[0]);
    console.log('最初のアイテムのキー:', Object.keys(histories[0]));
  }
};
