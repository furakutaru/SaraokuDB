import { useState, useEffect, useCallback } from 'react';
import { Horse, HorseData } from '../types';
import { fetchHorsesList, getAuctionHistories } from '../api/horsesApi';

interface HorsesData {
  horses: Horse[];
  loading: boolean;
  error: string | null;
  refreshData: () => Promise<void>;
}

// 文字列の `sold_price` をパースするヘルパー関数
const parseSoldPrice = (price: any): number | null => {
  if (price === null || price === undefined) return null;
  if (typeof price === 'number') return price;
  if (typeof price === 'string') {
    // 文字列が配列形式（例: "[1000000]"）の場合にパース
    const match = price.match(/\["?([0-9,]+)"?\]/);
    if (match && match[1]) {
      return parseInt(match[1].replace(/,/g, ''), 10);
    }
    // 通常の数値文字列の場合
    const parsed = parseInt(price.replace(/,/g, ''), 10);
    return isNaN(parsed) ? null : parsed;
  }
  return null;
};

interface UseHorsesDataParams {
  latestAuction?: boolean;
}

export const useHorsesData = ({ latestAuction = true }: UseHorsesDataParams = {}): HorsesData => {
  const [horses, setHorses] = useState<Horse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const processHorseData = (horse: any): Horse => {
    return {
      ...horse,
      sold_price: parseSoldPrice(horse.sold_price) || parseSoldPrice(horse.auction_histories?.[0]?.sold_price) || null,
      auction_date: horse.auction_histories?.[0]?.auction_date || horse.auction_date,
      seller: horse.auction_histories?.[0]?.seller || horse.seller,
      is_unsold: horse.auction_histories?.[0]?.is_unsold || horse.is_unsold || false,
      latest_auction: horse.auction_histories?.[0] || null,
      auction_histories: Array.isArray(horse.auction_histories) ? horse.auction_histories : [],
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
    } as Horse;
  };

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // 馬の一覧を取得（最新のオークションの馬のみを取得）
      const response = await fetchHorsesList({ latest_auction: latestAuction });
      
      let horsesData: Horse[] = [];
      
      if (typeof response === 'string') {
        // エラーメッセージの場合は空の配列を設定
        horsesData = [];
      } else if (response && typeof response === 'object' && 'horses' in response && Array.isArray(response.horses)) {
        // { horses: [...] } の形式の場合
        horsesData = response.horses.map(processHorseData);
      } else if (Array.isArray(response)) {
        // 配列が直接返ってきた場合
        horsesData = response.map(processHorseData);
      } else if (response && typeof response === 'object' && 'data' in response && 
                 response.data && typeof response.data === 'object' && 
                 'horses' in response.data && Array.isArray(response.data.horses)) {
        // { data: { horses: [...] } } の形式の場合
        horsesData = response.data.horses.map(processHorseData);
      } else {
        // その他の形式の場合は空の配列を返す
        console.warn('予期しないレスポンス形式:', response);
        horsesData = [];
      }
      
      setHorses(horsesData);
    } catch (err) {
      console.error('Error fetching horses data:', err);
      setError('データの取得中にエラーが発生しました');
      setHorses([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    horses,
    loading,
    error,
    refreshData: fetchData,
  };
};
