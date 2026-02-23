'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import HorseImage from '@/components/HorseImage';
import HorseCard from '@/components/HorseCard';
import { useRouter } from 'next/navigation';
import { Horse as BaseHorse, AuctionHistory, HorseData } from '@/types/horse';
import { getApiBase } from '@/lib/utils';

// コンポーネントで使用する馬の型を定義
export interface Horse {
  id: string | number;
  name?: string;
  auction_id?: string;
  sex: string;
  sire: string;
  dam: string;
  damsire: string;
  image_url: any; // ImageUrl | string の代わりに any を使用
  jbis_url?: string;
  detail_url?: string;
  created_at?: string;
  updated_at?: string;
  birth_year?: number;
  age?: number;
  color?: string;
  breeder?: string;
  owner?: string;
  trainer?: string;
  location?: string;
  auction_date?: string;
  sold_price?: number | null;
  is_unsold?: boolean;
  seller?: string;
  total_prize_start?: number;
  total_prize_latest?: number;
  prize_money?: { total_prize: string };
  display_prize?: string;
  display_roi?: string;
  display_weight?: string;
  display_price?: string;
  sort_price?: number;
  sort_prize?: number;
  sort_roi?: number;
  roi?: number;
  price_per_kg?: number;
  effectiveWeight?: number | null;
  auction_url?: string;
  unsold?: boolean;
  price?: number | null;
  race_records: {
    total_prize_money: number;
    last_race_date?: string;
    last_prize_update?: string;
  };
  auction_history?: AuctionHistory[];
  latest_auction?: AuctionHistory | null;
}

type HorseType = Horse;
import { Header } from '@/components/Header';

export default function HorsesPage() {
  const router = useRouter();
  const [horses, setHorses] = useState<HorseType[]>([]);
  const [auctionHistory, setAuctionHistory] = useState<AuctionHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'price' | 'age'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [showOnlyLatestAuction, setShowOnlyLatestAuction] = useState(true);
  const [latestAuctionDate, setLatestAuctionDate] = useState<string | null>(null);
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(24);
  const [total, setTotal] = useState<number>(0);
  const [debugInfo, setDebugInfo] = useState<{ url?: string; ran: boolean; received?: number; total?: number; apiBase?: string; err?: string }>({ ran: false });
  const isDebug = typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('debug') === '1';

  // 馬データを取得（バックエンドAPI + ページネーション）
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        const API_BASE = getApiBase();

        // 並び順のマッピング（価格と名前はサーバ側、年齢はクライアント側で実施）
        let sortParam = 'price_desc';
        if (sortBy === 'name') {
          sortParam = sortOrder === 'asc' ? 'name_asc' : 'name_desc';
        } else if (sortBy === 'price') {
          sortParam = sortOrder === 'asc' ? 'price_asc' : 'price_desc';
        }

        const skip = (page - 1) * limit;
        const latestParam = showOnlyLatestAuction ? 'true' : 'false';

        const url = `${API_BASE}/api/horses?skip=${skip}&limit=${limit}&sort=${encodeURIComponent(sortParam)}&latest_auction=${latestParam}`;
        if (isDebug) { console.log('[HorsesPage] API_BASE:', API_BASE, 'URL:', url); }
        setDebugInfo({ ran: true, url, apiBase: API_BASE });
        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error('データの取得に失敗しました');
        }

        const data = await response.json();

        // メタデータから合計件数などを取得
        if (data?.metadata) {
          setTotal(Number(data.metadata.total || 0));
          // latestAuctionDate はAPIからは取得できないため表示は抑制
          setLatestAuctionDate(null);
        }

        let items: HorseType[] = data?.horses || [];
        setDebugInfo(prev => ({ ...prev, received: (data?.horses || []).length, total: Number(data?.metadata?.total || 0) }));

        // 年齢ソートのみクライアント側で適用
        if (sortBy === 'age') {
          items = [...items].sort((a: any, b: any) => {
            const va = a.age || 0;
            const vb = b.age || 0;
            if (va === vb) return 0;
            return sortOrder === 'asc' ? va - vb : vb - va;
          });
        }

        setHorses(items);
        setError(null);
      } catch (err) {
        console.error('Error fetching data:', err);
        setDebugInfo(prev => ({ ...prev, err: String((err as any)?.message || err) }));
        setError('データの読み込み中にエラーが発生しました');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [page, limit, sortBy, sortOrder, showOnlyLatestAuction]);

  const DebugOverlay = () => !isDebug ? null : (
    <div style={{ position: 'fixed', top: 8, right: 8, zIndex: 9999 }}>
      <div style={{ background: '#111827', color: '#e5e7eb', padding: '8px 10px', borderRadius: 6, boxShadow: '0 2px 8px rgba(0,0,0,0.2)', maxWidth: 360 }}>
        <div style={{ fontWeight: 600, marginBottom: 4 }}>Debug</div>
        <div style={{ fontSize: 12, lineHeight: 1.4 }}>
          <div>API_BASE: <code>{debugInfo.apiBase || '(empty)'}</code></div>
          <div>URL: <code style={{ wordBreak: 'break-all' }}>{debugInfo.url}</code></div>
          <div>ran: {String(debugInfo.ran)} / received: {debugInfo.received ?? '-'} / total: {debugInfo.total ?? '-'}</div>
          {debugInfo.err && <div style={{ color: '#fca5a5' }}>error: {debugInfo.err}</div>}
        </div>
      </div>
    </div>
  );

  // フィルタリングとソートを適用した馬のリストを取得
  const filteredHorses = horses.filter(horse => {
    // 検索条件に一致するか確認
    const searchLower = searchTerm.toLowerCase();
    const matchesSearch = !searchTerm || 
      (horse.name && horse.name.toLowerCase().includes(searchLower)) ||
      (horse.sire && horse.sire.toLowerCase().includes(searchLower)) ||
      (horse.dam && horse.dam.toLowerCase().includes(searchLower)) ||
      (horse.damsire && horse.damsire.toLowerCase().includes(searchLower));
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
      <DebugOverlay />
      <Header pageTitle="直近追加の馬" />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <p className="text-sm text-gray-600">
            一覧: {total}頭中 {(page - 1) * limit + 1} - {Math.min(page * limit, total)}件を表示
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
        <div className="mt-8">
          {sortedHorses.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600">条件に一致する馬が見つかりませんでした</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {sortedHorses.map((horse: HorseType) => (
                <div key={horse.id} onClick={() => router.push(`/horses/${horse.id}`)}>
                  <HorseCard 
                    horse={horse} 
                    auctionHistory={horse.auction_history || []}
                    onClick={() => router.push(`/horses/${horse.id}`)}
                  />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ページネーション */}
        <div className="mt-8 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            ページ {page} / {Math.max(1, Math.ceil(total / limit))}
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1 || loading}
            >
              前へ
            </Button>
            <Button
              variant="outline"
              onClick={() => setPage((p) => (p * limit < total ? p + 1 : p))}
              disabled={page * limit >= total || loading}
            >
              次へ
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
