'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

// 型定義
interface RaceRecord {
  date: string;
  race_name: string;
  finish_position: string;
  prize_money: number;
  total_prize_money?: number;
}

interface BasicHorseInfo {
  id: string | number;
  name: string;
  sex: string;
  age: number;
  color?: string;
  birthday?: string;
  sire: string;
  dam: string;
  dam_sire: string;
  breeder?: string;
  owner?: string;
  trainer?: string;
  stable?: string;
  image_url?: string;
  jbis_url?: string;
  comment?: string;
  weight?: number | null;
  is_unsold?: boolean;
  sold_price: number | null;
  auction_date: string | null;
  seller?: string;
  unsold_count?: number;
  total_prize_latest?: number;
  disease_tags?: string | string[];
  primary_image?: string;
  race_records?: RaceRecord[];
}

interface HorseHistory {
  auction_date?: string | string[] | null;
  name?: string;
  sex?: string;
  age?: number | string;
  seller?: string;
  race_record?: string;
  comment?: string;
  sold_price?: number | number[] | null;
  total_prize_start?: number;
  unsold?: boolean;
  detail_url?: string;
  primary_image?: string;
  disease_tags?: string | string[];
  weight?: number | null;
}

interface Horse extends BasicHorseInfo {
  id: number;
  history: HorseHistory[];
  total_prize_latest?: number;
  total_prize_start?: number;
}

interface HorseDetailContentProps {
  horse: Horse;
}

// ヘルパー関数
const formatDate = (dateString: string): string => {
  if (!dateString) return '-';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  } catch (e) {
    return '-';
  }
};

const displayPrice = (price: number | null | undefined, unsold: boolean = false): string => {
  if (unsold) return '未落札';
  if (price === null || price === undefined) return '-';
  return new Intl.NumberFormat('ja-JP').format(price) + '円';
};

const formatPrize = (val: number | string | null | undefined): string => {
  if (val === null || val === undefined) return '-';
  const num = typeof val === 'string' ? parseFloat(val) : val;
  if (isNaN(num)) return '-';
  return new Intl.NumberFormat('ja-JP').format(num) + '万円';
};

// 馬詳細コンポーネント（Tailwindベース）
const HorseDetailContent = ({ horse }: HorseDetailContentProps) => {
  const latestHistory = horse.history?.[0] || {};

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <Link href="/horses" className="rounded-md bg-white border border-black text-black px-4 py-2 hover:bg-gray-100 transition-colors">
              ← 戻る
            </Link>
            <div className="flex gap-4">
              <Link href="/" className="rounded-md bg-white border border-black text-black px-4 py-2 hover:bg-gray-100">解析</Link>
              <Link href="/horses" className="rounded-md bg-white border border-black text-black px-4 py-2 hover:bg-gray-100">直近の追加</Link>
            </div>
          </div>
        </div>
      </header>

      {/* メイン */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* メイン情報カード */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <div className="flex justify-between items-center mb-4">
                <h1 className="text-2xl font-semibold">{horse.name || '不明'}</h1>
                <div className="text-gray-600">{horse.sex || ''} {horse.age || ''}歳</div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <div className="text-gray-500 text-sm">父</div>
                  <div className="text-gray-900">{horse.sire || '-'}</div>
                </div>
                <div>
                  <div className="text-gray-500 text-sm">母</div>
                  <div className="text-gray-900">{horse.dam || '-'}</div>
                </div>
                <div>
                  <div className="text-gray-500 text-sm">母の父</div>
                  <div className="text-gray-900">{horse.dam_sire || '-'}</div>
                </div>
                <div>
                  <div className="text-gray-500 text-sm">セリ市</div>
                  <div className="text-gray-900">{formatDate(horse.auction_date as string)}</div>
                </div>
                <div>
                  <div className="text-gray-500 text-sm">落札価格</div>
                  <div className="text-gray-900">{displayPrice(horse.sold_price, horse.is_unsold)}</div>
                </div>
              </div>
            </div>
          </div>

          {/* サイド情報カード */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">賞金情報</h3>
              <div className="space-y-3">
                <div>
                  <div className="text-gray-500 text-sm">総賞金</div>
                  <div className="text-gray-900">{formatPrize(horse.total_prize_latest)}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

// メインページコンポーネント
export default function Page({ params }: { params: { id: string } }) {
  const [horse, setHorse] = useState<Horse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const fetchHorseData = async () => {
      try {
        setLoading(true);
        const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
        const response = await fetch(`${apiBase}/api/horses/${params.id}?_=${Date.now()}`, {
          method: 'GET',
          headers: { 'Accept': 'application/json' },
          cache: 'no-store',
          credentials: 'same-origin'
        });
        if (!response.ok) {
          throw new Error('馬データの取得に失敗しました');
        }
        const data = await response.json();
        setHorse(data as Horse);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'エラーが発生しました');
      } finally {
        setLoading(false);
      }
    };

    fetchHorseData();
  }, [params.id, router]);

  if (loading) {
    return <div>読み込み中...</div>;
  }

  if (error) {
    return <div>エラー: {error}</div>;
  }

  if (!horse) {
    return <div>馬のデータが見つかりませんでした</div>;
  }

  return <HorseDetailContent horse={horse} />;
}
