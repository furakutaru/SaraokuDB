'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import HorseImage from '@/components/HorseImage';
import HorseCard from '@/components/HorseCard';
import { useRouter } from 'next/navigation';
import { Horse as BaseHorse, AuctionHistory, HorseData, HorseWithCalculations } from '@/types/horse';

// コンポーネントで使用する馬の型を定義
export interface Horse {
  // 基本情報
  id: string | number;
  name?: string;
  auction_id?: string;
  sex: string;
  age?: number;
  sire: string;
  dam: string;
  damsire: string;
  weight?: number | null;
  image_url: string | { image_url: string };
  jbis_url?: string;
  detail_url?: string;
  created_at?: string;
  updated_at?: string;
  birth_year?: number;
  color?: string;
  breeder?: string;
  owner?: string;
  trainer?: string;
  location?: string;
  sold_price?: number | null;
  is_unsold?: boolean;
  seller?: string;
  
  // オークション関連
  auction_history?: AuctionHistory[];
  auction_date?: string | string[];
  
  // 計算済みプロパティ
  total_prize_start?: number;
  total_prize_latest?: number;
  unsold_count?: number;
  roi?: number;
  price_per_kg?: number;
  primary_image?: string;
  display_price?: string;
  display_weight?: string;
  display_prize?: string;
  display_roi?: string;
  sort_price?: number;
  sort_prize?: number;
  sort_roi?: number;
  prize_money?: { total_prize: string };
  effectiveWeight?: number | null;
  auction_url?: string;
  unsold?: boolean;
  price?: number | null;
  race_records?: {
    total_prize_money: number;
    last_race_date?: string;
    last_prize_update?: string;
  };
  latest_auction?: AuctionHistory | null;
}

import { Header } from '@/components/Header';

