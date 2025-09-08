import { Horse, AuctionHistory } from '../types/horse';

/**
 * Transforms the API response to match the frontend's expected format
 * @param apiData Raw data from the API
 * @returns Transformed horse data in the frontend format
 */
export function transformHorseData(apiData: any): Horse {
  // 安定したIDを生成（IDがない場合）
  const horseId = apiData.id 
    ? String(apiData.id)
    : `horse-${apiData.name ? apiData.name.replace(/\s+/g, '-').toLowerCase() : 'unknown'}-${Date.now()}`;

  // 必須フィールドに適切なデフォルト値を設定
  const transformed: Horse = {
    id: horseId,
    name: apiData.name || '不明な馬名',
    sex: Array.isArray(apiData.sex) ? apiData.sex[0] || '' : (apiData.sex || ''),
    age: Array.isArray(apiData.age) ? apiData.age[0] || 0 : (apiData.age || 0),
    sire: apiData.sire || '不明',
    dam: apiData.dam || '不明',
    damsire: apiData.dam_sire || apiData.damsire || '不明',
    image_url: apiData.image_url || '',
    jbis_url: apiData.jbis_url || '',
    auction_url: apiData.auction_url || '',
    disease_tags: apiData.disease_tags 
      ? (Array.isArray(apiData.disease_tags) 
          ? apiData.disease_tags 
          : [apiData.disease_tags]) 
      : [],
    created_at: apiData.created_at || new Date().toISOString(),
    updated_at: apiData.updated_at || new Date().toISOString(),
    auction_history: []
  };

  // オークション履歴を処理
  if (apiData.auction_history && Array.isArray(apiData.auction_history)) {
    // 配列形式の履歴データを処理
    transformed.auction_history = apiData.auction_history.map((history: any, index: number) => ({
      id: history.id || `history-${horseId}-${index}`,
      horse_id: horseId,
      auction_date: history.auction_date || (Array.isArray(apiData.auction_date) ? apiData.auction_date[index] : apiData.auction_date) || '',
      sold_price: history.sold_price || null,
      total_prize_start: history.total_prize_start || 0,
      total_prize_latest: history.total_prize_latest || 0,
      weight: history.weight || null,
      seller: history.seller || '',
      is_unsold: history.is_unsold || false,
      comment: history.comment || '',
      created_at: history.created_at || new Date().toISOString()
    }));
  } else if (apiData.auction_date) {
    // 単一のオークションエントリ用のフォールバック
    transformed.auction_history = [{
      id: `history-${horseId}-0`,
      horse_id: horseId,
      auction_date: Array.isArray(apiData.auction_date) ? apiData.auction_date[0] : apiData.auction_date,
      sold_price: apiData.sold_price || null,
      total_prize_start: apiData.total_prize_start || 0,
      total_prize_latest: apiData.total_prize_latest || 0,
      weight: apiData.weight || null,
      seller: Array.isArray(apiData.seller) ? apiData.seller[0] : (apiData.seller || ''),
      is_unsold: apiData.is_unsold || false,
      comment: Array.isArray(apiData.comment) ? apiData.comment[0] : (apiData.comment || ''),
      created_at: apiData.created_at || new Date().toISOString()
    }];
  } else if (apiData.history && Array.isArray(apiData.history)) {
    // 既存のhistory配列がある場合
    transformed.auction_history = apiData.history.map((history: any, index: number) => ({
      id: history.id || `history-${horseId}-${index}`,
      horse_id: horseId,
      auction_date: history.auction_date || (Array.isArray(apiData.auction_date) ? apiData.auction_date[index] : apiData.auction_date) || new Date().toISOString().split('T')[0],
      sold_price: history.sold_price ?? apiData.sold_price ?? null,
      total_prize_start: history.total_prize_start ?? apiData.total_prize_start ?? 0,
      total_prize_latest: history.total_prize_latest ?? apiData.total_prize_latest ?? 0,
      weight: history.weight ?? apiData.weight ?? null,
      seller: history.seller || apiData.seller || '',
      is_unsold: (history.is_unsold ?? (history.sold_price === null || history.sold_price === 0)) || false,
      comment: history.comment || apiData.comment || '',
      created_at: history.created_at || new Date().toISOString()
    }));
  } else if (apiData.sold_price || apiData.auction_date) {
    // オークションデータがあるが履歴配列がない場合
    transformed.auction_history = [{
      id: `history-${horseId}-${Date.now()}`,
      horse_id: horseId,
      auction_date: apiData.auction_date || '',
      sold_price: apiData.sold_price || null,
      total_prize_start: apiData.total_prize_start || 0,
      total_prize_latest: apiData.total_prize_latest || 0,
      weight: apiData.weight || null,
      seller: apiData.seller || '',
      is_unsold: apiData.is_unsold || false,
      comment: apiData.comment || '',
      created_at: new Date().toISOString()
    }];
  }

  return transformed;
}

/**
 * Transforms an array of horse data
 * @param data Array of horse data from the API
 * @returns Array of transformed horse data
 */
export function transformHorseArray(data: any[]): Horse[] {
  return data.map(horse => transformHorseData(horse));
}
