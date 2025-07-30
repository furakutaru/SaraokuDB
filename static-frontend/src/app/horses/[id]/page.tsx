'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { format, parseISO } from 'date-fns';
import { ja } from 'date-fns/locale';

// UI Components
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

// Custom Components
import HorseImage from '@/components/HorseImage';

// Hooks
import useNormalize from '@/hooks/useNormalize';

// --- 型定義 ---
interface AuctionHistory {
  id: string;
  horse_id: string;
  auction_date: string;
  sold_price: number | null;
  total_prize_start: number;
  total_prize_latest: number;
  weight: number | null;
  seller: string;
  is_unsold: boolean;
  comment: string;
  created_at: string;
  // 互換性のためのプロパティ
  unsold?: boolean;
  detail_url?: string;
}

// 馬の型定義
interface Horse {
  id: string;
  name: string;
  sex: string;
  age: number;
  sire: string;
  dam: string;
  damsire: string;
  image_url?: string;
  jbis_url?: string;
  auction_url?: string;
  disease_tags?: string[];
  created_at: string;
  updated_at: string;
  history?: AuctionHistory[];
  // マージ用のフィールド
  sold_price?: number | null;
  unsold?: boolean;
}

// 馬詳細ページのプロパティ型
type HorseDetailPageProps = {
  params: {
    id: string;
  };
};

// 馬詳細コンテンツのプロパティ型
interface HorseDetailContentProps {
  horse: Horse;
}

// --- ヘルパー関数 ---
function calculateGrowthRate(start: number, latest: number): string {
  if (start === 0) return 'N/A';
  const growth = ((latest - start) / start) * 100;
  return `${growth > 0 ? '+' : ''}${growth.toFixed(2)}%`;
}

function formatDate(dateString: string | undefined): string {
  if (!dateString) return '日付不明';
  try {
    return format(parseISO(dateString), 'yyyy年MM月dd日', { locale: ja });
  } catch (error) {
    console.error('日付のフォーマットに失敗しました:', error);
    return '日付不明';
  }
}

function displayPrice(horse: Horse) {
  if (horse.unsold) {
    return '売却不成立';
  }
  
  if (horse.sold_price !== undefined && horse.sold_price !== null) {
    return `${horse.sold_price.toLocaleString()}万円`;
  }
  
  if (horse.history && horse.history.length > 0) {
    const latestAuction = horse.history[0];
    if (latestAuction.sold_price !== null) {
      return `${latestAuction.sold_price.toLocaleString()}万円`;
    }
    if (latestAuction.is_unsold) {
      return '売却不成立';
    }
  }
  
  return '価格情報なし';
}

// --- コンポーネント ---
function HorseDetailPage({ params }: HorseDetailPageProps) {
  const router = useRouter();
  const [horse, setHorse] = useState<Horse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHorseData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // 馬データとオークションデータを並列で取得
        const [horsesRes, auctionRes] = await Promise.all([
          fetch('/data/horses.json'),
          fetch('/data/auction_history.json')
        ]);

        if (!horsesRes.ok || !auctionRes.ok) {
          throw new Error('データの取得に失敗しました');
        }

        const [horsesData, auctionData] = await Promise.all([
          horsesRes.json(),
          auctionRes.json()
        ]);

        // 対象の馬を検索
        const foundHorse = horsesData.find((h: Horse) => h.id === params.id);
        
        if (!foundHorse) {
          throw new Error('指定された馬が見つかりませんでした');
        }

        // 馬に関連するオークション履歴をフィルタリングしてマージ
        const horseAuctions = (auctionData as AuctionHistory[])
          .filter(auction => auction.horse_id === params.id)
          .sort((a, b) => new Date(b.auction_date).getTime() - new Date(a.auction_date).getTime());

        // 最新のオークション情報を馬データにマージ
        const latestAuction = horseAuctions[0];
        const mergedHorse = {
          ...foundHorse,
          history: horseAuctions,
          sold_price: latestAuction?.sold_price ?? foundHorse.sold_price,
          unsold: latestAuction?.is_unsold || false
        };

        setHorse(mergedHorse);
      } catch (err) {
        console.error('馬データの取得中にエラーが発生しました:', err);
        setError(err instanceof Error ? err.message : '不明なエラーが発生しました');
      } finally {
        setLoading(false);
      }
    };

    fetchHorseData();
  }, [params.id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4"></div>
          <p>データを読み込んでいます...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
        <Button onClick={() => router.back()} variant="outline">
          前のページに戻る
        </Button>
      </div>
    );
  }

  if (!horse) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">馬の情報が見つかりませんでした</p>
            </div>
          </div>
        </div>
        <Button onClick={() => router.back()} variant="outline">
          前のページに戻る
        </Button>
      </div>
    );
  }

  return <HorseDetailContent horse={horse} />;
}