export default function HorsesPage() {
  const router = useRouter();
  const [horses, setHorses] = useState<Horse[]>([]);
  const [auctionHistory, setAuctionHistory] = useState<AuctionHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'price' | 'age'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [showOnlyLatestAuction, setShowOnlyLatestAuction] = useState(true);
  const [latestAuctionDate, setLatestAuctionDate] = useState<string | null>(null);

  // 日付をパースするヘルパー関数 (useCallbackでメモ化)
  const parseDate = useCallback((date: string | string[] | undefined): Date => {
    try {
      if (!date) return new Date(0);
      const dateStr = Array.isArray(date) ? date[0] : date;
      if (!dateStr) return new Date(0);
      return new Date(dateStr);
    } catch (error) {
      console.error('日付のパースに失敗しました:', { date, error });
      return new Date(0);
    }
  }, []);

  // 馬データを取得
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // 統一された馬データを取得
        const response = await fetch('/data/horses_combined.json');
        
        if (!response.ok) {
          throw new Error('データの取得に失敗しました');
        }

        const data: HorseData = await response.json();
        
        // メタデータから最新のオークション日を取得
        if (data.metadata) {
          setLatestAuctionDate(data.metadata.last_updated);
        }
        
        // 馬データを取得して整形
        const processedHorses = (data.horses || []).map(horse => {
          // 最新のオークション情報を取得
          const latestAuction = horse.auction_history && Array.isArray(horse.auction_history) && horse.auction_history.length > 0
            ? [...horse.auction_history].sort((a, b) => 
                parseDate(b.auction_date).getTime() - parseDate(a.auction_date).getTime()
              )[0]
            : null;
          
          // 互換性のためのプロパティを追加
          return {
            ...horse,
            // 基本情報
            name: horse.basic_info?.name || '',
            sex: horse.basic_info?.sex || '',
            age: horse.basic_info?.age || 0,
            sire: horse.basic_info?.sire || '',
            dam: horse.basic_info?.dam || '',
            damsire: horse.basic_info?.damsire || '',
            // オークション情報
            latest_auction: latestAuction,
            sold_price: latestAuction?.sold_price || latestAuction?.price || null,
            auction_date: latestAuction?.auction_date || '',
            seller: latestAuction?.seller || '',
            is_unsold: latestAuction?.is_unsold || false,
            // レコード情報
            race_records: horse.race_records || { total_prize_money: 0 }
          };
        });

        setHorses(processedHorses);
        setError(null);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('データの読み込み中にエラーが発生しました');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [parseDate]);

  // フィルタリングとソートを適用した馬のリストを取得
  const filteredHorses = horses.filter(horse => {
    // 検索条件に一致するか確認
    const searchLower = searchTerm.toLowerCase();
    const matchesSearch = !searchTerm || 
      (horse.name && horse.name.toLowerCase().includes(searchLower)) ||
      (horse.sire && horse.sire.toLowerCase().includes(searchLower)) ||
      (horse.dam && horse.dam.toLowerCase().includes(searchLower)) ||
      (horse.damsire && horse.damsire.toLowerCase().includes(searchLower));
    
    // 最新のオークションのみ表示する場合
    if (showOnlyLatestAuction && latestAuctionDate) {
      return matchesSearch && horse.auction_date === latestAuctionDate.split('T')[0];
    }
    
    return matchesSearch;
  });

  const sortedHorses = [...filteredHorses].sort((a, b) => {
    let valueA: any, valueB: any;
    
    switch (sortBy) {
      case 'name':
        valueA = a.name;
        valueB = b.name;
        break;
      case 'price':
        valueA = a.sold_price || 0;
        valueB = b.sold_price || 0;
        break;
      case 'age':
        valueA = a.age;
        valueB = b.age;
        break;
      default:
        return 0;
    }
    
    if (valueA < valueB) {
      return sortOrder === 'asc' ? -1 : 1;
    }
    if (valueA > valueB) {
      return sortOrder === 'asc' ? 1 : -1;
    }
    return 0;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header pageTitle="読み込み中..." />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center py-12">
            <p className="text-gray-600">データを読み込んでいます...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header pageTitle="エラー" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-red-50 border-l-4 border-red-400 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header pageTitle="直近追加の馬" />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {latestAuctionDate && (
          <div className="mb-8">
            <p className="text-sm text-gray-600">
              オークションの日付: {new Date(latestAuctionDate).toLocaleDateString('ja-JP', {year: 'numeric', month: 'long', day: 'numeric', weekday: 'short'})} | {sortedHorses.length}頭
            </p>
          </div>
        )}
        
        {/* 検索とフィルター */}
        <div className="mb-6">
          <div className="flex flex-col md:flex-row gap-4 mb-4">
            <input
              type="text"
              placeholder="馬名・血統で検索..."
              className="flex-1 p-2 border rounded"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <div className="flex gap-2">
              <select 
                className="p-2 border rounded"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'name' | 'price' | 'age')}
              >
                <option value="name">名前順</option>
                <option value="price">価格順</option>
                <option value="age">年齢順</option>
              </select>
              <button 
                className="p-2 border rounded"
                onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
              >
                {sortOrder === 'asc' ? '↑' : '↓'}
              </button>
            </div>
          </div>
          
          {latestAuctionDate && (
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">
                {showOnlyLatestAuction 
                  ? `最新オークション: ${new Date(latestAuctionDate).toLocaleDateString()}`
                  : '全オークションを表示中'}
              </span>
              <button
                onClick={() => setShowOnlyLatestAuction(!showOnlyLatestAuction)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                  showOnlyLatestAuction ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`${
                    showOnlyLatestAuction ? 'translate-x-6' : 'translate-x-1'
                  } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
                />
              </button>
              <span className="text-sm text-gray-600">
                {showOnlyLatestAuction ? '最新のみ' : '全期間'}
              </span>
            </div>
          )}
        </div>
        
        {/* 馬のグリッド表示 */}
        <div className="mt-8">
          {sortedHorses.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600">条件に一致する馬が見つかりませんでした</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {sortedHorses.map((horse: Horse) => {
                // Horse を HorseWithCalculations に変換
                const horseWithCalculations = {
                  ...horse,
                  // HorseWithCalculations の必須プロパティにデフォルト値を設定
                  total_prize_start: 0,
                  unsold_count: 0,
                  roi: 0,
                  price_per_kg: 0,
                  primary_image: typeof horse.image_url === 'string' ? horse.image_url : horse.image_url?.image_url || '',
                  display_price: '',
                  display_weight: '',
                  display_prize: '',
                  display_roi: '',
                  sort_price: 0,
                  sort_prize: 0,
                  sort_roi: 0,
                  auction_history: horse.auction_history || [],
                  // auction_date の型を明示的に変換
                  auction_date: Array.isArray(horse.auction_date) ? horse.auction_date[0] : horse.auction_date
                } as HorseWithCalculations;
                
                return (
                <div key={horse.id} onClick={() => router.push(`/horses/${horse.id}`)}>
                  <HorseCard 
                    horse={horseWithCalculations} 
                    auctionHistory={horse.auction_history || []}
                    onClick={() => router.push(`/horses/${horse.id}`)}
                  />
                </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
