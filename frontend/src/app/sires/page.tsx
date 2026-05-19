'use client';

import { Suspense, useEffect, useState, useMemo } from 'react';
import Link from 'next/link';
import { Header } from '@/components/Header';
import { getApiBase } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FaSort, FaSortUp, FaSortDown } from 'react-icons/fa';

// --- ユーティリティ ---
const parseNum = (val: any): number => {
  if (val === null || val === undefined) return 0;
  if (typeof val === 'number') return isNaN(val) ? 0 : val;
  const parsed = parseFloat(String(val).replace(/[^0-9.-]/g, ''));
  return isNaN(parsed) ? 0 : parsed;
};
const avg = (arr: number[]) => arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
const med = (arr: number[]) => {
  if (!arr.length) return 0;
  const s = [...arr].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 !== 0 ? s[m] : (s[m - 1] + s[m]) / 2;
};
const roi = (latest: number, start: number, price: number) =>
  price > 0 ? ((latest - start) / price) * 100 : null;

interface SireStat {
  sire: string;
  count: number;
  male: number;
  female: number;
  gelding: number;
  avgPrice: number;
  medPrice: number;
  avgRoi: number;
  medRoi: number;
  avgWeight: number;
  winRate: number; // 賞金獲得率（prize_latest > prize_start）
}

