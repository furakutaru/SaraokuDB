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

// 落札価格を表示するヘルパー関数
const formatSoldPrice = (price: number | string | null | undefined | any[], isUnsold: boolean = false, rawPrice?: any): string => {
  // デバッグ用ログは削除またはコメントアウト
  
  // 未落札フラグがtrueの場合は「主取り」を表示
  if (isUnsold) {
    return '主取り';
  }
  
  // rawPriceが存在する場合はそちらを優先
  if (rawPrice !== undefined && rawPrice !== null) {
    price = rawPrice;
  }

  // 配列の文字列表現（例: "[380000]"）を処理
  if (typeof price === 'string' && price.startsWith('[') && price.endsWith(']')) {
    try {
      const parsedArray = JSON.parse(price);
      if (Array.isArray(parsedArray) && parsedArray.length > 0) {
        price = parsedArray[0];
      }
    } catch (e) {
      console.error('Error parsing price as array:', e);
    }
  }
  
  // 配列の場合は最初の要素を使用
  if (Array.isArray(price)) {
    price = price.length > 0 ? price[0] : null;
  }

  // 価格がnullまたはundefinedまたは空文字または0の場合は「主取り」を表示
  if (price === null || price === undefined || price === '' || price === 0) {
    return '主取り';
  }

  try {
    // 文字列の場合はカンマを削除して数値に変換
    let numPrice: number;
    if (typeof price === 'string') {
      const cleanPrice = price.replace(/[^0-9.-]+/g, '');
      numPrice = parseFloat(cleanPrice);
    } else {
      numPrice = Number(price);
    }
    
    if (isNaN(numPrice) || numPrice <= 0) {
      return '-';
    }
    
    // 落札価格は「¥1,000」形式で表示
    return `¥${numPrice.toLocaleString('ja-JP')}`;
  } catch (error) {
    console.error('Error formatting price:', error);
    return '-';
  }
};

// 賞金をフォーマットするヘルパー関数（「17.5万円」形式で表示）
const formatPrize = (value: number | string | null | undefined, raceRecord?: any): string => {
  // デバッグ用のログを追加
  console.log('formatPrize - value:', value, 'raceRecord:', raceRecord);
  
  // レース成績が「データなし」または空のオブジェクト、またはレース成績がない場合は「未出走」を返す
  const isEmptyRaceRecord = 
    raceRecord === undefined || 
    raceRecord === null || 
    raceRecord === 'データなし' || 
    (raceRecord && typeof raceRecord === 'object' && Object.keys(raceRecord).length === 0) ||
    (raceRecord && typeof raceRecord === 'object' && raceRecord.formatted_record === 'データなし') ||
    (raceRecord && typeof raceRecord === 'object' && raceRecord.total_races === 0) ||
    (raceRecord && typeof raceRecord === 'object' && 
     !('total_races' in raceRecord) && 
     !('formatted_record' in raceRecord) && 
     !('wins' in raceRecord)) ||
    (raceRecord && typeof raceRecord === 'object' && raceRecord.record_format === 'simple' && raceRecord.total_races === 0);

  if (isEmptyRaceRecord) {
    console.log('formatPrize - 未出走と判定');
    return '未出走';
  }
  
  if (value === null || value === undefined || value === '') return '-';
  
  // 数値に変換
  const numValue = Number(value);
  
  if (isNaN(numValue) || numValue <= 0) return '-';
  
  // 1万円未満の場合はそのまま表示
  if (numValue < 10000) {
    return `${numValue.toLocaleString('ja-JP')}円`;
  }
  
  // 1万円以上の場合は「X.XX万円」形式で表示
  const manValue = numValue / 10000;
  // 小数点以下1桁まで表示（例: 17.5万円）
  const formattedValue = manValue % 1 === 0 ? manValue.toFixed(0) : manValue.toFixed(1);
  return `${formattedValue}万円`;
};

// normalize.ts から formatSex と getSexColor をインポート
import { formatSex, getSexColor } from '@/utils/normalize';

// 通貨フォーマットのエイリアス
const formatPrice = formatCurrency;

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

import { FaSort, FaSortUp, FaSortDown } from 'react-icons/fa';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Horse, AuctionHistory, HorseWithCalculations } from '@/types/horse';