function HorseDetailContent({ horse }: HorseDetailContentProps) {
  const normalize = useNormalize();
  
  // 安全に文字列を取得するヘルパー関数
  const safeString = (str: string | undefined, defaultValue = '不明'): string => {
    return str || defaultValue;
  };
  
  const renderAuctionHistory = useCallback(() => {
    if (!horse.history || horse.history.length === 0) {
      return <p className="text-gray-500">オークション履歴はありません</p>;
    }

    return (
      <div className="space-y-4">
        {horse.history.map((auction) => (
          <div key={auction.id} className="border-b pb-4 last:border-b-0 last:pb-0">
            <div className="flex justify-between items-start">
              <div>
                <p className="font-medium">{formatDate(auction.auction_date)}</p>
                <p className="text-sm text-gray-600">
                  売主: {safeString(auction.seller)}
                  {auction.weight ? ` | 体重: ${auction.weight}kg` : ''}
                </p>
              </div>
              <div className="text-right">
                <p className="font-bold">
                  {auction.is_unsold 
                    ? '売却不成立' 
                    : auction.sold_price 
                      ? `${auction.sold_price.toLocaleString()}万円`
                      : '価格情報なし'}
                </p>
                <p className="text-sm text-gray-600">
                  賞金: {auction.total_prize_latest?.toLocaleString() || '0'}万円
                  {auction.total_prize_start && auction.total_prize_start > 0 && (
                    <span className="ml-2">
                      ({auction.total_prize_start.toLocaleString()}万円 → {auction.total_prize_latest?.toLocaleString() || '0'}万円)
                    </span>
                  )}
                </p>
              </div>
            </div>
            {auction.comment && (
              <p className="mt-2 text-sm text-gray-700 bg-gray-50 p-2 rounded">
                {auction.comment}
              </p>
            )}
          </div>
        ))}
      </div>
    );
  }, [horse.history]);

  const renderCommentSection = useCallback(() => {
    const latestAuction = horse.history?.[0];
    if (!latestAuction?.comment) return null;

    return (
      <Card>
        <CardHeader>
          <CardTitle>コメント</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="whitespace-pre-line">{latestAuction.comment}</p>
        </CardContent>
      </Card>
    );
  }, [horse.history]);

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-6">
      <div className="mb-6">
        <Button variant="outline" asChild>
          <Link href="/horses">
            ← 馬一覧に戻る
          </Link>
        </Button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* 左カラム: 馬の基本情報 */}
        <div className="md:col-span-1">
          <Card className="mb-6">
            <div className="relative h-64 w-full">
              <HorseImage 
                src={horse.image_url || '/images/horse-placeholder.jpg'} 
                alt={horse.name || '馬の画像'} 
                className="rounded-t-lg object-cover w-full h-full"
              />
            </div>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-2xl">{horse.name}</CardTitle>
                  <CardDescription className="text-base">
                    {horse.sex} {horse.age}歳
                  </CardDescription>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold">
                    {displayPrice(horse)}
                  </p>
                  {horse.history?.[0]?.total_prize_start && horse.history[0].total_prize_start > 0 && (
                    <p className="text-sm text-gray-600">
                      賞金: {horse.history[0].total_prize_latest?.toLocaleString() || '0'}万円
                    </p>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div>
                  <span className="text-sm text-gray-500">父:</span>
                  <p className="font-medium">{safeString(horse.sire)}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-500">母:</span>
                  <p className="font-medium">{safeString(horse.dam)}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-500">母の父:</span>
                  <p className="font-medium">{safeString(horse.damsire)}</p>
                </div>
                
                {horse.disease_tags && horse.disease_tags.length > 0 && (
                  <div className="pt-2">
                    <span className="text-sm text-gray-500 block mb-1">特徴・注意点:</span>
                    <div className="flex flex-wrap gap-1">
                      {horse.disease_tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="bg-yellow-50 text-yellow-800">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className="pt-2 flex space-x-2">
                  {horse.jbis_url && (
                    <Button asChild variant="outline" size="sm">
                      <a href={horse.jbis_url} target="_blank" rel="noopener noreferrer">
                        JBIS
                      </a>
                    </Button>
                  )}
                  {horse.auction_url && (
                    <Button asChild variant="outline" size="sm">
                      <a href={horse.auction_url} target="_blank" rel="noopener noreferrer">
                        オークション
                      </a>
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* 右カラム: 馬の情報 */}
        <div className="md:col-span-2 space-y-6">
          {/* オークション履歴 */}
          <Card>
            <CardHeader>
              <CardTitle>オークション履歴</CardTitle>
            </CardHeader>
            <CardContent>
              {renderAuctionHistory()}
            </CardContent>
          </Card>
          
          {/* コメントセクション */}
          {renderCommentSection()}
        </div>
      </div>
    </div>
  );
}

export default HorseDetailPage;