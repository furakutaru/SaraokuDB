'use client';

import React from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import HorseImage from '@/components/HorseImage';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface HorseHistory {
  auction_date: string;
  name: string;
  sex: string;
  age: string;
  seller: string;
  race_record: string;
  comment: string;
  sold_price: number;
  total_prize_start: number;
}

interface Horse {
  id: number;
  history: HorseHistory[];
  sire: string;
  dam: string;
  dam_sire: string;
  primary_image: string;
  disease_tags: string;
  netkeiba_url: string;
  jbis_url: string;
  weight: number | null; // 体重（またはnull）
  unsold_count: number | null; // 主取り回数
  total_prize_latest: number; // 最新賞金
  created_at: string;
  updated_at: string;
}

interface HorseData {
  metadata: any;
  horses: Horse[];
}

// --- 追加ユーティリティ ---
const toArray = (val: any) => Array.isArray(val) ? val : [val];
const formatManYen = (val: number) => isNaN(val) ? '-' : `${(val/10000).toFixed(1)}万円`;

// 落札価格表示用関数を追加
const formatPrice = (price: number | null | undefined) => {
  if (price === null || price === undefined) return '-';
  // 落札価格は万円単位ではなく、実際の金額（円）で表示
  return '¥' + (price * 10000).toLocaleString();
};

// 以前の仕様に合わせた成長率計算
const calculateGrowthRate = (start: number, latest: number) => {
  if (start === 0) return '-';
  const rate = ((latest - start) / start * 100).toFixed(1);
  return (latest - start >= 0 ? '+' : '') + rate;
};

// 賞金バリデーション関数を追加
const formatPrize = (val: number | null | undefined) => {
  if (val === null || val === undefined) return '-';
  return `${val.toFixed(1)}万円`;
};

