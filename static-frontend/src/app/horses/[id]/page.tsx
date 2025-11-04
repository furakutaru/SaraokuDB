'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { format, parseISO } from 'date-fns';
import { ja } from 'date-fns/locale';
import { ExternalLink } from 'lucide-react';
import Image from 'next/image';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { UnifiedHorse, AuctionHistory } from '@/types/unifiedHorse';
import { Header } from '@/components/Header';

// レース記録の基本型
interface RaceRecordBase {
  total_races: number;
  wins: number;
  record_format?: string;
  formatted_record?: string;
}

// 拡張されたレース記録の型
interface ExtendedRaceRecord {
  total_prize_money: number;
  last_prize_update?: string;
  // レコード関連のプロパティ
  total_races: number;
  wins: number;
  record_format?: string;
  formatted_record?: string;
}

// コンポーネント用の型
// Horse型をUnifiedHorseの拡張として定義
type Horse = Omit<UnifiedHorse, 'race_record' | 'race_records'> & {
  // 基本情報をトップレベルに展開
  name: string;
  sex: string;
  age: number;
  sire: string;
  weight?: string | number;
  total_prize_start?: number;
  
  // レース記録関連
  race_record?: RaceRecordBase;
  race_records?: ExtendedRaceRecord;
  
  // 履歴情報
  history?: Array<{
    race_record?: RaceRecordBase;
    [key: string]: any;
  }>;
  
  // その他のプロパティ
  dam: string;
  damsire: string;
  color?: string;
  birthday?: string;
  image_url?: string;
  jbis_url?: string;
  auction_url?: string;
  is_retired?: boolean;
  is_unsold?: boolean;
  retirement_date?: string;
  sold_price?: number | string | null;
  
  // 賞金関連
  total_prize_latest: number;
  
  // 表示用プロパティ
  display_price?: string;
  display_weight?: string;
  display_roi?: string;
  
  // オークション情報
  latest_auction?: any;
  auction_history?: any[];
  
  // 互換性のためのプロパティ
  wins?: number;
  record_format?: string;
  formatted_record?: string;
  disease_tags?: string[] | string;
  
  // メタデータ
  metadata?: {
    created_at?: string;
    updated_at?: string;
    data_source?: string;
  };
};

// 馬詳細ページのプロパティ型
interface HorseDetailPageProps {
  params: {
    id: string;
  };
}

// 馬詳細コンテンツのプロパティ型
interface HorseDetailContentProps {
  horse: Horse;  // UnifiedHorse から Horse に変更
  auctionHistory: AuctionHistory | null;
  isPreview?: boolean;
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
  // オークション履歴がある場合はそちらを優先
  if (auctionHistory?.price) {
    return `${auctionHistory.price.toLocaleString()}万円`;
  }
  
  // 主取りの場合は「主取り」と表示
  if (horse.is_unsold) {
    return '主取り';
  }
  
  // 馬の直接のsold_priceをチェック
  if (horse.sold_price) {
    return `${parseInt(horse.sold_price.toString()).toLocaleString()}万円`;
  }
  
  // いずれも見つからない場合
  return '-';
};

// 賞金を表示する関数（一時的に簡素化）
const displayPrize = (horse: Horse) => {
  console.log('=== displayPrize called (simplified) ===');
  console.log('Horse data:', {
    id: horse.id,
    name: horse.name,
    total_prize_start: horse.total_prize_start,
    race_records: horse.race_records,
    history: horse.history ? horse.history[0] : null
  });

  // 一時的にtotal_prize_startをそのまま表示
  if (horse.total_prize_start === 0 || horse.total_prize_start === undefined) {
    return '0円';
  }
  return `${(horse.total_prize_start / 10000).toLocaleString()}万円`;
};

