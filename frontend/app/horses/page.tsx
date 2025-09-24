'use client';

import { useState, useEffect } from 'react';
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
};

export default function HorsesPage() {
  const [horses, setHorses] = useState<Horse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
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
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">馬一覧</h1>
        <Link 
          href="/" 
          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          ← トップに戻る
        </Link>
      </div>
      
      {horses.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500">表示する馬のデータがありません</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {horses.map((horse) => (
            <div 
              key={horse.id}
              className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300 border border-gray-100"
            >
              <Link href={`/horses/${horse.id}`}>
                <div className="p-6">
                  <h2 className="text-xl font-bold text-gray-900 mb-2">{horse.name}</h2>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p>{horse.sex}・{horse.age}歳</p>
                    <p>父: {horse.sire}</p>
                    <p>母: {horse.dam}</p>
                    <p>母父: {horse.damsire}</p>
                  </div>
                  {horse.sold_price && (
                    <div className="mt-3">
                      <p className="text-sm font-medium">落札価格: {horse.sold_price.toLocaleString()}万円</p>
                    </div>
                  )}
                  <div className="mt-4 text-sm text-blue-600 font-medium">
                    詳細を見る →
                  </div>
                </div>
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
