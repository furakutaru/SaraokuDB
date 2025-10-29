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
    // デバッグ用に馬の情報をログに出力
    console.log('Processing horse with damsire:', {
      id: horse.id,
      name: horse.name,
      dam_sire: horse.dam_sire, // バックエンドからは dam_sire として送られてくる
      damsire: horse.damsire,   // 既存の damsire フィールド（存在する場合）
      dam: horse.dam,
      sire: horse.sire,
      disease_tags: horse.disease_tags,
      hasDiseaseTags: Array.isArray(horse.disease_tags) && horse.disease_tags.length > 0
    });

    // オークションURLを取得（最新のオークション履歴から取得するか、直接指定されたURLを使用）
    const auctionUrl = horse.auction_histories?.[0]?.auction_url || horse.auction_url || '';
    
    const processedHorse = {
      ...horse,
      sold_price: parseSoldPrice(horse.sold_price) !== null ? parseSoldPrice(horse.sold_price) : 
                  (parseSoldPrice(horse.auction_histories?.[0]?.sold_price) !== null ? parseSoldPrice(horse.auction_histories?.[0]?.sold_price) : 
                  (horse.auction_histories?.[0]?.sold_price === 0 ? 0 : null)),
      auction_date: horse.auction_histories?.[0]?.auction_date || horse.auction_date,
      seller: horse.auction_histories?.[0]?.seller || horse.seller,
      is_unsold: horse.auction_histories?.[0]?.is_unsold || horse.is_unsold || false,
      latest_auction: horse.auction_histories?.[0] || null,
      auction_histories: Array.isArray(horse.auction_histories) ? horse.auction_histories : [],
      // 必須プロパティのデフォルト値を設定
      image_url: horse.image_url || '',
      jbis_url: horse.jbis_url || '',
      detail_url: horse.detail_url || '',
      auction_url: auctionUrl, // オークションURLを設定
      weight: horse.weight || 0,
      // 親馬情報を明示的に設定（dam_sire を優先して使用）
      sire: horse.sire || '不明',
      dam: horse.dam || '不明',
      // バックエンドの dam_sire を優先して使用し、なければ既存の damsire を使用
      damsire: horse.dam_sire || horse.damsire || '不明',
      race_records: horse.race_records || { total_prize_money: 0 },
      // disease_tagsを明示的に設定
      disease_tags: Array.isArray(horse.disease_tags) ? horse.disease_tags : []
    } as Horse;

    // 処理後のデータをログに出力
    console.log('Processed horse data:', {
      id: processedHorse.id,
      name: processedHorse.name,
      damsire: processedHorse.damsire,
      dam: processedHorse.dam,
      sire: processedHorse.sire
    });

    return processedHorse;
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
