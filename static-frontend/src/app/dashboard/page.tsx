"use client";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import HorseImage from '@/components/HorseImage';
import Link from 'next/link';

interface Horse {
  id: number;
  name: string;
  sex: string;
  age: number;
  sold_price: number;
  seller: string;
  total_prize_start: number;
  total_prize_latest: number;
  sire: string;
  dam: string;
  dam_sire: string;
  comment: string;
  weight: number;
  race_record: string;
  primary_image: string;
  auction_date: string;
  disease_tags: string;
  netkeiba_url: string;
  created_at: string;
  updated_at: string;
  unsold_count: number;
}

interface Metadata {
  last_updated: string;
  total_horses: number;
  average_price: number;
  average_growth_rate: number;
  horses_with_growth_data: number;
}

interface HorseData {
  metadata: Metadata;
  horses: Horse[];
}

const formatPrice = (price: number | null | undefined) => {
  if (price === null || price === undefined) return '-';
  return '¥' + price.toLocaleString();
};
const formatPrize = (val: number | null | undefined) => {
  if (val === null || val === undefined) return '-';
  return `${val.toFixed(1)}万円`;
};
const calcROI = (prize: number, price: number) => {
  if (!price || price === 0) return '-';
  return (prize / price).toFixed(2);
};

export default function DashboardPage() {
  const [data, setData] = useState<HorseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showType, setShowType] = useState<'all' | 'roi' | 'value'>('all');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await fetch('/data/horses.json');
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

  // 主取り馬除外
  const horses = data.horses.filter(h => !h.unsold_count || h.unsold_count === 0);

  // サマリー
  const avgROI = horses.length > 0 ? (
    horses.reduce((sum, h) => sum + (h.sold_price > 0 ? h.total_prize_latest / h.sold_price : 0), 0) / horses.length
  ) : 0;

  // 指標ボタン用データ
  const roiRanking = [...horses]
    .filter(h => h.sold_price > 0)
    .sort((a, b) => (b.total_prize_latest / b.sold_price) - (a.total_prize_latest / a.sold_price))
    .slice(0, 10);
  const valueHorses = horses.filter(h => h.sold_price > 0 && (h.total_prize_latest / h.sold_price) > avgROI && h.sold_price < data.metadata.average_price);

  // 表示切替
  let tableHorses = horses;
  if (showType === 'roi') tableHorses = roiRanking;
  if (showType === 'value') tableHorses = valueHorses;

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">ダッシュボード</h1>
        {/* サマリー */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardHeader>
              <CardTitle>総馬数</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{horses.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>平均落札価格</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatPrice(data.metadata.average_price)}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>平均ROI</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{avgROI.toFixed(2)}</div>
            </CardContent>
          </Card>
        </div>
        {/* 指標ボタン */}
        <div className="flex gap-4 mb-6">
          <Button onClick={() => setShowType('all')} variant={showType==='all'?'default':'outline'}>全馬</Button>
          <Button onClick={() => setShowType('roi')} variant={showType==='roi'?'default':'outline'}>ROIランキング</Button>
          <Button onClick={() => setShowType('value')} variant={showType==='value'?'default':'outline'}>妙味馬</Button>
        </div>
        {/* DataTable風の表 */}
        <div className="overflow-x-auto bg-white rounded-lg shadow">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">馬名</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">性別</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">年齢</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">父</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">落札価格</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">オークション時賞金</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">現在賞金</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">ROI</th>
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
                  <td className="px-3 py-2">{formatPrice(horse.sold_price)}</td>
                  <td className="px-3 py-2">{formatPrize(horse.total_prize_start)}</td>
                  <td className="px-3 py-2">{formatPrize(horse.total_prize_latest)}</td>
                  <td className="px-3 py-2">{calcROI(horse.total_prize_latest, horse.sold_price)}</td>
                  <td className="px-3 py-2">
                    {horse.primary_image ? (
                      <HorseImage src={horse.primary_image} alt={horse.name} className="w-12 h-12 object-contain rounded bg-gray-100" />
                    ) : (
                      <span className="text-gray-400">No Image</span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex flex-col gap-1">
                      {horse.netkeiba_url && (
                        <a href={horse.netkeiba_url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 underline">JBIS</a>
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
  );
} 