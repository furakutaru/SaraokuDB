import { Horse, AuctionHistory } from '../types/horse';

// seller が配列JSON文字列や配列のことがあるため、先頭の文字列を日本語テキストとして返す
function parseSeller(value: any): string {
  try {
    // 配列なら先頭要素
    if (Array.isArray(value)) {
      return value.length > 0 ? String(value[0] ?? '') : '';
    }
    // 文字列ならJSONの可能性を最大2回まで解決
    if (typeof value === 'string') {
      let str: any = value.trim();
      for (let i = 0; i < 2; i++) {
        const startsLikeJson = str.startsWith('[') || str.startsWith('{') || str.startsWith('"');
        if (!startsLikeJson) break;
        try {
          const parsed = JSON.parse(str);
          if (Array.isArray(parsed)) {
            return parsed.length > 0 ? String(parsed[0] ?? '') : '';
          }
          if (typeof parsed === 'string') {
            str = parsed.trim();
            continue; // もう一度評価
          }
          // オブジェクトなどはこれ以上推測しない
          break;
        } catch {
          break;
        }
      }
      return str;
    }
  } catch {
    return typeof value === 'string' ? value : '';
  }
  return '';
}

/**
 * Transforms the API response to match the frontend's expected format
 * @param apiData Raw data from the API
 * @returns Transformed horse data in the frontend format
 */
export function transformHorseData(apiData: any): Horse {
  // バックエンドから提供されるIDを使用
  // フロントエンドでは一時的なIDを生成せず、バックエンドのIDに依存する
  const horseId = apiData.id ? String(apiData.id) : '';

  // 必須フィールドに適切なデフォルト値を設定
  const transformed: Horse = {
    // IDはバックエンドで管理されるため、存在しない場合は空文字列を設定
    id: horseId,
    name: apiData.name || '不明な馬',
    sex: apiData.sex || '不明',
    age: apiData.age || 0,
    sire: apiData.sire || '不明',
    dam: apiData.dam || '不明',
    damsire: apiData.dam_sire || apiData.damsire || '不明',
    image_url: apiData.image_url || '',
    jbis_url: apiData.jbis_url || '',
    auction_url: apiData.auction_url || '',
    detail_url: apiData.detail_url || `#/horse/${horseId}`,
    sold_price: apiData.sold_price || null,
    seller: parseSeller(apiData.seller || ''),
    created_at: apiData.created_at || new Date().toISOString(),
    updated_at: apiData.updated_at || new Date().toISOString()
  };

  // オークション履歴を処理
  if (apiData.auction_history && Array.isArray(apiData.auction_history)) {
    // 配列形式の履歴データを処理
    apiData.auction_history.map((history: any, index: number) => ({
      // 履歴IDもバックエンドで管理されるため、存在しない場合は空文字列を設定
      id: history.id || '',
      horse_id: horseId,
      auction_date: history.auction_date || (Array.isArray(apiData.auction_date) ? apiData.auction_date[index] || '' : apiData.auction_date || ''),
      sold_price: history.sold_price || null,
      total_prize_start: history.total_prize_start || 0,
      total_prize_latest: history.total_prize_latest || 0,
      weight: history.weight || null,
      seller: parseSeller(history.seller ?? apiData.seller ?? ''),
      is_unsold: history.is_unsold || false,
      comment: history.comment || '',
      created_at: history.created_at || new Date().toISOString()
    }));
  } else if (apiData.auction_date) {
    // 単一のオークションエントリ用のフォールバック
    [{
      id: `history-${horseId}-0`,
      horse_id: horseId,
      auction_date: Array.isArray(apiData.auction_date) ? apiData.auction_date[0] : apiData.auction_date,
      sold_price: apiData.sold_price || null,
      total_prize_start: apiData.total_prize_start || 0,
      total_prize_latest: apiData.total_prize_latest || 0,
      weight: apiData.weight ? Number(apiData.weight) : null,
      seller: parseSeller(apiData.seller || ''),
      is_unsold: apiData.is_unsold || false,
      comment: Array.isArray(apiData.comment) ? apiData.comment[0] : (apiData.comment || ''),
      created_at: apiData.created_at || new Date().toISOString(),
      updated_at: apiData.updated_at || new Date().toISOString()
    }];
  } else if (apiData.history && Array.isArray(apiData.history)) {
    // 既存のhistory配列がある場合
    apiData.history.map((history: any, index: number) => ({
      id: history.id || `history-${horseId}-${index}`,
      horse_id: horseId,
      auction_date: history.auction_date || (Array.isArray(apiData.auction_date) ? apiData.auction_date[index] : apiData.auction_date) || new Date().toISOString().split('T')[0],
      sold_price: history.sold_price ?? apiData.sold_price ?? null,
      total_prize_start: history.total_prize_start ?? apiData.total_prize_start ?? 0,
      total_prize_latest: history.total_prize_latest ?? apiData.total_prize_latest ?? 0,
      weight: history.weight ?? apiData.weight ?? null,
      seller: parseSeller(history.seller ?? apiData.seller ?? ''),
      is_unsold: (history.is_unsold ?? (history.sold_price === null || history.sold_price === 0)) || false,
      comment: history.comment || apiData.comment || '',
      created_at: history.created_at || new Date().toISOString(),
      updated_at: history.updated_at || new Date().toISOString()
    }));
  } else if (apiData.sold_price || apiData.auction_date) {
    // オークションデータがあるが履歴配列がない場合
    [{
      id: `history-${horseId}-${Date.now()}`,
      horse_id: horseId,
      auction_date: apiData.auction_date || '',
      sold_price: apiData.sold_price || null,
      total_prize_start: apiData.total_prize_start || 0,
      total_prize_latest: apiData.total_prize_latest || 0,
      weight: apiData.weight ? Number(apiData.weight) : null,
      seller: parseSeller(apiData.seller || ''),
      is_unsold: apiData.is_unsold || false,
      comment: apiData.comment || '',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }];
  }

  return transformed;
}

/**
 * Transforms an array of horse data from the API
 * @param data Array of horse data from the API
 * @returns Array of transformed horse data
 */
export function transformHorseArray(data: any[]): Horse[] {
  if (!Array.isArray(data)) {
    console.error('Expected an array of horse data, received:', data);
    return [];
  }
  return data.map(horseData => transformHorseData(horseData));
}
