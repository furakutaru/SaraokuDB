'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CustomButton } from '@/components/ui/CustomButton';
import Link from 'next/link';

// 通貨をフォーマットするヘルパー関数
const formatCurrency = (value: number | string | null | undefined): string => {
  if (value === null || value === undefined || value === '') return '-';
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(numValue) || numValue <= 0) return '-';
  
  return new Intl.NumberFormat('ja-JP', {
    style: 'currency',
    currency: 'JPY',
    maximumFractionDigits: 0
  }).format(numValue);
};

// フォーマット関数をインポート
import { formatPrice, formatPrize } from '@/utils/format';

// normalize.ts から formatSex と getSexColor をインポート
import { formatSex, getSexColor } from '@/utils/normalize';

// 日付をフォーマットするヘルパー関数
const formatDate = (dateString: string | undefined): string => {
  if (!dateString) return '-';
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).format(date);
  } catch (e) {
    return '-';
  }
};

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Horse, AuctionHistory, HorseWithCalculations } from '@/types/horse';
import { HorseTable } from './horses/HorseTable';

// HorseWithCalculations 型を使用

interface HorseData {
  horses: Horse[];
  auction_histories: AuctionHistory[];
  metadata: {
    total: number;
    count: number;
    total_auctions?: number;
    average_price?: number;
    last_updated?: string;
    total_horses?: number; // 後方互換性のため
  };
}

// オークション履歴を馬ごとにグループ化する関数
const groupAuctionHistory = (auctionHistory: AuctionHistory[]): Record<string, AuctionHistory[]> => {
  return auctionHistory.reduce((acc, auction) => {
    const horseId = String(auction.horse_id);
    if (!acc[horseId]) {
      acc[horseId] = [];
    }
    acc[horseId].push(auction);
    return acc;
  }, {} as Record<string, AuctionHistory[]>);
};

