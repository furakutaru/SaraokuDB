"use client";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import HorseImage from '@/components/HorseImage';
import Link from 'next/link';
import { FaSort, FaSortUp, FaSortDown } from 'react-icons/fa';
import { useRouter } from 'next/navigation';
import { Horse, HorseData, HorseHistory } from '@/types/horse';

const formatPrice = (price: number | string | null | undefined) => {
  if (price === null || price === undefined) return '-';
  const numPrice = typeof price === 'string' ? parseFloat(price) : price;
  if (isNaN(numPrice)) return '-';
  return '¥' + numPrice.toLocaleString();
};

const formatPrize = (val: number | string | null | undefined) => {
  if (val === null || val === undefined || val === '') return '-';
  const numVal = Number(val);
  if (isNaN(numVal)) return '-';
  return `${numVal.toFixed(1)}万円`;
};

const calcROI = (prize: number | undefined, price: number | string | undefined): string => {
  if (!prize || !price) return '-';
  const numPrice = typeof price === 'string' ? parseFloat(price) : price;
  if (isNaN(numPrice) || numPrice === 0) return '-';
  return (prize / numPrice).toFixed(2);
};

export default function DashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<HorseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showType, setShowType] = useState<'all' | 'roi' | 'value'>('all');
  const [sortKey, setSortKey] = useState<string>('');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    fetchData();
    // ページタイトルを設定
    document.title = 'サラオクDB | 解析';
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await fetch('/data/horses_history.json');
      if (!response.ok) throw new Error('データの取得に失敗しました');
      const d = await response.json();
      setData(d);
    } catch (e: any) {
      setError('データの読み込みに失敗しました');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }
  if (error || !data) {
    return <div className="min-h-screen flex items-center justify-center text-red-600">{error || 'データがありません'}</div>;
  }

  // 最新履歴を抽出
  type HorseWithLatest = Horse & {
    total_prize_start: number | undefined;
    total_prize_latest: number | undefined;
    sold_price: number | string | undefined;
    unsold: boolean;
  };

  const horsesWithLatest: HorseWithLatest[] = data.horses.map(horse => {
    let latest: Partial<HorseHistory> = {};
    if (horse.history && horse.history.length > 0) {
      latest = horse.history[horse.history.length - 1];
    }
    return {
      ...horse,
      ...latest,
      detail_url: latest.detail_url || horse.detail_url, // detail_urlも最新履歴優先で
      total_prize_start: latest.total_prize_start ?? horse.total_prize_start,
      total_prize_latest: latest.total_prize_latest ?? horse.total_prize_latest,
      sold_price: latest.sold_price ?? horse.sold_price,
      unsold: horse.unsold_count ? horse.unsold_count > 0 : false
    } as HorseWithLatest;
  });

  // 主取り馬除外
  let horses = horsesWithLatest.filter(h => !h.unsold_count || h.unsold_count === 0);

  // 型ガード関数
  const isNumber = (value: unknown): value is number => {
    return typeof value === 'number' && !isNaN(value);
  };

  // サマリー
  const avgROI = horses.length > 0 ? (
    horses.reduce((sum, h) => {
      const soldPrice = typeof h.sold_price === 'number' ? h.sold_price : 0;
      const prizeLatest = h.total_prize_latest || 0;
      return sum + (soldPrice > 0 ? prizeLatest / soldPrice : 0);
    }, 0) / horses.length
  ) : 0;

  // 指標ボタン用データ
  const roiRanking = [...horses]
    .filter(h => {
      const soldPrice = typeof h.sold_price === 'number' ? h.sold_price : 0;
      return soldPrice > 0 && h.total_prize_latest;
    })
    .sort((a, b) => {
      const aSoldPrice = typeof a.sold_price === 'number' ? a.sold_price : 0;
      const bSoldPrice = typeof b.sold_price === 'number' ? b.sold_price : 0;
      const aROI = a.total_prize_latest ? a.total_prize_latest / aSoldPrice : 0;
      const bROI = b.total_prize_latest ? b.total_prize_latest / bSoldPrice : 0;
      return bROI - aROI;
    })
    .slice(0, 10);

  const valueHorses = horses.filter(h => {
    const soldPrice = typeof h.sold_price === 'number' ? h.sold_price : 0;
    const roi = h.total_prize_latest && soldPrice > 0 ? h.total_prize_latest / soldPrice : 0;
    return soldPrice > 0 && roi > avgROI && soldPrice < data.metadata.average_price;
  });

  // 表示切替
  let tableHorses: (Horse & HorseWithLatest)[] = [...horses];
  if (showType === 'roi') tableHorses = [...roiRanking] as (Horse & HorseWithLatest)[];
  if (showType === 'value') tableHorses = [...valueHorses] as (Horse & HorseWithLatest)[];

  // ソート関数
  const sortFunctions: { [key: string]: (a: Horse & HorseWithLatest, b: Horse & HorseWithLatest) => number } = {
    name: (a, b) => (a.name || '').localeCompare(b.name || '', 'ja'),
    sex: (a, b) => (a.sex || '').localeCompare(b.sex || '', 'ja'),
    age: (a, b) => {
      const ageA = typeof a.age === 'number' ? a.age : parseFloat(a.age as string) || 0;
      const ageB = typeof b.age === 'number' ? b.age : parseFloat(b.age as string) || 0;
      return ageA - ageB;
    },
    sire: (a, b) => (a.sire || '').localeCompare(b.sire || '', 'ja'),
    sold_price: (a, b) => {
      const aPrice = typeof a.sold_price === 'number' ? a.sold_price : 0;
      const bPrice = typeof b.sold_price === 'number' ? b.sold_price : 0;
      return aPrice - bPrice;
    },
    total_prize_start: (a, b) => (a.total_prize_start || 0) - (b.total_prize_start || 0),
    total_prize_latest: (a, b) => (a.total_prize_latest || 0) - (b.total_prize_latest || 0),
    roi: (a, b) => {
      const aSoldPrice = typeof a.sold_price === 'number' ? a.sold_price : 0;
      const bSoldPrice = typeof b.sold_price === 'number' ? b.sold_price : 0;
      const aROI = a.total_prize_latest && aSoldPrice > 0 ? a.total_prize_latest / aSoldPrice : 0;
      const bROI = b.total_prize_latest && bSoldPrice > 0 ? b.total_prize_latest / bSoldPrice : 0;
      return aROI - bROI;
    },
  };

  if (sortKey && sortFunctions[sortKey]) {
    tableHorses = [...tableHorses].sort((a, b) => {
      const res = sortFunctions[sortKey](a, b);
      return sortOrder === 'asc' ? res : -res;
    });
  }

  // ソートハンドラ
  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder(key === 'name' ? 'asc' : 'desc'); // 馬名はデフォルト昇順
    }
  };

  // ソートアイコン
  const renderSortIcon = (key: string) => {
    if (sortKey !== key) return <FaSort className="inline ml-1 text-gray-400" />;
    return sortOrder === 'asc' ? <FaSortUp className="inline ml-1 text-blue-600" /> : <FaSortDown className="inline ml-1 text-blue-600" />;
  };

  const displayPrice = (price: number | string | null | undefined, unsold: boolean | undefined = false) => {
    if (unsold === true) return '主取り';
    if (price === null || price === undefined || price === '') return '-';
    const numPrice = typeof price === 'string' ? parseFloat(price) : price;
    if (isNaN(numPrice)) return '-';
    return '¥' + numPrice.toLocaleString();
  };
  
  // Helper function to safely get detail URL
  const getDetailUrl = (horse: Horse & HorseWithLatest): string | undefined => {
    return horse.detail_url || (horse.history && horse.history.length > 0 ? horse.history[0].detail_url : undefined);
  };

  return (
    <>
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
      <div className="min-h-screen bg-gray-50 px-4 py-8">
        <div className="max-w-7xl mx-auto">
          {/* サマリー 横並びテキスト */}
          <div className="mb-6 text-lg font-semibold text-gray-700 flex flex-wrap gap-8">
            <span>総馬数: {horses.length}</span>
            <span>平均落札価格: {formatPrice(data.metadata.average_price)}</span>
            <span>平均ROI: {avgROI.toFixed(2)}</span>
          </div>
          {/* 指標ボタン（白文字色付き） */}
          <div className="flex gap-4 mb-6">
            <Button onClick={() => setShowType('all')} variant="default" className={showType==='all'?"bg-blue-600 text-white":"bg-blue-400 text-white"}>全馬</Button>
            <Button onClick={() => setShowType('roi')} variant="default" className={showType==='roi'?"bg-green-600 text-white":"bg-green-400 text-white"}>ROIランキング</Button>
            <Button onClick={() => setShowType('value')} variant="default" className={showType==='value'?"bg-orange-600 text-white":"bg-orange-400 text-white"}>妙味馬</Button>
          </div>
          {/* DataTable風の表 */}
          <div className="overflow-x-auto bg-white rounded-lg shadow">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('name')}>馬名{renderSortIcon('name')}</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('sex')}>性別{renderSortIcon('sex')}</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('age')}>年齢{renderSortIcon('age')}</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('sire')}>父{renderSortIcon('sire')}</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('sold_price')}>落札価格{renderSortIcon('sold_price')}</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('total_prize_start')}>オークション時賞金{renderSortIcon('total_prize_start')}</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('total_prize_latest')}>現在賞金{renderSortIcon('total_prize_latest')}</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('roi')}>ROI{renderSortIcon('roi')}</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">画像</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">リンク</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {tableHorses.map((horse) => (
                  <tr key={horse.id} className="hover:bg-blue-50">
                    <td className="px-3 py-2 font-medium text-gray-900">
                      <Link href={`/horses/${horse.id}`} className="hover:underline text-blue-700">{horse.name}</Link>
                    </td>
                    <td className="px-3 py-2">{horse.sex}</td>
                    <td className="px-3 py-2">{horse.age}</td>
                    <td className="px-3 py-2">{horse.sire}</td>
                    <td className="px-3 py-2">
                      {displayPrice(horse.sold_price, horse.unsold_count ? horse.unsold_count > 0 : undefined)}
                    </td>
                    <td className="px-3 py-2">{formatPrize(horse.total_prize_start)}</td>
                    <td className="px-3 py-2">{formatPrize(horse.total_prize_latest)}</td>
                    <td className="px-3 py-2">
                      {calcROI(horse.total_prize_latest, horse.sold_price)}
                    </td>
                    <td className="px-3 py-2">
                      {horse.primary_image ? (
                        <HorseImage src={horse.primary_image} alt={horse.name || 'Horse image'} className="w-12 h-12 object-contain rounded bg-gray-100" />
                      ) : (
                        <span className="text-gray-400">No Image</span>
                      )}
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex flex-col gap-1">
                        {horse.jbis_url && (
                          <a href={horse.jbis_url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 underline">JBIS</a>
                        )}
                        {getDetailUrl(horse) && (
                          <a href={getDetailUrl(horse)} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 underline">サラオク</a>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
} 