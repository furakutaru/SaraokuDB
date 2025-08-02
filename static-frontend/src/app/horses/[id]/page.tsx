'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { format, parseISO } from 'date-fns';
import { ja } from 'date-fns/locale';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

import { Header } from '@/components/Header';

// 馬の型定義（共通のHorse型を拡張）
interface Horse extends Omit<import('@/types/horse').Horse, 'comment' | 'disease_tags' | 'health_issues' | 'sold_price'> {
  // オプショナルなプロパティを追加
  unsold?: boolean;
  comment?: string;
  health_issues?: string | string[];
  disease_tags?: string | string[];
  race_record?: string;
  sold_price?: number | string | null;
}

// 馬詳細ページのプロパティ型
interface HorseDetailPageProps {
  params: {
    id: string;
  };
}

// 馬詳細コンテンツのプロパティ型
interface HorseDetailContentProps {
  horse: Horse;
  auctionHistory: AuctionHistory | null;
}

// オークション履歴の型定義
interface AuctionHistory {
  horse_id: string;
  auction_date: string;
  sold_price: number | null;
  total_prize_start: number;
  total_prize_latest: number;
  weight: number | null;
  seller: string;
  is_unsold: boolean;
  comment: string;
  id: string;
  created_at: string;
  updated_at: string;
}

// --- ヘルパー関数 ---
const calculateGrowthRate = (start: number, latest: number): string => {
  if (start === 0) return latest > 0 ? '∞' : '0';
  return (((latest - start) / start) * 100).toFixed(1);
};

const formatDate = (dateString: string | undefined): string => {
  if (!dateString) return '-';
  try {
    return format(parseISO(dateString), 'yyyy年MM月dd日', { locale: ja });
  } catch (e) {
    return dateString;
  }
};

const formatPrice = (price: number | string | null | undefined): string => {
  if (price === null || price === undefined) return '-';
  if (typeof price === 'string') {
    // 数値に変換可能な場合は変換
    const num = parseFloat(price.replace(/[^0-9.-]+/g, ''));
    if (!isNaN(num)) {
      return `¥${num.toLocaleString()}`;
    }
    return price;
  }
  return `¥${price.toLocaleString()}`;
};

const formatPrize = (prize: number | undefined): string => {
  if (prize === undefined) return '-';
  return `${prize.toLocaleString()} 万円`;
};

// 落札価格を表示する関数
const displayPrice = (horse: Horse, auctionHistory: AuctionHistory | null | undefined) => {
  console.log('displayPrice called with:', { 
    horseId: horse.id,
    horseSoldPrice: horse.sold_price,
    auctionHistory: auctionHistory 
  });

  // オークション履歴から価格を取得
  if (auctionHistory) {
    console.log('Found auction history:', { 
      is_unsold: auctionHistory.is_unsold,
      sold_price: auctionHistory.sold_price 
    });
    
    if (auctionHistory.is_unsold) {
      return <span className="text-red-600">未落札</span>;
    }
    if (auctionHistory.sold_price !== null && auctionHistory.sold_price !== undefined) {
      return <span>¥{auctionHistory.sold_price.toLocaleString()}</span>;
    }
  } else {
    console.log('No auction history found for horse:', horse.id);
  }
  
  // 互換性のため、horseオブジェクトからも確認
  console.log('Checking horse object for price:', { 
    unsold: horse.unsold,
    sold_price: horse.sold_price 
  });
  
  if (horse.unsold) {
    return <span className="text-red-600">未落札</span>;
  }
  if (horse.sold_price !== null && horse.sold_price !== undefined && horse.sold_price !== '') {
    try {
      const priceNum = typeof horse.sold_price === 'string' 
        ? parseInt(horse.sold_price.toString().replace(/[^0-9]/g, ''), 10)
        : Number(horse.sold_price);
        
      console.log('Parsed price number:', priceNum);
      
      if (!isNaN(priceNum)) {
        return <span>¥{priceNum.toLocaleString()}</span>;
      }
    } catch (e) {
      console.error('価格の変換に失敗しました:', e);
    }
  }
  
  console.log('No price found, returning default');
  return '-';
};