// フロントエンドで使用する馬の型（Horse型を拡張）
interface HorseWithAuction extends Horse {
  dam_sire: string; // damsireのエイリアス
  detail_url: string; // auction_urlのエイリアス
  comment?: string; // コメント
  // Horse インターフェースに weight と disease_tags を追加したので、ここでは不要
  // オークション情報（将来的な機能拡張用）
  latestAuction?: AuctionHistory;
  total_prize_start?: number;
  total_prize_latest?: number;
  is_unsold?: boolean;
  auction_date?: string;
  seller?: string;
  // Horseインターフェースのプロパティをオーバーライド
  sold_price?: number | null;
  race_record?: string;
  race_records?: any;  // より具体的な型に置き換えることが望ましい
  // その他のプロパティ
  [key: string]: any; // 動的なプロパティに対応
}

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
  const [horses, setHorses] = useState<HorseWithAuction[]>([]);
  const [auctionHistory, setAuctionHistory] = useState<AuctionHistory[]>([]);
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
        
        // 1回のAPI呼び出しでデータを取得
        const response = await fetch(`${apiBaseUrl}/api/horses`, { 
          cache: 'no-store' 
        });

        if (!response.ok) {
          throw new Error('データの取得に失敗しました');
        }

        const data = await response.json();
        
        // Horse型からHorseWithAuction型に変換
        const horsesWithAuction = data.horses.map((horse: any) => ({
          ...horse,
          dam_sire: horse.dam_sire || '',
          detail_url: horse.detail_url || '',
          comment: horse.comment,
          race_record: horse.race_record,
          race_records: horse.race_records
        }));
        
        setHorses(horsesWithAuction);
        setAuctionHistory(data.auction_histories || []);
        
        // メタデータを更新
        const newMetadata = {
          total: data.metadata?.total || 0,
          count: data.metadata?.count || 0,
          total_auctions: data.metadata?.total_auctions,
          average_price: data.metadata?.average_price,
          last_updated: data.metadata?.last_updated,
          total_horses: data.metadata?.total_horses || data.metadata?.total || 0
        };
        
        setMetadata(newMetadata);

        // オークション履歴を馬IDでグループ化
        const auctionHistoryByHorseId = groupAuctionHistory(data.auction_histories || []);
        
        // 馬データにオークション情報をマージ
        const horsesWithHistory = horsesWithAuction.map((horse: HorseWithAuction) => {
          // 既存のオークション情報を保持
          const latestAuction = horse.latestAuction || (auctionHistoryByHorseId[horse.id] || [])[0];
          
          // 馬の基本情報を保持しつつ、オークション情報をマージ
          return {
            ...horse,
            latestAuction: latestAuction || null,
            latest_auction: latestAuction || null,
            sold_price: latestAuction?.sold_price || null,
            is_unsold: latestAuction?.is_unsold || false,
            auction_date: latestAuction?.auction_date || horse.auction_date,
            seller: latestAuction?.seller || horse.seller,
            weight: latestAuction?.weight ?? horse.weight ?? null,
            total_prize_start: latestAuction?.total_prize_start || horse.total_prize_start,
            total_prize_latest: latestAuction?.total_prize_latest || horse.total_prize_latest,
            comment: latestAuction?.comment || horse.comment,
            race_record: horse.race_record,
            race_records: horse.race_records
          } as HorseWithAuction;
        });

        // データを状態に保存
        setHorses(horsesWithHistory);
        setAuctionHistory(data.auction_histories);
        setMetadata(newMetadata);
        setLoading(false);
      } catch (e: any) {
        console.error('データ取得エラー:', e);
        setError('データの読み込みに失敗しました: ' + e.message);
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
  const filteredHorses = horses.filter(horse => {
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
    filteredHorses.sort((a: Horse, b: Horse) => {
      let aValue = (a as any)[sortKey] || 0;
      let bValue = (b as any)[sortKey] || 0;
      
      // 数値に変換
      if (typeof aValue === 'string') aValue = parseFloat(aValue) || 0;
      if (typeof bValue === 'string') bValue = parseFloat(bValue) || 0;
      
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
  let tableHorses: Horse[] = [...filteredHorses];

  // 年齢を表示するヘルパー関数（null/undefined/空文字の場合は'-'を表示）
  const displayAge = (age: string | number | null | undefined): string => {
    if (age === null || age === undefined || age === '') return '-';
    return `${age}歳`;
  };

  // 落札価格を表示するヘルパー関数
  const displayPrice = formatSoldPrice;

  // 賞金を表示するヘルパー関数
  const displayPrize = formatPrize;

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
  type SortFunction = (a: Horse, b: Horse) => number;
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

  // ソートアイコン
  const renderSortIcon = (key: string) => {
    if (sortKey !== key) return <FaSort className="inline ml-1 text-gray-400" />;
    return sortOrder === 'asc' ? <FaSortUp className="inline ml-1 text-blue-600" /> : <FaSortDown className="inline ml-1 text-blue-600" />;
  };

  // 詳細ページのURLを安全に取得するヘルパー関数
  const getDetailUrl = (horse: Horse): string | undefined => {
    // detail_url または auction_url のいずれかが存在する場合に返す
    return (horse as any).detail_url || (horse as any).auction_url || undefined;
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
        <div className="overflow-x-auto bg-white rounded-lg shadow w-full">
          <table className="min-w-full divide-y divide-gray-200 w-full">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('name')}>馬名{renderSortIcon('name')}</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('sex')}>性別{renderSortIcon('sex')}</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('age')}>年齢{renderSortIcon('age')}</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('sire')}>父{renderSortIcon('sire')}</th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('weight')}>馬体重 (kg){renderSortIcon('weight')}</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('sold_price')}>落札価格{renderSortIcon('sold_price')}</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('total_prize_start')}>落札時賞金{renderSortIcon('total_prize_start')}</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('total_prize_latest')}>現在賞金{renderSortIcon('total_prize_latest')}</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('roi')}>ROI{renderSortIcon('roi')}</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-gray-500 uppercase">リンク</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-gray-500 uppercase w-24">病歴</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {tableHorses.map((horse) => (
                <tr key={horse.id} className="hover:bg-blue-50">
                  <td className="px-3 py-2 font-medium text-gray-900 whitespace-nowrap">
                    <Link href={`/horses/${horse.id}`} className="hover:underline text-blue-700 whitespace-nowrap">{horse.name}</Link>
                  </td>
                  <td className="px-3 py-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium text-white ${getSexColor(horse.sex)}`}>
                      {formatSex(horse.sex)}
                    </span>
                  </td>
                  <td className="px-3 py-2">{displayAge(horse.age)}</td>
                  <td className="px-3 py-2">{horse.sire || '-'}</td>
                  <td className="px-3 py-2 text-right">
                    {(() => {
                      // 体重データの処理
                      const weight = horse.weight as string | number | null | undefined;
                      
                      // 値が存在しないか無効な場合
                      if (weight === null || weight === undefined || weight === '') {
                        return '-';
                      }
                      
                      // 数値に変換を試みる
                      const weightStr = String(weight);
                      const numWeight = parseFloat(weightStr.replace(/[^0-9.]/g, ''));
                      
                      // 有効な数値の場合、整数に丸めて表示
                      if (!isNaN(numWeight) && isFinite(numWeight)) {
                        return `${Math.round(numWeight)} kg`;
                      }
                      
                      // 文字列として有効な場合
                      const trimmedWeight = weightStr.trim();
                      if (trimmedWeight !== '') {
                        // 「kg」が含まれていない場合は追加
                        return trimmedWeight.toLowerCase().includes('kg') ? trimmedWeight : `${trimmedWeight} kg`;
                      }
                      
                      // その他の場合はハイフンを表示
                      return '-';
                    })()}
                  </td>
                  <td className="px-3 py-2">
                    {formatSoldPrice(horse.sold_price, horse.is_unsold || false, (horse as any).sold_price_raw || (horse as any).raw_sold_price)}
                  </td>
                  <td className="px-3 py-2">
                    {(() => {
                      const raceRecord = (horse as HorseWithAuction).race_record || (horse as HorseWithAuction).race_records;
                      console.log('Debug - raceRecord:', raceRecord, 'total_prize_start:', horse.total_prize_start);
                      return formatPrize(horse.total_prize_start, raceRecord);
                    })()}
                  </td>
                  <td className="px-3 py-2">
                    {(() => {
                      const raceRecord = (horse as HorseWithAuction).race_record || (horse as HorseWithAuction).race_records;
                      return formatPrize(horse.total_prize_latest, raceRecord);
                    })()}
                  </td>
                  <td className="px-3 py-2">
                    {calcROI(horse.total_prize_latest, horse.total_prize_start, horse.sold_price)}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex flex-col gap-1 items-center">
                      {horse.jbis_url && (
                        <a href={horse.jbis_url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 underline whitespace-nowrap">JBIS</a>
                      )}
                      {getDetailUrl(horse) && (
                        <a href={getDetailUrl(horse)} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 underline whitespace-nowrap">サラオク</a>
                      )}
                    </div>
                  </td>
                  <td className="px-3 py-2 text-center">
                    {(() => {
                      // 病歴が「なし」の馬を判定
                      const isNoDisease = (tags: any) => {
                        if (tags === undefined || tags === null || tags === '') return true;
                        if (Array.isArray(tags)) {
                          if (tags.length === 0) return true;
                          return tags.every(tag => {
                            const strTag = String(tag).trim();
                            return strTag === '' || strTag === '-' || strTag === 'なし' || strTag === 'なし。' || strTag === '特になし' || strTag === '特になし。';
                          });
                        }
                        const strTag = String(tags).trim();
                        return strTag === '' || strTag === '-' || strTag === 'なし' || strTag === 'なし。' || strTag === '特になし' || strTag === '特になし。';
                      };
                      
                      // 病歴が「なし」の場合は青で表示、それ以外はピンクで「あり」と表示
                      return isNoDisease((horse as Horse & { disease_tags?: any[] }).disease_tags) ? (
                        <span className="text-xs font-medium bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full whitespace-nowrap inline-block w-12">
                          なし
                        </span>
                      ) : (
                        <span className="text-xs font-medium bg-pink-100 text-pink-800 px-2 py-0.5 rounded-full whitespace-nowrap inline-block w-12">
                          あり
                        </span>
                      );
                    })()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
