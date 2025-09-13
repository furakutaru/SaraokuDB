'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import HorseImage from '@/components/HorseImage';
import { useRouter } from 'next/navigation';

interface Horse {
  id: string; // UUID形式のID
  name: string;
  sex: string;
  age: number;
  sire: string;
  dam: string;
  damsire: string;
  image_url: string;
  jbis_url: string;
  auction_url: string;
  disease_tags: string[];
  weight: number | null;
  race_record: string;
  comment: string;
  created_at: string;
  updated_at: string;
  sold_price?: number | null;
  seller?: string;
  auction_date?: string;
  total_prize_start?: number;
  total_prize_latest?: number;
  is_unsold?: boolean;
}

interface AuctionHistory {
  id: string;
  horse_id: string;
  auction_date: string;
  sold_price: number | null;
  total_prize_start: number;
  total_prize_latest: number;
  weight: number | null;
  seller: string;
  is_unsold: boolean;
  comment: string;
  created_at: string;
}

interface HorseData {
  horses: Horse[];
  auctionHistories: AuctionHistory[];
  metadata: {
    last_updated: string;
    total_horses: number;
    total_auction_records: number;
  };
}

interface HorseData {
  horses: Horse[];
  auctionHistories: AuctionHistory[];
  metadata: {
    last_updated: string;
    total_horses: number;
    total_auction_records: number;
  };
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
      
