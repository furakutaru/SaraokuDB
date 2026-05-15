'use client';

import { Suspense, useEffect, useState, useMemo } from 'react';
import { Header } from '@/components/Header';
import { getApiBase } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ZAxis,
  BarChart, Bar, Legend, LineChart, Line, ComposedChart
} from 'recharts';

// --- 型定義・ヘルパー --- (AnalysisContent.tsxから抜粋)
interface AuctionHistory {
  horse_id: number;
  auction_date: string;
  price?: number;
  weight?: number;
  seller?: string;
  is_unsold: boolean;
  total_prize_start?: number;
  total_prize_latest?: number;
}

interface Horse {
  id: number;
  name: string;
  sex?: string;
  age?: number;
  sire?: string;
  dam_sire?: string;
  damsire?: string;
  weight?: number;
  sold_price?: number;
  is_unsold?: boolean;
  total_prize_start?: number;
  total_prize_latest?: number;
  disease_tags?: any;
  is_broodmare?: boolean;
}

const formatManYen = (value: number) => `${Math.round(value / 10000).toLocaleString()}万円`;

const calculateROI = (latest: number = 0, start: number = 0, price: number = 0) => {
  if (!price || price <= 0) return 0;
  return ((latest - start) / price) * 100;
};

// 疾病タグの解析
const hasSevereDisease = (tags: any) => {
  if (!tags) return false;
  const severe = ['屈腱炎', '骨折', '喘鳴症', 'ボーンシスト', '繋靭帯炎'];
  const tagStr = Array.isArray(tags) ? tags.join(',') : String(tags);
  return severe.some(s => tagStr.includes(s));
};

const hasAnyDisease = (tags: any) => {
  if (!tags) return false;
  const negativeTags = ['なし', 'なし。', '特になし', '特になし。', 'なし（特記事項なし）', '疾患履歴なし'];
  if (Array.isArray(tags)) return tags.length > 0 && !tags.every(t => negativeTags.includes(String(t).trim()));
  return !negativeTags.includes(String(tags).trim());
};


