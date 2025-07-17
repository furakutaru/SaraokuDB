import React from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import HorseImage from '@/components/HorseImage';
import fs from 'fs';
import path from 'path';

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
  disease_tags: string[] | string;
  netkeiba_url: string;
  created_at: string;
  updated_at: string;
  unsold_count: number; // 追加: 主取り回数
}

interface HorseData {
  metadata: {
    total_count: number;
    last_updated: string;
  };
  horses: Horse[];
}

interface PageProps {
  params: Promise<{ id: string }>;
}

// --- 追加ユーティリティ ---
const toArray = (val: any) => Array.isArray(val) ? val : [val];
const formatManYen = (val: number) => isNaN(val) ? '-' : `${(val/10000).toFixed(1)}万円`;

// --- ここから追加: generateStaticParams ---
export async function generateStaticParams() {
  const fs = require('fs');
  const path = require('path');
  const filePath = path.join(process.cwd(), 'public', 'data', 'horses.json');
  let ids: number[] = [];
  try {
    const fileContent = fs.readFileSync(filePath, 'utf-8');
    const data = JSON.parse(fileContent);
    ids = (data.horses || []).map((h: any) => h.id);
  } catch (e) {
    // エラー時は空配列
    ids = [];
  }
  return ids.map((id: number) => ({ id: id.toString() }));
}
// --- ここまで追加 ---

// 落札価格表示用関数を追加
const formatPrice = (price: number | null | undefined) => {
  if (price === null || price === undefined) return '-';
  return '¥' + price.toLocaleString();
};

// 以前の仕様に合わせた成長率計算
const calculateGrowthRate = (start: number, latest: number) => {
  if (start === 0) return '-';
  const rate = ((latest - start) / start * 100).toFixed(1);
  return (latest - start >= 0 ? '+' : '') + rate;
};

const getPrizeDifference = () => {
  return horse.total_prize_latest - horse.total_prize_start;
};

const getSexColor = (sex: string) => {
  return sex === '牡' ? 'bg-blue-100 text-blue-800' : 'bg-pink-100 text-pink-800';
};

const getGrowthColor = (rate: string) => {
  if (rate === 'N/A') return 'text-gray-500';
  const numRate = parseFloat(rate);
  if (numRate > 0) return 'text-green-600';
  if (numRate < 0) return 'text-red-600';
  return 'text-gray-600';
};

const getPrizeStatus = () => {
  if (horse.total_prize_start === 0 && horse.total_prize_latest === 0) {
    return 'オークション後未出走';
  } else if (horse.total_prize_start === 0 && horse.total_prize_latest > 0) {
    return 'オークション後出走済み';
  } else {
    return '賞金差分';
  }
};

// 賞金バリデーション関数を追加
const formatPrize = (val: number | null | undefined) => {
  if (val === null || val === undefined) return '-';
  return `${(val / 10000).toFixed(1)}万円`;
};

