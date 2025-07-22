'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import HorseImage from '@/components/HorseImage';
import { useRouter } from 'next/navigation';

interface HorseHistory {
  auction_date: string;
  name: string;
  sex: string;
  age: string;
  seller: string;
  race_record: string;
  comment: string;
  sold_price: number;
  total_prize_start: number;
}

interface Horse {
  id: number;
  history: HorseHistory[];
  sire: string;
  dam: string;
  dam_sire: string;
  primary_image: string;
  disease_tags: string;
  jbis_url: string;
  weight: number | null; // 体重
  unsold_count: number | null; // 主取り回数
  total_prize_latest: number; // 最新賞金
  created_at: string;
  updated_at: string;
  hidden?: boolean;
  unsold?: boolean;
}

interface Metadata {
  last_updated: string;
  total_horses: number;
  average_price: number;
}

interface HorseData {
  metadata: Metadata;
  horses: Horse[];
}

export default function HorsesPage() {
  const router = useRouter();
  const [data, setData] = useState<HorseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'price' | 'age'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  useEffect(() => {
    fetchData();
    // ページタイトルを設定
    document.title = 'サラオクDB | 馬一覧';
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      // horses_history.jsonから馬データを取得
      const response = await fetch('/data/horses_history.json');
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

  // 最新履歴を抽出
  const horsesWithLatest = data.horses.map(horse => {
    const latest = horse.history[horse.history.length - 1];
    return {
      ...latest,
      ...horse
    };
  });

  // 検索とソート前にhidden馬を除外
  const filteredHorses = horsesWithLatest
    .filter(horse => !horse.hidden)
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
          comparison = parseInt(a.age) - parseInt(b.age);
          break;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });

  // 賞金表示用関数
  // 賞金は万円単位で表示
  const formatPrize = (val: number | string | null | undefined) => {
    if (val === null || val === undefined || val === '' || isNaN(Number(val))) return '-';
    return `${Number(val).toFixed(1)}万円`;
  };

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
              <Link href="/dashboard">
                <Button variant="outline" className="rounded-md bg-white border border-black text-black hover:bg-gray-100">解析</Button>
              </Link>
              <Link href="/horses">
                <Button variant="outline" className="rounded-md bg-white border border-black text-black hover:bg-gray-100">馬一覧</Button>
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
                          <p className="font-semibold text-red-600">{displayPrice(horse.sold_price, horse.unsold)}</p>
                        </div>
                        <div>
                          <span className="text-gray-600">販売者:</span>
                          <p className="font-medium">{horse.seller || ''}</p>
                        </div>
                        <div>
                          <span className="text-gray-600">体重:</span>
                          <p className="font-medium">{horse.weight}kg</p>
                        </div>
                        {/* 成長率: すべての馬で必ず表示 */}
                        <div>
                          <span className="text-gray-600">成長率:</span>
                          <p className={`font-semibold ${parseFloat(getGrowthRate(horse.total_prize_start, horse.total_prize_latest)) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {getGrowthRate(horse.total_prize_start, horse.total_prize_latest)}%
                          </p>
                        </div>
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