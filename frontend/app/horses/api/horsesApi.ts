import type { Horse, AuctionHistory } from '../types';
import type { HorseData, HorseResponse, FetchHorsesParams, ApiMetadata } from '../types/api.types';

// APIレスポンスの型定義
interface ApiHorse {
  id: string | number;
  name?: string;
  sex?: string;
  age?: string | number;
  sire?: string;
  dam?: string;
  damsire?: string;
  auction_histories?: Array<{
    id?: number;
    horse_id?: string | number;
    sold_price?: number | null;
    auction_date?: string | string[];
    seller?: string | string[];
    is_unsold?: boolean;
    [key: string]: any;
  }>;
  [key: string]: any;
}

interface ApiResponse {
  horses?: ApiHorse[];
  [key: string]: any;
}

/**
 * 馬IDからオークション履歴を取得する
 * @param horseId 馬のID
 * @returns オークション履歴の配列
 */
export const getAuctionHistories = async (horseId: string | number): Promise<AuctionHistory[]> => {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    const response = await fetch(`${apiUrl}/api/auction_histories/horses/${horseId}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      cache: 'no-store',
    });

    if (!response.ok) {
      // 404の場合は空の配列を返す
      if (response.status === 404) {
        console.warn(`馬ID ${horseId} のオークション履歴は見つかりませんでした`);
        return [];
      }
      
      const errorText = await response.text();
      console.error('オークション履歴の取得に失敗しました:', {
        status: response.status,
        statusText: response.statusText,
        error: errorText,
        horseId
      });
      return [];
    }

    const data = await response.json();
    return Array.isArray(data) ? data : [];
  } catch (error) {
    console.error(`馬ID ${horseId} のオークション履歴取得中にエラーが発生しました:`, error);
    return [];
  }
};

/**
 * 馬の一覧を取得する
 * @returns 馬のデータ
 */
// 文字列の `sold_price` をパースするヘルパー関数
const parseSoldPrice = (price: any): number | null => {
  // null または undefined の場合は null を返す
  if (price === null || price === undefined) return null;
  
  // 数値の場合はそのまま返す
  if (typeof price === 'number') return price;
  
  // 文字列の場合
  if (typeof price === 'string') {
    // 空文字列の場合は null を返す
    if (price.trim() === '') return null;
    
    try {
      // 1. JSON配列としてパースを試みる（例: "[1000000]" や '["1000000"]'）
      if ((price.startsWith('[') && price.endsWith(']')) || 
          (price.startsWith('"["') && price.endsWith('"'))) {
        const parsedArray = JSON.parse(price.replace(/\"/g, '"'));
        if (Array.isArray(parsedArray) && parsedArray.length > 0) {
          const value = parsedArray[0];
          if (typeof value === 'number') return value;
          if (typeof value === 'string') {
            const num = parseInt(value.replace(/,/g, ''), 10);
            return isNaN(num) ? null : num;
          }
        }
      }
      
      // 2. 数値文字列の場合（例: "1000000" や "1,000,000"）
      const numStr = price.replace(/,/g, '');
      if (/^\d+$/.test(numStr)) {
        const parsed = parseInt(numStr, 10);
        return isNaN(parsed) ? null : parsed;
      }
      
      // 3. その他の形式の場合はログを出力して null を返す
      console.warn(`Unsupported price format: ${price}`);
      return null;
    } catch (e) {
      console.warn(`Failed to parse price: ${price}`, e);
      return null;
    }
  }
  
  // その他の型の場合は null を返す
  console.warn(`Unsupported price type: ${typeof price}`, price);
  return null;
};

// 馬データを処理するヘルパー関数
const processHorseData = (horse: any): Horse | null => {
  if (!horse) return null;
  
  return {
    id: horse.id,
    name: horse.name || '名前不明',
    sex: horse.sex || '不明',
    age: horse.age || 0,
    weight: horse.weight || null,
    sire: horse.sire || '不明',
    dam: horse.dam || '不明',
    damsire: horse.damsire || '不明',
    auction_history: horse.auction_histories || [],
    ...horse,
  };
};

// 認証トークンを取得する関数
const getAuthToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('authToken');
  }
  return null;
};

// 認証ヘッダーを取得する関数
const getAuthHeaders = (): HeadersInit => {
  const token = getAuthToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  };
};

/**
 * 馬の一覧を取得する
 * @param params 
 * @returns 馬のデータ
 */

export const fetchHorsesList = async (params: FetchHorsesParams = {}): Promise<HorseData> => {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    const url = new URL(`${apiUrl}/api/horses`);
    
    // クエリパラメータを追加
    if (params.latest_auction) {
      url.searchParams.append('latest_auction', 'true');
    }
    if (params.limit) {
      url.searchParams.append('limit', params.limit.toString());
    }

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        ...getAuthHeaders(),
      },
      cache: 'no-store',
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    // レスポンスの形式を確認し、必要に応じて加工
    const horses = Array.isArray(data) ? data : 
                 (data?.horses || []);
    
    // メタデータを取得（存在する場合）
    const metadata = data?.metadata || {};
    
    const processedHorses = horses
      .map(processHorseData)
      .filter((h: Horse | null): h is Horse => h !== null);
    
    console.log('APIレスポンス:', {
      総数: metadata.total || processedHorses.length,
      取得件数: processedHorses.length,
      メタデータ: metadata
    });
    
    return { 
      horses: processedHorses,
      total: metadata.total || processedHorses.length,
      metadata: {
        ...metadata,
        last_updated: metadata.last_updated || new Date().toISOString()
      }
    };
  } catch (error) {
    console.error('Error fetching horses:', error);
    return { 
      horses: [], 
      total: 0,
      metadata: {
        total: 0,
        skip: 0,
        limit: 0,
        last_updated: new Date().toISOString()
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
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    
    // 馬の基本情報を取得
    const [horseResponse, auctionHistoriesResponse] = await Promise.all([
      fetch(`${apiUrl}/api/horses/${id}`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        cache: 'no-store',
      }),
      // オークション履歴を並行して取得
      getAuctionHistories(id)
    ]);

    // 馬の基本情報のエラーハンドリング
    if (!horseResponse.ok) {
      const errorText = await horseResponse.text();
      console.error('馬の基本情報取得エラー:', {
        status: horseResponse.status,
        statusText: horseResponse.statusText,
        error: errorText
      });
      return null;
    }

    // 馬の基本情報をパース
    const responseData = await horseResponse.json();
    
    // レスポンスから馬データを抽出（新しい形式と古い形式の両方に対応）
    const horseData = responseData.horse || responseData;
    
    // オークション履歴をマージ（既存の履歴があればそれを使用、なければ取得した履歴を使用）
    if (!horseData.auction_histories || horseData.auction_histories.length === 0) {
      horseData.auction_histories = Array.isArray(auctionHistoriesResponse) ? 
        auctionHistoriesResponse : [];
    }
    
    console.log('馬データ取得:', {
      id: horseData.id,
      name: horseData.name,
      オークション履歴件数: horseData.auction_histories?.length || 0,
      最終更新: responseData.metadata?.last_updated || '不明'
    });
    
    return horseData as Horse;
  } catch (error) {
    console.error(`Error fetching horse with id ${id}:`, error);
    return null;
  }
};
