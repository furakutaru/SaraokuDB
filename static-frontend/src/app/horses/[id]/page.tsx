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
  const formatPrice = (price: number) => {
    return price.toLocaleString();
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
  const formatPrize = (val: any) => (typeof val === 'number' && !isNaN(val) ? `${val}万円` : '-');

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
                    <Badge className={getSexColor(horse.sex)}>
                      {horse.sex} {horse.age}歳
                    </Badge>
                  </div>
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
                  {/* 画像 */}
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
                        <div className="flex justify-between">
                          <span className="text-gray-600">体重:</span>
                          <span className="font-medium">{horse.weight}kg</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">販売者:</span>
                          <span className="font-medium">{horse.seller || '不明'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">オークション日:</span>
                          <span className="font-medium">{horse.auction_date}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">レース成績:</span>
                          <span className="font-medium">{horse.race_record || '不明'}</span>
                        </div>
                      </div>
                    </div>

                    {/* 血統情報 */}
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

            {/* コメント */}
            {horse.comment && horse.comment.trim() !== '' ? (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle className="text-lg">コメント</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-700 whitespace-pre-line leading-relaxed">{horse.comment}</p>
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
                <CardTitle className="text-lg">価格情報</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600 mb-1">
                    ¥{formatPrice(horse.sold_price || 0)}
                  </div>
                  <div className="text-sm text-gray-600">落札価格</div>
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
                      {formatPrize(horse.total_prize_start)}
                    </div>
                    <div className="text-xs text-gray-600">落札時</div>
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-gray-900">
                      {formatPrize(horse.total_prize_latest)}
                    </div>
                    <div className="text-xs text-gray-600">現在</div>
                  </div>
                </div>
                <div className="border-t pt-4">
                  <div className="text-center">
                    <div className={`text-xl font-bold ${horse.total_prize_latest - horse.total_prize_start > 0 ? 'text-green-600' : horse.total_prize_latest - horse.total_prize_start < 0 ? 'text-red-600' : 'text-gray-600'}`}> 
                      {(() => {
                        const start = horse.total_prize_start ?? 0;
                        const latest = horse.total_prize_latest ?? 0;
                        const diff = latest - start;
                        const date = horse.updated_at ? new Date(horse.updated_at) : null;
                        const dateStr = date ? `${date.getFullYear()}.${(date.getMonth()+1).toString().padStart(2,'0')}.${date.getDate().toString().padStart(2,'0')}` : '';
                        if (diff === 0) {
                          return '0円';
                        } else if (diff > 0) {
                          return `+${diff.toLocaleString()}円（${dateStr}現在）`;
                        } else {
                          return `-${Math.abs(diff).toLocaleString()}円（${dateStr}現在）`;
                        }
                      })()}
                    </div>
                    <div className={`text-sm font-medium ${horse.total_prize_latest - horse.total_prize_start > 0 ? 'text-green-600' : horse.total_prize_latest - horse.total_prize_start < 0 ? 'text-red-600' : 'text-gray-600'}`}> 
                      {calculateGrowthRate(horse.total_prize_start, horse.total_prize_latest)}%
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