// --- コンポーネント ---
const HorseDetailPage = ({ params }: HorseDetailPageProps) => {
  const router = useRouter();
  const [horse, setHorse] = useState<Horse | null>(null);
  const [auctionHistory, setAuctionHistory] = useState<AuctionHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHorse = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/data/horses.json`);
        const data = await response.json();
        
        // データ構造の確認（horsesプロパティがあるか、配列自体か）
        const horsesData = data.horses || (Array.isArray(data) ? data : []);
        const foundHorse = horsesData.find((h: any) => h.id === params.id);
        
        if (foundHorse) {
          setHorse(foundHorse);
        } else {
          setError('馬の情報が見つかりませんでした');
        }
      } catch (err) {
        console.error('Error fetching horse data:', err);
        setError('データの取得中にエラーが発生しました');
      } finally {
        setLoading(false);
      }
    };

    const fetchAuctionHistory = async () => {
      try {
        const response = await fetch(`/data/auction_history.json`);
        const data = await response.json();
        
        // データ構造の確認（auction_historyプロパティがあるか、配列自体か）
        const auctionHistoryData = data.auction_history || (Array.isArray(data) ? data : []);
        const foundAuctionHistory = auctionHistoryData.find((h: any) => h.horse_id === params.id);
        
        if (foundAuctionHistory) {
          setAuctionHistory(foundAuctionHistory);
        }
      } catch (err) {
        console.error('Error fetching auction history data:', err);
      }
    };

    fetchHorse();
    fetchAuctionHistory();
  }, [params.id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header pageTitle="読み込み中..." />
        <div className="container mx-auto p-4">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded w-1/4"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header pageTitle="エラー" />
        <div className="container mx-auto p-4">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative" role="alert">
            <strong className="font-bold">エラー: </strong>
            <span className="block sm:inline">{error || '馬の情報を取得できませんでした'}</span>
            <div className="mt-4">
              <Button variant="outline" onClick={() => router.back()}>
                一覧に戻る
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!horse) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header pageTitle="馬が見つかりません" />
        <div className="container mx-auto p-4">
          <p className="text-red-500">指定された馬の情報が見つかりませんでした</p>
          <div className="mt-4">
            <Button variant="outline" onClick={() => router.back()}>
              一覧に戻る
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return <HorseDetailContent horse={horse} auctionHistory={auctionHistory} />;
};

const HorseDetailContent: React.FC<HorseDetailContentProps> = ({ horse, auctionHistory }) => {
  return (
    <div>
      <Header pageTitle={`${horse.name} の詳細`} />
      
      <div className="container mx-auto px-4 py-6">
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* メインコンテンツ */}
          <div className="lg:col-span-2 space-y-6">
            {/* 基本情報カード */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <h1 className="text-2xl font-bold">{horse.name}</h1>
                    <div className="flex items-center space-x-2">
                      {horse.sex && <span className="text-gray-600">{horse.sex}</span>}
                      {horse.age && (
                        <span className="text-gray-600">{horse.age}歳</span>
                      )}
                    </div>
                  </div>
                  {horse.disease_tags && (
                    <div className="flex flex-wrap justify-end gap-1">
                      {Array.isArray(horse.disease_tags)
                        ? horse.disease_tags.map((tag, index) => (
                            <Badge key={index} variant="secondary" className="bg-red-100 text-red-800 text-xs">
                              {tag.trim()}
                            </Badge>
                          ))
                        : String(horse.disease_tags).split(',').map((tag, index) => (
                            <Badge key={index} variant="secondary" className="bg-red-100 text-red-800 text-xs">
                              {tag.trim()}
                            </Badge>
                          ))
                      }
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* 馬画像 - カードいっぱいに表示 */}
                  <div className="w-full">
                    <div className="relative w-full h-[500px]">
                      {horse.image_url ? (
                        <Image
                          src={horse.image_url}
                          alt={horse.name || '馬の画像'}
                          fill
                          className="object-contain"
                          style={{ objectFit: 'contain' }}
                          priority
                          unoptimized
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-gray-50 text-gray-400">
                          画像なし
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* レース戦績と血統情報 - 横並び表示 */}
                  <div className="space-y-4">
                    {/* レース戦績 */}
                    <div className="text-sm">
                      <div className="flex items-baseline gap-2">
                        <span className="text-gray-600 font-medium whitespace-nowrap">レース戦績：</span>
                        <span>{horse.race_record || '不明'}</span>
                      </div>
                    </div>

                    {/* 血統情報 - 横並び表示 */}
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <div className="flex items-baseline gap-1">
                          <span className="text-gray-600">父：</span>
                          <span>{horse.sire || '不明'}</span>
                        </div>
                      </div>
                      <div>
                        <div className="flex items-baseline gap-1">
                          <span className="text-gray-600">母：</span>
                          <span>{horse.dam || '不明'}</span>
                        </div>
                      </div>
                      <div>
                        <div className="flex items-baseline gap-1">
                          <span className="text-gray-600">母父：</span>
                          <span>{horse.damsire || '不明'}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* 毛色と生年月日 */}
                  {horse.color && (
                    <div className="flex items-center space-x-4 text-gray-600 text-sm">
                      <span>{horse.color}</span>
                      {horse.birthday && (
                        <>
                          <span>|</span>
                          <span>{formatDate(horse.birthday)}</span>
                        </>
                      )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* サイドバー - 価格・賞金情報 */}
          <div className="lg:col-span-1 space-y-6">
            {/* 落札価格情報 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">落札価格</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {displayPrice(horse, auctionHistory)}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 販売者情報 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">販売者</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className="text-base">
                    {horse.seller || '不明'}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 賞金情報 */}
            <Card>
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
                
                {horse.total_prize_start !== undefined && horse.total_prize_latest !== undefined && (
                  <div className="border-t pt-4">
                    <div className="text-center">
                      <div className={`text-xl font-bold ${
                        horse.total_prize_latest > horse.total_prize_start 
                          ? 'text-green-600' 
                          : horse.total_prize_latest < horse.total_prize_start 
                            ? 'text-red-600' 
                            : 'text-gray-600'
                      }`}>
                        {(() => {
                          const start = horse.total_prize_start ?? 0;
                          const latest = horse.total_prize_latest ?? 0;
                          const diff = latest - start;
                          const date = horse.updated_at ? new Date(horse.updated_at) : null;
                          const dateStr = date ? `${date.getFullYear()}.${(date.getMonth()+1).toString().padStart(2,'0')}.${date.getDate().toString().padStart(2,'0')}` : '';
                          
                          if (diff === 0) {
                            return '変動なし';
                          } else if (diff > 0) {
                            return `+${diff.toLocaleString()}円（${dateStr}現在）`;
                          } else {
                            return `${diff.toLocaleString()}円（${dateStr}現在）`;
                          }
                        })()}
                      </div>
                      <div className={`text-sm font-medium ${
                        horse.total_prize_latest > horse.total_prize_start 
                          ? 'text-green-600' 
                          : horse.total_prize_latest < horse.total_prize_start 
                            ? 'text-red-600' 
                            : 'text-gray-600'
                      }`}>
                        {calculateGrowthRate(horse.total_prize_start, horse.total_prize_latest)}%
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* データ更新日 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">データ情報</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                {auctionHistory?.auction_date && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">オークション日:</span>
                    <span>{formatDate(auctionHistory.auction_date)}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-600">作成日:</span>
                  <span>{horse.created_at ? formatDate(horse.created_at) : '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">更新日:</span>
                  <span>{horse.updated_at ? formatDate(horse.updated_at) : '-'}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* コメント */}
        <div className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">コメント</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700 whitespace-pre-line">
                {horse.comment || 'コメントはありません'}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default HorseDetailPage;
