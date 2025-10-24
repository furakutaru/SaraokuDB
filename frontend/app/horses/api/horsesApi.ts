import type { Horse, AuctionHistory, HorseData } from '../types';

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
  
  try {
    // デバッグ用ログ
    console.log('Horse data before mapping:', JSON.stringify({
      id: horse.id,
      name: horse.name,
      sold_price: horse.sold_price,
      auction_histories: horse.auction_histories ? 'exists' : 'not exists',
      has_latest_auction: !!(horse.auction_histories?.[0])
    }, null, 2));

    // オークション履歴を処理
    const auctionHistories = Array.isArray(horse.auction_histories) 
      ? horse.auction_histories 
      : [];
    
    // 最新のオークション情報を取得
    const latestAuction = auctionHistories[0] || {};
    
    // 販売価格をパース
    const soldPrice = parseSoldPrice(horse.sold_price) || 
                     parseSoldPrice(latestAuction.sold_price) || 
                     null;
    
    // 馬データを構築
    const processedHorse: any = {
      ...horse,
      sold_price: soldPrice,
      auction_date: latestAuction.auction_date || horse.auction_date || null,
      seller: latestAuction.seller || horse.seller || null,
      is_unsold: latestAuction.is_unsold || horse.is_unsold || false,
      latest_auction: latestAuction || null,
      auction_histories: auctionHistories,
      // 必須プロパティのデフォルト値を設定
      image_url: horse.image_url || '',
      jbis_url: horse.jbis_url || '',
      detail_url: horse.detail_url || '',
      auction_url: horse.auction_url || '',
      weight: horse.weight || 0,
      // その他の必須プロパティ
      sire: horse.sire || '',
      dam: horse.dam || '',
      damsire: horse.damsire || '',
      race_records: horse.race_records || { total_prize_money: 0 }
    };
    
    console.log('Processed horse data:', JSON.stringify({
      id: processedHorse.id,
      name: processedHorse.name,
      sold_price: processedHorse.sold_price,
      auction_histories_count: processedHorse.auction_histories?.length || 0
    }, null, 2));
    
    return processedHorse as Horse;
  } catch (error) {
    console.error('Error processing horse data:', error, 'Horse data:', horse);
    return null;
  }
};

// 認証トークンを取得するヘルパー関数
const getAuthToken = (): string | null => {
  // GitHub Actions環境では環境変数からトークンを取得
  if (process.env.GITHUB_ACTIONS === 'true' && process.env.AUTH_TOKEN) {
    return process.env.AUTH_TOKEN;
  }
  // ブラウザ環境の場合
  if (typeof window !== 'undefined') {
    return localStorage.getItem('authToken') || null;
  }
  return null;
};

export const fetchHorsesList = async (): Promise<HorseData> => {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    const url = new URL(`${apiUrl}/api/horses/`);
    
    // 認証トークンを取得
    const token = getAuthToken();
    const headers: HeadersInit = {
      'Accept': 'application/json',
    };
    
    // トークンがあればヘッダーに追加
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
      console.log('認証トークンを設定しました（トークンの長さ）:', token.length);
    } else {
      console.warn('認証トークンが設定されていません');
    }

    console.log('API URL:', url.toString());
    console.log('リクエストヘッダー:', JSON.stringify(headers));
    
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers,
      cache: 'no-store',
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('API Error:', {
        status: response.status,
        statusText: response.statusText,
        error: errorText
      });
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('API Response:', data);
    
    // レスポンスが配列の場合はそのまま処理
    if (Array.isArray(data)) {
      return { 
        horses: data.map(processHorseData).filter((h: Horse | null): h is Horse => h !== null)
      };
    }
    
    // レスポンスがオブジェクトでhorsesプロパティを持つ場合
    if (data && typeof data === 'object' && 'horses' in data) {
      const horses = Array.isArray(data.horses) 
        ? data.horses.map(processHorseData).filter((h: Horse | null): h is Horse => h !== null)
        : [];
      
      return { horses };
    }
    
    // 予期しないレスポンス形式の場合は空の配列を返す
    console.warn('予期しないレスポンス形式:', data);
    return { horses: [] };
  } catch (error) {
    console.error('Error fetching horses:', error);
    return { horses: [] };
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
    const horseData = await horseResponse.json();
    
    // オークション履歴をマージ
    if (Array.isArray(auctionHistoriesResponse)) {
      horseData.auction_histories = auctionHistoriesResponse;
    } else {
      horseData.auction_histories = [];
    }
    
    return horseData as Horse;
  } catch (error) {
    console.error(`Error fetching horse with id ${id}:`, error);
    return null;
  }
};
