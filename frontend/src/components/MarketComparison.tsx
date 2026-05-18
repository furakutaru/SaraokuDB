import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { getApiBase } from '@/lib/utils';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend, Cell } from 'recharts';

interface MarketComparisonProps {
  horseId: string | number;
  price: number | null;
  prize: number | null;
  weight: number | null;
  age: number | string | null;
  sex: string | null;
}

const calculatePercentile = (value: number, array: number[]) => {
  if (array.length === 0 || value === 0) return 0;
  const sorted = [...array].sort((a, b) => a - b);
  const index = sorted.findIndex(v => v >= value);
  if (index === -1) return 100;
  return Math.round((index / sorted.length) * 100);
};

const median = (arr: number[]) => {
  if (!arr.length) return 0;
  const sorted = [...arr].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
};

const average = (arr: number[]) => arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;

export function MarketComparison({ horseId, price, prize, weight, age, sex }: MarketComparisonProps) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`${getApiBase()}/api/horses?skip=0&limit=5000`);
        const json = await res.json();
        
        const horses = json.horses || [];
        const auctions = json.auction_histories || [];
        
        const groupedAuctions = auctions.reduce((acc: any, auc: any) => {
          if (!acc[auc.horse_id]) acc[auc.horse_id] = [];
          acc[auc.horse_id].push(auc);
          return acc;
        }, {});

        const processed = horses.map((h: any) => {
          const hAuctions = groupedAuctions[h.id] || [];
          const latest = hAuctions.sort((a: any, b: any) => new Date(b.auction_date).getTime() - new Date(a.auction_date).getTime())[0];

          const parseNum = (val: any) => {
            if (val === null || val === undefined) return 0;
            if (typeof val === 'number') return isNaN(val) ? 0 : val;
            const parsed = parseFloat(String(val).replace(/[^0-9.-]/g, ''));
            return isNaN(parsed) ? 0 : parsed;
          };

          return {
            ...h,
            sold_price: parseNum(latest?.price ?? h.sold_price),
            weight: parseNum(latest?.weight ?? h.weight),
            total_prize_latest: parseNum(latest?.total_prize_latest ?? h.total_prize_latest),
          };
        }).filter((h: any) => !h.is_unsold && h.sold_price > 0);
        
        setData(processed);
      } catch (e) {
        console.error("Failed to fetch market data", e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const stats = useMemo(() => {
    if (data.length === 0) return null;

    const safeRound = (n: number) => (isFinite(n) ? Math.round(n) : 0);

    const allPrices = data.map(h => h.sold_price).filter(v => isFinite(v) && v > 0);
    const allPrizes = data.map(h => h.total_prize_latest).filter(v => isFinite(v));
    const allWeights = data.map(h => h.weight).filter(w => w > 0 && isFinite(w));

    const cohortData = data.filter(h => h.age == age && h.sex == sex);
    const cohortPrices = cohortData.map(h => h.sold_price).filter(v => isFinite(v) && v > 0);
    const cohortPrizes = cohortData.map(h => h.total_prize_latest).filter(v => isFinite(v));

    const valPrice = price || 0;
    const valPrize = prize || 0;
    const valWeight = weight || 0;

    return {
      percentiles: [
        { subject: '落札価格', A: calculatePercentile(valPrice, allPrices), fullMark: 100 },
        { subject: '現在賞金', A: calculatePercentile(valPrize, allPrizes), fullMark: 100 },
        { subject: '馬体重', A: calculatePercentile(valWeight, allWeights), fullMark: 100 },
      ],
      barDataPrice: [
        { name: 'この馬', value: safeRound(valPrice / 10000), fill: '#f59e0b' },
        { name: '同年齢・同性別(平均)', value: safeRound(average(cohortPrices) / 10000), fill: '#3b82f6' },
        { name: '全馬(平均)', value: safeRound(average(allPrices) / 10000), fill: '#9ca3af' },
      ],
      barDataPrize: [
        { name: 'この馬', value: safeRound(valPrize / 10000), fill: '#f59e0b' },
        { name: '同年齢・同性別(中央値)', value: safeRound(median(cohortPrizes) / 10000), fill: '#10b981' },
        { name: '全馬(中央値)', value: safeRound(median(allPrizes) / 10000), fill: '#9ca3af' },
      ]
    };
  }, [data, price, prize, weight, age, sex]);

  if (loading) {
    return <div className="text-center p-4 text-sm text-gray-500">市場データを計算中...</div>;
  }

  if (!stats) return null;

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <span className="text-blue-500">📊</span> 市場比較（ベンチマーク）
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          
          {/* レーダーチャート: パーセンタイル */}
          <div className="h-64 flex flex-col items-center">
            <h3 className="text-sm font-bold text-gray-600 mb-2">全体の中での位置づけ (偏差値的)</h3>
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="70%" data={stats.percentiles}>
                <PolarGrid />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10 }} />
                <Radar name="パーセンタイル" dataKey="A" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.6} />
                <Tooltip formatter={(value: number) => [`上位 ${100 - value}%`, '位置']} />
              </RadarChart>
            </ResponsiveContainer>
            <p className="text-xs text-gray-400 mt-1">※外側に近いほど上位</p>
          </div>

          {/* バーチャート: 価格比較 */}
          <div className="h-64 flex flex-col items-center">
            <h3 className="text-sm font-bold text-gray-600 mb-2">落札価格の比較 (万円)</h3>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.barDataPrice} margin={{ top: 10, right: 10, bottom: 20, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} interval={0} angle={-15} textAnchor="end" />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip cursor={{ fill: 'transparent' }} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {stats.barDataPrice.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* バーチャート: 賞金比較 */}
          <div className="h-64 flex flex-col items-center">
            <h3 className="text-sm font-bold text-gray-600 mb-2">獲得賞金の比較 (万円)</h3>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.barDataPrize} margin={{ top: 10, right: 10, bottom: 20, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} interval={0} angle={-15} textAnchor="end" />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip cursor={{ fill: 'transparent' }} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {stats.barDataPrize.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

        </div>
      </CardContent>
    </Card>
  );
}
