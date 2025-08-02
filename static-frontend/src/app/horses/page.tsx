'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import HorseImage from '@/components/HorseImage';
import HorseCard from '@/components/HorseCard';
import { useRouter } from 'next/navigation';
import { Horse as HorseType, AuctionHistory } from '@/types/horse';
import { Header } from '@/components/Header';

export default function HorsesPage() {
  const [horses, setHorses] = useState<HorseType[]>([]);
  const [auctionHistory, setAuctionHistory] = useState<AuctionHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'price' | 'age'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [showOnlyLatestAuction, setShowOnlyLatestAuction] = useState(true);
  const [latestAuctionDate, setLatestAuctionDate] = useState<string | null>(null);

  // 馬データを取得
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // 馬データを取得
        const [horsesRes, historyRes] = await Promise.all([
          fetch('/data/horses.json'),
          fetch('/data/auction_history.json')
        ]);

        if (!horsesRes.ok || !historyRes.ok) {
          throw new Error('データの取得に失敗しました');
        }

        const horsesJson = await horsesRes.json();
        const historyJson = await historyRes.json();

        // 馬データを抽出（horses.jsonの構造に応じて）
        const horsesData = (
          (horsesJson && horsesJson.horses) || 
          (Array.isArray(horsesJson) && horsesJson) ||
          []
        ).filter(Boolean); // null/undefinedを除外

        // オークションデータを抽出
        const historyData = (
          (historyJson && historyJson.history) ||
          (historyJson && historyJson.data) ||
          (Array.isArray(historyJson) && historyJson) ||
          []
        ).filter(Boolean);

        // 最新のオークション日付を取得
        if (historyData.length > 0) {
          const latestDate = historyData.reduce((latest: string, item: any) => {
            const date = item.auction_date || item.date || '';
            return date > latest ? date : latest;
          }, '');
          setLatestAuctionDate(latestDate);
        }
        
        console.log('Loaded horses:', horsesData);
        console.log('Loaded history:', historyData);
        
        setHorses(horsesData);
        setAuctionHistory(historyData);
        setError(null);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('データの読み込み中にエラーが発生しました');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // フィルタリングとソートを適用した馬のリストを取得
  const filteredAndSortedHorses = (Array.isArray(horses) ? horses : [])
    .filter(horse => {
      if (!horse) return false;
      
      // 検索条件に一致するか
      const searchLower = searchTerm.toLowerCase();
      const matchesSearch = !searchTerm || 
        (horse.name && horse.name.toLowerCase().includes(searchLower)) ||
        (horse.sire && horse.sire.toLowerCase().includes(searchLower)) ||
        (horse.dam && horse.dam.toLowerCase().includes(searchLower)) ||
        (horse.damsire && horse.damsire.toLowerCase().includes(searchLower));

      // 最新のオークションのみ表示する場合
      const isLatestAuction = !showOnlyLatestAuction || 
        !latestAuctionDate ||  // latestAuctionDateがnullの場合は全件表示
        (horse.auction_date && horse.auction_date === latestAuctionDate) ||
        (horse.latest_auction && horse.latest_auction.auction_date === latestAuctionDate) ||
        (auctionHistory.some(auction => 
          auction.horse_id === horse.id && 
          auction.auction_date === latestAuctionDate
        ));

      return matchesSearch && isLatestAuction;
    })
    .sort((a, b) => {
      // ソート順を決定
      let comparison = 0;
      
      if (sortBy === 'name') {
        comparison = (a.name || '').localeCompare(b.name || '');
      } else if (sortBy === 'price') {
        const priceA = a.latest_auction?.sold_price || 0;
        const priceB = b.latest_auction?.sold_price || 0;
        comparison = priceA - priceB;
      } else if (sortBy === 'age') {
        const ageA = typeof a.age === 'number' ? a.age : (typeof a.age === 'string' ? parseInt(a.age, 10) : 0);
        const ageB = typeof b.age === 'number' ? b.age : (typeof b.age === 'string' ? parseInt(b.age, 10) : 0);
        comparison = (ageA || 0) - (ageB || 0);
      }
      
      // 降順の場合は反転
      return sortOrder === 'desc' ? -comparison : comparison;
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
        <div className="mb-8">
          <p className="text-sm text-gray-600">
            最新のオークションに出品された馬の一覧です
          </p>
        </div>
        
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
        {filteredAndSortedHorses.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredAndSortedHorses.map((horse) => (
              <HorseCard
                key={horse.id}
                horse={horse}
                auctionHistory={auctionHistory}
                onClick={() => window.location.href = `/horses/${horse.id}`}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-600">条件に一致する馬が見つかりませんでした</p>
          </div>
        )}
      </div>
    </div>
  );
}
