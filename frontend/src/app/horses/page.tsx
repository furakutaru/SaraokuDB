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
  name?: string;
  sex?: string;
  age?: number | string;
  seller?: string;
  sold_price?: number;
  auction_date?: string;
  race_record?: string;
  total_prize_start?: number;
  history?: HorseHistory[];
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
  detail_url?: string;
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
    document.title = 'サラオクDB | 直近の追加';
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      // horses_history.jsonから馬データを取得
      const response = await fetch('/data/horses_history.json');
      if (!response.ok) {
        throw new Error('データの取得に失敗しました');
      }
      const jsonData = await response.json();
      
      // デバッグ用: データを出力
      console.log('読み込まれた馬の数:', jsonData.horses.length);
      console.log('馬のID一覧:', jsonData.horses.map((h: Horse) => h.id));
      
      // 全ての馬データをそのままセット
      setData({
        ...jsonData,
        horses: jsonData.horses
      });
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
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">直近の追加</h1>
                <p className="text-gray-600">直近1週間以内に追加された馬の一覧です。</p>
              </div>
              <div className="text-sm text-gray-500">
                現在の日時: {new Date().toLocaleString('ja-JP')}
              </div>
            </div>
            <p className="text-gray-600 mb-4">{error || 'データが見つかりません'}</p>
            <Button onClick={fetchData} className="bg-blue-600 hover:bg-blue-700">
              再試行
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // 最新履歴を抽出
  const horsesWithLatest = data.horses.map(horse => {
    // historyが存在しない場合は馬自体のデータを使用
    if (!horse.history || horse.history.length === 0) {
      return {
        ...horse,
        name: horse.name || 'Unknown',
        sex: horse.sex || 'Unknown',
        age: horse.age || 'Unknown',
        seller: horse.seller || 'Unknown',
        sold_price: horse.sold_price || 0,
        auction_date: horse.auction_date || 'Unknown',
        race_record: horse.race_record || 'Unknown'
      };
    }
    
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
          comparison = parseInt(String(a.age || 0)) - parseInt(String(b.age || 0));
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
              <Link href="/">
                <Button variant="outline" className="rounded-md bg-white border border-black text-black hover:bg-gray-100">解析</Button>
              </Link>
              <Link href="/horses">
                <Button variant="outline" className="rounded-md bg-white border border-black text-black hover:bg-gray-100">直近の追加</Button>
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
        <div className="w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {filteredHorses.map((horse) => {
            // デバッグ用
            console.log('馬データ:', horse, 'id:', horse.id, typeof horse.id);
            // idがnull/undefinedの場合のみスキップ
            if (horse.id == null) return null;
            
            return (
              <Link key={horse.id} href={`/horses/${horse.id}`} className="block h-full">
                <div className="w-full bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow cursor-pointer flex flex-col overflow-hidden">
                  {/* 馬体画像 */}
                  <div className="w-full">
                    {horse.primary_image ? (
                      <HorseImage
                        src={horse.primary_image}
                        alt={`${horse.name}の画像`}
                        className="w-full max-w-full h-auto object-cover"
                      />
                    ) : (
                      <div className="w-full bg-gray-100 aspect-[4/3] flex items-center justify-center text-gray-400">
                        <span>No Image</span>
                      </div>
                    )}
                  </div>
                  {/* 馬情報 */}
                  <div className="p-3 w-full">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="text-sm font-semibold line-clamp-1">{horse.name}</h3>
                      <div className="text-xs text-gray-500 whitespace-nowrap ml-2">
                        {horse.sex} {horse.age}歳
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-1 text-xs text-gray-600 mb-2 w-full">
                      <div className="col-span-2">
                        <span className="font-medium">父</span>: {horse.sire || '不明'}
                      </div>
                      <div className="col-span-2">
                        <span className="font-medium">母</span>: {horse.dam || '不明'}
                      </div>
                      <div className="col-span-2">
                        <span className="font-medium">母父</span>: {horse.dam_sire || '不明'}
                      </div>
                    </div>
                    
                    <div className="mt-auto pt-2 border-t border-gray-100">
                      <div className="flex justify-between items-center">
                        <span className={`inline-block px-2 py-1 text-xs rounded ${
                          horse.unsold 
                            ? 'bg-gray-100 text-gray-800' 
                            : 'bg-blue-100 text-blue-800'
                        }`}>
                          {horse.unsold ? '主取り' : `落札: ¥${(horse.sold_price || 0).toLocaleString()}`}
                        </span>
                        
                        {horse.disease_tags && horse.disease_tags.length > 0 && horse.disease_tags !== 'なし' && horse.disease_tags !== 'なし。' ? (
                          <span className="inline-block bg-pink-100 text-pink-800 text-xs px-2 py-1 rounded">
                            病歴: あり
                          </span>
                        ) : (
                          <span className="inline-block bg-blue-50 text-blue-600 text-xs px-2 py-1 rounded">
                            病歴: なし
                          </span>
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