function SiresContent() {
  const [sires, setSires] = useState<SireStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState<keyof SireStat>('count');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [search, setSearch] = useState('');
  const [minCount, setMinCount] = useState(3);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`${getApiBase()}/api/horses?skip=0&limit=5000`);
        const json = await res.json();
        const horses = json.horses || [];
        const auctions = json.auction_histories || [];

        const grouped: Record<string, any[]> = {};
        auctions.forEach((a: any) => {
          if (!grouped[a.horse_id]) grouped[a.horse_id] = [];
          grouped[a.horse_id].push(a);
        });

        // 各馬に最新オークション情報を付加
        const enriched = horses.map((h: any) => {
          const hAucs = grouped[h.id] || [];
          const latest = hAucs.sort((a: any, b: any) =>
            new Date(b.auction_date).getTime() - new Date(a.auction_date).getTime()
          )[0];
          return {
            ...h,
            sold_price: parseNum(latest?.price ?? h.sold_price),
            is_unsold: latest?.is_unsold || h.is_unsold || false,
            weight: parseNum(latest?.weight ?? h.weight),
            total_prize_start: parseNum(latest?.total_prize_start ?? h.total_prize_start),
            total_prize_latest: parseNum(latest?.total_prize_latest ?? h.total_prize_latest),
          };
        });

        // 種牡馬ごとに集計
        const sireMap: Record<string, any[]> = {};
        enriched.forEach((h: any) => {
          const sire = h.sire?.trim() || '不明';
          if (!sireMap[sire]) sireMap[sire] = [];
          sireMap[sire].push(h);
        });

        const stats: SireStat[] = Object.entries(sireMap).map(([sire, horses]) => {
          const sold = horses.filter(h => !h.is_unsold && h.sold_price > 0);
          const prices = sold.map(h => h.sold_price);
          const rois = sold
            .map(h => roi(h.total_prize_latest, h.total_prize_start, h.sold_price))
            .filter((r): r is number => r !== null && isFinite(r) && r >= -100 && r <= 1000);
          const weights = horses.map(h => h.weight).filter(w => w > 0 && isFinite(w));
          const winners = sold.filter(h => h.total_prize_latest > h.total_prize_start);

          return {
            sire,
            count: horses.length,
            male: horses.filter(h => h.sex === '牡').length,
            female: horses.filter(h => h.sex === '牝').length,
            gelding: horses.filter(h => h.sex === 'セ').length,
            avgPrice: prices.length ? avg(prices) : 0,
            medPrice: prices.length ? med(prices) : 0,
            avgRoi: rois.length ? avg(rois) : 0,
            medRoi: rois.length ? med(rois) : 0,
            avgWeight: weights.length ? avg(weights) : 0,
            winRate: sold.length ? (winners.length / sold.length) * 100 : 0,
          };
        });

        setSires(stats);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const filtered = useMemo(() => {
    return sires
      .filter(s => s.count >= minCount)
      .filter(s => s.sire.toLowerCase().includes(search.toLowerCase()))
      .sort((a, b) => {
        const av = a[sortKey] as number;
        const bv = b[sortKey] as number;
        return sortDir === 'desc' ? bv - av : av - bv;
      });
  }, [sires, sortKey, sortDir, search, minCount]);

  const handleSort = (key: keyof SireStat) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('desc'); }
  };

  const SortIcon = ({ k }: { k: keyof SireStat }) =>
    sortKey !== k ? <FaSort className="inline ml-1 text-gray-400" /> :
      sortDir === 'asc' ? <FaSortUp className="inline ml-1 text-blue-500" /> :
        <FaSortDown className="inline ml-1 text-blue-500" />;

  const formatMan = (v: number) => v > 0 ? `${Math.round(v / 10000).toLocaleString()}万` : '-';

  if (loading) return <div className="flex justify-center items-center h-64 text-gray-500">読み込み中...</div>;

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">種牡馬別データ</h2>
          <p className="text-sm text-gray-500 mt-1">{filtered.length} 種牡馬 / 全 {sires.length} 種牡馬</p>
        </div>
        <div className="flex gap-3 items-center">
          <label className="text-sm text-gray-600">
            最低頭数:
            <select
              value={minCount}
              onChange={e => setMinCount(Number(e.target.value))}
              className="ml-2 border rounded px-2 py-1 text-sm"
            >
              {[1, 2, 3, 5, 10, 20].map(n => <option key={n} value={n}>{n}頭以上</option>)}
            </select>
          </label>
          <input
            type="text"
            placeholder="種牡馬名で検索..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="border rounded px-3 py-1.5 text-sm w-48"
          />
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  {[
                    { key: 'sire', label: '種牡馬名', align: 'left' },
                    { key: 'count', label: '頭数', align: 'right' },
                    { key: 'male', label: '牡', align: 'right' },
                    { key: 'female', label: '牝', align: 'right' },
                    { key: 'gelding', label: 'セン', align: 'right' },
                    { key: 'avgPrice', label: '平均落札', align: 'right' },
                    { key: 'medPrice', label: '中央落札', align: 'right' },
                    { key: 'avgRoi', label: '平均ROI', align: 'right' },
                    { key: 'medRoi', label: '中央ROI', align: 'right' },
                    { key: 'winRate', label: '賞金獲得率', align: 'right' },
                    { key: 'avgWeight', label: '平均馬体重', align: 'right' },
                  ].map(col => (
                    <th
                      key={col.key}
                      className={`px-3 py-3 text-xs font-semibold text-gray-600 uppercase cursor-pointer hover:bg-gray-100 text-${col.align}`}
                      onClick={() => handleSort(col.key as keyof SireStat)}
                    >
                      {col.label}<SortIcon k={col.key as keyof SireStat} />
                    </th>
                  ))}
                  <th className="px-3 py-3 text-xs font-semibold text-gray-600 text-center">詳細</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map(s => (
                  <tr key={s.sire} className="hover:bg-blue-50/40 transition-colors">
                    <td className="px-3 py-2.5 font-medium text-gray-800">
                      <Link href={`/sires/${encodeURIComponent(s.sire)}`} className="hover:text-blue-600 hover:underline">
                        {s.sire}
                      </Link>
                    </td>
                    <td className="px-3 py-2.5 text-right">{s.count}</td>
                    <td className="px-3 py-2.5 text-right text-blue-500">{s.male || '-'}</td>
                    <td className="px-3 py-2.5 text-right text-pink-500">{s.female || '-'}</td>
                    <td className="px-3 py-2.5 text-right text-green-600">{s.gelding || '-'}</td>
                    <td className="px-3 py-2.5 text-right">{formatMan(s.avgPrice)}</td>
                    <td className="px-3 py-2.5 text-right">{formatMan(s.medPrice)}</td>
                    <td className={`px-3 py-2.5 text-right font-semibold ${s.avgRoi >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                      {s.avgRoi !== 0 ? `${s.avgRoi.toFixed(1)}%` : '-'}
                    </td>
                    <td className={`px-3 py-2.5 text-right font-semibold ${s.medRoi >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                      {s.medRoi !== 0 ? `${s.medRoi.toFixed(1)}%` : '-'}
                    </td>
                    <td className="px-3 py-2.5 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <div className="h-1.5 rounded-full bg-gray-200 w-16 overflow-hidden">
                          <div
                            className="h-full bg-indigo-400 rounded-full"
                            style={{ width: `${Math.min(s.winRate, 100)}%` }}
                          />
                        </div>
                        <span className="text-xs">{s.winRate.toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5 text-right text-gray-600">
                      {s.avgWeight > 0 ? `${Math.round(s.avgWeight)}kg` : '-'}
                    </td>
                    <td className="px-3 py-2.5 text-center">
                      <Link
                        href={`/sires/${encodeURIComponent(s.sire)}`}
                        className="text-xs text-blue-500 hover:underline border border-blue-200 rounded px-2 py-0.5 hover:bg-blue-50"
                      >
                        詳細
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function SiresPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Header pageTitle="サラオクDB｜種牡馬別データ" />
      <SiresContent />
    </Suspense>
  );
}