// --- コンポーネント ---
const HorseDetailPage = ({ params }: HorseDetailPageProps) => {
  const router = useRouter();
  const [horse, setHorse] = useState<Horse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHorseData = async () => {
      try {
        setLoading(true);
        // APIエンドポイントからデータを取得（末尾のスラッシュを追加）
        const response = await fetch(`/api/horses/${params.id}/`, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
          // リダイレクトを自動で処理
          redirect: 'follow'
        });
        
        if (!response.ok) {
          throw new Error('データの取得に失敗しました');
        }

        const horseData = await response.json();
        
        if (!horseData) {
          throw new Error('データが空です');
        }

        // 馬の基本情報を整形
        const processedHorse: Horse = {
          ...horseData,
          // 基本情報をトップレベルに展開
          name: horseData.name || '',
          display_price: formatPrice(horseData.sold_price || 0),
          display_weight: horseData.weight ? `${horseData.weight}kg` : '不明',
          display_roi: `${calculateGrowthRate(horseData.total_prize_start || 0, horseData.total_prize_latest || 0)}%`,
          // メタデータ
          metadata: {
            created_at: horseData.metadata?.created_at || new Date().toISOString(),
            updated_at: horseData.metadata?.updated_at || new Date().toISOString(),
            data_source: horseData.metadata?.data_source || 'jbis'
          },
          // レコード情報（race_record または race_records からマッピング）
          race_records: {
            total_prize_money: horseData.total_prize_latest || 0,
            last_prize_update: horseData.race_records?.last_prize_update,
            // race_record があれば優先して使用、なければ race_records から取得
            total_races: horseData.race_record?.total_races || horseData.race_records?.total_races || 0,
            wins: horseData.race_record?.wins || horseData.race_records?.wins || 0,
            record_format: horseData.race_record?.record_format || horseData.race_records?.record_format,
            formatted_record: horseData.race_record?.formatted_record || horseData.race_records?.formatted_record
          },
          // 落札時賞金（最新の賞金情報を使用）
          total_prize_latest: horseData.total_prize_latest || 0,
          // オークション情報
          latest_auction: horseData.latest_auction || null,
          auction_history: horseData.auction_history || []
        };
        
        // デバッグ用
        console.log('Processed horse data:', {
          ...processedHorse,
          race_records: {
            ...processedHorse.race_records,
            total_races: processedHorse.race_records?.total_races,
            wins: processedHorse.race_records?.wins,
            hasRaceRecord: !!horseData.race_record,
            hasRaceRecords: !!horseData.race_records
          }
        });
        
        setHorse(processedHorse);
        setError(null);
      } catch (err) {
        console.error('馬データの取得中にエラーが発生しました:', err);
        setError('馬データの取得中にエラーが発生しました');
      } finally {
        setLoading(false);
      }
    };

    fetchHorseData();
  }, [params.id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error || !horse) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">
                {error || '馬の情報を取得できませんでした'}
              </p>
            </div>
          </div>
        </div>
        <div className="mt-4">
          <Button 
            onClick={() => router.back()}
            variant="outline"
          >
            一覧に戻る
          </Button>
        </div>
      </div>
    );
  }

  return <HorseDetailContent horse={horse} auctionHistory={horse.latest_auction || null} />;
};