      // バックエンドAPIから馬データを取得
      const response = await fetch('http://localhost:8001/horses/?limit=100');
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('API Error:', errorData);
        throw new Error(errorData.message || 'データの取得に失敗しました');
      }

      const result = await response.json();
      const horses = result.data || [];
      
      console.log('APIから取得した馬の数:', horses.length);
      
      // オークション履歴を馬データから抽出
      const auctionHistories = horses.flatMap((horse: any) => {
        if (!horse.auction_date || !Array.isArray(horse.auction_date)) return [];
        
        return horse.auction_date.map((date: string, index: number) => {
          // 販売価格を取得（配列の場合はインデックスでアクセス、そうでなければそのまま使用）
          const soldPrice = Array.isArray(horse.sold_price) 
            ? (index < horse.sold_price.length ? horse.sold_price[index] : null)
            : horse.sold_price;
            
          // 販売者の取得
          const seller = Array.isArray(horse.seller) 
            ? (index < horse.seller.length ? horse.seller[index] : '')
            : horse.seller || '';
            
          // コメントの取得
          const comment = Array.isArray(horse.comment)
            ? (index < horse.comment.length ? horse.comment[index] : '')
            : horse.comment || '';
            
          return {
            id: `${horse.id}-${index}`,
            horse_id: horse.id,
            auction_date: date,
            sold_price: soldPrice,
            total_prize_start: horse.total_prize_start || 0,
            total_prize_latest: horse.total_prize_latest || 0,
            weight: null,
            seller: seller,
            is_unsold: soldPrice === null || soldPrice === undefined || soldPrice === 0,
            comment: comment,
            created_at: horse.created_at || new Date().toISOString()
          };
        });
      });
      
      // 馬データを整形
      const formattedHorses = horses.map((horse: any) => {
        // 販売価格を取得（配列の場合は最初の要素、数値の場合はそのまま）
        const soldPrice = Array.isArray(horse.sold_price) 
          ? (horse.sold_price.length > 0 ? horse.sold_price[0] : null)
          : horse.sold_price;
          
        return {
          ...horse,
          // 配列フィールドを単一値に変換（最初の要素を使用）
          sex: Array.isArray(horse.sex) ? horse.sex[0] : horse.sex,
          age: Array.isArray(horse.age) ? horse.age[0] : horse.age,
          auction_date: Array.isArray(horse.auction_date) ? horse.auction_date[0] : horse.auction_date,
          sold_price: soldPrice,
          seller: Array.isArray(horse.seller) ? horse.seller[0] : horse.seller,
          comment: Array.isArray(horse.comment) ? horse.comment[0] : horse.comment,
          is_unsold: soldPrice === null || soldPrice === undefined || soldPrice === 0,
        };
      });
      
      console.log('フォーマット済み馬データ:', formattedHorses.slice(0, 3));
      
      // 馬データとオークション履歴を結合
      const horsesWithAuctionInfo = formattedHorses.map((horse: Horse) => {
        // 最新のオークション履歴を取得
        const latestAuction = auctionHistories
          .filter((ah: AuctionHistory) => ah.horse_id === horse.id)
          .sort((a: AuctionHistory, b: AuctionHistory) => new Date(b.auction_date).getTime() - new Date(a.auction_date).getTime())[0];

        // 価格を決定（馬オブジェクト → オークション履歴の順で優先）
        const soldPrice = horse.sold_price !== undefined ? horse.sold_price : 
                        (latestAuction?.sold_price !== undefined ? latestAuction.sold_price : null);
        
        // 主取りかどうかを判定（明示的に設定されていない場合は不明として扱う）
        const isUnsold = horse.is_unsold !== undefined ? horse.is_unsold : 
                        (latestAuction?.is_unsold !== undefined ? latestAuction.is_unsold : null);

        // 価格が取得できず、主取りフラグも不明な場合はエラー
        if (soldPrice === null && isUnsold === null) {
          console.error(`価格情報が不足しています: ${horse.name} (ID: ${horse.id})`);
        }

        return {
          ...horse,
          auction_date: latestAuction?.auction_date || horse.auction_date || '',
          sold_price: soldPrice,
          seller: latestAuction?.seller || horse.seller || 'Unknown',
          is_unsold: isUnsold,
          total_prize_start: latestAuction?.total_prize_start || horse.total_prize_start || 0,
          total_prize_latest: latestAuction?.total_prize_latest || horse.total_prize_latest || 0,
          weight: latestAuction?.weight || horse.weight || null
        };
      });

      setData({
        horses: horsesWithAuctionInfo,
        auctionHistories,
        metadata: {
          last_updated: new Date().toISOString(),
          total_horses: horses.length,
          total_auction_records: auctionHistories.length
        }
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

  // 馬データとオークション履歴を結合
  const horsesWithAuctionInfo = data.horses.map(horse => {
    // 馬に関連する最新のオークション履歴を取得
    const latestAuction = data.auctionHistories
      .filter(ah => ah.horse_id === horse.id)
      .sort((a, b) => new Date(b.auction_date).getTime() - new Date(a.auction_date).getTime())[0];

    // 馬オブジェクトのsold_priceを優先し、なければオークション履歴から取得
    const soldPrice = horse.sold_price !== undefined ? horse.sold_price : 
                     (latestAuction?.sold_price || null);
    
    // 主取りかどうかを判定
    const isUnsold = horse.is_unsold !== undefined ? horse.is_unsold : 
                    (soldPrice === null || soldPrice === 0);

    return {
      ...horse,
      auction_date: latestAuction?.auction_date || horse.auction_date || '',
      sold_price: soldPrice,
      seller: latestAuction?.seller || horse.seller || 'Unknown',
      is_unsold: isUnsold,
      total_prize_start: latestAuction?.total_prize_start || horse.total_prize_start || 0,
      total_prize_latest: latestAuction?.total_prize_latest || horse.total_prize_latest || 0,
      weight: latestAuction?.weight || horse.weight || null
    };
  });

  // 検索とソート
  const filteredHorses = horsesWithAuctionInfo
    .filter(horse => 
      horse.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      horse.sire.toLowerCase().includes(searchTerm.toLowerCase()) ||
      horse.dam.toLowerCase().includes(searchTerm.toLowerCase()) ||
      horse.damsire.toLowerCase().includes(searchTerm.toLowerCase())
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
          comparison = (a.age || 0) - (b.age || 0);
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
  // 落札価格は取得値そのまま（円単位）で表示
  const displayPrice = (price: number | null | undefined, is_unsold: boolean | undefined) => {
    if (is_unsold === true) return '主取り';
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
            
            // idがnull/undefinedの場合はスキップ
            if (!horse.id) return null;
            
            return (
              <Link key={horse.id} href={`/horses/${horse.id}`} className="block h-full">
                <div className="w-full bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow cursor-pointer flex flex-col overflow-hidden h-full">
                  {/* 馬体画像 */}
                  <div className="w-full aspect-[4/3] overflow-hidden">
                    {horse.image_url ? (
                      <HorseImage
                        src={horse.image_url}
                        alt={`${horse.name}の画像`}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full bg-gray-100 flex items-center justify-center text-gray-400">
                        <span>No Image</span>
                      </div>
                    )}
                  </div>
                  
                  {/* 馬情報 */}
                  <div className="p-4 flex-1 flex flex-col">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-lg font-semibold">{horse.name}</h3>
                      <div className="text-sm text-gray-600 ml-2">
                        {horse.sex} {horse.age}歳
                      </div>
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
                        <div className="truncate">{'seller' in horse ? horse.seller : '不明'}</div>
                      </div>
                    </div>
                    
                    <div className="mt-auto pt-2 border-t border-gray-100">
                      <div className="flex justify-between items-center">
                        <span className={`inline-block px-2 py-1 text-xs rounded ${
                          horse.is_unsold
                            ? 'bg-gray-100 text-gray-800' 
                            : 'bg-blue-100 text-blue-800'
                        }`}>
                          {displayPrice(horse.sold_price, horse.is_unsold)}
                        </span>
                        
                        {horse.disease_tags && horse.disease_tags.length > 0 && (
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