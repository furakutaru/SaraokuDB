import { useState, useEffect, useCallback } from 'react';
import { Horse, HorseData } from '../types';
import { fetchHorsesList, getAuctionHistories } from '../api/horsesApi';

interface HorsesData {
  horses: Horse[];
  loading: boolean;
  error: string | null;
  refreshData: () => Promise<void>;
}

export const useHorsesData = (): HorsesData => {
  const [horses, setHorses] = useState<Horse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // 馬の一覧を取得
      const response = await fetchHorsesList();
      let horses: Horse[] = [];
      
      if (typeof response === 'string') {
        // エラーメッセージの場合は空の配列を設定
        horses = [];
      } else if ('data' in response) {
        // dataプロパティがある場合は、その中からhorsesを取得
        const data = response.data as Partial<HorseData>;
        horses = data.horses || [];
      } else {
        // 直接Horseの配列が返ってきた場合
        horses = Array.isArray(response) ? response : [];
      }
      
      // 各馬のオークション履歴を取得
      const horsesWithHistory = await Promise.all(
        horses.map(async (horse: Horse) => {
          if (!horse.id) return horse;
          
          try {
            // 馬のデータからオークション履歴を取得
            const auctionHistories = horse.auction_histories || [];
            
            return {
              ...horse,
              auction_histories: Array.isArray(auctionHistories) ? auctionHistories : []
            };
          } catch (error) {
            console.error(`Failed to fetch history for horse ${horse.id}:`, error);
            return { 
              ...horse,
              auction_histories: [] 
            };
          }
        })
      );

      setHorses(horsesWithHistory.filter((h): h is Horse => h !== undefined));
    } catch (err) {
      console.error('Error fetching horses data:', err);
      setError('データの取得中にエラーが発生しました');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    horses: horses || [],
    loading,
    error,
    refreshData: fetchData,
  } as const;
};
