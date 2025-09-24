'use client';

import { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';

type Horse = {
  id: string | number;
  name: string;
  sex: string;
  age: number;
  sire: string;
  dam: string;
  damsire: string;
  image_url?: string;
  jbis_url?: string;
  auction_url?: string;
  sold_price?: number | null | any;
  seller?: string;
  auction_date?: string;
  is_unsold?: boolean;
  disease_tags?: string[] | string | null;
};

export default function HorsesPage() {
  const [horses, setHorses] = useState<Horse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'price' | 'age'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  useEffect(() => {
    const fetchHorses = async () => {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
        const apiUrl = `${baseUrl}/api/horses?_=${Date.now()}`;
        console.log('[horses/page] Fetch start:', apiUrl);

        const response = await fetch(apiUrl, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
          },
          cache: 'no-store',
          credentials: 'same-origin'
        });

        console.log('[horses/page] Fetch status:', response.status, response.statusText);
        if (!response.ok) {
          const text = await response.text();
          console.error('[horses/page] Error body:', text);
          throw new Error(`データの取得に失敗しました: ${response.status}`);
        }

        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
          const text = await response.text();
          console.error('[horses/page] 非JSONレスポンス:', text);
          throw new Error('無効なレスポンス形式です');
        }

        const data = await response.json();
        console.log('[horses/page] Response JSON:', data);

        // バックエンドは { horses, auctionHistories, metadata } の形
        const horsesArray: Horse[] = Array.isArray(data)
          ? data as Horse[]
          : (Array.isArray(data?.horses) ? data.horses : []);

        console.log('[horses/page] Parsed horses count:', horsesArray.length);
        setHorses(horsesArray);
      } catch (err) {
        console.error('Error:', err);
        setError('馬のデータの読み込み中にエラーが発生しました');
      } finally {
        setLoading(false);
      }
    };

    fetchHorses();
  }, []);

  // 表示用: 価格表示
  const displayPrice = (price: number | null | undefined, is_unsold?: boolean) => {
    if (is_unsold === true) return '主取り';
    if (price === null || price === undefined) return '-';
    try {
      return '¥' + Number(price).toLocaleString();
    } catch {
      return '-';
    }
  };

  // フィルタ・ソート
  const filteredHorses = useMemo(() => {
    let list = [...horses];
    const term = searchTerm.trim().toLowerCase();
    if (term) {
      list = list.filter(h =>
        (h.name || '').toLowerCase().includes(term) ||
        (h.sire || '').toLowerCase().includes(term) ||
        (h.dam || '').toLowerCase().includes(term) ||
        (h.damsire || '').toLowerCase().includes(term)
      );
    }
    list.sort((a, b) => {
      let cmp = 0;
      if (sortBy === 'name') {
        cmp = (a.name || '').localeCompare(b.name || '');
      } else if (sortBy === 'price') {
        const pa = Number(a.sold_price || 0);
        const pb = Number(b.sold_price || 0);
        cmp = pa - pb;
      } else if (sortBy === 'age') {
        cmp = (a.age || 0) - (b.age || 0);
      }
      return sortOrder === 'asc' ? cmp : -cmp;
    });
    return list;
  }, [horses, searchTerm, sortBy, sortOrder]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <Link href="/" className="rounded-md bg-white border border-black text-black px-4 py-2 hover:bg-gray-100 transition-colors">
              ← 戻る
            </Link>
            <div className="flex gap-4">
              <Link href="/" className="rounded-md bg-white border border-black text-black px-4 py-2 hover:bg-gray-100">解析</Link>
              <Link href="/horses" className="rounded-md bg-white border border-black text-black px-4 py-2 hover:bg-gray-100">直近の追加</Link>
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
              <label className="block text-sm font-medium text-gray-700 mb-2">検索</label>
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
                <label className="block text-sm font-medium text-gray-700 mb-2">ソート</label>
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
                <label className="block text-sm font-medium text-gray-700 mb-2">順序</label>
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
        {filteredHorses.length === 0 ? (
          <div className="text-center py-12 text-gray-500">表示する馬のデータがありません</div>
        ) : (
          <div className="w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            {filteredHorses.map((horse) => (
              <Link key={horse.id} href={`/horses/${horse.id}`} className="block h-full">
                <div className="w-full bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow cursor-pointer flex flex-col overflow-hidden h-full">
                  {/* 馬体画像 */}
                  <div className="w-full aspect-[4/3] overflow-hidden">
                    {horse.image_url ? (
                      <img src={horse.image_url} alt={`${horse.name}の画像`} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full bg-gray-100 flex items-center justify-center text-gray-400">No Image</div>
                    )}
                  </div>

                  {/* 馬情報 */}
                  <div className="p-4 flex-1 flex flex-col">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-lg font-semibold">{horse.name}</h3>
                      <div className="text-sm text-gray-600 ml-2">{horse.sex} {horse.age}歳</div>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm text-gray-700 mb-3">
                      <div>
                        <div className="text-gray-500 text-xs">父</div>
                        <div className="truncate">{horse.sire || '不明'}</div>
                      </div>
                      <div>
                        <div className="text-gray-500 text-xs">母</div>
                        <div className="truncate">{horse.dam || '不明'}</div>
                      </div>
                      <div>
                        <div className="text-gray-500 text-xs">母父</div>
                        <div className="truncate">{horse.damsire || '不明'}</div>
                      </div>
                      <div>
                        <div className="text-gray-500 text-xs">売主</div>
                        <div className="truncate">{'seller' in horse ? (horse.seller || '不明') : '不明'}</div>
                      </div>
                    </div>
                    <div className="mt-auto pt-2 border-t border-gray-100">
                      <div className="flex justify-between items-center">
                        <span className={`inline-block px-2 py-1 text-xs rounded ${horse.is_unsold ? 'bg-gray-100 text-gray-800' : 'bg-blue-100 text-blue-800'}`}>
                          {displayPrice(horse.sold_price as number | null | undefined, horse.is_unsold)}
                        </span>
                        {Array.isArray(horse.disease_tags) && horse.disease_tags.length > 0 && (
                          <span className="inline-flex items-center px-2 py-1 text-xs font-medium text-pink-800 bg-pink-100 rounded">
                            病歴: {horse.disease_tags[0]}
                            {horse.disease_tags.length > 1 && ` +${horse.disease_tags.length - 1}`}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* 結果件数 */}
        <div className="mt-8 text-center text-gray-600">{filteredHorses.length}頭の馬を表示中</div>
      </main>
    </div>
  );
}
