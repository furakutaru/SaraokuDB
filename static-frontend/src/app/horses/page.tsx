'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import HorseImage from '@/components/HorseImage';
import HorseCard from '../../components/HorseCard';
import { useRouter } from 'next/navigation';
import { Horse as HorseType, AuctionHistory } from '@/types/horse';

// 馬データの型定義
interface Horse extends HorseType {
  // 最新のオークション情報をフラット化したフィールド
  latest_auction?: {
    auction_date: string;
    sold_price: number | null;
    seller: string;
    weight: number | null;
    total_prize_start: number;
    total_prize_latest: number;
    is_unsold: boolean;
  };
  // 表示用の追加フィールド
  display_name?: string;
  display_age?: string | number;
  display_sex?: string;
  display_sold_price?: string | number | null;
  display_total_prize?: string | number;
}

// メタデータの型定義
interface Metadata {
  last_updated: string;
  total_horses: number;
  average_price?: number | null;
  description?: string;
  version?: string;
  data_source?: string;
  generated_at?: string;
}

// 馬データ全体の型定義
interface HorseData {
  metadata: Metadata;
  horses: Horse[];
  auction_history?: AuctionHistory[];
}

// 最新のオークション情報を取得するヘルパー関数
const getLatestAuction = (horse: HorseType, auctionHistory: AuctionHistory[]) => {
  // この馬のオークション履歴を取得
  const horseAuctions = auctionHistory.filter(ah => ah.horse_id === horse.id);
  
  // 日付でソート（新しい順）
  const sortedAuctions = [...horseAuctions].sort((a, b) => 
    new Date(b.auction_date).getTime() - new Date(a.auction_date).getTime()
  );
  
  // 最新のオークション情報を返す
  return sortedAuctions.length > 0 ? sortedAuctions[0] : null;
};