function DashboardContent() {
  const [data, setData] = useState<Horse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const API_BASE = getApiBase();
        const res = await fetch(`${API_BASE}/api/horses?skip=0&limit=5000`);
        if (!res.ok) throw new Error('データの取得に失敗しました');
        const payload = await res.json();
        
        const horses = payload.horses || [];
        const auctions = payload.auction_histories || [];
        
        // オークション履歴の紐付け
        const groupedAuctions = auctions.reduce((acc: any, auc: any) => {
          if (!acc[auc.horse_id]) acc[auc.horse_id] = [];
          acc[auc.horse_id].push(auc);
          return acc;
        }, {});

        const processed = horses.map((h: any) => {
          const hAuctions = groupedAuctions[h.id] || [];
          const latest = hAuctions.sort((a: any, b: any) => new Date(b.auction_date).getTime() - new Date(a.auction_date).getTime())[0];
          
          return {
            ...h,
            sold_price: latest?.price || h.sold_price || 0,
            is_unsold: latest?.is_unsold || h.is_unsold || false,
            weight: latest?.weight || h.weight || 0,
            total_prize_start: latest?.total_prize_start || h.total_prize_start || 0,
            total_prize_latest: latest?.total_prize_latest || h.total_prize_latest || 0,
          };
        }).filter((h: Horse) => !h.is_unsold && h.sold_price && h.sold_price > 0); // 取引成立馬のみ
        
        setData(processed);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // --- データ集計 ---

  // 1. Scatter Plot (Price vs ROI)
  // ROIが高すぎる外れ値（1000%超えなど）は丸めるか除外
  const scatterData = useMemo(() => {
    return data
      .map(h => {
        const roi = calculateROI(h.total_prize_latest, h.total_prize_start, h.sold_price);
        return {
          name: h.name,
          price: (h.sold_price || 0) / 10000,
          roi: Math.min(roi, 500), // 上限500%で丸める（グラフ崩れ防止）
          realRoi: roi,
          prizeDiff: ((h.total_prize_latest || 0) - (h.total_prize_start || 0)) / 10000
        };
      })
      .filter(d => d.price > 0);
  }, [data]);

  // 2. Sire Performance
  const sireData = useMemo(() => {
    const sires: Record<string, { count: number, totalPrice: number, totalPrizeDiff: number }> = {};
    data.forEach(h => {
      const sire = h.sire || '不明';
      if (!sires[sire]) sires[sire] = { count: 0, totalPrice: 0, totalPrizeDiff: 0 };
      sires[sire].count += 1;
      sires[sire].totalPrice += (h.sold_price || 0);
      sires[sire].totalPrizeDiff += ((h.total_prize_latest || 0) - (h.total_prize_start || 0));
    });
    
    return Object.entries(sires)
      .filter(([_, stats]) => stats.count >= 5) // サンプル数5頭以上
      .map(([sire, stats]) => ({
        sire,
        avgPrice: Math.round(stats.totalPrice / stats.count / 10000), // 万円
        avgPrizeDiff: Math.round(stats.totalPrizeDiff / stats.count / 10000), // 万円
        count: stats.count
      }))
      .sort((a, b) => b.avgPrice - a.avgPrice)
      .slice(0, 15); // 上位15頭
  }, [data]);

  // 3. Age & Sex Performance
  const ageSexData = useMemo(() => {
    const groups: Record<number, { 牡: number[], 牝: number[], セ: number[] }> = {};
    data.forEach(h => {
      const age = h.age || 0;
      const sex = h.sex || '不明';
      if (age < 2 || age > 10 || !['牡', '牝', 'セ'].includes(sex)) return;
      if (!groups[age]) groups[age] = { 牡: [], 牝: [], セ: [] };
      groups[age][sex as '牡' | '牝' | 'セ'].push(h.sold_price || 0);
    });

    return Object.entries(groups).map(([age, prices]) => ({
      age: `${age}歳`,
      牡: prices['牡'].length > 0 ? Math.round(prices['牡'].reduce((a, b) => a + b, 0) / prices['牡'].length / 10000) : null,
      牝: prices['牝'].length > 0 ? Math.round(prices['牝'].reduce((a, b) => a + b, 0) / prices['牝'].length / 10000) : null,
      セ: prices['セ'].length > 0 ? Math.round(prices['セ'].reduce((a, b) => a + b, 0) / prices['セ'].length / 10000) : null,
      count: prices['牡'].length + prices['牝'].length + prices['セ'].length
    })).filter(d => d.count >= 3).sort((a, b) => parseInt(a.age) - parseInt(b.age));
  }, [data]);

  // 4. Disease Impact
  const diseaseData = useMemo(() => {
    const groups = {
      '重度疾患あり': { count: 0, prices: [] as number[], rois: [] as number[] },
      'その他疾患あり': { count: 0, prices: [] as number[], rois: [] as number[] },
      '疾患記載なし': { count: 0, prices: [] as number[], rois: [] as number[] },
    };

    data.forEach(h => {
      const isSevere = hasSevereDisease(h.disease_tags);
      const isAny = hasAnyDisease(h.disease_tags);
      const price = (h.sold_price || 0) / 10000;
      const roi = calculateROI(h.total_prize_latest, h.total_prize_start, h.sold_price);
      
      let key: keyof typeof groups = '疾患記載なし';
      if (isSevere) key = '重度疾患あり';
      else if (isAny) key = 'その他疾患あり';

      groups[key].count++;
      groups[key].prices.push(price);
      // 外れ値を除外してROI平均を計算（-100%〜500%の範囲）
      if (roi >= -100 && roi <= 500) groups[key].rois.push(roi);
    });

    return Object.entries(groups).map(([name, stats]) => ({
      name,
      count: stats.count,
      avgPrice: stats.prices.length > 0 ? Math.round(stats.prices.reduce((a, b) => a + b, 0) / stats.prices.length) : 0,
      avgRoi: stats.rois.length > 0 ? Math.round(stats.rois.reduce((a, b) => a + b, 0) / stats.rois.length) : 0
    }));
  }, [data]);


  if (loading) {
    return <div className="flex justify-center items-center h-64">データを読み込み中...</div>;
  }
  if (error) {
    return <div className="text-red-500 p-4">エラー: {error}</div>;
  }

  const CustomTooltipScatter = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white border shadow p-2 text-sm rounded">
          <p className="font-bold">{data.name}</p>
          <p>落札価格: {data.price}万円</p>
          <p>獲得賞金(差分): {data.prizeDiff.toFixed(1)}万円</p>
          <p>ROI: {data.realRoi.toFixed(1)}%</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      <h2 className="text-2xl font-bold text-gray-800 border-b pb-2">データダッシュボード</h2>
      <p className="text-gray-500 text-sm">取引成立馬 {data.length}頭 のデータを元に分析しています。</p>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 1. 散布図 */}
        <Card className="col-span-1 lg:col-span-2">
          <CardHeader>
            <CardTitle>落札価格と回収率 (ROI) の分布</CardTitle>
            <p className="text-sm text-gray-500">
              ※ 価格に対してどれだけ賞金を稼いだか。左上（低価格・高ROI）が「お買い得馬」の領域です。
            </p>
          </CardHeader>
          <CardContent>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" dataKey="price" name="落札価格" unit="万" />
                  <YAxis type="number" dataKey="roi" name="ROI" unit="%" />
                  <ZAxis range={[30, 30]} />
                  <Tooltip content={<CustomTooltipScatter />} cursor={{ strokeDasharray: '3 3' }} />
                  <Scatter name="Horses" data={scatterData} fill="#3b82f6" fillOpacity={0.5} />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* 2. 種牡馬 */}
        <Card>
          <CardHeader>
            <CardTitle>種牡馬別パフォーマンス（平均落札価格 vs 獲得賞金）</CardTitle>
            <p className="text-sm text-gray-500">※ サンプル数5頭以上の上位15頭（落札価格降順）</p>
          </CardHeader>
          <CardContent>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={sireData} margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="sire" angle={-45} textAnchor="end" height={80} interval={0} tick={{ fontSize: 11 }} />
                  <YAxis yAxisId="left" orientation="left" stroke="#3b82f6" unit="万" />
                  <Tooltip />
                  <Legend verticalAlign="top" />
                  <Bar yAxisId="left" dataKey="avgPrice" name="平均落札価格" fill="#3b82f6" />
                  <Line yAxisId="left" type="monotone" dataKey="avgPrizeDiff" name="平均獲得賞金" stroke="#f59e0b" strokeWidth={2} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* 3. 年齢性別 */}
        <Card>
          <CardHeader>
            <CardTitle>年齢・性別別の平均落札価格推移</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={ageSexData} margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="age" />
                  <YAxis unit="万" />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="牡" stroke="#3b82f6" strokeWidth={2} connectNulls />
                  <Line type="monotone" dataKey="牝" stroke="#ec4899" strokeWidth={2} connectNulls />
                  <Line type="monotone" dataKey="セ" stroke="#10b981" strokeWidth={2} connectNulls />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* 4. 疾病 */}
        <Card>
          <CardHeader>
            <CardTitle>疾病記載の有無による価格とROIへの影響</CardTitle>
            <p className="text-sm text-gray-500">※ 重度：屈腱炎、骨折、喘鳴症など</p>
          </CardHeader>
          <CardContent>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={diseaseData} margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis yAxisId="left" unit="万" />
                  <YAxis yAxisId="right" orientation="right" unit="%" />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="avgPrice" name="平均落札価格" fill="#6366f1" />
                  <Line yAxisId="right" type="monotone" dataKey="avgRoi" name="平均ROI" stroke="#f43f5e" strokeWidth={3} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Header pageTitle="サラオクDB｜データダッシュボード" />
      <DashboardContent />
    </Suspense>
  );
}