export default async function HorseDetailPage({ params }: PageProps) {
  const { id } = await params;
  const horseId = parseInt(id);

  // データを直接読み込み
  let data: HorseData | null = null;
  let horse: Horse | null = null;
  let error: string | null = null;

  try {
    const filePath = path.join(process.cwd(), 'public', 'data', 'horses.json');
    const fileContent = fs.readFileSync(filePath, 'utf-8');
    data = JSON.parse(fileContent);
    
    if (data && data.horses) {
      horse = data.horses.find(h => h.id === horseId) || null;
      
      if (!horse) {
        error = '該当データがありません';
      }
    } else {
      error = 'データの形式が正しくありません';
    }
  } catch (e) {
    error = 'データの読み込みに失敗しました';
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">⚠️</div>
          <p className="text-gray-600">エラー: {error}</p>
          <Link href="/horses">
            <Button className="mt-4">一覧に戻る</Button>
          </Link>
        </div>
      </div>
    );
  }

  if (!horse) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-gray-400 text-xl mb-4">🐎</div>
          <p className="text-gray-600">データがありません</p>
          <Link href="/horses">
            <Button className="mt-4">一覧に戻る</Button>
          </Link>
        </div>
      </div>
    );
  }

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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <Link href="/horses" className="flex items-center text-gray-600 hover:text-gray-900">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              馬一覧に戻る
            </Link>
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
                    <h2 className="text-3xl font-bold text-gray-900">{horse.name}</h2>
                    {/* 性別・年齢履歴 */}
                    {toArray(horse.sex).map((sx, i) => (
                      <Badge key={i} className={getSexColor(sx)}>
                        {sx} {toArray(horse.age)[i] ?? ''}歳
                      </Badge>
                    ))}
                  </div>
                  {/* JBISリンクはそのまま */}
                  {horse.netkeiba_url && (
                    <a
                      href={horse.netkeiba_url}
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
                        alt={horse.name} 
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
                          <span className="font-medium">{toArray(horse.weight).join('kg / ')}kg</span>
                        </div>
                        {/* 販売者履歴 */}
                        <div className="flex justify-between">
                          <span className="text-gray-600">販売者:</span>
                          <span className="font-medium">{toArray(horse.seller).join(' / ')}</span>
                        </div>
                        {/* オークション日履歴 */}
                        <div className="flex justify-between">
                          <span className="text-gray-600">オークション日:</span>
                          <span className="font-medium">{toArray(horse.auction_date).join(' / ')}</span>
                        </div>
                        {/* レース成績履歴 */}
                        <div className="flex justify-between">
                          <span className="text-gray-600">レース成績:</span>
                          <span className="font-medium">{toArray(horse.race_record).join(' / ')}</span>
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
                    {(horse.disease_tags && (Array.isArray(horse.disease_tags) ? horse.disease_tags.length > 0 : String(horse.disease_tags).trim() !== '')) && (
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-3">病歴</h3>
                        <div className="flex flex-wrap gap-2">
                          {Array.isArray(horse.disease_tags)
                            ? horse.disease_tags.map((tag, index) => (
                                <Badge key={index} variant="secondary" className="bg-red-100 text-red-800">
                                  {tag.trim() || '-'}
                                </Badge>
                              ))
                            : String(horse.disease_tags).split(',').map((tag, index) => (
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
            {horse.comment && (Array.isArray(horse.comment) ? horse.comment.length > 0 : String(horse.comment).trim() !== '') ? (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle className="text-lg">コメント</CardTitle>
                </CardHeader>
                <CardContent>
                  {Array.isArray(horse.comment)
                    ? horse.comment.map((c, i) => (
                        <p key={i} className="text-gray-700 whitespace-pre-line leading-relaxed mb-2">{c}</p>
                      ))
                    : <p className="text-gray-700 whitespace-pre-line leading-relaxed">{horse.comment}</p>
                  }
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
                {horse.unsold_count > 0 && (
                  <div className="text-center text-blue-600 font-bold mb-2">主取り{horse.unsold_count}回</div>
                )}
                {/* 落札価格履歴 */}
                <div className="text-center">
                  {toArray(horse.sold_price).map((sp, i) => (
                    <div key={i} className="text-2xl font-bold mb-1">
                      {formatPrice(sp)}
                      <span className="text-xs text-gray-500 ml-2">{toArray(horse.auction_date)[i] ?? ''}</span>
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
                      {formatPrize(Number(horse.total_prize_start))}
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
                    <div className={`text-xl font-bold ${horse.total_prize_latest - horse.total_prize_start > 0 ? 'text-green-600' : horse.total_prize_latest - horse.total_prize_start < 0 ? 'text-red-600' : 'text-gray-600'}`}> 
                      {(() => {
                        const start = Number(horse.total_prize_start ?? 0);
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
                    <div className={`text-sm font-medium ${horse.total_prize_latest - horse.total_prize_start > 0 ? 'text-green-600' : horse.total_prize_latest - horse.total_prize_start < 0 ? 'text-red-600' : 'text-gray-600'}`}> 
                      {Number(horse.total_prize_start) === 0 ? '-' : ((Number(horse.total_prize_latest) - Number(horse.total_prize_start)) / Number(horse.total_prize_start) * 100).toFixed(1) + '%'}
                    </div>
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