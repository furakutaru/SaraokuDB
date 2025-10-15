import { HorseData } from '../types';

/**
 * 文字列から不正な文字を除去するヘルパー関数
 */
const sanitizeString = (str: any): string => {
  if (str === null || str === undefined) return '';
  if (Array.isArray(str)) {
    // 配列の場合は最初の要素を文字列に変換
    return sanitizeString(str[0]);
  }
  if (typeof str !== 'string') return String(str);
  // 制御文字や不正なUnicode文字を削除
  return str.replace(/[\u0000-\u001F\u007F-\u009F\uD800-\uDFFF]/g, '').trim();
};

/**
 * Fetches the list of horses from the API
 * @param latestOnly Whether to fetch only the latest auction data
 * @returns A promise that resolves to the horse data
 */
export const fetchHorsesList = async (latestOnly: boolean = false): Promise<HorseData> => {
  try {
    // 環境変数からAPIのベースURLを取得、デフォルトはローカルのバックエンドサーバー（ポート8001）
    // バックエンドのAPIRouterが /api プレフィックスを期待しているため、明示的に追加
    const baseUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001') + '/api';
    
    // 最新のオークションのみを取得するかどうかでエンドポイントを切り替え
    const endpoint = latestOnly ? '/horses/latest' : '/horses';
    // 連続するスラッシュを削除しつつ、パスを正しく結合
    const url = `${baseUrl}${endpoint}`.replace(/([^:]\/)\/+/g, '$1');
    
    console.log(`[fetchHorsesList] リクエストURL: ${url}`);
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store'
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // テキストとして取得してからパースすることで、不正なUTF-8文字を処理
    const responseText = await response.text();
    let responseData;
    
    try {
      // 正規表現を使用して不正なUTF-8文字を除去
      const cleanText = responseText.replace(/[\u0000-\u001F\u007F-\u009F\uD800-\uDFFF]/g, '');
      responseData = JSON.parse(cleanText);
    } catch (parseError) {
      console.error('[fetchHorsesList] JSONパースエラー:', parseError);
      // エラーが発生した場合は空のレスポンスを返す
      return {
        horses: [],
        auctionHistories: [],
        metadata: {
          last_updated: new Date().toISOString(),
          total_horses: 0,
          total_auction_records: 0
        }
      };
    }
    
    console.log('[fetchHorsesList] APIレスポンス:', {
      hasHorses: !!responseData.horses,
      horsesCount: responseData.horses?.length || 0,
      hasAuctionHistories: !!(responseData.auction_histories || responseData.auctionHistories),
      auctionHistoriesCount: (responseData.auction_histories || responseData.auctionHistories || []).length,
      metadata: responseData.metadata
    });

    // データの正規化
    const horses = Array.isArray(responseData.horses) 
      ? responseData.horses.map((horse: any) => ({
          ...horse,
          // 文字列フィールドのサニタイズ
          name: sanitizeString(horse.name),
          sire: sanitizeString(horse.sire),
          dam: sanitizeString(horse.dam),
          damsire: sanitizeString(horse.damsire),
          seller: sanitizeString(horse.seller),
          // 配列フィールドのサニタイズ
          disease_tags: Array.isArray(horse.disease_tags) 
            ? horse.disease_tags.map((tag: any) => sanitizeString(tag))
            : []
        }))
      : [];
      
    const auctionHistories = Array.isArray(responseData.auction_histories) 
      ? responseData.auction_histories.map((history: any) => ({
          ...history,
          // 文字列フィールドのサニタイズ
          seller: sanitizeString(history.seller),
          comment: sanitizeString(history.comment)
        }))
      : (Array.isArray(responseData.auctionHistories) 
          ? responseData.auctionHistories.map((history: any) => ({
              ...history,
              // 文字列フィールドのサニタイズ
              seller: sanitizeString(history.seller),
              comment: sanitizeString(history.comment)
            }))
          : []);

    return {
      horses,
      auctionHistories,
      metadata: {
        last_updated: responseData.metadata?.last_updated || new Date().toISOString(),
        total_horses: responseData.metadata?.total_horses || horses.length,
        total_auction_records: responseData.metadata?.total_auction_records || auctionHistories.length
      }
    };
  } catch (error) {
    console.error('[fetchHorsesList] エラー:', error);
    // エラー時に空のデータを返す
    return {
      horses: [],
      auctionHistories: [],
      metadata: {
        last_updated: new Date().toISOString(),
        total_horses: 0,
        total_auction_records: 0
      }
    };
  }
};

/**
 * Helper function to get auction histories from data
 * @param data The horse data
 * @returns An array of auction histories
 */
export const getAuctionHistories = (data: HorseData | null): any[] => {
  if (!data) return [];
  // どちらのプロパティ名でも取得できるようにする
  return data.auctionHistories || data.auction_histories || [];
};
