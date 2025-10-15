import type { Horse, AuctionHistory, HorseData, ApiMetadata } from '../types';

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
 * APIのベースURLを取得する
 */
const getApiBaseUrl = (): string => {
  // 環境変数からAPIのベースURLを取得、デフォルトはローカルのバックエンドサーバー（ポート8001）
  // バックエンドのAPIRouterが /api プレフィックスを期待しているため、明示的に追加
  const baseUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001') + '/api';
  return baseUrl.replace(/([^:]\/)\/+/g, '$1'); // 連続するスラッシュを削除
};

/**
 * エラーレスポンスを処理する
 */
const handleErrorResponse = async (response: Response): Promise<never> => {
  let errorMessage = `HTTP error! status: ${response.status}`;
  try {
    const errorData = await response.json();
    errorMessage = errorData.detail || errorMessage;
    console.error('Error parsing error response:', errorData);
  } catch (error) {
    console.error('Error parsing error response:', error);
  }
  throw new Error(errorMessage);
};

export interface HorseResponse {
  horse: Horse;
  auction_histories?: AuctionHistory[];
}

/**
 * 馬の一覧を取得する
 * @param latestOnly 最新のデータのみ取得するかどうか
 * @returns 馬のデータ
 */
export const fetchHorsesList = async (latestOnly: boolean = false): Promise<HorseData> => {
  try {
    const baseUrl = getApiBaseUrl();
    const endpoint = latestOnly ? '/horses/latest' : '/horses';
    const url = `${baseUrl}${endpoint}`;
    
    console.log(`[fetchHorsesList] リクエストURL: ${url}`);
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
      },
      cache: 'no-store',
      next: { revalidate: 60 } // 60秒間キャッシュ
    });

    if (!response.ok) {
      return await handleErrorResponse(response);
    }

    const responseText = await response.text();
    let responseData;
    
    try {
      // 正規表現を使用して不正なUTF-8文字を除去
      const cleanText = responseText.replace(/[\u0000-\u001F\u007F-\u009F\uD800-\uDFFF]/g, '');
      responseData = JSON.parse(cleanText);
    } catch (parseError) {
      console.error('[fetchHorsesList] JSONパースエラー:', parseError);
      // エラー時に空のデータを返す
      return {
        horses: [],
        auction_histories: [],
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
      hasAuctionHistories: !!responseData.auction_histories,
      auctionHistoriesCount: responseData.auction_histories?.length || 0,
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
      : [];

    return {
      horses,
      auction_histories: auctionHistories,
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
      auction_histories: [],
      metadata: {
        last_updated: new Date().toISOString(),
        total_horses: 0,
        total_auction_records: 0
      }
    };
  }
};

/**
 * 馬の詳細を取得する
 * @param id 馬のID
 * @returns 馬の詳細データ
 */
export const fetchHorseById = async (id: string | number): Promise<Horse | null> => {
  try {
    const baseUrl = getApiBaseUrl();
    const url = `${baseUrl}/horses/${id}`;
    
    console.log(`[fetchHorseById] リクエストURL: ${url}`);
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
      },
      next: { revalidate: 60 } // 60秒間キャッシュ
    });

    if (!response.ok) {
      if (response.status === 404) {
        console.log(`[fetchHorseById] 馬ID ${id} のデータが見つかりませんでした`);
        return null;
      }
      return await handleErrorResponse(response);
    }

    const responseText = await response.text();
    let responseData: HorseResponse;
    
    try {
      // 正規表現を使用して不正なUTF-8文字を除去
      const cleanText = responseText.replace(/[\u0000-\u001F\u007F-\u009F\uD800-\uDFFF]/g, '');
      responseData = JSON.parse(cleanText);
    } catch (parseError) {
      console.error('[fetchHorseById] JSONパースエラー:', parseError);
      throw new Error('馬データの解析に失敗しました');
    }

    if (!responseData.horse) {
      console.error('[fetchHorseById] 無効なレスポンス形式:', responseData);
      throw new Error('無効なレスポンス形式です');
    }

    return responseData.horse;
  } catch (error) {
    console.error(`[fetchHorseById] エラーが発生しました:`, error);
    throw error;
  }
};

/**
 * オークション履歴を取得する
 * @param horse 馬データ
 * @returns オークション履歴の配列
 */
export const getAuctionHistories = (horse: Horse | null): AuctionHistory[] => {
  if (!horse) return [];
  
  // history または auction_histories から履歴を取得
  const histories = horse.history 
    ? (Array.isArray(horse.history) ? horse.history : [horse.history])
    : horse.auction_histories || [];
  
  // 日付でソート（新しい順）
  return [...histories].sort((a: AuctionHistory, b: AuctionHistory) => {
    const getDate = (date: string | string[] | undefined): Date => {
      if (!date) return new Date(0);
      const dateStr = Array.isArray(date) ? date[0] : date;
      return new Date(dateStr) || new Date(0);
    };
    
    return getDate(b.auction_date).getTime() - getDate(a.auction_date).getTime();
  });
};
