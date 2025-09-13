import { useState, useEffect } from 'react';

export interface HorseData {
  id: string;
  name: string;
  sex: string;
  age: number;
  sire: string;
  dam: string;
  damsire: string;
  auction_date: string;
  sold_price: number | null;
  seller: string;
  history?: Array<{
    auction_date: string;
    sold_price: number | string | null;
    seller: string;
    [key: string]: any;
  }>;
  unsold?: boolean;
  original_sold_price?: number | string | null; // デバッグ用
  [key: string]: any;
}

interface DataIntegrityResult {
  data: HorseData[];
  isLoading: boolean;
  error: string | null;
}

export function useDataIntegrityCheck(): DataIntegrityResult {
  const [result, setResult] = useState<Omit<DataIntegrityResult, 'isLoading' | 'error'>>({
    data: [],
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkDataIntegrity = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // バックエンドAPIからデータを取得 (ポート8001を使用)
        const response = await fetch('http://localhost:8001/horses/');
        if (!response.ok) {
          throw new Error(`データの取得に失敗しました: ${response.status} ${response.statusText}`);
        }
        
        const responseData = await response.json();
        console.log('APIレスポンスデータ（生）:', responseData);
        
        // レスポンスから馬データを抽出
        let horsesData: HorseData[] = [];
        
        // レスポンスが成功し、dataプロパティが配列の場合
        if (responseData && responseData.status === 'success' && Array.isArray(responseData.data)) {
          console.log('dataプロパティから馬データを抽出します');
          horsesData = responseData.data;
        }
        // レスポンスが配列の場合はそのまま使用（後方互換性のため）
        else if (Array.isArray(responseData)) {
          console.log('配列形式のレスポンスを処理します');
          horsesData = responseData;
        } 
        // レスポンスがオブジェクトでhorsesプロパティが配列の場合（後方互換性のため）
        else if (responseData && typeof responseData === 'object' && 'horses' in responseData && Array.isArray(responseData.horses)) {
          console.log('horsesプロパティからデータを抽出します');
          horsesData = responseData.horses;
        } 
        // その他の形式はエラー
        else {
          console.error('予期しないデータ形式です:', responseData);
          throw new Error('無効なデータ形式です: 有効な馬データの配列が見つかりません');
        }

        console.log('抽出された馬データの最初の3件:', horsesData.slice(0, 3));
        
        // history配列から最新のオークション情報を取得し、sold_priceとunsoldフラグを設定
        const processedHorses = horsesData.map(horse => {
          // 最新のオークション情報を取得（history配列の最後の要素）
          const latestAuction = horse.history && horse.history.length > 0 
            ? horse.history[horse.history.length - 1] 
            : null;
          
          // sold_priceを最新のオークション情報から取得
          const soldPrice = latestAuction?.sold_price;
          // 数値に変換を試みる
          let soldPriceNum: number | null = null;
          let isUnsold = true;
          
          if (soldPrice !== null && soldPrice !== undefined) {
            const num = Number(soldPrice);
            if (!isNaN(num) && num > 0) {
              soldPriceNum = num;
              isUnsold = false;
            }
          }
          
          return {
            ...horse,
            sold_price: soldPriceNum,  // 数値に変換したsold_priceで上書き
            unsold: isUnsold,          // 主取りフラグを設定
            original_sold_price: soldPrice,  // デバッグ用に元の値も保持
            _debug: {                   // デバッグ用の追加情報
              originalType: typeof soldPrice,
              convertedValue: soldPriceNum,
              isUnsold: isUnsold
            }
          };
        });
        
        console.log('処理後の馬データ（最初の3件）:', processedHorses.slice(0, 3));
        
        // 結果を設定
        setResult({
          data: processedHorses,
        });
      } catch (err) {
        console.error('データ整合性チェックエラー:', err);
        setError(err instanceof Error ? err.message : 'データの整合性チェック中にエラーが発生しました');
      } finally {
        setIsLoading(false);
      }
    };

    checkDataIntegrity();
  }, []);

  return {
    ...result,
    isLoading,
    error,
  };
}