export default function HorsesPage() {
  const router = useRouter();
  const [data, setData] = useState<HorseData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [sortBy, setSortBy] = useState<'name' | 'price' | 'age'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  useEffect(() => {
    // ページタイトルを設定
    document.title = 'サラオクDB | 直近の追加';
    
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // 馬データとオークションデータを並列で取得
        const [horsesRes, auctionRes] = await Promise.all([
          fetch('/data/horses.json'),
          fetch('/data/auction_history.json')
        ]);
        
        if (!horsesRes.ok || !auctionRes.ok) {
          throw new Error('データの取得に失敗しました');
        }
        
        const horsesData = await horsesRes.json();
        const auctionData = await auctionRes.json();
        
        console.log('馬データの取得に成功:', horsesData.horses.length, '件');
        console.log('オークションデータの取得に成功:', auctionData.length, '件');
        
        // データをマッピングして型に合わせる
        const mappedHorses: Horse[] = horsesData.horses.map((horse: HorseType) => {
          // 最新のオークション情報を取得
          const latestAuction = getLatestAuction(horse, auctionData);
          
          return {
            ...horse,
            latest_auction: latestAuction ? {
              auction_date: latestAuction.auction_date,
              sold_price: latestAuction.sold_price,
              seller: latestAuction.seller,
              weight: latestAuction.weight,
              total_prize_start: latestAuction.total_prize_start,
              total_prize_latest: latestAuction.total_prize_latest,
              is_unsold: latestAuction.is_unsold
            } : undefined,
            // 表示用のフィールド
            display_name: horse.name || '名前不明',
            display_age: horse.age,
            display_sex: horse.sex,
            display_sold_price: latestAuction?.sold_price || null,
            display_total_prize: latestAuction?.total_prize_latest || 0
          };
        });
        
        // メタデータを準備
        const metadata: Metadata = {
          ...horsesData.metadata,
          total_horses: mappedHorses.length,
          last_updated: new Date().toISOString()
        };
        
        setData({
          metadata,
          horses: mappedHorses,
          auction_history: auctionData
        });
        
      } catch (err) {
        console.error('データの読み込み中にエラーが発生しました:', err);
        setError('データの読み込みに失敗しました');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">エラーが発生しました: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="container mx-auto p-4">
        <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">データがありません</strong>
          <span className="block sm:inline">表示するデータが存在しません。</span>
        </div>
      </div>
    );
  }

  // 履歴から最新の有効な価格を取得する関数
  const findLatestValidPrice = (history: AuctionHistory[] = []) => {
    if (!history || history.length === 0) return null;
    
    // 日付の新しい順にソート
    const sortedHistory = [...history].sort((a, b) => {
      const dateA = a.auction_date ? new Date(a.auction_date).getTime() : 0;
      const dateB = b.auction_date ? new Date(b.auction_date).getTime() : 0;
      return dateB - dateA;
    });
    
    // 有効な価格（数値で0より大きい）を見つける
    const validHistory = sortedHistory.find(item => {
      const price = item.sold_price;
      return price !== null && price !== undefined && price > 0;
    });
    
    return validHistory?.sold_price ?? null;
  };

  // 馬データを処理
  const horsesWithLatest = data?.horses?.map((horse: Horse & { sold_price?: number | null; auction_date?: string; seller?: string }) => {
    console.log(`Processing horse: ${horse.id} - ${horse.name}`);
    
    // 履歴から有効な価格を検索
    const validPrice = findLatestValidPrice(horse.history || []);
    const horsePrice = horse.latest_auction?.sold_price !== null && 
                      horse.latest_auction?.sold_price !== undefined && 
                      !isNaN(Number(horse.latest_auction.sold_price)) &&
                      Number(horse.latest_auction.sold_price) > 0
                      ? Number(horse.latest_auction.sold_price)
                      : null;
    
    console.log(`  Found valid price in history:`, validPrice);
    console.log(`  Horse price:`, horsePrice);
    
    // 最新の履歴を取得（日付の新しい順にソート）
    const latestHistory: { auction_date?: string; seller?: string } = horse.history && horse.history.length > 0 
      ? [...horse.history].sort((a, b) => {
          const dateA = a.auction_date ? new Date(a.auction_date).getTime() : 0;
          const dateB = b.auction_date ? new Date(b.auction_date).getTime() : 0;
          return dateB - dateA;
        })[0]
      : {};
    
    // マージしたデータを返す
    const mergedData: Horse & { sold_price?: number | null; auction_date?: string; seller?: string } = {
      ...horse,
      // 有効な価格があればそれを使用、なければ馬データの価格を使用
      sold_price: validPrice !== null ? validPrice : horsePrice,
      // 日付は最新の履歴があればそれを使用
      auction_date: latestHistory?.auction_date,
      // 売り主情報
      seller: latestHistory?.seller,
      // 型エラーを防ぐために明示的に型を設定
      id: horse.id,
      name: horse.name || 'Unknown',
      sex: horse.sex || 'Unknown',
      age: horse.age || 0
    };
    
    console.log('Merged data:', mergedData);
    return mergedData;
  }) || [];

  // 検索とソートを適用した馬のリストを取得
  const filteredHorses = (horsesWithLatest as (Horse & { sold_price: number | null })[])
    .filter((horse) => {
      if (!searchTerm) return true;
      
      const term = searchTerm.toLowerCase();
      return (
        (horse.name || '').toLowerCase().includes(term) ||
        (horse.sire || '').toLowerCase().includes(term) ||
        (horse.dam || '').toLowerCase().includes(term) ||
        (horse.damsire || '').toLowerCase().includes(term) ||
        (horse.latest_auction?.seller || '').toLowerCase().includes(term) ||
        (horse.latest_auction?.auction_date || '').includes(term) ||
        (horse.latest_auction?.sold_price && horse.latest_auction.sold_price.toString().includes(term))
      );
    })
    .sort((a, b) => {
      let comparison = 0;
      switch (sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'price':
          const priceA = a.latest_auction?.sold_price || 0;
          const priceB = b.latest_auction?.sold_price || 0;
          comparison = (typeof priceA === 'number' ? priceA : 0) - (typeof priceB === 'number' ? priceB : 0);
          break;
        case 'age':
          const ageA = typeof a.age === 'number' ? a.age : parseInt(String(a.age || 0), 10);
          const ageB = typeof b.age === 'number' ? b.age : parseInt(String(b.age || 0), 10);
          comparison = ageA - ageB;
          break;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });

  // 落札価格表示用関数
  // 落札価格は取得値そのまま（円単位）で表示すること。データは既に円単位で格納されている。
  const displayPrice = (price: number | null | undefined, unsold: boolean | undefined) => {
    if (unsold === true) return '主取り';
    if (price === null || price === undefined) return '-';
    return '¥' + price.toLocaleString();
  };

  const getGrowthRate = (start: number, latest: number) => {
    if (start === 0) return '0.0';
    return ((latest - start) / start * 100).toFixed(1);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <button
              onClick={() => router.back()}
              className="rounded-md bg-white border border-black text-black px-4 py-2 hover:bg-gray-100 transition-colors"
            >
              <svg className="w-5 h-5 mr-2 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
              戻る
            </button>
            <div className="flex gap-4">
              <Link href="/">
                <Button variant="outline" className="rounded-md bg-white border border-black text-black hover:bg-gray-100">解析</Button>
              </Link>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 items-center justify-between py-4">
            <div className="w-full sm:w-96">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <input
                  type="text"
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="馬名・父・母・母父・生産者・落札価格など"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>

            <div className="flex gap-2 w-full sm:w-auto">
              <select
                className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'name' | 'price' | 'age')}
              >
                <option value="name">馬名順</option>
                <option value="price">落札価格順</option>
                <option value="age">年齢順</option>
              </select>

              <button
                type="button"
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              >
                {sortOrder === 'asc' ? '↑' : '↓'}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* 馬一覧 */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filteredHorses.length > 0 ? (
            filteredHorses.map((horse: Horse & { sold_price: number | null }) => (
              <HorseCard
                key={horse.id}
                horse={horse}
                onClick={() => router.push(`/horses/${horse.id}`)}
              />
            ))
          ) : (
            <div className="col-span-full text-center py-12">
              <p className="text-gray-500">条件に一致する馬が見つかりませんでした</p>
              <button
                onClick={() => {
                  setSearchTerm('');
                  setSortBy('name');
                  setSortOrder('asc');
                }}
                className="mt-2 text-blue-600 hover:text-blue-800"
              >
                検索条件をリセット
              </button>
            </div>
          )}
        </div>

        {/* 結果件数 */}
        <div className="mt-8 text-center text-gray-600">
          {filteredHorses.length}頭の馬を表示中
        </div>
      </main>
    </div>
  );
}