const HorseDetailContent = ({ horse, auctionHistory }: HorseDetailContentProps) => {
  const router = useRouter();

  // 最新オークション情報を取得
  const latestAuction = horse.latest_auction;
  
  // 血統情報を抽出
  const sire = horse.sire || '';
  const dam = horse.dam || '';
  const damsire = horse.damsire || '';
  const color = horse.color || '';
  const birthday = horse.birthday || '';
  const imageUrl = horse.image_url || '';
  const jbisUrl = horse.jbis_url || '';
  const auctionUrl = horse.auction_url || '';

  // 疾病タグと健康状態
  const diseaseTags = horse.disease_tags || [];
  const healthIssues: string[] = [];
  
  // オークション情報を取得（互換性のため）
  const auctionInfo = horse.latest_auction || auctionHistory;
  
  // コメントを取得（互換性のため）
  const comment = auctionInfo?.comment;

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
                  {diseaseTags.length > 0 && (
                    <div className="flex flex-wrap justify-end gap-1">
                      {diseaseTags.map((tag, index) => (
                        <Badge key={index} variant="secondary" className="bg-red-100 text-red-800 text-xs">
                          {typeof tag === 'string' ? tag.trim() : String(tag).trim()}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* 馬画像 - カードいっぱいに表示 */}
                  <div className="w-full">
                    <div className="relative aspect-[4/3] w-full overflow-hidden rounded-lg bg-gray-100">
                      {imageUrl ? (
                        <Image
                          src={imageUrl}
                          alt={horse.name}
                          fill
                          className="object-cover"
                          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                          priority
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
                    {horse.race_records && (
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <span className="text-gray-600 font-medium whitespace-nowrap">獲得賞金：</span>
                        <span>{formatPrize(horse.race_records.total_prize_money)}</span>
                      </div>
                    )}
                    
                    {/* 血統情報 - 横並び表示 */}
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      {latestAuction?.comment && (
                        <div className="mt-4 p-4 bg-yellow-50 border-l-4 border-yellow-400">
                          <p className="text-yellow-700">{latestAuction.comment}</p>
                        </div>
                      )}
                      <div>
                        <div className="flex items-baseline gap-1">
                          <span className="text-gray-600">父：</span>
                          <span>{sire || '不明'}</span>
                        </div>
                      </div>
                      <div>
                        <div className="flex items-baseline gap-1">
                          <span className="text-gray-600">母：</span>
                          <span>{dam || '不明'}</span>
                        </div>
                      </div>
                      <div>
                        <div className="flex items-baseline gap-1">
                          <span className="text-gray-600">母父：</span>
                          <span>{damsire || '不明'}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* 毛色と生年月日 */}
                  <div className="flex flex-wrap gap-2 text-sm text-gray-600">
                    {color && (
                      <div className="flex items-center gap-1">
                        <span className="text-gray-600 font-medium">毛色：</span>
                        <span>{color}</span>
                      </div>
                    )}
                    {birthday && (
                      <div className="flex items-center gap-1">
                        <span className="text-gray-600 font-medium">生年月日：</span>
                        <span>{formatDate(birthday)}</span>
                      </div>
                    )}
                  </div>
                  
                  {/* 外部リンクボタン */}
                  <div className="flex gap-2 mt-2">
                    {jbisUrl && (
                      <a 
                        href={jbisUrl} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
                      >
                        <ExternalLink className="w-4 h-4" />
                        JBIS
                      </a>
                    )}
                    {auctionUrl && (
                      <a 
                        href={auctionUrl} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                      >
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                        </svg>
                        サラブレッドオークション
                      </a>
                    )}
                  </div>
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
                  {latestAuction?.price && (
                    <div className="mt-2 text-sm text-gray-600">
                      前回落札価格: {formatPrice(latestAuction.price)}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
            
            {/* 馬体重情報 */}
            {latestAuction?.weight && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">馬体重</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {latestAuction.weight} kg
                  </div>
                  {latestAuction.date && (
                    <div className="text-sm text-gray-600 mt-1">
                      計測日: {formatDate(latestAuction.date)}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* 戦績情報 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">戦績</CardTitle>
              </CardHeader>
              <CardContent>
                {horse.race_records ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-500">獲得賞金</p>
                        <p className="font-medium">
                          {(() => {
                            const result = displayPrize(horse);
                            console.log('Display Prize Result:', result, 'for horse:', horse.name);
                            return result;
                          })()}
                        </p>
                      </div>
                      <div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-gray-500">戦績情報はありません</p>
                )}
              </CardContent>
            </Card>

            {/* 戦績情報 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">戦績</CardTitle>
              </CardHeader>
              <CardContent>
                {horse.race_records ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-500">獲得賞金</p>
                        <p className="font-medium">
                          {(() => {
                            const result = displayPrize(horse);
                            console.log('Display Prize Result:', result, 'for horse:', horse.name);
                            return result;
                          })()}
                        </p>
                      </div>
                      <div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-gray-500">戦績情報はありません</p>
                )}
              </CardContent>
            </Card>

            {/* オークション情報 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">オークション情報</CardTitle>
              </CardHeader>
              <CardContent>
                {auctionInfo ? (
                  <div className="space-y-4">
                    {/* コメント表示 */}
                    {latestAuction?.comment && (
                      <div className="mb-4 p-3 bg-yellow-50 border-l-4 border-yellow-400 rounded">
                        <h4 className="font-medium text-yellow-700 mb-1">コメント</h4>
                        <p className="text-yellow-800 text-sm whitespace-pre-wrap">{latestAuction.comment}</p>
                      </div>
                    )}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="text-sm text-gray-500">開催日</div>
                        <div className="font-medium">{formatDate(auctionInfo.date)}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500">落札価格</div>
                        <div className="font-medium">
                          {auctionInfo.is_unsold 
                            ? '主取り' 
                            : auctionInfo.price 
                              ? `¥${auctionInfo.price.toLocaleString()}` 
                              : '不明'}
                        </div>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="text-sm text-gray-500">売主</div>
                        <div className="font-medium">{auctionInfo.seller || '不明'}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500">馬体重</div>
                        <div className="font-medium">
                          {auctionInfo.weight ? `${auctionInfo.weight}kg` : '計測なし'}
                        </div>
                      </div>
                    </div>
                    
                    {comment && (
                      <div className="mt-2">
                        <div className="text-sm text-gray-500 mb-1">コメント</div>
                        <div className="text-sm whitespace-pre-line bg-gray-50 p-3 rounded">
                          {comment}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-4 text-gray-500">
                    オークション情報がありません
                  </div>
                )}
              </CardContent>
            </Card>

            {/* 賞金情報 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">賞金情報</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* メタ情報 */}
                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="font-medium">登録情報</div>
                    <div>登録日: {formatDate(horse.metadata?.created_at) || '不明'}</div>
                    {horse.metadata?.updated_at && (
                      <div>更新日: {formatDate(horse.metadata.updated_at)}</div>
                    )}
                    <div>ID: {horse.id}</div>
                  </div>
                  
                  {/* 賞金情報 */}
                  <div className="space-y-2">
                    <div className="font-medium text-sm text-gray-600">レース成績</div>
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-gray-600">獲得賞金：</span>
                      <p className="text-2xl font-bold">
                        {(() => {
                          const result = displayPrize(horse as Horse);
                          console.log('Display Prize Result (large):', result, 'for horse:', horse?.name);
                          return result;
                        })()}
                      </p>
                    </div>
                    {horse.race_records?.last_prize_update && (
                      <div className="text-xs text-gray-500 mt-1">
                        賞金更新: {formatDate(horse.race_records.last_prize_update)}
                      </div>
                    )}
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
                {auctionHistory?.auction_date && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">オークション日:</span>
                    <span>{formatDate(auctionHistory.auction_date)}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-600">作成日:</span>
                  <span>{horse.metadata?.created_at ? formatDate(horse.metadata.created_at) : '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">更新日:</span>
                  <span>{horse.metadata?.updated_at ? formatDate(horse.metadata.updated_at) : '-'}</span>
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
                {latestAuction?.comment || 'コメントはありません'}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default HorseDetailPage;
