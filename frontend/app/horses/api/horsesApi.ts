import type { Horse, AuctionHistory, HorseData } from '../types';

/**
 * 馬IDからオークション履歴を取得する
 * @param horseId 馬のID
 * @returns オークション履歴の配列
 */
export const getAuctionHistories = async (horseId: string | number): Promise<AuctionHistory[]> => {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    const response = await fetch(`${apiUrl}/api/horses/${horseId}/auction-histories`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      cache: 'no-store',
    });

    if (!response.ok) {
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
export const fetchHorsesList = async (): Promise<HorseData> => {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    // 最新のオークションに出品された馬のみを取得するためのパラメータを追加
    const url = new URL(`${apiUrl}/api/horses`);
    url.searchParams.append('latest_auction', 'true');
    
    console.log('API URL:', url.toString());
    
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      cache: 'no-store',
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('API Error Response:', {
        status: response.status,
        statusText: response.statusText,
        error: errorText
      });
      throw new Error(`データの取得に失敗しました (${response.status} ${response.statusText})`);
    }

    const data = await response.json();
    console.log('API Response data type:', typeof data);
    
    // 最初の馬のデータをログに出力
    const sampleHorse = data.horses?.[0];
    console.log('Sample horse data:', JSON.stringify(sampleHorse, null, 2));
    
    // すべての馬のsold_priceを確認
    if (data.horses) {
      console.log('All sold_prices:');
      data.horses.forEach((horse: any, index: number) => {
        const price = horse.auction_histories?.[0]?.sold_price;
        console.log(`Horse ${index + 1} (${horse.name}):`, {
          value: price,
          type: typeof price,
          auction_histories: horse.auction_histories?.[0] 
            ? 'exists' 
            : 'no auction history'
        });
      });
    }
    
    // レスポンスが配列の場合はオブジェクトに変換
    if (Array.isArray(data)) {
      return { horses: data };
    }
    
    // レスポンスがオブジェクトでhorsesプロパティを持つ場合
    if (data && Array.isArray(data.horses)) {
      return { horses: data.horses };
    }
    
    // それ以外の形式の場合は空の配列を返す
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
    console.log(`Fetching horse with id: ${id} from ${apiUrl}/api/horses/${id}`);
    
    const response = await fetch(`${apiUrl}/api/horses/${id}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('API Error Response:', {
        status: response.status,
        statusText: response.statusText,
        error: errorText
      });
      throw new Error(`データの取得に失敗しました (${response.status} ${response.statusText})`);
    }

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    return data as Horse;
  } catch (error) {
    console.error(`Error fetching horse with id ${id}:`, error);
    return null;
  }
};
