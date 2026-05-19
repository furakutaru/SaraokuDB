'use client';

import { Suspense, useEffect, useState, useMemo } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Header } from '@/components/Header';
import { getApiBase } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ScatterChart, Scatter, ZAxis, LineChart, Line, ComposedChart, ReferenceLine
} from 'recharts';

const parseNum = (val: any): number => {
  if (val === null || val === undefined) return 0;
  if (typeof val === 'number') return isNaN(val) ? 0 : val;
  const p = parseFloat(String(val).replace(/[^0-9.-]/g, ''));
  return isNaN(p) ? 0 : p;
};
const avg = (arr: number[]) => arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
const med = (arr: number[]) => {
  if (!arr.length) return 0;
  const s = [...arr].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 !== 0 ? s[m] : (s[m - 1] + s[m]) / 2;
};
const safeRoi = (latest: number, start: number, price: number): number | null => {
  if (price <= 0) return null;
  const r = ((latest - start) / price) * 100;
  return isFinite(r) && r >= -200 && r <= 2000 ? r : null;
};
const fmMan = (v: number) => v > 0 ? `${Math.round(v / 10000).toLocaleString()}万` : '-';
const fmRoi = (v: number | null) => v !== null ? `${v.toFixed(1)}%` : '-';

function SireDetailContent({ sireName }: { sireName: string }) {
  const [allHorses, setAllHorses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

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
        const enriched = horses.map((h: any) => {
          const hAucs = (grouped[h.id] || []).sort((a: any, b: any) =>
            new Date(b.auction_date).getTime() - new Date(a.auction_date).getTime());
          const latest = hAucs[0];
          return {
            ...h,
            sold_price: parseNum(latest?.price ?? h.sold_price),
            is_unsold: latest?.is_unsold || h.is_unsold || false,
            weight: parseNum(latest?.weight ?? h.weight),
            total_prize_start: parseNum(latest?.total_prize_start ?? h.total_prize_start),
            total_prize_latest: parseNum(latest?.total_prize_latest ?? h.total_prize_latest),
          };
        });
        setAllHorses(enriched);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const horses = useMemo(() =>
    allHorses.filter(h => (h.sire?.trim() || '不明') === sireName),
    [allHorses, sireName]);

  const sold = useMemo(() =>
    horses.filter(h => !h.is_unsold && h.sold_price > 0), [horses]);

  // --- 基本統計 ---
  const basicStats = useMemo(() => {
    const prices = sold.map(h => h.sold_price);
    const rois = sold.map(h => safeRoi(h.total_prize_latest, h.total_prize_start, h.sold_price))
      .filter((r): r is number => r !== null);
    const weights = horses.map(h => h.weight).filter(w => w > 0);
    const winners = sold.filter(h => h.total_prize_latest > h.total_prize_start);
    return {
      total: horses.length, sold: sold.length, unsold: horses.length - sold.length,
      male: horses.filter(h => h.sex === '牡').length,
      female: horses.filter(h => h.sex === '牝').length,
      gelding: horses.filter(h => h.sex === 'セ').length,
      avgPrice: avg(prices), medPrice: med(prices),
      avgRoi: avg(rois), medRoi: med(rois),
      avgWeight: avg(weights), medWeight: med(weights),
      winRate: sold.length ? (winners.length / sold.length) * 100 : 0,
      prizeDiff: avg(sold.map(h => h.total_prize_latest - h.total_prize_start)),
    };
  }, [horses, sold]);

  // --- 年齢別集計 ---
  const ageData = useMemo(() => {
    const groups: Record<number, { prices: number[], rois: number[], count: number }> = {};
    sold.forEach(h => {
      const age = h.age || 0;
      if (age < 2 || age > 12) return;
      if (!groups[age]) groups[age] = { prices: [], rois: [], count: 0 };
      groups[age].prices.push(h.sold_price);
      groups[age].count++;
      const r = safeRoi(h.total_prize_latest, h.total_prize_start, h.sold_price);
      if (r !== null) groups[age].rois.push(r);
    });
    return Object.entries(groups)
      .map(([age, d]) => ({
        age: `${age}歳`,
        avgPrice: Math.round(avg(d.prices) / 10000),
        medPrice: Math.round(med(d.prices) / 10000),
        avgRoi: d.rois.length ? parseFloat(avg(d.rois).toFixed(1)) : null,
        count: d.count,
      }))
      .sort((a, b) => parseInt(a.age) - parseInt(b.age));
  }, [sold]);

  // --- 性別集計 ---
  const sexData = useMemo(() => {
    return ['牡', '牝', 'セ'].map(sex => {
      const group = sold.filter(h => h.sex === sex);
      const prices = group.map(h => h.sold_price);
      const rois = group.map(h => safeRoi(h.total_prize_latest, h.total_prize_start, h.sold_price))
        .filter((r): r is number => r !== null);
      return {
        sex, count: group.length,
        avgPrice: prices.length ? Math.round(avg(prices) / 10000) : 0,
        medPrice: prices.length ? Math.round(med(prices) / 10000) : 0,
        avgRoi: rois.length ? parseFloat(avg(rois).toFixed(1)) : 0,
        medRoi: rois.length ? parseFloat(med(rois).toFixed(1)) : 0,
      };
    }).filter(d => d.count > 0);
  }, [sold]);

  // --- 馬体重ゾーン別集計 ---
  const weightZoneData = useMemo(() => {
    const zones = [
      { label: '~420kg', min: 0, max: 420 },
      { label: '421~450', min: 421, max: 450 },
      { label: '451~480', min: 451, max: 480 },
      { label: '481~510', min: 481, max: 510 },
      { label: '511kg~', min: 511, max: 9999 },
    ];
    return zones.map(z => {
      const group = sold.filter(h => h.weight >= z.min && h.weight <= z.max && h.weight > 0);
      const prices = group.map(h => h.sold_price);
      const rois = group.map(h => safeRoi(h.total_prize_latest, h.total_prize_start, h.sold_price))
        .filter((r): r is number => r !== null);
      return {
        zone: z.label, count: group.length,
        avgPrice: prices.length ? Math.round(avg(prices) / 10000) : 0,
        avgRoi: rois.length ? parseFloat(avg(rois).toFixed(1)) : 0,
      };
    }).filter(d => d.count > 0);
  }, [sold]);

  // --- 散布図: 落札価格 vs ROI ---
  const scatterData = useMemo(() =>
    sold.map(h => {
      const r = safeRoi(h.total_prize_latest, h.total_prize_start, h.sold_price);
      return r !== null ? {
        name: h.name, sex: h.sex, age: h.age,
        price: Math.round(h.sold_price / 10000),
        roi: Math.max(-100, Math.min(r, 500)),
        realRoi: r,
      } : null;
    }).filter((d): d is NonNullable<typeof d> => d !== null),
    [sold]);

  // --- 疾病別集計 ---
  const diseaseData = useMemo(() => {
    const negativeTags = ['なし', 'なし。', '特になし', '特になし。', '疾患履歴なし'];
    const hasDisease = (tags: any) => {
      if (!tags) return false;
      const arr = Array.isArray(tags) ? tags : [String(tags)];
      return arr.length > 0 && !arr.every((t: string) => negativeTags.includes(t.trim()));
    };
    const severeKeywords = ['屈腱炎', '骨折', '喘鳴症', 'ボーンシスト', '繋靭帯炎'];
    const isSevere = (tags: any) => {
      const str = Array.isArray(tags) ? tags.join(',') : String(tags || '');
      return severeKeywords.some(k => str.includes(k));
    };
    const groups = { '重度疾患あり': [] as any[], 'その他疾患あり': [] as any[], '記載なし': [] as any[] };
    sold.forEach(h => {
      const key = isSevere(h.disease_tags) ? '重度疾患あり' :
        hasDisease(h.disease_tags) ? 'その他疾患あり' : '記載なし';
      groups[key].push(h);
    });
    return Object.entries(groups).map(([name, group]) => {
      const prices = group.map((h: any) => h.sold_price);
      const rois = group.map((h: any) => safeRoi(h.total_prize_latest, h.total_prize_start, h.sold_price))
        .filter((r): r is number => r !== null);
      return {
        name, count: group.length,
        avgPrice: prices.length ? Math.round(avg(prices) / 10000) : 0,
        avgRoi: rois.length ? parseFloat(avg(rois).toFixed(1)) : 0,
      };
    }).filter(d => d.count > 0);
  }, [sold]);

  if (loading) return <div className="flex justify-center items-center h-64 text-gray-500">読み込み中...</div>;
  if (horses.length === 0) return (
    <div className="max-w-7xl mx-auto px-4 py-8 text-center">
      <p className="text-gray-500">「{sireName}」の産駒データが見つかりませんでした。</p>
      <Link href="/sires" className="text-blue-500 hover:underline mt-4 inline-block">← 種牡馬一覧に戻る</Link>
    </div>
  );

  const StatCard = ({ label, value, sub }: { label: string; value: string; sub?: string }) => (
    <div className="bg-white rounded-lg border p-4 text-center">
      <div className="text-xs text-gray-500 uppercase font-bold tracking-wider mb-1">{label}</div>
      <div className="text-xl font-black text-gray-800">{value}</div>
      {sub && <div className="text-xs text-gray-400 mt-0.5">{sub}</div>}
    </div>
  );

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
      <div className="bg-white border shadow rounded p-2 text-xs">
        <p className="font-bold">{d.name}</p>
        <p>{d.sex} / {d.age}歳</p>
        <p>落札: {d.price}万円</p>
        <p>ROI: {d.realRoi?.toFixed(1)}%</p>
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* ページヘッダー */}
      <div className="flex items-center justify-between">
        <div>
          <Link href="/sires" className="text-sm text-blue-500 hover:underline">← 種牡馬一覧</Link>
          <h2 className="text-3xl font-black text-gray-900 mt-1">{sireName}</h2>
          <p className="text-gray-500 text-sm mt-1">産駒 {basicStats.total}頭のデータ分析</p>
        </div>
      </div>

      {/* KPIカード */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        <StatCard label="総頭数" value={`${basicStats.total}頭`} />
        <StatCard label="落札数" value={`${basicStats.sold}頭`} sub={`主取り ${basicStats.unsold}頭`} />
        <StatCard label="牡" value={`${basicStats.male}頭`} />
        <StatCard label="牝" value={`${basicStats.female}頭`} />
        <StatCard label="平均落札" value={fmMan(basicStats.avgPrice)} sub={`中央値 ${fmMan(basicStats.medPrice)}`} />
        <StatCard label="平均ROI" value={fmRoi(basicStats.avgRoi)} sub={`中央値 ${fmRoi(basicStats.medRoi)}`} />
        <StatCard label="賞金獲得率" value={`${basicStats.winRate.toFixed(0)}%`} sub="落札後に賞金増加" />
        <StatCard label="平均馬体重" value={basicStats.avgWeight > 0 ? `${Math.round(basicStats.avgWeight)}kg` : '-'} sub={`中央値 ${basicStats.medWeight > 0 ? Math.round(basicStats.medWeight) + 'kg' : '-'}`} />
      </div>

      {/* グラフグリッド */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* 年齢別落札価格 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">年齢別 落札価格（平均・中央値）</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={ageData} margin={{ top: 10, right: 10, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="age" tick={{ fontSize: 12 }} />
                  <YAxis unit="万" tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v: any) => `${v}万円`} />
                  <Legend />
                  <Bar dataKey="avgPrice" name="平均" fill="#3b82f6" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="medPrice" name="中央値" fill="#93c5fd" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* 年齢別ROI */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">年齢別 ROI（平均）</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={ageData} margin={{ top: 10, right: 10, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="age" tick={{ fontSize: 12 }} />
                  <YAxis unit="%" tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v: any) => `${v}%`} />
                  <ReferenceLine y={0} stroke="#9ca3af" strokeDasharray="4 4" />
                  <Bar dataKey="avgRoi" name="平均ROI" fill="#10b981" radius={[3, 3, 0, 0]} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* 性別比較 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">性別別 落札価格・ROI比較</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={sexData} margin={{ top: 10, right: 30, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="sex" tick={{ fontSize: 13 }} />
                  <YAxis yAxisId="left" unit="万" tick={{ fontSize: 11 }} />
                  <YAxis yAxisId="right" orientation="right" unit="%" tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="avgPrice" name="平均落札" fill="#6366f1" radius={[3, 3, 0, 0]} />
                  <Bar yAxisId="left" dataKey="medPrice" name="中央落札" fill="#a5b4fc" radius={[3, 3, 0, 0]} />
                  <Line yAxisId="right" type="monotone" dataKey="avgRoi" name="平均ROI" stroke="#f59e0b" strokeWidth={2} dot={{ r: 5 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* 馬体重ゾーン別 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">馬体重ゾーン別 落札価格・ROI</CardTitle>
            <p className="text-xs text-gray-400">活躍しやすい馬体重のヒント</p>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={weightZoneData} margin={{ top: 10, right: 30, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="zone" tick={{ fontSize: 11 }} />
                  <YAxis yAxisId="left" unit="万" tick={{ fontSize: 11 }} />
                  <YAxis yAxisId="right" orientation="right" unit="%" tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="avgPrice" name="平均落札" fill="#8b5cf6" radius={[3, 3, 0, 0]} />
                  <Line yAxisId="right" type="monotone" dataKey="avgRoi" name="平均ROI" stroke="#f43f5e" strokeWidth={2} dot={{ r: 5 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* 疾病別 */}
        {diseaseData.length > 1 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">疾病記載別 価格・ROIへの影響</CardTitle>
              <p className="text-xs text-gray-400">重度: 屈腱炎・骨折・喘鳴症など</p>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={diseaseData} margin={{ top: 10, right: 30, bottom: 5, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                    <YAxis yAxisId="left" unit="万" tick={{ fontSize: 11 }} />
                    <YAxis yAxisId="right" orientation="right" unit="%" tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Legend />
                    <Bar yAxisId="left" dataKey="avgPrice" name="平均落札" fill="#f97316" radius={[3, 3, 0, 0]} />
                    <Line yAxisId="right" type="monotone" dataKey="avgRoi" name="平均ROI" stroke="#ec4899" strokeWidth={2} dot={{ r: 5 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 散布図: 価格 vs ROI */}
        <Card className={diseaseData.length > 1 ? '' : 'lg:col-span-2'}>
          <CardHeader>
            <CardTitle className="text-base">落札価格 vs ROI（産駒個別）</CardTitle>
            <p className="text-xs text-gray-400">左上が「お買い得馬」の領域</p>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" dataKey="price" name="落札価格" unit="万" tick={{ fontSize: 11 }} />
                  <YAxis type="number" dataKey="roi" name="ROI" unit="%" domain={[-100, 500]} tick={{ fontSize: 11 }} />
                  <ZAxis range={[40, 40]} />
                  <ReferenceLine y={0} stroke="#9ca3af" strokeDasharray="4 4" />
                  <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
                  <Scatter data={scatterData} fill="#3b82f6" fillOpacity={0.6} />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 産駒リスト */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">産駒一覧 ({horses.length}頭)</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  {['馬名', '性別', '年齢', '馬体重', '落札価格', '落札時賞金', '現在賞金', 'ROI', '疾病'].map(h => (
                    <th key={h} className="px-3 py-2.5 text-xs font-semibold text-gray-600 text-left">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {horses.map(h => {
                  const r = safeRoi(h.total_prize_latest, h.total_prize_start, h.sold_price);
                  return (
                    <tr key={h.id} className="hover:bg-gray-50">
                      <td className="px-3 py-2">
                        <Link href={`/horses/${h.id}`} className="text-blue-600 hover:underline font-medium">{h.name}</Link>
                      </td>
                      <td className="px-3 py-2">
                        <span className={`text-xs font-bold ${h.sex === '牡' ? 'text-blue-500' : h.sex === '牝' ? 'text-pink-500' : 'text-green-600'}`}>
                          {h.sex || '-'}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-gray-600">{h.age || '-'}</td>
                      <td className="px-3 py-2 text-gray-600">{h.weight > 0 ? `${h.weight}kg` : '-'}</td>
                      <td className="px-3 py-2 font-medium">{h.is_unsold ? '主取り' : fmMan(h.sold_price)}</td>
                      <td className="px-3 py-2 text-gray-600">{fmMan(h.total_prize_start)}</td>
                      <td className="px-3 py-2 text-gray-600">{fmMan(h.total_prize_latest)}</td>
                      <td className={`px-3 py-2 font-semibold ${r !== null && r >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                        {fmRoi(r)}
                      </td>
                      <td className="px-3 py-2 text-xs text-gray-500">
                        {Array.isArray(h.disease_tags) && h.disease_tags.length > 0
                          ? h.disease_tags.slice(0, 2).join('・')
                          : '-'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function SireDetailPage() {
  const params = useParams();
  const sireName = decodeURIComponent(params.name as string);
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Header pageTitle={`サラオクDB｜${sireName}`} />
      <SireDetailContent sireName={sireName} />
    </Suspense>
  );
}
