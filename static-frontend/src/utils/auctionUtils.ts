// 基本のオークション履歴型を定義
export interface BaseAuctionHistory {
  id?: string | number;
  horse_id?: string | number;
  [key: string]: any;
}

export interface GroupedAuctionHistory {
  [key: string]: BaseAuctionHistory[];
}

/**
 * オークション履歴を馬IDでグループ化する
 * @param histories オークション履歴の配列
 * @returns 馬IDをキーとしたグループ化されたオークション履歴
 */
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

/**
 * オークション履歴のデバッグ情報を出力
 * @param histories オークション履歴の配列
 */
export const debugAuctionHistory = (histories: any[]): void => {
  console.log('=== オークション履歴デバッグ情報 ===');
  console.log('合計件数:', histories.length);
  if (histories.length > 0) {
    console.log('最初のアイテム:', histories[0]);
    console.log('最初のアイテムのキー:', Object.keys(histories[0]));
  }
};

/**
 * オークション履歴から馬IDを安全に取得
 * @param history オークション履歴オブジェクト
 * @returns 馬ID（見つからない場合はnull）
 */
export const getHorseId = (history: BaseAuctionHistory): string | null => {
  if (!history) return null;
  return String(history.horse_id ?? history.id ?? '');
};
