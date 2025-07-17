'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import HorseImage from '@/components/HorseImage';

interface Horse {
  id: number;
  name: string;
  sex: string;
  age: number;
  sold_price: number;
  seller: string;
  total_prize_start: number;
  total_prize_latest: number;
  sire: string;
  dam: string;
  dam_sire: string;
  comment: string;
  weight: number;
  race_record: string;
  primary_image: string;
  auction_date: string;
  disease_tags: string;
  netkeiba_url: string;
  created_at: string;
  updated_at: string;
}

interface Metadata {
  last_updated: string;
  total_horses: number;
  average_price: number;
  average_growth_rate: number;
  horses_with_growth_data: number;
  next_auction_date: string;
}

interface HorseData {
  metadata: Metadata;
  horses: Horse[];
}

export default function HorsesPage() {
  const [data, setData] = useState<HorseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'price' | 'age'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      // horses.jsonから馬データを取得
      const response = await fetch('/data/horses.json');
      if (!response.ok) {
        throw new Error('データの取得に失敗しました');
      }
      const data = await response.json();
      setData(data);
    } catch (err) {
      setError('データの読み込みに失敗しました');
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">データを読み込み中...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600 mb-4">エラー</h2>
          <p className="text-gray-600 mb-4">{error || 'データが見つかりません'}</p>
          <Button onClick={fetchData} className="bg-blue-600 hover:bg-blue-700">
            再試行
          </Button>
        </div>
      </div>
    );
  }

  const { horses } = data;

  // 検索とソート
  const filteredHorses = horses
    .filter(horse => 
      horse.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (horse.sire || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (horse.dam || '').toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      let comparison = 0;
      switch (sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'price':
          comparison = (a.sold_price || 0) - (b.sold_price || 0);
          break;
        case 'age':
          comparison = a.age - b.age;
          break;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });

  // 賞金表示用関数を追加
  const formatPrize = (val: number | null | undefined) => {
    if (val === null || val === undefined) return '-';
    return `${(val / 10000).toFixed(1)}万円`;
  };

  // 落札価格表示用関数を追加
  const formatPrice = (price: number | null | undefined) => {
    if (price === null || price === undefined) return '-';
    return '¥' + price.toLocaleString();
  };

  const getGrowthRate = (start: number, latest: number) => {
    if (start === 0) return '0';
    return ((latest - start) / start * 100).toFixed(1);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">馬一覧</h1>
              <p className="text-gray-600">総馬数: {horses.length}頭</p>
            </div>
            <div className="flex gap-4">
              <Link href="/" className="text-blue-600 hover:text-blue-800">
                ← ダッシュボードに戻る
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* メインコンテンツ */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 検索・ソート */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                検索
              </label>
              <input
                type="text"
                placeholder="馬名、父、母で検索..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ソート
                </label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as 'name' | 'price' | 'age')}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="name">馬名</option>
                  <option value="price">落札価格</option>
                  <option value="age">年齢</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  順序
                </label>
                <select
                  value={sortOrder}
                  onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="asc">昇順</option>
                  <option value="desc">降順</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* 馬一覧 */}
        <div className="space-y-4 mb-8">
          {filteredHorses.map((horse) => {
            // デバッグ用
            console.log('馬データ:', horse, 'id:', horse.id, typeof horse.id);
            // idがnull/undefinedの場合のみスキップ
            if (horse.id == null) return null;
            
            return (
              <Link key={horse.id} href={`/horses/${horse.id}`} className="block">
                <div className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow cursor-pointer">
                  <div className="flex items-center space-x-4">
                    {/* 馬体画像 */}
                    <div className="flex-shrink-0">
                      {horse.primary_image ? (
                        <HorseImage
                          src={horse.primary_image}
                          alt={horse.name}
                          className="w-20 h-20 object-contain rounded-lg bg-gray-100"
                        />
                      ) : (
                        <div className="w-20 h-20 bg-gray-200 rounded-lg flex items-center justify-center text-gray-400">No Image</div>
                      )}
                    </div>
                    {/* 基本情報 */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center mb-2">
                        <h3 className="text-lg font-semibold text-gray-900 mr-3">
                          {horse.name}
                        </h3>
                        <Badge variant={horse.sex === '牡' ? 'default' : 'secondary'}>
                          {horse.sex} {horse.age}歳
                        </Badge>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">落札価格:</span>
                          <p className="font-semibold text-red-600">{formatPrice(horse.sold_price)}</p>
                        </div>
                        <div>
                          <span className="text-gray-600">販売者:</span>
                          <p className="font-medium">{horse.seller || ''}</p>
                        </div>
                        <div>
                          <span className="text-gray-600">体重:</span>
                          <p className="font-medium">{horse.weight}kg</p>
                        </div>
                        {horse.total_prize_start > 0 && (
                          <div>
                            <span className="text-gray-600">成長率:</span>
                            <p className={`font-semibold ${parseFloat(getGrowthRate(horse.total_prize_start, horse.total_prize_latest)) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {getGrowthRate(horse.total_prize_start, horse.total_prize_latest)}%
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>

        {/* 結果件数 */}
        <div className="mt-8 text-center text-gray-600">
          {filteredHorses.length}頭の馬を表示中
        </div>
      </main>
    </div>
  );
} 