export default function AnalysisContent() {
  const [horses, setHorses] = useState<HorseWithCalculations[]>([]);
  const [filteredHorses, setFilteredHorses] = useState<HorseWithCalculations[]>([]);
  // オークション履歴は使用しないため削除
  // setAuctionHistory は使用しないため削除
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<{
    total: number;
    count: number;
    total_auctions?: number;
    average_price?: number;
    last_updated?: string;
    total_horses?: number; // 後方互換性のため
  }>({
    total: 0,
    count: 0,
    total_auctions: 0,
    average_price: 0,
    last_updated: new Date().toISOString(),
  });
  const [showType, setShowType] = useState<'all' | 'roi' | 'value'>('all');
  const [sortKey, setSortKey] = useState<string>('');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const router = useRouter();

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';
        
        // 馬データを取得
        console.log('馬データの取得を開始します...');
        const response = await fetch(`${apiBaseUrl}/api/horses`, { 
          cache: 'no-store',
          headers: {
            'Content-Type': 'application/json',
          }
        });
        
        console.log('APIリクエスト完了:', response.status, response.statusText);

        if (!response.ok) {
          let errorData;
          try {
            errorData = await response.json();
            console.error('APIエラーレスポンス:', {
              status: response.status,
              statusText: response.statusText,
              errorData,
              url: response.url
            });
          } catch (jsonError) {
            console.error('エラーレスポンスの解析に失敗しました:', jsonError);
          }
          throw new Error(`データの取得に失敗しました: ${response.status} ${response.statusText}`);
        }

        const responseData = await response.json();
        console.log('APIレスポンスを受信しました:', responseData);
        
        // データのバリデーションと正規化
        let data = [];
        if (Array.isArray(responseData)) {
          data = responseData;
        } else if (responseData && typeof responseData === 'object') {
          data = responseData.horses || responseData.data || 
                 Object.values(responseData).filter((item: any) => 
                   item && typeof item === 'object' && 'id' in item
                 );
        }
        
        if (!Array.isArray(data)) {
          console.error('無効な馬データ形式です:', responseData);
          throw new Error('無効なデータ形式です: 有効な馬データが見つかりません');
        }
        
        console.log(`馬データを取得しました: ${data.length}件`);
        
        // デバッグ用: 最初の馬データの全フィールドをログに出力（データがある場合のみ）
        if (data.length > 0) {
          console.log('最初の馬データの全フィールド:', Object.keys(data[0]));
          console.log('最初の馬データのjbis_url:', data[0].jbis_url || data[0].jbisUrl || '未設定');
        } else {
          console.warn('馬データが空です');
        }

        const horsesWithAuction = data.map((horse: any) => {
          const mappedHorse = {
            ...horse,
            dam_sire: horse.dam_sire || '',
            detail_url: horse.detail_url || '',
            jbis_url: horse.jbis_url || horse.jbisUrl || '', // jbis_url または jbisUrl のいずれかが存在する場合に設定
            comment: horse.comment,
            race_record: horse.race_record,
            race_records: horse.race_records
          };
          
          // デバッグ用: 最初の数件の馬データをログに出力
          if (horse.id <= 5) {
            console.log(`馬ID: ${horse.id}, 名前: ${horse.name}, jbis_url: ${mappedHorse.jbis_url}`);
          }
          
          return mappedHorse;
        });
        
        setHorses(horsesWithAuction);
        // メタデータを更新
        const newMetadata = {
          total: data.length,
          count: data.length,
          total_auctions: 0,
          average_price: 0,
          last_updated: new Date().toISOString(),
          total_horses: data.length
        };
        
        setMetadata(newMetadata);

        // オークション履歴は使用しないため空のオブジェクトを設定
        const auctionHistoryByHorseId: Record<string, any[]> = {};
        
        // 馬データにオークション情報をマージ
        const horsesWithHistory = horsesWithAuction.map((horse: HorseWithCalculations) => {
          // デバッグ用: ホワイトアッシュのデータをログに出力
          if (horse.name === 'ホワイトアッシュ') {
            console.log('ホワイトアッシュのデータ:', {
              horseData: horse,
              auctionHistory: auctionHistoryByHorseId[horse.id],
              latestAuction: horse.latestAuction || (auctionHistoryByHorseId[horse.id] || [])[0]
            });
          }
          // 既存のオークション情報を保持
          const latestAuction = horse.latestAuction || (auctionHistoryByHorseId[horse.id] || [])[0];
          
          // 馬の基本情報を保持しつつ、オークション情報をマージ
          return {
            ...horse,
            latestAuction: latestAuction || null,
            latest_auction: latestAuction || null,
            // sold_price は horse オブジェクトから直接取得
            sold_price: horse.sold_price !== undefined ? horse.sold_price : (latestAuction?.sold_price || null),
            // is_unsold も horse オブジェクトから直接取得
            is_unsold: horse.is_unsold !== undefined ? horse.is_unsold : (latestAuction?.is_unsold || false),
            auction_date: latestAuction?.auction_date || horse.auction_date,
            seller: latestAuction?.seller || horse.seller,
            weight: latestAuction?.weight ?? horse.weight ?? null,
            total_prize_start: latestAuction?.total_prize_start || horse.total_prize_start,
            total_prize_latest: latestAuction?.total_prize_latest || horse.total_prize_latest,
            comment: latestAuction?.comment || horse.comment,
            race_record: horse.race_record,
            race_records: horse.race_records
          } as HorseWithCalculations;
        });

        // データを状態に保存
        setHorses(horsesWithHistory);
        setMetadata(newMetadata);
        setLoading(false);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : '不明なエラー';
        console.error('データ取得エラー:', error);
        setError(`データの取得中にエラーが発生しました: ${errorMessage}`);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }
  if (error || !horses.length) {
    return <div className="min-h-screen flex items-center justify-center text-red-600">{error || 'データがありません'}</div>;
  }

  // 表示する馬のリストをフィルタリング
  const filteredHorsesList = horses.filter(horse => {
    if (showType === 'roi') {
      return horse.roi !== undefined && horse.roi > 0;
    } else if (showType === 'value') {
      const price = horse.sold_price || 0;
      const prize = horse.total_prize_latest || 0;
      return price > 0 && prize > 0 && prize >= price * 2;
    }
    return true;
  });

  // ソート
  if (sortKey) {
    filteredHorsesList.sort((a: HorseWithCalculations, b: HorseWithCalculations) => {
      let aValue = (a as any)[sortKey];
      let bValue = (b as any)[sortKey];
      
      // 価格の特別な処理
      if (sortKey === 'sold_price') {
        // 文字列の場合はカンマを削除して数値に変換
        const parsePrice = (price: any): number => {
          if (price === null || price === undefined) return 0;
          if (typeof price === 'number') return price;
          if (typeof price === 'string') {
            // カンマを削除して数値に変換
            const cleanPrice = price.replace(/[^0-9.-]+/g, '');
            return parseFloat(cleanPrice) || 0;
          }
          return 0;
        };
        
        aValue = parsePrice(aValue);
        bValue = parsePrice(bValue);
      } else {
        // その他のフィールドの処理
        aValue = aValue || 0;
        bValue = bValue || 0;
        
        // 数値に変換
        if (typeof aValue === 'string') aValue = parseFloat(aValue) || 0;
        if (typeof bValue === 'string') bValue = parseFloat(bValue) || 0;
      }
      
      return sortOrder === 'asc' 
        ? (aValue as number) - (bValue as number)
        : (bValue as number) - (aValue as number);
    });
  }

  // サマリー - RIO計算を詳細ページと合わせる
  const avgRIO = horses.length > 0 ? (
    horses.reduce((sum, h) => {
      let soldPrice = 0;
      const price = h.sold_price;
      
      // sold_priceの型を安全に処理
      if (price !== null && price !== undefined) {
        if (typeof price === 'number') {
          soldPrice = price;
        } else if (typeof price === 'string') {
          // 文字列から数値のみを抽出
          const numStr = String(price).replace(/[^0-9]/g, '') || '0';
          soldPrice = parseInt(numStr, 10) || 0;
        }
      }
      
      const prizeStart = h.total_prize_start || 0;
      const prizeLatest = h.total_prize_latest || 0;
      
      // 落札後に稼いだ賞金総額 = 現在の総賞金 - オークション時の総賞金
      const earnedPrize = prizeLatest - prizeStart;
      
      // RIO = 落札後に稼いだ賞金総額 / 落札価格
      const rio = soldPrice > 0 ? (earnedPrize * 10000) / soldPrice : 0;
      
      return sum + (isFinite(rio) ? rio : 0);
    }, 0) / horses.length
  ) : 0;
  
  // 平均価格を計算してメタデータを更新
  if (metadata) {
    const validPrices = horses
      .map(h => {
        // 価格が数値でない場合は0として扱う
        const price = h.sold_price;
        
        // null, undefined, 空文字の場合はスキップ
        if (price === null || price === undefined) {
          return null;
        }
        
        // 数値の場合はそのまま返す
        if (typeof price === 'number') {
          return price > 0 ? price : null;
        }
        
        // 文字列の場合は数値に変換を試みる
        const strPrice = String(price).trim();
        if (!strPrice) return null;
        
        const num = parseInt(strPrice.replace(/[^0-9]/g, ''), 10);
        return isNaN(num) || num <= 0 ? null : num;
      })
      .filter((price): price is number => 
        price !== null && price > 0
      );
      
    if (validPrices.length > 0) {
      const sum = validPrices.reduce((a, b) => a + b, 0);
      const avg = Math.round(sum / validPrices.length);
      metadata.average_price = avg;
    } else {
      metadata.average_price = 0;
      // デバッグ用: 馬のデータをログに出力（より詳細に）
      console.group('馬のデータの詳細');
      horses.forEach((h, index) => {
        console.group(`馬 ${index + 1}: ${h.name} (ID: ${h.id})`);
        console.log('sold_price:', h.sold_price, 'type:', typeof h.sold_price);
        console.log('unsold:', h.unsold);
        console.log('sold_price が数値かどうか:', typeof h.sold_price === 'number');
        console.log('sold_price が0より大きいか:', h.sold_price != null && h.sold_price > 0);
        console.log('sold_price が有効な数値か:', h.sold_price != null && !isNaN(Number(h.sold_price)));
        console.log('--- 生データ ---');
        console.log(JSON.stringify(h, null, 2));
        console.groupEnd();
      });
      console.groupEnd();
      
      console.warn('有効な落札価格データがありません。以下の可能性があります：', {
        '馬の総数': horses.length,
        'sold_price が数値の馬の数': horses.filter(h => typeof h.sold_price === 'number').length,
        'sold_price が0より大きい馬の数': horses.filter(h => h.sold_price != null && h.sold_price > 0).length,
        'unsold が true の馬の数': horses.filter(h => h.unsold).length,
        'sold_price が null または undefined の馬の数': horses.filter(h => h.sold_price === null || h.sold_price === undefined).length
      });
    }
  }

  // 指標ボタン用データ
  const roiRanking = [...horses]
    .filter(h => {
      const soldPrice = h.sold_price !== null && h.sold_price !== undefined ? 
        (typeof h.sold_price === 'number' ? h.sold_price : 0) : 0;
      return soldPrice > 0 && h.total_prize_latest;
    })
    .sort((a, b) => {
      const aSoldPrice = a.sold_price !== null && a.sold_price !== undefined ? 
        (typeof a.sold_price === 'number' ? a.sold_price : 0) : 0;
      const bSoldPrice = b.sold_price !== null && b.sold_price !== undefined ? 
        (typeof b.sold_price === 'number' ? b.sold_price : 0) : 0;
      const aROI = a.total_prize_latest ? a.total_prize_latest / (aSoldPrice || 1) : 0;
      const bROI = b.total_prize_latest ? b.total_prize_latest / (bSoldPrice || 1) : 0;
      return bROI - aROI;
    })
    .slice(0, 10);

  const valueHorses = horses.filter(h => {
    const soldPrice = h.sold_price !== null && h.sold_price !== undefined ? 
      (typeof h.sold_price === 'number' ? h.sold_price : 0) : 0;
    const prizeStart = h.total_prize_start || 0;
    const prizeLatest = h.total_prize_latest || 0;
    const earnedPrize = prizeLatest - prizeStart;
    const rio = soldPrice > 0 ? earnedPrize / soldPrice : 0;
    return soldPrice > 0 && rio > avgRIO && soldPrice < (metadata?.average_price || 0);
  });

  // 表示切替
  let tableHorses: HorseWithCalculations[] = [...filteredHorsesList];

  // 年齢を表示するヘルパー関数（null/undefined/空文字の場合は'-'を表示）
  const displayAge = (age: string | number | null | undefined): string => {
    if (age === null || age === undefined || age === '') return '-';
    return `${age}歳`;
  };

  // 落札価格を表示するヘルパー関数
  const displayPrice = formatPrice;

  // 賞金を表示するヘルパー関数
  const displayPrize = (value: number | string | null | undefined): string => {
    return formatPrize(value);
  };

  // ROIを計算するヘルパー関数
  const calcROI = (prizeLatest: number | null | undefined, prizeStart: number | null | undefined, price: number | string | null | undefined): string => {
    // 賞金データがない場合は計算不可
    if (prizeLatest === undefined || prizeLatest === null || prizeStart === undefined || prizeStart === null) return '-';
    
    // 価格を数値に変換
    const numPrice = price === null || price === undefined ? 0 : (typeof price === 'string' ? parseFloat(price) : price);
    
    // 価格が無効な場合は計算不可
    if (isNaN(numPrice) || numPrice <= 0) return '-';
    
    // 落札後に稼いだ賞金総額 = 現在の総賞金 - オークション時の総賞金
    const earnedPrize = prizeLatest - prizeStart;
    
    // 落札価格が0以下の場合は計算不可
    if (numPrice <= 0) return '-';
    
    // RIO = 落札後に稼いだ賞金総額 / 落札価格
    const rio = (earnedPrize * 10000) / numPrice;
    
    // パーセンテージで返す（例: 0.15 → 15.0%）
    return (rio * 100).toFixed(1) + '%';
  };

  // ソート関数の型定義
  type SortFunction = (a: HorseWithCalculations, b: HorseWithCalculations) => number;
  const sortFunctions: Record<string, SortFunction> = {
    name: (a, b) => (a?.name ?? '').localeCompare(b?.name ?? '', 'ja'),
    sex: (a, b) => (a?.sex ?? '').localeCompare(b?.sex ?? '', 'ja'),
    weight: (a, b) => (a?.weight ?? 0) - (b?.weight ?? 0),
    age: (a, b) => {
      const ageA = typeof a?.age === 'number' ? a.age : 
                 (a?.age ? parseFloat(String(a.age)) : 0);
      const ageB = typeof b?.age === 'number' ? b.age : 
                 (b?.age ? parseFloat(String(b.age)) : 0);
      return ageA - ageB;
    },
    sire: (a, b) => (a?.sire ?? '').localeCompare(b?.sire ?? '', 'ja'),
    sold_price: (a, b) => {
      const aPrice = a?.sold_price !== null && a?.sold_price !== undefined ? 
        (typeof a.sold_price === 'number' ? a.sold_price : 0) : 0;
      const bPrice = b.sold_price !== null && b.sold_price !== undefined ? 
        (typeof b.sold_price === 'number' ? b.sold_price : 0) : 0;
      return aPrice - bPrice;
    },
    total_prize_start: (a, b) => (a.total_prize_start || 0) - (b.total_prize_start || 0),
    total_prize_latest: (a, b) => (a.total_prize_latest || 0) - (b.total_prize_latest || 0),
    roi: (a, b) => {
      const aSoldPrice = typeof a.sold_price === 'number' ? a.sold_price : 0;
      const bSoldPrice = typeof b.sold_price === 'number' ? b.sold_price : 0;
      
      // 落札後に稼いだ賞金総額 = 現在の総賞金 - オークション時の総賞金
      const aEarnedPrize = (a.total_prize_latest || 0) - (a.total_prize_start || 0);
      const bEarnedPrize = (b.total_prize_latest || 0) - (b.total_prize_start || 0);
      
      // RIO = 落札後に稼いだ賞金総額 / 落札価格
      const aROI = aSoldPrice > 0 ? aEarnedPrize / aSoldPrice : 0;
      const bROI = bSoldPrice > 0 ? bEarnedPrize / bSoldPrice : 0;
      
      return aROI - bROI;
    },
    disease_tags: (a, b) => {
      // 病歴の有無を判定する関数
      const hasDisease = (horse: HorseWithCalculations) => {
        const tags = (horse as any).disease_tags;
        if (tags === undefined || tags === null || tags === '') return false;
        if (Array.isArray(tags)) {
          if (tags.length === 0) return false;
          return !tags.every(tag => {
            const strTag = String(tag).trim();
            return strTag === '' || strTag === '-' || strTag === 'なし' || strTag === 'なし。' || strTag === '特になし' || strTag === '特になし。';
          });
        }
        const strTag = String(tags).trim();
        return !(strTag === '' || strTag === '-' || strTag === 'なし' || strTag === 'なし。' || strTag === '特になし' || strTag === '特になし。');
      };
      
      const aHasDisease = hasDisease(a) ? 1 : 0;
      const bHasDisease = hasDisease(b) ? 1 : 0;
      
      return aHasDisease - bHasDisease;
    },
  };

  if (sortKey && sortFunctions[sortKey]) {
    tableHorses = [...tableHorses].sort((a, b) => {
      const res = sortFunctions[sortKey](a, b);
      return sortOrder === 'asc' ? res : -res;
    });
  }

  // ソートハンドラー
  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('desc');
    }
  };

  // 行クリックハンドラー
  const handleRowClick = (id: string | number) => {
    router.push(`/horses/${id}`);
  };

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-8">
      <div className="max-w-7xl mx-auto">
        {/* サマリー 横並びテキスト */}
        <div className="mb-6 text-lg font-semibold text-gray-700 flex flex-wrap gap-8">
          <span>総馬数: {horses.length}</span>
          <span>平均落札価格: {formatCurrency(metadata.average_price)}</span>
          <span>平均ROI: {avgRIO.toFixed(2)}%</span>
        </div>
        {/* 指標ボタン（白文字色付き） */}
        <div className="flex gap-4 mb-6">
          <Button 
            onClick={() => setShowType('all')} 
            className={`${showType==='all' ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-400 hover:bg-blue-500'} text-white hover:text-white`}
          >
            全馬
          </Button>
          <Button 
            onClick={() => setShowType('roi')} 
            className={`${showType==='roi' ? 'bg-green-600 hover:bg-green-700' : 'bg-green-400 hover:bg-green-500'} text-white hover:text-white`}
          >
            ROIランキング
          </Button>
          <CustomButton 
            onClick={() => setShowType('value')}
            active={showType === 'value'}
          >
            妙味馬
          </CustomButton>
        </div>
        {/* DataTable風の表 */}
        <HorseTable 
          horses={horses}
          onRowClick={handleRowClick}
        />
      </div>
    </div>
  );
}
