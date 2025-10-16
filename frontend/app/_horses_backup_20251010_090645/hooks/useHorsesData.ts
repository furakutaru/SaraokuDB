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
      let horsesData: HorseData;
      
      if (typeof response === 'string') {
        horsesData = { horses: [] };
      } else if ('data' in response) {
        horsesData = response.data as HorseData;
      } else {
        horsesData = response as unknown as HorseData;
      }
      
      // 各馬のオークション履歴を取得
      const horsesWithHistory = await Promise.all(
        (horsesData.horses || []).map(async (horse: Horse) => {
          if (!horse.id) return horse;
          
          try {
            // 馬のデータからオークション履歴を取得
            const auctionHistories = getAuctionHistories({ horses: [horse] }) || [];
            
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
    horses,
    loading,
    error,
    refreshData: fetchData,
  };
};