export default function HorseDetailPage(props: any) {
  const router = useRouter();
  const horseId = parseInt(props.params.id);
  const [horse, setHorse] = useState<Horse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await fetch('/data/horses_history.json');
        if (!response.ok) throw new Error('データの取得に失敗しました');
        const data: HorseData = await response.json();
        const found = data.horses.find(h => h.id === horseId) || null;
        setHorse(found);
        if (!found) setError('該当データがありません');
      } catch (e: any) {
        setError('データの読み込みに失敗しました');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [horseId]);

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

  if (error || !horse) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">⚠️</div>
          <p className="text-gray-600">エラー: {error || 'データがありません'}</p>
          <Link href="/horses">
            <Button className="mt-4">一覧に戻る</Button>
          </Link>
        </div>
      </div>
    );
  }

  // 最新履歴を取得
  const latest = horse.history[horse.history.length - 1];

  // 落札価格フォーマット（円単位で保存されているので、そのまま表示）
  // const formatPrice = (price: number) => {
  //   return price.toLocaleString();
  // };

  // 以前の仕様に合わせた成長率計算
  // const calculateGrowthRate = (start: number, latest: number) => {
  //   if (start === 0) return '-';
  //   const rate = ((latest - start) / start * 100).toFixed(1);
  //   return (latest - start >= 0 ? '+' : '') + rate;
  // };

  // const getPrizeDifference = () => {
  //   return horse.total_prize_latest - horse.total_prize_start;
  // };

  // const getSexColor = (sex: string) => {
  //   return sex === '牡' ? 'bg-blue-100 text-blue-800' : 'bg-pink-100 text-pink-800';
  // };

  // const getGrowthColor = (rate: string) => {
  //   if (rate === 'N/A') return 'text-gray-500';
  //   const numRate = parseFloat(rate);
  //   if (numRate > 0) return 'text-green-600';
  //   if (numRate < 0) return 'text-red-600';
  //   return 'text-gray-600';
  // };

  // const getPrizeStatus = () => {
  //   if (horse.total_prize_start === 0 && horse.total_prize_latest === 0) {
  //     return 'オークション後未出走';
  //   } else if (horse.total_prize_start === 0 && horse.total_prize_latest > 0) {
  //     return 'オークション後出走済み';
  //   } else {
  //     return '賞金差分';
  //   }
  // };

  // 賞金バリデーション関数を追加
  // const formatPrize = (val: number | null | undefined) => {
  //   if (val === null || val === undefined) return '-';
  //   return `${(val / 10000).toFixed(1)}万円`;
  // };

  // horse変数が定義された後にgetSexColorを再定義
  const getSexColor = (sex: string) => {
    return sex === '牡' ? 'bg-blue-100 text-blue-800' : 'bg-pink-100 text-pink-800';
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
            <h1 className="text-xl font-semibold text-gray-900">馬詳細情報</h1>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* メイン情報 */}
          <div className="lg:col-span-2">
            <Card className="mb-6">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <h2 className="text-3xl font-bold text-gray-900">{latest.name}</h2>
                    {/* 性別・年齢履歴 */}
                    {toArray(latest.sex).map((sx, i) => (
                      <Badge key={i} className={getSexColor(sx)}>
                        {sx} {toArray(latest.age)[i] ?? ''}歳
                      </Badge>
                    ))}
                  </div>
                  {/* JBISリンク */}
                  {(horse.jbis_url || horse.netkeiba_url) && (
                    <a
                      href={horse.jbis_url || horse.netkeiba_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                      JBIS
                    </a>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* 画像はそのまま */}
                  <div className="flex justify-center">
                    {horse.primary_image ? (
                      <HorseImage 
                        src={horse.primary_image} 
                        alt={latest.name} 
                        className="w-64 h-64 object-contain rounded-lg shadow-lg bg-gray-100"
                      />
                    ) : (
                      <div className="w-64 h-64 bg-gray-200 rounded-lg flex items-center justify-center">
                        <div className="text-center text-gray-500">
                          <svg className="w-16 h-16 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          <p>No Image</p>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* 基本情報 */}
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">基本情報</h3>
                      <div className="space-y-2 text-sm">
                        {/* 体重履歴 */}
                        <div className="flex justify-between">
                          <span className="text-gray-600">体重:</span>
                          <span className="font-medium">{horse.weight}kg</span>
                        </div>
                        {/* 販売者履歴 */}
                        <div className="flex justify-between">
                          <span className="text-gray-600">販売者:</span>
                          <span className="font-medium">{toArray(latest.seller).join(' / ')}</span>
                        </div>
                        {/* オークション日履歴 */}
                        <div className="flex justify-between">
                          <span className="text-gray-600">オークション日:</span>
                          <span className="font-medium">{toArray(latest.auction_date).join(' / ')}</span>
                        </div>
                        {/* レース成績履歴 */}
                        <div className="flex justify-between">
                          <span className="text-gray-600">レース成績:</span>
                          <span className="font-medium">{toArray(latest.race_record).join(' / ')}</span>
                        </div>
                      </div>
                    </div>

                    {/* 血統・病歴はそのまま */}
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">血統</h3>
                      <div className="space-y-2 text-sm">
                        <div className="flex">
                          <span className="text-gray-600 w-12">父：</span>
                          <span className="font-medium text-left">{horse.sire || '-'}</span>
                        </div>
                        <div className="flex">
                          <span className="text-gray-600 w-12">母：</span>
                          <span className="font-medium text-left">{horse.dam || '-'}</span>
                        </div>
                        <div className="flex">
                          <span className="text-gray-600 w-12">母父：</span>
                          <span className="font-medium text-left">{horse.dam_sire || '-'}</span>
                        </div>
                      </div>
                    </div>

                    {/* 病歴 */}
                    {(horse.disease_tags && (String(horse.disease_tags).trim() !== '')) && (
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-3">病歴</h3>
                        <div className="flex flex-wrap gap-2">
                          {String(horse.disease_tags).split(',').map((tag, index) => (
                                <Badge key={index} variant="secondary" className="bg-red-100 text-red-800">
                                  {tag.trim() || '-'}
                                </Badge>
                              ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* コメント履歴 */}
            {latest.comment && (String(latest.comment).trim() !== '') ? (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle className="text-lg">コメント</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-700 whitespace-pre-line leading-relaxed">{latest.comment}</p>
                </CardContent>
              </Card>
            ) : (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle className="text-lg">コメント</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-400">-</p>
                </CardContent>
              </Card>
            )}
          </div>

          {/* サイドバー - 価格・賞金情報 */}
          <div className="lg:col-span-1">
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="text-lg">落札価格</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* 主取り回数表示 */}
                {horse.unsold_count && horse.unsold_count > 0 && (
                  <div className="text-center text-blue-600 font-bold mb-2">主取り{horse.unsold_count}回</div>
                )}
                {/* 落札価格履歴 */}
                <div className="text-center">
                  {toArray(latest.sold_price).map((sp, i) => (
                    <div key={i} className="text-2xl font-bold mb-1">
                      {formatPrice(sp)}
                      <span className="text-xs text-gray-500 ml-2">{toArray(latest.auction_date)[i] ?? ''}</span>
                    </div>
                  ))}
                  <div className="text-sm text-gray-600">落札価格履歴</div>
                </div>
              </CardContent>
            </Card>

            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="text-lg">賞金情報</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-lg font-semibold text-gray-900">
                      {formatPrize(Number(latest.total_prize_start))}
                    </div>
                    <div className="text-xs text-gray-600">落札時</div>
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-gray-900">
                      {formatPrize(Number(horse.total_prize_latest))}
                    </div>
                    <div className="text-xs text-gray-600">現在</div>
                  </div>
                </div>
                <div className="border-t pt-4">
                  <div className="text-center">
                    <div className={`text-xl font-bold ${horse.total_prize_latest - latest.total_prize_start > 0 ? 'text-green-600' : horse.total_prize_latest - latest.total_prize_start < 0 ? 'text-red-600' : 'text-gray-600'}`}> 
                      {(() => {
                        const start = Number(latest.total_prize_start ?? 0);
                        const latest = Number(horse.total_prize_latest ?? 0);
                        const diff = latest - start;
                        if (diff === 0) {
                          return '0万円';
                        } else if (diff > 0) {
                          return `+${formatManYen(diff)}`;
                        } else {
                          return `-${formatManYen(Math.abs(diff))}`;
                        }
                      })()}
                    </div>
                    <div className="text-sm text-gray-600">オークション後の活躍</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* データ更新日 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">データ情報</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">作成日:</span>
                  <span>{new Date(horse.created_at).toLocaleDateString('ja-JP')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">更新日:</span>
                  <span>{new Date(horse.updated_at).toLocaleDateString('ja-JP')}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
} 